import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "00_great_ai_race_effects.txt"
TRIGGERS_PATH = ROOT / "common" / "scripted_triggers" / "MD_great_ai_race_triggers.txt"
ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "MD_on_actions.txt"
GAME_RULES_PATH = ROOT / "common" / "game_rules" / "00_game_rules.txt"
DECISIONS_PATH = ROOT / "common" / "decisions" / "MD_great_ai_race_decisions.txt"
GAME_RULES_LOC_PATH = ROOT / "localisation" / "english" / "MD_game_rules_l_english.yml"
RACE_LOC_PATH = ROOT / "localisation" / "english" / "MD_great_ai_race_l_english.yml"

COUNTRY_CAPABILITIES = (
    "capability",
    "compute",
    "talent",
    "deployment",
    "control_capacity",
    "public_confidence",
)
COUNTRY_DERIVED_STATE = (
    "ai_race_public_alarm",
    "ai_race_control_debt",
    "ai_race_frontier_gap",
    "ai_race_rank",
)
GLOBAL_STATE = (
    "global.ai_race_frontier_capability",
    "global.ai_race_temperature",
    "global.ai_race_frontier_pressure",
    "global.ai_race_leader_id",
    "global.ai_race_epoch",
    "global.ai_race_last_processed_quarter",
    "global.ai_race_dirty_update_var",
)
UPSTREAM_PREFIXES = (
    "USA_ai_core_",
    "CHI_huawei_",
    "CHI_ic_inf_nsc",
    "energy_",
    "unfulfilled_energy_",
    "country_microchip_",
    "research_slots_",
)


def _extract_block(text: str, start: int) -> str:
    opening = text.index("{", start)
    depth = 0
    in_comment = False
    in_string = False
    escaped = False
    for index in range(opening, len(text)):
        character = text[index]
        if in_comment:
            if character == "\n":
                in_comment = False
            continue
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise AssertionError("Unclosed scripted block")


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, match.start())


def _variable_write_targets(text: str) -> set[str]:
    targets = set(
        re.findall(
            r"\b(?:set_variable|add_to_variable|subtract_from_variable)\s*=\s*"
            r"\{\s*([A-Za-z0-9_.]+)\s*=",
            text,
        )
    )
    targets.update(re.findall(r"\bclear_variable\s*=\s*([A-Za-z0-9_.]+)", text))
    targets.update(
        re.findall(
            r"\bclamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_.]+)",
            text,
        )
    )
    return targets


def test_race_is_the_sole_writer_of_its_persistent_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    writes = _variable_write_targets(effects)

    assert writes
    assert all(
        target.startswith("ai_race_") or target.startswith("global.ai_race_")
        for target in writes
    )
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)

    country_flags = re.findall(
        r"\b(?:set_country_flag|clr_country_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        effects,
    )
    global_flags = re.findall(
        r"\b(?:set_global_flag|clr_global_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        effects,
    )
    arrays = re.findall(
        r"\b(?:add_to_array|clear_array)\s*=\s*(?:\{\s*)?([A-Za-z0-9_.]+)",
        effects,
    )

    assert country_flags and all(flag.startswith("AI_RACE_") for flag in country_flags)
    assert global_flags and all(
        flag.startswith("GLOBAL_ai_race_") for flag in global_flags
    )
    assert arrays and all(array.startswith("global.ai_race_") for array in arrays)


def test_first_enabled_pulse_publishes_without_advancing_scheduled_state():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "ai_race_initialize_global")
    rebuild = _named_block(effects, "ai_race_rebuild_derived_state")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    quarterly = _named_block(effects, "ai_race_quarterly_reconcile")

    assert initialize.index("set_global_flag = GLOBAL_ai_race_initialized") < (
        initialize.index("ai_race_rebuild_derived_state = yes")
    )
    assert dispatch.index("ai_race_initialize_global = yes") < dispatch.index(
        "check_variable = { global.month = 1 }"
    )
    assert "ai_race_rebuild_country_metrics = yes" in rebuild
    assert "ai_race_rebuild_frontier_and_ranking = yes" in rebuild
    assert "global.ai_race_epoch" not in rebuild
    assert "global.ai_race_last_processed_quarter" not in rebuild
    assert "global.ai_race_dirty_update_var" not in rebuild
    assert "ai_race_rebuild_derived_state = yes" in quarterly
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert on_actions.count("ai_race_monthly_dispatch = yes") == 1


def test_modes_cleanup_and_participant_reentry_have_live_routes():
    triggers = TRIGGERS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    rules = GAME_RULES_PATH.read_text(encoding="utf-8")
    on_actions = ON_ACTIONS_PATH.read_text(encoding="utf-8")

    full = _named_block(triggers, "ai_race_full_mode")
    outcomes = _named_block(triggers, "ai_race_outcomes_only_mode")
    enabled = _named_block(triggers, "ai_race_enabled")
    eligible = _named_block(triggers, "ai_race_eligible_participant")
    refresh = _named_block(effects, "ai_race_refresh_participants")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    teardown = _named_block(effects, "ai_race_teardown_global")
    rule = _named_block(rules, "rule_ai_race")

    assert "option = outcomes_only" in full
    assert "option = disabled" in full
    assert "option = outcomes_only" in outcomes
    assert "ai_race_full_mode = yes" in enabled
    assert "ai_race_outcomes_only_mode = yes" in enabled
    assert "NOT = { has_country_flag = collapsed_nation }" in eligible
    assert "original_tag = USA" in eligible and "original_tag = CHI" in eligible
    assert "clr_country_flag = AI_RACE_active" in refresh
    assert "ai_race_initialize_country = yes" in refresh
    assert "ai_race_teardown_global = yes" in dispatch
    assert "ai_race_clear_country_state = yes" in teardown
    assert "clr_global_flag = GLOBAL_ai_race_initialized" in teardown
    assert "ai_race_monthly_dispatch = yes" in on_actions
    assert "name = full" in rule
    assert "name = outcomes_only" in rule
    assert "name = disabled" in rule


def test_country_adapters_use_one_energy_guard_and_all_ai_technology_tiers():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    rebuild = _named_block(effects, "ai_race_rebuild_country_metrics")

    assert "has_country_flag = USA_ai_core_state_initialized" in rebuild
    assert "CHI_corporate_systems_has_meaningful_state = yes" in rebuild
    assert "has_country_flag = CHI_huawei_state_initialized" in rebuild
    assert rebuild.count("check_variable = { energy_difference_variable < 0 }") == 2
    assert "check_variable = { energy_balance < 0 }" not in rebuild
    assert "unfulfilled_energy_demand_var" not in rebuild

    for tier in range(1, 15):
        assert (
            len(
                re.findall(
                    rf"\bhas_tech\s*=\s*artificial_intelligence_{tier}\b", rebuild
                )
            )
            == 2
        )

    first_clear = rebuild.index("clear_variable = ai_race_capability_external")
    first_owner_read = rebuild.index("USA_ai_core_frontier_capability")
    first_total = rebuild.index("set_variable = { ai_race_capability =")
    assert first_clear < first_owner_read < first_total


def test_rebuild_is_idempotent_and_quarter_wrapper_owns_replay_mutation():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    rebuild = _named_block(effects, "ai_race_rebuild_derived_state")
    quarterly = _named_block(effects, "ai_race_quarterly_reconcile")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    debug_repair = _named_block(effects, "ai_race_debug_repair")

    assert not any(
        target.endswith("_stock") for target in _variable_write_targets(metrics)
    )
    for capability in COUNTRY_CAPABILITIES:
        assert f"clear_variable = ai_race_{capability}_external" in metrics
        assert (
            f"set_variable = {{ ai_race_{capability} = ai_race_{capability}_stock }}"
            in metrics
        )
        assert (
            f"add_to_variable = {{ ai_race_{capability} = ai_race_{capability}_external }}"
            in metrics
        )

    for scheduled in (
        "global.ai_race_epoch",
        "global.ai_race_last_processed_quarter",
        "global.ai_race_dirty_update_var",
    ):
        assert scheduled not in rebuild
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert "global.ai_race_dirty_update_var" in quarterly
    assert "global.ai_race_last_processed_quarter" in dispatch
    assert "ai_race_quarterly_reconcile = yes" not in debug_repair
    assert "ai_race_rebuild_derived_state = yes" in debug_repair


def test_ranking_replay_guards_and_clamps_match_the_documented_bounds():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    repair_country = _named_block(effects, "ai_race_repair_country_state")
    repair_global = _named_block(effects, "ai_race_repair_global_state")
    ranking = _named_block(effects, "ai_race_rebuild_frontier_and_ranking")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")

    for capability in COUNTRY_CAPABILITIES:
        for suffix in ("_stock", "_external", ""):
            variable = f"ai_race_{capability}{suffix}"
            assert (
                f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
                in repair_country
            )
    for variable in COUNTRY_DERIVED_STATE[:2]:
        assert (
            f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
            in repair_country
        )
    assert (
        "clamp_variable = { var = ai_race_frontier_gap min = -100 max = 0 }"
        in repair_country
    )
    assert "clamp_variable = { var = ai_race_rank min = 0 max = 2 }" in repair_country
    for variable in GLOBAL_STATE[:3]:
        assert (
            f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
            in repair_global
        )

    assert "check_variable = { _chi_cap > _usa_cap }" in ranking
    assert ranking.index("else = {") < ranking.index(
        "USA = { set_variable = { ai_race_rank = 1 } }"
    )
    assert "set_variable = { ai_race_frontier_gap = ai_race_capability }" in ranking
    assert (
        "subtract_from_variable = { ai_race_frontier_gap = global.ai_race_frontier_capability }"
        in ranking
    )
    assert "global.ai_race_last_processed_quarter = ai_race_current_quarter" in dispatch
    for month in (1, 4, 7, 10):
        assert f"check_variable = {{ global.month = {month} }}" in dispatch


def test_debug_and_rule_localisation_match_the_headless_phase_contract():
    decisions = DECISIONS_PATH.read_text(encoding="utf-8")
    rules_loc_bytes = GAME_RULES_LOC_PATH.read_bytes()
    race_loc_bytes = RACE_LOC_PATH.read_bytes()

    for payload in (rules_loc_bytes, race_loc_bytes):
        assert payload.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in payload
        assert b":0" not in payload

    rules_loc = rules_loc_bytes.decode("utf-8-sig")
    race_loc = race_loc_bytes.decode("utf-8-sig")
    for key in (
        "RULE_AI_RACE",
        "RULE_AI_RACE_FULL",
        "RULE_AI_RACE_FULL_DESC",
        "RULE_AI_RACE_OUTCOMES_ONLY",
        "RULE_AI_RACE_OUTCOMES_ONLY_DESC",
        "RULE_AI_RACE_OFF",
        "RULE_AI_RACE_OFF_DESC",
    ):
        assert re.search(rf"(?m)^ {key}: ", rules_loc)
    for key in (
        "AI_RACE_debug_category",
        "AI_RACE_debug_category_desc",
        "AI_RACE_debug_readout",
        "AI_RACE_debug_readout_desc",
        "AI_RACE_debug_repair",
        "AI_RACE_debug_repair_desc",
    ):
        assert re.search(rf"(?m)^ {key}: ", race_loc)

    assert "complete simulation" not in rules_loc
    assert "autonomous choices" not in rules_loc
    assert "routine alerts" not in rules_loc
    assert "clocks are suppressed" not in rules_loc
    assert "available = { ai_race_enabled = yes }" not in decisions
    assert decisions.count('log = "[GetDateText]: [Root.GetName]: Decision ') == 2
