from copy import deepcopy

import pytest
from ai_race_state_model_test import _named_block, _parse_race_script
from stalker_lifecycle_test import ROOT, StalkerScript, _option

EVENTS = "events/FBC_bright_falls.txt"


class BrightFallsScript(StalkerScript):
    def __init__(self):
        super().__init__()
        self.effects.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_effects/99_FBC_bright_falls_effects.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.research = []
        self.country(809, tag="WASHINGTON")
        self.countries[809]["controller"] = 1
        self.actor = 1
        self.countries[1]["vars"].update(
            FBC_response_capacity=2,
            FBC_containment_integrity=50,
            FBC_exposure=10,
            FBC_floor_knowledge=0,
            FBC_wing_knowledge=0,
            political_power=200,
        )
        self.goto(2000, 3, 1)
        self.run("FBC_monthly_bright_falls_pulse", 1)

    def execute_statement(self, statement, identifier):
        if statement[0] == "add_tech_bonus":
            self.research.append((identifier, statement[2]))
        elif statement[0] != "custom_effect_tooltip":
            super().execute_statement(statement, identifier)


def choose(script, number, letter):
    script.hidden_option(f"FBC.{number}", f"FBC.{number}.{letter}", EVENTS)


def option_allowed(script, number, letter):
    body = _option(f"FBC.{number}", f"FBC.{number}.{letter}", EVENTS)
    return script.condition(
        next(value for key, _, value in body if key == "trigger"), 1
    )


@pytest.mark.parametrize(
    "letter,evidence,capacity", [("a", 1, 2), ("b", 2, 1), ("c", 0, 2)]
)
def test_preparation_options_reserve_once_and_record_evidence_only_after_review(
    letter, evidence, capacity
):
    script = BrightFallsScript()
    choose(script, 50, letter)
    variables = script.countries[1]["vars"]
    assert variables["FBC_response_capacity"] == capacity
    assert variables["FBC_bf_evidence"] == 0
    before = variables.copy()
    choose(script, 50, letter)
    assert variables == before
    script = deepcopy(script)
    script.goto(2000, 4, 29)
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert script.countries[1]["vars"]["FBC_bf_phase"] == (4 if letter == "c" else 2)
    script.goto(2000, 5, 1)
    script.run("FBC_monthly_bright_falls_pulse", 1)
    if letter != "c":
        choose(script, 51, "a")
    variables = script.countries[1]["vars"]
    assert variables["FBC_bf_evidence"] == evidence
    assert variables["FBC_response_capacity"] == 2
    choose(script, 51, "a")
    assert variables["FBC_response_capacity"] == 2


def test_full_capacity_blocks_team_but_not_monitor_or_emergency_perimeter():
    script = BrightFallsScript()
    script.countries[1]["vars"]["FBC_response_capacity"] = 0
    assert not option_allowed(script, 50, "b")
    assert option_allowed(script, 50, "a")
    choose(script, 50, "b")
    assert script.countries[1]["vars"]["FBC_bf_phase"] == 1
    script.goto(2010, 1, 2)
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert not option_allowed(script, 52, "a")
    assert option_allowed(script, 52, "b")


def test_site_loss_pauses_days_releases_once_and_waits_for_a_team_on_return():
    script = BrightFallsScript()
    choose(script, 50, "b")
    script.goto(2000, 3, 21)
    script.countries[809]["controller"] = 2
    script.run("FBC_monthly_bright_falls_pulse", 1)
    variables = script.countries[1]["vars"]
    assert variables["FBC_bf_remaining"] == 40
    assert variables["FBC_response_capacity"] == 2
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert variables["FBC_response_capacity"] == 2
    script.goto(2001, 1, 1)
    script.countries[809]["controller"] = 1
    variables["FBC_response_capacity"] = 0
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert "FBC_bf_due" not in variables
    variables["FBC_response_capacity"] = 1
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert variables["FBC_bf_due"] == script.globals["num_days"] + 40
    assert variables["FBC_response_capacity"] == 0


@pytest.mark.parametrize("phase", [2, 3, 4])
def test_2010_closes_unanswered_preparation_without_inventing_evidence(phase):
    script = BrightFallsScript()
    choose(script, 50, "b")
    variables = script.countries[1]["vars"]
    variables["FBC_bf_phase"] = phase
    script.goto(2010, 1, 2)
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert variables["FBC_bf_phase"] == 5
    assert variables["FBC_bf_evidence"] == 0
    assert variables["FBC_response_capacity"] == 2
    assert "FBC_bf_due" not in variables


@pytest.mark.parametrize(
    "response,evidence,result",
    [("a", 0, 2), ("a", 1, 1), ("a", 2, 1), ("b", 0, 2), ("b", 2, 2), ("c", 2, 3)],
)
def test_crisis_endings_keep_canonical_disappearance_and_release_once(
    response, evidence, result
):
    script = BrightFallsScript()
    variables = script.countries[1]["vars"]
    variables.update(FBC_bf_phase=5, FBC_bf_evidence=evidence)
    choose(script, 52, response)
    script.goto(2000, 5, 1)
    script.run("FBC_monthly_bright_falls_pulse", 1)
    choose(script, 53, "a")
    assert variables["FBC_bf_result"] == result
    assert variables["FBC_response_capacity"] == 2
    before = variables.copy()
    choose(script, 53, "a")
    assert variables == before
    assert len(script.research) == int(result == 1)


@pytest.mark.parametrize("crisis", [False, True])
def test_withdrawal_closes_early_work_or_downgrades_crisis(crisis):
    script = BrightFallsScript()
    if crisis:
        script.countries[1]["vars"]["FBC_bf_phase"] = 5
        choose(script, 52, "a")
    else:
        choose(script, 50, "b")
    script.run("FBC_bf_withdraw", 1)
    script.run("FBC_bf_withdraw", 1)
    variables = script.countries[1]["vars"]
    assert variables["FBC_response_capacity"] == 2
    assert variables["FBC_bf_phase"] == (7 if crisis else 4)
    assert "FBC_bf_due" not in variables


def test_host_disappearance_returns_only_its_own_commitment():
    script = BrightFallsScript()
    script.run("FBC_commit_floor_team", 1)
    choose(script, 50, "b")
    script.countries[1]["exists"] = False
    script.run("FBC_monthly_bright_falls_pulse", 2)
    script.run("FBC_monthly_bright_falls_pulse", 2)
    variables = script.countries[1]["vars"]
    assert variables["FBC_bf_phase"] == 9
    assert variables["FBC_response_capacity"] == 1
    assert variables["FBC_floor_committed"] == 1


def test_recurring_review_does_not_reserve_teams_or_repeat_completion():
    script = BrightFallsScript()
    choose(script, 50, "c")
    text = (ROOT / "common/decisions/FBC_bright_falls_decisions.txt").read_text(
        encoding="utf-8"
    )
    body = _parse_race_script(
        _named_block(_named_block(text, "FBC_bf_records_review"), "complete_effect")
    )["complete_effect"]
    script.execute(body, 1)
    script.goto(2000, 5, 1)
    script.run("FBC_monthly_bright_falls_pulse", 1)
    variables = script.countries[1]["vars"]
    assert variables["FBC_bf_evidence"] == 1
    assert variables["FBC_response_capacity"] == 2
    before = variables.copy()
    script.run("FBC_monthly_bright_falls_pulse", 1)
    assert variables == before
    assert script.condition([("has_country_flag", "=", "FBC_bf_review_cooldown")], 1)


@pytest.mark.parametrize("evidence,price", [(0, 50), (1, 25), (2, 25)])
def test_field_authorization_checks_and_charges_its_discounted_cost(evidence, price):
    script = BrightFallsScript()
    variables = script.countries[1]["vars"]
    variables.update(
        FBC_bf_phase=5, FBC_bf_evidence=evidence, political_power=price - 1
    )
    assert not option_allowed(script, 52, "a")
    variables["political_power"] = price
    assert option_allowed(script, 52, "a")
    choose(script, 52, "a")
    assert variables["political_power"] == 0
