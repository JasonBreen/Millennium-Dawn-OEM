import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


EFFECTS = _read("common/scripted_effects/99_FBC_polar_effects.txt")
EVENTS = _read("events/FBC_polar.txt")
LOC = _read("localisation/english/MD_FBC_polar_l_english.yml")


def _event(event_id):
    start = EVENTS.index(f"id = {event_id}\n")
    end = EVENTS.find("\ncountry_event = {", start)
    return EVENTS[start : end if end > 0 else len(EVENTS)]


def test_the_pulse_opens_one_case_at_a_working_tier_two_drilling_rig():
    pulse = _named_block(EFFECTS, "FBC_monthly_polar_pulse")
    assert "FBC_scenario_enabled = yes" in pulse
    assert "NOT = { has_global_flag = FBC_polar_case_open }" in pulse
    assert "NOT = { has_global_flag = FBC_polar_cooldown }" in pulse
    assert "array = global.at_members" in pulse
    assert "check_variable = { antarctica_lab_ice_tech_boost > 0 }" in pulse
    assert "chance = 2" in pulse
    assert "set_variable = { FBC_polar_station_id = FBC_polar_candidate }" in pulse
    find = _named_block(EFFECTS, "FBC_polar_find_drilling_station")
    assert "global.antarctica_station_tier^FBC_polar_station > 1" in find
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^FBC_polar_station = 12"
            in find
        )
    pulse_file = _read("common/scripted_effects/99_FBC_pulse_effects.txt")
    assert "FBC_monthly_polar_pulse = yes" in _named_block(
        pulse_file, "FBC_monthly_pulse"
    )


def test_every_ending_closes_the_case_and_releases_the_team():
    assert "set_global_flag = { flag = FBC_polar_cooldown value = 1 days = 1095 }" in (
        _named_block(EFFECTS, "FBC_polar_close_case")
    )
    for event_id in ("FBC.22", "FBC.24"):
        body = _event(event_id)
        assert "FBC_release_polar_team = yes" in body
        assert "FBC_polar_close_case = yes" in body
    seal = _event("FBC.20").split("name = FBC.20.b", 1)[0]
    assert "FBC_polar_close_case = yes" in seal
    decline = _event("FBC.21").split("name = FBC.21.b", 1)[1]
    assert "FBC_polar_close_case = yes" in decline
    assert "FROM = { country_event = FBC.23 }" in decline
    commit = _event("FBC.21").split("name = FBC.21.b", 1)[0]
    assert "check_variable = { FBC_response_capacity > 0 }" in commit
    assert "75 = { country_event = { id = FBC.22 days = 45 } }" in commit
    assert "25 = { country_event = { id = FBC.24 days = 45 } }" in commit


def test_a_breakout_damages_only_the_drilling_rig_through_antarctica():
    breakout = _named_block(EFFECTS, "FBC_polar_breakout")
    assert "global.antarctica_station_controller^station_id = THIS.id" in breakout
    assert breakout.count("antarctica_mark_blizzard_slot_damaged = yes") == 4
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^station_id = 12" in breakout
        )
    assert (
        "set_variable = { research_station_module_repair_days_remaining = 30 }"
        in breakout
    )
    assert "antarctica_recalculate_country_laboratory_effects = yes" in breakout
    assert "set_variable = { global.antarctica_station" not in breakout


def test_event_ids_stay_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = FBC\.(\d+)$", EVENTS)]
    assert sorted(ids) == [20, 21, 22, 23, 24]
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip) = (FBC[A-Za-z0-9_.]*)", EVENTS
    )
    keys.append("FBC_polar_core_findings")
    for key in keys:
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
