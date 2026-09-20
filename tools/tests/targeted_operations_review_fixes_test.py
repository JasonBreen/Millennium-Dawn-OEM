import re

from great_ai_race_state_model_test import _extract_block
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import TargetScript
from targeted_operations_redesign_test import block, read


def test_collection_rebuild_prunes_inactive_typed_assignments_and_pauses_packages():
    script = TargetScript()
    variables = script.target(11)
    script.target(12)
    script.target(15)
    variables["TOP_package_state"][11] = 2
    variables["TOP_package_state"][12] = 2
    variables["TOP_package_state"][15] = 2
    variables["TOP_collection_focus"][12] = 2
    script.globals["TOP_status"][11] = 2
    script.ineligible_roles.add(15)
    script.globals["TOP_group_destroyed"][2] = 1
    variables["TOP_org_package_state"][2] = 2
    variables["TOP_collecting_subjects"] = [11, 12, 15, 1002]

    script.run("TOP_process_collection_assignments", 1)

    assert variables["TOP_collecting_subjects"] == [12]
    assert variables["TOP_package_state"][11] == 1
    assert variables["TOP_package_state"][12] == 2
    assert variables["TOP_package_state"][15] == 1
    assert variables["TOP_org_package_state"][2] == 1


def test_liaison_merge_never_replaces_a_known_location_with_an_empty_report():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_lead_state"][11] = 101
    variables["TOP_lead_host"][11] = 2
    variables["TOP_lead_age"][11] = 40
    script.temps.update(
        TOP_liaison_snapshot_kind=1,
        TOP_liaison_snapshot_id=11,
        TOP_liaison_axis_1=90,
        TOP_liaison_axis_2=0,
        TOP_liaison_axis_3=90,
        TOP_liaison_state=0,
        TOP_liaison_host=0,
        TOP_liaison_age=0,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_lead_state"][11] == 101
    assert variables["TOP_lead_host"][11] == 2
    assert variables["TOP_lead_age"][11] == 40

    variables["TOP_org_lead_state"][2] = 101
    variables["TOP_org_lead_host"][2] = 2
    variables["TOP_org_lead_age"][2] = 35
    script.temps.update(
        TOP_liaison_snapshot_kind=2,
        TOP_liaison_snapshot_id=2,
        TOP_liaison_axis_1=90,
        TOP_liaison_axis_2=0,
        TOP_liaison_axis_3=90,
        TOP_liaison_state=0,
        TOP_liaison_host=0,
        TOP_liaison_age=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_org_lead_state"][2] == 101
    assert variables["TOP_org_lead_host"][2] == 2
    assert variables["TOP_org_lead_age"][2] == 35


def test_linked_exploitation_skips_fully_saturated_dossiers():
    script = TargetScript()
    variables = script.target(11, status=2)
    script.globals["TOP_custodian"][11] = 1
    script.globals["TOP_exploitation_until"][11] = 100
    script.globals["TOP_affiliation"][11] = 1
    for target, score in ((12, 100), (13, 10), (14, 20)):
        script.target(target)
        script.globals["TOP_affiliation"][target] = 1
        for axis in (
            "TOP_identity_confidence",
            "TOP_location_confidence",
            "TOP_pattern_confidence",
        ):
            variables[axis][target] = score
    variables["TOP_selected"] = 11

    script.call("TOP_exploit_linked_targets", TARGET=11)

    for axis in (
        "TOP_identity_confidence",
        "TOP_location_confidence",
        "TOP_pattern_confidence",
    ):
        assert variables[axis][12] == 100
        assert variables[axis][13] == 30
        assert variables[axis][14] == 40
    assert script.globals["TOP_exploited"][11] == 1


def test_prosecuting_an_iraq_hunt_target_refreshes_legacy_progress_immediately():
    script = TargetScript()
    variables = script.target(56, status=2)
    script.globals["TOP_custodian"][56] = 1
    variables["TOP_selected"] = 56
    before = script.external["TOP_update_iraq_progress", 1]

    script.run("TOP_prosecute_selected", 1)

    assert script.globals["TOP_status"][56] == 4
    assert script.external["TOP_update_iraq_progress", 1] == before + 1


def test_review_risk_calculators_preserve_visit_exception_and_ordinary_cap():
    review = ReviewScript()
    review.actor.update(
        TOP_proposal_target=1,
        TOP_proposal_method=1,
        TOP_proposal_pattern=0,
        TOP_proposal_host_posture=1,
        TOP_proposal_doctrine=4,
        TOP_proposal_rigor=1,
    )
    review.actor["TOP_case_visit_status^1"] = 0
    review.run("TOP_calculate_person_proposal_risks")
    assert review.actor["TOP_proposal_exposure_score"] == 95
    assert review.actor["TOP_proposal_harm_risk"] == 40

    review.actor["TOP_case_visit_status^1"] = 1
    review.run("TOP_calculate_person_proposal_risks")
    assert review.actor["TOP_proposal_harm_risk"] == 100

    review.actor.update(
        TOP_proposal_pattern=0,
        TOP_proposal_host_posture=3,
        TOP_proposal_doctrine=4,
        TOP_proposal_rigor=1,
    )
    review.run("TOP_calculate_organization_proposal_risks")
    assert review.actor["TOP_proposal_exposure_score"] == 40
    assert review.actor["TOP_proposal_harm_risk"] == 40


def test_cooperative_host_recalculates_and_freezes_risk_and_liaison_relationship():
    review = ReviewScript()
    review.ready_for_host(method=1)
    assert review.actor["TOP_proposal_exposure_score"] == 85
    review.run("TOP_send_host_request")
    review.call("TOP_answer_host_request", identifier=2, POSTURE=4)
    assert review.actor["TOP_proposal_exposure_score"] == 50
    assert review.countries[2]["vars"]["TOP_liaison_partners"] == [1]
    review.run("TOP_close_review_event")
    review.run("TOP_approve_review")
    assert review.case(1, "exposure_score") == 50
    assert review.case(1, "harm_risk") == 0


def test_pending_attribution_and_open_oversight_block_case_reuse_then_reset():
    review = ReviewScript()
    review.actor["TOP_attribution_pending_people"] = [1]
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor.get("TOP_proposal_stage", 0) == 0

    review.actor["TOP_attribution_pending_people"] = []
    review.actor["TOP_case_oversight_open^1"] = 1
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor.get("TOP_proposal_stage", 0) == 0

    review.actor.update(
        {
            "TOP_case_oversight_open^1": 0,
            "TOP_case_attribution_due^1": 42,
            "TOP_case_attribution_investigated^1": 1,
            "TOP_case_oversight^1": 3,
            "TOP_case_crisis_opened^1": 1,
        }
    )
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor["TOP_proposal_stage"] == 1
    assert review.actor["TOP_case_attribution_due^1"] == 0
    assert review.actor["TOP_case_attribution_investigated^1"] == 0
    assert review.actor["TOP_case_oversight^1"] == 0
    assert review.actor["TOP_case_oversight_open^1"] == 0
    assert review.actor["TOP_case_crisis_opened^1"] == 0

    organization = ReviewScript()
    organization.actor.update(
        {
            "TOP_selected_kind": 2,
            "TOP_selected_organization": 1,
            "TOP_org_known^1": 1,
            "TOP_org_package_state^1": 1,
            "TOP_org_verification^1": 95,
            "TOP_org_location^1": 95,
            "TOP_org_activity^1": 95,
            "TOP_org_lead_age^1": 0,
            "TOP_org_lead_state^1": 100,
            "TOP_org_lead_host^1": 2,
            "TOP_org_case_phase^1": 0,
            "TOP_org_case_oversight_open^1": 0,
            "TOP_active_organization_cases": [],
        }
    )
    organization.globals.update(
        {
            "TOP_group_window^1": 1,
            "TOP_group_destroyed^1": 0,
            "TOP_group_facility_objectives^1": 7,
        }
    )
    organization.actor["TOP_attribution_pending_organizations"] = [1]
    organization.run("TOP_begin_organization_review")
    assert organization.actor.get("TOP_proposal_stage", 0) == 0

    organization.actor["TOP_attribution_pending_organizations"] = []
    organization.actor["TOP_org_case_oversight_open^1"] = 1
    organization.run("TOP_begin_organization_review")
    assert organization.actor.get("TOP_proposal_stage", 0) == 0

    organization.actor.update(
        {
            "TOP_org_case_oversight_open^1": 0,
            "TOP_org_case_attribution_due^1": 42,
            "TOP_org_case_attribution_investigated^1": 1,
            "TOP_org_case_oversight^1": 3,
        }
    )
    organization.run("TOP_begin_organization_review")
    assert organization.actor["TOP_proposal_stage"] == 1
    assert organization.actor["TOP_org_case_attribution_due^1"] == 0
    assert organization.actor["TOP_org_case_attribution_investigated^1"] == 0
    assert organization.actor["TOP_org_case_oversight^1"] == 0
    assert organization.actor["TOP_org_case_oversight_open^1"] == 0


def test_authoritative_review_gates_and_blocker_cover_pending_consequences():
    person = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_authorize",
    )
    organization = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_review_organization",
    )
    blocker = read("common/scripted_localisation/04_targeted_operations_redesign.txt")
    localization = read(
        "localisation/english/MD_targeted_operations_redesign_l_english.yml"
    )

    assert "TOP_attribution_pending_people = TOP_selected" in person
    assert "TOP_case_oversight_open^TOP_selected = 0" in person
    assert (
        "TOP_attribution_pending_organizations = TOP_selected_organization"
        in organization
    )
    assert "TOP_org_case_oversight_open^TOP_selected_organization = 0" in organization
    assert "name = TOP_action_blocker" in blocker
    assert "TOP_blocker_attribution_pending" in blocker
    assert (
        "prior operation's attribution investigation is still pending" in localization
    )


def test_liaison_eligibility_uses_persistent_relationship_and_free_inbox():
    trigger = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_request_liaison",
    )
    request = block(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_request_liaison",
    )
    answer = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_answer_host_request",
    )

    assert "TOP_incoming_liaison_actor = 0" in trigger
    assert "is_in_array = { TOP_liaison_partners = PREV }" in trigger
    assert "TOP_case_host_posture" not in trigger
    assert "TOP_org_case_host_posture" not in trigger
    assert "TOP_liaison_partner = PREV" not in trigger
    assert request.index("TOP_can_request_liaison = yes") < request.index(
        "add_political_power = -25"
    )
    assert "add_to_array = { TOP_liaison_partners = TOP_incoming_actor }" in answer


def test_capture_crisis_remote_access_vip_and_frozen_resolution_contracts():
    shared = block(
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_apply_shared_consequences",
    )
    access = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_access_available",
    )
    vip = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_assign_vip_detail",
    )
    person = block(
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_calculate_person_consequences",
    )
    organization = block(
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_calculate_organization_consequences",
    )

    assert "TOP_result = 2" in shared
    assert "TOP_start_capture_crisis = yes" in shared
    assert "TOP_start_strategic_leader_crisis = yes" in shared
    assert "Native launch revalidates base, equipment, range, and DLC gates" in access
    assert "TOP_role_target = TOP_arg_target" in vip
    assert "TOP_authored_role_eligible = yes" in vip
    assert "TOP_case_exposure_score^TOP_target" in person
    assert "TOP_case_harm_risk^TOP_target" in person
    assert "TOP_get_defensive_modifiers" not in person
    assert "TOP_org_case_exposure_score^TOP_group_target" in organization
    assert "TOP_org_case_harm_risk^TOP_group_target" in organization


def test_every_effectful_redesign_event_option_has_exactly_one_log():
    events = read("events/Targeted Operations Redesign.txt")
    options = [
        _extract_block(events, match.start())
        for match in re.finditer(r"(?m)^\toption = \{", events)
    ]
    assert options
    no_effect_options = {
        "TOP_redesign.1.e",
        "TOP_redesign.2.c",
        "TOP_redesign.10.a",
        "TOP_redesign.40.e",
    }
    for option in options:
        expected_logs = 0 if any(name in option for name in no_effect_options) else 1
        assert option.count("\n\t\tlog = ") == expected_logs
