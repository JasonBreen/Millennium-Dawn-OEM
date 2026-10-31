import copy
import re

import pytest
import validate_decisions
import validate_localisation
from shared.ai_race_test_support import (
    ANTHROPIC_AXIS_WEIGHT,
    ANTHROPIC_CAPSTONE_DELTAS,
    ANTHROPIC_MAPPING,
    COUNTRY_CAPABILITIES,
    COUNTRY_DERIVED_STATE,
    DECISIONS_PATH,
    EFFECTS_PATH,
    EU_ANTHROPIC_MAPPING,
    EU_ANTHROPIC_WITHHELD,
    GAME_RULES_LOC_PATH,
    GAME_RULES_PATH,
    GLOBAL_STATE,
    ON_ACTIONS_PATH,
    RACE_GUI_PATH,
    RACE_LOC_PATH,
    ROOT,
    SCRIPTED_LOC_PATH,
    STARLINK_ADD,
    TRIGGERS_PATH,
    UPSTREAM_PREFIXES,
    XAI_CAPSTONE_DELTAS,
    XAI_MAPPING,
    RaceScript,
    _anthropic_block,
    _enrolled_race,
    _eu_anthropic_block,
    _extract_block,
    _named_block,
    _parse_race_script,
    _race_text,
    _review_and_commit,
    _variable_write_targets,
)
from shared.suite import build_validator, write_tree
from validate_localization_encoding import LocalizationValidator


def test_race_writes_only_its_state_and_the_economy_expense_hook():
    effects = _race_text("common/scripted_effects", "[0-9][0-9]_ai_race*.txt")
    writes = _variable_write_targets(effects)

    assert writes
    assert all(
        target.removeprefix("PREV.").startswith("ai_race_")
        or target.startswith("global.ai_race_")
        or target == "additional_expenses_rate"
        for target in writes
    )
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)
    for name, body in _parse_race_script(effects).items():
        if "additional_expenses_rate" in _variable_write_targets(
            _named_block(effects, name)
        ):
            assert name == "ai_race_refresh_finance_expense"

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
    effects = _race_text("common/scripted_effects")
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
    assert "ai_race_rebuild_derived_state = yes" in quarterly
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert on_actions.count("ai_race_monthly_dispatch = yes") == 1


def test_modes_cleanup_and_participant_reentry_have_live_routes():
    triggers = _race_text("common/scripted_triggers")
    effects = _race_text("common/scripted_effects")
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
    assert "original_tag" not in eligible
    assert "date > 2015.12.31" in eligible
    assert "has_tech = artificial_intelligence_7" in eligible
    assert "array = global.ai_race_all_initialized" in refresh
    assert "array = global.ai_race_all_initialized" in teardown
    discovery = _named_block(effects, "ai_race_discover_participants")
    assert "array = global.countries" in discovery
    assert "ai_race_initialize_country = yes" in discovery
    assert "ai_race_teardown_global = yes" in dispatch
    assert "ai_race_clear_country_state = yes" in teardown
    assert "clr_global_flag = GLOBAL_ai_race_initialized" in teardown
    assert "ai_race_monthly_dispatch = yes" in on_actions
    assert "name = full" in rule
    assert "name = outcomes_only" in rule
    assert "name = disabled" in rule


def test_capability_rebuild_counts_every_ai_technology_tier():
    effects = _race_text("common/scripted_effects")
    rebuild = _named_block(effects, "ai_race_rebuild_country_metrics")

    assert rebuild.count("ai_race_count_ai_technology = yes") == 2
    ladder = _named_block(effects, "ai_race_count_ai_technology")
    for tier in range(1, 15):
        assert (
            len(
                re.findall(
                    rf"\bhas_tech\s*=\s*artificial_intelligence_{tier}\b", effects
                )
            )
            == 1
        )
        assert f"has_tech = artificial_intelligence_{tier} }}" in ladder


def test_rebuild_is_idempotent_and_quarter_wrapper_owns_replay_mutation():
    effects = _race_text("common/scripted_effects")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    rebuild = _named_block(effects, "ai_race_rebuild_derived_state")
    quarterly = _named_block(effects, "ai_race_quarterly_reconcile")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    debug_repair = _named_block(effects, "ai_race_debug_repair_state")

    assert not any(
        target.endswith("_stock") for target in _variable_write_targets(metrics)
    )
    for axis in COUNTRY_CAPABILITIES:
        reset = f"set_variable = {{ ai_race_{axis} = ai_race_{axis}_stock }}"
        overlay = f"add_to_variable = {{ ai_race_{axis} = ai_race_{axis}_external }}"
        assert metrics.index(reset) < metrics.index(overlay)

    for scheduled in (
        "global.ai_race_epoch",
        "global.ai_race_last_processed_quarter",
    ):
        assert scheduled not in rebuild
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert "global.ai_race_last_processed_quarter" in dispatch
    assert "ai_race_quarterly_reconcile = yes" not in debug_repair
    assert "ai_race_rebuild_derived_state = yes" in debug_repair


def test_ranking_replay_guards_and_clamps_match_the_documented_bounds():
    effects = _race_text("common/scripted_effects")
    repair_country = _named_block(effects, "ai_race_repair_country_state")
    repair_global = _named_block(effects, "ai_race_repair_global_state")
    ranking = _named_block(effects, "ai_race_rebuild_frontier_and_ranking")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")

    for suffix in ("_stock", "_external", ""):
        assert (
            f"clamp_variable = {{ var = ai_race_capability{suffix} min = 0 max = 100 }}"
            in repair_country
        )
    assert (
        "clamp_variable = { var = ai_race_frontier_gap min = -100 max = 0 }"
        in repair_country
    )
    assert (
        "clamp_variable = { var = ai_race_rank min = 0 max = global.ai_race_all_initialized^num }"
        in repair_country
    )
    assert (
        "clamp_variable = { var = global.ai_race_frontier_capability min = 0 max = 100 }"
        in repair_global
    )

    assert "ai_race_sort_participants = yes" in ranking
    assert "global.ai_race_first_finisher_id" not in ranking
    assert (
        "ai_race_effective_capability > global.ai_race_frontier_capability" in ranking
    )
    assert (
        "set_variable = { ai_race_frontier_gap = ai_race_effective_capability }"
        in ranking
    )
    assert (
        "subtract_from_variable = { ai_race_frontier_gap = global.ai_race_frontier_capability }"
        in ranking
    )
    assert "global.ai_race_last_processed_quarter = ai_race_current_quarter" in dispatch
    for month in (1, 4, 7, 10):
        assert f"check_variable = {{ global.month = {month} }}" in dispatch


def test_player_facing_finance_and_shortfall_terms():
    loc = RACE_LOC_PATH.read_text(encoding="utf-8-sig")
    for term in (
        "Emergency AI Financing",
        "Outstanding AI Financing",
        "Capacity Shortfall",
    ):
        assert term in loc


def test_rule_labels_resolve_from_the_declared_rule_fields():
    rule = _parse_race_script(
        _named_block(GAME_RULES_PATH.read_text(encoding="utf-8"), "rule_ai_race")
    )["rule_ai_race"]
    keys = dict(
        validate_localisation._parse_loc_keys_from_text(
            GAME_RULES_LOC_PATH.read_text(encoding="utf-8-sig")
        )
    )
    labels = [value for key, _, value in rule if key == "name"]
    labels.extend(
        value
        for key, _, block in rule
        if key in {"default", "option"}
        for field, _, value in block
        if field in {"text", "desc"}
    )
    assert labels
    assert all(label.strip('"') in keys for label in labels)


@pytest.mark.parametrize(
    "check,category",
    [
        ("validate_missing_log", "missing-decision-log"),
        ("validate_missing_localisation", "missing-decision-localisation"),
    ],
)
@pytest.mark.parametrize("broken", [False, True])
def test_shared_decision_validation_covers_race_content(
    tmp_path, check, category, broken
):
    decisions = _race_text("common/decisions")
    loc = RACE_LOC_PATH.read_text(encoding="utf-8")
    if broken:
        if check == "validate_missing_log":
            decisions = re.sub(r"(?m)^\s*log\s*=.*$", "", decisions)
        else:
            loc = "\ufeffl_english:\n"
    write_tree(
        tmp_path,
        {
            "common/decisions/race.txt": decisions,
            "common/decisions/categories/race.txt": _race_text(
                "common/decisions/categories"
            ),
            "localisation/english/race_l_english.yml": loc,
        },
    )
    validator = validate_decisions.Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1
    )
    getattr(validator, check)()
    assert {issue.category for issue in validator._issues} == (
        {category} if broken else set()
    )


@pytest.mark.parametrize(
    "source", [RACE_LOC_PATH, GAME_RULES_LOC_PATH], ids=["race", "rules"]
)
@pytest.mark.parametrize("check", ["encoding", "yaml"])
@pytest.mark.parametrize("broken", [False, True])
def test_shared_localisation_validation_covers_race_content(
    tmp_path, source, check, broken
):
    text = source.read_text(encoding="utf-8")
    if broken:
        if check == "encoding":
            text = text.removeprefix("\ufeff")
        else:
            text = re.sub(r"(?m)^( [\w.-]+): ", r"\1:0 ", text, count=1)
    relative = "localisation/english/race_l_english.yml"
    write_tree(tmp_path, {relative: text})
    if check == "encoding":
        validator = LocalizationValidator()
        assert validator.validate_file(tmp_path / relative) is not broken
        assert bool(validator.errors) is broken
    else:
        validator = build_validator(validate_localisation.Validator, tmp_path)
        validator.validate_yaml_syntax()
        assert bool(validator._issues) is broken


def test_harness_rejects_the_unsupported_temporary_clear_effect():
    race = RaceScript()
    race.country(1)
    with pytest.raises(AssertionError, match="Unsupported effect clear_temp_variable"):
        race.execute([("clear_temp_variable", "=", "counter")], 1)


def test_harness_rejects_math_blocks_inside_variable_comparisons():
    race = RaceScript()
    race.country(1)
    script = _parse_race_script(
        "trigger = { check_variable = { var = counter value = { value = 2 multiply = 8 } } }"
    )["trigger"]
    with pytest.raises(AssertionError, match="check_variable needs a scalar value"):
        race.condition(script, 1)


def test_harness_rejects_value_statements_inside_math_conditionals():
    race = RaceScript()
    race.country(1)
    expression = _parse_race_script(
        "math = { value = 1 if = { limit = { value = 1 equals = 1 } value = 2 } }"
    )["math"]
    with pytest.raises(AssertionError, match="value is only the base"):
        race.value(expression, 1)


@pytest.mark.parametrize("initial, expected", [(0, 23), (1, 15), (2, 18)])
def test_harness_branches_observe_mutations_and_keep_nested_chains_independent(
    initial, expected
):
    race = RaceScript()
    country = race.country(1)
    country["vars"]["counter"] = initial
    script = _parse_race_script("""
        effects = {
            if = {
                limit = { check_variable = { counter = 0 } }
                set_variable = { counter = 1 }
                if = {
                    limit = { check_variable = { counter = 2 } }
                    set_variable = { counter = 100 }
                }
                else_if = {
                    limit = { check_variable = { counter = 1 } }
                    add_to_variable = { counter = 2 }
                }
                else = { set_variable = { counter = 1000 } }
            }
            else_if = {
                limit = { check_variable = { counter = 1 } }
                add_to_variable = { counter = 4 }
            }
            else = { add_to_variable = { counter = 6 } }
            if = {
                limit = { check_variable = { counter > 4 } }
                add_to_variable = { counter = 10 }
            }
            else = { add_to_variable = { counter = 20 } }
        }
        trigger = {
            if = {
                limit = { check_variable = { counter > 20 } }
                check_variable = { counter = 23 }
            }
            else = { check_variable = { counter < 20 } }
        }
        """)
    race.execute(script["effects"], 1)
    assert country["vars"]["counter"] == expected
    assert race.condition(script["trigger"], 1)
    country["vars"]["counter"] = 24
    assert not race.condition(script["trigger"], 1)


@pytest.mark.parametrize(
    "value, present", [("", False), ("value = 0", False), ("value = 1", True)]
)
def test_harness_timed_flag_presence_requires_nonzero_value(value, present):
    race = RaceScript()
    country = race.country(1)
    statements = _parse_race_script(
        f"effect = {{ set_country_flag = {{ flag = pending days = 9 {value} }} }}"
    )["effect"]
    race.execute(statements, 1)
    assert race._flag(country["flags"], "pending") is present
    race.goto(2016, 1, 9)
    assert race._flag(country["flags"], "pending") is present
    race.goto(2016, 1, 10)
    assert not race._flag(country["flags"], "pending")


@pytest.mark.parametrize("readiness", [0, 0.5, 1])
def test_readiness_withholds_only_the_funded_share_of_capability(readiness):
    race, country = _enrolled_race(ratios=[1] * 6)
    _review_and_commit(race)
    country["ratios"] = [readiness] * 6
    race.run("ai_race_refresh_dashboard", 1)

    variables = country["vars"]
    stock = variables["ai_race_capability_stock"]
    assert variables["ai_race_stage"] == 1
    assert stock == 5
    assert variables["ai_race_effective_capability"] == pytest.approx(
        variables["ai_race_capability_external"] + stock * readiness
    )


@pytest.mark.parametrize("readiness,expected", [(0, 80), (0.5, 97.5), (1, 100)])
def test_executed_funded_share_is_added_before_cap(readiness, expected):
    race, country = _enrolled_race()
    variables = country["vars"]
    variables.update(
        ai_race_stage=4,
        ai_race_capability_external=80,
        ai_race_capability_stock=35,
        ai_race_capability=100,
        ai_race_current_readiness=readiness,
    )

    for _ in range(2):
        race.run("ai_race_refresh_effective_capability", 1)
        assert variables["ai_race_effective_capability"] == pytest.approx(expected)
        assert variables["ai_race_capability"] == 100

    variables["ai_race_capability_stock"] = 0
    variables["ai_race_capability"] = 80
    race.run("ai_race_refresh_effective_capability", 1)
    assert variables["ai_race_effective_capability"] == 80


@pytest.mark.parametrize("mode", ["full", "outcomes_only", "disabled"])
def test_executed_unfunded_or_non_full_mode_keeps_combined_capability(mode):
    race, country = _enrolled_race(mode=mode)
    variables = country["vars"]
    variables.update(
        ai_race_stage=0 if mode == "full" else 4,
        ai_race_capability_external=80,
        ai_race_capability_stock=35,
        ai_race_capability=100,
        ai_race_current_readiness=0,
    )
    race.run("ai_race_refresh_effective_capability", 1)
    assert variables["ai_race_effective_capability"] == 100


def test_capability_stock_tracks_the_funded_stage_and_clears_with_progression():
    race, country = _enrolled_race(ratios=[1] * 6)
    variables = country["vars"]
    for stage, expected in ((0, 0), (1, 5), (2, 12), (3, 22), (4, 35)):
        variables["ai_race_stage"] = stage
        race.run("ai_race_refresh_capability_stock", 1)
        assert variables["ai_race_capability_stock"] == expected
    race.run("ai_race_clear_progression_state", 1)
    assert variables.get("ai_race_capability_stock", 0) == 0


@pytest.mark.parametrize(
    "financing,ratios,principal",
    [(False, [1] * 6, 0), (True, [1, 1, 0.75, 1, 1, 1], 550), (True, [0] * 6, 850)],
)
def test_executed_normal_and_emergency_transactions(financing, ratios, principal):
    race, country = _enrolled_race(ratios=ratios)
    _review_and_commit(race, financing=financing)
    assert country["vars"]["ai_race_stage"] == 1
    assert country["vars"].get("ai_race_stage_months", 0) == 0
    assert race.charges == [(1, -50)]
    assert country["vars"]["treasury"] == 99950
    assert len(country["ledger"]) == int(financing)
    if financing:
        stage, approved, weekly, term = country["ledger"][0]
        assert (stage, approved, term) == pytest.approx((1, principal, 520))
        assert weekly * term == pytest.approx(approved)


@pytest.mark.parametrize(
    "change",
    [
        "treasury",
        "ratio",
        "date",
        "tech",
        "bankruptcy",
        "skip_cost",
        "unsettled",
    ],
)
def test_executed_confirmation_rechecks_and_charges_nothing_on_invalid_state(change):
    race, country = _enrolled_race()
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    if change == "treasury":
        country["vars"]["treasury"] = 49.999
    elif change == "ratio":
        country["ratios"][0] = 0.999
    elif change == "date":
        race.goto(2015, 12, 31)
    elif change == "tech":
        country["techs"].clear()
    elif change == "bankruptcy":
        country["missions"].add("bankruptcy_incoming_collapse")
    elif change == "skip_cost":
        country["flags"]["MD_skip_treasury_cost"] = None
    else:
        country["vars"]["ai_race_capacity_settled"] = 0
    race.temps["ai_race_requested_financing"] = 0
    race.run("ai_race_commit_review", 1)
    assert race.charges == []
    assert country["vars"]["ai_race_stage"] == 0
    assert country["ledger"] == []
    assert race.events[-1] == (1, "ai_race.11")


@pytest.mark.parametrize("financing", [False, True])
def test_executed_gdp_change_invalidates_only_financed_confirmation(financing):
    ratios = [1, 1, 0.75, 1, 1, 1] if financing else [1] * 6
    race, country = _enrolled_race(ratios=ratios)
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    country["vars"]["gdp_total"] += 1
    race.temps["ai_race_requested_financing"] = int(financing)
    race.run("ai_race_commit_review", 1)
    if financing:
        assert race.charges == []
        assert country["vars"]["ai_race_stage"] == 0
        assert country["ledger"] == []
        assert race.events[-1] == (1, "ai_race.11")
    else:
        assert race.charges == [(1, -50)]
        assert country["vars"]["ai_race_stage"] == 1


@pytest.mark.parametrize("action", ["cancel", "expired", "duplicate"])
def test_executed_cancel_expiry_and_duplicate_confirmation(action):
    race, country = _enrolled_race()
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    race.temps["ai_race_requested_financing"] = 0
    if action == "cancel":
        race.run("ai_race_defer_review", 1)
    elif action == "expired":
        race.goto(2016, 1, 8)
    else:
        race.run("ai_race_commit_review", 1)
    race.run("ai_race_commit_review", 1)
    assert len(race.charges) == (1 if action == "duplicate" else 0)
    assert "AI_RACE_review_pending" not in country["flags"]


def test_executed_pending_lock_prevents_duplicate_dialogs_and_eventually_expires():
    race, _country = _enrolled_race()
    race.temps["ai_race_requested_stage"] = 1
    race.run("ai_race_begin_review", 1)
    race.run("ai_race_begin_review", 1)
    assert race.events == [(1, "ai_race.1")]
    race.goto(2016, 1, 10)
    race.run("ai_race_begin_review", 1)
    assert race.events == [(1, "ai_race.1"), (1, "ai_race.1")]


def test_executed_earliest_months_reach_terminal_in_january_2025_without_entry_credit():
    race, country = _enrolled_race(ai=True)
    for year in range(2016, 2026):
        for month in range(1, 13):
            if (year, month) > (2025, 1):
                break
            race.goto(year, month)
            race.run("ai_race_monthly_dispatch", 1)
            if (year, month) in {(2016, 1), (2019, 1), (2024, 1), (2025, 1)}:
                expected = {(2016, 1): 1, (2019, 1): 2, (2024, 1): 3, (2025, 1): 4}[
                    (year, month)
                ]
                assert country["vars"]["ai_race_stage"] == expected
                assert country["vars"].get("ai_race_stage_months", 0) == 0
    assert race.charges == [(1, -50), (1, -150), (1, -400), (1, -1000)]
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert race.events == [(1, "ai_race_news.1")]


def test_executed_progress_survives_shortage_and_repair_without_replay():
    race, country = _enrolled_race(ratios=[0.5] * 6)
    _review_and_commit(race, financing=True)
    race.goto(2016, 2)
    race.run("ai_race_monthly_dispatch", 1)
    assert country["vars"]["ai_race_stage_months"] == 1
    ledger = copy.deepcopy(country["ledger"])
    country["ratios"] = [0] * 6
    for action in (
        "ai_race_debug_repair_state",
        "ai_race_refresh_dashboard",
        "ai_race_monthly_dispatch",
    ):
        race.run(action, 1)
    reloaded = copy.deepcopy(race)
    reloaded.run("ai_race_monthly_dispatch", 1)
    assert reloaded.countries[1]["vars"]["ai_race_stage_months"] == 1
    assert reloaded.countries[1]["ledger"] == ledger
    variables = country["vars"]
    assert variables["ai_race_capability_stock"] == 5
    assert variables["ai_race_effective_capability"] == pytest.approx(
        variables["ai_race_capability"] - variables["ai_race_capability_stock"]
    )
    country["ratios"] = [1] * 6
    race.run("ai_race_refresh_dashboard", 1)
    assert variables["ai_race_effective_capability"] == variables["ai_race_capability"]
    assert variables["ai_race_effective_capability"] == 50
    assert country["ledger"] == ledger


@pytest.mark.parametrize("mode", ["full", "outcomes_only", "disabled"])
@pytest.mark.parametrize("corporate_mode", ["full", "outcomes_only", "disabled"])
def test_executed_mode_cross_product_and_late_start(mode, corporate_mode):
    race = RaceScript(mode, corporate_mode)
    country = race.country(1, ai=True)
    race.goto(2030, 6)
    race.run("ai_race_monthly_dispatch", 1)
    assert country["vars"].get("ai_race_stage", 0) == (1 if mode == "full" else 0)
    assert len(race.charges) == (1 if mode == "full" else 0)
    assert race.globals.get("ai_race_all_initialized", []) == (
        [] if mode == "disabled" else [1]
    )
    assert "ai_race_first_finisher_id" not in race.globals


def test_executed_generic_discovery_inactivity_return_and_off_cleanup():
    race = RaceScript()
    country = race.country(1, tag="BRA")
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1]
    _review_and_commit(race)
    country["exists"] = False
    race.goto(2016, 2)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_participants"] == []
    assert country["vars"]["ai_race_stage"] == 1
    country["exists"] = True
    country["techs"].clear()
    race.goto(2016, 3)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_participants"] == [1]
    assert country["vars"]["ai_race_stage_months"] == 1
    country["exists"] = False
    country["vars"]["debt"] = 123
    race.mode = "disabled"
    race.run("ai_race_monthly_dispatch", 1)
    assert not any(key.startswith("ai_race_") for key in country["vars"])
    assert country["flags"] == {}
    assert country["vars"]["debt"] == 123
    assert race.globals["ai_race_all_initialized"] == []


def test_executed_human_enrollment_between_discovery_and_next_january():
    race = RaceScript()
    race.country(1)
    later = race.country(2, tag="IND")
    later["techs"].clear()
    race.run("ai_race_monthly_dispatch", 1)
    race.goto(2016, 2)
    later["techs"].add("artificial_intelligence_7")
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1]
    race.run("ai_race_refresh_dashboard", 2)
    assert race.globals["ai_race_all_initialized"] == [1, 2]
    assert race.charges == []
    assert not later["vars"].get("ai_race_stage_months")


@pytest.mark.parametrize("mode", ["full", "outcomes_only", "disabled"])
@pytest.mark.parametrize("corporate_mode", ["full", "outcomes_only", "disabled"])
@pytest.mark.parametrize("year, ai", [(2015, False), (2016, False), (2016, True)])
def test_technology_completion_announces_human_enrollment_once_before_interaction(
    mode, corporate_mode, year, ai
):
    race = RaceScript(mode, corporate_mode)
    country = race.country(1, ai=ai)
    race.goto(year, 6)
    technology = _named_block(
        (ROOT / "common/technologies/engineering.txt").read_text(encoding="utf-8"),
        "artificial_intelligence_7",
    )
    completed = _parse_race_script(_named_block(technology, "on_research_complete"))[
        "on_research_complete"
    ]
    race.execute(completed, 1)
    eligible_human = mode != "disabled" and year >= 2016 and not ai
    assert race.unlocked_categories == (
        [(1, "AI_RACE_category")] if eligible_human else []
    )
    assert race.globals.get("ai_race_all_initialized", []) == (
        [1] if eligible_human else []
    )
    race.execute(completed, 1)
    assert len(race.unlocked_categories) == int(eligible_human)
    assert race.charges == country["ledger"] == []
    assert country["vars"].get("ai_race_stage", 0) == 0


def test_executed_ranking_stage_progress_capability_id_and_frontier_are_distinct():
    race = RaceScript()
    for identifier, stage, progress, capability in [
        (4, 1, 10, 80),
        (3, 2, 0, 20),
        (2, 1, 11, 50),
        (1, 1, 11, 50),
    ]:
        country = race.country(identifier, capability=capability)
        race.run("ai_race_initialize_country", identifier)
        country["vars"].update(
            ai_race_stage=stage,
            ai_race_stage_months=progress,
            ai_race_effective_capability=capability,
        )
    race.run("ai_race_rebuild_frontier_and_ranking", 4)
    assert race.globals["ai_race_ranked_participants"] == [3, 1, 2, 4]
    assert race.countries[3]["vars"]["ai_race_rank"] == 1
    assert race.globals["ai_race_frontier_capability"] == 80
    assert race.countries[3]["vars"]["ai_race_frontier_gap"] == -60
    assert "ai_race_first_finisher_id" not in race.globals


@pytest.mark.parametrize("reverse", [False, True])
def test_executed_simultaneous_autonomous_terminal_candidates_have_one_historical_winner(
    reverse,
):
    race = RaceScript()
    for identifier, capability in (
        [(3, 60), (2, 80), (1, 80)] if not reverse else [(1, 80), (2, 80), (3, 60)]
    ):
        country = race.country(identifier, ai=True, capability=capability)
        race.run("ai_race_initialize_country", identifier)
        country["vars"].update(
            ai_race_stage=3,
            ai_race_stage_months=11,
            ai_race_stage_entry_month=2024 * 12 + 1,
        )
    race.goto(2025, 1)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert all(
        country["vars"]["ai_race_stage"] == 4 for country in race.countries.values()
    )
    assert [event for event in race.events if event[1] == "ai_race_news.1"] == [
        (1, "ai_race_news.1")
    ]
    race.countries[1]["exists"] = False
    race.run("ai_race_rebuild_derived_state", 2)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert race.countries[2]["vars"]["ai_race_rank"] == 1


@pytest.mark.parametrize(
    "constraint", ["allowed", "readiness", "debt", "weekly", "reserve"]
)
def test_executed_autonomous_emergency_policy_boundaries(constraint):
    race, country = _enrolled_race(ai=True, ratios=[0.75] * 6)
    country["vars"]["debt"] = 599.999
    if constraint == "readiness":
        country["ratios"][5] = 0.749
    elif constraint == "debt":
        country["vars"]["debt"] = 600
    elif constraint == "weekly":
        country["vars"]["treasury_rate"] = 550 / 520 - 0.001
    elif constraint == "reserve":
        country["vars"]["treasury"] = 50 + (2 + 550 / 520) * 52 - 0.001
    race.run("ai_race_autonomous_purchase", 1)
    assert bool(country["ledger"]) is (constraint == "allowed")
    assert len(race.charges) == (1 if constraint == "allowed" else 0)


@pytest.mark.parametrize(
    "stage,year,technology", [(0, 2016, 7), (1, 2019, 7), (2, 2024, 8), (3, 2025, 8)]
)
def test_executed_stage_dates_technology_and_completed_work_are_all_required(
    stage, year, technology
):
    race, country = _enrolled_race(stage=stage, year=year)
    race.goto(year - 1, 12, 31)
    assert not race.condition(race.triggers["ai_race_can_review"], 1)
    race.goto(year, 1)
    assert race.condition(race.triggers["ai_race_can_review"], 1)
    country["techs"].discard(f"artificial_intelligence_{technology}")
    assert not race.condition(race.triggers["ai_race_can_review"], 1)
    country["techs"].add(f"artificial_intelligence_{technology}")
    if stage:
        country["vars"]["ai_race_stage_months"] -= 1
        assert not race.condition(race.triggers["ai_race_can_review"], 1)


@pytest.mark.parametrize("criterion", range(6))
def test_executed_direct_funding_requires_every_readiness_boundary(criterion):
    race, country = _enrolled_race()
    country["ratios"][criterion] = 0.999
    _review_and_commit(race)
    assert race.charges == []
    country["ratios"][criterion] = 1
    _review_and_commit(race)
    assert race.charges == [(1, -50)]


def test_executed_two_human_finishers_receive_reports_but_only_one_world_announcement():
    race, first = _enrolled_race(stage=3, year=2025)
    second = race.country(2, tag="JAP")
    race.run("ai_race_initialize_country", 2)
    second["vars"].update(ai_race_stage=3, ai_race_stage_months=12)
    race.run("ai_race_refresh_operating_state", 2)
    _review_and_commit(race)
    _review_and_commit(race, identifier=2)
    assert first["vars"]["ai_race_stage"] == second["vars"]["ai_race_stage"] == 4
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert [
        (country, event)
        for country, event in race.events
        if event in {"ai_race_news.1", "ai_race.10"}
    ] == [(1, "ai_race_news.1"), (1, "ai_race.10"), (2, "ai_race.10")]


def test_executed_annual_discovery_enrolls_new_ai_without_resetting_existing_history():
    race, first = _enrolled_race()
    _review_and_commit(race)
    later = race.country(2, ai=True)
    later["techs"].clear()
    race.run("ai_race_monthly_dispatch", 1)
    later["techs"].add("artificial_intelligence_7")
    race.goto(2016, 12)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1]
    race.goto(2017, 1)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_all_initialized"] == [1, 2]
    assert first["vars"]["ai_race_stage"] == later["vars"]["ai_race_stage"] == 1
    assert later["vars"].get("ai_race_stage_months", 0) == 0


def test_executed_outcomes_cleanup_preserves_historical_first_until_off():
    race, country = _enrolled_race(stage=3, year=2025, ratios=[0.5] * 6)
    _review_and_commit(race, financing=True)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert country["vars"]["ai_race_bonus"] == pytest.approx(0.025)
    assert country["vars"]["ai_race_demand_power"] == 60
    country["vars"]["debt"] = 77
    race.mode = "outcomes_only"
    race.run("ai_race_refresh_dashboard", 1)
    assert country["vars"].get("ai_race_stage", 0) == 0
    assert country["ledger"] == []
    assert country["vars"]["debt"] == 77
    assert country["vars"]["ai_race_bonus"] == 0
    assert country["vars"]["ai_race_demand_power"] == 0
    assert country["vars"]["ai_race_effective_capability"] == 50
    assert race.globals["ai_race_ranked_participants"] == [1]
    assert race.globals["ai_race_first_finisher_id"] == 1

    race.mode = "full"
    second = race.country(2, tag="JAP")
    race.run("ai_race_initialize_country", 2)
    second["vars"].update(ai_race_stage=3, ai_race_stage_months=12)
    race.run("ai_race_refresh_operating_state", 2)
    _review_and_commit(race, identifier=2)
    assert second["vars"]["ai_race_stage"] == 4
    assert second["vars"]["ai_race_bonus"] == pytest.approx(0.04)
    assert race.globals["ai_race_first_finisher_id"] == 1
    assert [event for event in race.events if event[1] == "ai_race_news.1"] == [
        (1, "ai_race_news.1")
    ]

    race.mode = "disabled"
    race.run("ai_race_monthly_dispatch", 1)
    assert "ai_race_first_finisher_id" not in race.globals


@pytest.mark.parametrize("readiness,expected", [(0, 0), (0.5, 17.5), (1, 35)])
def test_dashboard_usable_funded_share_runs_from_source(readiness, expected):
    race, country = _enrolled_race()
    variables = country["vars"]
    variables.update(
        ai_race_stage=4,
        ai_race_capability_stock=35,
        ai_race_capability=100,
        ai_race_current_readiness=readiness,
    )
    race.run("ai_race_refresh_effective_capability", 1)
    assert variables["ai_race_capability_funded_usable"] == pytest.approx(expected)
    variables["ai_race_stage"] = 0
    race.run("ai_race_refresh_effective_capability", 1)
    assert variables["ai_race_capability_funded_usable"] == 0


@pytest.mark.parametrize("mode", ["outcomes_only", "disabled"])
def test_dashboard_funded_share_is_hidden_outside_full_mode(mode):
    race, country = _enrolled_race(mode=mode)
    variables = country["vars"]
    variables.update(
        ai_race_stage=4,
        ai_race_capability_stock=35,
        ai_race_capability=100,
        ai_race_current_readiness=1,
    )
    race.run("ai_race_refresh_effective_capability", 1)
    assert variables["ai_race_capability_funded_usable"] == 0


def test_dashboard_breakdown_tooltip_is_reachable():
    if not RACE_GUI_PATH.exists():
        pytest.skip("interface/ not in this checkout")
    gui = RACE_GUI_PATH.read_text(encoding="utf-8")
    assert 'pdx_tooltip = "[ai_race_capability_breakdown]"' in gui


def test_dashboard_breakdown_has_all_score_inputs():
    loc = RACE_LOC_PATH.read_text(encoding="utf-8-sig")
    scripted = SCRIPTED_LOC_PATH.read_text(encoding="utf-8")
    for value in (
        "ai_race_capability_external",
        "ai_race_capability_stock",
        "ai_race_capability_funded_usable",
        "ai_race_effective_capability",
    ):
        assert f"[?ROOT.{value}|1]" in loc
    assert (
        "ai_race_full_mode = yes"
        in scripted.split("name = ai_race_capability_breakdown", 1)[1].split(
            "name = ai_race_current_bottleneck", 1
        )[0]
    )


@pytest.mark.parametrize(
    "ratios,expected",
    [
        ([1, 1, 1, 1, 1, 1], "none"),
        ([0.5, 0.5, 0.5, 0.5, 0.5, 0.5], "civs"),
        ([1, 0.5, 0.5, 1, 1, 1], "network"),
        ([1, 1, 0.5, 0.5, 1, 1], "power"),
        ([1, 1, 1, 0.5, 0.5, 1], "microchips"),
        ([1, 1, 1, 1, 0.5, 0.5], "composites"),
        ([1, 1, 1, 1, 1, 0.5], "oil"),
    ],
)
def test_dashboard_bottleneck_source_order_resolves_ties(ratios, expected):
    scripted = SCRIPTED_LOC_PATH.read_text(encoding="utf-8")
    start = scripted.index("name = ai_race_current_bottleneck")
    block = scripted[start : scripted.index("\n}", start)]
    choices = re.findall(
        r"ai_race_current_(civs|network|power|microchips|composites|oil)_ratio "
        r"= ai_race_current_readiness",
        block,
    )
    assert choices == list(RaceScript.criteria)
    readiness = min(ratios)
    selected = (
        "none"
        if readiness == 1
        else next(name for name in choices if ratios[choices.index(name)] == readiness)
    )
    assert selected == expected
    assert f"AI_RACE_bottleneck_{selected}" in block


@pytest.mark.parametrize("value,expected", [(2, 1), (10, 9), (11, 111)])
def test_documented_math_conditionals_use_expression_limits(value, expected):
    race = RaceScript()
    country = race.country(1)
    country["vars"]["math_input"] = value
    expression = _parse_race_script(
        "math = { value = math_input if = { limit = { value = math_input greater_than = 10 } add = 100 } else = { subtract = 1 } }"
    )["math"]
    assert race.value(expression, 1) == expected


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


def test_first_enabled_pulse_publishes_without_advancing_scheduled_state_oem():
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
    assert "ai_race_rebuild_derived_state = yes" in quarterly
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert on_actions.count("ai_race_monthly_dispatch = yes") == 1


def test_modes_cleanup_and_participant_reentry_have_live_routes_oem():
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
    assert "original_tag" not in eligible
    assert "date > 2015.12.31" in eligible
    assert "has_tech = artificial_intelligence_7" in eligible
    assert "array = global.ai_race_all_initialized" in refresh
    assert "array = global.ai_race_all_initialized" in teardown
    discovery = _named_block(effects, "ai_race_discover_participants")
    assert "array = global.countries" in discovery
    assert "ai_race_initialize_country = yes" in discovery
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

    assert rebuild.count("ai_race_count_ai_technology = yes") == 2
    generic_adapter = _named_block(effects, "ai_race_generic_adapter")
    assert generic_adapter.count("ai_race_count_ai_technology = yes") == 1
    ladder = _named_block(effects, "ai_race_count_ai_technology")
    for tier in range(1, 15):
        assert (
            len(
                re.findall(
                    rf"\bhas_tech\s*=\s*artificial_intelligence_{tier}\b", effects
                )
            )
            == 1
        )
        assert f"has_tech = artificial_intelligence_{tier} }}" in ladder

    first_clear = rebuild.index("clear_variable = ai_race_capability_external")
    first_owner_read = rebuild.index("USA_ai_core_frontier_capability")
    first_total = rebuild.index("set_variable = { ai_race_capability =")
    assert first_clear < first_owner_read < first_total


def test_rebuild_is_idempotent_and_quarter_wrapper_owns_replay_mutation_oem():
    effects = _race_text("common/scripted_effects")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    rebuild = _named_block(effects, "ai_race_rebuild_derived_state")
    quarterly = _named_block(effects, "ai_race_quarterly_reconcile")
    dispatch = _named_block(effects, "ai_race_monthly_dispatch")
    debug_repair = _named_block(effects, "ai_race_debug_repair_state")

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
    ):
        assert scheduled not in rebuild
    assert "add_to_variable = { global.ai_race_epoch = 1 }" in quarterly
    assert "global.ai_race_last_processed_quarter" in dispatch
    assert "ai_race_quarterly_reconcile = yes" not in debug_repair
    assert "ai_race_rebuild_derived_state = yes" in debug_repair


def test_ranking_replay_guards_and_clamps_match_the_documented_bounds_oem():
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
    assert (
        "clamp_variable = { var = ai_race_rank min = 0 max = global.ai_race_all_initialized^num }"
        in repair_country
    )
    for variable in GLOBAL_STATE[:3]:
        assert (
            f"clamp_variable = {{ var = {variable} min = 0 max = 100 }}"
            in repair_global
        )

    assert "ai_race_sort_participants = yes" in ranking
    assert "global.ai_race_first_finisher_id" not in ranking
    assert (
        "ai_race_effective_capability > global.ai_race_frontier_capability" in ranking
    )
    assert (
        "set_variable = { ai_race_frontier_gap = ai_race_effective_capability }"
        in ranking
    )
    assert (
        "subtract_from_variable = { ai_race_frontier_gap = global.ai_race_frontier_capability }"
        in ranking
    )
    assert "global.ai_race_last_processed_quarter = ai_race_current_quarter" in dispatch
    for month in (1, 4, 7, 10):
        assert f"check_variable = {{ global.month = {month} }}" in dispatch


def test_debug_and_playable_decisions_have_localisation_and_logging():
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

    for decision in ("research", "implementation", "expansion", "frontier"):
        name = f"AI_RACE_review_{decision}"
        block = _named_block(decisions, name)
        assert f"Decision {name}" in block
        assert re.search(rf"(?m)^ {name}: ", race_loc)
    assert "Emergency AI Financing" in race_loc
    assert "Outstanding AI Financing" in race_loc
    assert "Capacity Shortfall" in race_loc


def test_executed_progress_survives_shortage_and_repair_without_replay_oem():
    race, country = _enrolled_race(ratios=[0.5] * 6)
    _review_and_commit(race, financing=True)
    race.goto(2016, 2)
    race.run("ai_race_monthly_dispatch", 1)
    assert country["vars"]["ai_race_stage_months"] == 1
    ledger = copy.deepcopy(country["ledger"])
    country["ratios"] = [0] * 6
    for action in (
        "ai_race_debug_repair_state",
        "ai_race_refresh_dashboard",
        "ai_race_monthly_dispatch",
    ):
        race.run(action, 1)
    reloaded = copy.deepcopy(race)
    reloaded.run("ai_race_monthly_dispatch", 1)
    assert reloaded.countries[1]["vars"]["ai_race_stage_months"] == 1
    assert reloaded.countries[1]["ledger"] == ledger
    variables = country["vars"]
    assert variables["ai_race_capability_stock"] == 5
    assert variables["ai_race_effective_capability"] == pytest.approx(
        variables["ai_race_capability"] - variables["ai_race_capability_stock"]
    )
    country["ratios"] = [1] * 6
    race.run("ai_race_refresh_dashboard", 1)
    assert variables["ai_race_effective_capability"] == variables["ai_race_capability"]
    assert variables["ai_race_effective_capability"] == 50
    assert country["ledger"] == ledger


def test_anthropic_contribution_runs_on_both_united_states_adapter_paths():
    effects = _race_text("common/scripted_effects")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")

    # Corporate History on and its fallback both reach the lab overlay.
    assert metrics.count("ai_race_usa_anthropic_contribution = yes") == 2


def test_anthropic_axes_map_to_their_exact_external_at_the_stated_weight():
    block = _anthropic_block()

    for external, axis in ANTHROPIC_MAPPING:
        expected = (
            f"add_to_variable = {{ {external} = "
            f"{{ value = {axis} multiply = {ANTHROPIC_AXIS_WEIGHT} }} }}"
        )
        assert block.count(expected) == 1, expected

    # No axis reaches an external it was not assigned to.
    for _, axis in ANTHROPIC_MAPPING:
        owner = next(ext for ext, a in ANTHROPIC_MAPPING if a == axis)
        for line in block.splitlines():
            if axis in line:
                assert owner in line, (axis, owner, line.strip())


def test_anthropic_capstone_overlays_apply_their_exact_deltas():
    block = _anthropic_block()
    branches = re.split(r"(?=has_idea = USA_anthropic_)", block)[1:]
    assert len(branches) == len(ANTHROPIC_CAPSTONE_DELTAS), len(branches)

    seen = {}
    for branch in branches:
        capstone = re.match(r"has_idea = (USA_anthropic_[A-Za-z_]+)", branch).group(1)
        deltas = re.findall(
            r"add_to_variable\s*=\s*\{\s*(ai_race_[a-z_]+_external)\s*=\s*(\d+)\s*\}",
            branch,
        )
        seen[capstone] = tuple((name, int(value)) for name, value in deltas)

    assert seen == {k: tuple(v) for k, v in ANTHROPIC_CAPSTONE_DELTAS.items()}


def test_anthropic_contribution_is_additive_read_only_and_gated():
    block = _anthropic_block()

    assert "corporate_history_enabled = yes" in block
    assert "has_country_flag = USA_anthropic_state_initialized" in block

    # Only external slots move, and only upward from the adapter's own baseline.
    writes = _variable_write_targets(block)
    assert writes
    assert all(target.endswith("_external") for target in writes), writes
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)
    assert "set_variable" not in block
    assert "subtract_from_variable" not in block


def test_anthropic_capstone_overlay_applies_at_most_once():
    block = _anthropic_block()
    capstone_start = block.index("has_idea = USA_anthropic_safety_governed_frontier")
    tail = block[capstone_start:]

    # One if plus three else_if, so the capstones cannot stack.
    assert tail.count("has_idea = USA_anthropic_") == len(ANTHROPIC_CAPSTONE_DELTAS)
    assert tail.count("else_if") == len(ANTHROPIC_CAPSTONE_DELTAS) - 1


def test_eu_contribution_runs_after_every_adapter_has_written_its_externals():
    effects = _race_text("common/scripted_effects")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")

    assert metrics.count("ai_race_eu_anthropic_contribution = yes") == 1
    # The generic adapter assigns externals with set_variable, so an EU overlay
    # placed before it would be overwritten instead of added.
    assert metrics.index("ai_race_generic_adapter = yes") < metrics.index(
        "ai_race_eu_anthropic_contribution = yes"
    )
    assert metrics.index("ai_race_eu_anthropic_contribution = yes") < metrics.index(
        "set_variable = { ai_race_capability = ai_race_capability_stock }"
    )


def test_eu_anthropic_mapping_is_exact_and_withholds_ownership_axes():
    block = _eu_anthropic_block()

    for external, axis, weight in EU_ANTHROPIC_MAPPING:
        expected = (
            f"add_to_variable = {{ {external} = "
            f"{{ value = USA.{axis} multiply = {weight} }} }}"
        )
        assert block.count(expected) == 1, expected

    for withheld in EU_ANTHROPIC_WITHHELD:
        assert withheld not in block, withheld

    writes = _variable_write_targets(block)
    assert writes == {external for external, _, _ in EU_ANTHROPIC_MAPPING}, writes
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)
    assert "set_variable" not in block


def test_eu_contribution_covers_every_european_union_shape():
    block = _eu_anthropic_block()

    # Sovereign members, including an EU112 federation, keep the membership idea.
    assert "has_idea = EU_member" in block
    # A formed United States of Europe removes EU_member, so it is found by its flag.
    # The reserved formable id is deliberately not read here: validate_decisions
    # rejects any inline formable_committed_id literal at or above 100.
    assert "has_country_flag = USoE" in block
    # Turning the EU off entirely withdraws the contribution.
    assert "NOT = { has_global_flag = GAME_RULE_eu_disabled }" in block
    # The lab has to exist and be running somewhere, and access is not free in wartime.
    assert "has_country_flag = USA_anthropic_state_initialized" in block
    assert "NOT = { has_war_with = USA }" in block
    assert "NOT = { original_tag = USA }" in block
    assert "corporate_history_enabled = yes" in block


def test_eu111_formation_drops_membership_so_the_sentinel_is_required():
    """The sentinel branch is load-bearing, not belt-and-braces."""
    voting = (
        ROOT / "common" / "scripted_effects" / "99_EU_voting_scripted_effects.txt"
    ).read_text(encoding="utf-8")
    result = _named_block(voting, "focus_EU111_QMV_result")
    assert "remove_ideas = EU_member" in result


def test_dashboard_capability_inputs_are_sampled_before_the_lab_overlay():
    effects = _race_text("common/scripted_effects")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    assert (
        metrics.count(
            "set_variable = { ai_race_capability_national_input = ai_race_capability_external }"
        )
        == 3
    )
    assert (
        metrics.count(
            "set_variable = { ai_race_capability_lab_overlay = ai_race_capability_external }"
        )
        == 3
    )
    assert (
        metrics.count(
            "subtract_from_variable = { ai_race_capability_lab_overlay = ai_race_capability_national_input }"
        )
        == 3
    )
    assert metrics.count("clear_variable = ai_race_capability_lab_overlay") == 1
    assert metrics.index("ai_race_eu_anthropic_contribution = yes") < metrics.rindex(
        "set_variable = { ai_race_capability_lab_overlay = ai_race_capability_external }"
    )


def test_dashboard_breakdown_has_all_score_inputs_and_is_reachable():
    gui = RACE_GUI_PATH.read_text(encoding="utf-8")
    loc = RACE_LOC_PATH.read_text(encoding="utf-8-sig")
    scripted = SCRIPTED_LOC_PATH.read_text(encoding="utf-8")
    assert 'pdx_tooltip = "[ai_race_capability_breakdown]"' in gui
    for value in (
        "ai_race_capability_national_input",
        "ai_race_capability_lab_overlay",
        "ai_race_capability_external",
        "ai_race_capability_stock",
        "ai_race_capability_funded_usable",
        "ai_race_effective_capability",
    ):
        assert f"[?ROOT.{value}|1]" in loc
    assert (
        "ai_race_full_mode = yes"
        in scripted.split("name = ai_race_capability_breakdown", 1)[1].split(
            "name = ai_race_current_bottleneck", 1
        )[0]
    )


def test_xai_contribution_writes_only_race_state_and_reads_starlink_once():
    effects = _race_text("common/scripted_effects")
    metrics = _named_block(effects, "ai_race_rebuild_country_metrics")
    block = _named_block(effects, "ai_race_usa_xai_contribution")
    europe = _named_block(effects, "ai_race_eu_anthropic_contribution")

    assert metrics.count("ai_race_usa_xai_contribution = yes") == 2
    assert metrics.index("ai_race_usa_anthropic_contribution = yes") < metrics.index(
        "ai_race_usa_xai_contribution = yes"
    )
    assert "USA_spacex_" not in europe
    assert "ai_race_usa_xai_contribution" not in europe
    assert "USA_xai_reconstruct_complete" not in block
    assert "corporate_history_enabled = yes" in block
    assert "has_country_flag = USA_xai_state_initialized" in block

    for external, axis in XAI_MAPPING:
        expected = (
            f"add_to_variable = {{ {external} = "
            f"{{ value = {axis} multiply = 2 }} }}"
        )
        assert block.count(expected) == 1, expected

    writes = _variable_write_targets(block)
    assert writes
    assert all(target.startswith("ai_race_") for target in writes), writes
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)

    branches = re.split(r"(?=has_idea = USA_xai_)", block)[1:]
    assert len(branches) == len(XAI_CAPSTONE_DELTAS)
    assert block.count("else_if") == len(XAI_CAPSTONE_DELTAS) - 1

    assert effects.count(STARLINK_ADD) == 1
    guard = block.index("has_country_flag = USA_spacex_state_initialized")
    starlink_if = _extract_block(block, block.rindex("if = {", 0, guard))
    assert STARLINK_ADD in starlink_if
    assert (
        "check_variable = { var = USA_spacex_leo_satcom_presence value = 1 compare = greater_than_or_equals }"
        in starlink_if
    )
    assert "multiply" not in starlink_if
    assert block.count(STARLINK_ADD) == 1


def test_xai_talent_raid_dents_openai_under_one_flag():
    openai = (
        ROOT / "common" / "scripted_effects" / "USA_openai_effects.txt"
    ).read_text(encoding="utf-8")
    xai = (ROOT / "common" / "scripted_effects" / "USA_xai_effects.txt").read_text(
        encoding="utf-8"
    )
    dent = _named_block(openai, "USA_openai_apply_xai_talent_dent")
    route = _named_block(xai, "USA_xai_apply_talent_route")

    assert "has_country_flag = USA_openai_state_initialized" in dent
    assert "NOT = { has_country_flag = USA_xai_openai_talent_taken }" in dent
    assert "add_to_variable = { USA_openai_frontier_capability = -1 }" in dent
    assert "add_to_variable = { USA_openai_deployment_reach = -1 }" in dent
    assert "USA_openai_clamp_state = yes" in dent
    assert "set_country_flag" not in dent
    assert route.count("USA_openai_apply_xai_talent_dent = yes") == 1
    assert route.count("set_country_flag = USA_xai_openai_talent_taken") == 1
    assert xai.count("set_country_flag = USA_xai_openai_talent_taken") == 1


def test_xai_followup_tooltips_name_treasury_duration_and_corporate_history():
    loc = (ROOT / "localisation" / "english" / "MD_focus_USA_l_english.yml").read_text(
        encoding="utf-8-sig"
    )
    decisions = (ROOT / "common" / "decisions" / "USA.txt").read_text(encoding="utf-8")

    def _desc(key):
        return next(line for line in loc.splitlines() if line.startswith(f" {key}:"))

    for key, treasury in (
        ("USA_xai_colossus_scale_decision_desc", "25 billion"),
        ("USA_xai_grok_deployment_decision_desc", "15 billion"),
        ("USA_xai_colossus_expansion_decision_desc", "25 billion"),
        ("USA_xai_grok_platform_decision_desc", "15 billion"),
    ):
        line = _desc(key)
        assert "Corporate History" in line
        assert "365 days" in line
        assert treasury in line
    for key in (
        "USA_xai_talent_concentration_decision_desc",
        "USA_xai_truth_seeking_charter_decision_desc",
        "USA_xai_open_weights_decision_desc",
    ):
        line = _desc(key)
        assert "Corporate History" in line
        assert "365 days" in line
    assert "does not draw on the treasury" in _desc(
        "USA_xai_open_weights_decision_desc"
    )

    expansion = _named_block(decisions, "USA_xai_colossus_expansion_decision")
    assert "has_country_flag = USA_xai_colossus_chosen" in expansion
    assert "set_country_flag = USA_xai_followup_set" in expansion
    assert "factor = 5" in expansion.split("ai_will_do", 1)[1]
    platform = _named_block(decisions, "USA_xai_grok_platform_decision")
    weights = _named_block(decisions, "USA_xai_open_weights_decision")
    assert "has_country_flag = USA_xai_grok_chosen" in platform
    assert "USA_xai_deployment" in platform
    assert "factor = 5" not in platform
    assert "factor = 5" not in weights
    assert "is_historical_focus_on = yes" in platform
    assert "is_historical_focus_on = yes" in weights
    for block in (expansion, platform, weights):
        assert "NOT = { has_country_flag = USA_xai_followup_set }" in block
        assert "has_country_flag = USA_xai_state_initialized" in block
        assert "365" in block
