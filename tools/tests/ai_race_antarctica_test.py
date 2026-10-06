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


def test_a_dismantled_station_tombstone_is_skipped():
    race, variables = _station_race(tier=1)
    variables["country_owned_station_ids"] = [-1, STATION]
    race.globals["antarctica_station_tier"] = [0] * STATION + [1, 3]
    race.run("ai_race_antarctica_contribution", 1)
    assert variables["ai_race_capability_antarctica"] == 2


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


def test_a_racing_ai_with_full_laboratories_swaps_one_for_the_vault():
    ai = (ROOT / "common/scripted_effects/00_antarctica_ai_effects.txt").read_text(
        encoding="utf-8"
    )
    monthly = _named_block(ai, "ai_antarctica_monthly")
    assert monthly.index("ai_install_station_module_in_empty_slot = yes") < (
        monthly.index("ai_antarctica_swap_in_quantum_vault = yes")
    )
    swap = _named_block(ai, "ai_antarctica_swap_in_quantum_vault")
    assert "ai_race_active = yes" in swap
    assert (
        "NOT = { check_variable = { global.antarctica_station_install_pending^player_station_id > 0 } }"
        in swap
    )
    for slot in range(6, 10):
        assert (
            f"NOT = {{ check_variable = {{ global.antarctica_station_module_slot_{slot}^player_station_id = 11 }} }}"
            in swap
        )
    assert swap.count("antarctica_station_slot_unlocked_by_tier = yes") == 4
    assert "check_variable = { ai_vault_empty_lab = 0 }" in swap
    assert "set_variable = { selected_antarctica_station_selected_module = 11 }" in swap
    for check in (
        "antarctica_is_module_researched = yes",
        "antarctica_can_install_module_power_balance = yes",
        "antarctica_can_install_module_staff_availability = yes",
        "antarctica_can_install_module_no_duplicate_laboratories = yes",
        "antarctica_station_selected_slot_module_different = yes",
    ):
        assert check in swap
    assert swap.index("selected_antarctica_station_selected_module = 11") < swap.index(
        "antarctica_queue_selected_station_module_install = yes"
    )
