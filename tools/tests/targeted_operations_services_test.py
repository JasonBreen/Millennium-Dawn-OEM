from copy import deepcopy
from pathlib import Path

import pytest

from shared.ai_race_test_support import _named_block
from targeted_operations_core_test import TargetScript

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def test_investigation_is_victim_owned_and_idempotent():
    script = TargetScript()
    victim = script.countries[2]["vars"]
    victim["ct_attacked_by_org_arr"] = [0, 2, 0]
    before = deepcopy(victim["ct_attacked_by_org_arr"])

    for attacker, sequence, subject, evidence in [
        (1, 4, 15, 0), (1, 4, 15, 2), (1, 4, 15, 1), (3, 4, 16, 0), (1, 5, 18, 1)
    ]:
        script.temps.update(
            top_investigation_source=attacker,
            TOP_case_result_sequence=sequence,
            TOP_target=subject,
            top_investigation_evidence=evidence,
        )
        script.run("top_record_victim_investigation", 2)

    assert victim["top_investigation_sources"] == [1, 3, 1]
    assert victim["top_investigation_sequences"] == [4, 4, 5]
    assert victim["top_investigation_targets"] == [15, 16, 18]
    assert victim["top_investigation_evidence"] == [2, 0, 1]
    assert victim["ct_attacked_by_org_arr"] == before
    assert "top_investigation_sources" not in script.countries[1]["vars"]


def test_native_completion_checks_the_reserved_host_and_consumes_binding_once():
    script = TargetScript()
    actor = script.countries[1]["vars"]
    actor.update(
        top_agency_case_host=2,
        top_agency_case_kind=2,
        top_agency_case_sequence=7,
        TOP_operation_subject_kind=2,
        TOP_operation_subject_id=10,
        TOP_operation_sequence=7,
    )
    script.triggers["TOP_organization_mission_binding_valid"] = [("always", "=", "yes")]
    script.effects["TOP_resolve_organization_operation"] = [
        ("add_to_variable", "=", [("test_resolutions", "=", "1")])
    ]
    script.temps["top_agency_callback_host"] = 3
    script.run("top_resolve_agency_case", 1)
    assert actor.get("test_resolutions", 0) == 0
    script.temps["top_agency_callback_host"] = 2
    script.globals["TOP_rule_mode"] = 0
    script.run("top_resolve_agency_case", 1)
    assert actor.get("test_resolutions", 0) == 0
    script.globals["TOP_rule_mode"] = 1
    actor["TOP_operation_sequence"] = 8
    script.run("top_resolve_agency_case", 1)
    assert actor.get("test_resolutions", 0) == 0
    actor["TOP_operation_sequence"] = 7
    script.run("top_resolve_agency_case", 1)
    script.run("top_resolve_agency_case", 1)
    assert actor["test_resolutions"] == 1


@pytest.mark.parametrize(
    "host,has_dlc,has_agency,route",
    [(2, True, True, True), (1, True, True, False), (2, False, True, False), (2, True, False, False)],
)
def test_native_dispatch_reserves_only_agency_cases_with_a_foreign_host(
    host, has_dlc, has_agency, route
):
    script = TargetScript()
    script.enabled_dlcs = {"La Resistance"} if has_dlc else set()
    script.countries[1]["intelligence_agency"] = has_agency
    actor = script.countries[1]["vars"]
    actor.update(TOP_operation_sequence=5, TOP_operation_subject_kind=1)
    script.temps["top_agency_host"] = host
    script.run("top_reserve_agency_case", 1)
    assert bool(actor.get("top_agency_case_sequence", 0)) is route
    if route:
        assert actor["top_agency_case_host"] == host
        assert actor["top_agency_case_kind"] == 1


def test_invalidated_case_cannot_rebind_while_its_engine_operation_is_running():
    script = TargetScript()
    script.enabled_dlcs = {"La Resistance"}
    actor = script.countries[1]
    actor["intelligence_agency"] = True
    actor["vars"]["top_agency_case_host"] = 2
    actor["is_running_operation"] = {(2, "operation_execute_targeted_case")}
    script.temps["top_agency_host"] = 3
    route = script.triggers["top_agency_route_available"]
    assert not script.condition(route, 1)
    actor["is_running_operation"].clear()
    assert script.condition(route, 1)


def test_national_and_faction_entry_points_do_not_use_counter_terror():
    gui = read("common/scripted_guis/01_targeted_operations_gui.txt")
    assert "parent_window_name = countryintelligenceagencyview" in _named_block(
        gui, "top_national_service_gui"
    )
    assert "parent_window_name = countryfactionview" in _named_block(
        gui, "top_faction_service_gui"
    )
    assert "open_MD_countrymissilesview" not in gui
    assert "var_open_MD_CT_gui" not in gui
    security = _named_block(
        read("common/scripted_triggers/03_targeted_operations_security.txt"),
        "TOP_security_window_visible",
    )
    assert "open_MD_countrymissilesview" not in security
    assert "top_faction_desk = 1" in security
    international = read("common/scripted_guis/00_missiles_scripted_guis.txt")
    assert "TOP_open_button" not in international
    assert "TOP_open_dossiers" not in international
    assert "name = \"TOP_open_button\"" not in read("interface/MD_countrymissilesview.gui")
