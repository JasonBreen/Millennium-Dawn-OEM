import json
import re
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "USA_anthropic_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_anthropic_effects.txt"
CORE_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_ai_core_effects.txt"
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
    "USA_anthropic_governance_strength": 8,
    "USA_anthropic_frontier_capability": 2,
    "USA_anthropic_commercial_reach": 0,
    "USA_anthropic_safety_discipline": 8,
    "USA_anthropic_cloud_independence": 4,
}

MILESTONES = (
    (1, 2021, "2021.5.28"),
    (2, 2022, "2022.4.29"),
    (3, 2023, "2023.2.3"),
    (4, 2023, "2023.3.14"),
    (5, 2023, "2023.5.9"),
    (6, 2023, "2023.9.19"),
    (7, 2023, "2023.9.25"),
    (8, 2024, "2024.3.4"),
    (9, 2024, "2024.11.22"),
    (10, 2025, "2025.5.22"),
)

OUTCOMES = {
    "USA_anthropic_safety_governed_frontier",
    "USA_anthropic_cloud_aligned_scale",
    "USA_anthropic_multi_cloud_independence",
    "USA_anthropic_cautious_research_laboratory",
}

CANONICAL_OPTIONS = {
    1: "a",
    2: "a",
    3: "c",
    4: "a",
    5: "a",
    6: "a",
    7: "c",
    8: "b",
    9: "c",
    10: "a",
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
    event_id = f"USA_anthropic_events.{event_number}"
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


def test_state_contract_initialization_clamps_and_ownership_match():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "USA_anthropic_initialize_state")
    clamp = _named_block(effects, "USA_anthropic_clamp_state")
    for axis, value in AXES.items():
        assert f"set_variable = {{ {axis} = {value} }}" in initialize
        assert f"clamp_variable = {{ var = {axis} min = 0 max = 10 }}" in clamp
    assert "set_country_flag = USA_anthropic_state_initialized" in initialize

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "USA_anthropic")
    assert chain["name"] == "Anthropic"
    assert chain["namespace"] == "USA_anthropic_events"
    assert chain["tier"] == 1
    assert chain["owned_prefixes"] == ["USA_anthropic"]
    assert chain["allowed_writes"] == ["USA_ai_core_sync_anthropic_state"]
    assert chain["variables"] == {axis: {"min": 0, "max": 10} for axis in AXES}
    assert set(chain["outcome_ideas"]) == OUTCOMES


def test_satellite_writes_only_owned_state_and_never_replays_cloud_owner_state():
    corpus = "\n".join(
        path.read_text(encoding="utf-8") for path in (EVENTS_PATH, EFFECTS_PATH)
    )
    writes = re.findall(
        r"(?:set_variable|add_to_variable|subtract_from_variable)\s*=\s*\{\s*"
        r"([A-Za-z0-9_]+)\s*=",
        corpus,
    )
    writes += re.findall(r"clamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_]+)", corpus)
    assert writes
    assert all(identifier.startswith("USA_anthropic_") for identifier in writes)
    flags = re.findall(
        r"(?:set_country_flag|clr_country_flag)\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?([A-Za-z0-9_]+)",
        corpus,
    )
    assert flags
    assert all(identifier.startswith("USA_anthropic_") for identifier in flags)
    assert not re.search(r"set_country_flag\s*=\s*USA_google_", corpus)
    assert not re.search(r"\bartificial_intelligence_(?:[1-9]|1[0-4])\b", corpus)


def test_visible_events_have_guards_previews_and_reachable_historical_ai_routes():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    for event_number, _year, _date in MILESTONES:
        event = _event_block(events, event_number)
        assert "is_triggered_only = yes" in event
        assert "corporate_history_full_enabled = yes" in event
        assert "original_tag = USA" in event
        assert "NOT = { has_country_flag = collapsed_nation }" in event
        assert f"USA_anthropic_event_{event_number}_resolved" in event
        options = _option_blocks(event)
        assert len(options) == 4
        for option in options:
            assert "log = " in option
            assert "custom_effect_tooltip = USA_anthropic_events." in option
            assert "hidden_effect = {" in option
            assert "ai_chance = {" in option
            base = re.search(r"\bbase\s*=\s*(\d+(?:\.\d+)?)", option)
            assert base and float(base.group(1)) > 0
        suffix = CANONICAL_OPTIONS[event_number]
        canonical = next(
            option
            for option in options
            if f"name = USA_anthropic_events.{event_number}.{suffix}" in option
        )
        assert re.search(r"(?m)^\s*base\s*=\s*(?:8[0-9]|9[0-9]|100)\b", canonical)
        assert "is_historical_focus_on = yes" in canonical


def test_reconstruction_and_scheduler_are_silent_ordered_guarded_and_reachable():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    reconstruct = _named_block(effects, "USA_anthropic_reconstruct_history")
    assert "country_event =" not in reconstruct
    assert "news_event =" not in reconstruct
    positions = []
    for event_number, _year, date in MILESTONES:
        positions.append(reconstruct.index(f"date > {date}"))
        assert f"USA_anthropic_event_{event_number}_resolved" in reconstruct
        if event_number < 10:
            apply = _named_block(
                effects, f"USA_anthropic_apply_event_{event_number}_historical"
            )
            assert (
                f"set_country_flag = USA_anthropic_event_{event_number}_resolved"
                in apply
            )
            assert re.search(
                r"USA_anthropic_apply_(?:safety|enterprise|cloud|multicloud)_route = yes",
                apply,
            )
    assert positions == sorted(positions)

    scheduler = _named_block(effects, "USA_anthropic_schedule_current_year_events")
    assert "corporate_history_full_enabled = yes" in scheduler
    assert "original_tag = USA" in scheduler
    assert "NOT = { has_country_flag = collapsed_nation }" in scheduler
    assert "has_country_flag = USA_anthropic_reconstruct_complete" in scheduler
    for event_number, _year, _date in MILESTONES:
        helper_name = f"USA_anthropic_schedule_event_{event_number}"
        assert f"{helper_name} = yes" in scheduler
        helper = _named_block(effects, helper_name)
        assert (
            helper.count(f"country_event = {{ id = USA_anthropic_events.{event_number}")
            >= 2
        )
        assert f"USA_anthropic_event_{event_number}_pending" in helper
        assert f"USA_anthropic_event_{event_number}_delivery_expected" in helper

    callers = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (COMMON_EFFECTS_PATH, DISPATCH_PATH, MONTHLY_DISPATCH_PATH)
    )
    assert "USA_anthropic_reconstruct_history = yes" in callers
    assert "USA_anthropic_schedule_current_year_events = yes" in callers


def test_terminal_callback_and_core_receiver_are_exact_and_idempotent():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    for outcome in OUTCOMES:
        suffix = outcome.removeprefix("USA_anthropic_")
        apply = _named_block(effects, f"USA_anthropic_apply_{suffix}")
        assert f"add_ideas = {outcome}" in apply
        assert "set_country_flag = USA_anthropic_capstone_resolved" in apply
        assert apply.index(
            "set_country_flag = USA_anthropic_capstone_resolved"
        ) < apply.index("USA_anthropic_terminal_callback = yes")
    callback = _named_block(effects, "USA_anthropic_terminal_callback")
    assert (
        "NOT = { has_country_flag = USA_anthropic_terminal_callback_sent }" in callback
    )
    assert callback.count("USA_ai_core_sync_anthropic_state = yes") == 1

    core = CORE_EFFECTS_PATH.read_text(encoding="utf-8")
    receiver = _named_block(core, "USA_ai_core_sync_anthropic_state")
    assert "NOT = { has_country_flag = USA_ai_core_capstone_resolved }" in receiver
    assert (
        "NOT = { has_country_flag = USA_ai_core_anthropic_state_received }" in receiver
    )
    assert "set_country_flag = USA_ai_core_anthropic_state_received" in receiver
    assert "USA_ai_core_clamp_state = yes" in receiver
    fragments = {
        "USA_anthropic_safety_governed_frontier": (
            "add_to_variable = { USA_ai_core_state_alignment = 1 }",
            "add_to_variable = { USA_ai_core_public_legitimacy = 2 }",
            "add_to_variable = { USA_ai_core_frontier_capability = 1 }",
        ),
        "USA_anthropic_cloud_aligned_scale": (
            "add_to_variable = { USA_ai_core_frontier_capability = 1 }",
            "add_to_variable = { USA_ai_core_compute_depth = 2 }",
            "add_to_variable = { USA_ai_core_infrastructure_burden = 1 }",
        ),
        "USA_anthropic_multi_cloud_independence": (
            "add_to_variable = { USA_ai_core_compute_depth = 1 }",
            "add_to_variable = { USA_ai_core_ecosystem_openness = 2 }",
            "add_to_variable = { USA_ai_core_public_legitimacy = 1 }",
        ),
        "USA_anthropic_cautious_research_laboratory": (
            "add_to_variable = { USA_ai_core_ecosystem_openness = 1 }",
            "add_to_variable = { USA_ai_core_public_legitimacy = 2 }",
            "add_to_variable = { USA_ai_core_frontier_capability = -1 }",
        ),
    }
    for idea, values in fragments.items():
        assert f"has_idea = {idea}" in receiver
        assert all(value in receiver for value in values)


def test_localisation_is_bom_lf_and_covers_all_anthropic_references():
    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    localisation = raw.decode("utf-8-sig")
    keys = set(re.findall(r"(?m)^\s*([A-Za-z0-9_.-]+):(?:\d+)?\s+", localisation))
    events = EVENTS_PATH.read_text(encoding="utf-8")
    references = set(
        re.findall(
            r"(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(USA_anthropic(?:_events)?[A-Za-z0-9_.-]*)",
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
        if item.get("chain") == "USA_anthropic"
    }
    assert names == {
        "anthropic_full_2021_complete_chronology",
        "anthropic_full_2023_mid_chain",
        "anthropic_full_2025_before_capstone",
        "anthropic_full_post_2025_reconstructs_once",
        "anthropic_outcomes_only_post_2025_silent",
        "anthropic_disabled_post_2025_inert",
    }
    scripts = ScriptIndex.load(ROOT)
    results, passed = run_scenarios(manifest, scenarios, sorted(names), scripts)
    assert passed, results
