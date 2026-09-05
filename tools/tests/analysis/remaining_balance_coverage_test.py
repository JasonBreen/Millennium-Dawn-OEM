"""Fixture-only CLI, geometry, and write-protection checks for balance tools."""

import importlib
import io
import sys

import apply_ai_path_weights as weights
import pytest
from shared.suite import write_text


@pytest.fixture
def hotspots():
    pytest.importorskip("numpy")
    pytest.importorskip("PIL")
    return importlib.import_module("tools.balance.set_renewable_hotspots")


@pytest.fixture
def scurves():
    pytest.importorskip("scipy")
    return importlib.import_module("tools.balance.set_energy_tech_scurves")


@pytest.fixture
def miniature_map(tmp_path, hotspots):
    map_dir = tmp_path / "map"
    write_text(
        map_dir / "definition.csv",
        "province;red;green;blue;type;coastal;terrain;continent\n"
        "short;line\n"
        "1;255;0;0;land;true;plains;1\n"
        "2;0;255;0;land;false;forest;1\n"
        "3;0;0;255;sea;false;ocean;1\n"
        "4;255;255;0;land;false;desert;1\n",
    )
    image = hotspots.Image.new("RGB", (4, 2))
    red, green, blue, black = (255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0)
    image.putdata([red, red, green, blue, red, green, black, blue])
    image.save(map_dir / "provinces.bmp")
    hotspots.Image.new("L", (4, 2), 180).save(map_dir / "heightmap.bmp")
    return tmp_path


def test_province_geometry_ignores_unknown_pixels_and_tracks_weighted_land(
    miniature_map, hotspots
):
    geo = hotspots.load_province_geo(str(miniature_map))
    assert geo["cnt"].tolist() == [0, 3, 2, 2]
    assert geo["cx"][1] == pytest.approx(1 / 3)
    assert geo["cy"][1] == pytest.approx(1 / 3)
    assert geo["h"][1] == 180
    result = hotspots.state_geo([1, 2, 3, 4, 999], geo)
    latitude, longitude = hotspots.project(0.8, 0.4)
    assert result == pytest.approx((latitude, longitude, True, "plains", 1.0))
    assert hotspots.state_geo([3, 4, 999], geo) is None


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("existing_only", [False, True])
def test_hotspot_cli_normalizes_states_and_honors_dry_run(
    miniature_map, hotspots, monkeypatch, capsys, apply, existing_only
):
    states = miniature_map / "history" / "states"
    existing = write_text(
        states / "1.txt",
        "state = {\n\towner = USA\n\tprovinces = { 1 }\n"
        f"\tset_variable = {{ {hotspots.VAR} = 1.000 }}\n}}\n",
    )
    new = write_text(
        states / "2.txt", "state = {\n\towner = USA\n\tprovinces = { 2 }\n}\n"
    )
    sea = write_text(states / "3.txt", "state = {\n\tprovinces = { 3 }\n}\n")
    missing = write_text(states / "4.txt", "state = {\n\towner = USA\n}\n")
    before = {path: path.read_bytes() for path in (existing, new, sea, missing)}
    args = ["hotspots", "--root", str(miniature_map)]
    if apply:
        args.append("--apply")
    if existing_only:
        args.append("--existing-only")
    monkeypatch.setattr(sys, "argv", args)
    assert hotspots.main() == 0
    output = capsys.readouterr().out
    assert ("APPLIED" if apply else "DRY RUN") in output
    assert ("inserted=0" if existing_only else "inserted=1") in output
    assert ("no-provinces=0" if existing_only else "no-provinces=2") in output
    assert sea.read_bytes() == before[sea]
    assert missing.read_bytes() == before[missing]
    if not apply or existing_only:
        assert {path: path.read_bytes() for path in before} == before
    else:
        values = [
            float(
                hotspots.SET_RE.search(path.read_text(encoding="utf-8"))
                .group()
                .split("=")[-1]
                .strip(" }")
            )
            for path in (existing, new)
        ]
        assert sum(values) / len(values) == pytest.approx(1, abs=0.001)
        assert values[0] > values[1]


def test_hotspot_cli_rejects_no_states_and_skips_unowned_state(
    miniature_map, hotspots, monkeypatch, capsys
):
    monkeypatch.setattr(sys, "argv", ["hotspots", "--root", str(miniature_map)])
    with pytest.raises(SystemExit, match="no states matched"):
        hotspots.main()
    source = write_text(
        miniature_map / "history" / "states" / "1.txt",
        "state = {\n\tprovinces = { 1 }\n}\n",
    )
    original = source.read_bytes()
    monkeypatch.setattr(
        sys, "argv", ["hotspots", "--root", str(miniature_map), "--apply"]
    )
    assert hotspots.main() == 0
    assert "skipped=1" in capsys.readouterr().out
    assert source.read_bytes() == original


def test_hotspot_removes_duplicate_at_end_of_file(hotspots):
    first = f"set_variable = {{ {hotspots.VAR} = 1.000 }}"
    updated, action = hotspots.update_text(first + "\n\t" + first, 1.25)
    assert action == "update"
    assert updated == f"set_variable = {{ {hotspots.VAR} = 1.250 }}\n"


def _focus_file(tmp_path, body="\t\tai_will_do = { base = 2 }\n", name="DEN.txt"):
    return write_text(
        tmp_path / name,
        "focus_tree = {\n\tfocus = {\n\t\tid = DEN_a\n" + body + "\t}\n}\n",
    )


@pytest.mark.parametrize("dry_run", [False, True])
@pytest.mark.parametrize("stdin", [False, True])
def test_path_weights_cli_uses_same_mapping_from_file_or_stdin(
    tmp_path, monkeypatch, capsys, dry_run, stdin
):
    source = _focus_file(
        tmp_path,
        "\t\tai_will_do = {\n\t\t\tbase = 2\n\t\t\tmodifier = { factor = 0 DEN_ai_old_path = yes }\n\t\t}\n",
    )
    original = source.read_bytes()
    mapping = "group selected owner=DEN_ai_selected_path not=DEN_ai_not_selected_path\nDEN_a selected 2.5\n"
    map_path = write_text(tmp_path / "mapping.txt", mapping)
    monkeypatch.setattr(sys, "stdin", io.StringIO(mapping))
    args = ["--tag", "den", "--map", "-" if stdin else str(map_path)]
    if stdin:
        monkeypatch.setattr(
            weights, "resolve_focus_file", lambda root, tag: str(source)
        )
        args.extend(["--path", str(tmp_path)])
    else:
        args.extend(["--file", str(source)])
    if dry_run:
        args.append("--dry-run")
    assert weights.main(args) == 0
    output = capsys.readouterr().out
    assert "1 focuses re-owned, 0 un-owned, 1 path modifiers replaced" in output
    assert "DEN_a: removed" in output
    if dry_run:
        assert source.read_bytes() == original
        assert "nothing written" in output
    else:
        text = source.read_text(encoding="utf-8")
        assert "factor = 2.5 DEN_ai_selected_path = yes" in text
        assert "DEN_ai_old_path" not in text
        assert b"\r" not in source.read_bytes()
        assert not source.read_bytes().startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize(
    ("mapping", "filename", "error"),
    [
        ("DEN_a missing", "DEN.txt", "mapping error"),
        ("boost invalid", "DEN.txt", "not a number"),
        ("DEN_a -", "DEN_shared.txt", "refusing to gate a shared focus file"),
        ("DEN_missing -", "DEN.txt", "focus ids not in this file"),
    ],
)
def test_path_weights_cli_errors_preserve_source(
    tmp_path, monkeypatch, capsys, mapping, filename, error
):
    source = _focus_file(tmp_path, name=filename)
    original = source.read_bytes()
    monkeypatch.setattr(sys, "stdin", io.StringIO(mapping))
    assert weights.main(["--tag", "DEN", "--map", "-", "--file", str(source)]) == 1
    assert error in capsys.readouterr().err
    assert source.read_bytes() == original


def test_path_weights_cli_refuses_non_idempotent_transform(
    tmp_path, monkeypatch, capsys
):
    source = _focus_file(tmp_path)
    original = source.read_bytes()
    monkeypatch.setattr(sys, "stdin", io.StringIO("DEN_a -"))
    monkeypatch.setattr(
        weights, "apply", lambda lines, mapping, tag: ([*lines, "# drifting\n"], [])
    )
    assert weights.main(["--tag", "DEN", "--map", "-", "--file", str(source)]) == 1
    assert "not idempotent" in capsys.readouterr().err
    assert source.read_bytes() == original


@pytest.mark.parametrize(
    "body",
    [
        "",
        "\t\tai_will_do = { }\n",
        "\t\tai_will_do = { add = 2 }\n",
        "\t\tai_will_do = {\n\t\t\tfactor = 3\n\n\t\t\tadd = 2\n\t\t}\n",
    ],
)
def test_neutral_path_rewrite_keeps_non_path_controls(tmp_path, body):
    source = _focus_file(tmp_path, body)
    output, notes = weights.apply(
        source.read_text(encoding="utf-8").splitlines(True),
        weights.parse_mapping("DEN_a -"),
        "DEN",
    )
    text = "".join(output)
    assert text.count("ai_will_do = {") == 1
    assert "modifier =" not in text
    assert notes == []
    if "add = 2" in body:
        assert "add = 2" in text
    assert ("base = 3" if "factor = 3" in body else "base = 1") in text


def test_path_blocks_without_ids_are_ignored_and_unbalanced_blocks_rejected():
    assert weights.find_focus_spans(["focus = {\n", "}\n"]) == {}
    with pytest.raises(weights.MappingError, match="unbalanced ai_will_do"):
        weights._find_ai_will_do(["focus = {\n", "ai_will_do = {\n", "broken\n"], 0, 3)
    with pytest.raises(weights.MappingError, match="unbalanced modifier"):
        weights.rebuild_block(
            ["ai_will_do = {\n", "modifier = {\n", "broken\n"], 0, 3, None, 0, "DEN"
        )


@pytest.mark.parametrize("apply", [False, True])
def test_energy_cli_uses_complete_fixture_and_reports_written_modifiers(
    tmp_path, scurves, monkeypatch, capsys, apply
):
    blocks = []
    for chain in scurves.CHAINS.values():
        for tech in chain["techs"]:
            blocks.append(f"\t{tech} = {{\n\t\t{chain['power']} = 0.1\n\t}}\n")
    source = write_text(
        tmp_path / "industry.txt", "technologies = {\n" + "".join(blocks) + "}\n"
    )
    original = source.read_bytes()
    monkeypatch.setattr(scurves, "INDUSTRY", str(source))
    monkeypatch.setattr(sys, "argv", ["scurves", *(["--apply"] if apply else [])])
    assert scurves.main() == 0
    output = capsys.readouterr().out
    assert (
        "APPLIED: 35 techs edited" if apply else "DRY RUN: 35 techs edited"
    ) in output
    assert "amplitudes: fossil" in output
    if apply:
        text = source.read_text(encoding="utf-8")
        for chain in scurves.CHAINS.values():
            assert text.count(chain["speed"] + " = ") == len(chain["techs"])
            assert text.count(chain["infra"] + " = ") == len(chain["techs"])
    else:
        assert source.read_bytes() == original
        assert "re-run with --apply" in output


def test_energy_cli_missing_tech_aborts_the_entire_write(
    tmp_path, scurves, monkeypatch, capsys
):
    source = write_text(tmp_path / "industry.txt", "technologies = {\n}\n")
    original = source.read_bytes()
    monkeypatch.setattr(scurves, "INDUSTRY", str(source))
    monkeypatch.setattr(sys, "argv", ["scurves", "--apply"])
    assert scurves.main() == 1
    assert "aborted write" in capsys.readouterr().out
    assert source.read_bytes() == original
