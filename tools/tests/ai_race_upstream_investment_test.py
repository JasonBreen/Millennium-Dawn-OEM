"""Check the AI Race savings boundary and the generation-bound investment offer guard."""

import re
from pathlib import Path

import pytest
from ai_race_state_model_test import RaceScript, _parse_race_script

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = ROOT / "common/scripted_effects/99_investment_scripted_effects.txt"
EVENTS = ROOT / "events/investments_events.txt"
TRIGGERS = ROOT / "common/scripted_triggers/00_investment_scripted_triggers.txt"
PROGRESSION = ROOT / "common/scripted_effects/03_ai_race_progression_effects.txt"


def _propose_source():
    text = EFFECTS.read_text(encoding="utf-8")
    start = text.index("investment_ai_propose_project = {")
    return text[start : text.index("\n}\n", start)]


def test_purchase_waits_for_the_generation_bound_offer():
    triggers = TRIGGERS.read_text(encoding="utf-8")
    progression = PROGRESSION.read_text(encoding="utf-8")
    assert re.search(
        r"investment_ai_offer_pending\s*=\s*\{\s*"
        r"check_variable\s*=\s*\{\s*investment_ai_offer_target\s*>\s*0\s*\}\s*\}",
        triggers,
    )
    assert "NOT = { investment_ai_offer_pending = yes }" in progression
    source = _propose_source()
    assert "NOT = { investment_ai_offer_pending = yes }" in source
    assert "check_variable = { investment_ai_offer_generation < 2097151 }" in source


def test_offer_is_recorded_before_it_is_sent():
    source = _propose_source()
    assert source.index("investment_ai_record_offer = yes") < source.index(
        "country_event = investments_event.3"
    )
    events = EVENTS.read_text(encoding="utf-8")
    assert "investment_ai_offer_matches_context = yes" in events
    assert "investment_ai_propose_project = yes" in events


def test_investment_quotes_before_testing_race_reserve():
    source = _propose_source()
    spendable = source.index(
        "set_temp_variable = { investment_ai_spendable_cash = treasury }"
    )
    assert source.index("project_monetary_cost_calculation = yes") < spendable
    assert source.index("calculate_project_duration = yes") < spendable
    assert spendable < source.index(
        "check_variable = { var = investment_ai_spendable_cash value = project_monetary_cost^-1 compare = greater_than_or_equals }"
    )


@pytest.mark.parametrize(
    "treasury,reserve,active,expected",
    [
        (61.999, 50, True, False),
        (62, 50, True, True),
        (11.999, 50, False, False),
        (12, 50, False, True),
    ],
)
def test_source_affordability_preserves_live_race_reserve(
    treasury, reserve, active, expected
):
    source = _propose_source()
    start = source.index(
        "set_temp_variable = { investment_ai_spendable_cash = treasury }"
    )
    compare = source.index(
        "check_variable = { var = investment_ai_spendable_cash value = project_monetary_cost^-1"
    )
    end = source.rindex("if = {", start, compare)
    statements = _parse_race_script(f"offer = {{ {source[start:end]} }}")["offer"]
    check = _parse_race_script(
        "guard = { check_variable = { var = investment_ai_spendable_cash "
        "value = project_monetary_cost^-1 compare = greater_than_or_equals } }"
    )["guard"]

    model = RaceScript()
    country = model.country(1, ai=True)
    country["vars"].update(
        treasury=treasury,
        ai_race_ai_savings_target=reserve,
        **{"project_monetary_cost^-1": 12},
    )
    model.triggers["ai_race_ai_expansion_permitted"] = [
        ("always", "=", "yes" if active else "no")
    ]
    model.execute(statements, 1)
    assert model.condition(check, 1) is expected
