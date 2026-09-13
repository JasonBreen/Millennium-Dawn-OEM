from pathlib import Path

import pytest
from great_ai_race_state_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
)
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import TargetScript

ROOT = Path(__file__).resolve().parents[2]
ENCODED_STATE = -10737.40617
STATE_GUARDS = (
    (
        "scripted_effects/00_targeted_operations_effects.txt",
        "TOP_import_target_location",
        "TOP_import_state",
    ),
    (
        "scripted_effects/01_targeted_operations_world.txt",
        "TOP_global_monthly",
        "global.TOP_state^TOP_target",
    ),
    (
        "scripted_effects/01_targeted_operations_world.txt",
        "TOP_register_missing_organizations",
        "global.TOP_state^TOP_target",
    ),
    (
        "scripted_effects/01_targeted_operations_world.txt",
        "TOP_update_detained_targets",
        "global.TOP_custody_state^TOP_prisoner",
    ),
    (
        "scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_end_visit",
        "global.TOP_visit_return_state^TOP_visit_target",
    ),
    (
        "scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_end_visit",
        "TOP_visit_restore_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_authorize",
        "TOP_lead_state^TOP_selected",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_facility_available",
        "TOP_facility_state",
    ),
    (
        "scripted_triggers/02_targeted_operations_authorization_triggers.txt",
        "TOP_review_valid",
        "TOP_proposal_state",
    ),
    (
        "scripted_triggers/04_targeted_operations_cases.txt",
        "TOP_native_binding_unused",
        "TOP_binding_state",
    ),
    (
        "scripted_triggers/05_targeted_operations_runtime.txt",
        "TOP_visit_can_invite",
        "TOP_visit_trigger_state",
    ),
    (
        "scripted_localisation/01_targeted_operations_status.txt",
        "TOP_selected_location",
        "TOP_lead_state^TOP_selected",
    ),
)


def _location_guards(statements, variable):
    found = []
    for statement in statements:
        key, _, operand = statement
        if key == "NOT" and operand == [
            ("check_variable", "=", [(variable, "=", "0")])
        ]:
            found.append(statement)
        elif key == "check_variable" and operand == [(variable, ">", "0")]:
            found.append(statement)
        elif isinstance(operand, list):
            found.extend(_location_guards(operand, variable))
    return found


@pytest.mark.parametrize("path,block,variable", STATE_GUARDS)
@pytest.mark.parametrize("state", (ENCODED_STATE, 101, 0))
def test_location_presence_guards_accept_nonzero_state_references(
    path, block, variable, state
):
    text = (ROOT / "common" / path).read_text(encoding="utf-8")
    if block == "TOP_selected_location":
        start = text.rfind("defined_text", 0, text.index(f"name = {block}"))
        statements = _parse_race_script(_extract_block(text, start))["defined_text"]
    else:
        statements = _parse_race_script(_named_block(text, block))[block]
    guards = _location_guards(statements, variable)
    assert len(guards) == 1
    script = TargetScript()
    script.temps[variable] = state
    assert script.condition(guards, 1) == (state != 0)


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
def test_import_preserves_explicit_state_instead_of_random_fallback(state):
    script = TargetScript()
    script.state(state, 2)
    assert script.countries[2]["states"][0] != state
    script.temps["TOP_import_state"] = state
    script.call("TOP_import_target_location", 2, TARGET=1)
    assert script.globals["TOP_state"][1] == state
    assert script.globals["TOP_host"][1] == 2
    assert script.globals["TOP_active_targets"] == [1]
    assert script.temps["TOP_import_state"] == 0


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
def test_monthly_host_refresh_resolves_changed_state_controller(state):
    script = TargetScript()
    script.state(state, 3)
    script.target(1, host=2, state=state)
    script.stubs.add("TOP_activate_candidates")
    script.run("TOP_global_monthly", 1)
    assert script.globals["TOP_state"][1] == state
    assert script.globals["TOP_host"][1] == 3


@pytest.mark.parametrize("state", (ENCODED_STATE, 105, 0))
@pytest.mark.parametrize("kind", (1, 2, 3))
def test_facility_availability_keeps_building_and_missing_state_requirements(
    state, kind
):
    script = TargetScript()
    if state:
        script.state(state, 2)
        script.countries[state]["vars"]["industrial_complex"] = 1
        script.countries[state]["resources"] = ["oil"]
    script.temps.update(TOP_facility_state=state, TOP_facility_kind=kind)
    trigger = script.triggers["TOP_facility_available"]
    assert script.condition(trigger, 1) == (state != 0)
    if state:
        script.countries[state]["vars"].update(industrial_complex=0, infrastructure=0)
        script.countries[state]["resources"] = []
        assert not script.condition(trigger, 1)


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
@pytest.mark.parametrize("method", (2, 5))
def test_host_review_and_case_preserve_state_and_normal_cost(state, method):
    review = ReviewScript()
    review.move_target(1, state, 2)
    review.ready_for_host(method)
    assert review.actor.get("TOP_proposal_stage") == 2
    assert review.actor["TOP_proposal_state"] == state
    assert review.countries[1]["power"] == 200
    review.run("TOP_send_host_request")
    assert review.countries[2]["vars"]["TOP_incoming_state"] == state
    review.call("TOP_answer_host_request", identifier=2, CONSENT=1)
    review.run("TOP_close_review_event")
    review.run("TOP_approve_review")
    assert review.case(1, "state") == state
    assert review.case(1, "consent") == 1
    assert review.case(1, "phase") == (2 if method == 2 else 3)
    assert review.actor["TOP_authorized_state"] == state
    assert review.countries[1]["power"] == 150
    assert review.binding(method=method, state=state)
    review.run("TOP_approve_review")
    assert review.countries[1]["power"] == 150


@pytest.mark.parametrize("blocked", ("funding", "consent"))
def test_encoded_state_cannot_bypass_review_funding_or_cooperation_consent(blocked):
    review = ReviewScript()
    review.move_target(1, ENCODED_STATE, 2)
    review.ready_for_host(method=5 if blocked == "consent" else 2)
    assert review.actor.get("TOP_proposal_stage") == 2
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    if blocked == "funding":
        review.countries[1]["power"] = 49
    power = review.countries[1]["power"]
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 1
    assert review.countries[1]["power"] == power
    assert "TOP_authorized_target" not in review.actor


@pytest.mark.parametrize("state", (ENCODED_STATE, 9999, 10000, 0))
def test_native_binding_preserves_upper_boundary_and_zero_sentinel(state):
    review = ReviewScript()
    review.temps.update(TOP_arg_target=1, TOP_arg_method=2, TOP_arg_state=state)
    assert review.condition(review.triggers["TOP_native_binding_unused"], 1) == (
        state != 0 and state < 10000
    )
    assert review.temps["TOP_binding_key"] == pytest.approx(20000 + state * 2 + 2)


def test_retired_encoded_native_binding_cannot_be_recycled():
    review = ReviewScript()
    review.move_target(1, ENCODED_STATE, 2)
    review.approve_unilateral()
    assert review.binding(state=ENCODED_STATE)
    sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=sequence)
    assert review.actor["TOP_retired_native_bindings"] == pytest.approx(
        [20000 + ENCODED_STATE * 2 + 2]
    )
    review.approve_unilateral()
    assert review.case(1, "phase") == 1
    assert not review.binding(state=ENCODED_STATE)
    assert review.countries[1]["power"] == 150
    review.approve_unilateral(method=1)
    assert review.case(1, "phase") == 2
    assert review.binding(method=1, state=ENCODED_STATE)
    assert review.countries[1]["power"] == 100
