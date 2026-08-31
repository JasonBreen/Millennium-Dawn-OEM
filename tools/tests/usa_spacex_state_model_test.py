import datetime
import json
import re
import sys
from pathlib import Path

from tools.shared_utils import extract_block_from_text

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "analysis"))

from simulate_corporate_history import ScriptIndex, run_scenarios

EVENTS_PATH = ROOT / "events" / "USA_spacex_events.txt"
EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_spacex_effects.txt"
IDEAS_PATH = ROOT / "common" / "ideas" / "USA_spacex_ideas.txt"
LOCALISATION_PATH = ROOT / "localisation" / "english" / "MD_focus_USA_l_english.yml"
COMMON_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_effects.txt"
)
MONTHLY_DISPATCH_PATH = (
    ROOT
    / "common"
    / "scripted_effects"
    / "00_corporate_history_monthly_dispatch_effects.txt"
)
MIDYEAR_RECOVERY_PATH = (
    ROOT
    / "common"
    / "scripted_effects"
    / "00_corporate_history_midyear_recovery_effects.txt"
)
CONTRACT_PATH = ROOT / "tools" / "corporate_history_contract.json"
SCENARIOS_PATH = ROOT / "tools" / "corporate_history_scenarios.json"

AXES = (
    "USA_spacex_launch_cadence_reliability",
    "USA_spacex_reusability_depth",
    "USA_spacex_government_partnership",
    "USA_spacex_commercial_market_power",
    "USA_spacex_leo_satcom_presence",
    "USA_spacex_heavy_deep_space_lift",
    "USA_spacex_geostrategic_access",
)

# event, year, date, delay, dispatcher, resolved marker, historical recorder
MILESTONES = (
    (
        1,
        2002,
        "2002.3.14",
        72,
        "USA_spacex_dispatch_2002",
        "USA_spacex_founded",
        "USA_spacex_record_foundation",
    ),
    (
        2,
        2008,
        "2008.9.28",
        271,
        "USA_spacex_dispatch_2008",
        "USA_spacex_falcon1_success",
        "USA_spacex_record_falcon1_success",
    ),
    (
        3,
        2006,
        "2006.8.1",
        212,
        "USA_spacex_dispatch_2006",
        "USA_spacex_cots_crs_awarded",
        "USA_spacex_record_cots_crs_awarded",
    ),
    (
        4,
        2010,
        "2010.6.4",
        154,
        "USA_spacex_dispatch_2010",
        "USA_spacex_falcon9_firstflight",
        "USA_spacex_record_falcon9_firstflight",
    ),
    (
        5,
        2015,
        "2015.12.22",
        355,
        "USA_spacex_dispatch_2015",
        "USA_spacex_first_stage_landing",
        "USA_spacex_record_first_landing",
    ),
    (
        6,
        2018,
        "2018.2.6",
        36,
        "USA_spacex_dispatch_2018",
        "USA_spacex_falcon_heavy_demo",
        "USA_spacex_record_falcon_heavy_demo",
    ),
    (
        7,
        2019,
        "2019.5.23",
        142,
        "USA_spacex_dispatch_2019",
        "USA_spacex_starlink_initial",
        "USA_spacex_record_starlink_initial",
    ),
    (
        8,
        2020,
        "2020.5.30",
        150,
        "USA_spacex_dispatch_2020",
        "USA_spacex_commercial_crew_operational",
        "USA_spacex_record_commercial_crew",
    ),
    (
        9,
        2021,
        "2021.8.1",
        212,
        "USA_spacex_dispatch_2021_nssl",
        "USA_spacex_nssl_dual_source",
        "USA_spacex_record_nssl_dual_source",
    ),
    (
        10,
        2021,
        "2021.4.16",
        105,
        "USA_spacex_dispatch_2021_hls",
        "USA_spacex_hls_award",
        "USA_spacex_record_hls_award",
    ),
    (
        11,
        2023,
        "2023.4.20",
        109,
        "USA_spacex_dispatch_2023",
        "USA_spacex_iterative_licensing",
        "USA_spacex_record_starship_iterative_licensing",
    ),
    (
        12,
        2026,
        "2026.9.1",
        243,
        "USA_spacex_dispatch_2026",
        "USA_spacex_capstone_resolved",
        "USA_spacex_resolve_capstone",
    ),
)

OUTCOMES = (
    "USA_spacex_cadence_champion",
    "USA_spacex_allied_leo_connectivity",
    "USA_spacex_deep_space_stack",
    "USA_spacex_commercial_monopoly_risk",
    "USA_spacex_mixed_provider_ecosystem",
)


def _extract_block(text: str, start: int) -> str:
    _body, end = extract_block_from_text(text, start)
    assert end != -1, "Unclosed scripted block"
    return text[start:end]


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^[ \t]*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"Missing block {name}"
    return _extract_block(text, match.start())


def _event_block(text: str, event_number: int) -> str:
    event_id = f"USA_spacex_events.{event_number}"
    for match in re.finditer(r"(?m)^country_event\s*=\s*\{", text):
        block = _extract_block(text, match.start())
        if re.search(rf"\bid\s*=\s*{re.escape(event_id)}\b", block):
            return block
    raise AssertionError(f"Missing event {event_id}")


def _assignment_blocks(text: str, key: str) -> list[str]:
    return [
        _extract_block(text, match.start())
        for match in re.finditer(rf"\b{re.escape(key)}\s*=\s*\{{", text)
    ]


def _axis_writes(text: str) -> dict[str, int]:
    writes = {}
    for axis, value in re.findall(
        r"add_to_variable\s*=\s*\{\s*" r"(USA_spacex_[A-Za-z0-9_]+)\s*=\s*(-?\d+)\s*\}",
        text,
    ):
        if axis in AXES:
            writes[axis] = writes.get(axis, 0) + int(value)
    return writes


def test_manifest_initialization_clamp_and_idea_ownership():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    ideas = IDEAS_PATH.read_text(encoding="utf-8")
    initialize = _named_block(effects, "USA_spacex_initialize_state")
    clamp = _named_block(effects, "USA_spacex_clamp_state")

    nonzero_initial = {
        "USA_spacex_launch_cadence_reliability": 1,
        "USA_spacex_reusability_depth": 1,
        "USA_spacex_government_partnership": 1,
        "USA_spacex_geostrategic_access": 1,
    }
    for axis, value in nonzero_initial.items():
        assert f"set_variable = {{ {axis} = {value} }}" in initialize
    for axis in set(AXES) - set(nonzero_initial):
        assert f"set_variable = {{ {axis} = 0 }}" not in initialize
    assert "set_country_flag = USA_spacex_state_initialized" in initialize

    for axis in AXES:
        assert f"set_temp_variable = {{ corp_value = {axis} }}" in clamp
        assert f"set_variable = {{ {axis} = corp_value }}" in clamp
    assert clamp.count("corporate_history_clamp_value = yes") == len(AXES)

    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    chain = next(item for item in manifest["chains"] if item["root"] == "USA_spacex")
    assert chain["name"] == "SpaceX"
    assert chain["tag"] == "USA"
    assert chain["namespace"] == "USA_spacex_events"
    assert chain["tier"] == 1
    assert chain["owned_prefixes"] == ["USA_spacex"]
    assert set(chain["variables"]) == set(AXES)
    assert all(
        bounds == {"min": 0, "max": 10} for bounds in chain["variables"].values()
    )
    assert chain["allowed_reads"] == []
    assert chain["allowed_writes"] == []
    assert chain["terminal_marker"] == "USA_spacex_reconstruct_complete"
    assert chain["terminal_date"] == "2026-09-01"
    assert set(chain["outcome_ideas"]) == set(OUTCOMES)

    for outcome in OUTCOMES:
        block = _named_block(ideas, outcome)
        assert "picture =" in block
        assert "allowed =" not in block


def test_reconstruction_owns_completion_and_full_preserves_visible_choices():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    common = COMMON_EFFECTS_PATH.read_text(encoding="utf-8")
    monthly_dispatch = MONTHLY_DISPATCH_PATH.read_text(encoding="utf-8")

    reconstruct_root = _named_block(effects, "USA_spacex_reconstruct_history")
    reconstruct = _named_block(effects, "USA_spacex_reconstruct_outcomes_history")
    assert "corporate_history_outcomes_only_enabled = yes" in reconstruct_root
    assert "USA_spacex_reconstruct_outcomes_history = yes" in reconstruct_root
    for _number, _year, date, _delay, _dispatch, _marker, recorder in MILESTONES:
        if recorder == "USA_spacex_resolve_capstone":
            continue
        assert f"date > {date}" in reconstruct
        assert f"{recorder} = yes" in reconstruct
    assert "date > 2026.9.1" in reconstruct
    assert "USA_spacex_resolve_capstone = yes" in reconstruct
    assert "set_country_flag = USA_spacex_reconstruct_complete" in reconstruct_root
    assert "set_country_flag = USA_spacex_reconstruct_complete" not in reconstruct

    monthly = _named_block(common, "USA_corporate_history_monthly_outcomes")
    full_branch = next(
        block
        for block in _assignment_blocks(monthly, "if")
        if re.match(
            r"if\s*=\s*\{\s*limit\s*=\s*\{\s*"
            r"corporate_history_full_enabled\s*=\s*yes\s*\}",
            block,
        )
    )
    assert "USA_spacex_reconstruct_history = yes" not in full_branch
    assert monthly.count("USA_spacex_reconstruct_history = yes") == 1
    outcomes_call = monthly.index("USA_spacex_reconstruct_history = yes")
    assert (
        monthly.rfind("corporate_history_outcomes_only_enabled = yes", 0, outcomes_call)
        >= 0
    )
    assert "NOT = { has_country_flag = USA_spacex_reconstruct_complete }" in monthly
    assert "USA_spacex_events.90" not in monthly
    assert monthly.index("USA_spacex_recover_prior_year_history = yes") < monthly.index(
        "corporate_history_monthly_dispatch = yes"
    )

    bootstrap = _named_block(monthly_dispatch, "corporate_history_country_bootstrap")
    assert bootstrap.count("USA_spacex_reconstruct_history = yes") == 1
    assert "USA_spacex_schedule_current_year_events = yes" in bootstrap


def test_every_visible_event_has_exact_schedule_pending_cleanup_and_recovery():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    events = EVENTS_PATH.read_text(encoding="utf-8")
    recovery_text = MIDYEAR_RECOVERY_PATH.read_text(encoding="utf-8")
    recovery = _named_block(
        recovery_text, "USA_corporate_history_recover_midyear_events"
    )
    recovery_initialization = _named_block(
        recovery_text, "USA_corporate_history_initialize_midyear_recovery"
    )
    assert "midyear_spacex" not in recovery_initialization

    for number, year, date, delay, dispatcher, marker, _recorder in MILESTONES:
        milestone = datetime.date(*map(int, date.split(".")))
        assert (milestone - datetime.date(year, 1, 1)).days == delay

        pending = f"USA_corporate_history_midyear_spacex_events_{number}_pending"
        resolved = f"USA_corporate_history_midyear_spacex_events_{number}_resolved"
        dispatch = _named_block(effects, dispatcher)
        assert f"NOT = {{ has_country_flag = {resolved} }}" in dispatch
        assert f"NOT = {{ has_country_flag = {marker} }}" in dispatch
        assert f"NOT = {{ has_country_flag = {pending} }}" in dispatch
        assert f"flag = {pending} days = {delay + 60} value = 1" in dispatch
        assert (
            f"country_event = {{ id = USA_spacex_events.{number} days = {delay} }}"
            in dispatch
        )

        event = _event_block(events, number)
        assert "is_triggered_only = yes" in event
        assert "original_tag = USA" in event
        immediate = _assignment_blocks(event, "immediate")
        assert len(immediate) == 1
        assert f"clr_country_flag = {pending}" in immediate[0]

        assert f"date > {date}" in recovery
        assert f"NOT = {{ has_country_flag = {resolved} }}" in recovery
        assert f"NOT = {{ has_country_flag = {marker} }}" in recovery
        assert f"NOT = {{ has_country_flag = {pending} }}" in recovery
        assert f"NOT = {{ has_country_flag = {marker} }}" in recovery
        assert (
            f"country_event = {{ id = USA_spacex_events.{number} days = 1 }}"
            in recovery
        )

    prior_year = _named_block(effects, "USA_spacex_recover_prior_year_history")
    for number, _year, _date, _delay, _dispatcher, marker, _recorder in MILESTONES:
        pending = f"USA_corporate_history_midyear_spacex_events_{number}_pending"
        assert f"NOT = {{ has_country_flag = {pending} }}" in prior_year
        assert f"NOT = {{ has_country_flag = {marker} }}" in prior_year


def test_historical_deltas_match_tooltips_and_capstone_routes_are_flags_only():
    effects = EFFECTS_PATH.read_text(encoding="utf-8")
    localisation = LOCALISATION_PATH.read_text(encoding="utf-8-sig")

    expected = {
        "USA_spacex_record_falcon9_firstflight": {
            "USA_spacex_launch_cadence_reliability": 1,
            "USA_spacex_government_partnership": 1,
        },
        "USA_spacex_record_starlink_initial": {
            "USA_spacex_leo_satcom_presence": 2,
            "USA_spacex_commercial_market_power": 1,
        },
        "USA_spacex_record_commercial_crew": {
            "USA_spacex_government_partnership": 2,
            "USA_spacex_launch_cadence_reliability": 1,
        },
    }
    for effect_name, writes in expected.items():
        assert _axis_writes(_named_block(effects, effect_name)) == writes

    assert (
        ' USA_spacex_events.4.a_tt: "Launch Cadence: §G+1§! • '
        'Government Partnership: §G+1§!."' in localisation
    )
    assert (
        ' USA_spacex_events.7.a_tt: "LEO Satcom Presence: §G+2§! • '
        'Commercial Power: §G+1§!."' in localisation
    )
    assert (
        ' USA_spacex_events.8.a_tt: "Government Partnership: §G+2§! • '
        'Launch Cadence: §G+1§!."' in localisation
    )

    route_suffixes = (
        "cadence",
        "starship",
        "public_contract",
        "starlink",
        "monopoly",
        "mixed",
    )
    for suffix in route_suffixes:
        route = _named_block(effects, f"USA_spacex_record_route_{suffix}")
        assert "USA_spacex_clear_route = yes" in route
        assert f"set_country_flag = USA_spacex_route_{suffix}" in route
        assert _axis_writes(route) == {}
        assert "USA_spacex_clamp_state = yes" not in route

    resolver = _named_block(effects, "USA_spacex_resolve_capstone")
    assert resolver.count("USA_spacex_clear_capstone_outcome = yes") == 0
    for outcome in OUTCOMES:
        assert outcome in effects

    event_12 = _event_block(EVENTS_PATH.read_text(encoding="utf-8"), 12)
    assert "USA_spacex_events.12.d_option executed" in event_12
    assert "USA_spacex_events.12.d executed" not in event_12


def test_english_localisation_and_event_contract_are_load_safe():
    raw = LOCALISATION_PATH.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert not raw.startswith(b"\xef\xbb\xbf\xef\xbb\xbf")
    assert b"\r\n" not in raw

    text = raw.decode("utf-8-sig")
    assert text.startswith("l_english:\n")
    assert ":0 " not in text
    assert "‑" not in "\n".join(
        line for line in text.splitlines() if "USA_spacex" in line
    )
    spacex_key_lines = [
        line for line in text.splitlines() if re.match(r"^\s*USA_spacex", line)
    ]
    assert spacex_key_lines
    assert all(line.startswith(" USA_spacex") for line in spacex_key_lines)

    events = EVENTS_PATH.read_text(encoding="utf-8")
    for number in range(1, 13):
        event = _event_block(events, number)
        assert "is_triggered_only = yes" in event
        assert "original_tag = USA" in event
        assert re.search(rf"\bid\s*=\s*USA_spacex_events\.{number}\b", event)


def test_static_scenarios_cover_full_resumed_outcomes_and_off():
    manifest = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    names = {
        item["name"]
        for item in scenarios["scenarios"]
        if item.get("chain") == "USA_spacex"
    }
    assert names == {
        "spacex_full_2000_chronology",
        "spacex_full_2023_resumed_history",
        "spacex_outcomes_only_2026_terminal",
        "spacex_disabled_2026_inert",
    }

    scripts = ScriptIndex.load(ROOT)
    results, passed = run_scenarios(manifest, scenarios, sorted(names), scripts)
    assert passed, results
