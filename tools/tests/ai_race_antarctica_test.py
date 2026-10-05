import pytest
from ai_race_state_model_test import (
    EFFECTS_PATH,
    RACE_LOC_PATH,
    ROOT,
    RaceScript,
    _named_block,
)

STATION = 7


class StationRaceScript(RaceScript):
    """Reads Antarctica's per-station global arrays by index, as `array^index`."""

    def value(self, name, identifier):
        if isinstance(name, str) and "^" in name and not name.endswith("^num"):
            array, index = name.split("^", 1)
            return self.value(array, identifier)[int(self.value(index, identifier))]
        return super().value(name, identifier)


def _station_race(*, lab_ai=0.034, tier=1):
    race = StationRaceScript()
    country = race.country(1)
    variables = country["vars"]
    variables.update(
        antarctica_lab_cat_ai=lab_ai,
        country_owned_station_ids=[STATION],
        ai_race_capability_external=10,
    )
    race.globals["antarctica_station_tier"] = [0] * STATION + [tier]
    return race, variables


@pytest.mark.parametrize("tier,expected", [(1, 2), (2, 4), (3, 6), (4, 6)])
def test_a_working_quantum_vault_adds_capability_by_station_tier(tier, expected):
    race, variables = _station_race(tier=tier)
    race.run("ai_race_antarctica_contribution", 1)
    assert variables["ai_race_capability_antarctica"] == expected
    assert variables["ai_race_capability_external"] == 10 + expected


def test_no_working_vault_adds_nothing_and_clears_the_last_reading():
    race, variables = _station_race(lab_ai=0, tier=3)
    variables["ai_race_capability_antarctica"] = 6
    race.run("ai_race_antarctica_contribution", 1)
    assert "ai_race_capability_antarctica" not in variables
    assert variables["ai_race_capability_external"] == 10


def test_the_contribution_runs_after_the_lab_overlay_and_before_the_totals():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    call = metrics.index("ai_race_antarctica_contribution = yes")
    assert metrics.rindex("ai_race_capability_lab_overlay") < call
    assert call < metrics.index(
        "set_variable = { ai_race_capability = ai_race_capability_stock }"
    )
    assert "clear_variable = ai_race_capability_antarctica" in _named_block(
        effects, "ai_race_clear_country_state"
    )
    loc = RACE_LOC_PATH.read_text(encoding="utf-8-sig")
    assert loc.count("[?ROOT.ai_race_capability_antarctica|1]") == 2


def test_a_racing_ai_builds_the_quantum_vault_first():
    ai = (ROOT / "common/scripted_effects/00_antarctica_ai_effects.txt").read_text(
        encoding="utf-8"
    )
    pick = ai.index("set_temp_variable = { ai_antarctica_module_pick = 11 }")
    hook = ai[ai.rindex("if = {", 0, pick) : pick]
    assert "ai_race_active = yes" in hook
    assert "selected_antarctica_station_selected_module_category = 5" in hook
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^player_station_id = 11"
            in hook
        )
    assert pick < ai.index("antarctica_queue_selected_station_module_install = yes")
