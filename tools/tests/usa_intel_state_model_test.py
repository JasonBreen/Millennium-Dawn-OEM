import datetime
import json
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "USA_intel_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_intel_effects.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "USA_intel_ideas.txt"
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
DASHBOARD_PATH = ROOT / "common" / "decisions" / "USA_corporate_systems_dashboard.txt"
DASHBOARD_LOC_PATH = (
    ROOT
    / "common"
    / "scripted_localisation"
    / "USA_corporate_systems_dashboard_scripted_localisation.txt"
)
CORPORATE_SYSTEMS_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "USA_corporate_systems_effects.txt"
)
PHYSICAL_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "USA_physical_compute_stack_effects.txt"
)
PHYSICAL_IDEAS_PATH = ROOT / "common" / "ideas" / "USA_physical_compute_stack_ideas.txt"
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
SCENARIOS_PATH = ROOT / "tools" / "corporate_history_scenarios.json"
SOURCE_MAP_PATH = (
    ROOT
    / "docs"
    / "src"
    / "content"
    / "resources"
    / "intel-corporate-history-source-map.md"
)

AXES = (
    "USA_intel_architecture_leadership",
    "USA_intel_process_execution",
    "USA_intel_platform_leverage",
    "USA_intel_manufacturing_resilience",
    "USA_intel_foundry_credibility",
    "USA_intel_portfolio_breadth",
    "USA_intel_capital_discipline",
)
INITIAL = (8, 9, 9, 8, 1, 6, 8)

MILESTONES = (
    (1, 2000, "2000.11.20"),
    (2, 2002, "2002.7.8"),
    (3, 2003, "2003.3.12"),
    (4, 2006, "2006.7.27"),
    (5, 2010, "2010.8.4"),
    (6, 2015, "2015.1.15"),
    (7, 2015, "2015.12.28"),
    (8, 2018, "2018.1.3"),
    (9, 2019, "2019.12.16"),
    (10, 2020, "2020.7.23"),
    (11, 2021, "2021.3.23"),
    (12, 2022, "2022.1.21"),
    (13, 2024, "2024.11.26"),
    (14, 2025, "2025.8.22"),
    (15, 2026, "2026.1.5"),
)

ROUTES = (
    (
        ("USA_intel_netburst_frequency_race", (1, -1, 1, 0, 0, 0, -1)),
        ("USA_intel_netburst_balanced_pipeline", (1, 1, 0, 0, 0, 0, -1)),
        ("USA_intel_netburst_mobile_efficiency", (1, 0, -1, 0, 0, 1, -1)),
    ),
    (
        ("USA_intel_itanium_enterprise_push", (-1, 1, -1, 0, 0, 1, -1)),
        ("USA_intel_itanium_x86_bridge", (1, 0, 1, 0, 0, 1, 0)),
        ("USA_intel_itanium_open_ecosystem", (0, 0, -2, 0, 0, 2, -1)),
    ),
    (
        ("USA_intel_centrino_integrated_platform", (1, 0, 1, 1, 0, 1, -1)),
        ("USA_intel_centrino_open_components", (0, 0, -1, 1, 0, 1, 0)),
        ("USA_intel_centrino_wireless_scale", (0, 0, 1, 0, 0, 2, -1)),
    ),
    (
        ("USA_intel_core_architecture_reset", (2, 1, 0, 1, 0, 0, 1)),
        ("USA_intel_core_process_rescue", (1, 2, 0, 1, 0, 0, -1)),
        ("USA_intel_core_platform_continuity", (1, -1, 2, 0, 0, 0, 1)),
    ),
    (
        ("USA_intel_ftc_compliance_settlement", (0, 0, -1, 0, 0, 1, 1)),
        ("USA_intel_ftc_litigation", (0, 0, 1, -1, 0, 0, -2)),
        ("USA_intel_ftc_open_interfaces", (1, 0, -2, 0, 0, 2, 0)),
    ),
    (
        ("USA_intel_mobile_contra_revenue_exit", (0, 0, -1, 0, 0, -1, 2)),
        ("USA_intel_mobile_subsidy_escalation", (0, -1, 1, 0, 0, 2, -2)),
        ("USA_intel_mobile_modem_focus", (1, 1, 0, 0, 0, 1, -1)),
    ),
    (
        ("USA_intel_altera_integrated", (1, 0, 0, 0, 0, 2, -2)),
        ("USA_intel_altera_independent_federation", (0, 0, -1, 0, 0, 1, -1)),
        ("USA_intel_altera_divestiture", (0, 0, 0, 0, 0, -1, 2)),
    ),
    (
        ("USA_intel_spectre_coordinated_mitigation", (-1, 0, -1, 2, 0, 0, -1)),
        ("USA_intel_spectre_minimal_disclosure", (0, 0, 1, -2, 0, 0, 1)),
        ("USA_intel_spectre_open_security", (1, 0, -2, 1, 0, 0, -1)),
    ),
    (
        ("USA_intel_habana_integrated_ai", (1, 0, 0, 0, 0, 2, -2)),
        ("USA_intel_habana_open_accelerator", (1, 0, -1, 0, 0, 1, -1)),
        ("USA_intel_habana_partnership", (0, 0, 0, 0, 0, 1, 1)),
    ),
    (
        ("USA_intel_process_delay_hybrid_fabs", (0, -2, 0, 1, -1, 0, 1)),
        ("USA_intel_process_delay_double_down", (0, 1, 0, -1, 1, 0, -3)),
        ("USA_intel_process_delay_outsource", (1, -1, 0, -2, -2, 0, 2)),
    ),
    (
        ("USA_intel_idm2_foundry_reset", (0, 1, 0, 1, 3, 0, -2)),
        ("USA_intel_idm2_product_first", (2, 0, 0, 0, -1, 1, 1)),
        ("USA_intel_idm2_open_foundry", (0, 0, -2, 0, 3, 1, -2)),
    ),
    (
        ("USA_intel_ohio_megafab", (0, 1, 0, 2, 2, 0, -2)),
        ("USA_intel_ohio_staged_buildout", (0, 0, 0, 1, 1, 0, 1)),
        ("USA_intel_ohio_cancelled", (0, 0, 0, -1, -2, 0, 2)),
    ),
    (
        ("USA_intel_chips_separated_foundry", (0, 0, -1, 0, 2, 0, 2)),
        ("USA_intel_foundry_reintegrated", (1, 0, 1, 0, 1, 0, -1)),
        ("USA_intel_chips_contract_minimal", (0, 0, 0, -1, -1, 0, 1)),
    ),
    (
        ("USA_intel_us_equity_national_anchor", (0, 0, 0, 1, 1, 0, 2)),
        ("USA_intel_us_equity_guardrails", (0, 0, -1, 0, 1, 0, 1)),
        ("USA_intel_us_equity_rejected", (0, 0, 1, 0, -1, 0, -1)),
    ),
    (
        ("USA_intel_18a_domestic_ramp", (1, 2, 0, 1, 1, 0, 1)),
        ("USA_intel_18a_open_foundry_launch", (0, 1, -2, 0, 2, 1, 0)),
        ("USA_intel_18a_outsourced_portfolio", (1, 1, 0, 0, -2, 1, 2)),
    ),
)

OUTCOMES = {
    "domestic_silicon_arsenal": "USA_intel_domestic_silicon_arsenal",
    "open_systems_foundry": "USA_intel_open_systems_foundry",
    "integrated_compute_foundry": "USA_intel_integrated_compute_foundry",
    "x86_platform_fortress": "USA_intel_x86_platform_fortress",
    "fabless_architecture_house": "USA_intel_fabless_architecture_house",
    "managed_retrenchment": "USA_intel_managed_retrenchment",
}

OUTCOME_ROUTES = {
    "domestic_silicon_arsenal": "AAAAAAAAAAAAAAA",
    "open_systems_foundry": "AAAAAAAAAAAAAAB",
    "integrated_compute_foundry": "AAAAAAAAAAAAAAC",
    "managed_retrenchment": "AAAAAAAAAAAAACC",
    "x86_platform_fortress": "AAAAAAAAAAAABAC",
    "fabless_architecture_house": "AAAAAAAAACBCCBB",
}

ALLOWED_READS = {
    "CAN_ati_rocm_open_ecosystem",
    "TAI_tsmc_advanced_packaging_expanded",
    "TAI_via_cross_license_settlement",
    "USA_apple_intel_transition",
    "USA_apple_silicon_transition",
    "USA_ibm_x86_divested",
    "USA_micron_imflash_deep",
    "USA_nvidia_cuda_committed",
}

DEPENDENCY_ORDER = [
    "CAN_ati",
    "TAI_pc_industry",
    "TAI_tsmc",
    "USA_apple",
    "USA_ibm",
    "USA_micron",
    "USA_nvidia",
]

PICTURES = ("GFX_computer",) * 15

SHARED_LOCALISATION_KEYS = {
    "USA_corporate_systems_processor_foundry",
    "USA_corporate_systems_processor_foundry_desc",
    "USA_processor_architecture_anchor",
    "USA_processor_architecture_anchor_desc",
    "USA_full_spectrum_compute_stack",
    "USA_full_spectrum_compute_stack_desc",
    "USA_intel_dashboard_era_start",
    "USA_intel_dashboard_era_netburst_itanium",
    "USA_intel_dashboard_era_core_platform",
    "USA_intel_dashboard_era_diversification_strain",
    "USA_intel_dashboard_era_process_crisis",
    "USA_intel_dashboard_era_foundry_reset",
    "USA_intel_dashboard_era_18a_resolution",
    "USA_intel_dashboard_capstone_unresolved",
    "USA_intel_dashboard_processor_pillar_established",
    "USA_intel_dashboard_processor_pillar_gap",
    "USA_intel_dashboard_not_initialized",
    "USA_intel_dashboard_full_spectrum_operational",
    "USA_intel_dashboard_full_spectrum_physical_only",
    "USA_intel_dashboard_full_spectrum_processor_only",
    "USA_intel_dashboard_full_spectrum_developing",
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
    event_id = f"USA_intel_events.{event_number}"
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


def _axis_writes(text: str) -> List[Tuple[str, int]]:
    return [
        (axis, int(value))
        for axis, value in re.findall(
            r"add_to_variable\s*=\s*\{\s*"
            r"(USA_intel_[A-Za-z0-9_]+)\s*=\s*(-?\d+)\s*\}",
            text,
        )
        if axis in AXES
    ]


def _apply_route(route: str) -> Tuple[Tuple[int, ...], Set[str]]:
    state = list(INITIAL)
    flags = set()
    for event_index, letter in enumerate(route):
        option_index = ord(letter) - ord("A")
        flag, delta = ROUTES[event_index][option_index]
        flags.add(flag)
        state = [max(0, min(10, value + change)) for value, change in zip(state, delta)]
    return tuple(state), flags


def _resolve(state: Tuple[int, ...], flags: Set[str]) -> str:
    architecture, process, platform, manufacturing, foundry, breadth, capital = state
    if (
        "USA_intel_us_equity_national_anchor" in flags
        and "USA_intel_18a_domestic_ramp" in flags
        and process >= 8
        and manufacturing >= 8
        and foundry >= 8
        and capital >= 6
    ):
        return "domestic_silicon_arsenal"
    if (
        "USA_intel_18a_open_foundry_launch" in flags
        and foundry >= 7
        and platform <= 6
        and breadth >= 8
    ):
        return "open_systems_foundry"
    if architecture >= 8 and foundry >= 6 and breadth >= 8:
        return "integrated_compute_foundry"
    if architecture >= 8 and platform >= 8 and foundry < 6:
        return "x86_platform_fortress"
    if architecture >= 7 and foundry <= 3 and manufacturing <= 6:
        return "fabless_architecture_house"
    return "managed_retrenchment"


def _idea_block(text: str, idea: str) -> str:
    match = re.search(rf"(?m)^\t\t{re.escape(idea)}\s*=\s*\{{", text)
    assert match, f"Missing idea {idea}"
    return _extract_block(text, match.start())


def _assignment_blocks(text: str, key: str) -> List[str]:
    return [
        _extract_block(text, match.start())
        for match in re.finditer(rf"\b{re.escape(key)}\s*=\s*\{{", text)
    ]


def _engine_effect_payload(block: str) -> str:
    body = block[block.index("{") + 1 : block.rfind("}")]
    state_call = re.compile(
        r"USA_intel_(?:record_[A-Za-z0-9_]+|resolve_history)\s*=\s*yes"
    )
    return "\n".join(
        line.strip()
        for line in body.splitlines()
        if line.strip() and not state_call.fullmatch(line.strip())
    )


def _has_negative_treasury_change(option: str) -> bool:
    return any(
        float(value) < 0
        for value in re.findall(r"\btreasury_change\s*=\s*(-?\d+(?:\.\d+)?)", option)
    )


def _has_bankruptcy_zero_modifier(option: str) -> bool:
    ai_chance = _assignment_blocks(option, "ai_chance")
    assert len(ai_chance) == 1
    modifiers = _assignment_blocks(ai_chance[0], "modifier")
    for index, modifier in enumerate(modifiers):
        factor_zero = re.search(r"\bfactor\s*=\s*0(?:\.0+)?(?=\s|\})", modifier)
        bankruptcy = re.search(
            r"\bhas_active_mission\s*=\s*bankruptcy_incoming_collapse\b", modifier
        )
        negated = re.search(
            r"NOT\s*=\s*\{[^{}]*\bhas_active_mission\s*=\s*"
            r"bankruptcy_incoming_collapse\b[^{}]*\}",
            modifier,
            re.DOTALL,
        )
        later_add = any(
            re.search(r"\badd\s*=", item) for item in modifiers[index + 1 :]
        )
        if factor_zero and bankruptcy and not negated and not later_add:
            return True
    return False


def _has_unconditional_historical_zero_modifier(option: str) -> bool:
    ai_chance = _assignment_blocks(option, "ai_chance")
    assert len(ai_chance) == 1
    for modifier in _assignment_blocks(ai_chance[0], "modifier"):
        bankruptcy_exception = re.search(
            r"NOT\s*=\s*\{[^{}]*\bhas_active_mission\s*=\s*"
            r"bankruptcy_incoming_collapse\b[^{}]*\}",
            modifier,
            re.DOTALL,
        )
        if (
            re.search(r"\bfactor\s*=\s*0(?:\.0+)?(?=\s|\})", modifier)
            and "is_historical_focus_on = yes" in modifier
            and not bankruptcy_exception
        ):
            return True
    return False


def _has_positive_bankruptcy_weight(option: str) -> bool:
    ai_chance = _assignment_blocks(option, "ai_chance")
    assert len(ai_chance) == 1
    base = re.search(r"\bbase\s*=\s*(-?\d+(?:\.\d+)?)", ai_chance[0])
    if base and float(base.group(1)) > 0:
        return True
    for modifier in _assignment_blocks(ai_chance[0], "modifier"):
        add = re.search(r"\badd\s*=\s*(\d+(?:\.\d+)?)", modifier)
        if (
            add
            and float(add.group(1)) > 0
            and "has_active_mission = bankruptcy_incoming_collapse" in modifier
        ):
            return True
    return False


def test_initial_state_clamp_and_manifest_contract_match():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "USA_intel_initialize_state")
    clamp = _named_block(effects, "USA_intel_clamp_state")

    for axis, value in zip(AXES, INITIAL):
        assert f"set_variable = {{ {axis} = {value} }}" in initialize
        assert f"set_temp_variable = {{ corp_value = {axis} }}" in clamp
        assert f"set_variable = {{ {axis} = corp_value }}" in clamp
    assert "set_variable = { USA_intel_corporate_era = 0 }" in initialize
    assert clamp.count("corporate_history_clamp_value = yes") == len(AXES)
    assert "clamp_variable = { var = USA_intel_corporate_era min = 0 max = 6 }" in clamp
    for era in range(1, 7):
        advance = _named_block(effects, f"USA_intel_advance_era_{era}")
        assert f"set_variable = {{ USA_intel_corporate_era = {era} }}" in advance
        assert advance.count("USA_intel_clamp_state = yes") == 1

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "USA_intel")
    assert chain["name"] == "Intel"
    assert chain["tag"] == "USA"
    assert chain["namespace"] == "USA_intel_events"
    assert chain["tier"] == 1
    assert set(chain["variables"]) == set(AXES) | {"USA_intel_corporate_era"}
    for axis in AXES:
        assert chain["variables"][axis] == {"min": 0, "max": 10}
    assert chain["variables"]["USA_intel_corporate_era"] == {"min": 0, "max": 6}
    assert chain["owned_prefixes"] == ["USA_intel"]
    assert set(chain["allowed_reads"]) == ALLOWED_READS
    assert chain["allowed_writes"] == []
    assert chain["dependency_order"] == DEPENDENCY_ORDER
    assert chain["terminal_marker"] == "USA_intel_history_complete"
    assert chain["terminal_date"] == "2026-01-05"
    assert chain["requires_current_year_scheduler"] is True
    assert chain["allow_multiple_completion_producers"] is True
    assert chain["bridge_refresh_policy"] == "immediate"
    assert set(chain["outcome_ideas"]) == set(OUTCOMES.values())


def test_all_authored_routes_are_distinct_clamped_and_reachable():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    for event_number, routes in enumerate(ROUTES, start=1):
        clear = _named_block(effects, f"USA_intel_clear_event_{event_number:02d}_route")
        for flag, delta in routes:
            assert f"clr_country_flag = {flag}" in clear
            record = _named_block(
                effects, f"USA_intel_record_{flag.removeprefix('USA_intel_')}"
            )
            assert f"set_country_flag = {flag}" in record
            assert f"USA_intel_mark_event_{event_number:02d}_resolved = yes" in record
            assert sorted(_axis_writes(record)) == sorted(
                (axis, change) for axis, change in zip(AXES, delta) if change
            )
            assert record.count("USA_intel_clamp_state = yes") == 1

    for expected, route in OUTCOME_ROUTES.items():
        state, flags = _apply_route(route)
        assert _resolve(state, flags) == expected

    historical_state, historical_flags = _apply_route("A" * 15)
    assert historical_state == (10, 10, 6, 10, 9, 10, 6)
    assert _resolve(historical_state, historical_flags) == "domestic_silicon_arsenal"


def test_capstone_priority_ideas_and_completion_paths_are_authoritative():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    resolver = _named_block(effects, "USA_intel_update_capstone")
    clear = _named_block(effects, "USA_intel_clear_capstone_outcomes")
    ordered_calls = tuple(f"USA_intel_apply_{suffix}" for suffix in OUTCOMES)
    positions = [resolver.index(call) for call in ordered_calls]
    assert positions == sorted(positions)
    assert resolver.count("USA_intel_clear_capstone_outcomes = yes") == 1
    assert resolver.count("USA_physical_compute_stack_resolve = yes") == 1
    assert resolver.count("USA_corporate_systems_update_economic_bridge = yes") == 0

    for suffix, idea in OUTCOMES.items():
        assert idea in clear
        applicator = _named_block(effects, f"USA_intel_apply_{suffix}")
        assert f"add_ideas = {idea}" in applicator
        idea_definition = _idea_block(ideas, idea)
        assert "picture = generic_intel_bonus" in idea_definition
        assert "allowed = " not in idea_definition
        assert len(re.findall(r"(?m)^\t\t\t\t[A-Za-z0-9_]+\s*=", idea_definition)) <= 5

    resolve = _named_block(effects, "USA_intel_resolve_history")
    reconstruct = _named_block(effects, "USA_intel_reconstruct_history")
    assert resolve.count("set_country_flag = USA_intel_history_complete") == 1
    assert reconstruct.count("set_country_flag = USA_intel_history_complete") == 1
    assert "date > 2026.1.5" in reconstruct
    assert "USA_intel_update_capstone = yes" in reconstruct
    assert "USA_intel_resolve_history = yes" not in reconstruct


def test_policy_adapters_are_owner_local_bounded_inputs():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    expected = {
        "USA_intel_apply_open_systems_procurement": {
            "USA_intel_foundry_credibility": 1,
            "USA_intel_platform_leverage": -1,
        },
        "USA_intel_apply_domestic_capacity_grants": {
            "USA_intel_manufacturing_resilience": 1,
            "USA_intel_foundry_credibility": 1,
        },
        "USA_intel_apply_secure_federal_systems": {
            "USA_intel_platform_leverage": 1,
            "USA_intel_capital_discipline": 1,
        },
        "USA_intel_apply_advanced_computing_consortium": {
            "USA_intel_architecture_leadership": 1,
            "USA_intel_portfolio_breadth": 1,
        },
    }
    for effect_name, changes in expected.items():
        block = _named_block(effects, effect_name)
        assert "has_country_flag = USA_intel_state_initialized" in block
        assert dict(_axis_writes(block)) == changes
        assert block.count("USA_intel_clamp_state = yes") == 1


def test_source_map_covers_every_exact_milestone_date():
    source_map = SOURCE_MAP_PATH.read_text(encoding="utf-8")
    for _event_number, _year, date in MILESTONES:
        iso_date = datetime.date(*map(int, date.split("."))).isoformat()
        assert iso_date in source_map
    for domain in ("intel.com", "ftc.gov", "sec.gov", "commerce.gov"):
        assert domain in source_map.lower()


def test_reconstruction_scheduling_and_recovery_cover_every_milestone():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    reconstruction = _named_block(effects, "USA_intel_reconstruct_history")
    schedule_history = _named_block(effects, "USA_intel_schedule_history")
    recovery = _named_block(effects, "USA_intel_recover_history")

    historical_records = []
    for event_number, year, date in MILESTONES:
        prefix = f"USA_intel_event_{event_number}"
        route_flag, _delta = ROUTES[event_number - 1][0]
        record_name = f"USA_intel_record_{route_flag.removeprefix('USA_intel_')}"
        historical_records.append(_named_block(effects, record_name))
        assert f"date > {date}" in reconstruction
        assert (
            f"NOT = {{ has_country_flag = USA_intel_expected_event_{event_number} }}"
            in reconstruction
        )
        assert f"NOT = {{ has_country_flag = {prefix}_pending }}" in reconstruction
        assert f"NOT = {{ has_country_flag = {prefix}_resolved }}" in reconstruction
        assert f"{record_name} = yes" in reconstruction

        milestone = datetime.date(*map(int, date.split(".")))
        delay = (milestone - datetime.date(year, 1, 1)).days
        schedule = _named_block(effects, f"USA_intel_schedule_event_{event_number}")
        assert f"NOT = {{ has_country_flag = {prefix}_resolved }}" in schedule
        assert (
            f"NOT = {{ has_country_flag = USA_intel_expected_event_{event_number} }}"
            in schedule
        )
        assert f"NOT = {{ has_country_flag = {prefix}_pending }}" in schedule
        assert f"set_country_flag = USA_intel_expected_event_{event_number}" in schedule
        assert f"flag = {prefix}_pending value = 1 days = {delay + 60}" in schedule
        assert (
            f"country_event = {{ id = USA_intel_events.{event_number} days = {delay} }}"
            in schedule
        )
        assert f"USA_intel_schedule_event_{event_number} = yes" in schedule_history

        assert f"date > {date}" in recovery
        assert f"has_country_flag = USA_intel_expected_event_{event_number}" in recovery
        assert f"NOT = {{ has_country_flag = {prefix}_pending }}" in recovery
        assert f"NOT = {{ has_country_flag = {prefix}_resolved }}" in recovery
        assert (
            f"country_event = {{ id = USA_intel_events.{event_number} days = 1 }}"
            in recovery
        )

    reconstruction_graph = reconstruction + "\n" + "\n".join(historical_records)
    for forbidden in (
        "modify_treasury_effect",
        "treasury_change",
        "add_political_power",
        "add_stability",
        "add_tech_bonus",
        "add_timed_idea",
        "add_building_construction",
        "add_offsite_building",
        "country_event =",
    ):
        assert forbidden not in reconstruction_graph

    scheduler_alias = _named_block(effects, "USA_intel_schedule_current_year_events")
    assert "USA_intel_schedule_history = yes" in scheduler_alias
    wrapper = _named_block(effects, "USA_intel_corporate_history_wrapper")
    assert "corporate_history_enabled = yes" in wrapper
    assert "USA_intel_reconstruct_history = yes" in wrapper
    assert "corporate_history_full_enabled = yes" in wrapper
    assert "USA_intel_schedule_current_year_events = yes" in wrapper


def test_shared_dispatch_recovers_full_late_starts_and_preserves_modes():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    common = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    dispatch = DISPATCH_PATH.read_text(encoding="utf-8")
    monthly_dispatch = MONTHLY_DISPATCH_PATH.read_text(encoding="utf-8")

    bootstrap = _named_block(monthly_dispatch, "corporate_history_country_bootstrap")
    monthly = _named_block(common, "USA_corporate_history_monthly_outcomes")
    full_monthly = next(
        block
        for block in _assignment_blocks(monthly, "if")
        if "limit = { corporate_history_full_enabled = yes }" in block
    )
    global_dispatch = _named_block(
        monthly_dispatch, "corporate_history_monthly_dispatch"
    )
    reconstruct = _named_block(effects, "USA_intel_reconstruct_history")
    schedule = _named_block(effects, "USA_intel_schedule_history")
    recovery = _named_block(effects, "USA_intel_recover_history")

    assert "corporate_history_enabled = yes" in global_dispatch
    assert "USA_intel_reconstruct_history = yes" in bootstrap
    assert "corporate_history_full_enabled = yes" in bootstrap
    assert "USA_intel_schedule_current_year_events = yes" in bootstrap
    assert "NOT = { has_country_flag = USA_intel_history_complete }" in full_monthly
    assert full_monthly.index(
        "USA_intel_reconstruct_history = yes"
    ) < full_monthly.index("USA_intel_recover_history = yes")
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert "USA_intel_reconstruct_history = yes" in monthly
    assert "NOT = { has_country_flag = USA_intel_history_complete }" in monthly
    assert "corporate_history_enabled = yes" in reconstruct
    assert "corporate_history_full_enabled = yes" not in reconstruct
    assert "corporate_history_full_enabled = yes" in schedule
    assert "corporate_history_full_enabled = yes" in recovery

    for year in sorted({year for _event_number, year, _date in MILESTONES}):
        year_effect = _named_block(dispatch, f"USA_corporate_trigger_year_{year}")
        assert "USA_intel_corporate_history_wrapper = yes" in year_effect
        year_router = _named_block(
            monthly_dispatch, f"corporate_history_dispatch_year_{year}"
        )
        assert "original_tag = USA" in year_router
        assert f"USA_corporate_trigger_year_{year} = yes" in year_router

    corpus = effects + "\n" + common + "\n" + dispatch + "\n" + monthly_dispatch
    assert "USA_intel_events.90" not in corpus


def test_static_scenarios_cover_full_later_start_resumed_outcomes_and_off():
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    names = {
        item["name"]
        for item in scenarios["scenarios"]
        if item.get("chain") == "USA_intel"
    }
    assert names == {
        "intel_full_2000_scheduler_only",
        "intel_full_2024_later_start",
        "intel_full_2025_resumed_state",
        "intel_outcomes_only_2026_terminal",
        "intel_disabled_2026_inert",
    }

    resumed = next(
        item
        for item in scenarios["scenarios"]
        if item.get("name") == "intel_full_2025_resumed_state"
    )
    assert resumed["initial_markers"] == [
        f"USA_intel_event_{event_number}_resolved" for event_number in range(1, 14)
    ]
    assert resumed["expected"]["visible_events"] == ["USA_intel_events.14"]
    assert resumed["expected"]["stranded_markers"] == []

    scripts = ScriptIndex.load(ROOT)
    results, passed = run_scenarios(manifest, scenarios, sorted(names), scripts)
    assert passed, results


def test_dashboard_bridge_policies_and_physical_stack_use_read_only_adapters():
    dashboard = DASHBOARD_PATH.read_text(encoding="utf-8")
    dashboard_loc = DASHBOARD_LOC_PATH.read_text(encoding="utf-8")
    corporate_effects = CORPORATE_SYSTEMS_EFFECTS_PATH.read_text(encoding="utf-8")
    physical_effects = PHYSICAL_EFFECTS_PATH.read_text(encoding="utf-8")
    physical_ideas = PHYSICAL_IDEAS_PATH.read_text(encoding="utf-8")

    panel = _named_block(dashboard, "USA_corporate_systems_processor_foundry")
    assert "cost = 0" in panel
    assert "has_country_flag = USA_intel_state_initialized" in panel
    assert "always = no" in panel
    assert "ai_will_do = { base = 0 }" in panel
    for selector in (
        "USA_intel_dashboard_era",
        "USA_intel_dashboard_capstone",
        "USA_intel_dashboard_processor_pillar",
        "USA_intel_dashboard_full_spectrum",
    ):
        assert f"name = {selector}" in dashboard_loc

    contribution = _named_block(
        corporate_effects, "USA_corporate_systems_intel_contribution"
    )
    for idea in OUTCOMES.values():
        assert f"has_idea = {idea}" in contribution
    contribution_writes = re.findall(
        r"(?:add_to|subtract_from)_temp_variable\s*=\s*\{\s*"
        r"(USA_oem_contribution_[A-Za-z0-9_]+)\s*=\s*1\s*\}",
        contribution,
    )
    assert len(contribution_writes) == 11
    assert contribution.count("else_if = {") == len(OUTCOMES) - 1

    policy_effects = (
        "USA_intel_apply_open_systems_procurement",
        "USA_intel_apply_domestic_capacity_grants",
        "USA_intel_apply_secure_federal_systems",
        "USA_intel_apply_advanced_computing_consortium",
    )
    for effect_name in policy_effects:
        assert f"{effect_name} = yes" in dashboard
    assert dashboard.count("has_country_flag = USA_intel_state_initialized") >= 5

    original_stack, intel_extension = physical_effects.split(
        "# Intel extends the aggregate", maxsplit=1
    )
    stack_resolution = original_stack[
        original_stack.index("USA_physical_compute_stack_resolve") :
    ]
    assert "USA_intel_" not in stack_resolution
    for original_idea in (
        "USA_foundational_semiconductor_base",
        "USA_memory_arsenal",
        "USA_mission_critical_networks",
        "USA_physical_compute_stack",
    ):
        assert original_idea in stack_resolution
    for intel_idea in (
        "USA_processor_architecture_anchor",
        "USA_full_spectrum_compute_stack",
    ):
        assert intel_idea in intel_extension
        assert _idea_block(physical_ideas, intel_idea)
    assert "USA_corporate_systems_update_economic_bridge = yes" in intel_extension


def test_visible_events_have_three_durable_routes_and_bespoke_era_art():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    event_ids = re.findall(r"(?m)^\s*id\s*=\s*(USA_intel_events\.\d+)\s*$", events)
    assert event_ids == [f"USA_intel_events.{number}" for number in range(1, 16)]
    assert len(event_ids) == len(set(event_ids))

    for event_number, (routes, picture) in enumerate(zip(ROUTES, PICTURES), start=1):
        event = _event_block(events, event_number)
        options = _option_blocks(event)
        assert len(options) == 3
        assert "is_triggered_only = yes" in event
        assert "fire_only_once = yes" in event
        assert "corporate_history_full_enabled = yes" in event
        assert "original_tag = USA" in event
        assert "NOT = { has_country_flag = collapsed_nation }" in event
        assert f"picture = {picture}" in event
        assert f"title = USA_intel_events.{event_number}.t" in event
        assert f"desc = USA_intel_events.{event_number}.d" in event

        immediate = _named_block(event, "immediate")
        assert "USA_intel_initialize_state = yes" in immediate
        assert f"USA_intel_mark_event_{event_number:02d}_resolved = yes" in immediate
        for option_index, (option, (flag, _delta)) in enumerate(zip(options, routes)):
            suffix = "abc"[option_index]
            key = f"USA_intel_events.{event_number}.{suffix}"
            record = f"USA_intel_record_{flag.removeprefix('USA_intel_')}"
            hidden_effect = _named_block(option, "hidden_effect")
            engine_payload = _engine_effect_payload(hidden_effect)
            effect_tooltips = _assignment_blocks(option, "effect_tooltip")
            assert f"name = {key}" in option
            assert f"custom_effect_tooltip = {key}_tt" in option
            assert f'{key} executed"' in option
            assert f"{record} = yes" in option
            assert "ai_chance = {" in option
            assert "hidden_effect = {" in option
            if engine_payload:
                assert len(effect_tooltips) == 1
                effect_tooltip = effect_tooltips[0]
                assert "USA_intel_record_" not in effect_tooltip
                assert "USA_intel_resolve_history" not in effect_tooltip
                assert _engine_effect_payload(effect_tooltip) == engine_payload
                preview = re.search(r"(?m)^\s*effect_tooltip\s*=", option)
                custom = re.search(r"(?m)^\s*custom_effect_tooltip\s*=", option)
                assert preview and custom and preview.start() < custom.start()
            else:
                assert effect_tooltips == []
            if event_number == 15:
                assert "USA_intel_resolve_history = yes" in option
            else:
                assert "USA_intel_resolve_history = yes" not in option


def test_event_ai_always_has_a_bankruptcy_safe_route():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    for event_number in range(1, 16):
        options = _option_blocks(_event_block(events, event_number))
        for option in options:
            if _has_negative_treasury_change(option):
                assert _has_bankruptcy_zero_modifier(option)
        assert any(
            not _has_negative_treasury_change(option)
            and not _has_bankruptcy_zero_modifier(option)
            and not _has_unconditional_historical_zero_modifier(option)
            and _has_positive_bankruptcy_weight(option)
            for option in options
        )


def test_localisation_inventory_dashboard_values_and_utf8_bom_are_complete():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    localisation = LOCALISATION_PATH.read_text(encoding="utf-8-sig")
    assert LOCALISATION_PATH.read_bytes().startswith(b"\xef\xbb\xbf")
    keys = set(re.findall(r"(?m)^ ([A-Za-z0-9_.]+):", localisation))

    referenced = set(
        re.findall(
            r"(?m)^\s*(?:title|desc|name|custom_effect_tooltip)\s*=\s*"
            r"(USA_intel_events\.[A-Za-z0-9_.]+)\s*$",
            events,
        )
    )
    for idea in OUTCOMES.values():
        referenced.add(idea)
        referenced.add(f"{idea}_desc")
    referenced.update(SHARED_LOCALISATION_KEYS)
    assert referenced <= keys

    option_tooltips = dict(
        re.findall(
            r"(?m)^ (USA_intel_events\.(?:[1-9]|1[0-5])\.[abc]_tt):"
            r'(?:\d+)?\s+"([^"]*)"\s*$',
            localisation,
        )
    )
    expected_tooltips = {
        f"USA_intel_events.{event_number}.{suffix}_tt"
        for event_number in range(1, 16)
        for suffix in "abc"
    }
    axis_labels = {
        axis.removeprefix("USA_intel_").replace("_", " ").title() for axis in AXES
    }
    assert set(option_tooltips) == expected_tooltips
    for tooltip in option_tooltips.values():
        lower_tooltip = tooltip.casefold()
        assert tooltip.strip()
        assert not any(
            phrase in lower_tooltip
            for phrase in (
                "treasury",
                "political power",
                "research bonus",
                "technology",
            )
        )
        assert any(label in tooltip for label in axis_labels)

    processor_desc = re.search(
        r'(?m)^ USA_corporate_systems_processor_foundry_desc:(?:\d+)?\s+"([^"]*)"',
        localisation,
    )
    assert processor_desc
    for axis in AXES:
        assert f"[?{axis}|0]" in processor_desc.group(1)
    for selector in (
        "[USA_intel_dashboard_era]",
        "[USA_intel_dashboard_capstone]",
        "[USA_intel_dashboard_processor_pillar]",
        "[USA_intel_dashboard_full_spectrum]",
    ):
        assert selector in processor_desc.group(1)

    physical_desc = re.search(
        r'(?m)^ USA_corporate_systems_physical_compute_desc:(?:\d+)?\s+"([^"]*)"',
        localisation,
    )
    assert physical_desc
    assert "[USA_intel_dashboard_processor_pillar]" in physical_desc.group(1)
    assert "[USA_intel_dashboard_full_spectrum]" in physical_desc.group(1)


def test_intel_uses_existing_repository_art():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")

    assert events.count("picture = GFX_computer") == 15
    assert ideas.count("picture = generic_intel_bonus") == 6


def test_intel_owns_all_persistent_writes_and_declares_foreign_reads():
    events = EVENTS_PATH.read_text(encoding="utf-8")
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    corpus = events + "\n" + effects

    flag_writes = re.findall(
        r"(?:set|clr)_country_flag\s*=\s*(?:\{\s*flag\s*=\s*)?" r"([A-Z][A-Za-z0-9_]+)",
        corpus,
    )
    assert flag_writes
    assert all(flag.startswith("USA_intel_") for flag in flag_writes)

    variable_writes = re.findall(
        r"(?:set_variable|add_to_variable|subtract_from_variable)\s*=\s*\{\s*"
        r"([A-Za-z0-9_]+)\s*=",
        corpus,
    )
    assert variable_writes
    assert all(variable.startswith("USA_intel_") for variable in variable_writes)

    read_flags = set(re.findall(r"has_country_flag\s*=\s*([A-Z][A-Za-z0-9_]+)", corpus))
    foreign_reads = {
        flag
        for flag in read_flags
        if not flag.startswith("USA_intel_") and flag != "collapsed_nation"
    }
    assert foreign_reads == ALLOWED_READS
