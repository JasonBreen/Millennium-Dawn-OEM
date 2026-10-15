from copy import deepcopy

import pytest
from ai_race_state_model_test import _named_block, _parse_race_script
from stalker_lifecycle_test import ROOT, StalkerScript, _option

EVENTS = "events/DEUSEX_corporate_cold_war.txt"
CRISIS_CASES = [("USA", 66), ("CHI", 67), ("GER", 68)]


class CorporateScript(StalkerScript):
    def __init__(self):
        super().__init__()
        for name in ("augmentation", "illuminati", "corporate_cold_war"):
            self.effects.update(
                _parse_race_script(
                    (
                        ROOT / f"common/scripted_effects/99_DEUSEX_{name}_effects.txt"
                    ).read_text(encoding="utf-8")
                )
            )
        self.triggers["DEUSEX_scenario_enabled"] = [("always", "=", "yes")]
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/99_DEUSEX_augmentation_triggers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/99_DEUSEX_illuminati_triggers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.stubs.add("modify_treasury_effect")
        self.globals.update(
            DEUSEX_illum_exposure=10,
            DEUSEX_illum_capital=40,
            DEUSEX_illum_media=30,
            DEUSEX_illum_security=30,
        )
        for tag in ("USA", "CHI", "GER"):
            self.countries[self.tag(tag)]["vars"].update(
                political_power=200,
                DEUSEX_program_phase=3,
                DEUSEX_illum_influence=20,
                DEUSEX_aug_adoption=20,
                DEUSEX_aug_unrest=0,
            )
        self.goto(2001, 1, 1)
        self.rolls = []

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "random":
            assert all(name != "modifier" for name, _, _ in operand)
            chance = self.value(
                next(value for name, _, value in operand if name == "chance"),
                identifier,
            )
            self.rolls.append(chance)
        elif key != "custom_effect_tooltip":
            super().execute_statement(statement, identifier)


def choose(script, number, letter, tag):
    script.actor = script.tag(tag)
    script.hidden_option(f"DEUSEX.{number}", f"DEUSEX.{number}.{letter}", EVENTS)


def option_allowed(script, number, letter, tag):
    body = _option(f"DEUSEX.{number}", f"DEUSEX.{number}.{letter}", EVENTS)
    script.actor = script.tag(tag)
    return script.condition(
        next(value for key, _, value in body if key == "trigger"), script.actor
    )


def decision(script, name, tag):
    text = (
        ROOT / "common/decisions/DEUSEX_corporate_cold_war_decisions.txt"
    ).read_text(encoding="utf-8")
    body = _parse_race_script(
        _named_block(_named_block(text, name), "complete_effect")
    )["complete_effect"]
    script.actor = script.tag(tag)
    script.execute(body, script.actor)


@pytest.mark.parametrize("tag,number", [("USA", 60), ("CHI", 61), ("GER", 62)])
@pytest.mark.parametrize("letter,policy", [("a", 1), ("b", 2), ("c", 3)])
def test_each_country_finishes_a_timed_case_and_keeps_one_historical_choice(
    tag, number, letter, policy
):
    script = CorporateScript()
    decision(script, f"DEUSEX_cc_{tag}_investigation", tag)
    variables = script.countries[script.tag(tag)]["vars"]
    assert variables["DEUSEX_cc_phase"] == 2
    script.goto(2001, 2, 28)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    assert variables["DEUSEX_cc_phase"] == 2
    script = deepcopy(script)
    script.goto(2001, 3, 2)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    choose(script, number, letter, tag)
    variables = script.countries[script.tag(tag)]["vars"]
    assert variables["DEUSEX_cc_policy"] == policy
    assert variables["DEUSEX_cc_phase"] == 4
    before = variables.copy(), script.globals.copy()
    choose(script, number, letter, tag)
    assert (variables, script.globals) == before
    assert variables["DEUSEX_aug_adoption"] == 20


@pytest.mark.parametrize("tag", ["USA", "CHI", "GER"])
def test_exclusive_reward_waits_for_an_existing_industry_and_never_creates_german_industry(
    tag,
):
    script = CorporateScript()
    identifier = script.tag(tag)
    variables = script.countries[identifier]["vars"]
    variables["DEUSEX_cc_policy"] = 3
    script.run("DEUSEX_cc_apply_arrangement", identifier)
    script.run("DEUSEX_cc_apply_arrangement", identifier)
    assert variables["DEUSEX_illum_influence"] == 30
    assert variables["DEUSEX_aug_adoption"] == 20
    assert "DEUSEX_aug_open" not in script.countries[identifier]["flags"]
    if tag != "GER":
        script.run("DEUSEX_open_augmentation_industry", identifier)
        script.run("DEUSEX_cc_apply_arrangement", identifier)
        assert variables["DEUSEX_aug_adoption"] == 30
        assert variables["DEUSEX_illum_influence"] == 30


@pytest.mark.parametrize(
    "sender,recipient,number",
    [("USA", "GER", 63), ("CHI", "USA", 64), ("GER", "CHI", 65)],
)
@pytest.mark.parametrize("letter,expected", [("a", 2), ("b", 3)])
def test_additional_exchange_requires_consent_and_cannot_reward_twice(
    sender, recipient, number, letter, expected
):
    script = CorporateScript()
    variables = script.countries[script.tag(sender)]["vars"]
    variables["DEUSEX_cc_policy"] = 2
    decision(script, f"DEUSEX_cc_{sender}_exchange", sender)
    assert "DEUSEX_cc_exchange_notice" in script.countries[script.tag(sender)]["flags"]
    choose(script, number, letter, recipient)
    assert variables["DEUSEX_cc_exchange"] == expected
    before = deepcopy(script.countries)
    choose(script, number, letter, recipient)
    assert script.countries == before


@pytest.mark.parametrize("reason", ["timeout", "annexation", "war"])
def test_interrupted_exchange_retains_national_case_and_rejects_stale_acceptance(
    reason,
):
    script = CorporateScript()
    variables = script.countries[1]["vars"]
    variables.update(DEUSEX_cc_policy=2, DEUSEX_cc_phase=4)
    decision(script, "DEUSEX_cc_USA_exchange", "USA")
    if reason == "timeout":
        script.goto(2001, 3, 2)
    elif reason == "annexation":
        script.countries[script.tag("GER")]["exists"] = False
    else:
        script.countries[1]["has_war_with"] = {script.tag("GER")}
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    choose(script, 63, "a", "GER")
    assert variables["DEUSEX_cc_exchange"] == 4
    assert variables["DEUSEX_cc_phase"] == 4


@pytest.mark.parametrize(
    "protocol,funded,chance",
    [(False, False, 4), (True, False, 4), (False, True, 4), (True, True, 2)],
)
def test_shortage_probability_changes_only_with_safety_and_active_funding(
    protocol, funded, chance
):
    script = CorporateScript()
    flags = script.countries[1]["flags"]
    if protocol:
        flags["DEUSEX_cc_safety_protocol"] = None
    if funded:
        flags["DEUSEX_aug_neuropozyne_funded"] = None
    script.run("DEUSEX_augmentation_month", 1)
    assert script.rolls == [chance]


def test_shortage_chance_resets_after_funding_ends_and_respects_existing_cooldown():
    script = CorporateScript()
    flags = script.countries[1]["flags"]
    flags.update(DEUSEX_cc_safety_protocol=None, DEUSEX_aug_neuropozyne_funded=None)
    script.run("DEUSEX_augmentation_month", 1)
    del flags["DEUSEX_aug_neuropozyne_funded"]
    script.run("DEUSEX_augmentation_month", 1)
    flags["DEUSEX_aug_shortage_cooldown"] = None
    script.run("DEUSEX_augmentation_month", 1)
    assert script.rolls == [2, 4]


@pytest.mark.parametrize("tag,number", CRISIS_CASES)
@pytest.mark.parametrize("prepared", [False, True])
def test_2027_safety_verification_requires_preexisting_preparation(
    tag, number, prepared
):
    script = CorporateScript()
    identifier = script.tag(tag)
    variables = script.countries[identifier]["vars"]
    variables["DEUSEX_cc_crisis"] = 1
    if prepared:
        script.countries[identifier]["flags"]["DEUSEX_cc_safety_protocol"] = None
    script.goto(2027, 1, 2)
    choose(script, number, "a", tag)
    script.goto(2027, 3, 3)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    assert variables["DEUSEX_cc_crisis"] == 4
    assert (
        "DEUSEX_cc_safety_verified" in script.countries[identifier]["flags"]
    ) == prepared


@pytest.mark.parametrize("adoption,loss", [(20, -0.03), (40, -0.06), (80, -0.1)])
@pytest.mark.parametrize("verified", [False, True])
def test_verified_safety_limits_stability_loss_without_removing_incident_unrest(
    adoption, loss, verified
):
    script = CorporateScript()
    variables = script.countries[1]["vars"]
    variables.update(DEUSEX_aug_adoption=adoption, stability=0.5)
    if verified:
        script.countries[1]["flags"]["DEUSEX_cc_safety_verified"] = None
    script.run("DEUSEX_aug_incident_damage", 1)
    assert variables["stability"] == pytest.approx(
        0.5 + loss + (0.02 if verified else 0)
    )
    assert variables["DEUSEX_aug_unrest"] == 40


def test_october_closes_unfinished_intervention_before_delayed_choice_can_execute():
    script = CorporateScript()
    script.goto(2027, 8, 2)
    script.countries[1]["vars"]["DEUSEX_cc_crisis"] = 1
    choose(script, 66, "a", "USA")
    script.goto(2027, 10, 2)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    assert script.countries[1]["vars"]["DEUSEX_cc_crisis"] == 5
    assert "DEUSEX_cc_crisis_wait" not in script.countries[1]["flags"]
    choose(script, 66, "b", "USA")
    assert script.countries[1]["vars"]["DEUSEX_cc_crisis"] == 5


def test_abandonment_and_disabled_pulse_cannot_grant_safety_or_corporate_rewards():
    script = CorporateScript()
    decision(script, "DEUSEX_cc_USA_investigation", "USA")
    script.run("DEUSEX_cc_abandon", 1)
    script.run("DEUSEX_cc_abandon", 1)
    script.goto(2027, 1, 2)
    script.triggers["DEUSEX_scenario_enabled"] = [("always", "=", "no")]
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    assert script.countries[1]["vars"]["DEUSEX_cc_phase"] == 5
    assert "DEUSEX_cc_crisis" not in script.countries[1]["vars"]


@pytest.mark.parametrize("tag,number", CRISIS_CASES)
@pytest.mark.parametrize("letter,prepared", [("b", False), ("b", True), ("c", False)])
def test_patient_protection_and_corporate_deference_costs_and_outcomes(
    tag, number, letter, prepared
):
    script = CorporateScript()
    identifier = script.tag(tag)
    variables = script.countries[identifier]["vars"]
    variables["DEUSEX_cc_crisis"] = 1
    price = (25 if prepared else 50) if letter == "b" else 0
    variables["political_power"] = price
    if prepared:
        script.countries[identifier]["flags"]["DEUSEX_cc_evidence"] = None
    script.goto(2027, 1, 2)
    choose(script, number, letter, tag)
    assert variables["political_power"] == 0
    script.goto(2027, 3, 3)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    assert variables["DEUSEX_cc_crisis"] == 4
    assert variables["DEUSEX_illum_influence"] == (10 if letter == "b" else 30)
    assert "DEUSEX_cc_safety_verified" not in script.countries[identifier]["flags"]


@pytest.mark.parametrize("tag,number", CRISIS_CASES)
@pytest.mark.parametrize("letter", ["a", "b"])
@pytest.mark.parametrize(
    "month,day,allowed",
    [(7, 2, True), (7, 3, False), (8, 2, False), (10, 1, False), (10, 2, False)],
)
def test_paid_interventions_require_a_full_runway_at_display_and_execution(
    tag, number, letter, month, day, allowed
):
    script = CorporateScript()
    identifier = script.tag(tag)
    script.countries[identifier]["vars"]["DEUSEX_cc_crisis"] = 1
    script.goto(2027, month, day)
    assert option_allowed(script, number, letter, tag) == allowed
    before = deepcopy(script.countries)
    choose(script, number, letter, tag)
    if allowed:
        assert script.countries[identifier]["vars"]["DEUSEX_cc_crisis"] == 2
        assert script.countries[identifier]["flags"]["DEUSEX_cc_crisis_wait"] == (
            script.globals["num_days"] + 60
        )
    else:
        assert script.countries == before


@pytest.mark.parametrize("tag,number", CRISIS_CASES)
@pytest.mark.parametrize("letter", ["a", "b"])
def test_latest_allowed_intervention_finishes_at_next_review_and_rewards_once(
    tag, number, letter
):
    script = CorporateScript()
    identifier = script.tag(tag)
    variables = script.countries[identifier]["vars"]
    variables["DEUSEX_cc_crisis"] = 1
    script.countries[identifier]["flags"]["DEUSEX_cc_safety_protocol"] = None
    script.goto(2027, 7, 2)
    choose(script, number, letter, tag)
    script.goto(2027, 9, 1)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    assert variables["DEUSEX_cc_crisis"] == 4
    script = deepcopy(script)
    script.goto(2027, 10, 1)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    country = script.countries[identifier]
    assert country["vars"]["DEUSEX_cc_crisis"] == 4
    assert "DEUSEX_cc_evidence" in country["flags"]
    assert ("DEUSEX_cc_safety_verified" in country["flags"]) == (letter == "a")
    assert country["vars"]["DEUSEX_illum_influence"] == (20 if letter == "a" else 10)
    before = deepcopy(country)
    script.goto(2027, 10, 2)
    script.run("DEUSEX_monthly_corporate_cold_war_pulse", 1)
    choose(script, number, letter, tag)
    assert script.countries[identifier] == before
    for other in {"USA", "CHI", "GER"} - {tag}:
        assert script.countries[script.tag(other)]["vars"]["DEUSEX_cc_crisis"] == 5


@pytest.mark.parametrize("tag,number", CRISIS_CASES)
@pytest.mark.parametrize("month,day", [(8, 3), (10, 1)])
def test_corporate_response_stays_available_after_intervention_deadline(
    tag, number, month, day
):
    script = CorporateScript()
    identifier = script.tag(tag)
    script.countries[identifier]["vars"]["DEUSEX_cc_crisis"] = 1
    script.goto(2027, month, day)
    assert option_allowed(script, number, "c", tag)
    choose(script, number, "c", tag)
    assert script.countries[identifier]["vars"]["DEUSEX_cc_crisis"] == 4
    assert script.countries[identifier]["vars"]["political_power"] == 200


@pytest.mark.parametrize(
    "sender,recipient,number",
    [("USA", "GER", 63), ("CHI", "USA", 64), ("GER", "CHI", 65)],
)
@pytest.mark.parametrize("balance", [-10, 0, 24])
def test_exchange_consent_can_charge_negative_political_power_once(
    sender, recipient, number, balance
):
    script = CorporateScript()
    script.countries[script.tag(sender)]["vars"]["DEUSEX_cc_policy"] = 2
    decision(script, f"DEUSEX_cc_{sender}_exchange", sender)
    variables = script.countries[script.tag(recipient)]["vars"]
    variables["political_power"] = balance
    assert option_allowed(script, number, "a", recipient)
    choose(script, number, "a", recipient)
    assert variables["political_power"] == balance - 25
    assert script.countries[script.tag(sender)]["vars"]["DEUSEX_cc_exchange"] == 2
    before = deepcopy(script.countries)
    choose(script, number, "a", recipient)
    assert script.countries == before


@pytest.mark.parametrize("tag,number", CRISIS_CASES)
@pytest.mark.parametrize("letter", ["a", "b"])
@pytest.mark.parametrize("evidence", [False, True])
@pytest.mark.parametrize("balance", [-10, 0, 24])
def test_crisis_choices_can_charge_negative_political_power_once(
    tag, number, letter, evidence, balance
):
    script = CorporateScript()
    script.goto(2027, 1, 2)
    identifier = script.tag(tag)
    variables = script.countries[identifier]["vars"]
    variables.update(DEUSEX_cc_crisis=1, political_power=balance)
    if evidence:
        script.countries[identifier]["flags"]["DEUSEX_cc_evidence"] = None
    assert option_allowed(script, number, letter, tag)
    choose(script, number, letter, tag)
    cost = 25 if letter == "a" or evidence else 50
    assert variables["political_power"] == balance - cost
    assert variables["DEUSEX_cc_crisis"] == 2
    before = deepcopy(script.countries)
    choose(script, number, letter, tag)
    assert script.countries == before


@pytest.mark.parametrize(
    "number,letter,tag",
    [(63, "a", "GER"), (64, "a", "USA"), (65, "a", "CHI")]
    + [(number, letter, tag) for tag, number in CRISIS_CASES for letter in ["a", "b"]],
)
def test_paid_choices_retain_positive_bankruptcy_ai_weights(number, letter, tag):
    script = CorporateScript()
    identifier = script.tag(tag)
    body = _option(f"DEUSEX.{number}", f"DEUSEX.{number}.{letter}", EVENTS)
    ai = next(value for key, _, value in body if key == "ai_chance")
    base = float(next(value for key, _, value in ai if key == "base"))
    modifier = next(
        value
        for key, _, value in ai
        if key == "modifier"
        and ("has_active_mission", "=", "bankruptcy_incoming_collapse") in value
    )
    conditions = [entry for entry in modifier if entry[0] != "factor"]
    assert not script.condition(conditions, identifier)
    script.countries[identifier]["missions"].add("bankruptcy_incoming_collapse")
    assert script.condition(conditions, identifier)
    factor = float(next(value for key, _, value in modifier if key == "factor"))
    assert 0 < base * factor < base
