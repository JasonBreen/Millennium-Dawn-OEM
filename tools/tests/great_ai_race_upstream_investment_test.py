"""Check the AI Race savings boundary against upstream investment ownership."""

import re
from pathlib import Path

import pytest
from great_ai_race_state_model_test import RaceScript, _parse_race_script

ROOT = Path(__file__).resolve().parents[2]
EVENTS = ROOT / "events/investments_events.txt"
TRIGGERS = ROOT / "common/scripted_triggers/00_investment_scripted_triggers.txt"
PROGRESSION = ROOT / "common/scripted_effects/03_great_ai_race_progression_effects.txt"


def _offer_source():
    text = EVENTS.read_text(encoding="utf-8")
    start = text.index("id = investments_event.500")
    return text[start:]


def test_purchase_waits_for_the_existing_upstream_offer_lock():
    triggers = TRIGGERS.read_text(encoding="utf-8")
    progression = PROGRESSION.read_text(encoding="utf-8")
    assert re.search(
        r"investment_ai_offer_pending\s*=\s*\{\s*"
        r"has_country_flag\s*=\s*investments_ai_pending\s*\}",
        triggers,
    )
    assert "NOT = { investment_ai_offer_pending = yes }" in progression


def test_investment_quotes_before_testing_race_reserve():
    source = _offer_source()
    assert source.index("project_monetary_cost_calculation = yes") < source.index(
        "set_temp_variable = { investment_ai_spendable_cash = treasury }"
    )
    assert source.index("calculate_project_duration = yes") < source.index(
        "set_temp_variable = { investment_ai_spendable_cash = treasury }"
    )
    assert source.index(
        "set_temp_variable = { investment_ai_spendable_cash = treasury }"
    ) < source.index(
        "check_variable = { var = investment_ai_spendable_cash value = project_monetary_cost^-1 compare = greater_than_or_equals }"
    )
    assert source.index(
        "limit = { check_variable = { investment_ai_reserve_blocked = 0 } }"
    ) < source.index("Investment deferred to protect AI Race savings.")


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
    source = _offer_source()
    start = source.index(
        "set_temp_variable = { investment_ai_spendable_cash = treasury }"
    )
    end = source.index("# Log Values", start)
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
