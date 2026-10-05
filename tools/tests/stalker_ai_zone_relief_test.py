import re

import pytest
from ai_race_state_model_test import _named_block
from stalker_lifecycle_test import ROOT, StalkerScript

ZONE = 698
RELIEF_DAYS = 180


def _zone(*, ai=True, political_power=10, containment=20, breach=False, mission=None):
    script = StalkerScript()
    script.globals["STALKER_active_zone_anchors"] = [ZONE]
    state = script.countries[ZONE]
    state["vars"].update(
        STALKER_zone_containment=containment,
        STALKER_zone_activity=90,
        STALKER_zone_exploitation=40,
    )
    if breach:
        state["flags"]["STALKER_perimeter_breach_active"] = None
    holder_id = state["controller"]
    holder = script.countries[holder_id]
    holder["ai"] = ai
    holder["vars"]["political_power"] = political_power
    if mission:
        holder["missions"].add(mission)
    return script, state, holder_id


def _relieved(script, holder_id):
    return script.external["small_expenditure", holder_id]


def test_a_broke_ai_zone_in_crisis_is_reinforced_and_paid_from_the_treasury():
    script, state, holder_id = _zone()
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)

    assert state["vars"]["STALKER_zone_containment"] == 40
    assert state["vars"]["STALKER_zone_activity"] == 80
    assert _relieved(script, holder_id) == 1
    assert (
        state["flags"]["STALKER_ai_zone_relief_cooldown"]
        == script.globals["num_days"] + RELIEF_DAYS
    )


def test_a_perimeter_breach_counts_as_a_crisis_above_30_containment():
    script, state, holder_id = _zone(containment=50, breach=True)
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == 70
    assert _relieved(script, holder_id) == 1


def test_relief_waits_out_its_cooldown():
    script, state, holder_id = _zone()
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    state["vars"]["STALKER_zone_containment"] = 10
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == 10
    assert _relieved(script, holder_id) == 1


@pytest.mark.parametrize(
    "case",
    [
        {"ai": False},
        {"political_power": 50},
        {"containment": 30},
        {"mission": "bankruptcy_incoming_collapse"},
    ],
    ids=["player", "can_afford_the_decision", "not_in_crisis", "near_bankruptcy"],
)
def test_no_relief_outside_a_broke_ai_crisis(case):
    script, state, holder_id = _zone(**case)
    before = state["vars"]["STALKER_zone_containment"]
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == before
    assert _relieved(script, holder_id) == 0
    assert "STALKER_ai_zone_relief_cooldown" not in state["flags"]


def test_no_relief_while_the_zone_policy_is_pending():
    script, state, holder_id = _zone()
    state["flags"]["STALKER_zone_policy_pending"] = None
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert _relieved(script, holder_id) == 0


def test_relief_runs_from_the_monthly_pulse_and_matches_the_decision():
    pulse = (ROOT / "common/scripted_effects/99_STALKER_pulse_effects.txt").read_text(
        encoding="utf-8"
    )
    assert (
        _named_block(pulse, "STALKER_monthly_pulse").count(
            "STALKER_monthly_ai_zone_relief_pulse = yes"
        )
        == 1
    )
    decision = _named_block(
        (ROOT / "common/decisions/STALKER_decisions.txt").read_text(encoding="utf-8"),
        "STALKER_reinforce_zone_containment",
    )
    cost = int(re.search(r"\n\t\tcost = (\d+)", decision).group(1))
    cooldown = int(re.search(r"days_re_enable = (\d+)", decision).group(1))
    effects = (
        ROOT / "common/scripted_effects/99_STALKER_scripted_effects.txt"
    ).read_text(encoding="utf-8")
    relief = _named_block(effects, "STALKER_monthly_ai_zone_relief_pulse")
    assert f"has_political_power < {cost}" in relief
    assert f"days = {cooldown}" in relief
    assert "small_expenditure = yes" in decision and "small_expenditure = yes" in relief
