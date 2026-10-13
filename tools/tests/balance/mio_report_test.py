"""Exercise archetype coverage and branch alternatives in actual MIO exports."""

from xml.etree import ElementTree
from zipfile import ZipFile

import pytest

pytest.importorskip("pyradox")
pytest.importorskip("xlsxwriter")

from shared.suite import write_text

from tools.balance import mio_report


@pytest.mark.parametrize("predicate", ["is_usa_or_breakaway", "is_benelux_country"])
def test_concrete_group_members_reach_console_and_spreadsheet(
    tmp_path, monkeypatch, capsys, predicate
):
    equipment = mio_report.Equipment
    carrier = equipment(
        tag="carrier",
        is_archetype=True,
        archetype=None,
        types=["naval"],
        is_buildable=False,
        stats=mio_report.AllEquipmentStats(),
    )
    hull = equipment(
        tag="carrier_hull_1",
        is_archetype=False,
        archetype=carrier,
        types=["naval"],
        is_buildable=True,
        stats=mio_report.AllEquipmentStats(),
    )
    index = {carrier.tag: carrier, hull.tag: hull}
    write_text(
        tmp_path / "mios" / "carrier.txt",
        """
        carrier_org = {
            equipment_type = { carriers }
            initial_trait = { equipment_bonus = { build_cost_ic = -0.05 } }
            trait = {
                token = left
                limit_to_equipment_type = { carriers }
                mutually_exclusive = { right }
                equipment_bonus = { carrier_size = 0.1 }
            }
            trait = {
                token = right
                equipment_bonus = { carrier_size = 0.2 }
            }
        }
        """,
    )
    mios = mio_report.MIO.from_directory(
        tmp_path / "mios",
        {"carriers": mio_report.EquipmentGroup("carriers", [hull.tag])},
        False,
        equipment_index=index,
    )
    mios["carrier_org"].allowed_scope = {predicate: "yes"}
    assert mios["carrier_org"].equipment_types == {"carrier"}
    assert mios["carrier_org"].traits[0].applies_to == {"carrier"}

    mio_report.report_specific_equipment_type(carrier, mios, mio_report.WEIGHTS)
    console = capsys.readouterr().out
    assert "MIO: carrier_org" in console
    assert predicate in console
    assert "common score: 0.05" in console
    assert "carrier_size: +0.20" in console

    monkeypatch.setattr(
        equipment, "get_equipment_index", classmethod(lambda cls: index)
    )
    output = tmp_path / "report.xlsx"
    mio_report.spreadsheet_report(mios, mio_report.WEIGHTS, str(output))

    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(output) as archive:
        strings = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        values = ["".join(item.itertext()) for item in strings]
        workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        assert [sheet.attrib["name"] for sheet in workbook.find("x:sheets", ns)] == [
            "Cover",
            "carrier",
        ]
        sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet2.xml"))
        cells = {cell.attrib["r"]: cell for cell in sheet.findall(".//x:c", ns)}
        assert values[int(cells["C1"].find("x:v", ns).text)] == "Common Score"
        assert float(cells["C2"].find("x:v", ns).text) == pytest.approx(0.05)
        assert float(cells["D2"].find("x:v", ns).text) == 1
        assert predicate in values[int(cells["B2"].find("x:v", ns).text)]
        alternatives = values[int(cells["E2"].find("x:v", ns).text)]
        assert "left: carrier_size: +0.10" in alternatives
        assert "right: carrier_size: +0.20" in alternatives
        assert "excludes: right" in alternatives
