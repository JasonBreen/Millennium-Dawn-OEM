import re

from ai_race_state_model_test import ROOT, _named_block


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


EFFECTS = _read("common/scripted_effects/99_DEUSEX_augmentation_effects.txt")
EVENTS = _read("events/DEUSEX_augmentation.txt")
DECISIONS = _read("common/decisions/DEUSEX_augmentation_decisions.txt")
LOC = _read("localisation/english/MD_DEUSEX_augmentation_l_english.yml")


def _event(event_id):
    start = EVENTS.index(f"id = {event_id}\n")
    end = EVENTS.find("\n\n# ", start)
    return EVENTS[start : end if end > 0 else len(EVENTS)]


def test_the_pulse_offers_each_host_once_on_its_date():
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_augmentation_pulse")
    assert "DEUSEX_scenario_enabled = yes" in pulse
    for date, flag, tag, event_id in (
        ("2007.1.1", "DEUSEX_aug_usa_offered", "USA", "DEUSEX.30"),
        ("2009.1.1", "DEUSEX_aug_chi_offered", "CHI", "DEUSEX.31"),
    ):
        offer = pulse[pulse.index(f"date > {date}") :]
        offer = offer[
            : offer.index(
                f"{tag} = {{ country_event = {{ id = {event_id} days = 1 }} }}"
            )
        ]
        assert f"country_exists = {tag}" in offer
        assert f"NOT = {{ has_global_flag = {flag} }}" in offer
        assert f"set_global_flag = {flag}" in offer
    pulses = _read("common/scripted_effects/99_DEUSEX_pulse_effects.txt")
    assert "DEUSEX_monthly_augmentation_pulse = yes" in _named_block(
        pulses, "DEUSEX_monthly_pulse"
    )


def test_every_host_month_runs_only_after_its_industry_opens():
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_augmentation_pulse")
    for tag in ("USA", "CHI"):
        assert (
            f"limit = {{ country_exists = {tag} {tag} = {{ has_country_flag = DEUSEX_aug_open }} }}"
            in pulse
        )
        assert f"{tag} = {{ DEUSEX_augmentation_month = yes }}" in pulse


def test_unrest_and_neuropozyne_scale_with_adoption():
    month = _named_block(EFFECTS, "DEUSEX_augmentation_month")
    assert (
        "DEUSEX_unrest_gain = { value = DEUSEX_aug_adoption multiply = 0.05 }" in month
    )
    funded = month[month.index("has_country_flag = DEUSEX_aug_neuropozyne_funded") :]
    assert "multiply_temp_variable = { DEUSEX_unrest_gain = 0.5 }" in funded
    assert (
        "treasury_change = { value = DEUSEX_aug_adoption multiply = -0.015 }" in funded
    )
    assert month.index("add_to_variable = { DEUSEX_aug_unrest = -2 }") < month.index(
        "DEUSEX_update_augmentation = yes"
    )
    assert "chance = 4" in month
    assert "flag = DEUSEX_aug_shortage_cooldown value = 1 days = 365" in month
    assert "check_variable = { DEUSEX_aug_unrest > 59 }" in month
    assert "flag = DEUSEX_aug_riot_cooldown value = 1 days = 365" in month


def test_the_modifier_reads_values_the_update_effect_sets():
    modifiers = _read(
        "common/dynamic_modifiers/00_DEUSEX_augmentation_dynamic_modifiers.txt"
    )
    industry = _named_block(modifiers, "DEUSEX_augmentation_industry")
    update = _named_block(EFFECTS, "DEUSEX_update_augmentation")
    for variable in re.findall(r"= (DEUSEX_aug_[a-z_]+_factor)", industry):
        assert f"set_variable = {{ {variable} = " in update, variable
    assert update.index(
        "clamp_variable = { var = DEUSEX_aug_adoption min = 0 max = 100 }"
    ) < update.index("DEUSEX_aug_research_factor")
    army = update[update.index("has_country_flag = DEUSEX_aug_military") :]
    assert (
        "DEUSEX_aug_army_factor = { value = DEUSEX_aug_adoption multiply = 0.0008 }"
        in army
    )
    opening = _named_block(EFFECTS, "DEUSEX_open_augmentation_industry")
    assert opening.index("DEUSEX_update_augmentation = yes") < opening.index(
        "add_dynamic_modifier = { modifier = DEUSEX_augmentation_industry }"
    )


def test_every_adoption_or_unrest_change_refreshes_the_modifier():
    for text in (EVENTS, DECISIONS):
        for match in re.finditer(
            r"add_to_variable = \{ DEUSEX_aug_(adoption|unrest) = ", text
        ):
            ends = [text.find(close, match.end()) for close in ("\n\t\t}", "\n\t\t\t}")]
            block_end = min(end for end in ends if end > 0)
            assert "DEUSEX_update_augmentation = yes" in text[match.end() : block_end]


def test_the_incident_and_the_restoration_act_reach_only_hosts_with_adoption():
    pulse = _named_block(EFFECTS, "DEUSEX_monthly_augmentation_pulse")
    incident = pulse[pulse.index("date > 2027.10.1") : pulse.index("date > 2029.1.1")]
    assert "news_event = { id = DEUSEX.35 days = 1 }" in incident
    for tag in ("USA", "CHI"):
        assert (
            f"limit = {{ {tag} = {{ DEUSEX_has_augmentation_industry = yes }} }}\n"
            f"\t\t\t\t{tag} = {{ country_event = {{ id = DEUSEX.34 days = 1 }} }}"
        ) in incident
    act = pulse[pulse.index("date > 2029.1.1") :]
    assert "has_global_flag = DEUSEX_aug_incident_done" in act
    assert "country_event = { id = DEUSEX.36 days = 1 }" in act
    triggers = _read("common/scripted_triggers/99_DEUSEX_augmentation_triggers.txt")
    industry = _named_block(triggers, "DEUSEX_has_augmentation_industry")
    assert "exists = yes" in industry
    assert "check_variable = { DEUSEX_aug_adoption > 0 }" in industry


def test_the_restoration_act_closes_the_growth_decisions():
    adopt = _event("DEUSEX.36").split("name = DEUSEX.36.b", 1)[0]
    assert "set_country_flag = DEUSEX_aug_restricted" in adopt
    assert "clr_country_flag = DEUSEX_aug_neuropozyne_funded" in adopt
    for decision in (
        "DEUSEX_fund_augmentation_research",
        "DEUSEX_military_augmentation_programme",
        "DEUSEX_fund_neuropozyne",
    ):
        visible = _named_block(_named_block(DECISIONS, decision), "visible")
        assert "NOT = { has_country_flag = DEUSEX_aug_restricted }" in visible


def test_costs_carry_ai_affordability_checks():
    for decision in ("DEUSEX_fund_augmentation_research", "DEUSEX_fund_neuropozyne"):
        weights = _named_block(_named_block(DECISIONS, decision), "ai_will_do")
        assert "has_active_mission = bankruptcy_incoming_collapse" in weights
        assert "ai_has_high_deficit = yes" in weights
    for event_id in ("DEUSEX.30", "DEUSEX.31", "DEUSEX.32", "DEUSEX.34"):
        paid = _event(event_id).split("name = ", 2)[1]
        assert "modify_treasury_effect = yes" in paid
        assert "has_active_mission = bankruptcy_incoming_collapse" in paid
        assert "ai_has_high_deficit = yes" in paid


def test_events_are_gated_and_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"(?m)^\tid = DEUSEX\.(\d+)$", EVENTS)]
    assert sorted(ids) == [30, 31, 32, 33, 34, 35, 36]
    for event_id in ids:
        head = _event(f"DEUSEX.{event_id}").split("option = {", 1)[0]
        gate = head[head.index("\n\ttrigger = {") :]
        assert "DEUSEX_scenario_enabled = yes" in _named_block(gate, "trigger")
    keys = re.findall(
        r"(?:title|text|desc|name|custom_effect_tooltip|tooltip) = (DEUSEX[A-Za-z0-9_.]*)",
        EVENTS + DECISIONS,
    )
    keys += re.findall(r"(?m)^\t(DEUSEX_[a-z_]+) = \{$", DECISIONS)
    keys += ["DEUSEX_augmentation_category", "DEUSEX_augmentation_industry"]
    for key in set(keys):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
    for line in LOC.splitlines()[1:]:
        assert re.match(r'^ [A-Za-z0-9_.]+: ".*"$', line), line
