from copy import deepcopy

import pytest
from ai_race_state_model_test import _named_block, _parse_race_script
from stalker_lifecycle_test import ROOT, StalkerScript, _option


class ProliferationScript(StalkerScript):
    def __init__(self):
        super().__init__()
        for name in ("scripted", "operations", "proliferation", "incidents"):
            path = f"common/scripted_effects/99_METALGEAR_{name}_effects.txt"
            self.effects.update(
                _parse_race_script((ROOT / path).read_text(encoding="utf-8"))
            )
        self.triggers["METALGEAR_scenario_enabled"] = [("always", "=", "yes")]
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/99_METALGEAR_proliferation_triggers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        if self.tag("JAP") is None:
            self.country(920, tag="JAP")
        self.country(769, tag="NEW_YORK")
        self.countries[769]["controller"] = 1
        self.globals.update(
            METALGEAR_capacity=2,
            METALGEAR_coherence=70,
            METALGEAR_reach=50,
            METALGEAR_exposure=10,
        )
        for tag in ("USA", "JAP", "SOV"):
            self.countries[self.tag(tag)]["vars"].update(
                political_power=200, METALGEAR_review_phase=4
            )
        self.goto(2001, 1, 1)

    def execute_statement(self, statement, identifier):
        if statement[0] != "custom_effect_tooltip":
            super().execute_statement(statement, identifier)


def choose(script, number, letter, tag="USA"):
    script.actor = script.tag(tag)
    filename = (
        "events/METALGEAR_" + ("proliferation" if number < 60 else "incidents") + ".txt"
    )
    script.hidden_option(
        f"METALGEAR.{number}", f"METALGEAR.{number}.{letter}", filename
    )


def available(script, number, letter):
    filename = (
        "events/METALGEAR_" + ("proliferation" if number < 60 else "incidents") + ".txt"
    )
    return script.condition(
        next(
            body
            for key, _, body in _option(
                f"METALGEAR.{number}", f"METALGEAR.{number}.{letter}", filename
            )
            if key == "trigger"
        ),
        script.actor,
    )


def start_trail(script, tag):
    text = (ROOT / "common/decisions/METALGEAR_proliferation_decisions.txt").read_text(
        encoding="utf-8"
    )
    body = _parse_race_script(
        _named_block(_named_block(text, f"METALGEAR_pf_{tag}_trail"), "complete_effect")
    )["complete_effect"]
    script.actor = script.tag(tag)
    script.execute(body, script.actor)


@pytest.mark.parametrize("tag,number", [("USA", 50), ("JAP", 51), ("SOV", 52)])
@pytest.mark.parametrize("letter,policy", [("a", 1), ("b", 2), ("c", 3)])
def test_national_trail_has_a_real_delay_and_one_terminal_policy(
    tag, number, letter, policy
):
    script = ProliferationScript()
    start_trail(script, tag)
    assert script.globals["METALGEAR_capacity"] == (1 if tag == "USA" else 2)
    script.goto(2001, 2, 28)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_phase"] == 2
    script = deepcopy(script)
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, number, letter, tag)
    variables = script.countries[script.tag(tag)]["vars"]
    assert variables["METALGEAR_pf_policy"] == policy
    assert script.globals["METALGEAR_capacity"] == 2
    before = variables.copy(), script.globals.copy()
    choose(script, number, letter, tag)
    assert (variables, script.globals) == before


@pytest.mark.parametrize("tag", ["USA", "JAP", "SOV"])
def test_2005_cancels_unfinished_trail_and_abandonment_is_idempotent(tag):
    script = ProliferationScript()
    start_trail(script, tag)
    script.goto(2005, 1, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    script.run("METALGEAR_pf_interrupt", script.tag(tag))
    assert script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_phase"] == 5
    assert script.globals["METALGEAR_capacity"] == 2


@pytest.mark.parametrize(
    "japan,russia", [("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")]
)
def test_cooperation_requires_both_national_consents_and_returns_once(japan, russia):
    script = ProliferationScript()
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    choose(script, 54, japan, "JAP")
    choose(script, 55, russia, "SOV")
    assert script.globals["METALGEAR_capacity"] == 1
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, 56, "a")
    assert script.globals["METALGEAR_capacity"] == 2
    assert script.globals["METALGEAR_reach"] == 50 + 5 * (japan == "a") + 5 * (
        russia == "a"
    )
    before = script.globals.copy()
    choose(script, 56, "a")
    assert script.globals == before


@pytest.mark.parametrize("tag,number", [("JAP", 54), ("SOV", 55)])
@pytest.mark.parametrize("interruption", ["war", "annexation"])
def test_interrupted_partner_closes_without_canceling_other_country(
    tag, number, interruption
):
    script = ProliferationScript()
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    country = script.countries[script.tag(tag)]
    if interruption == "annexation":
        country["exists"] = False
    else:
        country["has_war_with"] = {1}
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, number, "a", tag)
    assert country["vars"]["METALGEAR_pf_exchange"] == 4
    other = script.tag("SOV" if tag == "JAP" else "JAP")
    assert script.countries[other]["vars"]["METALGEAR_pf_exchange"] == 1
    assert script.countries[1]["vars"]["METALGEAR_pf_inquiry"] == 2


def test_missing_shadow_records_still_dispatches_inquiry_and_both_incidents():
    script = ProliferationScript()
    script.goto(2006, 1, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert script.countries[1]["vars"]["METALGEAR_pf_inquiry"] == 1
    for year, case in [(2007, "tanker"), (2009, "shell")]:
        script.goto(year, 5, 1)
        script.run("METALGEAR_monthly_incidents_pulse", 1)
        assert script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] == 1


@pytest.mark.parametrize("case,brief,report", [("tanker", 59, 60), ("shell", 61, 62)])
@pytest.mark.parametrize("route,result", [("a", 1), ("b", 2), ("c", 3)])
def test_incident_routes_keep_separate_results_and_release_once(
    case, brief, report, route, result
):
    script = ProliferationScript()
    variables = script.countries[1]["vars"]
    variables[f"METALGEAR_pf_{case}_phase"] = 1
    choose(script, brief, route)
    assert script.globals["METALGEAR_capacity"] == (2 if route == "c" else 1)
    script = deepcopy(script)
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    choose(script, report, "a")
    variables = script.countries[1]["vars"]
    assert variables[f"METALGEAR_pf_{case}_result"] == result
    assert script.globals["METALGEAR_capacity"] == 2
    before = variables.copy(), script.globals.copy()
    choose(script, report, "b")
    assert (variables, script.globals) == before
    other = "tanker" if case == "shell" else "shell"
    assert f"METALGEAR_pf_{other}_result" not in variables


@pytest.mark.parametrize("brief,case", [(59, "tanker"), (61, "shell")])
def test_exhausted_capacity_or_lost_new_york_retains_emergency_authority(brief, case):
    script = ProliferationScript()
    script.actor = 1
    script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] = 1
    script.globals["METALGEAR_capacity"] = 0
    assert not available(script, brief, "a")
    assert not available(script, brief, "b")
    assert available(script, brief, "c")
    script.countries[769]["controller"] = 2
    choose(script, brief, "c")
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    assert script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] == 3
    assert script.globals["METALGEAR_capacity"] == 0


@pytest.mark.parametrize("case,brief", [("tanker", 59), ("shell", 61)])
def test_lost_site_or_host_releases_only_the_affected_commitment(case, brief):
    script = ProliferationScript()
    script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] = 1
    choose(script, brief, "a")
    script.countries[769]["controller"] = 2
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    assert script.globals["METALGEAR_capacity"] == 2
    assert script.countries[1]["vars"][f"METALGEAR_pf_{case}_route"] == 3


@pytest.mark.parametrize("prepared", [False, True])
@pytest.mark.parametrize("partners", [0, 1, 2])
def test_independent_authorization_checks_and_charges_the_actual_discounted_cost(
    prepared, partners
):
    script = ProliferationScript()
    script.actor = 1
    variables = script.countries[1]["vars"]
    variables.update(
        METALGEAR_pf_tanker_phase=1, METALGEAR_pf_inquiry_result=int(prepared)
    )
    for tag in ("JAP", "SOV")[:partners]:
        script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_exchange"] = 2
    price = (25 if prepared else 50) - 5 * partners
    variables["political_power"] = price - 1
    assert not available(script, 59, "a")
    variables["political_power"] = price
    assert available(script, 59, "a")
    choose(script, 59, "a")
    assert variables["political_power"] == 0
