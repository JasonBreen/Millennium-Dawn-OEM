import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


DECISIONS = _read("common/decisions/STALKER_antarctic_decisions.txt")
EFFECTS = _read("common/scripted_effects/99_STALKER_antarctic_effects.txt")
EVENTS = _read("events/STALKER_antarctic.txt")
OBSERVER = _read("events/MD_Antarctica.txt")
LOC = _read("localisation/english/MD_STALKER_antarctic_l_english.yml")


def test_the_study_needs_five_artifacts_and_a_working_radiation_laboratory():
    study = _named_block(DECISIONS, "STALKER_polar_artifact_study")
    available = _named_block(study, "available")
    assert "check_variable = { STALKER_artifact_stockpile > 4.99 }" in available
    assert "check_variable = { antarctica_lab_cat_nuclear_reactors > 0 }" in available
    assert (
        "has_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }"
        in available
    )
    effect = _named_block(study, "complete_effect")
    assert "add_to_variable = { STALKER_artifact_stockpile = -5 }" in effect
    assert (
        "add_dynamic_modifier = { modifier = STALKER_polar_artifact_samples days = 180 }"
        in effect
    )
    assert "country_event = { id = STALKER.190 days = 180 }" in effect
    assert "has_active_mission = bankruptcy_incoming_collapse" in _named_block(
        study, "ai_will_do"
    )


def test_the_samples_speed_research_and_station_iterations():
    modifiers = _read(
        "common/dynamic_modifiers/00_STALKER_antarctic_dynamic_modifiers.txt"
    )
    samples = _named_block(modifiers, "STALKER_polar_artifact_samples")
    assert "research_speed_factor = 0.03" in samples
    assert "antarctica_lab_iteration_progress_modifier = 0.15" in samples


def test_observers_find_the_study_only_when_nothing_else_was_reported():
    start = OBSERVER.index("# STALKER: Zone artifacts under study")
    branch = OBSERVER[start : OBSERVER.index("\n\t\t\t}\n", start) + 5]
    assert branch.split("\n", 2)[1].strip() == "else_if = {"
    assert "STALKER_scenario_enabled = yes" in branch
    assert (
        "has_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }" in branch
    )
    assert "STALKER_polar_study_detected = yes" in branch
    preceding = OBSERVER[
        OBSERVER.rindex("if = {\n\t\t\t\tlimit = {\n\t\t\t\t\tOR = {", 0, start) : start
    ]
    assert "station_illegal_activities > 0" in preceding
    assert "station_open_loop_module = 1" in preceding


def test_seized_samples_end_the_study_and_use_the_treaty_penalty():
    detected = _named_block(EFFECTS, "STALKER_polar_study_detected")
    assert (
        "remove_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }"
        in detected
    )
    assert (
        "set_country_flag = { flag = STALKER_polar_study_seized days = 180 value = 1 }"
        in detected
    )
    assert "news_event = STALKER.191" in detected
    assert "country_event = MD_antarctica.4" in detected
    results = EVENTS[EVENTS.index("id = STALKER.190") :]
    assert (
        "NOT = { has_country_flag = STALKER_polar_study_seized }"
        in results.split("option", 1)[0]
    )


def test_event_ids_stay_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"id = STALKER\.(\d+)", EVENTS)]
    assert ids and all(190 <= n <= 199 for n in ids)
    for key in re.findall(
        r"(?:title|desc|name|tooltip|custom_effect_tooltip) = (STALKER[A-Za-z0-9_.]*)",
        DECISIONS + EVENTS + EFFECTS,
    ):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
    for key in (
        "STALKER_polar_artifact_study",
        "STALKER_polar_artifact_study_desc",
        "STALKER_polar_artifact_samples",
        "STALKER_polar_artifact_study_bonus",
    ):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
