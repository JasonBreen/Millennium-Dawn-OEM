import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


EFFECTS = _read("common/scripted_effects/99_METALGEAR_operations_effects.txt")
EVENTS = _read("events/METALGEAR_operations.txt")
DECISIONS = _read("common/decisions/METALGEAR_operations_decisions.txt")
LOC = _read("localisation/english/MD_METALGEAR_operations_l_english.yml")
OPERATIONS = {
    "METALGEAR_steer_procurement": "0",
    "METALGEAR_manage_news_cycle": "2",
    "METALGEAR_influence_foreign_desk": "1",
}


def test_the_pulse_runs_after_the_network_and_keeps_the_modifier_on_the_usa():
    pulses = _named_block(
        _read("common/scripted_effects/99_METALGEAR_pulse_effects.txt"),
        "METALGEAR_monthly_pulse",
    )
    assert pulses.index("METALGEAR_monthly_network_pulse = yes") < pulses.index(
        "METALGEAR_monthly_operations_pulse = yes"
    )
    pulse = _named_block(EFFECTS, "METALGEAR_monthly_operations_pulse")
    assert "has_global_flag = GLOBAL_METALGEAR_network_ready" in pulse
    assert "country_exists = USA" in pulse
    usa = _named_block(pulse, "USA")
    assert usa.index("METALGEAR_refresh_patriots_factors = yes") < usa.index(
        "add_dynamic_modifier = { modifier = METALGEAR_patriots }"
    )
    assert "NOT = { has_dynamic_modifier = { modifier = METALGEAR_patriots } }" in usa


def test_the_modifier_reads_values_the_refresh_sets_from_the_meters():
    modifiers = _read(
        "common/dynamic_modifiers/00_METALGEAR_operations_dynamic_modifiers.txt"
    )
    patriots = _named_block(modifiers, "METALGEAR_patriots")
    refresh = _named_block(EFFECTS, "METALGEAR_refresh_patriots_factors")
    variables = re.findall(r"= (METALGEAR_[a-z_]+_factor)", patriots)
    assert len(variables) == 3
    for variable in variables:
        assert f"set_variable = {{ {variable} = " in refresh, variable
    assert refresh.index("METALGEAR_clamp_network = yes") < refresh.index(
        "METALGEAR_pp_factor"
    )
    assert (
        "value = global.METALGEAR_coherence subtract = 50 multiply = 0.005" in refresh
    )


def test_every_operation_holds_a_commitment_until_it_ends():
    for decision, node in OPERATIONS.items():
        body = _named_block(DECISIONS, decision)
        assert "available = { METALGEAR_has_capacity = yes }" in body
        assert "days_remove = 60" in body
        start = _named_block(body, "complete_effect")
        assert f"set_temp_variable = {{ mg_i = {node} }}" in start
        assert "METALGEAR_start_operation = yes" in start
        end = _named_block(body, "remove_effect")
        assert "METALGEAR_end_operation = yes" in end
        assert f'Decision {decision}"' in start and f'Decision {decision}"' in end
        weights = _named_block(body, "ai_will_do")
        assert "check_variable = { global.METALGEAR_exposure > 45 }" in weights
        assert "has_active_mission = bankruptcy_incoming_collapse" in weights
    start = _named_block(EFFECTS, "METALGEAR_start_operation")
    assert "subtract_from_variable = { global.METALGEAR_capacity = 1 }" in start
    assert "check_variable = { global.METALGEAR_node_true^mg_i = 2 }" in start
    assert "add_to_variable = { global.METALGEAR_capacity = 1 }" in _named_block(
        EFFECTS, "METALGEAR_end_operation"
    )


def test_operation_results():
    procurement = _named_block(
        _named_block(DECISIONS, "METALGEAR_steer_procurement"), "remove_effect"
    )
    assert "category = CAT_armor" in procurement
    news = _named_block(
        _named_block(DECISIONS, "METALGEAR_manage_news_cycle"), "remove_effect"
    )
    assert "set_temp_variable = { party_popularity_increase = 0.03 }" in news
    assert "party_index" not in news
    desk = _named_block(DECISIONS, "METALGEAR_influence_foreign_desk")
    assert "target_root_trigger = { METALGEAR_is_controller = yes }" in desk
    influence = _named_block(desk, "remove_effect")
    assert influence.index("FROM = { exists = yes }") < influence.index(
        "change_influence_percentage = yes"
    )
    assert "set_temp_variable = { influence_target = FROM.id }" in influence


def test_high_exposure_forces_one_scandal_a_year():
    pulse = _named_block(EFFECTS, "METALGEAR_monthly_operations_pulse")
    scandal = pulse[
        pulse.index("check_variable = { global.METALGEAR_exposure > 60 }") :
    ]
    assert "NOT = { has_global_flag = METALGEAR_scandal_cooldown }" in scandal
    assert "flag = METALGEAR_scandal_cooldown value = 1 days = 365" in scandal
    assert "country_event = { id = METALGEAR.40 days = 1 }" in scandal
    event = EVENTS[EVENTS.index("id = METALGEAR.40") :]
    assert "trigger = { METALGEAR_is_controller = yes }" in event
    bury, expose = event.split("name = METALGEAR.40.b", 1)
    assert "add_to_variable = { global.METALGEAR_exposure = -20 }" in bury
    assert "set_variable = { global.METALGEAR_exposure = 10 }" in expose
    for option in (bury, expose):
        assert "METALGEAR_refresh_patriots_factors = yes" in option


def test_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = METALGEAR\.(\d+)$", EVENTS)]
    assert ids == [40]
    keys = re.findall(
        r"(?:title|desc|name|custom_effect_tooltip) = (METALGEAR[A-Za-z0-9_.]*)",
        EVENTS + DECISIONS,
    )
    keys += list(OPERATIONS) + [f"{key}_desc" for key in OPERATIONS]
    keys += ["METALGEAR_patriots", "METALGEAR_patriots_desc"]
    for key in set(keys):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
    for line in LOC.splitlines()[1:]:
        assert re.match(r'^ [A-Za-z0-9_.]+: ".*"$', line), line
