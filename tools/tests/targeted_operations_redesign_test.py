import json
import re
from pathlib import Path

from great_ai_race_state_model_test import _named_block

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def block(relative: str, name: str) -> str:
    return _named_block(read(relative), name)


def test_game_rule_modes_and_authoritative_eligibility_contract():
    rules = read("common/game_rules/01_targeted_operations.txt")
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    effects = read("common/scripted_effects/00_targeted_operations_effects.txt")

    assert "default = {\n\t\tname = TOP_limited_sandbox_option" in rules
    assert rules.count("name = TOP_limited_sandbox_option") == 1
    assert rules.count("name = TOP_full_sandbox_option") == 1
    assert rules.count("name = TOP_disabled_option") == 1
    for name in (
        "TOP_enabled",
        "TOP_limited_sandbox",
        "TOP_full_sandbox",
        "TOP_person_operational_eligible",
        "TOP_organization_operational_eligible",
        "TOP_facility_operational_eligible",
    ):
        assert f"{name} = {{" in triggers

    assert "is_ai = no" in block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_human_offense",
    )
    assert "TOP_human_offense = yes" in block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_operational_eligible",
    )
    assert "TOP_human_offense = yes" in block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_organization_operational_eligible",
    )
    assert "TOP_rule_enabled" not in effects


def test_all_generated_native_raids_are_player_only():
    raids = read("common/raids/targeted_operations_raids.txt")
    raid_count = len(
        re.findall(r"^[ \t]*TOP_(?:drone|capture)_\d+ = \{", raids, re.MULTILINE)
    )

    assert raid_count > 0
    assert raids.count("ai_will_do = { base = 0 }") == raid_count
    assert "ai_will_do = { base = 1 }" not in raids


def test_manifest_has_four_classes_and_first_class_irgc_organizations():
    manifest = json.loads(read("tools/data/targeted_operations.json"))
    groups = {group["id"]: group for group in manifest["groups"]}

    assert set(manifest["facility_objective_defaults"]) == {
        "militant_network",
        "state_security",
        "political_executive",
        "civilian_organization",
    }
    assert {groups[index]["group_class"] for index in range(1, 11)} == {
        "militant_network"
    }
    assert {groups[index]["group_class"] for index in range(22, 25)} == {
        "militant_network"
    }
    assert groups[11]["group_class"] == "state_security"
    assert {groups[index]["group_class"] for index in (12, 17, 18, 19, 20)} == {
        "state_security"
    }
    assert {groups[index]["group_class"] for index in (13, 14, 15, 16)} == {
        "political_executive"
    }
    assert groups[21]["group_class"] == "civilian_organization"

    for index in (12, 17, 18, 19, 20):
        assert groups[index]["public_identity"] is True
        assert "ct_id" not in groups[index]


def test_facility_objective_defaults_match_organization_classes():
    manifest = json.loads(read("tools/data/targeted_operations.json"))
    defaults = manifest["facility_objective_defaults"]

    assert defaults["militant_network"] == ["command", "training", "funding"]
    assert defaults["state_security"] == ["command", "training", "funding"]
    assert defaults["political_executive"] == ["command", "funding"]
    assert defaults["civilian_organization"] == ["command", "funding"]


def test_public_and_nonpublic_subject_seeding_uses_three_axes():
    public_seed = block(
        "common/scripted_effects/06_targeted_operations_redesign.txt",
        "TOP_seed_public_subjects",
    )
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")

    assert "TOP_identity_confidence^top_public_target = 100" in public_seed
    assert "TOP_location_confidence^top_public_target" not in public_seed
    assert "TOP_pattern_confidence^top_public_target" not in public_seed
    assert "TOP_org_verification^top_public_group = 100" in public_seed
    assert "TOP_org_location^top_public_group" not in public_seed
    assert "TOP_org_activity^top_public_group" not in public_seed
    assert "TOP_identity_confidence^TOP_target = 15" in compatibility
    assert "TOP_location_confidence^TOP_target = 15" in compatibility
    assert "TOP_pattern_confidence^TOP_target = 0" in compatibility
    assert "TOP_org_verification^TOP_arg_group = 15" in compatibility
    assert "TOP_org_location^TOP_arg_group = 15" in compatibility
    organization_adapter = _named_block(compatibility, "TOP_add_organization_lead")
    assert "TOP_org_activity^TOP_arg_group = 15" not in organization_adapter
    assert (
        "add_to_variable = { TOP_org_activity^TOP_arg_group = TOP_arg_amount }"
        in organization_adapter
    )


def test_collection_focus_spillover_decay_and_staleness_contract():
    effects = read("common/scripted_effects/06_targeted_operations_redesign.txt")
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")

    for name in (
        "TOP_apply_person_collection_gain",
        "TOP_apply_organization_collection_gain",
    ):
        gain = _named_block(effects, name)
        assert "multiply = 0.25" in gain
        assert "min = 0 max = 100" in gain
        assert "lead_age" in gain
    assert "TOP_location_confidence^top_tick_target = 5" in compatibility
    assert "TOP_pattern_confidence^top_tick_target = 3" in compatibility
    assert "TOP_org_location^top_tick_group = 5" in compatibility
    assert "TOP_org_activity^top_tick_group = 3" in compatibility
    assert "TOP_lead_age^TOP_arg_target < 57" in triggers
    assert "TOP_org_lead_age^TOP_group_target < 57" in triggers


def test_package_and_operation_capacity_are_independent():
    triggers = read("common/scripted_triggers/07_targeted_operations_redesign.txt")
    person_begin = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_begin_person_operation",
    )
    organization_begin = block(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt",
        "TOP_begin_organization_operation",
    )

    assert "TOP_collecting_subjects^num < 3" in triggers
    assert "TOP_operation_subject_kind = 0" in read(
        "common/scripted_triggers/04_targeted_operations_cases.txt"
    )
    assert "TOP_operation_subject_kind = 1" in person_begin
    assert "TOP_operation_subject_kind = 2" in organization_begin
    assert "TOP_case_phase^TOP_arg_target = 3" in person_begin
    assert "TOP_org_case_phase^TOP_arg_group = 3" in organization_begin


def test_packages_pause_resume_and_abandon_without_erasing_knowledge():
    effects = read(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt"
    )
    person_abandon = _named_block(effects, "TOP_abandon_person_package")
    organization_abandon = _named_block(effects, "TOP_abandon_organization_package")

    assert "TOP_package_state^TOP_selected = 0" in person_abandon
    assert "TOP_identity_confidence" not in person_abandon
    assert "TOP_location_confidence" not in person_abandon
    assert "TOP_pattern_confidence" not in person_abandon
    assert "TOP_org_package_state^TOP_selected_organization = 0" in organization_abandon
    assert "TOP_org_verification" not in organization_abandon
    assert "TOP_org_location" not in organization_abandon
    assert "TOP_org_activity" not in organization_abandon
    assert "TOP_stop_organization_collection = {" in effects


def test_typed_selection_and_immutable_review_snapshots_are_separate():
    person_review = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_begin_review",
    )
    organization_review = block(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt",
        "TOP_begin_organization_review",
    )

    assert "TOP_proposal_subject_kind = 1" in person_review
    assert "TOP_proposal_subject_kind = 2" in organization_review
    assert "TOP_proposal_method = 6" in organization_review
    for snapshot in (
        "TOP_proposal_identity",
        "TOP_proposal_location",
        "TOP_proposal_pattern",
        "TOP_proposal_lead_age",
        "TOP_proposal_state",
        "TOP_proposal_host",
        "TOP_proposal_access",
        "TOP_proposal_host_posture",
        "TOP_proposal_doctrine",
        "TOP_proposal_capability",
    ):
        assert snapshot in person_review
        assert snapshot in organization_review
    person_risk = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_calculate_person_proposal_risks",
    )
    organization_risk = block(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt",
        "TOP_calculate_organization_proposal_risks",
    )
    for review in (person_risk, organization_risk):
        assert "TOP_proposal_harm_risk > 40" in review
        assert "TOP_proposal_harm_risk = 40" in review
        assert "var = TOP_proposal_harm_risk min = 0 max = 100" in review
    assert "TOP_case_visit_status^TOP_proposal_target = 0" in person_risk


def test_delegated_doctrine_compresses_only_nonleader_review():
    person_review = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_begin_review",
    )
    organization_review = block(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt",
        "TOP_begin_organization_review",
    )
    triggers = read(
        "common/scripted_triggers/02_targeted_operations_authorization_triggers.txt"
    )

    assert "TOP_review_is_political_leader = {" in triggers
    assert "check_variable = { TOP_proposal_doctrine = 4 }" in person_review
    assert "NOT = { TOP_review_is_political_leader = yes }" in person_review
    assert "TOP_open_senior_review = yes" in person_review
    assert "check_variable = { TOP_proposal_doctrine = 4 }" in organization_review
    assert "TOP_open_senior_review = yes" in organization_review
    assert "country_event = TOP_authorization.1" in person_review
    assert "country_event = TOP_authorization.1" in organization_review


def test_leader_assassination_is_explicit_and_requires_enhanced_package():
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    authorization = read(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
    )
    localization = read(
        "localisation/english/MD_targeted_operations_authorization_l_english.yml"
    ) + read("localisation/english/MD_targeted_operations_redesign_l_english.yml")

    assert "TOP_identity_confidence^TOP_arg_target > 79" in triggers
    assert "TOP_location_confidence^TOP_arg_target > 79" in triggers
    assert "TOP_pattern_confidence^TOP_arg_target > 79" in triggers
    assert "TOP_review_is_leader_assassination = yes" in authorization
    assert '"Assassination"' in localization
    assert '"Authorize Assassination"' in localization
    assert "capture feasibility" in localization.lower()


def test_facility_operations_damage_map_and_replace_disruption_only():
    organization = read(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt"
    )
    result = block(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt",
        "TOP_damage_organization_facility",
    )
    disruption = block(
        "common/scripted_effects/07_targeted_operations_organization_cases.txt",
        "TOP_apply_organization_disruption",
    )

    assert "damage_building = { type = infrastructure" in result
    assert "damage_building = { type = arms_factory" in result
    assert "damage_building = { type = industrial_complex" in result
    assert "TOP_group_disruption_type^TOP_group_target" in disruption
    assert "TOP_group_disruption_until^TOP_group_target" in disruption
    assert "add = 90" in disruption
    assert "kill_country_leader" not in organization + result + disruption
    assert "global.TOP_status" not in result


def test_resolution_uses_one_intelligence_roll_and_bda_never_rerolls_truth():
    resolution = read("common/scripted_effects/08_targeted_operations_resolution.txt")
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")
    person_resolution = _named_block(resolution, "TOP_resolve_person_operation")
    bda = _named_block(compatibility, "TOP_process_timers")
    investigation = _named_block(resolution, "TOP_process_attribution_investigations")

    assert person_resolution.count("randomize_temp_variable") == 1
    assert person_resolution.count("TOP_intelligence_roll >") == 3
    assert "TOP_kill_target" not in bda
    assert "TOP_capture_target" not in bda
    assert (
        investigation.count(
            "random = { chance = TOP_investigation_chance add_to_variable"
        )
        == 2
    )
    assert "TOP_case_attribution^top_attribution_target < 3" in investigation
    assert "TOP_org_case_attribution^top_attribution_group < 3" in investigation


def test_archive_is_typed_and_circular_at_128_rows():
    initialization = read("common/scripted_effects/06_targeted_operations_redesign.txt")
    resolution = read("common/scripted_effects/08_targeted_operations_resolution.txt")

    for field in (
        "subject_kind",
        "subject_id",
        "objective",
        "host",
        "identity",
        "location",
        "pattern",
        "lead_age",
        "access",
        "host_posture",
        "doctrine",
        "rigor",
        "physical",
        "bda",
        "attribution",
        "harm",
        "custodian",
        "sequence",
    ):
        assert f"TOP_archive_{field} = 128" in initialization
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")
    assert (resolution + compatibility).count(
        "modulo_variable = { TOP_archive_cursor = 128 }"
    ) == 2


def test_doctrine_vip_liaison_and_custody_depth_contracts():
    triggers = read("common/scripted_triggers/07_targeted_operations_redesign.txt")
    depth = read("common/scripted_effects/09_targeted_operations_depth.txt")

    assert "has_political_power > 99" in block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_change_doctrine",
    )
    assert "add = 365" in block(
        "common/scripted_effects/06_targeted_operations_redesign.txt",
        "TOP_change_doctrine",
    )
    assert "TOP_vip_capacity = 2" in triggers
    assert triggers.count("TOP_vip_capacity = 1") == 2
    assert "add = 91" in block(
        "common/scripted_effects/06_targeted_operations_redesign.txt",
        "TOP_assign_vip_detail",
    )
    assert "TOP_liaison_multiplier = 0.75" in depth
    assert "TOP_liaison_multiplier = 0.5" in depth
    assert "TOP_liaison_pair_until" in depth
    assert "global.TOP_exploited^TOP_arg_target = 1" in depth
    custody = depth + read("common/scripted_effects/00_targeted_operations_effects.txt")
    for disposition in (
        "TOP_prosecute_selected",
        "TOP_transfer_selected",
        "TOP_exchange_selected",
        "TOP_release_selected",
    ):
        assert f"{disposition} = {{" in custody


def test_oversight_uses_a_typed_queue_without_overwriting_open_subjects():
    depth = read("common/scripted_effects/09_targeted_operations_depth.txt")
    person_open = _named_block(depth, "TOP_open_oversight")
    organization_open = _named_block(depth, "TOP_open_organization_oversight")
    dispatcher = _named_block(depth, "TOP_dispatch_next_oversight")
    resolver = _named_block(depth, "TOP_resolve_oversight")
    events = read("events/Targeted Operations Redesign.txt")

    assert "TOP_oversight_subject_id" not in person_open
    assert "TOP_oversight_subject_id" not in organization_open
    assert "add_to_array = { TOP_oversight_queue" in person_open
    assert "add = 1000" in organization_open
    assert "TOP_oversight_subject_id = 0" in dispatcher
    assert "TOP_oversight_queue^num > 0" in dispatcher
    assert "remove_from_array = { TOP_oversight_queue" in dispatcher
    assert "TOP_oversight_subject_kind = 1" in dispatcher
    assert "TOP_oversight_subject_kind = 2" in dispatcher
    assert "TOP_dispatch_next_oversight = yes" in resolver
    oversight_event = events[events.index("\tid = TOP_redesign.20") :]
    assert (
        "trigger = { check_variable = { TOP_oversight_subject_id > 0 } }"
        in oversight_event
    )


def test_strategic_crisis_consults_faction_partners_and_guarantors():
    runtime = block(
        "common/scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_start_exposed_kill_crisis",
    )
    crisis_event = read("events/Targeted Operations Runtime.txt")
    crisis_event = crisis_event[crisis_event.index("\tid = TOP_crisis.7") :]

    assert "every_country = {" in runtime
    assert "is_in_faction_with = var:global.TOP_crisis_actor" in runtime
    assert "is_in_faction_with = var:global.TOP_crisis_protection" in runtime
    assert "is_guaranteed_by = PREV" in runtime
    for choice in (
        "harsh_sanctions",
        "add_war_support",
        "TOP_counterintelligence_level",
        "TOP_adjust_crisis_tension",
    ):
        assert choice in crisis_event
    for option in ("a", "b", "c", "g", "e", "f"):
        assert f"name = TOP_crisis.7.{option}" in crisis_event


def test_capture_uses_distinct_custody_crisis_copy_and_authored_tripwires():
    events = read("events/Targeted Operations Runtime.txt")
    localization = read(
        "localisation/english/MD_targeted_operations_authorization_l_english.yml"
    )
    depth = read("common/scripted_effects/09_targeted_operations_depth.txt")

    for event_id in ("TOP_crisis.10", "TOP_crisis.1", "TOP_crisis.2", "TOP_crisis.4"):
        event_start = events.index(f"\tid = {event_id}\n")
        event = events[event_start : event_start + 1400]
        assert "global.TOP_crisis_capture = 1" in event
        assert f"{event_id}.t_capture" in event
        assert f"{event_id}.d_capture" in event
        assert f" {event_id}.t_capture:" in localization
        assert f" {event_id}.d_capture:" in localization
    assert "custody and hostage crisis" in localization
    assert "negotiated return" in localization

    for effect, flag in (
        ("TOP_grant_expanded_doctrine_override", "TOP_expanded_doctrine_override"),
        ("TOP_grant_delegated_doctrine_override", "TOP_delegated_doctrine_override"),
        ("TOP_grant_strategic_tripwire", "TOP_strategic_tripwire"),
    ):
        assert f"set_country_flag = {flag}" in _named_block(depth, effect)


def test_public_compatibility_interfaces_remain_available():
    effects = read("common/scripted_effects/00_targeted_operations_effects.txt")

    for name in (
        "TOP_add_target_lead",
        "TOP_grant_target_mandate",
        "TOP_add_organization_lead",
        "TOP_grant_group_mandate",
        "TOP_kill_target",
        "TOP_capture_target",
        "TOP_release_selected",
        "TOP_transfer_selected",
    ):
        assert f"{name} = {{" in effects


def test_operations_center_exposes_required_filters_tabs_and_dimensions():
    gui = read("interface/targeted_operations.gui")
    scripted_gui = read("common/scripted_guis/01_targeted_operations_gui.txt")
    localization = read(
        "localisation/english/MD_targeted_operations_redesign_l_english.yml"
    )
    dispatch = read("common/scripted_localisation/01_targeted_operations_names.txt")

    assert "size = { width = 1040 height = 700 }" in gui
    title = gui[gui.index('name = "TOP_title"') :][:250]
    assert 'font = "hoi_24header"' in title
    assert "hoi_22mbs" not in gui
    for control in (
        "TOP_filter_active",
        "TOP_filter_cold",
        "TOP_filter_all",
        "TOP_filter_people",
        "TOP_filter_organizations",
        "TOP_dossier_tab",
        "TOP_package_tab",
        "TOP_authority_tab",
        "TOP_custody_tab",
        "TOP_archive_tab",
        "TOP_security_tab",
    ):
        assert control in gui
        assert control in scripted_gui
    assert 'buttonText = "TOP_organization_row_label"' in gui
    assert "[TOP_organization_row_class]: [TOP_organization_row_name]" in localization
    assert "name = TOP_authorized_name" not in dispatch
    assert "name = TOP_row_name" not in dispatch
