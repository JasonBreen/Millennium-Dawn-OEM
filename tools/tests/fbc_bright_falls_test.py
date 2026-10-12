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
        self.country(764, tag="MAINE")
        self.countries[764]["controller"] = 1
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


@pytest.mark.parametrize(
    "number,letter,evidence,price,phase,capacity",
    [
        (50, "a", 0, 25, 2, 2),
        (50, "b", 0, 50, 2, 1),
        (52, "a", 0, 50, 6, 1),
        (52, "a", 1, 25, 6, 1),
        (52, "a", 2, 25, 6, 1),
        (52, "b", 0, 50, 6, 2),
    ],
)
@pytest.mark.parametrize("balance", [-20, 0, 24, 49, 50])
def test_paid_options_allow_negative_power_and_charge_once(
    number, letter, evidence, price, phase, capacity, balance
):
    script = BrightFallsScript()
    variables = script.countries[1]["vars"]
    variables.update(
        FBC_bf_phase=1 if number == 50 else 5,
        FBC_bf_evidence=evidence,
        political_power=balance,
    )
    assert option_allowed(script, number, letter)
    choose(script, number, letter)
    assert variables["political_power"] == balance - price
    assert variables["FBC_bf_phase"] == phase
    assert variables["FBC_response_capacity"] == capacity
    before = variables.copy()
    choose(script, number, letter)
    assert variables == before


def ai_weight(script, body):
    weight = float(next(value for key, _, value in body if key == "base"))
    for key, _, modifier in body:
        if key != "modifier":
            continue
        conditions = [entry for entry in modifier if entry[0] not in {"factor", "add"}]
        if script.condition(conditions, 1):
            for name, _, value in modifier:
                if name == "factor":
                    weight *= float(value)
                elif name == "add":
                    weight += float(value)
    return weight


def withdrawal_ai_weight(script):
    text = (ROOT / "common/decisions/FBC_bright_falls_decisions.txt").read_text(
        encoding="utf-8"
    )
    body = _parse_race_script(
        _named_block(_named_block(text, "FBC_bf_withdraw_team"), "ai_will_do")
    )["ai_will_do"]
    return ai_weight(script, body)


@pytest.mark.parametrize("number,letter", [(50, "a"), (50, "b"), (52, "a"), (52, "b")])
def test_paid_options_keep_positive_but_reduced_bankruptcy_weights(number, letter):
    script = BrightFallsScript()
    body = next(
        value
        for key, _, value in _option(f"FBC.{number}", f"FBC.{number}.{letter}", EVENTS)
        if key == "ai_chance"
    )
    normal = ai_weight(script, body)
    script.countries[1]["missions"].add("bankruptcy_incoming_collapse")
    assert 0 < ai_weight(script, body) < normal


@pytest.mark.parametrize("phase", range(10))
@pytest.mark.parametrize("controlled", [False, True])
def test_dashboard_pauses_only_active_cases_when_washington_is_lost(phase, controlled):
    script = BrightFallsScript()
    script.countries[1]["vars"]["FBC_bf_phase"] = phase
    script.countries[809]["controller"] = 1 if controlled else 2
    text = (
        ROOT
        / "common/scripted_localisation/99_FBC_bright_falls_scripted_localisation.txt"
    ).read_text(encoding="utf-8")
    definitions = _parse_race_script("source = {" + text + "}")["source"]
    status = next(
        body for _, _, body in definitions if ("name", "=", "FBC_bf_status") in body
    )
    for key, _, body in status:
        if key != "text":
            continue
        trigger = next((value for name, _, value in body if name == "trigger"), [])
        if script.condition(trigger, 1):
            actual = next(
                value for name, _, value in body if name == "localization_key"
            )
            break
    expected = f"FBC_bf_phase_{phase}" if phase else "FBC_bf_dormant"
    if not controlled and 0 < phase < 8:
        expected = "FBC_bf_paused"
    assert actual == expected


@pytest.mark.parametrize("exposure", [10, 80])
@pytest.mark.parametrize(
    "capacity,case,phase,committed,expected",
    [
        (1, "floor", 1, 0, 1),
        (0, "floor", 0, 0, 1),
        (0, "floor", 1, 0, 13),
        (0, "floor", 3, 0, 13),
        (0, "floor", 4, 0, 1),
        (0, "floor", 2, 1, 1),
        (0, "wing", 1, 0, 13),
        (0, "wing", 3, 0, 13),
        (0, "wing", 5, 0, 1),
        (0, "wing", 2, 1, 1),
    ],
)
def test_ai_withdrawal_rises_only_for_a_case_waiting_on_exhausted_capacity(
    exposure, capacity, case, phase, committed, expected
):
    script = BrightFallsScript()
    choose(script, 50, "b")
    script.countries[1]["vars"].update(
        {
            "FBC_exposure": exposure,
            "FBC_response_capacity": capacity,
            f"FBC_{case}_phase": phase,
            f"FBC_{case}_committed": committed,
        }
    )
    assert withdrawal_ai_weight(script) == expected


@pytest.mark.parametrize(
    "overrides,controlled,ended,pending,expected",
    [
        ({}, True, False, False, 13),
        ({"FBC_response_capacity": 1}, True, False, False, 1),
        ({"FBC_sh_phase": 0}, True, False, False, 1),
        ({"FBC_sh_phase": 1}, True, False, False, 1),
        ({"FBC_sh_phase": 3}, True, False, False, 1),
        ({"FBC_sh_intervention": 2}, True, False, False, 1),
        ({"FBC_sh_intervention": 3}, True, False, False, 1),
        ({"FBC_sh_committed": 1}, True, False, False, 1),
        ({}, False, False, False, 1),
        ({}, True, True, False, 1),
        ({}, True, False, True, 1),
    ],
)
def test_ai_withdrawal_counts_only_resumable_silent_hill_team_interventions(
    overrides, controlled, ended, pending, expected
):
    script = BrightFallsScript()
    choose(script, 50, "b")
    script.countries[764]["controller"] = 1 if controlled else 2
    script.countries[1]["vars"].update(
        FBC_response_capacity=0,
        FBC_sh_phase=2,
        FBC_sh_intervention=1,
        FBC_sh_committed=0,
    )
    script.countries[1]["vars"].update(overrides)
    if ended:
        script.global_flags["FBC_sh_ended"] = None
    if pending:
        script.countries[1]["flags"]["FBC_sh_ending_pending"] = None
    assert withdrawal_ai_weight(script) == expected
