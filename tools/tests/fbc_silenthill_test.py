import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


EFFECTS = _read("common/scripted_effects/99_FBC_silenthill_effects.txt")
EVENTS = _read("events/FBC_silenthill.txt")
LOC = _read("localisation/english/MD_FBC_silenthill_l_english.yml")


def _event(event_id):
    start = EVENTS.index(f"id = {event_id}\n")
    end = EVENTS.find("\n\n# ", start)
    return EVENTS[start : end if end > 0 else len(EVENTS)]


def test_the_case_runs_from_the_bureau_pulse_once_the_bureau_exists():
    pulses = _named_block(
        _read("common/scripted_effects/99_FBC_pulse_effects.txt"), "FBC_monthly_pulse"
    )
    assert "FBC_monthly_silenthill_pulse = yes" in pulses
    pulse = _named_block(EFFECTS, "FBC_monthly_silenthill_pulse")
    assert "FBC_scenario_enabled = yes" in pulse
    assert "USA = { has_variable = FBC_containment_integrity }" in pulse
    setup = pulse[pulse.index("NOT = { has_global_flag = FBC_sh_ready }") :]
    assert setup.index("FBC_update_silenthill_fog = yes") < setup.index(
        "add_dynamic_modifier = { modifier = FBC_silent_hill_fog }"
    )
    assert "764 = {" in setup


def test_the_fog_drives_the_state_modifier():
    modifiers = _read(
        "common/dynamic_modifiers/00_FBC_silenthill_dynamic_modifiers.txt"
    )
    fog = _named_block(modifiers, "FBC_silent_hill_fog")
    update = _named_block(EFFECTS, "FBC_update_silenthill_fog")
    variables = re.findall(r"= (FBC_sh_[a-z_]+_factor)", fog)
    assert len(variables) == 4
    for variable in variables:
        assert f"set_variable = {{ {variable} = " in update, variable
    assert update.index(
        "clamp_variable = { var = FBC_sh_fog min = 0 max = 100 }"
    ) < update.index("FBC_sh_supply_factor")
    month = _named_block(EFFECTS, "FBC_silenthill_fog_month")
    assert "check_variable = { FBC_sh_committed > 0 }" in month
    assert "check_variable = { FBC_sh_intervention = 3 }" in month


def test_reports_come_at_25_fog_and_the_town_answers_each_intervention():
    case = _named_block(EFFECTS, "FBC_silenthill_case_month")
    report = case[: case.index("else_if")]
    assert "check_variable = { FBC_sh_fog > 24 }" in report
    assert "is_controlled_by = USA" in report
    assert "country_event = { id = FBC.30 days = 1 }" in report
    answer = case[case.index("else_if") :]
    assert "60 = { country_event = { id = FBC.31 days = 1 } }" in answer
    assert "40 = { country_event = { id = FBC.32 days = 1 } }" in answer
    assert "country_event = { id = FBC.33 days = 1 }" in answer
    assert "country_event = { id = FBC.34 days = 1 }" in answer
    paused = case[case.rindex("else_if") :]
    assert "FBC_release_silenthill_team = yes" in paused
    for option, choice, delay in (("a", 1, 6), ("b", 2, 8), ("c", 3, 10)):
        body = _event("FBC.30").split(f"name = FBC.30.{option}", 1)[1]
        body = body.split("option = {", 1)[0]
        assert f"set_temp_variable = {{ FBC_sh_choice = {choice} }}" in body
        assert f"set_temp_variable = {{ FBC_sh_delay = {delay} }}" in body
        assert "FBC_silenthill_intervene = yes" in body


def test_a_team_is_committed_and_always_released():
    first = _event("FBC.30").split("name = FBC.30.b", 1)[0]
    assert "check_variable = { FBC_response_capacity > 0 }" in first
    assert "FBC_commit_silenthill_team = yes" in first
    for event_id in ("FBC.31", "FBC.32"):
        for option in _event(event_id).split("option = {")[1:]:
            assert "FBC_release_silenthill_team = yes" in option
    release = _named_block(EFFECTS, "FBC_release_silenthill_team")
    assert "clamp_variable = { var = FBC_response_capacity min = 0 max = 2 }" in release


def test_bureau_changes_are_clamped_and_refreshed():
    for match in re.finditer(
        r"add_to_variable = \{ FBC_(exposure|containment_integrity) = ", EVENTS
    ):
        following = EVENTS[match.end() : match.end() + 300]
        assert "FBC_clamp_bureau = yes" in following
        assert "FBC_refresh_bureau_factors = yes" in following


def test_the_dashboard_shows_the_case():
    core = _read("localisation/english/MD_FBC_l_english.yml")
    line = re.search(r'(?m)^ FBC_bureau_category_desc: "(.*)"$', core).group(1)
    assert "[FBC_sh_case_status] [FBC_sh_fog_band]" in line
    sloc = _read(
        "common/scripted_localisation/99_FBC_silenthill_scripted_localisation.txt"
    )
    for key in re.findall(r"localization_key = (FBC_sh_[a-z_]+)", sloc):
        assert re.search(rf"(?m)^ {key}: \"", LOC), key


def test_events_are_gated_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = FBC\.(\d+)$", EVENTS)]
    assert sorted(ids) == list(range(30, 44))
    for event_id in ids:
        head = _event(f"FBC.{event_id}").split("option = {", 1)[0]
        gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
        assert "FBC_scenario_enabled = yes" in gate
        assert "original_tag = USA" in gate
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip) = (FBC[A-Za-z0-9_.]*)", EVENTS
    )
    keys += [
        "FBC_silent_hill_fog",
        "FBC_silent_hill_fog_desc",
        "FBC_silent_hill_otherworld",
        "FBC_silent_hill_otherworld_desc",
    ]
    for key in set(keys):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
    for line in LOC.splitlines()[1:]:
        assert re.match(r'^ [A-Za-z0-9_.]+: ".*"$', line), line


def test_reports_lost_to_a_change_of_control_are_sent_again():
    case = _named_block(EFFECTS, "FBC_silenthill_case_month")
    report = case[: case.index("else_if")]
    assert "NOT = { has_country_flag = FBC_sh_report_pending }" in report
    assert "set_variable = { FBC_sh_phase = 1 }" not in report
    head = _event("FBC.30").split("option = {", 1)[0]
    gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
    assert "check_variable = { FBC_sh_phase = 0 }" in gate
    assert "764 = { is_controlled_by = ROOT }" in gate
    assert "set_variable = { FBC_sh_phase = 1 }" in _named_block(head, "immediate")
    quarantine = (
        _event("FBC.30").split("name = FBC.30.b", 1)[1].split("option = {", 1)[0]
    )
    assert "trigger = { 764 = { is_controlled_by = ROOT } }" in quarantine


def test_a_retaken_town_waits_for_a_team_before_the_timer_resumes():
    case = _named_block(EFFECTS, "FBC_silenthill_case_month")
    running = case[case.index("check_variable = { FBC_sh_phase = 2 }") :]
    assert running.index("FBC_commit_silenthill_team = yes") < running.index(
        "add_to_variable = { FBC_sh_answer_in = -1 }"
    )
    countdown = running[: running.index("add_to_variable = { FBC_sh_answer_in = -1 }")]
    assert "check_variable = { FBC_sh_committed > 0 }" in countdown
    sloc = _read(
        "common/scripted_localisation/99_FBC_silenthill_scripted_localisation.txt"
    )
    assert sloc.index("FBC_sh_waiting_for_team") < sloc.index("FBC_sh_team_in_town")


def test_visitors_and_the_order_grow_on_the_state_from_the_pulse():
    pulse = _named_block(EFFECTS, "FBC_monthly_silenthill_pulse")
    state = pulse[pulse.index("FBC_silenthill_fog_month = yes") :]
    assert state.index("FBC_silenthill_fog_month = yes") < state.index(
        "FBC_silenthill_town_month = yes"
    )
    assert "FBC_silenthill_town_events_month = yes" in pulse
    fog = _named_block(EFFECTS, "FBC_silenthill_fog_month")
    assert "value = FBC_sh_visitors multiply = 0.02" in fog
    town = _named_block(EFFECTS, "FBC_silenthill_town_month")
    visitors, order = town.split("check_variable = { FBC_sh_fog > 49 }")
    assert "check_variable = { FBC_sh_fog > 24 }" in visitors
    assert "check_variable = { FBC_sh_intervention = 2 }" in visitors
    assert "multiply_temp_variable = { FBC_sh_visitor_gain = 0.5 }" in visitors
    assert "clamp_variable = { var = FBC_sh_visitors min = 0 max = 100 }" in visitors
    assert "has_country_flag = FBC_sh_order_watched" in order
    assert "multiply_temp_variable = { FBC_sh_order_gain = 0.5 }" in order
    assert "clamp_variable = { var = FBC_sh_order min = 0 max = 100 }" in order


def test_the_siren_letters_and_order_need_a_reported_case_in_the_bureaus_hands():
    month = _named_block(EFFECTS, "FBC_silenthill_town_events_month")
    gate = month[: month.index("FBC_sh_siren_cooldown")]
    assert "check_variable = { FBC_sh_phase > 0 }" in gate
    assert "764 = { is_controlled_by = USA }" in gate
    siren = month[: month.index("FBC_sh_letters_cooldown")]
    assert "check_variable = { FBC_sh_fog > 39 }" in siren
    assert "value = FBC_sh_fog multiply = 0.15" in siren
    assert "chance = FBC_sh_siren_chance" in siren
    assert "country_event = { id = FBC.35 days = 1 }" in siren
    assert "check_variable = { FBC_sh_visitors > 19 }" in month
    assert "country_event = { id = FBC.36 days = 1 }" in month
    order = month[month.index("FBC_sh_order_known") :]
    first, rite = order.split("else_if", 1)
    assert "check_variable = { FBC_sh_order > 39 }" in first
    assert "country_event = { id = FBC.37 days = 1 }" in first
    assert "has_country_flag = FBC_sh_order_known" in rite
    assert "check_variable = { FBC_sh_order > 79 }" in rite
    assert "country_event = { id = FBC.38 days = 1 }" in rite


def test_the_order_is_known_on_arrival_so_a_lost_notice_is_sent_again():
    head = _event("FBC.37").split("option = {", 1)[0]
    gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
    assert "NOT = { has_country_flag = FBC_sh_order_known }" in gate
    assert "set_country_flag = FBC_sh_order_known" in _named_block(head, "immediate")
    month = _named_block(EFFECTS, "FBC_silenthill_town_events_month")
    assert (
        "set_country_flag = { flag = FBC_sh_order_pending value = 1 days = 7 }" in month
    )


def test_team_options_need_a_team_and_the_turnback_cost_scales():
    siren = _event("FBC.35").split("name = FBC.35.a", 1)[1].split("option = {", 1)[0]
    assert "trigger = { check_variable = { FBC_sh_committed > 0 } }" in siren
    assert "FBC_release_silenthill_team = yes" in siren
    for event_id in ("FBC.37", "FBC.38"):
        raid = _event(event_id).split(f"name = {event_id}.a", 1)[1]
        raid = raid.split("option = {", 1)[0]
        assert "trigger = { check_variable = { FBC_response_capacity > 0 } }" in raid
    head = _event("FBC.36").split("option = {", 1)[0]
    immediate = _named_block(head, "immediate")
    assert "set_variable = { FBC_sh_turnback_cost = " in immediate
    turnback = _event("FBC.36").split("name = FBC.36.a", 1)[1].split("option = {", 1)[0]
    assert "add_political_power = FBC_sh_turnback_cost" in turnback


def test_every_new_option_is_weighted_for_the_ai():
    for event_id in ("FBC.35", "FBC.36", "FBC.37", "FBC.38"):
        options = _event(event_id).split("option = {")[1:]
        assert len(options) == 3, event_id
        for option in options:
            assert "ai_chance = {" in option, event_id


def test_the_otherworld_is_a_fixed_state_modifier_with_english_text():
    modifiers = _read(
        "common/dynamic_modifiers/00_FBC_silenthill_dynamic_modifiers.txt"
    )
    otherworld = _named_block(modifiers, "FBC_silent_hill_otherworld")
    assert "local_supplies = -0.5" in otherworld
    assert "attrition_for_controller = 0.25" in otherworld
    assert "modifier = FBC_silent_hill_otherworld days = 30" in _event("FBC.35")
    assert EVENTS.count("modifier = FBC_silent_hill_otherworld days = 60") == 2
    core = _read("localisation/english/MD_FBC_l_english.yml")
    line = re.search(r'(?m)^ FBC_bureau_category_desc: "(.*)"$', core).group(1)
    assert "[FBC_sh_visitors_band] [FBC_sh_order_band]" in line


def test_one_ending_closes_the_case_and_stops_the_pulse():
    pulse = _named_block(EFFECTS, "FBC_monthly_silenthill_pulse")
    gate = pulse[: pulse.index("FBC_sh_ready")]
    assert "NOT = { has_global_flag = FBC_sh_ended }" in gate
    assert "FBC_silenthill_ending_month = yes" in pulse
    close = _named_block(EFFECTS, "FBC_silenthill_end_case")
    assert "set_global_flag = FBC_sh_ended" in close
    assert "set_variable = { FBC_sh_ending = FBC_sh_ending_choice }" in close
    assert "FBC_release_silenthill_team = yes" in close
    for choice, event_id in enumerate(
        ("FBC.39", "FBC.40", "FBC.41", "FBC.42", "FBC.43"), 1
    ):
        head = _event(event_id).split("option = {", 1)[0]
        gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
        assert "NOT = { has_global_flag = FBC_sh_ended }" in gate, event_id
        immediate = _named_block(head, "immediate")
        assert f"set_temp_variable = {{ FBC_sh_ending_choice = {choice} }}" in immediate
        assert "FBC_silenthill_end_case = yes" in immediate
        lifts = "FBC_silenthill_lift_fog = yes" in immediate
        assert lifts == (event_id in ("FBC.39", "FBC.42", "FBC.43")), event_id
        for option in _event(event_id).split("option = {")[1:]:
            assert "ai_chance = {" in option, event_id


def test_endings_are_checked_in_order_and_the_jokes_need_their_rule():
    month = _named_block(EFFECTS, "FBC_silenthill_ending_month")
    assert "NOT = { has_country_flag = FBC_sh_ending_pending }" in month
    order = [
        month.index("country_event = { id = FBC.41 days = 1 }"),
        month.index("country_event = { id = FBC.40 days = 1 }"),
        month.index("country_event = { id = FBC.39 days = 1 }"),
        month.index("rule = rule_fbc_silenthill_jokes option = ENABLED"),
    ]
    assert order == sorted(order)
    assert "FBC_sh_rebirth_ready = yes" in month[: order[0]]
    assert "FBC_sh_in_water_ready = yes" in month[order[0] : order[1]]
    assert "FBC_sh_leave_ready = yes" in month[order[1] : order[2]]
    triggers = _read("common/scripted_triggers/99_FBC_silenthill_scripted_triggers.txt")
    rebirth = _named_block(triggers, "FBC_sh_rebirth_ready")
    assert "has_global_flag = FBC_sh_rite_performed" in rebirth
    assert "check_variable = { FBC_sh_fog > 89 }" in rebirth
    jokes = month[order[3] :]
    dog = jokes[jokes.index("FBC.42") :]
    assert "modifier = { factor = 0 check_variable = { FBC_sh_committed < 1 } }" in dog
    rules = _read("common/game_rules/00_game_rules.txt")
    rule = _named_block(rules, "rule_fbc_silenthill_jokes")
    default = _named_block(rule, "default")
    assert "name = DISABLED" in default


def test_a_finished_rite_is_recorded_for_rebirth():
    rite = _event("FBC.38")
    stop, evacuate, let_happen = rite.split("option = {")[1:]
    failure = stop[stop.index("50 = {", stop.index("50 = {") + 1) :]
    assert "set_global_flag = FBC_sh_rite_performed" in failure
    assert "set_global_flag = FBC_sh_rite_performed" not in evacuate
    assert "set_global_flag = FBC_sh_rite_performed" in let_happen


def test_cooldowns_start_on_arrival_and_a_pending_flag_covers_the_queue():
    month = _named_block(EFFECTS, "FBC_silenthill_town_events_month")
    for name, event_id, days in (
        ("siren", "FBC.35", 180),
        ("letters", "FBC.36", 180),
        ("rite", "FBC.38", 365),
    ):
        assert f"NOT = {{ has_country_flag = FBC_sh_{name}_pending }}" in month
        assert (
            f"set_country_flag = {{ flag = FBC_sh_{name}_pending value = 1 days = 7 }}"
            in month
        )
        assert f"set_country_flag = {{ flag = FBC_sh_{name}_cooldown" not in month
        head = _event(event_id).split("option = {", 1)[0]
        assert (
            f"set_country_flag = {{ flag = FBC_sh_{name}_cooldown value = 1 days = {days} }}"
            in _named_block(head, "immediate")
        )


def test_pulling_back_needs_a_running_intervention():
    pull_back = (
        _event("FBC.35").split("name = FBC.35.b", 1)[1].split("option = {", 1)[0]
    )
    assert "trigger = { check_variable = { FBC_sh_phase = 2 } }" in pull_back
    assert "add_to_variable = { FBC_sh_answer_in = 2 }" in pull_back


def test_turning_visitors_back_charges_and_removes_the_same_snapshot():
    head = _event("FBC.36").split("option = {", 1)[0]
    immediate = _named_block(head, "immediate")
    assert (
        "set_variable = { FBC_sh_turnback_visitors = FBC_sh_visitors_now }" in immediate
    )
    turnback = _event("FBC.36").split("name = FBC.36.a", 1)[1].split("option = {", 1)[0]
    assert "value = FBC_sh_turnback_visitors multiply = -0.75" in turnback
    assert "value = FBC_sh_visitors multiply" not in turnback


def test_queued_letters_and_rite_recheck_their_threshold_on_arrival():
    for event_id, threshold in (
        ("FBC.36", "check_variable = { FBC_sh_visitors > 19 }"),
        ("FBC.38", "check_variable = { FBC_sh_order > 79 }"),
    ):
        head = _event(event_id).split("option = {", 1)[0]
        gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
        assert threshold in gate, event_id
        assert "is_controlled_by = ROOT" in gate, event_id


def test_an_ending_queues_alone_and_every_event_rejects_a_closed_case():
    pulse = _named_block(EFFECTS, "FBC_monthly_silenthill_pulse")
    usa = pulse[pulse.index("FBC_silenthill_ending_month = yes") :]
    gated = usa[usa.index("NOT = { has_country_flag = FBC_sh_ending_pending }") :]
    assert "FBC_silenthill_case_month = yes" in gated
    assert "FBC_silenthill_town_events_month = yes" in gated
    for event_id in range(30, 44):
        head = _event(f"FBC.{event_id}").split("option = {", 1)[0]
        gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
        assert "NOT = { has_global_flag = FBC_sh_ended }" in gate, event_id
    for event_id, condition in (
        ("FBC.39", "FBC_sh_leave_ready = yes"),
        ("FBC.40", "FBC_sh_in_water_ready = yes"),
        ("FBC.41", "FBC_sh_rebirth_ready = yes"),
        ("FBC.43", "check_variable = { FBC_sh_committed > 0 }"),
    ):
        head = _event(event_id).split("option = {", 1)[0]
        gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
        assert condition in gate, event_id
