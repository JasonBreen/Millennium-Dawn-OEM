import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


EFFECTS = _read("common/scripted_effects/99_DEUSEX_traitor_effects.txt")
TRIGGERS = _read("common/scripted_triggers/99_DEUSEX_traitor_triggers.txt")
EVENTS = _read("events/DEUSEX_traitor.txt")
DECISIONS = _read("common/decisions/DEUSEX_traitor_decisions.txt")
LOC = _read("localisation/english/MD_DEUSEX_traitor_l_english.yml")
SUSPECTS = ("page", "zhao", "taggart", "duclare", "darrow")
WINGS = {1: "capital", 2: "media", 3: "security"}


def _event(event_id):
    start = EVENTS.index(f"id = {event_id}\n")
    end = EVENTS.find("\n\n# ", start)
    return EVENTS[start : end if end > 0 else len(EVENTS)]


def _dossiers():
    traits = _named_block(EFFECTS, "DEUSEX_set_traitor_traits")
    found = {}
    for index, branch in enumerate(re.split(r"\n\t(?:else_if|else) = \{", traits), 1):
        values = dict(
            re.findall(r"global\.DEUSEX_traitor_(wing|stance|face) = (\d)", branch)
        )
        found[index] = (int(values["wing"]), int(values["stance"]), int(values["face"]))
    return found


def test_the_hunt_starts_once_while_the_circle_has_a_member():
    pulses = _named_block(
        _read("common/scripted_effects/99_DEUSEX_pulse_effects.txt"),
        "DEUSEX_monthly_pulse",
    )
    assert pulses.index("DEUSEX_monthly_illuminati_pulse = yes") < pulses.index(
        "DEUSEX_monthly_traitor_pulse = yes"
    )
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_traitor_pulse")
    start = pulse[pulse.rindex("else_if = {") :]
    assert "has_variable = global.DEUSEX_illum_member" in start
    assert "NOT = { has_global_flag = DEUSEX_traitor_hunt_done }" in start
    assert "check_variable = { global.DEUSEX_illum_agenda > 0 }" in start
    assert "chance = 4" in start
    assert "set_global_flag = DEUSEX_traitor_hunt_done" in _named_block(
        EFFECTS, "DEUSEX_end_traitor_hunt"
    )
    hunt = _named_block(EFFECTS, "DEUSEX_start_traitor_hunt")
    darrow = hunt[hunt.index("global.DEUSEX_traitor = 4") :]
    assert darrow.index("has_global_flag = DEUSEX_aug_incident_done") < darrow.index(
        "global.DEUSEX_traitor = 5"
    )
    assert "set_variable = { global.DEUSEX_traitor_clock = 18 }" in hunt


def test_dossiers_are_unique_and_match_the_fit_triggers_and_the_text():
    dossiers = _dossiers()
    assert sorted(dossiers) == [1, 2, 3, 4, 5]
    assert len(set(dossiers.values())) == 5
    category = re.search(r'(?m)^ DEUSEX_traitor_category_desc: "(.*)"$', LOC).group(1)
    for index, key in enumerate(SUSPECTS, 1):
        wing, stance, face = dossiers[index]
        fits = _named_block(TRIGGERS, f"DEUSEX_{key}_fits")
        assert f"global.DEUSEX_traitor_wing = {wing}" in fits
        assert f"global.DEUSEX_traitor_stance = {stance}" in fits
        assert f"global.DEUSEX_traitor_face = {face}" in fits
        name = re.search(rf'(?m)^ DEUSEX_suspect_{index}: "(.*)"$', LOC).group(1)
        line = category[category.index(f"§Y{name}§!") :].split("\\n", 1)[0]
        assert f"{WINGS[wing]} wing" in line, line
        assert ("for augmentation" if stance == 1 else "against augmentation") in line
        assert ("corporate" if face == 1 else "public figure") in line
        accuse = _named_block(DECISIONS, f"DEUSEX_accuse_{key}")
        assert f"set_temp_variable = {{ DEUSEX_suspect = {index} }}" in accuse
        weights = _named_block(accuse, "ai_will_do")
        assert weights.count(f"DEUSEX_{key}_fits = yes") == 3


def test_suspect_wings_for_a_wrong_name_match_the_dossiers():
    dossiers = _dossiers()
    wing = _named_block(EFFECTS, "DEUSEX_set_suspect_wing")
    assert "set_temp_variable = { DEUSEX_wing = 1 }" in wing
    assert dossiers[2][0] == 3 and "DEUSEX_suspect = 2" in wing
    assert dossiers[3][0] == 2 and dossiers[4][0] == 2
    assert (
        "check_variable = { DEUSEX_suspect > 2 } check_variable = { DEUSEX_suspect < 5 }"
        in wing
    )
    assert dossiers[1][0] == 1 and dossiers[5][0] == 1


def test_clues_reveal_only_while_the_hunt_runs():
    for decision, clue in (
        ("DEUSEX_trace_the_money", "wing"),
        ("DEUSEX_read_the_leaks", "stance"),
        ("DEUSEX_watch_the_table", "face"),
    ):
        body = _named_block(DECISIONS, decision)
        assert f"NOT = {{ has_global_flag = DEUSEX_clue_{clue} }}" in _named_block(
            body, "visible"
        )
        reveal = _named_block(body, "remove_effect")
        assert reveal.index("has_global_flag = DEUSEX_traitor_hunt") < reveal.index(
            f"set_global_flag = DEUSEX_clue_{clue}"
        )
    watch = _named_block(DECISIONS, "DEUSEX_watch_the_table")
    assert "add_to_variable = { global.DEUSEX_traitor_clock = -1 }" in watch


def test_an_accusation_is_judged_against_the_hidden_traitor():
    accuse = _named_block(EFFECTS, "DEUSEX_accuse_suspect")
    right, wrong = accuse.split("else_if = {", 1)
    assert "check_variable = { global.DEUSEX_traitor = DEUSEX_suspect }" in right
    assert right.index("DEUSEX_end_traitor_hunt = yes") < right.index(
        "country_event = { id = DEUSEX.53 days = 1 }"
    )
    assert "set_temp_variable = { DEUSEX_wing = global.DEUSEX_traitor_wing }" in right
    assert "has_global_flag = DEUSEX_traitor_hunt" in wrong
    assert "DEUSEX_set_suspect_wing = yes" in wrong
    assert "add_to_variable = { global.DEUSEX_traitor_clock = -3 }" in wrong
    assert "country_event = { id = DEUSEX.54 days = 1 }" in wrong


def test_the_clock_running_out_costs_the_member_its_seat():
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_traitor_pulse")
    lost = pulse[: pulse.index("else_if = {")]
    assert "NOT = { has_variable = global.DEUSEX_illum_member }" in lost
    assert "DEUSEX_end_traitor_hunt = yes" in lost
    tick = pulse[pulse.index("check_variable = { global.DEUSEX_traitor_clock < 1 }") :]
    assert tick.index("DEUSEX_end_traitor_hunt = yes") < tick.index(
        "country_event = { id = DEUSEX.51 days = 1 }"
    )
    assert "news_event = { id = DEUSEX.52 days = 1 }" in tick
    betrayed = _named_block(EFFECTS, "DEUSEX_betrayed_by_traitor")
    assert "clr_country_flag = DEUSEX_inner_circle" in betrayed
    assert "clear_variable = global.DEUSEX_illum_member" in betrayed
    assert betrayed.index(
        "has_dynamic_modifier = { modifier = DEUSEX_inner_circle }"
    ) < (betrayed.index("remove_dynamic_modifier = { modifier = DEUSEX_inner_circle }"))
    assert "set_variable = { DEUSEX_illum_influence = 50 }" in betrayed
    assert "NOT = { has_dynamic_modifier = { modifier = DEUSEX_illuminati_grip } }" in (
        betrayed
    )
    assert "DEUSEX_betrayed_by_traitor = yes" in _event("DEUSEX.51")


def test_events_are_gated_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = DEUSEX\.(\d+)$", EVENTS)]
    assert sorted(ids) == [50, 51, 52, 53, 54]
    for event_id in ids:
        head = _event(f"DEUSEX.{event_id}").split("option = {", 1)[0]
        assert "DEUSEX_scenario_enabled = yes" in head[head.index("\n\ttrigger = ") :]
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip|tooltip) = (DEUSEX[A-Za-z0-9_.]*)",
        EVENTS + DECISIONS,
    )
    decisions = re.findall(r"(?m)^\t(DEUSEX_[a-z_]+) = \{$", DECISIONS)
    keys += decisions + [f"{key}_desc" for key in decisions]
    keys += ["DEUSEX_traitor_category", "DEUSEX_traitor_category_desc"]
    keys += re.findall(
        r"localization_key = (DEUSEX_[a-z0-9_]+)",
        _read(
            "common/scripted_localisation/99_DEUSEX_traitor_scripted_localisation.txt"
        ),
    )
    for key in set(keys):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
    for line in LOC.splitlines()[1:]:
        assert re.match(r'^ [A-Za-z0-9_.]+: ".*"$', line), line
    assert "judas" not in (EFFECTS + EVENTS + DECISIONS + LOC).lower()
