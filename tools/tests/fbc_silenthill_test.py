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
    assert sorted(ids) == [30, 31, 32, 33, 34]
    for event_id in ids:
        head = _event(f"FBC.{event_id}").split("option = {", 1)[0]
        gate = _named_block(head[head.index("\n\ttrigger = {") :], "trigger")
        assert "FBC_scenario_enabled = yes" in gate
        assert "original_tag = USA" in gate
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip) = (FBC[A-Za-z0-9_.]*)", EVENTS
    )
    keys += ["FBC_silent_hill_fog", "FBC_silent_hill_fog_desc"]
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
