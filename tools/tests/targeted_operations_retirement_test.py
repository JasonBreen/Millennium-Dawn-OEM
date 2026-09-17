"""Cold dossiers retire, and only when nothing is riding on them.

TOP_country_tick decays confidence by 5 and ages the lead by 28 each pass. Once
confidence reaches zero the file closes and the name leaves the roster, which is
the only path in the mod that removes an entry from TOP_dossiers. These cover the
guards on that path: an open case, a recorded outcome, and custody all keep the
file, and clearing TOP_known lets the normal detection path reopen it.
"""

import pytest
from targeted_operations_core_test import ScriptArray, TargetScript

HELD_ASSESSMENTS = (2, 3, 4, 5, 7, 8, 9)


def _discovered(org_intel=40.4443):
    """A country with one discovered dossier, opened through the real path."""
    script = TargetScript()
    script.stubs.add("TOP_political_country_opportunities")
    script.stubs.add("TOP_visit_country_opportunities")
    script.globals["TOP_active_targets"] = ScriptArray([1])
    script.globals["active_terror_orgs"] = ScriptArray([10, 0, 1])
    script.globals["TOP_status"][1] = 1
    script.globals["TOP_host"][1] = 2
    script.globals["TOP_state"][1] = 101
    variables = script.countries[1]["vars"]
    variables["international_terror_org_intel"] = ScriptArray([0, org_intel, 0])
    variables["TOP_open"] = 1

    script.run("TOP_country_tick", 1)
    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_confidence"][1] == 15
    return script, variables


def _go_cold(variables, org_intel=8.8):
    """Put the file one tick from zero, with organisation intel too low to reopen."""
    variables["international_terror_org_intel"][1] = org_intel
    variables["TOP_confidence"][1] = 5


def test_a_cold_file_closes_and_leaves_the_roster():
    script, variables = _discovered()
    _go_cold(variables)

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == []
    assert variables["TOP_known"][1] == 0
    assert variables["TOP_assessment"][1] == 0
    assert variables["TOP_confidence"][1] == 0


def test_a_file_above_zero_is_kept():
    script, variables = _discovered()
    variables["international_terror_org_intel"][1] = 8.8
    variables["TOP_confidence"][1] = 10

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_known"][1] == 1
    assert variables["TOP_confidence"][1] == 5


def test_an_open_case_keeps_a_cold_file():
    script, variables = _discovered()
    _go_cold(variables)
    variables["TOP_active_cases"] = ScriptArray([1])

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_known"][1] == 1


@pytest.mark.parametrize("assessment", HELD_ASSESSMENTS)
def test_a_recorded_outcome_keeps_a_cold_file(assessment):
    script, variables = _discovered()
    _go_cold(variables)
    variables["TOP_assessment"][1] = assessment

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_assessment"][1] == assessment


@pytest.mark.parametrize("status", (0, 2))
def test_a_target_not_at_large_keeps_its_file(status):
    script, variables = _discovered()
    _go_cold(variables)
    script.globals["TOP_status"][1] = status

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_known"][1] == 1


def test_confirmed_dead_is_recorded_rather_than_retired():
    script, variables = _discovered()
    _go_cold(variables)
    script.globals["TOP_confirmed_dead"][1] = 1

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_assessment"][1] == 3


def test_retiring_the_open_file_clears_the_selection():
    script, variables = _discovered()
    _go_cold(variables)
    variables["TOP_selected"] = 1

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == []
    assert variables["TOP_selected"] == 0


def test_retiring_one_file_leaves_another_selected():
    script, variables = _discovered()
    _go_cold(variables)
    variables["TOP_selected"] = 2

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == []
    assert variables["TOP_selected"] == 2


def test_clearing_known_lets_the_detection_path_reopen_the_file():
    script, variables = _discovered()
    _go_cold(variables, org_intel=40.4443)

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_known"][1] == 1
    assert variables["TOP_confidence"][1] == 15
    assert variables["TOP_lead_age"][1] == 0


def test_retirement_does_not_disturb_the_global_registry():
    script, variables = _discovered()
    _go_cold(variables)
    before = {
        name: list(value)
        for name, value in script.globals.items()
        if isinstance(value, list)
    }

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == []
    after = {
        name: list(value)
        for name, value in script.globals.items()
        if isinstance(value, list)
    }
    assert after == before


def test_country_arrays_keep_their_length_through_a_retirement():
    script, variables = _discovered()
    _go_cold(variables)
    sizes = {
        name: len(value) for name, value in variables.items() if isinstance(value, list)
    }

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == []
    for name, size in sizes.items():
        if name == "TOP_dossiers":
            continue
        assert len(variables[name]) == size, name
