import json
import re
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "USA_openai_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_openai_effects.txt"
CORE_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_ai_core_effects.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "USA_openai_ideas.txt"
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
    "USA_openai_mission_control": 8,
    "USA_openai_frontier_capability": 2,
    "USA_openai_deployment_reach": 0,
    "USA_openai_safety_governance": 6,
    "USA_openai_compute_independence": 3,
}

MILESTONES = (
    (1, 2015, "2015.12.11"),
    (2, 2019, "2019.3.11"),
    (3, 2020, "2020.6.11"),
    (4, 2022, "2022.11.30"),
    (5, 2023, "2023.3.14"),
    (6, 2023, "2023.11.17"),
    (7, 2024, "2024.3.8"),
    (8, 2025, "2025.1.21"),
    (9, 2025, "2025.10.28"),
)

OUTCOMES = {
    "USA_openai_nonprofit_controlled_pbc",
    "USA_openai_scaled_commercial_platform",
    "USA_openai_diversified_frontier_consortium",
    "USA_openai_safety_governed_laboratory",
}

CANONICAL_OPTIONS = {
    1: "a",
    2: "b",
    3: "c",
    4: "b",
    5: "b",
    6: "c",
    7: "c",
    8: "d_option",
    9: "a",
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
    event_id = f"USA_openai_events.{event_number}"
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
    initialize = _named_block(effects, "USA_openai_initialize_state")
    clamp = _named_block(effects, "USA_openai_clamp_state")

    assert "NOT = { has_country_flag = USA_openai_state_initialized }" in initialize
    assert "set_country_flag = USA_openai_state_initialized" in initialize
    for axis, value in AXES.items():
        assert f"set_variable = {{ {axis} = {value} }}" in initialize
        assert f"clamp_variable = {{ var = {axis} min = 0 max = 10 }}" in clamp

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "USA_openai")
    assert chain["name"] == "OpenAI"
    assert chain["tag"] == "USA"
    assert chain["namespace"] == "USA_openai_events"
    assert chain["tier"] == 1
    assert chain["owned_prefixes"] == ["USA_openai"]
    assert chain["allowed_writes"] == ["USA_ai_core_sync_openai_state"]
    assert chain["requires_current_year_scheduler"] is True
    assert chain["allow_yearly_scheduler_duplicates"] is True
    assert chain["variables"] == {axis: {"min": 0, "max": 10} for axis in AXES}
    assert set(chain["outcome_ideas"]) == OUTCOMES


def test_openai_writes_only_owned_state_and_does_not_replay_partner_choices():
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
    assert all(identifier.startswith("USA_openai_") for identifier in variable_writes)

    flag_writes = re.findall(
        r"(?:set_country_flag|clr_country_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        corpus,
    )
    assert flag_writes
    assert all(identifier.startswith("USA_openai_") for identifier in flag_writes)
    assert not re.search(r"set_country_flag\s*=\s*USA_(?:microsoft|oracle)_", corpus)
    assert not re.search(r"\bartificial_intelligence_(?:[1-9]|1[0-4])\b", corpus)


def test_visible_events_have_guards_logs_previews_and_reachable_ai_options():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    for event_number, _year, _date in MILESTONES:
        event = _event_block(events, event_number)
        assert "is_triggered_only = yes" in event
        assert "corporate_history_full_enabled = yes" in event
        assert "original_tag = USA" in event
        assert "NOT = { has_country_flag = collapsed_nation }" in event
        assert f"USA_openai_event_{event_number}_resolved" in event
        options = _option_blocks(event)
        assert len(options) == 4
        for option in options:
            assert "log = " in option
            assert "custom_effect_tooltip = USA_openai_events." in option
            assert "hidden_effect = {" in option
            assert "ai_chance = {" in option
            base = re.search(r"\bbase\s*=\s*(\d+(?:\.\d+)?)", option)
            assert base and float(base.group(1)) > 0


def test_reconstruction_is_silent_ordered_clamped_and_historical():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    reconstruct = _named_block(effects, "USA_openai_reconstruct_history")
    assert "country_event =" not in reconstruct
    assert "news_event =" not in reconstruct
    assert "USA_openai_initialize_state = yes" in reconstruct
    for route in ("mission", "commercial", "safety", "compute"):
        route_effect = _named_block(effects, f"USA_openai_apply_{route}_route")
        assert "USA_openai_clamp_state = yes" in route_effect

    positions = []
    for event_number, _year, date in MILESTONES:
        positions.append(reconstruct.index(f"date > {date}"))
        assert f"USA_openai_event_{event_number}_resolved" in reconstruct
        if event_number < 9:
            apply = _named_block(
                effects, f"USA_openai_apply_event_{event_number}_historical"
            )
            assert (
                f"set_country_flag = USA_openai_event_{event_number}_resolved" in apply
            )
            assert re.search(
                r"USA_openai_apply_(?:mission|commercial|safety|compute)_route = yes",
                apply,
            )
    assert positions == sorted(positions)

    events = EVENTS_PATH.read_text(encoding="utf-8")
    for event_number, option_suffix in CANONICAL_OPTIONS.items():
        event = _event_block(events, event_number)
        canonical_name = f"USA_openai_events.{event_number}.{option_suffix}"
        canonical = next(
            option
            for option in _option_blocks(event)
            if f"name = {canonical_name}" in option
        )
        assert re.search(r"(?m)^\s*base\s*=\s*(?:8[0-9]|9[0-9]|100)\b", canonical)


def test_schedulers_are_guarded_and_have_live_aggregate_callers():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    aggregate = _named_block(effects, "USA_openai_schedule_current_year_events")
    assert "corporate_history_full_enabled = yes" in aggregate
    assert "original_tag = USA" in aggregate
    assert "NOT = { has_country_flag = collapsed_nation }" in aggregate
    assert "NOT = { has_country_flag = USA_openai_capstone_resolved }" in aggregate
    for event_number, _year, _date in MILESTONES:
        helper_name = f"USA_openai_schedule_event_{event_number}"
        assert f"{helper_name} = yes" in aggregate
        helper = _named_block(effects, helper_name)
        assert (
            helper.count(f"country_event = {{ id = USA_openai_events.{event_number}")
            >= 2
        )
        assert f"USA_openai_event_{event_number}_pending" in helper
        assert f"USA_openai_event_{event_number}_delivery_expected" in helper

    callers = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (COMMON_EFFECTS_PATH, DISPATCH_PATH, MONTHLY_DISPATCH_PATH)
    )
    assert "USA_openai_reconstruct_history = yes" in callers
    assert "USA_openai_schedule_current_year_events = yes" in callers
    assert "USA_openai_schedule_event_1 = yes" not in callers


def test_terminal_resolution_calls_core_once_after_setting_an_exactly_one_idea():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    resolver = _named_block(effects, "USA_openai_resolve_capstone")
    assert "NOT = { has_country_flag = USA_openai_capstone_resolved }" in resolver
    clear = _named_block(effects, "USA_openai_clear_capstone_outcome")
    for outcome in OUTCOMES:
        assert outcome in clear
        suffix = outcome.removeprefix("USA_openai_")
        apply = _named_block(effects, f"USA_openai_apply_{suffix}")
        assert f"add_ideas = {outcome}" in apply
        assert "USA_openai_clear_capstone_outcome = yes" in apply
        assert "set_country_flag = USA_openai_capstone_resolved" in apply
        assert apply.index(
            "set_country_flag = USA_openai_capstone_resolved"
        ) < apply.index("USA_openai_terminal_callback = yes")
        assert apply.count("USA_openai_terminal_callback = yes") == 1

    callback = _named_block(effects, "USA_openai_terminal_callback")
    assert "NOT = { has_country_flag = USA_openai_terminal_callback_sent }" in callback
    assert callback.count("USA_ai_core_sync_openai_state = yes") == 1
    assert callback.index("USA_ai_core_sync_openai_state = yes") < callback.index(
        "set_country_flag = USA_openai_terminal_callback_sent"
    )


def test_core_receiver_mapping_is_exact_idempotent_clamped_and_post_capstone_noop():
    core_effects = CORE_EFFECTS_PATH.read_text(encoding="utf-8")
    receiver = _named_block(core_effects, "USA_ai_core_sync_openai_state")
    assert "NOT = { has_country_flag = USA_ai_core_capstone_resolved }" in receiver
    assert "NOT = { has_country_flag = USA_ai_core_openai_state_received }" in receiver
    assert "set_country_flag = USA_ai_core_openai_state_received" in receiver
    assert "USA_ai_core_clamp_state = yes" in receiver

    expected_fragments = {
        "USA_openai_nonprofit_controlled_pbc": (
            "add_to_variable = { USA_ai_core_frontier_capability = 1 }",
            "add_to_variable = { USA_ai_core_state_alignment = 1 }",
            "add_to_variable = { USA_ai_core_public_legitimacy = 2 }",
        ),
        "USA_openai_scaled_commercial_platform": (
            "add_to_variable = { USA_ai_core_frontier_capability = 2 }",
            "add_to_variable = { USA_ai_core_compute_depth = 1 }",
            "add_to_variable = { USA_ai_core_infrastructure_burden = 2 }",
            "add_to_variable = { USA_ai_core_public_legitimacy = -1 }",
        ),
        "USA_openai_diversified_frontier_consortium": (
            "add_to_variable = { USA_ai_core_compute_depth = 2 }",
            "add_to_variable = { USA_ai_core_ecosystem_openness = 2 }",
            "add_to_variable = { USA_ai_core_infrastructure_burden = 1 }",
        ),
        "USA_openai_safety_governed_laboratory": (
            "add_to_variable = { USA_ai_core_state_alignment = 1 }",
            "add_to_variable = { USA_ai_core_public_legitimacy = 2 }",
            "add_to_variable = { USA_ai_core_frontier_capability = -1 }",
        ),
    }
    for idea, fragments in expected_fragments.items():
        assert f"has_idea = {idea}" in receiver
        assert all(fragment in receiver for fragment in fragments)


def test_localisation_is_bom_lf_and_covers_every_openai_reference():
    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    localisation = raw.decode("utf-8-sig")
    keys = set(re.findall(r"(?m)^\s*([A-Za-z0-9_.-]+):(?:\d+)?\s+", localisation))
    events = EVENTS_PATH.read_text(encoding="utf-8")
    references = set(
        re.findall(
            r"(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(USA_openai(?:_events)?[A-Za-z0-9_.-]*)",
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
        if item.get("chain") == "USA_openai"
    }
    assert names == {
        "openai_full_2015_complete_chronology",
        "openai_full_2023_mid_chain",
        "openai_full_2025_before_capstone",
        "openai_full_post_2025_reconstructs_once",
        "openai_outcomes_only_post_2025_silent",
        "openai_disabled_post_2025_inert",
    }
    scripts = ScriptIndex.load(ROOT)
    results, passed = run_scenarios(manifest, scenarios, sorted(names), scripts)
    assert passed, results
