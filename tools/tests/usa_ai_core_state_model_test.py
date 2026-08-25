import json
import re
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "USA_ai_core_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_ai_core_effects.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "USA_ai_core_ideas.txt"
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_USA_l_english.yml"
COMMON_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_effects.txt"
)
DISPATCH_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_dispatch_effects.txt"
)
MONTHLY_DISPATCH_PATH = (
    ROOT
    / "common"
    / "scripted_effects"
    / "00_corporate_history_monthly_dispatch_effects.txt"
)
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
SCENARIOS_PATH = ROOT / "tools" / "corporate_history_scenarios.json"

AXES = {
    "USA_ai_core_frontier_capability": 2,
    "USA_ai_core_compute_depth": 3,
    "USA_ai_core_ecosystem_openness": 6,
    "USA_ai_core_state_alignment": 2,
    "USA_ai_core_infrastructure_burden": 1,
    "USA_ai_core_public_legitimacy": 5,
}

MILESTONES = (
    (1, 2001, "2001.1.29"),
    (2, 2006, "2006.3.14"),
    (3, 2012, "2012.12.3"),
    (4, 2016, "2016.10.12"),
    (5, 2017, "2017.6.12"),
    (6, 2019, "2019.2.11"),
    (7, 2020, "2020.8.26"),
    (8, 2022, "2022.10.4"),
    (9, 2023, "2023.10.30"),
    (10, 2024, "2024.12.20"),
    (11, 2025, "2025.7.23"),
    (12, 2026, "2026.3.4"),
)

OUTCOMES = {
    "USA_ai_core_private_frontier_primacy",
    "USA_ai_core_open_innovation_ecosystem",
    "USA_ai_core_federal_compute_compact",
    "USA_ai_core_resilient_industrial_base",
    "USA_ai_core_power_constrained_leadership",
}

ENERGY_READS = {
    "energy_balance",
    "unfulfilled_energy_demand_var",
    "energy_difference_variable",
}


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


def _event_block(text: str, event_number: int) -> str:
    event_id = f"USA_ai_core_events.{event_number}"
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, match.start())
        if re.search(rf"\bid\s*=\s*{re.escape(event_id)}\b", block):
            return block
    raise AssertionError(f"Missing event {event_id}")


def _option_blocks(event: str) -> List[str]:
    return [
        _extract_block(event, match.start())
        for match in re.finditer(r"(?m)^\toption\s*=\s*\{", event)
    ]


def test_state_contract_initialization_and_clamps_match():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "USA_ai_core_initialize_state")
    clamp = _named_block(effects, "USA_ai_core_clamp_state")

    assert "NOT = { has_country_flag = USA_ai_core_state_initialized }" in initialize
    assert "set_country_flag = USA_ai_core_state_initialized" in initialize
    for axis, value in AXES.items():
        assert f"set_variable = {{ {axis} = {value} }}" in initialize
        assert f"clamp_variable = {{ var = {axis} min = 0 max = 10 }}" in clamp

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "USA_ai_core")
    assert chain["name"] == "AI Industry Core"
    assert chain["tag"] == "USA"
    assert chain["namespace"] == "USA_ai_core_events"
    assert chain["tier"] == 1
    assert chain["owned_prefixes"] == ["USA_ai_core"]
    assert chain["allowed_writes"] == []
    assert chain["requires_current_year_scheduler"] is True
    assert chain["allow_yearly_scheduler_duplicates"] is True
    assert chain["variables"] == {axis: {"min": 0, "max": 10} for axis in AXES}
    assert set(chain["outcome_ideas"]) == OUTCOMES


def test_core_writes_only_owned_state_and_never_writes_energy_or_technology():
    corpus = "\n".join(
        path.read_text(encoding="utf-8") for path in (EVENTS_PATH, EFFECTS_PATH)
    )
    variable_writes = re.findall(
        r"(?:set_variable|add_to_variable|subtract_from_variable)\s*=\s*\{\s*"
        r"([A-Za-z0-9_]+)\s*=",
        corpus,
    )
    variable_writes += re.findall(
        r"clamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_]+)", corpus
    )
    assert variable_writes
    assert all(identifier.startswith("USA_ai_core_") for identifier in variable_writes)
    assert ENERGY_READS.isdisjoint(variable_writes)

    flag_writes = re.findall(
        r"(?:set_country_flag|clr_country_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        corpus,
    )
    assert flag_writes
    assert all(identifier.startswith("USA_ai_core_") for identifier in flag_writes)
    assert not re.search(r"\bartificial_intelligence_(?:[1-9]|1[0-4])\b", corpus)


def test_visible_events_have_guarded_effects_tooltips_logs_and_ai_fallbacks():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    for event_number, _year, _date in MILESTONES:
        event = _event_block(events, event_number)
        assert "is_triggered_only = yes" in event
        assert "corporate_history_full_enabled = yes" in event
        assert "original_tag = USA" in event
        assert "NOT = { has_country_flag = collapsed_nation }" in event
        assert f"USA_ai_core_event_{event_number}_resolved" in event
        options = _option_blocks(event)
        assert len(options) == (5 if event_number == 12 else 3)
        for option in options:
            assert "log = " in option
            assert "custom_effect_tooltip = USA_ai_core_events." in option
            assert "hidden_effect = {" in option
            assert "ai_chance = {" in option
            base = re.search(r"\bbase\s*=\s*(\d+(?:\.\d+)?)", option)
            assert base and float(base.group(1)) > 0
            if event_number < 12:
                assert "USA_ai_core_clamp_state = yes" in option or (
                    f"USA_ai_core_apply_event_{event_number}_historical = yes" in option
                )


def test_infrastructure_cost_routes_zero_during_economic_distress():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    burden_increasing_options = {
        2: (0, 1),
        5: (1, 2),
        10: (0, 1),
        11: (0, 2),
    }
    fallback_options = {2: 2, 5: 0, 10: 2, 11: 1}
    for event_number, option_indexes in burden_increasing_options.items():
        options = _option_blocks(_event_block(events, event_number))
        for option_index in option_indexes:
            option = options[option_index]
            assert (
                "factor = 0 has_active_mission = bankruptcy_incoming_collapse" in option
            )
            assert "factor = 0 ai_has_major_economic_problems = yes" in option
            assert "factor = 0 check_variable = { treasury < 0 }" in option
        fallback = options[fallback_options[event_number]]
        assert "factor = 0 ai_has_major_economic_problems = yes" not in fallback
        assert "factor = 0 check_variable = { treasury < 0 }" not in fallback


def test_reconstruction_is_silent_ordered_clamped_and_idempotent():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    reconstruct = _named_block(effects, "USA_ai_core_reconstruct_history")
    assert "country_event =" not in reconstruct
    assert "news_event =" not in reconstruct
    assert "USA_ai_core_initialize_state = yes" in reconstruct
    assert "USA_ai_core_clamp_state = yes" in reconstruct
    assert "set_country_flag = USA_ai_core_reconstruct_complete" in reconstruct

    positions = []
    for event_number, _year, date in MILESTONES:
        positions.append(reconstruct.index(f"date > {date}"))
        assert f"USA_ai_core_event_{event_number}_resolved" in reconstruct
        if event_number < 12:
            apply = _named_block(
                effects, f"USA_ai_core_apply_event_{event_number}_historical"
            )
            assert (
                f"set_country_flag = USA_ai_core_event_{event_number}_resolved" in apply
            )
            assert "USA_ai_core_clamp_state = yes" in apply
    assert positions == sorted(positions)


def test_schedulers_have_one_guarded_visible_event_anchor_and_live_callers():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    aggregate = _named_block(effects, "USA_ai_core_schedule_current_year_events")
    assert "corporate_history_full_enabled = yes" in aggregate
    assert "original_tag = USA" in aggregate
    assert "NOT = { has_country_flag = collapsed_nation }" in aggregate
    assert "NOT = { has_country_flag = USA_ai_core_capstone_resolved }" in aggregate
    for event_number, _year, _date in MILESTONES:
        helper_name = f"USA_ai_core_schedule_event_{event_number}"
        assert f"{helper_name} = yes" in aggregate
        helper = _named_block(effects, helper_name)
        assert (
            helper.count(f"country_event = {{ id = USA_ai_core_events.{event_number}")
            >= 2
        )
        assert f"USA_ai_core_event_{event_number}_pending" in helper
        assert f"USA_ai_core_event_{event_number}_delivery_expected" in helper
        if event_number < 12:
            assert f"USA_ai_core_event_{event_number}_resolved" in helper
        else:
            assert "USA_ai_core_capstone_resolved" in helper

    callers = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (COMMON_EFFECTS_PATH, DISPATCH_PATH, MONTHLY_DISPATCH_PATH)
    )
    assert "USA_ai_core_reconstruct_history = yes" in callers
    assert "USA_ai_core_schedule_current_year_events = yes" in callers
    assert "USA_ai_core_schedule_event_1 = yes" not in callers


def test_capstone_applies_exactly_one_terminal_idea_without_axis_mutations():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    resolver = _named_block(effects, "USA_ai_core_resolve_capstone")
    assert "NOT = { has_country_flag = USA_ai_core_capstone_resolved }" in resolver
    assert "add_to_variable" not in resolver
    assert "set_variable" not in resolver
    for outcome in OUTCOMES:
        suffix = outcome.removeprefix("USA_ai_core_")
        apply = _named_block(effects, f"USA_ai_core_apply_{suffix}")
        assert f"add_ideas = {outcome}" in apply
        assert "USA_ai_core_clear_capstone_outcome = yes" in apply
        assert "set_country_flag = USA_ai_core_capstone_resolved" in apply

    clear = _named_block(effects, "USA_ai_core_clear_capstone_outcome")
    assert all(outcome in clear for outcome in OUTCOMES)
    for receiver in ("openai", "anthropic"):
        block = _named_block(effects, f"USA_ai_core_sync_{receiver}_state")
        assert "NOT = { has_country_flag = USA_ai_core_capstone_resolved }" in block
        assert (
            f"NOT = {{ has_country_flag = USA_ai_core_{receiver}_state_received }}"
            in block
        )


def test_localisation_is_bom_lf_and_covers_every_core_reference():
    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    localisation = raw.decode("utf-8-sig")
    keys = set(re.findall(r"(?m)^\s*([A-Za-z0-9_.-]+):(?:\d+)?\s+", localisation))
    events = EVENTS_PATH.read_text(encoding="utf-8")
    references = set(
        re.findall(
            r"(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(USA_ai_core(?:_events)?[A-Za-z0-9_.-]*)",
            events,
        )
    )
    references.update(AXES)
    for outcome in OUTCOMES:
        references.add(outcome)
        references.add(f"{outcome}_desc")
    assert references <= keys, sorted(references - keys)


def test_static_scenarios_cover_full_late_outcomes_and_off():
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    names = {
        item["name"]
        for item in scenarios["scenarios"]
        if item.get("chain") == "USA_ai_core"
    }
    assert names == {
        "ai_core_full_2000_complete_chronology",
        "ai_core_full_post_2026_reconstructs_once",
        "ai_core_outcomes_only_post_2026_silent",
        "ai_core_disabled_post_2026_inert",
    }
    scripts = ScriptIndex.load(ROOT)
    results, passed = run_scenarios(manifest, scenarios, sorted(names), scripts)
    assert passed, results
