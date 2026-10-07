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
    member = pulse[pulse.index("array = global.at_members") :]
    assert "exists = yes" in _named_block(member, "limit")
    assert "add_to_temp_array = { FBC_polar_hits = THIS }" in member
    loop_end = pulse.index("check_variable = { FBC_polar_hits^num > 0 }")
    assert pulse.index("set_global_flag = FBC_polar_case_open") > loop_end
    assert (
        "set_global_flag = { flag = FBC_polar_case_watchdog value = 1 days = 60 }"
        in pulse[loop_end:]
    )
    assert pulse.index("country_event = FBC.20") > loop_end
    assert "array = FBC_polar_hits" in pulse[loop_end:]
    chosen = _named_block(pulse[loop_end:], "random_scope_in_array")
    assert chosen.index("FBC_polar_find_drilling_station = yes") < chosen.index(
        "set_variable = { FBC_polar_station_id = FBC_polar_candidate }"
    )
    assert "set_variable = { FBC_polar_country = PREV.id }" in chosen
    assert "USA = { has_variable = FBC_containment_integrity }" in pulse
    find = _named_block(EFFECTS, "FBC_polar_find_drilling_station")
    guard = find.index("check_variable = { FBC_polar_station > 0 }")
    assert guard < find.index("global.antarctica_station_tier^FBC_polar_station > 1")
    assert "global.antarctica_station_exists^FBC_polar_station > 0" in find
    assert "global.antarctica_station_controller^FBC_polar_station = THIS.id" in find
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^FBC_polar_station = 12"
            in find
        )
        assert (
            f"global.antarctica_station_module_slot_{slot}_blizzard_damaged^FBC_polar_station > 0"
            in find
        )
    assert "global.antarctica_station_output_fuel_usage^FBC_polar_station < 1" in find
    assert "global.antarctica_station_output_storage^FBC_polar_station > 0" in find
    assert "global.antarctica_station_output_power^FBC_polar_station" in find
    assert "NOT = { has_country_flag = FBC_polar_rig_down }" in find
    pulse_file = _read("common/scripted_effects/99_FBC_pulse_effects.txt")
    assert "FBC_monthly_polar_pulse = yes" in _named_block(
        pulse_file, "FBC_monthly_pulse"
    )


def test_every_ending_closes_the_case_and_releases_the_team():
    close = _named_block(EFFECTS, "FBC_polar_close_case")
    assert (
        "set_global_flag = { flag = FBC_polar_cooldown value = 1 days = 1095 }" in close
    )
    assert "clear_variable = FBC_polar_country" in _named_block(close, "USA")
    assert "clear_variable = FBC_polar_station_id" in _named_block(close, "USA")
    assert "clr_global_flag = FBC_polar_case_watchdog" in close
    assert "clear_variable = FBC_polar_country" not in EVENTS
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


def test_delayed_event_transitions_renew_the_case_watchdog():
    watchdog = (
        "set_global_flag = { flag = FBC_polar_case_watchdog value = 1 days = 60 }"
    )
    controller_choice = _event("FBC.20").split("name = FBC.20.b", 1)[1]
    usa_path = _named_block(controller_choice, "if")
    assert "limit = { country_exists = USA }" in usa_path
    assert usa_path.index(watchdog) < usa_path.index(
        "USA = { country_event = { id = FBC.21 days = 7 } }"
    )

    bureau_commit = _event("FBC.21").split("name = FBC.21.b", 1)[0]
    hidden_effect = _named_block(bureau_commit, "hidden_effect")
    assert hidden_effect.index("FBC_commit_polar_team = yes") < hidden_effect.index(
        watchdog
    )
    assert hidden_effect.index(watchdog) < hidden_effect.index("random_list = {")


def test_a_breakout_stops_only_the_rig_with_its_own_timer():
    breakout = _named_block(EFFECTS, "FBC_polar_breakout")
    assert (
        "set_country_flag = { flag = FBC_polar_rig_down value = 1 days = 31 }"
        in breakout
    )
    assert "country_event = { id = FBC.25 days = 30 }" in breakout
    back = _event("FBC.25")
    assert "hidden = yes" in back
    assert "clr_country_flag = FBC_polar_rig_down" in back
    assert "antarctica_recalculate_country_laboratory_effects = yes" in back
    assert "antarctica_recalculate_country_laboratory_effects = yes" in breakout
    for avoided in (
        "antarctica_mark_blizzard_slot_damaged",
        "research_station_module_repair_days_remaining",
        "global.antarctica_station",
    ):
        assert avoided not in breakout
    antarctica = _read("common/scripted_effects/00_antarctica_effects.txt")
    module = _named_block(
        antarctica, "antarctica_apply_single_laboratory_module_effect"
    )
    rig = module[module.index("check_variable = { station_lab_module = 12 }") :]
    gate = rig.index("NOT = { has_country_flag = FBC_polar_rig_down }")
    assert gate < rig.index("add_to_variable = { antarctica_lab_ice_tech_boost = 1 }")
    assert gate < rig.index(
        "add_to_variable = { antarctica_lab_cat_excavation_tech = 0.025 }"
    )
    reward = _named_block(
        antarctica, "antarctica_apply_single_laboratory_iteration_reward"
    )
    rig_reward = reward[reward.index("check_variable = { station_lab_module = 12 }") :]
    assert rig_reward.index(
        "NOT = { has_country_flag = FBC_polar_rig_down }"
    ) < rig_reward.index("category = CAT_excavation")
    progress = _named_block(antarctica, "antarctica_process_station_research_progress")
    down = progress.index(
        "var:station_controller = { has_country_flag = FBC_polar_rig_down }"
    )
    assert (
        progress.index("check_variable = { station_controller > 0 }", down - 200) < down
    )
    rig_lab = progress[
        down : progress.index(
            "add_to_temp_variable = { station_active_lab_slots = -1 }", down
        )
    ]
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^process_station_id = 12"
            in rig_lab
        )
        assert (
            f"global.antarctica_station_module_slot_{slot}_blizzard_damaged^process_station_id > 0"
            in rig_lab
        )
    assert down < progress.index(
        "set_temp_variable = { station_completed_iteration = 0 }"
    )


def test_a_lost_bureau_result_closes_the_case_and_returns_the_team():
    pulse = _named_block(EFFECTS, "FBC_monthly_polar_pulse")
    recovery = _named_block(pulse, "if")
    assert "has_global_flag = FBC_polar_case_open" in recovery
    assert "NOT = { country_exists = USA }" in recovery
    lost_owner = _named_block(recovery, "USA")
    assert "check_variable = { FBC_polar_committed < 1 }" in lost_owner
    assert lost_owner.index(
        "check_variable = { FBC_polar_country > 0 }"
    ) < lost_owner.index("var:FBC_polar_country = { exists = no }")
    assert "FROM = { exists = yes }" in _named_block(_event("FBC.21"), "trigger")
    assert "FBC_release_polar_team = yes" in recovery
    assert "FBC_polar_close_case = yes" in recovery
    assert "NOT = { has_global_flag = FBC_polar_case_watchdog }" in recovery


def test_every_event_is_gated_and_bureau_factors_refresh_after_changes():
    for event_id in ("FBC.20", "FBC.21", "FBC.22", "FBC.23", "FBC.24", "FBC.25"):
        head = _event(event_id).split("option", 1)[0]
        assert "FBC_scenario_enabled = yes" in _named_block(head, "trigger")
    for body in (
        _event("FBC.21").split("name = FBC.21.b", 1)[1],
        _event("FBC.22"),
        _event("FBC.24"),
    ):
        assert body.index("FBC_clamp_bureau = yes") < body.index(
            "FBC_refresh_bureau_factors = yes"
        )
    seal = _event("FBC.20").split("name = FBC.20.b", 1)[0]
    assert "has_political_power" not in seal
    assert "has_active_mission = bankruptcy_incoming_collapse" in seal


def test_event_ids_stay_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = FBC\.(\d+)$", EVENTS)]
    assert sorted(ids) == [20, 21, 22, 23, 24, 25]
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip) = (FBC[A-Za-z0-9_.]*)", EVENTS
    )
    keys.append("FBC_polar_core_findings")
    for key in keys:
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key


def test_delayed_results_land_only_on_the_station_the_case_opened_on():
    triggers = _read("common/scripted_triggers/99_FBC_scripted_triggers.txt")
    stands = _named_block(triggers, "FBC_polar_case_rig_stands")
    assert "global.antarctica_station_exists^FBC_polar_station_id > 0" in stands
    assert (
        "global.antarctica_station_controller^FBC_polar_station_id = FBC_polar_country"
        in stands
    )
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^FBC_polar_station_id = 12"
            in stands
        )
        assert (
            f"global.antarctica_station_module_slot_{slot}_blizzard_damaged^FBC_polar_station_id > 0"
            in stands
        )
    assert (
        "global.antarctica_station_output_fuel_usage^FBC_polar_station_id < 1" in stands
    )
    assert "global.antarctica_station_output_storage^FBC_polar_station_id > 0" in stands
    assert "global.antarctica_station_output_power^FBC_polar_station_id" in stands
    exists_guard = "var:FBC_polar_country = { exists = yes }"
    rig_down_guard = (
        "var:FBC_polar_country = { NOT = { has_country_flag = FBC_polar_rig_down } }"
    )
    assert exists_guard in stands
    assert stands.index(exists_guard) < stands.index(rig_down_guard)
    for body, result in (
        (
            _event("FBC.21").split("name = FBC.21.b", 1)[1],
            "FROM = { country_event = FBC.23 }",
        ),
        (_event("FBC.22"), "add_tech_bonus"),
        (_event("FBC.24"), "var:FBC_polar_country = { country_event = FBC.23 }"),
    ):
        assert body.index("limit = { FBC_polar_case_rig_stands = yes }") < body.index(
            result
        )


def test_result_tooltips_match_whether_the_original_rig_still_works():
    for event_id, regular, stale in (
        ("FBC.21", "FBC.21.b_tt", "FBC_polar_stale_breakout_tt"),
        ("FBC.22", "FBC.22.a_tt", "FBC_polar_stale_containment_tt"),
        ("FBC.24", "FBC.24.a_tt", "FBC_polar_stale_failure_tt"),
    ):
        body = _event(event_id)
        if event_id == "FBC.21":
            body = body.split("name = FBC.21.b", 1)[1]
        assert "limit = { FBC_polar_case_rig_stands = yes }" in body
        assert f"custom_effect_tooltip = {regular}" in body
        assert f"custom_effect_tooltip = {stale}" in body
