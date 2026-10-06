import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


EFFECTS = _read("common/scripted_effects/99_DEUSEX_illuminati_effects.txt")
TRIGGERS = _read("common/scripted_triggers/99_DEUSEX_illuminati_triggers.txt")
EVENTS = _read("events/DEUSEX_illuminati.txt")
DECISIONS = _read("common/decisions/DEUSEX_illuminati_decisions.txt")
LOC = _read("localisation/english/MD_DEUSEX_illuminati_l_english.yml")
TARGETS = ("USA", "CHI", "GER", "ENG", "FRA", "SOV", "JAP", "RAJ")


def _event(event_id):
    start = EVENTS.index(f"id = {event_id}\n")
    end = EVENTS.find("\n\n# ", start)
    return EVENTS[start : end if end > 0 else len(EVENTS)]


def test_the_pulse_sets_up_once_and_only_targets_outside_the_circle_grow():
    pulses = _read("common/scripted_effects/99_DEUSEX_pulse_effects.txt")
    assert "DEUSEX_monthly_illuminati_pulse = yes" in _named_block(
        pulses, "DEUSEX_monthly_pulse"
    )
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_illuminati_pulse")
    assert "DEUSEX_scenario_enabled = yes" in pulse
    assert "NOT = { has_global_flag = DEUSEX_illuminati_ready }" in pulse
    assert "set_global_flag = DEUSEX_illuminati_ready" in _named_block(
        EFFECTS, "DEUSEX_setup_illuminati"
    )
    growth = pulse[pulse.index("every_country = {") :]
    growth = _named_block(growth, "every_country")
    assert "DEUSEX_is_illuminati_target = yes" in growth
    assert "NOT = { has_country_flag = DEUSEX_inner_circle }" in growth
    assert "DEUSEX_illuminati_month = yes" in growth
    targets = _named_block(TRIGGERS, "DEUSEX_is_illuminati_target")
    assert sorted(re.findall(r"tag = ([A-Z]{3})", targets)) == sorted(TARGETS)


def test_a_lost_member_frees_the_seat_and_keeps_nothing():
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_illuminati_pulse")
    lost = pulse[pulse.index("var:global.DEUSEX_illum_member = { exists = no }") :]
    lost = lost[: lost.index("every_country")]
    assert "clr_country_flag = DEUSEX_inner_circle" in lost
    assert lost.index("has_dynamic_modifier = { modifier = DEUSEX_inner_circle }") < (
        lost.index("remove_dynamic_modifier = { modifier = DEUSEX_inner_circle }")
    )
    assert "clear_variable = global.DEUSEX_illum_member" in lost


def test_influence_drives_the_grip_and_the_offer():
    month = _named_block(EFFECTS, "DEUSEX_illuminati_month")
    assert "set_temp_variable = { DEUSEX_illum_gain = 0.5 }" in month
    assert month.index("DEUSEX_update_illuminati_grip = yes") < month.index(
        "add_dynamic_modifier = { modifier = DEUSEX_illuminati_grip }"
    )
    assert "flag = DEUSEX_illum_offer_cooldown value = 1 days = 730" in month
    assert "country_event = { id = DEUSEX.40 days = 1 }" in month
    modifiers = _read(
        "common/dynamic_modifiers/00_DEUSEX_illuminati_dynamic_modifiers.txt"
    )
    for modifier, effect in (
        ("DEUSEX_illuminati_grip", "DEUSEX_update_illuminati_grip"),
        ("DEUSEX_inner_circle", "DEUSEX_update_inner_circle"),
    ):
        update = _named_block(EFFECTS, effect)
        for variable in re.findall(
            r"= (DEUSEX_[a-z_]+)$", _named_block(modifiers, modifier), re.M
        ):
            assert f"set_variable = {{ {variable} = " in update, variable
    grip = _named_block(EFFECTS, "DEUSEX_update_illuminati_grip")
    assert grip.index("clamp_variable = { var = DEUSEX_illum_influence") < grip.index(
        "DEUSEX_illum_pp_factor"
    )
    assert "check_variable = { global.DEUSEX_illum_agenda = 4 }" in grip


def test_joining_swaps_the_grip_for_the_circle():
    join = _named_block(EFFECTS, "DEUSEX_join_inner_circle")
    assert "set_variable = { global.DEUSEX_illum_member = THIS }" in join
    assert join.index(
        "has_dynamic_modifier = { modifier = DEUSEX_illuminati_grip }"
    ) < (join.index("remove_dynamic_modifier = { modifier = DEUSEX_illuminati_grip }"))
    assert join.index("DEUSEX_update_inner_circle = yes") < join.index(
        "add_dynamic_modifier = { modifier = DEUSEX_inner_circle }"
    )
    seek = _named_block(DECISIONS, "DEUSEX_seek_inner_circle")
    assert "NOT = { has_variable = global.DEUSEX_illum_member }" in _named_block(
        seek, "visible"
    )
    assert "NOT = { has_variable = global.DEUSEX_illum_member }" in _named_block(
        seek, "complete_effect"
    )


def test_wings_are_zero_sum():
    empower = _named_block(EFFECTS, "DEUSEX_empower_wing")
    for wing in ("capital", "media", "security"):
        assert f"add_to_variable = {{ global.DEUSEX_illum_{wing} = -3 }}" in empower
        assert f"add_to_variable = {{ global.DEUSEX_illum_{wing} = 18 }}" in empower
    for decision, wing in (
        ("DEUSEX_empower_capital", 1),
        ("DEUSEX_empower_media", 2),
        ("DEUSEX_empower_security", 3),
    ):
        assert f"set_temp_variable = {{ DEUSEX_wing = {wing} }}" in _named_block(
            DECISIONS, decision
        )


def test_the_agenda_has_four_gated_stages():
    ready = _named_block(TRIGGERS, "DEUSEX_agenda_ready")
    for stage in range(4):
        assert f"check_variable = {{ global.DEUSEX_illum_agenda = {stage} }}" in ready
    assert "date > 2025.1.1" in ready
    assert "has_global_flag = DEUSEX_aug_incident_done" in ready
    agenda = _named_block(DECISIONS, "DEUSEX_advance_the_agenda")
    assert "DEUSEX_agenda_ready = yes" in _named_block(agenda, "available")
    assert "DEUSEX_advance_agenda = yes" in _named_block(agenda, "remove_effect")
    chip = _named_block(EFFECTS, "DEUSEX_advance_agenda")
    assert "check_variable = { global.DEUSEX_illum_agenda = 2 }" in chip
    assert "multiply_temp_variable = { DEUSEX_chip_gain = 0.2 }" in chip


def test_the_restoration_act_serves_the_agenda():
    act = _read("events/DEUSEX_augmentation.txt")
    act = act[act.index("id = DEUSEX.36") :]
    adopt = act.split("name = DEUSEX.36.b", 1)[0]
    assert "limit = { DEUSEX_restoration_act_serves_illuminati = yes }" in adopt
    assert "add_to_variable = { DEUSEX_illum_influence = 20 }" in adopt
    assert "factor = 3 check_variable = { global.DEUSEX_illum_agenda > 2 }" in adopt
    serves = _named_block(TRIGGERS, "DEUSEX_restoration_act_serves_illuminati")
    assert "NOT = { has_country_flag = DEUSEX_inner_circle }" in serves


def test_the_masquerade_slips_once_a_year():
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_illuminati_pulse")
    assert "check_variable = { global.DEUSEX_illum_exposure > 69 }" in pulse
    assert "NOT = { has_global_flag = DEUSEX_masquerade_cooldown }" in pulse
    slips = _named_block(EFFECTS, "DEUSEX_masquerade_slips")
    assert "flag = DEUSEX_masquerade_cooldown value = 1 days = 365" in slips
    assert "news_event = { id = DEUSEX.41 days = 1 }" in slips
    assert "add_to_variable = { DEUSEX_illum_influence = -10 }" in slips
    assert "country_event = { id = DEUSEX.42 days = 1 }" in slips
    choice = _event("DEUSEX.42")
    assert "trigger" in choice and "has_country_flag = DEUSEX_inner_circle" in choice
    for option in choice.split("option = {")[1:]:
        assert "DEUSEX_update_inner_circle = yes" in option


def test_every_change_refreshes_its_modifier():
    for text in (EVENTS, DECISIONS):
        for match in re.finditer(
            r"add_to_variable = \{ DEUSEX_illum_influence = ", text
        ):
            following = text[match.end() : match.end() + 200]
            assert "DEUSEX_update_illuminati_grip = yes" in following
        for match in re.finditer(
            r"add_to_variable = \{ global\.DEUSEX_illum_(exposure|capital|media|security) = ",
            text,
        ):
            following = text[match.end() : match.end() + 400]
            assert (
                "DEUSEX_update_inner_circle = yes" in following
                or "DEUSEX_clamp_illuminati = yes" in following
            )


def test_events_are_gated_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = DEUSEX\.(\d+)$", EVENTS)]
    assert sorted(ids) == [40, 41, 42]
    for event_id in ids:
        head = _event(f"DEUSEX.{event_id}").split("option = {", 1)[0]
        gate = head[head.index("\n\ttrigger = ") :]
        assert "DEUSEX_scenario_enabled = yes" in gate
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip|tooltip) = (DEUSEX[A-Za-z0-9_.]*)",
        EVENTS + DECISIONS,
    )
    keys += re.findall(r"(?m)^\t(DEUSEX_[a-z_]+) = \{$", DECISIONS)
    keys += [
        f"{key}_desc" for key in re.findall(r"(?m)^\t(DEUSEX_[a-z_]+) = \{$", DECISIONS)
    ]
    keys += ["DEUSEX_illuminati_category", "DEUSEX_inner_circle_category"]
    keys += ["DEUSEX_illuminati_grip", "DEUSEX_inner_circle"]
    keys += re.findall(
        r"localization_key = (DEUSEX_[a-z0-9_]+)",
        _read(
            "common/scripted_localisation/99_DEUSEX_illuminati_scripted_localisation.txt"
        ),
    )
    other = _read("localisation/english/MD_DEUSEX_augmentation_l_english.yml")
    for key in set(keys):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC + other), key
    for line in LOC.splitlines()[1:]:
        assert re.match(r'^ [A-Za-z0-9_.]+: ".*"$', line), line
