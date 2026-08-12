#!/usr/bin/env python3
"""Validate the corporate-history framework contract."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import blank_quoted_strings, extract_block_from_text, strip_comments
from validator_common import BaseValidator, run_validator_main

TITLE = "CORPORATE HISTORY CONTRACT VALIDATION"

_EVENT_KEYWORDS = (
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
)
_EVENT_ALT = "|".join(_EVENT_KEYWORDS)
_EVENT_DEF_RE = re.compile(r"(?m)^(" + _EVENT_ALT + r")\s*=\s*\{")
_BLOCK_IDENTIFIER = r"[A-Za-z0-9_.:@^\[\]-]+"
_TOP_LEVEL_BLOCK_RE = re.compile(r"(?m)^(" + _BLOCK_IDENTIFIER + r")\s*=\s*\{")
_OPTION_RE = re.compile(r"\boption\s*=\s*\{")
_IMMEDIATE_RE = re.compile(r"\bimmediate\s*=\s*\{")
_ID_RE = re.compile(r"\bid\s*=\s*([A-Za-z0-9_.]+)")
_EVENT_SHORT_CALL_RE = re.compile(
    r"\b(?:" + _EVENT_ALT + r")\s*=\s*([A-Za-z0-9_.]+)\b(?!\s*\{)"
)
_EVENT_LONG_CALL_RE = re.compile(r"\b(?:" + _EVENT_ALT + r")\s*=\s*\{")
_EFFECT_YES_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b")
_SET_VAR_RE = re.compile(
    r"\b(?:set_variable|add_to_variable|subtract_from_variable|multiply_variable|divide_variable)\s*=\s*\{\s*([A-Za-z0-9_]+)"
)
_CLAMP_VAR_RE = re.compile(
    r"\bclamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_]+)\s+min\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s+max\s*=\s*(-?(?:\d+(?:\.\d*)?|\.\d+))"
)
_SET_TEMP_CORP_RE = re.compile(
    r"\bset_temp_variable\s*=\s*\{\s*corp_value\s*=\s*([A-Za-z0-9_]+)\s*\}"
)
_DIRECT_CORP_CLAMP_RE = re.compile(r"\bcorporate_history_clamp_value\s*=\s*yes\b")
_ADD_IDEA_RE = re.compile(r"\badd_ideas\s*=\s*([A-Za-z0-9_]+)")
_REMOVE_IDEA_RE = re.compile(r"\bremove_ideas\s*=\s*([A-Za-z0-9_]+)")
_REMOVE_IDEA_BLOCK_RE = re.compile(r"\bremove_ideas\s*=\s*\{")
_BLOCK_HEADER_RE = re.compile(r"([A-Za-z0-9_.:@^\[\]-]+)\s*=\s*\{")
_MARKER_TRIGGER_RE = re.compile(r"\b(?:has_country_flag|has_idea)\s*=")
_LOC_KEY_PREFIX_RE = re.compile(r"^\s*([^\s:#]+):\d*(?:\s+.*)?$")
_VALID_LOC_VALUE_RE = re.compile(r'^\s*[^\s:#]+:\d*\s+"(?:\\.|[^"\\])*"\s*(?:#.*)?$')
_SCRIPT_TOKEN_CAPTURE = r"([A-Za-z0-9_.:@^\[\]-]+)"
_SCRIPT_TOKEN_RE = re.compile(r"[A-Za-z0-9_.:@^\[\]-]+")
_NATIVE_FLAG_WRITE_EFFECT_PATTERN = (
    r"(?:set|clr|modify)_"
    r"(?:character|country|country_pmc|global|mio|project|state|unit_leader)_flag"
)
_NATIVE_VARIABLE_BLOCK_EFFECTS = (
    "set_variable",
    "add_to_variable",
    "subtract_from_variable",
    "multiply_variable",
    "divide_variable",
    "modulo_variable",
    "clamp_variable",
    "randomize_variable",
    "set_variable_to_random",
)
_NATIVE_VARIABLE_BLOCK_EFFECT_PATTERN = (
    r"(?:" + "|".join(_NATIVE_VARIABLE_BLOCK_EFFECTS) + r")"
)
_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS = ("clear_variable", "round_variable")
_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECT_PATTERN = (
    r"(?:" + "|".join(_NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS) + r")"
)
_NATIVE_ARRAY_BLOCK_EFFECTS = ("add_to_array", "remove_from_array", "resize_array")
_NATIVE_ARRAY_BLOCK_EFFECT_PATTERN = (
    r"(?:" + "|".join(_NATIVE_ARRAY_BLOCK_EFFECTS) + r")"
)
_NATIVE_WRITE_PATTERNS = (
    re.compile(
        r"\b" + _NATIVE_FLAG_WRITE_EFFECT_PATTERN + r"\s*=\s*"
        r"(?:\{\s*flag\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_FLAG_WRITE_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\bflag\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b" + _NATIVE_VARIABLE_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{\s*"
        r"(?:var\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_VARIABLE_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\bvar\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b"
        + _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECT_PATTERN
        + r"\s*=\s*"
        + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\b(?:var|which)\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b" + _NATIVE_ARRAY_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{\s*"
        r"(?:array\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b" + _NATIVE_ARRAY_BLOCK_EFFECT_PATTERN + r"\s*=\s*\{[^{}]*?"
        r"\barray\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(r"\bclear_array\s*=\s*" + _SCRIPT_TOKEN_CAPTURE),
    re.compile(
        r"\bclear_array\s*=\s*\{[^{}]*?\barray\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:find_highest_in_array|find_lowest_in_array)\s*=\s*\{[^{}]*?"
        r"\bvalue\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:find_highest_in_array|find_lowest_in_array)\s*=\s*\{[^{}]*?"
        r"\bindex\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:add_ideas|remove_ideas|add_idea|remove_idea)\s*=\s*"
        + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\badd_timed_idea\s*=\s*\{[^{}]*?\bidea\s*=\s*" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:complete_national_focus|uncomplete_national_focus|unlock_national_focus)\s*=\s*"
        r"(?:\{\s*focus\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE
    ),
    re.compile(
        r"\b(?:" + _EVENT_ALT + r")\s*=\s*"
        r"(?:\{[^{}]*?\bid\s*=\s*)?" + _SCRIPT_TOKEN_CAPTURE,
        re.DOTALL,
    ),
)
_NATIVE_IDEA_BLOCK_RE = re.compile(
    r"\b(?:add_ideas|remove_ideas)\s*=\s*\{([^{}]*)\}", re.DOTALL
)
_NATIVE_CONTRACT_ROLES = (
    "effect",
    "trigger",
    "on_action",
    "event",
    "idea",
    "decision",
    "category",
)
_CUSTOM_EFFECT_REWARDS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("Political Power", re.compile(r"\badd_political_power\b")),
    ("Stability", re.compile(r"\badd_stability\b")),
    ("War Support", re.compile(r"\badd_war_support\b")),
    ("treasury changes", re.compile(r"\bmodify_treasury_effect\b")),
    ("research bonuses", re.compile(r"\badd_tech_bonus\b|\badd_research_slot\b")),
    (
        "factories",
        re.compile(
            r"\badd_building_construction\b[\s\S]{0,120}\b(?:industrial_complex|arms_factory|dockyard|office_park)\b"
        ),
    ),
    (
        "microchip plants",
        re.compile(
            r"\badd_building_construction\b[\s\S]{0,120}\bmicrochip_plant\b|\bproduction_speed_microchip_plant_factor\b"
        ),
    ),
    (
        "one-time economic rewards",
        re.compile(r"\badd_extra_state_shared_building_slots\b|\badd_resource\b"),
    ),
)


def _native_token_fragment(token: str, prefixes: Tuple[str, ...]) -> Optional[str]:
    for fragment in re.split(r"[.:@^\[\]]+", token):
        if fragment.startswith(prefixes):
            return fragment
    return None


def _collect_native_write_tokens(text: str, prefixes: Tuple[str, ...]) -> Set[str]:
    native_writes: Set[str] = set()
    for pattern in _NATIVE_WRITE_PATTERNS:
        for token in pattern.findall(text):
            fragment = _native_token_fragment(token, prefixes)
            if fragment:
                native_writes.add(fragment)
    for idea_block in _NATIVE_IDEA_BLOCK_RE.findall(text):
        for token in _SCRIPT_TOKEN_RE.findall(idea_block):
            fragment = _native_token_fragment(token, prefixes)
            if fragment:
                native_writes.add(fragment)
    return native_writes


_WRITE_KEYWORDS = (
    "set_country_flag",
    "clr_country_flag",
    "set_variable",
    "add_to_variable",
    "subtract_from_variable",
    "multiply_variable",
    "divide_variable",
    "clamp_variable",
    "add_ideas",
    "remove_ideas",
)
_READ_KEYWORDS = ("has_country_flag", "has_idea", "check_variable")
_OEM_STARTUP_EFFECT = "OEM_corporate_history_startup_bootstrap"
_OEM_STARTUP_FLAG = "GLOBAL_oem_corporate_history_startup_dispatched"
_OEM_STARTUP_ON_ACTION = "common/on_actions/01_oem_corporate_history_on_actions.txt"
_USA_2000_STARTUP_EVENTS = (
    "USA_oem_events.13",
    "gpu_development.1",
    "USA_ibm_events.12",
    "USA_ibm_events.13",
    "USA_ibm_events.90",
    "USA_e3_events.1",
    "USA_e3_events.90",
    "USA_hp_events.1",
)


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and Decimal(str(value)).is_finite()
    )


def _is_repeatable_decision(text: str) -> bool:
    return bool(re.search(r"\bfire_only_once\s*=\s*no\b", strip_comments(text)))


def _removes_active_decision(text: str, decision_id: str) -> bool:
    return bool(
        re.search(
            rf"(?m)^\s*remove_decision\s*=\s*{re.escape(decision_id)}\s*$",
            strip_comments(text),
        )
    )


@dataclass(frozen=True)
class Bound:
    minimum: Decimal
    maximum: Decimal


@dataclass(frozen=True)
class AuxiliaryLifecycleConfig:
    root: str
    tag: str
    reconstruction_effect: str
    scheduler_effect: str
    monthly_driver: str
    terminal_marker: str
    terminal_date: str
    expected_yearly_callers: Mapping[str, str]


@dataclass
class ChainConfig:
    name: str
    tag: str
    namespace: str
    root: str
    tier: int
    owned_prefixes: Tuple[str, ...]
    variables: Dict[str, Bound]
    outcome_idea_prefixes: Tuple[str, ...]
    requires_current_year_scheduler: bool
    allow_yearly_scheduler_duplicates: bool
    callerless_anchors: Set[str]
    allowed_multiple_callers: Set[str]
    allowed_reads: Tuple[str, ...]
    allowed_writes: Tuple[str, ...]
    full_start_strategies: Tuple[str, ...] = ()
    outcomes_only_strategy: str = ""
    declared_monthly_driver: str = ""
    terminal_marker: str = ""
    terminal_date: str = ""
    outcome_ideas: Tuple[str, ...] = ()
    expected_callers: Mapping[str, Tuple[str, ...]] = field(default_factory=dict)
    dependency_order: Tuple[str, ...] = ()
    localisation_prefixes: Tuple[str, ...] = ()
    effect_preview_policy: str = "engine_or_explicit"
    tooltip_exemptions: Mapping[str, str] = field(default_factory=dict)
    bridge_refresh_policy: str = "none"
    ai_bankruptcy_exceptions: Tuple[str, ...] = ()
    auxiliary_completion_markers: Tuple[str, ...] = ()
    auxiliary_lifecycles: Tuple[AuxiliaryLifecycleConfig, ...] = ()
    allow_multiple_completion_producers: bool = False

    @property
    def completion_flag(self) -> str:
        return self.terminal_marker or f"{self.root}_reconstruct_complete"

    @property
    def reconstruct_effect(self) -> str:
        return f"{self.root}_reconstruct_history"

    @property
    def initialize_effect(self) -> str:
        return f"{self.root}_initialize_state"

    @property
    def clamp_effect(self) -> str:
        return f"{self.root}_clamp_state"

    @property
    def scheduler_effect(self) -> str:
        return f"{self.root}_schedule_current_year_events"

    @property
    def hidden_ninety_id(self) -> str:
        return f"{self.namespace}.90"

    @property
    def monthly_driver(self) -> str:
        return (
            self.declared_monthly_driver
            or f"{self.tag}_corporate_history_monthly_outcomes"
        )


@dataclass
class BlockDef:
    name: str
    file: str
    line: int
    body: str


@dataclass
class EventDef:
    event_id: str
    file: str
    line: int
    body: str
    hidden: bool
    options: List[BlockDef] = field(default_factory=list)
    immediates: List[BlockDef] = field(default_factory=list)


@dataclass
class IdeaDef:
    idea_id: str
    file: str
    line: int
    body: str


@dataclass
class CallSite:
    target: str
    file: str
    line: int
    kind: str
    owner: str

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.owner}"


class Validator(BaseValidator):
    TITLE = TITLE
    STAGED_EXTENSIONS = [".txt", ".json", ".yml"]

    def __init__(self, mod_path: str, **kwargs):
        super().__init__(mod_path, **kwargs)
        self._root = Path(self.mod_path)
        self._manifest_path = self._root / "tools" / "corporate_history_contract.json"
        self._manifest_payload: Dict[str, object] = {}
        self._effect_call_parents_cache: Optional[Dict[str, Set[str]]] = None
        self._effect_call_children_cache: Optional[Dict[str, List[str]]] = None
        self._on_action_texts_cache: Optional[List[Tuple[str, str]]] = None

    def run_validations(self):
        self._log_section("loading manifest")
        chains = self._load_manifest()
        if not chains:
            return
        chain_by_namespace = {chain.namespace: chain for chain in chains}
        chain_by_root = {chain.root: chain for chain in chains}

        self._log_section("indexing corporate history")
        effect_defs = self._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
        self._effect_call_parents_cache = self._effect_call_parents(effect_defs)
        self._effect_call_children_cache = self._effect_call_children(effect_defs)
        event_defs = self._load_events()
        idea_defs = self._load_idea_definitions(chains, event_defs)
        core_namespaces = self._discover_core_namespaces(
            effect_defs.get("corporate_history_on_startup", []),
            effect_defs,
        )
        call_sites = self._load_event_call_sites(
            event_defs, effect_defs, core_namespaces
        )
        mode_defs = self._load_top_level_blocks(
            [
                "common/game_rules/00_game_rules.txt",
                "common/scripted_triggers/MD_corporate_history_triggers.txt",
            ]
        )

        self._log_section("mode contract")
        self._report(
            self._validate_mode_contract(mode_defs),
            "Corporate-history game-rule modes are exact",
            "Corporate-history game-rule mode issues:",
            category="Corporate-history mode contract",
        )

        self._log_section("manifest coverage")
        self._report(
            self._validate_manifest_coverage(
                chains, core_namespaces, chain_by_namespace
            ),
            "Corporate-history manifest covers current namespaces",
            "Corporate-history manifest coverage issues:",
            category="Corporate-history manifest",
        )
        self._report(
            self._validate_lifecycle_metadata(
                chains, effect_defs, event_defs, call_sites
            ),
            "Corporate-history lifecycle metadata matches scripted behavior",
            "Corporate-history lifecycle metadata issues:",
            category="Corporate-history manifest",
        )

        self._log_section("event reachability")
        self._report(
            self._validate_event_reachability(
                chains, event_defs, call_sites, effect_defs
            ),
            "Corporate-history event reachability is intact",
            "Corporate-history event reachability issues:",
            category="Corporate-history event reachability",
        )

        self._log_section("OEM startup architecture")
        self._report(
            self._validate_oem_startup_architecture(
                effect_defs, event_defs, call_sites
            ),
            "OEM startup bootstrap and USA 2000 schedule are intact",
            "OEM startup architecture issues:",
            category="OEM startup architecture",
        )

        self._log_section("dispatcher integrity")
        self._report(
            self._validate_dispatchers(chains, effect_defs, event_defs, call_sites),
            "Corporate-history dispatchers are intact",
            "Corporate-history dispatcher issues:",
            category="Corporate-history dispatcher integrity",
        )

        self._log_section("tier-1 contract")
        self._report(
            self._validate_tier_one_contract(
                chains, effect_defs, event_defs, idea_defs
            ),
            "Tier-1 chains satisfy the framework contract",
            "Tier-1 corporate-history contract issues:",
            category="Corporate-history Tier-1 contract",
        )

        self._log_section("clamp coverage")
        self._report(
            self._validate_clamp_coverage(chains, event_defs, effect_defs),
            "Bounded variables clamp correctly",
            "Corporate-history clamp coverage issues:",
            category="Corporate-history clamp coverage",
        )

        self._log_section("reconstruction safety")
        self._report(
            self._validate_reconstruction_safety(chains, effect_defs, event_defs),
            "Reconstruction effects are safe",
            "Corporate-history reconstruction issues:",
            category="Corporate-history reconstruction safety",
        )

        self._log_section("completion markers")
        self._report(
            self._validate_completion_markers(chains, effect_defs),
            "Reconstruction-complete markers have valid ownership",
            "Corporate-history completion-marker issues:",
            category="Corporate-history completion markers",
        )

        self._log_section("cross-chain ownership")
        self._report(
            self._validate_cross_chain_ownership(
                chains, chain_by_root, event_defs, effect_defs
            ),
            "Cross-chain ownership stays within the declared contract",
            "Corporate-history cross-chain ownership issues:",
            category="Corporate-history cross-chain ownership",
        )

        self._log_section("localisation contract")
        self._report(
            self._validate_localisation_contract(chains, event_defs),
            "Corporate-history English localisation is complete",
            "Corporate-history English localisation issues:",
            category="Corporate-history localisation contract",
        )

        self._log_section("economic bridge")
        self._report(
            self._validate_economic_bridge(chains, event_defs, effect_defs),
            "Corporate-history economic bridge is coherent",
            "Corporate-history economic bridge issues:",
            category="Corporate-history economic bridge",
        )

        self._log_section("real-options economic layer")
        self._report(
            self._validate_economic_layers(effect_defs, chains),
            "Corporate-history real-options economic layers are coherent",
            "Corporate-history real-options economic-layer issues:",
            category="Corporate-history real-options economic layer",
        )

        self._log_section("shared systems")
        self._report(
            self._validate_shared_systems(effect_defs, event_defs),
            "Shared-system contracts are coherent",
            "Shared-system contract issues:",
            category="Shared-system contract",
        )

    def _load_manifest(self) -> List[ChainConfig]:
        if not self._manifest_path.exists():
            self.add_error(
                "Corporate-history manifest",
                f"Missing manifest: {self._manifest_path.relative_to(self._root)}",
            )
            return []
        try:
            payload = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.add_error(
                "Corporate-history manifest",
                f"Failed to load {self._manifest_path.relative_to(self._root)}: {exc}",
            )
            return []

        self._manifest_payload = payload

        raw_chains = payload.get("chains")
        if not isinstance(raw_chains, list) or not raw_chains:
            self.add_error(
                "Corporate-history manifest",
                "Manifest requires a non-empty chains list",
            )
            return []

        contract_version = int(payload.get("schema_version", 1))
        required_v2 = (
            "full_start_strategies",
            "outcomes_only_strategy",
            "monthly_driver",
            "terminal_marker",
            "terminal_date",
            "outcome_ideas",
            "expected_callers",
            "dependency_order",
            "localisation_prefixes",
            "effect_preview_policy",
            "bridge_refresh_policy",
        )
        chains = []
        for index, raw in enumerate(raw_chains):
            if not isinstance(raw, dict):
                self.add_error(
                    "Corporate-history manifest",
                    f"chains[{index}] must be an object",
                )
                continue
            missing = [field for field in required_v2 if field not in raw]
            if contract_version >= 2 and missing:
                self.add_error(
                    "Corporate-history manifest",
                    f"chains[{index}] is missing required fields: {', '.join(missing)}",
                )
                continue
            try:
                bounds = {
                    name: Bound(Decimal(str(cfg["min"])), Decimal(str(cfg["max"])))
                    for name, cfg in raw.get("variables", {}).items()
                }
                expected_callers = {
                    event_id: tuple(callers)
                    for event_id, callers in raw.get("expected_callers", {}).items()
                }
                auxiliary_lifecycles = tuple(
                    AuxiliaryLifecycleConfig(
                        root=str(auxiliary["root"]),
                        tag=str(auxiliary["tag"]),
                        reconstruction_effect=str(auxiliary["reconstruction_effect"]),
                        scheduler_effect=str(auxiliary["scheduler_effect"]),
                        monthly_driver=str(auxiliary["monthly_driver"]),
                        terminal_marker=str(auxiliary["terminal_marker"]),
                        terminal_date=str(auxiliary["terminal_date"]),
                        expected_yearly_callers={
                            str(event_id): str(caller)
                            for event_id, caller in auxiliary[
                                "expected_yearly_callers"
                            ].items()
                        },
                    )
                    for auxiliary in raw.get("auxiliary_lifecycles", [])
                )
                chain = ChainConfig(
                    name=raw["name"],
                    tag=raw["tag"],
                    namespace=raw["namespace"],
                    root=raw["root"],
                    tier=int(raw["tier"]),
                    owned_prefixes=tuple(raw.get("owned_prefixes", [raw["root"]])),
                    variables=bounds,
                    outcome_idea_prefixes=tuple(raw.get("outcome_idea_prefixes", [])),
                    requires_current_year_scheduler=bool(
                        raw.get("requires_current_year_scheduler", False)
                    ),
                    allow_yearly_scheduler_duplicates=bool(
                        raw.get("allow_yearly_scheduler_duplicates", False)
                    ),
                    callerless_anchors=set(raw.get("callerless_anchors", [])),
                    allowed_multiple_callers=set(
                        raw.get("allowed_multiple_callers", [])
                    ),
                    allowed_reads=tuple(raw.get("allowed_reads", [])),
                    allowed_writes=tuple(raw.get("allowed_writes", [])),
                    full_start_strategies=tuple(raw.get("full_start_strategies", [])),
                    outcomes_only_strategy=str(raw.get("outcomes_only_strategy", "")),
                    declared_monthly_driver=str(raw.get("monthly_driver", "")),
                    terminal_marker=str(raw.get("terminal_marker", "")),
                    terminal_date=str(raw.get("terminal_date", "")),
                    outcome_ideas=tuple(raw.get("outcome_ideas", [])),
                    expected_callers=expected_callers,
                    dependency_order=tuple(raw.get("dependency_order", [])),
                    localisation_prefixes=tuple(raw.get("localisation_prefixes", [])),
                    effect_preview_policy=str(
                        raw.get("effect_preview_policy", "engine_or_explicit")
                    ),
                    tooltip_exemptions={
                        str(option): str(reason)
                        for option, reason in raw.get("tooltip_exemptions", {}).items()
                    },
                    bridge_refresh_policy=str(raw.get("bridge_refresh_policy", "none")),
                    ai_bankruptcy_exceptions=tuple(
                        raw.get("ai_bankruptcy_exceptions", [])
                    ),
                    auxiliary_completion_markers=tuple(
                        raw.get("auxiliary_completion_markers", [])
                    ),
                    auxiliary_lifecycles=auxiliary_lifecycles,
                    allow_multiple_completion_producers=bool(
                        raw.get("allow_multiple_completion_producers", False)
                    ),
                )
            except (KeyError, TypeError, ValueError) as exc:
                self.add_error(
                    "Corporate-history manifest",
                    f"chains[{index}] is invalid: {exc}",
                )
                continue
            if chain.outcomes_only_strategy not in ("", "reconstruction", "suppressed"):
                self.add_error(
                    "Corporate-history manifest",
                    f"{chain.name} has invalid outcomes_only_strategy {chain.outcomes_only_strategy}",
                )
                continue
            if chain.requires_current_year_scheduler != (
                "current_year_scheduler" in chain.full_start_strategies
            ):
                self.add_error(
                    "Corporate-history manifest",
                    f"{chain.name} requires_current_year_scheduler disagrees with full_start_strategies",
                )
            chains.append(chain)
        return chains

    def _validate_shared_systems(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        schema_version = int(self._manifest_payload.get("schema_version", 1))
        raw_systems = self._manifest_payload.get("shared_systems")
        if raw_systems is None and schema_version < 4:
            return findings
        if not isinstance(raw_systems, list) or not raw_systems:
            return [
                (
                    "Schema v4 requires a non-empty shared_systems list",
                    "tools/corporate_history_contract.json",
                    1,
                )
            ]

        required_fields = (
            "name",
            "root",
            "namespace",
            "game_rule",
            "dispatcher_host",
            "participant_array",
            "event_ids",
            "variables",
            "initial_state",
            "support_model_codes",
            "support_model_precedence",
            "reconstruction_baseline",
            "historical_routes",
            "scripted_effects",
            "files",
            "lifecycle_markers",
            "storage_lifecycle_markers",
            "adoption_ideas",
            "support_ideas",
            "persistent_idea_modifiers",
            "owned_timed_ideas",
            "timed_idea_modifiers",
            "programs",
            "excluded_generic_idea_tags",
            "reconstruction_effect",
            "cleanup_effect",
            "refresh_ideas_effect",
            "allowed_native_reads",
            "native_write_prefixes",
            "localisation_keys",
            "usa_bridge_effect",
        )
        required_files = (
            "rule",
            "trigger",
            "effect",
            "on_action",
            "event",
            "idea",
            "decision",
            "category",
            "bridge",
            "ibm_event",
        )

        for index, raw_system in enumerate(raw_systems):
            if not isinstance(raw_system, dict):
                findings.append(
                    (
                        f"shared_systems[{index}] must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            missing = [field for field in required_fields if field not in raw_system]
            if missing:
                findings.append(
                    (
                        f"shared_systems[{index}] is missing required fields: {', '.join(missing)}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            name = str(raw_system["name"])
            root = str(raw_system["root"])
            namespace = str(raw_system["namespace"])
            files = raw_system["files"]
            if not isinstance(files, dict):
                findings.append(
                    (
                        f"{name} files must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            missing_files = [field for field in required_files if field not in files]
            if missing_files:
                findings.append(
                    (
                        f"{name} files is missing: {', '.join(missing_files)}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            declared_text: Dict[str, str] = {}
            for role, relative in files.items():
                if role in ("localisation", "integration"):
                    continue
                path = self._root / str(relative)
                if not path.is_file():
                    findings.append(
                        (f"{name} missing {role} file {relative}", str(relative), 1)
                    )
                    continue
                try:
                    declared_text[role] = path.read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError as exc:
                    findings.append(
                        (
                            f"{name} cannot read {role} file {relative}: {exc}",
                            str(relative),
                            1,
                        )
                    )

            game_rule = raw_system["game_rule"]
            if not isinstance(game_rule, dict):
                findings.append(
                    (
                        f"{name} game_rule must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                rule_id = str(game_rule.get("id", ""))
                options = game_rule.get("options")
                default = str(game_rule.get("default", ""))
                mode_defs = self._load_top_level_blocks(
                    [str(files["rule"]), str(files["trigger"])]
                )
                rule_defs = mode_defs.get(rule_id, [])
                if len(rule_defs) != 1:
                    findings.append(
                        (
                            f"{name} requires exactly one {rule_id}; found {len(rule_defs)}",
                            str(files["rule"]),
                            rule_defs[0].line if rule_defs else 1,
                        )
                    )
                elif options != ["full", "outcomes_only", "off"] or default != "full":
                    findings.append(
                        (
                            f"{name} game rule must declare Full, Outcomes Only, and Off with Full default",
                            str(files["rule"]),
                            rule_defs[0].line,
                        )
                    )
                elif not all(
                    re.search(rf"\bname\s*=\s*{re.escape(option)}\b", rule_defs[0].body)
                    for option in options
                ):
                    findings.append(
                        (
                            f"{name} game-rule script does not contain all declared options",
                            rule_defs[0].file,
                            rule_defs[0].line,
                        )
                    )
                trigger_names = (
                    f"{root}_full_enabled",
                    f"{root}_outcomes_only_enabled",
                    f"{root}_enabled",
                )
                for trigger_name in trigger_names:
                    definitions = mode_defs.get(trigger_name, [])
                    if len(definitions) != 1:
                        findings.append(
                            (
                                f"{name} requires exactly one {trigger_name}; found {len(definitions)}",
                                str(files["trigger"]),
                                definitions[0].line if definitions else 1,
                            )
                        )

            expected_variable_bounds = {
                f"{root}_base_deployment": (0, 10),
                f"{root}_base_stewardship": (0, 10),
                f"{root}_base_assurance": (0, 10),
                f"{root}_adapter_deployment": (-2, 2),
                f"{root}_adapter_stewardship": (-2, 2),
                f"{root}_adapter_assurance": (-2, 2),
                f"{root}_effective_deployment": (0, 10),
                f"{root}_effective_stewardship": (0, 10),
                f"{root}_effective_assurance": (0, 10),
                f"{root}_base_support_model": (0, 3),
                f"{root}_adapter_support_model": (0, 3),
                f"{root}_effective_support_model": (0, 3),
                f"{root}_milestone_stage": (0, 5),
            }
            raw_variables = raw_system["variables"]
            normalized_bounds: Dict[str, Tuple[Decimal, Decimal]] = {}
            if isinstance(raw_variables, dict):
                for variable, bounds in raw_variables.items():
                    if (
                        not isinstance(bounds, dict)
                        or "min" not in bounds
                        or "max" not in bounds
                    ):
                        continue
                    try:
                        normalized_bounds[str(variable)] = (
                            Decimal(str(bounds["min"])),
                            Decimal(str(bounds["max"])),
                        )
                    except (ValueError, TypeError):
                        pass
            expected_normalized = {
                variable: (Decimal(str(bounds[0])), Decimal(str(bounds[1])))
                for variable, bounds in expected_variable_bounds.items()
            }
            if normalized_bounds != expected_normalized:
                findings.append(
                    (
                        f"{name} must declare the exact bounded base, adapter, effective, support, and milestone variables",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            expected_initial_state = {
                "deployment": 2,
                "stewardship": 3,
                "assurance": 3,
                "support_model": 0,
                "milestone_stage": 0,
            }
            if raw_system["initial_state"] != expected_initial_state:
                findings.append(
                    (
                        f"{name} must declare the approved 2/3/3 Mixed initial state",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            if raw_system["support_model_codes"] != {
                "mixed": 0,
                "upstream": 1,
                "enterprise": 2,
                "national": 3,
            } or raw_system["support_model_precedence"] != (
                "non_mixed_base_else_adapter"
            ):
                findings.append(
                    (
                        f"{name} must declare support codes 0..3 and base-first precedence",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            expected_baseline = [
                {
                    "stage": stage,
                    "deployment": deployment,
                    "stewardship": stewardship,
                    "assurance": assurance,
                    "support_model": 0,
                }
                for stage, deployment, stewardship, assurance in (
                    (0, 2, 3, 3),
                    (1, 3, 3, 3),
                    (2, 4, 3, 3),
                    (3, 5, 3, 4),
                    (4, 6, 3, 4),
                    (5, 7, 3, 5),
                )
            ]
            if raw_system["reconstruction_baseline"] != expected_baseline:
                findings.append(
                    (
                        f"{name} must declare the approved neutral reconstruction baseline",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            expected_historical_routes = {
                "BRA": "upstream",
                "CHI": "national",
                "ENG": "upstream",
                "FRA": "national",
                "GER": "upstream",
                "RAJ": "national",
                "SOV": "national",
                "USA": "enterprise",
            }
            if raw_system["historical_routes"] != expected_historical_routes:
                findings.append(
                    (
                        f"{name} must declare the approved national historical routes",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            effect_text = declared_text.get("effect", "")
            effect_lookup = {
                effect_name: definitions[0]
                for effect_name, definitions in effect_defs.items()
                if len(definitions) == 1
            }

            def reachable_effects(effect_name: str) -> Dict[str, BlockDef]:
                reachable: Dict[str, BlockDef] = {}
                pending = (
                    [effect_lookup[effect_name]] if effect_name in effect_lookup else []
                )
                while pending:
                    effect = pending.pop()
                    if effect.name in reachable:
                        continue
                    reachable[effect.name] = effect
                    for call in _EFFECT_YES_RE.finditer(effect.body):
                        target = call.group(1)
                        if (
                            target.startswith(root)
                            and target in effect_lookup
                            and target not in reachable
                        ):
                            pending.append(effect_lookup[target])
                return reachable

            clamp_bounds = {
                match.group(1): (Decimal(match.group(2)), Decimal(match.group(3)))
                for match in _CLAMP_VAR_RE.finditer(strip_comments(effect_text))
            }
            for variable, bounds in expected_normalized.items():
                if clamp_bounds.get(variable) != bounds:
                    findings.append(
                        (
                            f"{name} must clamp {variable} to {bounds[0]}..{bounds[1]}",
                            str(files["effect"]),
                            1,
                        )
                    )

            scripted_effects = raw_system["scripted_effects"]
            if not isinstance(scripted_effects, list) or not scripted_effects:
                findings.append(
                    (
                        f"{name} scripted_effects must be a non-empty list",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                for effect_name in scripted_effects:
                    definitions = effect_defs.get(str(effect_name), [])
                    if len(definitions) != 1:
                        findings.append(
                            (
                                f"{name} requires exactly one {effect_name}; found {len(definitions)}",
                                str(files["effect"]),
                                definitions[0].line if definitions else 1,
                            )
                        )

            event_ids = raw_system["event_ids"]
            if event_ids != [f"{namespace}.{number}" for number in range(1, 6)]:
                findings.append(
                    (
                        f"{name} must reserve exactly {namespace}.1 through {namespace}.5",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                event_ids = []
            for event_id in event_ids:
                event = event_defs.get(str(event_id))
                if event is None:
                    findings.append(
                        (f"{name} missing event {event_id}", str(files["event"]), 1)
                    )
                    continue
                if event.file.replace("\\", "/") != str(files["event"]).replace(
                    "\\", "/"
                ):
                    findings.append(
                        (
                            f"{event_id} is outside its declared event file",
                            event.file,
                            event.line,
                        )
                    )
                if "is_triggered_only = yes" not in event.body:
                    findings.append(
                        (f"{event_id} must be triggered-only", event.file, event.line)
                    )
                if not event.options:
                    findings.append(
                        (
                            f"{event_id} requires at least one option",
                            event.file,
                            event.line,
                        )
                    )
            event_text = declared_text.get("event", "")
            if re.search(r"\bnews_event\s*=", event_text):
                findings.append(
                    (
                        f"{name} must not define global news events",
                        str(files["event"]),
                        1,
                    )
                )
            undeclared_events = {
                event_id
                for event_id in event_defs
                if event_id.startswith(f"{namespace}.")
                and event_id not in set(event_ids)
            }
            if undeclared_events:
                findings.append(
                    (
                        f"{name} has undeclared events: {', '.join(sorted(undeclared_events))}",
                        str(files["event"]),
                        1,
                    )
                )

            system_text = "\n".join(
                declared_text.get(role, "") for role in ("effect", "on_action", "event")
            )
            for event_id, markers in raw_system["lifecycle_markers"].items():
                if (
                    event_id not in event_ids
                    or not isinstance(markers, list)
                    or len(markers) != 3
                ):
                    findings.append(
                        (
                            f"{name} lifecycle declaration for {event_id} must list expected, pending, and resolved markers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                for marker in markers:
                    if str(marker) not in system_text:
                        findings.append(
                            (
                                f"{event_id} never uses lifecycle marker {marker}",
                                str(files["effect"]),
                                1,
                            )
                        )

            if re.search(r"\b(?:every_country|random_country)\s*=", system_text):
                findings.append(
                    (
                        f"{name} may not use every_country or random_country",
                        str(files["effect"]),
                        1,
                    )
                )
            participant_array = str(raw_system["participant_array"])
            if (
                participant_array not in effect_text
                or "is_in_array" not in effect_text
                or "add_to_array" not in effect_text
                or "remove_from_array" not in effect_text
            ):
                findings.append(
                    (
                        f"{name} participant registry must deduplicate registration and support removal",
                        str(files["effect"]),
                        1,
                    )
                )
            on_action_text = declared_text.get("on_action", "")
            dispatcher_host = str(raw_system["dispatcher_host"])
            if (
                f"{dispatcher_host} =" not in on_action_text
                or "on_monthly" not in on_action_text
            ):
                findings.append(
                    (
                        f"{name} must use {dispatcher_host} as its monthly dispatcher host",
                        str(files["on_action"]),
                        1,
                    )
                )
            if re.search(
                rf"\boriginal_tag\s*=\s*{re.escape(dispatcher_host)}\b", system_text
            ):
                findings.append(
                    (
                        f"{dispatcher_host} may dispatch {name} but may not own gameplay state",
                        str(files["effect"]),
                        1,
                    )
                )

            reconstruction_name = str(raw_system["reconstruction_effect"])
            reconstruction_defs = effect_defs.get(reconstruction_name, [])
            if len(reconstruction_defs) == 1:
                forbidden_reconstruction = (
                    "add_political_power",
                    "modify_treasury_effect",
                    "add_tech_bonus",
                    "add_timed_idea",
                    "add_stability",
                    "add_war_support",
                    "add_building_construction",
                )
                for effect in reachable_effects(reconstruction_name).values():
                    for token in forbidden_reconstruction:
                        if re.search(rf"\b{token}\b", effect.body):
                            findings.append(
                                (
                                    f"{reconstruction_name} transitively contains forbidden side effect {token} through {effect.name}",
                                    effect.file,
                                    effect.line,
                                )
                            )

            adoption_ideas = raw_system["adoption_ideas"]
            support_ideas = raw_system["support_ideas"]
            idea_ids = (
                adoption_ideas + support_ideas
                if isinstance(adoption_ideas, list) and isinstance(support_ideas, list)
                else []
            )
            idea_text = declared_text.get("idea", "")
            owned_timed_ideas = raw_system["owned_timed_ideas"]
            if not isinstance(owned_timed_ideas, list):
                owned_timed_ideas = []
                findings.append(
                    (
                        f"{name} owned_timed_ideas must be a list",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            all_owned_ideas = [*idea_ids, *owned_timed_ideas]
            for idea_id in all_owned_ideas:
                if (
                    len(
                        re.findall(
                            rf"(?m)^\s*{re.escape(str(idea_id))}\s*=\s*\{{", idea_text
                        )
                    )
                    != 1
                ):
                    findings.append(
                        (f"{name} missing idea {idea_id}", str(files["idea"]), 1)
                    )

            def normalize_modifier_contract(
                payload: object,
            ) -> Dict[str, Dict[str, Decimal]]:
                normalized: Dict[str, Dict[str, Decimal]] = {}
                if not isinstance(payload, dict):
                    return normalized
                for idea_id, modifiers in payload.items():
                    if not isinstance(modifiers, dict):
                        continue
                    try:
                        normalized[str(idea_id)] = {
                            str(modifier): Decimal(str(value))
                            for modifier, value in modifiers.items()
                        }
                    except (ValueError, TypeError):
                        continue
                return normalized

            expected_persistent_modifiers = {
                f"{root}_experimental_adoption": {},
                f"{root}_institutional_adoption": {
                    "research_speed_factor": Decimal("0.005"),
                    "offices_productivity": Decimal("0.005"),
                },
                f"{root}_infrastructure_standard": {
                    "research_speed_factor": Decimal("0.005"),
                    "country_productivity_growth_modifier": Decimal("0.005"),
                    "offices_productivity": Decimal("0.01"),
                    "cyber_defense_rating_modifier": Decimal("1"),
                },
                f"{root}_broad_economic_adoption": {
                    "research_speed_factor": Decimal("0.01"),
                    "country_productivity_growth_modifier": Decimal("0.01"),
                    "offices_productivity": Decimal("0.02"),
                    "corporate_tax_income_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_mixed_linux_estate": {
                    "research_speed_factor": Decimal("-0.01"),
                    "cyber_defense_rating_modifier": Decimal("-1"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_upstream_partnership": {
                    "research_speed_factor": Decimal("0.01"),
                    "receiving_investment_cost_modifier": Decimal("-0.025"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_enterprise_distribution": {
                    "offices_productivity": Decimal("0.01"),
                    "corporate_tax_income_multiplier_modifier": Decimal("0.01"),
                    "internal_investments_money_cost_modifier": Decimal("0.025"),
                },
                f"{root}_national_baseline": {
                    "cyber_defense_rating_modifier": Decimal("2"),
                    "research_speed_factor": Decimal("-0.005"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.02"),
                },
            }
            persistent_modifiers = normalize_modifier_contract(
                raw_system["persistent_idea_modifiers"]
            )
            if persistent_modifiers != expected_persistent_modifiers:
                findings.append(
                    (
                        f"{name} must declare the approved persistent economic modifier matrix",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            expected_timed_modifiers = {
                f"{root}_shared_updates_program": {
                    "research_speed_factor": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_national_signing_program": {
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.02")
                },
                f"{root}_upstream_maintenance_program": {
                    "research_speed_factor": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_enterprise_support_program": {
                    "country_productivity_growth_modifier": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("-0.01"),
                },
                f"{root}_lifecycle_hardening_program": {
                    "cyber_defense_rating_modifier": Decimal("2"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.01"),
                },
                f"{root}_public_procurement_program": {
                    "research_speed_factor": Decimal("0.01"),
                    "country_productivity_growth_modifier": Decimal("0.01"),
                    "bureaucracy_cost_multiplier_modifier": Decimal("0.02"),
                },
            }
            timed_modifiers = normalize_modifier_contract(
                raw_system["timed_idea_modifiers"]
            )
            if timed_modifiers != expected_timed_modifiers:
                findings.append(
                    (
                        f"{name} must declare the approved timed economic modifier matrix",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            declared_modifier_contract = {
                **persistent_modifiers,
                **timed_modifiers,
            }
            for idea_id, expected_modifiers in declared_modifier_contract.items():
                match = re.search(rf"(?m)^\s*{re.escape(idea_id)}\s*=\s*\{{", idea_text)
                if match is None:
                    continue
                idea_body, _ = extract_block_from_text(idea_text, match.end() - 1)
                modifier_match = re.search(r"\bmodifier\s*=\s*\{", idea_body)
                modifier_body = ""
                if modifier_match is not None:
                    modifier_body, _ = extract_block_from_text(
                        idea_body, modifier_match.end() - 1
                    )
                actual_modifiers = {
                    modifier: Decimal(value)
                    for modifier, value in re.findall(
                        r"(?m)^\s*([a-z][a-z0-9_]*)\s*=\s*"
                        r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*$",
                        strip_comments(modifier_body),
                    )
                }
                if actual_modifiers != expected_modifiers:
                    findings.append(
                        (
                            f"{idea_id} modifiers do not match the shared-system contract",
                            str(files["idea"]),
                            1,
                        )
                    )

            expected_programs = {
                f"{root}_fund_upstream_maintenance": {
                    "political_power": 25,
                    "gdp_fraction": 0.001,
                    "duration_days": 365,
                    "cooldown_days": 365,
                    "deployment": 0,
                    "stewardship": 1,
                    "assurance": 1,
                    "support_model": None,
                    "idea": f"{root}_upstream_maintenance_program",
                },
                f"{root}_contract_enterprise_support": {
                    "political_power": 25,
                    "gdp_fraction": 0.001,
                    "duration_days": 365,
                    "cooldown_days": 365,
                    "deployment": 1,
                    "stewardship": 0,
                    "assurance": 1,
                    "support_model": 2,
                    "idea": f"{root}_enterprise_support_program",
                },
                f"{root}_harden_lifecycle": {
                    "political_power": 35,
                    "gdp_fraction": 0.001,
                    "duration_days": 365,
                    "cooldown_days": 365,
                    "deployment": 0,
                    "stewardship": 0,
                    "assurance": 2,
                    "support_model": None,
                    "idea": f"{root}_lifecycle_hardening_program",
                },
                f"{root}_public_procurement": {
                    "political_power": 50,
                    "gdp_fraction": 0.002,
                    "duration_days": 730,
                    "cooldown_days": 365,
                    "deployment": 1,
                    "stewardship": 1,
                    "assurance": 1,
                    "support_model": None,
                    "idea": f"{root}_public_procurement_program",
                },
            }
            if raw_system["programs"] != expected_programs:
                findings.append(
                    (
                        f"{name} must declare the approved program costs, durations, and state changes",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )

            program_effects = {
                f"{root}_fund_upstream_maintenance": (
                    f"{root}_apply_upstream_maintenance_program"
                ),
                f"{root}_contract_enterprise_support": (
                    f"{root}_apply_enterprise_support_program"
                ),
                f"{root}_harden_lifecycle": (
                    f"{root}_apply_lifecycle_hardening_program"
                ),
                f"{root}_public_procurement": (
                    f"{root}_apply_public_procurement_program"
                ),
            }
            decision_text = declared_text.get("decision", "")
            trigger_text = declared_text.get("trigger", "")
            category_text = declared_text.get("category", "")
            if f"{root}_full_enabled = yes" not in category_text:
                findings.append(
                    (
                        f"{name} decision category must be visible only in Full mode",
                        str(files["category"]),
                        1,
                    )
                )
            for program_id, program in expected_programs.items():
                match = re.search(
                    rf"(?m)^\s*{re.escape(program_id)}\s*=\s*\{{", decision_text
                )
                if match is None:
                    findings.append(
                        (
                            f"{name} missing program {program_id}",
                            str(files["decision"]),
                            1,
                        )
                    )
                    continue
                decision_body, _ = extract_block_from_text(
                    decision_text, match.end() - 1
                )
                if not re.search(
                    rf"\bcost\s*=\s*{program['political_power']}\b", decision_body
                ) or not re.search(
                    rf"\bdays_remove\s*=\s*{program['duration_days']}\b",
                    decision_body,
                ):
                    findings.append(
                        (
                            f"{program_id} must use its declared PP cost and active duration",
                            str(files["decision"]),
                            1,
                        )
                    )
                if not _is_repeatable_decision(decision_body):
                    findings.append(
                        (
                            f"{program_id} must remain reusable after its declared cooldown",
                            str(files["decision"]),
                            1,
                        )
                    )
                for block_name in ("complete_effect", "remove_effect"):
                    block_match = re.search(rf"\b{block_name}\s*=\s*\{{", decision_body)
                    if block_match is None:
                        findings.append(
                            (
                                f"{program_id} is missing {block_name}",
                                str(files["decision"]),
                                1,
                            )
                        )
                        continue
                    block_body, _ = extract_block_from_text(
                        decision_body, block_match.end() - 1
                    )
                    if not re.match(r"\s*log\s*=", strip_comments(block_body)):
                        findings.append(
                            (
                                f"{program_id} {block_name} must log first",
                                str(files["decision"]),
                                1,
                            )
                        )
                    if block_name == "remove_effect" and not re.search(
                        rf"set_country_flag\s*=\s*\{{\s*flag\s*=\s*{root}_program_cooldown\s+days\s*=\s*{program['cooldown_days']}\b",
                        block_body,
                    ):
                        findings.append(
                            (
                                f"{program_id} must begin its declared cooldown when it ends",
                                str(files["decision"]),
                                1,
                            )
                        )
                if f"{root}_full_enabled = yes" not in decision_body:
                    findings.append(
                        (
                            f"{program_id} must be exposed only in Full mode",
                            str(files["decision"]),
                            1,
                        )
                    )
                if (
                    "has_active_mission = bankruptcy_incoming_collapse"
                    not in decision_body
                ):
                    findings.append(
                        (
                            f"{program_id} must block AI during bankruptcy collapse",
                            str(files["decision"]),
                            1,
                        )
                    )

                apply_name = program_effects[program_id]
                apply_defs = effect_defs.get(apply_name, [])
                if len(apply_defs) != 1:
                    findings.append(
                        (
                            f"{program_id} requires exactly one {apply_name}",
                            str(files["effect"]),
                            1,
                        )
                    )
                    continue
                apply_body = apply_defs[0].body
                gdp_suffix = "0_1" if program["gdp_fraction"] == 0.001 else "0_2"
                if f"{root}_pay_gdp_{gdp_suffix}_percent = yes" not in apply_body:
                    findings.append(
                        (
                            f"{apply_name} does not charge its declared GDP fraction",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                for axis in ("deployment", "stewardship", "assurance"):
                    delta = program[axis]
                    change = rf"add_to_variable\s*=\s*\{{\s*{root}_base_{axis}\s*=\s*{delta}\s*\}}"
                    if delta and not re.search(change, apply_body):
                        findings.append(
                            (
                                f"{apply_name} is missing {axis} {delta:+d}",
                                apply_defs[0].file,
                                apply_defs[0].line,
                            )
                        )
                support_model = program["support_model"]
                support_pattern = (
                    rf"set_variable\s*=\s*\{{\s*{root}_base_support_model\s*="
                )
                if support_model is None and re.search(support_pattern, apply_body):
                    findings.append(
                        (
                            f"{apply_name} may not change the support model",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                elif support_model is not None and not re.search(
                    support_pattern + rf"\s*{support_model}\s*\}}", apply_body
                ):
                    findings.append(
                        (
                            f"{apply_name} must set support model {support_model}",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                if not re.search(
                    rf"add_timed_idea\s*=\s*\{{\s*idea\s*=\s*{re.escape(str(program['idea']))}\s+days\s*=\s*{program['duration_days']}\s*\}}",
                    apply_body,
                ):
                    findings.append(
                        (
                            f"{apply_name} must apply its declared timed idea",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )
                if f"{root}_program_cooldown" in apply_body:
                    findings.append(
                        (
                            f"{apply_name} may not start cooldown before the program ends",
                            apply_defs[0].file,
                            apply_defs[0].line,
                        )
                    )

            if not all(
                str(program["idea"]) in trigger_text
                for program in expected_programs.values()
            ):
                findings.append(
                    (
                        f"{name} active-program trigger must cover all four program ideas",
                        str(files["trigger"]),
                        1,
                    )
                )
            procurement_match = re.search(
                rf"(?m)^\s*{root}_public_procurement\s*=\s*\{{", decision_text
            )
            if procurement_match is not None:
                procurement_body, _ = extract_block_from_text(
                    decision_text, procurement_match.end() - 1
                )
                if not re.search(
                    r"NOT\s*=\s*\{\s*original_tag\s*=\s*USA\s*\}",
                    procurement_body,
                ):
                    findings.append(
                        (
                            f"{root}_public_procurement must be hidden for USA",
                            str(files["decision"]),
                            1,
                        )
                    )
            refresh_name = str(raw_system["refresh_ideas_effect"])
            refresh_defs = effect_defs.get(refresh_name, [])
            if len(refresh_defs) == 1:
                refresh_body = refresh_defs[0].body
                refresh_owned_text = "\n".join(
                    effect.body for effect in reachable_effects(refresh_name).values()
                )
                missing_ideas = [
                    idea for idea in idea_ids if str(idea) not in refresh_owned_text
                ]
                if missing_ideas:
                    findings.append(
                        (
                            f"{refresh_name} does not own every declared idea: {', '.join(missing_ideas)}",
                            refresh_defs[0].file,
                            refresh_defs[0].line,
                        )
                    )
                if raw_system["excluded_generic_idea_tags"] != ["USA"] or not re.search(
                    r"NOT\s*=\s*\{\s*original_tag\s*=\s*USA\s*\}", refresh_body
                ):
                    findings.append(
                        (
                            f"{refresh_name} must exclude USA from both generic idea families",
                            refresh_defs[0].file,
                            refresh_defs[0].line,
                        )
                    )

            cleanup_name = str(raw_system["cleanup_effect"])
            cleanup_defs = effect_defs.get(cleanup_name, [])
            if len(cleanup_defs) == 1:
                cleanup_body = cleanup_defs[0].body
                cleanup_owned_text = "\n".join(
                    effect.body for effect in reachable_effects(cleanup_name).values()
                )
                cleanup_missing = [
                    idea
                    for idea in all_owned_ideas
                    if str(idea) not in cleanup_owned_text
                ]
                if cleanup_missing or participant_array not in cleanup_body:
                    findings.append(
                        (
                            f"{cleanup_name} must remove every owned idea and the participant entry",
                            cleanup_defs[0].file,
                            cleanup_defs[0].line,
                        )
                    )
                active_decisions_missing = [
                    program_id
                    for program_id in expected_programs
                    if not _removes_active_decision(cleanup_owned_text, program_id)
                ]
                if active_decisions_missing:
                    findings.append(
                        (
                            f"{cleanup_name} must cancel every active program decision: "
                            f"{', '.join(active_decisions_missing)}",
                            cleanup_defs[0].file,
                            cleanup_defs[0].line,
                        )
                    )

            prefixes = tuple(
                str(prefix) for prefix in raw_system["native_write_prefixes"]
            )
            allowed_reads = {str(token) for token in raw_system["allowed_native_reads"]}
            native_contract_text = strip_comments(
                "\n".join(
                    declared_text.get(role, "") for role in _NATIVE_CONTRACT_ROLES
                )
            )
            native_reads: Set[str] = set()
            for pattern in (
                re.compile(
                    r"\b(?:has_country_flag|has_idea|has_completed_focus)\s*=\s*"
                    + _SCRIPT_TOKEN_CAPTURE
                ),
                re.compile(
                    r"\bcheck_variable\s*=\s*\{\s*(?:var\s*=\s*)?"
                    + _SCRIPT_TOKEN_CAPTURE
                ),
            ):
                for token in pattern.findall(native_contract_text):
                    fragment = _native_token_fragment(token, prefixes)
                    if fragment:
                        native_reads.add(fragment)
            undeclared_reads = native_reads - allowed_reads
            if undeclared_reads:
                findings.append(
                    (
                        f"{name} has undeclared native reads: {', '.join(sorted(undeclared_reads))}",
                        str(files["effect"]),
                        1,
                    )
                )
            unused_reads = allowed_reads - native_reads
            if unused_reads:
                findings.append(
                    (
                        f"{name} declares unused native reads: {', '.join(sorted(unused_reads))}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            native_writes = _collect_native_write_tokens(native_contract_text, prefixes)
            if native_writes:
                findings.append(
                    (
                        f"{name} writes native-system state: {', '.join(sorted(native_writes))}",
                        str(files["effect"]),
                        1,
                    )
                )

            localisation_files = files.get("localisation")
            if not isinstance(localisation_files, list) or not localisation_files:
                findings.append(
                    (
                        f"{name} requires declared English localisation files",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                localisation_text = ""
                for relative in localisation_files:
                    path = self._root / str(relative)
                    if not path.is_file():
                        findings.append(
                            (
                                f"{name} missing localisation file {relative}",
                                str(relative),
                                1,
                            )
                        )
                        continue
                    raw_bytes = path.read_bytes()
                    if not raw_bytes.startswith(b"\xef\xbb\xbf"):
                        findings.append(
                            (f"{relative} must retain a UTF-8 BOM", str(relative), 1)
                        )
                    localisation_text += (
                        raw_bytes.decode("utf-8-sig", errors="replace") + "\n"
                    )
                for key in raw_system["localisation_keys"]:
                    if not re.search(
                        rf"(?m)^ {re.escape(str(key))}:\d*\s", localisation_text
                    ):
                        findings.append(
                            (
                                f"{name} missing localisation key {key}",
                                str(localisation_files[0]),
                                1,
                            )
                        )

            integration_files = files.get("integration")
            integration_text = ""
            if isinstance(integration_files, list):
                for relative in integration_files:
                    path = self._root / str(relative)
                    if path.is_file():
                        integration_text += (
                            path.read_text(encoding="utf-8-sig", errors="replace")
                            + "\n"
                        )
            for event_id, markers in raw_system["storage_lifecycle_markers"].items():
                if not isinstance(markers, list) or len(markers) != 3:
                    findings.append(
                        (
                            f"{name} storage lifecycle declaration for {event_id} must list expected, pending, and resolved markers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                for marker in markers:
                    if str(marker) not in integration_text:
                        findings.append(
                            (
                                f"{event_id} never uses lifecycle marker {marker}",
                                str(files["integration"][0]),
                                1,
                            )
                        )

            ibm_event_text = declared_text.get("ibm_event", "")
            added_ibm_events = sorted(
                number
                for number in (
                    int(value)
                    for value in re.findall(
                        r"\bid\s*=\s*USA_ibm_events\.(\d+)", ibm_event_text
                    )
                )
                if number > 50 and number != 90
            )
            if added_ibm_events:
                findings.append(
                    (
                        f"IBM story events may not extend beyond .50: {added_ibm_events}",
                        str(files["ibm_event"]),
                        1,
                    )
                )

            bridge_name = str(raw_system["usa_bridge_effect"])
            bridge_defs = effect_defs.get(bridge_name, [])
            if len(bridge_defs) != 1:
                findings.append(
                    (
                        f"{name} requires exactly one {bridge_name}; found {len(bridge_defs)}",
                        str(files["bridge"]),
                        bridge_defs[0].line if bridge_defs else 1,
                    )
                )
            else:
                bridge_body = bridge_defs[0].body
                required_base_reads = (
                    f"{root}_base_deployment",
                    f"{root}_base_stewardship",
                    f"{root}_base_assurance",
                    f"{root}_base_support_model",
                )
                if not all(token in bridge_body for token in required_base_reads):
                    findings.append(
                        (
                            f"{bridge_name} must read all four generic base-state inputs",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )
                if (
                    f"{root}_adapter_" in bridge_body
                    or f"{root}_effective_" in bridge_body
                ):
                    findings.append(
                        (
                            f"{bridge_name} may not read adapter or effective Linux state",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )
                contribution_changes = re.findall(
                    r"(?:add_to_temp_variable|subtract_from_temp_variable)\s*=\s*\{\s*"
                    r"USA_oem_contribution_[A-Za-z0-9_]+\s*=\s*"
                    r"(-?(?:\d+(?:\.\d*)?|\.\d+))\s*\}",
                    bridge_body,
                )
                if any(abs(float(value)) > 1 for value in contribution_changes):
                    findings.append(
                        (
                            f"{bridge_name} contributions must be limited to one point per axis",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )

        return findings

    def _validate_economic_layers(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        chains: Sequence[ChainConfig],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        schema_version = int(self._manifest_payload.get("schema_version", 1))
        raw_layers = self._manifest_payload.get("economic_layers")
        if raw_layers is None and schema_version < 3:
            return findings
        if not isinstance(raw_layers, list) or not raw_layers:
            return [
                (
                    "Schema v3 requires a non-empty economic_layers list",
                    "tools/corporate_history_contract.json",
                    1,
                )
            ]

        required_fields = (
            "name",
            "tag",
            "updater",
            "bridge",
            "effect_file",
            "dynamic_modifier_file",
            "decision_file",
            "idea_file",
            "scripted_localisation_file",
            "localisation_file",
            "initialized_flag",
            "variables",
            "source_variables",
            "cdf",
            "modifier_families",
            "policy_programs",
            "dashboard_variables",
            "scripted_localisation",
            "localisation_keys",
        )

        chain_variables = {variable for chain in chains for variable in chain.variables}
        for index, raw_layer in enumerate(raw_layers):
            if not isinstance(raw_layer, dict):
                findings.append(
                    (
                        f"economic_layers[{index}] must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue
            missing = [field for field in required_fields if field not in raw_layer]
            if missing:
                findings.append(
                    (
                        f"economic_layers[{index}] is missing required fields: {', '.join(missing)}",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                continue

            layer_name = str(raw_layer["name"])

            def read_layer_file(field: str) -> Tuple[str, str]:
                relative = str(raw_layer[field])
                path = self._root / relative
                try:
                    return relative, path.read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError:
                    findings.append(
                        (f"{layer_name} is missing {field} {relative}", relative, 1)
                    )
                    return relative, ""

            effect_file, effect_text_raw = read_layer_file("effect_file")
            dynamic_file, dynamic_text_raw = read_layer_file("dynamic_modifier_file")
            decision_file, decision_text_raw = read_layer_file("decision_file")
            idea_file, idea_text_raw = read_layer_file("idea_file")
            scripted_loc_file, scripted_loc_text_raw = read_layer_file(
                "scripted_localisation_file"
            )
            localisation_file, localisation_text = read_layer_file("localisation_file")
            effect_text = strip_comments(effect_text_raw)
            dynamic_text = strip_comments(dynamic_text_raw)
            decision_text = strip_comments(decision_text_raw)
            idea_text = strip_comments(idea_text_raw)
            scripted_loc_text = strip_comments(scripted_loc_text_raw)

            updater = str(raw_layer["updater"])
            bridge = str(raw_layer["bridge"])
            updater_defs = effect_defs.get(updater, [])
            if len(updater_defs) != 1:
                findings.append(
                    (
                        f"{layer_name} requires exactly one authoritative updater {updater}; found {len(updater_defs)}",
                        effect_file,
                        1,
                    )
                )
                updater_body = effect_text
            else:
                updater_body = updater_defs[0].body
                if updater_defs[0].file.replace("\\", "/") != effect_file.replace(
                    "\\", "/"
                ):
                    findings.append(
                        (
                            f"{updater} must be defined in {effect_file}",
                            updater_defs[0].file,
                            updater_defs[0].line,
                        )
                    )

            bridge_defs = effect_defs.get(bridge, [])
            if len(bridge_defs) != 1:
                findings.append(
                    (
                        f"{layer_name} bridge {bridge} must have exactly one definition",
                        effect_file,
                        1,
                    )
                )
            else:
                calls = len(
                    re.findall(
                        rf"\b{re.escape(updater)}\s*=\s*yes\b", bridge_defs[0].body
                    )
                )
                if calls != 1:
                    findings.append(
                        (
                            f"{bridge} must call {updater} exactly once; found {calls}",
                            bridge_defs[0].file,
                            bridge_defs[0].line,
                        )
                    )

            for token in ("ln", "log", "sqrt", "exp", "pow"):
                if re.search(rf"\b{token}\s*=", effect_text):
                    findings.append(
                        (
                            f"{layer_name} uses unsupported scripted math operator {token}",
                            effect_file,
                            1,
                        )
                    )
            for forbidden_gate in (
                "corporate_history_full_enabled",
                "corporate_history_outcomes_only_enabled",
            ):
                if forbidden_gate in updater_body:
                    findings.append(
                        (
                            f"{updater} must be mode-neutral and cannot read {forbidden_gate}",
                            effect_file,
                            1,
                        )
                    )
            for required_gate in (
                "corporate_history_enabled",
                "collapsed_nation",
                str(raw_layer["initialized_flag"]),
            ):
                if required_gate not in updater_body:
                    findings.append(
                        (
                            f"{updater} is missing required gate or cleanup symbol {required_gate}",
                            effect_file,
                            1,
                        )
                    )
            if "force_update_dynamic_modifier" in effect_text:
                findings.append(
                    (
                        f"{layer_name} must not force-update dynamic modifiers",
                        effect_file,
                        1,
                    )
                )

            daily_files = []
            for filepath in self._collect_text_files(["common/on_actions/**/*.txt"]):
                try:
                    on_action_text = Path(filepath).read_text(
                        encoding="utf-8-sig", errors="replace"
                    )
                except OSError:
                    continue
                if updater in strip_comments(on_action_text):
                    daily_files.append(self._relpath(filepath))
            for daily_file in daily_files:
                findings.append(
                    (
                        f"{updater} must be reached through the economic bridge, not an on-action",
                        daily_file,
                        1,
                    )
                )

            raw_variables = raw_layer["variables"]
            declared_variables: Set[str] = set()
            if not isinstance(raw_variables, dict) or not raw_variables:
                findings.append(
                    (
                        f"{layer_name} requires declared bounded variables",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                raw_variables = {}
            script_clamps = {
                match.group(1): (Decimal(match.group(2)), Decimal(match.group(3)))
                for match in _CLAMP_VAR_RE.finditer(effect_text)
            }
            for variable, raw_bound in raw_variables.items():
                declared_variables.add(str(variable))
                try:
                    expected = (
                        Decimal(str(raw_bound["min"])),
                        Decimal(str(raw_bound["max"])),
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    findings.append(
                        (
                            f"{layer_name} has invalid bounds for {variable}: {exc}",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if script_clamps.get(str(variable)) != expected:
                    findings.append(
                        (
                            f"{updater} must clamp {variable} to economic-layer bounds {expected[0]}..{expected[1]}",
                            effect_file,
                            1,
                        )
                    )
                if not re.search(
                    rf"\bclear_variable\s*=\s*{re.escape(str(variable))}\b",
                    updater_body,
                ):
                    findings.append(
                        (
                            f"{updater} Off cleanup must clear {variable}",
                            effect_file,
                            1,
                        )
                    )

            for match in _SET_VAR_RE.finditer(effect_text):
                variable = match.group(1)
                if variable in chain_variables:
                    findings.append(
                        (
                            f"{layer_name} writes company-owned variable {variable}",
                            effect_file,
                            self._line(effect_text, match.start()),
                        )
                    )
                elif (
                    variable.startswith("USA_oem_")
                    and variable not in declared_variables
                    and not variable.endswith("_display")
                ):
                    findings.append(
                        (
                            f"{layer_name} writes undeclared persistent variable {variable}",
                            effect_file,
                            self._line(effect_text, match.start()),
                        )
                    )

            for source_variable in raw_layer["source_variables"]:
                if not re.search(
                    rf"\b{re.escape(str(source_variable))}\b", updater_body
                ):
                    findings.append(
                        (
                            f"{updater} does not read declared source variable {source_variable}",
                            effect_file,
                            1,
                        )
                    )

            cdf = raw_layer["cdf"]
            if not isinstance(cdf, dict):
                findings.append(
                    (
                        f"{layer_name} CDF contract must be an object",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
            else:
                knots = cdf.get("knots", [])
                values = cdf.get("values", [])
                cdf_lists = isinstance(knots, list) and isinstance(values, list)
                cdf_numeric = cdf_lists and all(
                    _is_finite_number(value) for value in (*knots, *values)
                )
                if cdf_lists and not cdf_numeric:
                    findings.append(
                        (
                            f"{layer_name} CDF knots and values must contain only finite numbers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if not cdf_lists or (
                    cdf_numeric
                    and (
                        len(knots) != len(values)
                        or len(knots) < 2
                        or any(left >= right for left, right in zip(knots, knots[1:]))
                        or any(left >= right for left, right in zip(values, values[1:]))
                        or any(value < 0 or value > 1 for value in values)
                    )
                ):
                    findings.append(
                        (
                            f"{layer_name} CDF knots and values must be paired, monotonic, and bounded",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if cdf_numeric:
                    for value in values:
                        if str(value) not in effect_text:
                            findings.append(
                                (
                                    f"{layer_name} CDF script is missing contracted value {value}",
                                    effect_file,
                                    1,
                                )
                            )
                if not re.search(
                    r"clamp_temp_variable\s*=\s*\{\s*var\s*=\s*USA_oem_cdf_output\s+min\s*=\s*0\s+max\s*=\s*1",
                    effect_text,
                ):
                    findings.append(
                        (
                            f"{layer_name} CDF output must clamp to 0..1",
                            effect_file,
                            1,
                        )
                    )

            all_modifier_members: List[str] = []
            families = raw_layer["modifier_families"]
            if not isinstance(families, list) or not families:
                findings.append(
                    (
                        f"{layer_name} requires modifier families",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                families = []
            for family in families:
                if not isinstance(family, dict):
                    continue
                family_name = str(family.get("name", "unnamed"))
                members = family.get("members", [])
                thresholds = family.get("thresholds", [])
                score = str(family.get("score", ""))
                if isinstance(thresholds, list) and not all(
                    _is_finite_number(threshold) for threshold in thresholds
                ):
                    findings.append(
                        (
                            f"{layer_name} modifier family {family_name} thresholds must contain only finite numbers",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if (
                    not isinstance(members, list)
                    or not isinstance(thresholds, list)
                    or len(members) != len(thresholds) + 1
                    or any(
                        left >= right for left, right in zip(thresholds, thresholds[1:])
                    )
                ):
                    findings.append(
                        (
                            f"{layer_name} modifier family {family_name} has invalid members or thresholds",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                if score not in declared_variables:
                    findings.append(
                        (
                            f"{layer_name} modifier family {family_name} reads undeclared score {score}",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                for threshold in thresholds:
                    threshold_text = str(threshold)
                    if not re.search(
                        rf"check_variable\s*=\s*\{{\s*{re.escape(score)}\s*<\s*{re.escape(threshold_text)}\s*\}}",
                        updater_body,
                    ):
                        findings.append(
                            (
                                f"{layer_name} modifier family {family_name} is missing threshold {threshold_text} for {score}",
                                effect_file,
                                1,
                            )
                        )
                for member in members:
                    member = str(member)
                    all_modifier_members.append(member)
                    definitions = len(
                        re.findall(rf"(?m)^{re.escape(member)}\s*=\s*\{{", dynamic_text)
                    )
                    if definitions != 1:
                        findings.append(
                            (
                                f"Dynamic modifier {member} must be defined exactly once; found {definitions}",
                                dynamic_file,
                                1,
                            )
                        )
                    if not re.search(
                        rf"\badd_dynamic_modifier\s*=\s*\{{\s*modifier\s*=\s*{re.escape(member)}\b",
                        updater_body,
                    ):
                        findings.append(
                            (
                                f"{updater} never assigns dynamic modifier {member}",
                                effect_file,
                                1,
                            )
                        )
                    remove_count = len(
                        re.findall(
                            rf"\bremove_dynamic_modifier\s*=\s*\{{\s*modifier\s*=\s*{re.escape(member)}\b",
                            updater_body,
                        )
                    )
                    if remove_count < len(members) + 1:
                        findings.append(
                            (
                                f"{updater} must clear {member} in every {family_name} tier branch and Off cleanup",
                                effect_file,
                                1,
                            )
                        )
                    if not re.search(
                        rf"\bremove_dynamic_modifier\s*=\s*\{{\s*modifier\s*=\s*{re.escape(member)}\b",
                        updater_body,
                    ):
                        findings.append(
                            (
                                f"{updater} never clears dynamic modifier {member}",
                                effect_file,
                                1,
                            )
                        )

            programs = raw_layer["policy_programs"]
            if not isinstance(programs, list) or len(programs) != 4:
                findings.append(
                    (
                        f"{layer_name} requires exactly four policy programs",
                        "tools/corporate_history_contract.json",
                        1,
                    )
                )
                programs = []
            program_ideas: List[str] = []
            for program_index, program in enumerate(programs):
                if not isinstance(program, dict):
                    findings.append(
                        (
                            f"{layer_name} policy_programs[{program_index}] must be an object",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                    continue
                decision = str(program.get("decision", ""))
                idea = str(program.get("idea", ""))
                days = int(program.get("days", 0))
                cooldown_days = int(program.get("cooldown_days", 0))
                program_ideas.append(idea)
                decision_match = re.search(
                    rf"(?m)^\s*{re.escape(decision)}\s*=\s*\{{", decision_text
                )
                if decision_match is None:
                    findings.append(
                        (f"Missing policy decision {decision}", decision_file, 1)
                    )
                    continue
                decision_body, end = extract_block_from_text(
                    decision_text, decision_match.end() - 1
                )
                if end == -1:
                    findings.append(
                        (
                            f"Could not parse policy decision {decision}",
                            decision_file,
                            1,
                        )
                    )
                    continue
                available_match = re.search(r"\bavailable\s*=\s*\{", decision_body)
                available_body = ""
                if available_match is not None:
                    available_body, _ = extract_block_from_text(
                        decision_body, available_match.end() - 1
                    )
                timed_pattern = re.compile(
                    rf"\badd_timed_idea\s*=\s*\{{\s*idea\s*=\s*{re.escape(idea)}\s+days\s*=\s*{days}\s*\}}"
                )
                if len(timed_pattern.findall(decision_body)) != 1:
                    findings.append(
                        (
                            f"{decision} must add {idea} once for {days} days",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                cooldown_pattern = re.compile(
                    rf"\bdays_re_enable\s*=\s*{cooldown_days}\b"
                )
                if len(cooldown_pattern.findall(decision_body)) != 1:
                    findings.append(
                        (
                            f"{decision} must declare a {cooldown_days}-day cooldown",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                if not _is_repeatable_decision(decision_body):
                    findings.append(
                        (
                            f"{decision} must remain reusable after its declared cooldown",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                if str(program.get("refresh_policy")) != "block_while_active":
                    findings.append(
                        (
                            f"{decision} must declare block_while_active refresh policy",
                            "tools/corporate_history_contract.json",
                            1,
                        )
                    )
                if not re.search(
                    rf"NOT\s*=\s*\{{\s*has_idea\s*=\s*{re.escape(idea)}\s*\}}",
                    available_body,
                ):
                    findings.append(
                        (
                            f"{decision} must block while {idea} is active",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                if not re.search(
                    r"NOT\s*=\s*\{\s*has_country_flag\s*=\s*collapsed_nation\s*\}",
                    available_body,
                ):
                    findings.append(
                        (
                            f"{decision} must be unavailable after national collapse",
                            decision_file,
                            self._line(decision_text, decision_match.start()),
                        )
                    )
                definitions = len(
                    re.findall(rf"(?m)^\s*{re.escape(idea)}\s*=\s*\{{", idea_text)
                )
                if definitions != 1:
                    findings.append(
                        (
                            f"Policy idea {idea} must be defined exactly once; found {definitions}",
                            idea_file,
                            1,
                        )
                    )
                if not re.search(
                    rf"\bremove_ideas\s*=\s*\{{[^}}]*\b{re.escape(idea)}\b",
                    updater_body,
                    re.DOTALL,
                ):
                    findings.append(
                        (
                            f"{updater} Off/collapse cleanup must remove {idea}",
                            effect_file,
                            1,
                        )
                    )

            dashboard_text = decision_text + "\n" + localisation_text
            for variable in raw_layer["dashboard_variables"]:
                if str(variable) not in dashboard_text:
                    findings.append(
                        (
                            f"{layer_name} dashboard does not read authoritative output {variable}",
                            localisation_file,
                            1,
                        )
                    )
            for name in raw_layer["scripted_localisation"]:
                if not re.search(
                    rf"\bname\s*=\s*{re.escape(str(name))}\b", scripted_loc_text
                ):
                    findings.append(
                        (
                            f"Missing scripted localisation {name}",
                            scripted_loc_file,
                            1,
                        )
                    )

            localisation_keys = set(raw_layer["localisation_keys"])
            localisation_keys.update(program_ideas)
            localisation_keys.update(f"{idea}_desc" for idea in program_ideas)
            localisation_keys.update(all_modifier_members)
            localisation_keys.update(
                f"{member}_desc" for member in all_modifier_members
            )
            defined_loc_keys = {
                match.group(1)
                for line in localisation_text.splitlines()
                if (match := _LOC_KEY_PREFIX_RE.match(line))
            }
            for key in sorted(localisation_keys):
                if key not in defined_loc_keys:
                    findings.append(
                        (
                            f"Missing English real-options localisation key {key}",
                            localisation_file,
                            1,
                        )
                    )

            try:
                localisation_bytes = (self._root / localisation_file).read_bytes()
            except OSError:
                localisation_bytes = b""
            if localisation_bytes and not localisation_bytes.startswith(
                b"\xef\xbb\xbf"
            ):
                findings.append(
                    (
                        f"{localisation_file} must retain its UTF-8 BOM",
                        localisation_file,
                        1,
                    )
                )

        return findings

    def _validate_mode_contract(
        self, mode_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        rule_defs = mode_defs.get("rule_corporate_history", [])
        if len(rule_defs) != 1:
            return [
                (
                    f"rule_corporate_history requires exactly one definition; found {len(rule_defs)}",
                    "common/game_rules/00_game_rules.txt",
                    rule_defs[0].line if rule_defs else 0,
                )
            ]

        rule = rule_defs[0]
        options: List[Tuple[str, str]] = []
        for child, _start, _end, body in self._iter_direct_child_blocks(rule.body):
            if child not in ("default", "option"):
                continue
            name = re.search(r"\bname\s*=\s*([A-Za-z0-9_]+)", body)
            if name:
                options.append((child, name.group(1)))
        if options != [
            ("default", "full"),
            ("option", "outcomes_only"),
            ("option", "disabled"),
        ]:
            findings.append(
                (
                    "rule_corporate_history must define Full, Outcomes Only, and Disabled in that order",
                    rule.file,
                    rule.line,
                )
            )

        full = mode_defs.get("corporate_history_full_enabled", [])
        outcomes = mode_defs.get("corporate_history_outcomes_only_enabled", [])
        enabled = mode_defs.get("corporate_history_enabled", [])
        expected_rule_checks = {
            "corporate_history_full_enabled": ("outcomes_only", "disabled"),
            "corporate_history_outcomes_only_enabled": ("outcomes_only",),
        }
        for name, defs in (
            ("corporate_history_full_enabled", full),
            ("corporate_history_outcomes_only_enabled", outcomes),
            ("corporate_history_enabled", enabled),
        ):
            if len(defs) != 1:
                findings.append(
                    (
                        f"{name} requires exactly one definition; found {len(defs)}",
                        "common/scripted_triggers/MD_corporate_history_triggers.txt",
                        defs[0].line if defs else 0,
                    )
                )
        if len(full) == 1:
            body = full[0].body
            for option in expected_rule_checks["corporate_history_full_enabled"]:
                pattern = (
                    r"NOT\s*=\s*\{\s*has_game_rule\s*=\s*\{\s*rule\s*=\s*"
                    r"rule_corporate_history\s+option\s*=\s*" + option + r"\s*\}\s*\}"
                )
                if not re.search(pattern, body):
                    findings.append(
                        (
                            f"corporate_history_full_enabled does not exclude {option}",
                            full[0].file,
                            full[0].line,
                        )
                    )
        if len(outcomes) == 1 and not re.search(
            r"has_game_rule\s*=\s*\{\s*rule\s*=\s*rule_corporate_history\s+option\s*=\s*outcomes_only\s*\}",
            outcomes[0].body,
        ):
            findings.append(
                (
                    "corporate_history_outcomes_only_enabled does not select outcomes_only",
                    outcomes[0].file,
                    outcomes[0].line,
                )
            )
        if len(enabled) == 1 and not all(
            marker in enabled[0].body
            for marker in (
                "corporate_history_full_enabled = yes",
                "corporate_history_outcomes_only_enabled = yes",
            )
        ):
            findings.append(
                (
                    "corporate_history_enabled must combine Full and Outcomes Only",
                    enabled[0].file,
                    enabled[0].line,
                )
            )
        return findings

    def _collect_text_files(
        self, patterns: Sequence[str], ignore_staged: bool = True
    ) -> List[str]:
        seen: Set[str] = set()
        files: List[str] = []
        for pattern in patterns:
            for path in self._collect_files([pattern], ignore_staged=ignore_staged):
                if path not in seen:
                    seen.add(path)
                    files.append(path)
        return files

    def _load_top_level_blocks(
        self, patterns: Sequence[str]
    ) -> Dict[str, List[BlockDef]]:
        results: Dict[str, List[BlockDef]] = {}
        for filepath in self._collect_text_files(patterns):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            for match in _TOP_LEVEL_BLOCK_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                name = match.group(1)
                results.setdefault(name, []).append(
                    BlockDef(
                        name,
                        self._relpath(filepath),
                        self._line(text, match.start()),
                        body,
                    )
                )
        return results

    def _load_events(self) -> Dict[str, EventDef]:
        events: Dict[str, EventDef] = {}
        for filepath in self._collect_text_files(["events/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for match in _EVENT_DEF_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                id_match = _ID_RE.search(body)
                if not id_match:
                    continue
                event_id = id_match.group(1)
                event_def = EventDef(
                    event_id=event_id,
                    file=rel,
                    line=self._line(text, match.start()),
                    body=body,
                    hidden=bool(re.search(r"\bhidden\s*=\s*yes\b", body)),
                )
                event_def.options = self._nested_blocks(
                    body,
                    _OPTION_RE,
                    f"{event_id}:option",
                    rel,
                    event_def.line,
                )
                event_def.immediates = self._nested_blocks(
                    body,
                    _IMMEDIATE_RE,
                    f"{event_id}:immediate",
                    rel,
                    event_def.line,
                )
                events[event_id] = event_def
        return events

    def _load_idea_definitions(
        self, chains: Sequence[ChainConfig], event_defs: Dict[str, EventDef]
    ) -> Dict[str, IdeaDef]:
        idea_ids: Set[str] = set()
        chain_effects = self._load_top_level_blocks(
            ["common/scripted_effects/**/*_effects.txt"]
        )
        for chain in chains:
            idea_ids.update(chain.outcome_ideas)
            prefixes = chain.outcome_idea_prefixes
            if not prefixes:
                continue
            bodies = [
                effect.body
                for defs in chain_effects.values()
                for effect in defs
                if effect.name.startswith(chain.root)
            ]
            bodies.extend(
                event.body
                for event in event_defs.values()
                if event.event_id.startswith(chain.namespace + ".")
            )
            for body in bodies:
                idea_ids.update(self._idea_ids_in(body, prefixes))
        if not idea_ids:
            return {}

        results: Dict[str, IdeaDef] = {}
        idea_pattern = re.compile(
            r"(?m)^\s*("
            + "|".join(sorted(re.escape(i) for i in idea_ids))
            + r")\s*=\s*\{"
        )
        for filepath in self._collect_text_files(["common/ideas/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for match in idea_pattern.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                idea_id = match.group(1)
                results[idea_id] = IdeaDef(
                    idea_id=idea_id,
                    file=rel,
                    line=self._line(text, match.start()),
                    body=body,
                )
        return results

    def _idea_ids_in(self, body: str, prefixes: Sequence[str]) -> Set[str]:
        found: Set[str] = set()
        for pattern in (_ADD_IDEA_RE, _REMOVE_IDEA_RE):
            for match in pattern.finditer(body):
                idea_id = match.group(1)
                if any(idea_id.startswith(prefix) for prefix in prefixes):
                    found.add(idea_id)
        for match in _REMOVE_IDEA_BLOCK_RE.finditer(body):
            block, end = extract_block_from_text(body, match.end() - 1)
            if end == -1:
                continue
            for idea_id in re.findall(r"\b([A-Za-z0-9_]+)\b", block):
                if any(idea_id.startswith(prefix) for prefix in prefixes):
                    found.add(idea_id)
        return found

    def _discover_core_namespaces(
        self,
        startup_defs: Sequence[BlockDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> Set[str]:
        namespaces: Set[str] = set()
        for defs in effect_defs.values():
            for effect in defs:
                if effect.name.endswith("_corporate_trigger_year_2001") or (
                    "_corporate_trigger_year_" in effect.name
                ):
                    namespaces.update(self._event_namespaces_in_text(effect.body))
        for startup in startup_defs:
            namespaces.update(self._event_namespaces_in_text(startup.body))
        return namespaces

    def _load_event_call_sites(
        self,
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
        namespaces: Set[str],
    ) -> Dict[str, List[CallSite]]:
        tracked = frozenset(event_defs)
        call_sites: Dict[str, List[CallSite]] = {event_id: [] for event_id in tracked}

        for defs in effect_defs.values():
            for effect in defs:
                for target, line in self._find_event_calls(
                    effect.body, effect.line, tracked
                ):
                    call_sites.setdefault(target, []).append(
                        CallSite(target, effect.file, line, "effect", effect.name)
                    )

        for event in event_defs.values():
            for idx, option in enumerate(event.options, start=1):
                owner = f"{event.event_id}.option_{idx}"
                for target, line in self._find_event_calls(
                    option.body, option.line, tracked
                ):
                    call_sites.setdefault(target, []).append(
                        CallSite(target, option.file, line, "event-option", owner)
                    )
            for idx, immediate in enumerate(event.immediates, start=1):
                owner = f"{event.event_id}.immediate_{idx}"
                for target, line in self._find_event_calls(
                    immediate.body, immediate.line, tracked
                ):
                    call_sites.setdefault(target, []).append(
                        CallSite(target, immediate.file, line, "event-immediate", owner)
                    )

        generic_patterns = [
            "common/decisions/**/*.txt",
            "common/national_focus/**/*.txt",
            "common/on_actions/**/*.txt",
        ]
        for filepath in self._collect_text_files(generic_patterns):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            rel = self._relpath(filepath)
            for target, line in self._find_event_calls(text, 1, tracked):
                call_sites.setdefault(target, []).append(
                    CallSite(target, rel, line, "script", f"{rel}:{line}")
                )

        startup_ids = frozenset(_USA_2000_STARTUP_EVENTS).intersection(tracked)
        startup_needles = tuple(event_id.encode("ascii") for event_id in startup_ids)
        covered = (
            "common/decisions/",
            "common/national_focus/",
            "common/on_actions/",
            "common/scripted_effects/",
        )
        for filepath in self._collect_text_files(
            ["common/**/*.txt", "history/**/*.txt"]
        ):
            rel = self._relpath(filepath)
            normalized = rel.replace("\\", "/")
            if normalized.startswith(covered):
                continue
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            if not any(needle in raw for needle in startup_needles):
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            for target, line in self._find_event_calls(text, 1, startup_ids):
                call_sites.setdefault(target, []).append(
                    CallSite(target, rel, line, "script", f"{rel}:{line}")
                )
        return call_sites

    def _validate_manifest_coverage(
        self,
        chains: Sequence[ChainConfig],
        core_namespaces: Set[str],
        chain_by_namespace: Dict[str, ChainConfig],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        for identity_field, values in (
            ("name", [chain.name for chain in chains]),
            ("namespace", [chain.namespace for chain in chains]),
            ("root", [chain.root for chain in chains]),
        ):
            for value in sorted(set(values)):
                count = values.count(value)
                if count > 1:
                    findings.append(
                        (
                            f"Manifest {identity_field} {value} is declared {count} times",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
        root_values = [chain.root for chain in chains]
        auxiliary_roots = [
            lifecycle.root
            for chain in chains
            for lifecycle in chain.auxiliary_lifecycles
        ]
        for root in sorted(set(auxiliary_roots)):
            count = auxiliary_roots.count(root)
            if root in root_values or count != 1:
                findings.append(
                    (
                        f"Auxiliary lifecycle root {root} must be unique; found {count + root_values.count(root)} declarations",
                        "tools/corporate_history_contract.json",
                        0,
                    )
                )
        for chain in chains:
            if len(chain.dependency_order) != len(set(chain.dependency_order)):
                findings.append(
                    (
                        f"{chain.name} dependency_order contains duplicate roots",
                        "tools/corporate_history_contract.json",
                        0,
                    )
                )
            for dependency in chain.dependency_order:
                count = root_values.count(dependency)
                if dependency == chain.root:
                    findings.append(
                        (
                            f"{chain.name} cannot depend on its own root {dependency}",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
                elif count != 1:
                    findings.append(
                        (
                            f"{chain.name} dependency {dependency} must match exactly one manifest root; found {count}",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
            declared_auxiliary_markers = {
                lifecycle.terminal_marker for lifecycle in chain.auxiliary_lifecycles
            }
            if declared_auxiliary_markers != set(chain.auxiliary_completion_markers):
                findings.append(
                    (
                        f"{chain.name} auxiliary lifecycle markers differ from auxiliary_completion_markers",
                        "tools/corporate_history_contract.json",
                        0,
                    )
                )
        for namespace in sorted(core_namespaces):
            if namespace not in chain_by_namespace:
                findings.append(
                    (f"Unregistered corporate-history namespace {namespace}", "", 0)
                )
        return findings

    def _validate_lifecycle_metadata(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        startup_defs = effect_defs.get("corporate_history_on_startup", [])
        startup_full_branches = [
            self._startup_full_branch(startup.body) for startup in startup_defs
        ]
        startup_outcomes_branches = [
            self._startup_outcomes_branch(startup.body) for startup in startup_defs
        ]

        for chain in chains:
            if (
                "reconstruction" in chain.full_start_strategies
                or chain.outcomes_only_strategy == "reconstruction"
            ):
                findings.extend(
                    self._validate_terminal_date(
                        chain.name,
                        chain.reconstruct_effect,
                        chain.completion_flag,
                        chain.terminal_date,
                        effect_defs,
                    )
                )
            for lifecycle in chain.auxiliary_lifecycles:
                findings.extend(
                    self._validate_terminal_date(
                        f"{chain.name} auxiliary {lifecycle.root}",
                        lifecycle.reconstruction_effect,
                        lifecycle.terminal_marker,
                        lifecycle.terminal_date,
                        effect_defs,
                    )
                )
                reconstruction = effect_defs.get(lifecycle.reconstruction_effect, [])
                scheduler = effect_defs.get(lifecycle.scheduler_effect, [])
                if len(reconstruction) != 1:
                    findings.append(
                        (
                            f"{lifecycle.root} requires exactly one reconstruction effect {lifecycle.reconstruction_effect}",
                            "common/scripted_effects",
                            reconstruction[0].line if reconstruction else 0,
                        )
                    )
                if len(scheduler) != 1:
                    findings.append(
                        (
                            f"{lifecycle.root} requires exactly one scheduler effect {lifecycle.scheduler_effect}",
                            "common/scripted_effects",
                            scheduler[0].line if scheduler else 0,
                        )
                    )
                    continue
                if not any(
                    f"{lifecycle.reconstruction_effect} = yes" in branch
                    for branch in startup_full_branches
                ):
                    findings.append(
                        (
                            f"{lifecycle.reconstruction_effect} is not registered in the Full startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
                if not any(
                    f"{lifecycle.reconstruction_effect} = yes" in branch
                    for branch in startup_outcomes_branches
                ):
                    findings.append(
                        (
                            f"{lifecycle.reconstruction_effect} is not registered in the Outcomes Only startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
                if not any(
                    f"{lifecycle.scheduler_effect} = yes" in branch
                    for branch in startup_full_branches
                ):
                    findings.append(
                        (
                            f"{lifecycle.scheduler_effect} is not registered in the Full startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
                monthly = effect_defs.get(lifecycle.monthly_driver, [])
                if (
                    len(monthly) != 1
                    or f"{lifecycle.reconstruction_effect} = yes" not in monthly[0].body
                    or lifecycle.terminal_marker not in monthly[0].body
                ):
                    findings.append(
                        (
                            f"{lifecycle.reconstruction_effect} lacks a completion-guarded call from {lifecycle.monthly_driver}",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            monthly[0].line if monthly else 0,
                        )
                    )

                scheduled_events = {
                    target
                    for target, _line in self._find_event_calls(
                        scheduler[0].body, scheduler[0].line, frozenset()
                    )
                }
                expected_events = set(lifecycle.expected_yearly_callers)
                if scheduled_events != expected_events:
                    findings.append(
                        (
                            f"{lifecycle.scheduler_effect} events differ from expected_yearly_callers: expected {', '.join(sorted(expected_events)) or 'none'}; found {', '.join(sorted(scheduled_events)) or 'none'}",
                            scheduler[0].file,
                            scheduler[0].line,
                        )
                    )
                for event_id, dispatcher in lifecycle.expected_yearly_callers.items():
                    event = event_defs.get(event_id)
                    if event is None:
                        findings.append(
                            (
                                f"{lifecycle.root} expected yearly event {event_id} is undefined",
                                scheduler[0].file,
                                scheduler[0].line,
                            )
                        )
                        continue
                    actual_yearly = {
                        caller.owner
                        for caller in self._dedupe_callers(call_sites.get(event_id, []))
                        if caller.kind == "effect"
                        and "_corporate_trigger_year_" in caller.owner
                    }
                    if actual_yearly != {dispatcher}:
                        findings.append(
                            (
                                f"{event_id} yearly callers differ from the auxiliary lifecycle: expected {dispatcher}; found {', '.join(sorted(actual_yearly)) or 'none'}",
                                event.file,
                                event.line,
                            )
                        )
                    scheduler_callers = {
                        caller.owner
                        for caller in self._dedupe_callers(call_sites.get(event_id, []))
                        if caller.kind == "effect"
                        and caller.owner == lifecycle.scheduler_effect
                    }
                    if scheduler_callers != {lifecycle.scheduler_effect}:
                        findings.append(
                            (
                                f"{event_id} is not called by auxiliary scheduler {lifecycle.scheduler_effect}",
                                event.file,
                                event.line,
                            )
                        )
                    year_match = re.search(
                        r"_corporate_trigger_year_(\d{4})$", dispatcher
                    )
                    expected_year = int(year_match.group(1)) if year_match else -1
                    windows = self._scheduler_window_years(scheduler[0], event_id)
                    if windows != {expected_year}:
                        findings.append(
                            (
                                f"{lifecycle.scheduler_effect} must schedule {event_id} only in the {expected_year} January 1 window; found {', '.join(str(year) for year in sorted(windows)) or 'none'}",
                                scheduler[0].file,
                                scheduler[0].line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _validate_terminal_date(
        self,
        label: str,
        reconstruction_effect: str,
        terminal_marker: str,
        terminal_date: str,
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        definitions = effect_defs.get(reconstruction_effect, [])
        if len(definitions) != 1:
            return [
                (
                    f"{label} terminal date cannot be checked without exactly one {reconstruction_effect}",
                    "common/scripted_effects",
                    definitions[0].line if definitions else 0,
                )
            ]
        try:
            parsed = date.fromisoformat(terminal_date)
        except ValueError:
            return [
                (
                    f"{label} has invalid terminal_date {terminal_date}",
                    "tools/corporate_history_contract.json",
                    0,
                )
            ]
        expected = f"{parsed.year}.{parsed.month}.{parsed.day}"
        actual = self._terminal_guard_dates(definitions[0].body, terminal_marker)
        if actual == {expected}:
            return []
        return [
            (
                f"{label} terminal marker {terminal_marker} must use date > {expected}; found {', '.join(sorted(actual)) or 'none'}",
                definitions[0].file,
                definitions[0].line,
            )
        ]

    def _terminal_guard_dates(self, body: str, marker: str) -> Set[str]:
        dates: Set[str] = set()
        marker_pattern = re.compile(
            rf"\bset_country_flag\s*=\s*(?:{re.escape(marker)}\b|\{{\s*flag\s*=\s*{re.escape(marker)}\b)"
        )
        for name, _start, _end, child in self._iter_direct_child_blocks(body):
            limit = self._direct_child_block(child, "limit")
            if name in ("if", "else_if") and limit and marker_pattern.search(child):
                dates.update(
                    re.findall(r"\bdate\s*>\s*(\d{4}\.\d{1,2}\.\d{1,2})", limit)
                )
            dates.update(self._terminal_guard_dates(child, marker))
        return dates

    def _start_date_window(self, block: str) -> Optional[int]:
        """Year of the `NOT = { has_start_date < Y.1.1 } ... has_start_date < Y.1.2` pair.

        The lower bound always sits in the block's own limit. The upper bound may
        sit there too, or — where the block opens a whole-year window and its arms
        split January 1 from the rest (Nintendo, Russian Computing Sovereignty) —
        in the limit of a direct child arm. A sibling milestone's window is never
        consulted.
        """
        own = self._direct_child_block(block, "limit") or ""
        lower = re.search(
            r"NOT\s*=\s*\{\s*has_start_date\s*<\s*(\d{4})\.1\.1\s*\}",
            own,
        )
        if not lower:
            return None
        candidates = [own] + [
            self._direct_child_block(child, "limit") or ""
            for name, _s, _e, child in self._iter_direct_child_blocks(block)
            if name in ("if", "else_if")
        ]
        for text in candidates:
            upper = re.search(r"\bhas_start_date\s*<\s*(\d{4})\.1\.2\b", text)
            if upper and upper.group(1) == lower.group(1):
                return int(lower.group(1))
        return None

    def _scheduler_window_years(self, scheduler: BlockDef, event_id: str) -> Set[int]:
        years: Set[int] = set()
        self._collect_window_years(
            scheduler.body, scheduler.line, event_id, None, years
        )
        return years

    def _collect_window_years(
        self,
        body: str,
        line: int,
        event_id: str,
        inherited: Optional[int],
        years: Set[int],
    ) -> None:
        """Walk if/else_if children tracking the innermost start-date window in scope.

        Schedulers hoist their chain-level guard (`*_start_year_events_scheduled`,
        and for France the whole rule/tag/collapse gate) into an outer `if`, so the
        January-1 window can sit one or more levels above the block that queues the
        event. Only the window matters here; the enclosing guards are checked
        elsewhere.
        """

        def count_calls(text: str) -> int:
            return sum(
                1
                for target, _line in self._find_event_calls(text, line, frozenset())
                if target == event_id
            )

        for name, _start, _end, child in self._iter_direct_child_blocks(body):
            if name not in ("if", "else_if"):
                continue
            total = count_calls(child)
            if not total:
                continue
            window = self._start_date_window(child)
            if window is None:
                window = inherited
            nested = sum(
                count_calls(grandchild)
                for grandname, _gs, _ge, grandchild in self._iter_direct_child_blocks(
                    child
                )
                if grandname in ("if", "else_if")
            )
            # Queued directly by this block rather than only by a nested one.
            if total > nested and window is not None:
                years.add(window)
            if nested:
                self._collect_window_years(child, line, event_id, window, years)

    def _validate_event_reachability(
        self,
        chains: Sequence[ChainConfig],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        for chain in chains:
            for event_id, event in sorted(event_defs.items()):
                if not event_id.startswith(chain.namespace + "."):
                    continue
                callers = self._dedupe_callers(call_sites.get(event_id, []))
                expected = chain.expected_callers.get(event_id)
                if expected is not None:
                    actual_keys = tuple(sorted(caller.key for caller in callers))
                    expected_keys = tuple(sorted(expected))
                    if actual_keys != expected_keys:
                        findings.append(
                            (
                                f"{event_id} callers differ from the manifest: expected {', '.join(expected_keys) or 'none'}; found {', '.join(actual_keys) or 'none'}",
                                event.file,
                                event.line,
                            )
                        )
                    continue
                if not callers and event_id not in chain.callerless_anchors:
                    findings.append(
                        (
                            f"{event_id} has no direct callers and is not a declared custom/pre-2000 anchor",
                            event.file,
                            event.line,
                        )
                    )
                    continue
                if len(callers) <= 1:
                    continue
                if self._multiple_callers_allowed(chain, event_id, callers):
                    continue
                caller_desc = ", ".join(sorted(c.owner for c in callers))
                findings.append(
                    (
                        f"{event_id} has multiple direct callers: {caller_desc}",
                        event.file,
                        event.line,
                    )
                )
        return findings

    def _validate_oem_startup_architecture(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        on_action_path = self._root.joinpath(*_OEM_STARTUP_ON_ACTION.split("/"))
        if (
            not on_action_path.exists()
            and not set(_USA_2000_STARTUP_EVENTS).intersection(event_defs)
            and _OEM_STARTUP_EFFECT not in effect_defs
            and not {
                "gpu_development_schedule_current_year_events",
                "USA_ibm_schedule_prehistory",
                "USA_e3_schedule_current_year_events",
            }.intersection(effect_defs)
        ):
            return []

        findings: List[Tuple[str, str, int]] = []
        on_action_text = ""
        if on_action_path.exists():
            on_action_text = strip_comments(
                on_action_path.read_text(encoding="utf-8-sig", errors="replace")
            )
        else:
            findings.append(
                (
                    "The authoritative OEM startup on-action file is missing",
                    _OEM_STARTUP_ON_ACTION,
                    0,
                )
            )

        definition_sites = self._event_definition_sites(
            frozenset(_USA_2000_STARTUP_EVENTS)
        )
        for event_id in _USA_2000_STARTUP_EVENTS:
            sites = definition_sites.get(event_id, [])
            if len(sites) != 1:
                findings.append(
                    (
                        f"USA 2000 startup event {event_id} requires exactly one definition; found {len(sites)}",
                        sites[0][0] if sites else "events",
                        sites[0][1] if sites else 0,
                    )
                )

        bootstrap_defs = effect_defs.get(_OEM_STARTUP_EFFECT, [])
        if len(bootstrap_defs) != 1:
            findings.append(
                (
                    f"{_OEM_STARTUP_EFFECT} requires exactly one definition; found {len(bootstrap_defs)}",
                    "common/scripted_effects/00_corporate_history_effects.txt",
                    bootstrap_defs[0].line if bootstrap_defs else 0,
                )
            )

        bootstrap_callers = self._script_effect_call_sites(_OEM_STARTUP_EFFECT)
        normalized_callers = [
            (path.replace("\\", "/"), line) for path, line in bootstrap_callers
        ]
        if len(normalized_callers) != 1 or (
            normalized_callers and normalized_callers[0][0] != _OEM_STARTUP_ON_ACTION
        ):
            callers = ", ".join(f"{path}:{line}" for path, line in normalized_callers)
            findings.append(
                (
                    f"{_OEM_STARTUP_EFFECT} requires exactly one caller in {_OEM_STARTUP_ON_ACTION}; found {callers or 'none'}",
                    _OEM_STARTUP_ON_ACTION,
                    normalized_callers[0][1] if normalized_callers else 0,
                )
            )

        repository_script_patterns = [
            "common/**/*.txt",
            "events/**/*.txt",
            "history/**/*.txt",
        ]
        direct_bootstrap_callers = self._raw_script_call_sites(
            _OEM_STARTUP_EFFECT, repository_script_patterns
        )
        normalized_direct_bootstrap_callers = [
            (path.replace("\\", "/"), line) for path, line in direct_bootstrap_callers
        ]
        if len(normalized_direct_bootstrap_callers) != 1 or (
            normalized_direct_bootstrap_callers
            and normalized_direct_bootstrap_callers[0][0] != _OEM_STARTUP_ON_ACTION
        ):
            rendered = ", ".join(
                f"{path}:{line}" for path, line in normalized_direct_bootstrap_callers
            )
            findings.append(
                (
                    f"{_OEM_STARTUP_EFFECT} requires exactly one direct repository caller in {_OEM_STARTUP_ON_ACTION}; found {rendered or 'none'}",
                    (
                        direct_bootstrap_callers[0][0]
                        if direct_bootstrap_callers
                        else _OEM_STARTUP_ON_ACTION
                    ),
                    direct_bootstrap_callers[0][1] if direct_bootstrap_callers else 0,
                )
            )

        direct_corporate_callers = self._raw_script_call_sites(
            "corporate_history_on_startup", ["common/on_actions/**/*.txt"]
        )
        if direct_corporate_callers:
            rendered = ", ".join(
                f"{path.replace(os.sep, '/')}:{line}"
                for path, line in direct_corporate_callers
            )
            findings.append(
                (
                    f"corporate_history_on_startup must not be called directly from on_actions; found {rendered}",
                    direct_corporate_callers[0][0],
                    direct_corporate_callers[0][1],
                )
            )

        scoped_calls = 0
        for wrapper, _start, _end, wrapper_body in self._iter_direct_child_blocks(
            on_action_text
        ):
            if wrapper != "on_actions":
                continue
            for (
                child,
                _child_start,
                _child_end,
                startup_body,
            ) in self._iter_direct_child_blocks(wrapper_body):
                if child != "on_startup":
                    continue
                tag_match = re.search(r"\btag\s*=\s*ABK\b", startup_body)
                if tag_match:
                    file_tag_match = re.search(r"\btag\s*=\s*ABK\b", on_action_text)
                    findings.append(
                        (
                            "OEM on_startup tests tag = ABK in ROOT=None instead of entering ABK scope",
                            _OEM_STARTUP_ON_ACTION,
                            self._line(
                                on_action_text,
                                file_tag_match.start() if file_tag_match else 0,
                            ),
                        )
                    )
                effect_body = self._direct_child_block(startup_body, "effect")
                if effect_body is None:
                    continue
                abk_body = self._direct_child_block(effect_body, "ABK")
                if abk_body and re.search(
                    rf"\b{re.escape(_OEM_STARTUP_EFFECT)}\s*=\s*yes\b",
                    self._direct_block_text(abk_body),
                ):
                    scoped_calls += 1
        if scoped_calls != 1:
            findings.append(
                (
                    f"OEM startup requires exactly one on_actions -> on_startup -> effect -> ABK scoped bootstrap call; found {scoped_calls}",
                    _OEM_STARTUP_ON_ACTION,
                    0,
                )
            )

        guarded_body = ""
        direct_guarded_body = ""
        bootstrap = bootstrap_defs[0] if len(bootstrap_defs) == 1 else None
        if bootstrap is not None:
            bootstrap_children = list(self._iter_direct_child_blocks(bootstrap.body))
            guarded_blocks = []
            for child, _start, _end, body in bootstrap_children:
                if child != "if":
                    continue
                limit = self._direct_child_block(body, "limit") or ""
                if self._is_exact_global_flag_guard(limit, _OEM_STARTUP_FLAG):
                    guarded_blocks.append(body)
            if (
                len(bootstrap_children) != 1
                or len(guarded_blocks) != 1
                or self._direct_block_text(bootstrap.body).strip()
            ):
                findings.append(
                    (
                        f"{_OEM_STARTUP_EFFECT} requires one sole direct NOT has_global_flag guard for {_OEM_STARTUP_FLAG}; found {len(guarded_blocks)} valid guards across {len(bootstrap_children)} direct blocks",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )
            else:
                guarded_body = guarded_blocks[0]
                direct_guarded_body = self._direct_block_text(guarded_body)

            set_pattern = re.compile(
                rf"\bset_global_flag\s*=\s*{re.escape(_OEM_STARTUP_FLAG)}\b"
            )
            sets = list(set_pattern.finditer(bootstrap.body))
            if (
                len(sets) != 1
                or not guarded_body
                or not set_pattern.search(direct_guarded_body)
            ):
                findings.append(
                    (
                        f"{_OEM_STARTUP_EFFECT} must set {_OEM_STARTUP_FLAG} exactly once inside its guarded branch",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )
            else:
                marker_match = set_pattern.search(guarded_body)
                executable_block_before_marker = bool(
                    marker_match
                    and any(
                        child != "limit" and start < marker_match.start()
                        for child, start, _end, _body in self._iter_direct_child_blocks(
                            guarded_body
                        )
                    )
                )
                marker_is_first_direct_statement = bool(
                    re.match(
                        rf"\s*set_global_flag\s*=\s*{re.escape(_OEM_STARTUP_FLAG)}\b",
                        direct_guarded_body,
                    )
                )
                if (
                    not marker_is_first_direct_statement
                    or executable_block_before_marker
                ):
                    findings.append(
                        (
                            f"{_OEM_STARTUP_EFFECT} must set {_OEM_STARTUP_FLAG} before dispatching startup work and as its first direct effect statement",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )

            marker_sets, marker_clears = self._global_flag_write_sites(
                _OEM_STARTUP_FLAG
            )
            if len(marker_sets) != 1 or marker_sets[0][0] != bootstrap.file:
                rendered = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}" for path, line in marker_sets
                )
                findings.append(
                    (
                        f"{_OEM_STARTUP_FLAG} must be set only by {_OEM_STARTUP_EFFECT}; found {rendered or 'none'}",
                        marker_sets[0][0] if marker_sets else bootstrap.file,
                        marker_sets[0][1] if marker_sets else bootstrap.line,
                    )
                )
            if marker_clears:
                rendered = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}"
                    for path, line in marker_clears
                )
                findings.append(
                    (
                        f"{_OEM_STARTUP_FLAG} must never be cleared; found {rendered}",
                        marker_clears[0][0],
                        marker_clears[0][1],
                    )
                )

            if not re.search(
                r"\bcorporate_history_on_startup\s*=\s*yes\b",
                direct_guarded_body,
            ):
                findings.append(
                    (
                        "corporate_history_on_startup must be called directly from the guarded OEM bootstrap",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )

        corporate_owners: List[Tuple[str, int]] = []
        corporate_pattern = re.compile(r"\bcorporate_history_on_startup\s*=\s*yes\b")
        for name, definitions in effect_defs.items():
            for definition in definitions:
                corporate_owners.extend(
                    (
                        name,
                        definition.line
                        + self._line(definition.body, match.start())
                        - 1,
                    )
                    for match in corporate_pattern.finditer(definition.body)
                )
        if [owner for owner, _line in corporate_owners] != [_OEM_STARTUP_EFFECT]:
            findings.append(
                (
                    "corporate_history_on_startup must have the OEM bootstrap as its sole scripted-effect owner",
                    (
                        bootstrap.file
                        if bootstrap is not None
                        else "common/scripted_effects/00_corporate_history_effects.txt"
                    ),
                    corporate_owners[0][1] if corporate_owners else 0,
                )
            )
        direct_corporate_callers = self._raw_script_call_sites(
            "corporate_history_on_startup", repository_script_patterns
        )
        if len(direct_corporate_callers) != 1 or (
            bootstrap is not None
            and direct_corporate_callers
            and direct_corporate_callers[0][0] != bootstrap.file
        ):
            rendered = ", ".join(
                f"{path.replace(os.sep, '/')}:{line}"
                for path, line in direct_corporate_callers
            )
            findings.append(
                (
                    f"corporate_history_on_startup requires {_OEM_STARTUP_EFFECT} as its sole direct repository caller; found {rendered or 'none'}",
                    (
                        direct_corporate_callers[0][0]
                        if direct_corporate_callers
                        else (
                            bootstrap.file
                            if bootstrap is not None
                            else "common/scripted_effects"
                        )
                    ),
                    direct_corporate_callers[0][1] if direct_corporate_callers else 0,
                )
            )

        usa_branches = self._oem_startup_country_branches(guarded_body, "USA")
        if len(usa_branches) != 1:
            findings.append(
                (
                    f"The guarded OEM bootstrap requires exactly one explicit USA country branch; found {len(usa_branches)}",
                    bootstrap.file if bootstrap is not None else _OEM_STARTUP_ON_ACTION,
                    bootstrap.line if bootstrap is not None else 0,
                )
            )
        else:
            usa_limit, usa_scope = usa_branches[0]
            if not self._is_exact_country_exists_limit(usa_limit, "USA"):
                findings.append(
                    (
                        "The OEM bootstrap USA scope must be entered from an unconditionally country_exists = USA branch",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )
            direct_usa_scope = self._direct_block_text(usa_scope)
            for effect_name in (
                "gpu_development_reconstruct_history",
                "gpu_development_schedule_current_year_events",
            ):
                count = len(
                    re.findall(rf"\b{re.escape(effect_name)}\s*=\s*yes\b", usa_scope)
                )
                if count != 1:
                    findings.append(
                        (
                            f"USA startup requires exactly one {effect_name} call; found {count}",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )
                elif not re.search(
                    rf"\b{re.escape(effect_name)}\s*=\s*yes\b", direct_usa_scope
                ):
                    findings.append(
                        (
                            f"USA startup must call {effect_name} directly in USA scope without a Corporate History gate",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )
            dell_gate = ""
            for child, _start, _end, body in self._iter_direct_child_blocks(usa_scope):
                if child not in ("if", "else_if"):
                    continue
                limit = self._direct_child_block(body, "limit") or ""
                if self._is_exact_dell_2000_full_limit(
                    limit
                ) and self._direct_event_calls(body, "USA_oem_events.13"):
                    dell_gate = body
                if (
                    "corporate_history_full_enabled = yes" in limit
                    and "gpu_development_schedule_current_year_events = yes" in body
                ):
                    findings.append(
                        (
                            "USA GPU startup is incorrectly gated by Corporate History Full mode",
                            bootstrap.file,
                            bootstrap.line,
                        )
                    )
            if not dell_gate:
                findings.append(
                    (
                        "USA_oem_events.13 is not reachable from the USA bootstrap under its 2000 Full-mode gate",
                        bootstrap.file,
                        bootstrap.line,
                    )
                )

        startup_defs = effect_defs.get("corporate_history_on_startup", [])
        startup = startup_defs[0] if len(startup_defs) == 1 else None
        full_branch = self._startup_full_branch(startup.body) if startup else ""
        outcomes_branch = self._startup_outcomes_branch(startup.body) if startup else ""
        if startup is None:
            findings.append(
                (
                    f"corporate_history_on_startup requires exactly one definition; found {len(startup_defs)}",
                    "common/scripted_effects/00_corporate_history_effects.txt",
                    startup_defs[0].line if startup_defs else 0,
                )
            )
        else:
            if not full_branch:
                findings.append(
                    (
                        "corporate_history_on_startup is missing its Full-mode branch",
                        startup.file,
                        startup.line,
                    )
                )
            if not outcomes_branch:
                findings.append(
                    (
                        "corporate_history_on_startup is missing its Outcomes Only branch",
                        startup.file,
                        startup.line,
                    )
                )
            full_only_symbols = (
                "USA_oem_events.13",
                "USA_ibm_events.12",
                "USA_ibm_events.13",
                "USA_ibm_events.90",
                "USA_ibm_schedule_prehistory",
                "USA_e3_events.1",
                "USA_e3_events.90",
                "USA_e3_schedule_current_year_events",
                "USA_hp_events.1",
            )
            full_only_effects = {
                "USA_ibm_schedule_prehistory",
                "USA_e3_schedule_current_year_events",
            }
            full_only_events = {
                "USA_oem_events.13",
                "USA_ibm_events.12",
                "USA_ibm_events.13",
                "USA_ibm_events.90",
                "USA_e3_events.1",
                "USA_e3_events.90",
                "USA_hp_events.1",
            }
            outcomes_effects, outcomes_events = self._mixed_script_descendants(
                outcomes_branch, effect_defs, event_defs
            )
            if (
                any(symbol in outcomes_branch for symbol in full_only_symbols)
                or full_only_effects.intersection(outcomes_effects)
                or full_only_events.intersection(outcomes_events)
            ):
                findings.append(
                    (
                        "Outcomes Only schedules a Full-mode USA corporate popup",
                        startup.file,
                        startup.line,
                    )
                )
            if any(
                child == "else"
                for child, _start, _end, _body in self._iter_direct_child_blocks(
                    startup.body
                )
            ):
                findings.append(
                    (
                        "Corporate History Off must leave startup inert; an else branch is present",
                        startup.file,
                        startup.line,
                    )
                )
            direct_children = [
                child
                for child, _start, _end, _body in self._iter_direct_child_blocks(
                    startup.body
                )
            ]
            if (
                direct_children != ["if", "else_if"]
                or self._direct_block_text(startup.body).strip()
            ):
                findings.append(
                    (
                        "Corporate History startup must contain only its direct Full and Outcomes Only branches so Off remains inert",
                        startup.file,
                        startup.line,
                    )
                )

        full_usa_branches = self._oem_startup_country_branches(full_branch, "USA")
        full_usa_scopes = [scope for _limit, scope in full_usa_branches]
        full_usa_body = "\n".join(full_usa_scopes)
        if full_branch and not full_usa_scopes:
            findings.append(
                (
                    "Corporate History Full startup does not enter an explicit USA scope",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )
        anchor_branches = [
            (limit, scope)
            for limit, scope in full_usa_branches
            if self._direct_event_calls(scope, "USA_ibm_events.90")
            or self._direct_event_calls(scope, "USA_e3_events.90")
        ]
        anchor_shape_valid = False
        anchor_calls_valid = False
        if len(anchor_branches) == 1:
            anchor_limit, anchor_scope = anchor_branches[0]
            anchor_shape_valid = self._is_exact_country_exists_limit(
                anchor_limit, "USA"
            )
            ibm_calls = self._direct_event_calls(anchor_scope, "USA_ibm_events.90")
            e3_calls = self._direct_event_calls(anchor_scope, "USA_e3_events.90")
            anchor_calls_valid = bool(
                len(ibm_calls) == 1
                and ibm_calls[0][1] == 1
                and len(e3_calls) == 1
                and e3_calls[0][1] == 1
            )
        if full_branch and not anchor_shape_valid:
            findings.append(
                (
                    "IBM and E3 startup anchors must share one reachable country_exists = USA branch with no additional gate",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )
        elif full_branch and not anchor_calls_valid:
            findings.append(
                (
                    "IBM and E3 startup anchors must both be queued directly at days = 1 in their USA branch",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )

        expected_callers = {
            "USA_oem_events.13": ("effect", _OEM_STARTUP_EFFECT),
            "gpu_development.1": (
                "effect",
                "gpu_development_schedule_current_year_events",
            ),
            "USA_ibm_events.12": ("effect", "USA_ibm_schedule_prehistory"),
            "USA_ibm_events.13": ("effect", "USA_ibm_schedule_prehistory"),
            "USA_ibm_events.90": ("effect", "corporate_history_on_startup"),
            "USA_e3_events.1": (
                "effect",
                "USA_e3_schedule_current_year_events",
            ),
            "USA_e3_events.90": ("effect", "corporate_history_on_startup"),
            "USA_hp_events.1": ("effect", "corporate_history_on_startup"),
        }
        for event_id, expected in expected_callers.items():
            actual = [
                (caller.kind, caller.owner) for caller in call_sites.get(event_id, [])
            ]
            if actual != [expected]:
                rendered = ", ".join(f"{kind}:{owner}" for kind, owner in actual)
                event = event_defs.get(event_id)
                findings.append(
                    (
                        f"{event_id} requires sole caller {expected[0]}:{expected[1]}; found {rendered or 'none'}",
                        event.file if event else "events",
                        event.line if event else 0,
                    )
                )

        findings.extend(
            self._validate_usa_2000_startup_schedule(
                effect_defs,
                event_defs,
                bootstrap,
                startup,
                full_branch,
                full_usa_body,
            )
        )

        yearly_path = (
            self._root / "common" / "scripted_effects" / "00_yearly_effects.txt"
        )
        if yearly_path.exists():
            yearly_text = strip_comments(
                yearly_path.read_text(encoding="utf-8-sig", errors="replace")
            )
            forbidden = (
                _OEM_STARTUP_EFFECT,
                "corporate_history_on_startup",
                "gpu_development_schedule_current_year_events",
                *_USA_2000_STARTUP_EVENTS,
            )
            for symbol in forbidden:
                match = re.search(rf"\b{re.escape(symbol)}\b", yearly_text)
                if match:
                    findings.append(
                        (
                            f"OEM startup symbol {symbol} must remain outside upstream-owned 00_yearly_effects.txt",
                            "common/scripted_effects/00_yearly_effects.txt",
                            self._line(yearly_text, match.start()),
                        )
                    )

        return self._dedupe_findings(findings)

    def _validate_dispatchers(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        call_sites: Dict[str, List[CallSite]],
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        defined_dispatchers = {
            name: defs
            for name, defs in effect_defs.items()
            if "_corporate_trigger_year_" in name
        }
        yearly_calls = self._effect_call_counts(
            effect_defs, [name for name in defined_dispatchers]
        )
        registered_namespaces = {chain.namespace for chain in chains}
        defined_events = set(event_defs)

        for name, defs in sorted(defined_dispatchers.items()):
            if len(defs) != 1:
                for definition in defs:
                    findings.append(
                        (
                            f"{name} requires exactly one definition; found {len(defs)}",
                            definition.file,
                            definition.line,
                        )
                    )
                continue
            definition = defs[0]
            callers = yearly_calls.get(name, [])
            on_action_callers = self._script_effect_call_sites(name)
            call_count = len(callers) + len(on_action_callers)
            if call_count != 1:
                findings.append(
                    (
                        f"{name} requires exactly one yearly-dispatch caller; found {call_count}",
                        definition.file,
                        definition.line,
                    )
                )
            year_match = re.search(r"_corporate_trigger_year_(\d{4})$", name)
            if call_count == 1 and year_match:
                expected_owner = f"trigger_year_{year_match.group(1)}_events"
                if callers:
                    if callers[0][2] != expected_owner:
                        findings.append(
                            (
                                f"{name} must be called by {expected_owner}; found {callers[0][2]}",
                                callers[0][0],
                                callers[0][1],
                            )
                        )
                else:
                    on_action_file, on_action_line = on_action_callers[0]
                    expected_on_action = (
                        "common/on_actions/01_oem_corporate_history_on_actions.txt"
                    )
                    if on_action_file.replace("\\", "/") != expected_on_action:
                        findings.append(
                            (
                                f"{name} must be called by {expected_owner} or the dedicated OEM yearly on-action; found {on_action_file}",
                                on_action_file,
                                on_action_line,
                            )
                        )

            all_scheduled = self._find_event_calls(
                definition.body, definition.line, frozenset()
            )
            guarded_targets: List[str] = []
            for child, _start, _end, body in self._iter_direct_child_blocks(
                definition.body
            ):
                if child not in ("if", "else_if"):
                    continue
                limit = self._direct_child_block(body, "limit")
                if not limit or "corporate_history_full_enabled = yes" not in limit:
                    continue
                guarded_targets.extend(
                    target
                    for target, _line in self._find_event_calls(
                        body, definition.line, frozenset()
                    )
                )
            if len(guarded_targets) != len(all_scheduled):
                findings.append(
                    (
                        f"{name} schedules events outside its corporate_history_full_enabled branch",
                        definition.file,
                        definition.line,
                    )
                )
            scheduled = all_scheduled
            counts: Dict[str, int] = {}
            for target, _line in scheduled:
                counts[target] = counts.get(target, 0) + 1
                if target not in defined_events:
                    findings.append(
                        (
                            f"{name} calls undefined event {target}",
                            definition.file,
                            definition.line,
                        )
                    )
            for target, count in sorted(counts.items()):
                if count > 1:
                    findings.append(
                        (
                            f"{name} schedules {target} {count} times",
                            definition.file,
                            definition.line,
                        )
                    )

        yearly_inline = effect_defs
        for defs in yearly_inline.values():
            for block in defs:
                if not block.file.endswith(
                    "common\\scripted_effects\\00_yearly_effects.txt"
                ) and not block.file.endswith(
                    "common/scripted_effects/00_yearly_effects.txt"
                ):
                    continue
                for target, line in self._find_event_calls(
                    block.body, block.line, defined_events
                ):
                    namespace = target.split(".", 1)[0]
                    if namespace in registered_namespaces:
                        findings.append(
                            (
                                f"{target} is scheduled inline in 00_yearly_effects.txt instead of through its corporate dispatcher",
                                block.file,
                                line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _validate_tier_one_contract(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        idea_defs: Dict[str, IdeaDef],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        startup_defs = effect_defs.get("corporate_history_on_startup", [])
        startup_full_branches = [
            self._startup_full_branch(startup.body) for startup in startup_defs
        ]
        startup_outcomes_branches = [
            self._startup_outcomes_branch(startup.body) for startup in startup_defs
        ]
        monthly_defs = {
            name: defs[0] for name, defs in effect_defs.items() if len(defs) == 1
        }

        startup_callers = self._script_effect_call_sites("corporate_history_on_startup")
        if len(startup_callers) != 1:
            findings.append(
                (
                    f"corporate_history_on_startup requires exactly one on-action caller; found {len(startup_callers)}",
                    (
                        startup_callers[0][0]
                        if startup_callers
                        else "common/on_actions/00_on_actions.txt"
                    ),
                    startup_callers[0][1] if startup_callers else 0,
                )
            )
        for driver in sorted({chain.monthly_driver for chain in chains}):
            driver_callers = self._script_effect_call_sites(driver)
            if len(driver_callers) != 1:
                findings.append(
                    (
                        f"{driver} requires exactly one matching on-monthly caller; found {len(driver_callers)}",
                        driver_callers[0][0] if driver_callers else "common/on_actions",
                        driver_callers[0][1] if driver_callers else 0,
                    )
                )

        for chain in chains:
            if chain.outcomes_only_strategy == "reconstruction":
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.reconstruct_effect,
                        f"{chain.name} is missing its declared Outcomes Only reconstruction effect",
                    )
                )
                if not self._flag_is_produced(chain.completion_flag, effect_defs):
                    findings.append(
                        (
                            f"{chain.completion_flag} is never produced",
                            f"common/scripted_effects/{chain.root}_effects.txt",
                            0,
                        )
                    )
                if not any(
                    f"{chain.reconstruct_effect} = yes" in branch
                    for branch in startup_outcomes_branches
                ):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} is not registered in the Outcomes Only startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
                monthly = monthly_defs.get(chain.monthly_driver)
                if (
                    monthly is None
                    or f"{chain.reconstruct_effect} = yes" not in monthly.body
                    or chain.completion_flag not in monthly.body
                ):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} lacks a completion-guarded call from {chain.monthly_driver}",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            monthly.line if monthly else 0,
                        )
                    )
            if "current_year_scheduler" in chain.full_start_strategies:
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.scheduler_effect,
                        f"{chain.name} is missing its declared current-year scheduler",
                    )
                )
                if not any(
                    self._startup_reaches_scheduler(chain, branch, event_defs)
                    for branch in startup_full_branches
                ):
                    findings.append(
                        (
                            f"{chain.scheduler_effect} is not reachable from the Full startup branch",
                            "common/scripted_effects/00_corporate_history_effects.txt",
                            0,
                        )
                    )
            if chain.tier != 1:
                continue
            if chain.variables:
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.initialize_effect,
                        f"{chain.name} is missing its initialization effect",
                    )
                )
                findings.extend(
                    self._require_effect(
                        effect_defs,
                        chain.clamp_effect,
                        f"{chain.name} is missing its clamp effect",
                    )
                )
            findings.extend(
                self._require_effect(
                    effect_defs,
                    chain.reconstruct_effect,
                    f"{chain.name} is missing its reconstruction effect",
                )
            )
            event_90 = event_defs.get(chain.hidden_ninety_id)
            startup_reconstructs = any(
                f"{chain.reconstruct_effect} = yes" in branch
                for branch in startup_full_branches
            )
            if (event_90 is None or not event_90.hidden) and not startup_reconstructs:
                file = f"events/{chain.namespace}.txt"
                line = event_90.line if event_90 else 0
                findings.append(
                    (
                        f"{chain.hidden_ninety_id} is missing or not hidden and "
                        f"{chain.reconstruct_effect} is not called directly from "
                        "corporate_history_on_startup",
                        event_90.file if event_90 else file,
                        line,
                    )
                )
            if not self._flag_is_produced(chain.completion_flag, effect_defs):
                findings.append(
                    (
                        f"{chain.completion_flag} is never produced",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            if not startup_defs or not any(
                self._chain_is_registered_in_startup(chain, startup.body)
                for startup in startup_defs
            ):
                findings.append(
                    (
                        f"{chain.name} is missing startup registration in corporate_history_on_startup",
                        "common/scripted_effects/00_corporate_history_effects.txt",
                        0,
                    )
                )
            monthly = monthly_defs.get(chain.monthly_driver)
            if (
                monthly is None
                or f"{chain.reconstruct_effect} = yes" not in monthly.body
            ):
                findings.append(
                    (
                        f"{chain.reconstruct_effect} is not called from {chain.monthly_driver}",
                        "common/scripted_effects/00_corporate_history_effects.txt",
                        monthly.line if monthly else 0,
                    )
                )
            if (
                chain.requires_current_year_scheduler
                and chain.scheduler_effect not in effect_defs
            ):
                findings.append(
                    (
                        f"{chain.name} is missing its current-year scheduler {chain.scheduler_effect}",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            if not self._has_terminal_resolver(chain, effect_defs):
                findings.append(
                    (
                        f"{chain.name} is missing a terminal resolver effect",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            outcome_ids = self._outcome_ideas_for_chain(chain, idea_defs)
            if not outcome_ids:
                findings.append(
                    (
                        f"{chain.name} has no permanent outcome ideas registered under {', '.join(chain.outcome_idea_prefixes)}",
                        f"common/ideas/{chain.root}_ideas.txt",
                        0,
                    )
                )
            if not self._has_cleanup_path(chain, effect_defs, event_defs, outcome_ids):
                findings.append(
                    (
                        f"{chain.name} is missing a mutually exclusive cleanup effect",
                        f"common/scripted_effects/{chain.root}_effects.txt",
                        0,
                    )
                )
            for idea_id in sorted(outcome_ids):
                idea = idea_defs.get(idea_id)
                if idea is None:
                    findings.append(
                        (
                            f"Missing outcome idea definition {idea_id}",
                            f"common/ideas/{chain.root}_ideas.txt",
                            0,
                        )
                    )
                    continue
                if not re.search(
                    rf"\ballowed\s*=\s*\{{\s*original_tag\s*=\s*{re.escape(chain.tag)}\s*\}}",
                    idea.body,
                ):
                    findings.append(
                        (
                            f"{idea_id} is missing allowed = {{ original_tag = {chain.tag} }}",
                            idea.file,
                            idea.line,
                        )
                    )
                if not re.search(
                    r"\ballowed_civil_war\s*=\s*\{\s*always\s*=\s*yes\s*\}",
                    idea.body,
                ):
                    findings.append(
                        (
                            f"{idea_id} is missing allowed_civil_war = {{ always = yes }}",
                            idea.file,
                            idea.line,
                        )
                    )
        return findings

    def _validate_clamp_coverage(
        self,
        chains: Sequence[ChainConfig],
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in chains:
            if not chain.variables:
                continue
            clamp = effect_lookup.get(chain.clamp_effect)
            if clamp is not None:
                reachable_clamps = self._reachable_chain_effects(
                    chain, clamp, effect_lookup
                )
                declared_bounds: Dict[str, Tuple[Decimal, Decimal]] = {}
                for effect in reachable_clamps.values():
                    declared_bounds.update(
                        {
                            match.group(1): (
                                Decimal(match.group(2)),
                                Decimal(match.group(3)),
                            )
                            for match in _CLAMP_VAR_RE.finditer(effect.body)
                        }
                    )
                    declared_bounds.update(self._indirect_temp_clamps(effect.body))
                for variable, bound in chain.variables.items():
                    expected = (bound.minimum, bound.maximum)
                    standard_clamp = expected == (0, 10) and re.search(
                        rf"\bset_temp_variable\s*=\s*\{{\s*corp_value\s*=\s*{re.escape(variable)}\s*\}}"
                        rf".*?\bcorporate_history_clamp_value\s*=\s*yes\b"
                        rf".*?\bset_variable\s*=\s*\{{\s*{re.escape(variable)}\s*=\s*corp_value\s*\}}",
                        "\n".join(effect.body for effect in reachable_clamps.values()),
                        re.DOTALL,
                    )
                    if declared_bounds.get(variable) != expected and not standard_clamp:
                        findings.append(
                            (
                                f"{chain.clamp_effect} must clamp {variable} to manifest bounds {bound.minimum}..{bound.maximum}",
                                clamp.file,
                                clamp.line,
                            )
                        )
            saw_clamped_option = False
            saw_mutating_option = False
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + "."):
                    continue
                for option in [*event.options, *event.immediates]:
                    pending, used_clamp, mutated = self._trace_mutation_path(
                        option.body, chain, effect_lookup, set()
                    )
                    if not mutated:
                        continue
                    saw_mutating_option = True
                    if used_clamp:
                        saw_clamped_option = True
                    if pending:
                        findings.append(
                            (
                                f"{event.event_id} option at line {option.line} mutates bounded variables without a later {chain.clamp_effect} call",
                                option.file,
                                option.line,
                            )
                        )
            if saw_mutating_option and not saw_clamped_option:
                findings.append(
                    (
                        f"{chain.name} clamps bounded variables only at initialization",
                        f"events/{chain.namespace}.txt",
                        0,
                    )
                )
        return findings

    def _indirect_temp_clamps(self, body: str) -> Dict[str, Tuple[int, int]]:
        pattern = re.compile(
            r"\bset_temp_variable\s*=\s*\{\s*corp_value\s*=\s*([A-Za-z0-9_]+)\s*\}"
            r".*?\bclamp_temp_variable\s*=\s*\{\s*var\s*=\s*corp_value\s+min\s*=\s*(-?\d+)\s+max\s*=\s*(-?\d+)\s*\}"
            r".*?\bset_variable\s*=\s*\{\s*\1\s*=\s*corp_value\s*\}",
            re.DOTALL,
        )
        return {
            match.group(1): (int(match.group(2)), int(match.group(3)))
            for match in pattern.finditer(body)
        }

    def _validate_reconstruction_safety(
        self,
        chains: Sequence[ChainConfig],
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in chains:
            reconstruct = effect_lookup.get(chain.reconstruct_effect)
            if reconstruct is None:
                continue
            reachable = self._reachable_chain_effects(chain, reconstruct, effect_lookup)
            for effect in reachable.values():
                for label, pattern in _CUSTOM_EFFECT_REWARDS:
                    if pattern.search(effect.body):
                        findings.append(
                            (
                                f"{chain.reconstruct_effect} transitively replays {label} through {effect.name}",
                                effect.file,
                                effect.line,
                            )
                        )
                event_calls = self._find_event_calls(
                    effect.body, effect.line, frozenset()
                )
                for target, line in event_calls:
                    event = event_defs.get(target)
                    target_namespace = target.split(".", 1)[0]
                    is_declared_cross_chain = any(
                        target.startswith(prefix) for prefix in chain.allowed_writes
                    )
                    is_delivery_effect = "_schedule_" in effect.name
                    has_silent_catchup_guard = (
                        f"NOT = {{ has_country_flag = {chain.root}_catchup_silent }}"
                        in effect.body
                        and f"set_country_flag = {chain.root}_catchup_silent"
                        in reconstruct.body
                    )
                    if (event is not None and event.hidden) or is_delivery_effect:
                        continue
                    if has_silent_catchup_guard:
                        continue
                    if target_namespace != chain.namespace and is_declared_cross_chain:
                        continue
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} transitively fires an event through {effect.name}",
                            effect.file,
                            line,
                        )
                    )
            if not self._flag_is_produced(
                chain.completion_flag,
                {name: [effect] for name, effect in reachable.items()},
            ):
                findings.append(
                    (
                        f"{chain.reconstruct_effect} never sets {chain.completion_flag}",
                        reconstruct.file,
                        reconstruct.line,
                    )
                )
            for block in self._nested_blocks(
                reconstruct.body,
                re.compile(r"\b(?:if|else_if)\s*=\s*\{"),
                chain.reconstruct_effect,
                reconstruct.file,
                reconstruct.line,
            ):
                if not self._block_has_state_change(block.body, chain):
                    continue
                if "date >" not in block.body:
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} has a state-changing block without a date guard",
                            block.file,
                            block.line,
                        )
                    )
                if not self._has_marker_guard(block.body):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} has a state-changing block without sibling-marker guards",
                            block.file,
                            block.line,
                        )
                    )
        return self._dedupe_findings(findings)

    def _reachable_chain_effects(
        self,
        chain: ChainConfig,
        root_effect: BlockDef,
        effect_lookup: Dict[str, BlockDef],
    ) -> Dict[str, BlockDef]:
        reachable: Dict[str, BlockDef] = {}
        pending = [root_effect]
        while pending:
            effect = pending.pop()
            if effect.name in reachable:
                continue
            reachable[effect.name] = effect
            for match in _EFFECT_YES_RE.finditer(effect.body):
                name = match.group(1)
                if (
                    name.startswith(chain.root)
                    and name in effect_lookup
                    and name not in reachable
                ):
                    pending.append(effect_lookup[name])
        return reachable

    def _validate_completion_markers(
        self, chains: Sequence[ChainConfig], effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings = []
        discovered_flags: Set[str] = set()
        for defs in effect_defs.values():
            for effect in defs:
                discovered_flags.update(
                    re.findall(r"\b([A-Za-z0-9_]+_reconstruct_complete)\b", effect.body)
                )
        owners: Dict[str, List[ChainConfig]] = {}
        for chain in chains:
            declared_markers = (
                chain.completion_flag,
                *chain.auxiliary_completion_markers,
            )
            for marker in declared_markers:
                if marker in discovered_flags:
                    owners.setdefault(marker, []).append(chain)
        for flag in sorted(discovered_flags):
            chain_owners = owners.get(flag, [])
            if len(chain_owners) != 1:
                findings.append(
                    (f"{flag} has {len(chain_owners)} owning chains", "", 0)
                )
                continue
            producers = self._flag_producers(flag, effect_defs)
            if not producers:
                findings.append((f"{flag} has no producers", "", 0))
            elif (
                len(producers) > 1
                and not chain_owners[0].allow_multiple_completion_producers
            ):
                findings.append(
                    (
                        f"{flag} has {len(producers)} producers",
                        producers[0][0],
                        producers[0][1],
                    )
                )
            consumers = self._monthly_consumers(flag, effect_defs)
            if len(consumers) != 1:
                file = (
                    consumers[0][0]
                    if consumers
                    else "common/scripted_effects/00_corporate_history_effects.txt"
                )
                line = consumers[0][1] if consumers else 0
                findings.append(
                    (
                        f"{flag} has {len(consumers)} intended monthly-driver consumers",
                        file,
                        line,
                    )
                )
        return findings

    def _validate_cross_chain_ownership(
        self,
        chains: Sequence[ChainConfig],
        chain_by_root: Dict[str, ChainConfig],
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        del chain_by_root
        findings = []
        ownership_patterns: List[Tuple[ChainConfig, str, re.Pattern[str]]] = []
        for chain in chains:
            for prefix in chain.owned_prefixes:
                ownership_patterns.append(
                    (
                        chain,
                        prefix,
                        re.compile(r"\b" + re.escape(prefix) + r"[A-Za-z0-9_]*\b"),
                    )
                )

        for chain in chains:
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + "."):
                    continue
                findings.extend(
                    self._cross_chain_findings_in_text(
                        chain,
                        event.body,
                        event.file,
                        event.line,
                        ownership_patterns,
                    )
                )
            for name, definitions in effect_defs.items():
                if not name.startswith(chain.root):
                    continue
                for definition in definitions:
                    findings.extend(
                        self._cross_chain_findings_in_text(
                            chain,
                            definition.body,
                            definition.file,
                            definition.line,
                            ownership_patterns,
                        )
                    )
        return self._dedupe_findings(findings)

    def _cross_chain_findings_in_text(
        self,
        chain: ChainConfig,
        text: str,
        rel: str,
        base_line: int,
        ownership_patterns: Sequence[Tuple[ChainConfig, str, re.Pattern[str]]],
    ) -> List[Tuple[str, str, int]]:
        findings = []
        stack: List[str] = []
        for offset, raw_line in enumerate(text.splitlines()):
            line_no = base_line + offset
            code = blank_quoted_strings(raw_line)
            headers = re.findall(r"(" + _BLOCK_IDENTIFIER + r")\s*=\s*\{", code)
            stack.extend(headers)
            tokens: List[Tuple[ChainConfig, str]] = []
            seen_tokens: Set[Tuple[str, str]] = set()
            for owner, _prefix, pattern in ownership_patterns:
                if owner is chain:
                    continue
                for token in pattern.findall(code):
                    key = (owner.root, token)
                    if key not in seen_tokens:
                        seen_tokens.add(key)
                        tokens.append((owner, token))
            for owner, token in sorted(tokens, key=lambda item: item[1]):
                if self._line_is_cross_write(code, owner, stack):
                    if not self._is_allowed(token, chain.allowed_writes):
                        findings.append(
                            (
                                f"{chain.name} writes {token}, owned by {owner.name}, outside declared exceptions",
                                rel,
                                line_no,
                            )
                        )
                elif self._line_is_cross_read(code, stack):
                    if not self._is_allowed(token, chain.allowed_reads):
                        label = (
                            "read-only AI/flavour use"
                            if any(ctx in ("ai_chance", "trigger") for ctx in stack)
                            else "read"
                        )
                        findings.append(
                            (
                                f"{chain.name} has undeclared cross-chain {label} of {token}, owned by {owner.name}",
                                rel,
                                line_no,
                            )
                        )
            closes = code.count("}")
            while closes > 0 and stack:
                stack.pop()
                closes -= 1
        return findings

    def _validate_localisation_contract(
        self, chains: Sequence[ChainConfig], event_defs: Dict[str, EventDef]
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []
        all_key_locations: Dict[str, List[Tuple[str, int]]] = {}
        scoped_key_locations: Dict[str, List[Tuple[str, int]]] = {}
        prefixes = tuple(
            prefix
            for chain in chains
            for prefix in (chain.localisation_prefixes or (chain.namespace, chain.root))
        )
        for filepath in self._collect_text_files(["localisation/english/**/*.yml"]):
            path = Path(filepath)
            try:
                raw = path.read_bytes()
                text = raw.decode("utf-8-sig")
            except (OSError, UnicodeDecodeError):
                continue
            rel = self._relpath(path)
            file_has_scoped_key = False
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = _LOC_KEY_PREFIX_RE.match(line)
                if not match:
                    continue
                key = match.group(1)
                is_scoped = key.startswith(prefixes)
                if not _VALID_LOC_VALUE_RE.match(line):
                    if is_scoped:
                        file_has_scoped_key = True
                        findings.append(
                            (
                                f"Malformed English corporate-history localisation value {key}",
                                rel,
                                line_no,
                            )
                        )
                    continue
                all_key_locations.setdefault(key, []).append((rel, line_no))
                if not is_scoped:
                    continue
                file_has_scoped_key = True
                scoped_key_locations.setdefault(key, []).append((rel, line_no))
            if file_has_scoped_key:
                if not raw.startswith(b"\xef\xbb\xbf"):
                    findings.append(
                        ("English OEM localisation file is missing a UTF-8 BOM", rel, 1)
                    )

        for key, locations in sorted(scoped_key_locations.items()):
            if len(locations) > 1:
                findings.append(
                    (
                        f"English OEM localisation key {key} is defined {len(locations)} times",
                        locations[0][0],
                        locations[0][1],
                    )
                )

        for chain in chains:
            seen_option_keys: Set[str] = set()
            chain_events = [
                event
                for event_id, event in event_defs.items()
                if event_id.startswith(chain.namespace + ".") and not event.hidden
            ]
            for event in chain_events:
                referenced = []
                for pattern in (
                    r"\btitle\s*=\s*([A-Za-z0-9_.-]+)",
                    r"\bdesc\s*=\s*([A-Za-z0-9_.-]+)",
                    r"\btext\s*=\s*([A-Za-z0-9_.-]+)",
                ):
                    referenced.extend(re.findall(pattern, event.body))
                for option in event.options:
                    name_match = re.search(
                        r"\bname\s*=\s*([A-Za-z0-9_.-]+)", option.body
                    )
                    if not name_match:
                        continue
                    option_key = name_match.group(1)
                    seen_option_keys.add(option_key)
                    referenced.append(option_key)
                    tooltip_keys = re.findall(
                        r"\b(?:custom_effect_tooltip|tooltip)\s*=\s*([A-Za-z0-9_.-]+)",
                        option.body,
                    )
                    referenced.extend(tooltip_keys)
                    if (
                        chain.effect_preview_policy == "explicit"
                        and self._option_has_mechanical_effect(option.body, chain)
                        and f"{option_key}_tt" not in tooltip_keys
                        and option_key not in chain.tooltip_exemptions
                    ):
                        findings.append(
                            (
                                f"{option_key} requires exact custom_effect_tooltip = {option_key}_tt",
                                option.file,
                                option.line,
                            )
                        )
                for key in referenced:
                    if key not in all_key_locations:
                        findings.append(
                            (
                                f"Missing English corporate-history localisation key {key}",
                                event.file,
                                event.line,
                            )
                        )
            for idea_id in chain.outcome_ideas:
                for key in (idea_id, f"{idea_id}_desc"):
                    if key not in all_key_locations:
                        findings.append(
                            (
                                f"Missing English outcome localisation key {key}",
                                "localisation/english",
                                0,
                            )
                        )
            for option_key, reason in chain.tooltip_exemptions.items():
                if not reason.strip():
                    findings.append(
                        (
                            f"Tooltip exemption {option_key} requires a reason",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
                if option_key not in seen_option_keys:
                    findings.append(
                        (
                            f"Tooltip exemption {option_key} does not match a visible option in {chain.namespace}",
                            "tools/corporate_history_contract.json",
                            0,
                        )
                    )
        return self._dedupe_findings(findings)

    def _option_has_mechanical_effect(self, body: str, chain: ChainConfig) -> bool:
        if any(
            token in body
            for token in (
                "modify_treasury_effect",
                "add_political_power",
                "add_stability",
                "add_war_support",
                "add_ideas",
                "remove_ideas",
                "add_tech_bonus",
                "add_research_slot",
            )
        ):
            return True
        return any(variable in body for variable in chain.variables)

    def _validate_economic_bridge(
        self,
        chains: Sequence[ChainConfig],
        event_defs: Dict[str, EventDef],
        effect_defs: Dict[str, List[BlockDef]],
    ) -> List[Tuple[str, str, int]]:
        immediate_chains = [
            chain for chain in chains if chain.bridge_refresh_policy == "immediate"
        ]
        if not immediate_chains:
            return []
        findings: List[Tuple[str, str, int]] = []
        update_defs = effect_defs.get(
            "USA_corporate_systems_update_economic_bridge", []
        )
        clear_defs = effect_defs.get(
            "USA_corporate_systems_clear_economic_bridge_ideas", []
        )
        rebuild_defs = effect_defs.get(
            "USA_corporate_systems_rebuild_company_contributions", []
        )
        if len(update_defs) != 1 or len(clear_defs) != 1 or len(rebuild_defs) != 1:
            return [
                (
                    "USA economic bridge requires exactly one update, clear, and contribution rebuild effect",
                    "common/scripted_effects/USA_corporate_systems_effects.txt",
                    0,
                )
            ]

        update = update_defs[0]
        thresholds = [
            int(value)
            for value in re.findall(
                r"USA_corporate_systems_economic_integration_score\s*<\s*(\d+)",
                update.body,
            )
        ]
        if thresholds != [15, 22, 29, 38]:
            findings.append(
                (
                    f"USA economic bridge thresholds must be 15, 22, 29, 38; found {thresholds}",
                    update.file,
                    update.line,
                )
            )
        expected_ideas = {
            f"USA_corporate_systems_economic_integration_{level}"
            for level in range(1, 6)
        }
        if set(_ADD_IDEA_RE.findall(update.body)) != expected_ideas:
            findings.append(
                (
                    "USA economic bridge update must select each of its five tier ideas",
                    update.file,
                    update.line,
                )
            )
        clear = clear_defs[0]
        if not all(idea in clear.body for idea in expected_ideas):
            findings.append(
                (
                    "USA economic bridge cleanup must remove all five tier ideas",
                    clear.file,
                    clear.line,
                )
            )
        if "corporate_history_enabled = yes" not in update.body or not all(
            marker in update.body
            for marker in (
                "USA_corporate_systems_clear_derived_axes = yes",
                "USA_corporate_systems_clear_economic_bridge_ideas = yes",
            )
        ):
            findings.append(
                (
                    "USA economic bridge must clear derived axes and tier ideas when corporate history is Off",
                    update.file,
                    update.line,
                )
            )

        contribution_axes = (
            "open_standards",
            "vertical_integration",
            "supply_resilience",
            "security_control",
            "national_compute_stack",
        )
        contribution_body = rebuild_defs[0].body
        for axis in contribution_axes:
            variable = f"USA_oem_contribution_{axis}"
            if not re.search(
                rf"\bset_temp_variable\s*=\s*\{{\s*{variable}\s*=\s*0\s*\}}",
                contribution_body,
            ):
                findings.append(
                    (
                        f"USA economic bridge must reset {variable} before accumulation",
                        rebuild_defs[0].file,
                        rebuild_defs[0].line,
                    )
                )
            if not re.search(
                rf"\bclamp_temp_variable\s*=\s*\{{\s*var\s*=\s*{variable}\s+min\s*=\s*-3\s+max\s*=\s*3\s*\}}",
                contribution_body,
            ):
                findings.append(
                    (
                        f"USA economic bridge must clamp {variable} to -3..3",
                        rebuild_defs[0].file,
                        rebuild_defs[0].line,
                    )
                )

        effective_defs = effect_defs.get(
            "USA_corporate_systems_rebuild_effective_axes", []
        )
        if len(effective_defs) != 1:
            findings.append(
                (
                    "USA economic bridge requires exactly one effective-axis rebuild effect",
                    "common/scripted_effects/USA_corporate_systems_effects.txt",
                    0,
                )
            )
        else:
            for axis in contribution_axes:
                variable = f"USA_oem_effective_{axis}"
                if not re.search(
                    rf"\bclamp_variable\s*=\s*\{{\s*var\s*=\s*{variable}\s+min\s*=\s*0\s+max\s*=\s*10\s*\}}",
                    effective_defs[0].body,
                ):
                    findings.append(
                        (
                            f"USA economic bridge must clamp {variable} to 0..10",
                            effective_defs[0].file,
                            effective_defs[0].line,
                        )
                    )

        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in immediate_chains:
            company = chain.root.split("_", 1)[-1]
            contribution_name = f"USA_corporate_systems_{company}_contribution"
            contribution = effect_lookup.get(contribution_name)
            if contribution is None:
                findings.append(
                    (
                        f"{chain.name} declares an immediate bridge refresh without {contribution_name}",
                        "common/scripted_effects/USA_corporate_systems_effects.txt",
                        0,
                    )
                )
                continue
            if (
                len(
                    re.findall(
                        rf"\b{re.escape(contribution_name)}\s*=\s*yes\b",
                        contribution_body,
                    )
                )
                != 1
            ):
                findings.append(
                    (
                        f"USA economic bridge must accumulate {contribution_name} exactly once",
                        rebuild_defs[0].file,
                        rebuild_defs[0].line,
                    )
                )
            contribution_tokens = set(
                re.findall(
                    r"\b(?:has_country_flag|has_idea)\s*=\s*([A-Za-z0-9_]+)",
                    contribution.body,
                )
            )
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + "."):
                    continue
                immediate_mutates = any(
                    self._body_writes_tokens(
                        immediate.body, contribution_tokens, effect_lookup
                    )
                    for immediate in event.immediates
                )
                immediate_refreshes = any(
                    self._body_reaches_effect(
                        immediate.body,
                        "USA_corporate_systems_update_economic_bridge",
                        effect_lookup,
                    )
                    for immediate in event.immediates
                )
                for option in event.options:
                    mutates_contribution = (
                        immediate_mutates
                        or self._body_writes_tokens(
                            option.body, contribution_tokens, effect_lookup
                        )
                    )
                    if (
                        mutates_contribution
                        and not immediate_refreshes
                        and not self._body_reaches_effect(
                            option.body,
                            "USA_corporate_systems_update_economic_bridge",
                            effect_lookup,
                        )
                    ):
                        findings.append(
                            (
                                f"{event.event_id} changes a USA bridge contribution without an immediate refresh",
                                option.file,
                                option.line,
                            )
                        )
        return self._dedupe_findings(findings)

    def _body_reaches_effect(
        self,
        body: str,
        target: str,
        effect_lookup: Mapping[str, BlockDef],
        seen: FrozenSet[str] = frozenset(),
    ) -> bool:
        for match in _EFFECT_YES_RE.finditer(body):
            name = match.group(1)
            if name == target:
                return True
            if name in seen or name not in effect_lookup:
                continue
            if self._body_reaches_effect(
                effect_lookup[name].body, target, effect_lookup, seen | {name}
            ):
                return True
        return False

    def _body_writes_tokens(
        self,
        body: str,
        tokens: Iterable[str],
        effect_lookup: Mapping[str, BlockDef],
        seen: FrozenSet[str] = frozenset(),
    ) -> bool:
        for token in tokens:
            escaped = re.escape(token)
            if re.search(
                rf"\b(?:set_country_flag|clr_country_flag|add_ideas|remove_ideas)\s*=\s*(?:\{{[^}}]*\b)?{escaped}\b",
                body,
                re.DOTALL,
            ) or re.search(
                rf"\b(?:set_variable|add_to_variable|subtract_from_variable|multiply_variable|divide_variable)\s*=\s*\{{\s*{escaped}\s*=",
                body,
            ):
                return True
        for match in _EFFECT_YES_RE.finditer(body):
            name = match.group(1)
            if name in seen or name not in effect_lookup:
                continue
            if self._body_writes_tokens(
                effect_lookup[name].body, tokens, effect_lookup, seen | {name}
            ):
                return True
        return False

    def _find_event_calls(
        self, text: str, base_line: int, tracked_ids: Iterable[str]
    ) -> List[Tuple[str, int]]:
        tracked = set(tracked_ids)
        results: List[Tuple[str, int]] = []
        for match in _EVENT_SHORT_CALL_RE.finditer(text):
            target = match.group(1)
            if tracked and target not in tracked:
                continue
            results.append((target, base_line + self._line(text, match.start()) - 1))
        for match in _EVENT_LONG_CALL_RE.finditer(text):
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                continue
            id_match = _ID_RE.search(body)
            if not id_match:
                continue
            target = id_match.group(1)
            if tracked and target not in tracked:
                continue
            results.append((target, base_line + self._line(text, match.start()) - 1))
        return results

    def _event_namespaces_in_text(self, text: str) -> Set[str]:
        namespaces = set()
        for target, _line in self._find_event_calls(text, 1, frozenset()):
            if "." in target:
                namespaces.add(target.split(".", 1)[0])
        return namespaces

    def _nested_blocks(
        self,
        text: str,
        pattern: re.Pattern[str],
        owner: str,
        file: str,
        base_line: int,
    ) -> List[BlockDef]:
        blocks = []
        for match in pattern.finditer(text):
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                continue
            blocks.append(
                BlockDef(
                    owner,
                    file,
                    base_line + self._line(text, match.start()) - 1,
                    body,
                )
            )
        return blocks

    def _require_effect(
        self, effect_defs: Dict[str, List[BlockDef]], effect_name: str, message: str
    ) -> List[Tuple[str, str, int]]:
        if effect_name in effect_defs:
            return []
        return [(message, f"common/scripted_effects/{effect_name}.txt", 0)]

    def _dedupe_callers(self, callers: Sequence[CallSite]) -> List[CallSite]:
        by_key: Dict[str, CallSite] = {}
        for caller in callers:
            by_key.setdefault(caller.key, caller)
        return list(by_key.values())

    def _multiple_callers_allowed(
        self, chain: ChainConfig, event_id: str, callers: Sequence[CallSite]
    ) -> bool:
        if event_id in chain.allowed_multiple_callers:
            return True
        if not chain.allow_yearly_scheduler_duplicates:
            return False
        owners = {caller.owner for caller in callers if caller.kind == "effect"}
        if len(owners) != len(callers):
            return False
        if chain.scheduler_effect not in owners:
            return False
        yearly = [owner for owner in owners if "_corporate_trigger_year_" in owner]
        return len(yearly) == 1 and len(owners) == 2

    def _effect_call_counts(
        self, effect_defs: Dict[str, List[BlockDef]], targets: Sequence[str]
    ) -> Dict[str, List[Tuple[str, int, str]]]:
        target_set = set(targets)
        counts: Dict[str, List[Tuple[str, int, str]]] = {name: [] for name in targets}
        for defs in effect_defs.values():
            for effect in defs:
                for match in _EFFECT_YES_RE.finditer(effect.body):
                    name = match.group(1)
                    if name in target_set:
                        counts[name].append(
                            (
                                effect.file,
                                effect.line
                                + self._line(effect.body, match.start())
                                - 1,
                                effect.name,
                            )
                        )
        return counts

    def _flag_is_produced(
        self, flag: str, effect_defs: Dict[str, List[BlockDef]]
    ) -> bool:
        return bool(self._flag_producers(flag, effect_defs))

    def _flag_producers(
        self, flag: str, effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, int]]:
        producers = []
        pattern = re.compile(r"\bset_country_flag\s*=\s*" + re.escape(flag) + r"\b")
        for defs in effect_defs.values():
            for effect in defs:
                for match in pattern.finditer(effect.body):
                    producers.append(
                        (
                            effect.file,
                            effect.line + self._line(effect.body, match.start()) - 1,
                        )
                    )
        return producers

    def _monthly_consumers(
        self, flag: str, effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, int]]:
        consumers = []
        pattern = re.compile(re.escape(flag))
        for name, defs in effect_defs.items():
            if not name.endswith("_corporate_history_monthly_outcomes"):
                continue
            for effect in defs:
                for match in pattern.finditer(effect.body):
                    consumers.append(
                        (
                            effect.file,
                            effect.line + self._line(effect.body, match.start()) - 1,
                        )
                    )
                    break
        return consumers

    def _event_definition_sites(
        self, tracked: FrozenSet[str]
    ) -> Dict[str, List[Tuple[str, int]]]:
        sites: Dict[str, List[Tuple[str, int]]] = {event_id: [] for event_id in tracked}
        for filepath in self._collect_text_files(["events/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            for match in _EVENT_DEF_RE.finditer(text):
                body, end = extract_block_from_text(text, match.end() - 1)
                if end == -1:
                    continue
                id_match = _ID_RE.search(body)
                if id_match and id_match.group(1) in tracked:
                    sites[id_match.group(1)].append(
                        (self._relpath(filepath), self._line(text, match.start()))
                    )
        return sites

    def _oem_startup_country_branches(
        self, body: str, tag: str
    ) -> List[Tuple[str, str]]:
        country_exists = re.compile(rf"\bcountry_exists\s*=\s*{re.escape(tag)}\b")
        branches: List[Tuple[str, str]] = []
        for child, _start, _end, branch in self._iter_direct_child_blocks(body):
            if child not in ("if", "else_if"):
                continue
            limit = self._direct_child_block(branch, "limit") or ""
            if country_exists.search(limit):
                scope = self._direct_child_block(branch, tag)
                if scope is not None:
                    branches.append((limit, scope))
        return branches

    def _country_scopes_in_branches(self, body: str, tag: str) -> List[str]:
        scopes: List[str] = []
        country_exists = re.compile(rf"\bcountry_exists\s*=\s*{re.escape(tag)}\b")
        for child, _start, _end, branch in self._iter_direct_child_blocks(body):
            if child not in ("if", "else_if"):
                continue
            limit = self._direct_child_block(branch, "limit") or ""
            scope = self._direct_child_block(branch, tag)
            if country_exists.search(limit) and scope is not None:
                scopes.append(scope)
        return scopes

    def _is_exact_country_exists_limit(self, limit: str, tag: str) -> bool:
        return bool(
            re.fullmatch(rf"\s*country_exists\s*=\s*{re.escape(tag)}\s*", limit)
        )

    def _is_exact_yes_trigger(self, limit: str, trigger: str) -> bool:
        return self._direct_has_exact_clauses(
            limit, (rf"\b{re.escape(trigger)}\s*=\s*yes\b",)
        )

    def _is_exact_dell_2000_full_limit(self, limit: str) -> bool:
        return self._direct_has_exact_clauses(
            limit,
            (
                r"\bdate\s*<\s*2001\.1\.1\b",
                r"\bcorporate_history_full_enabled\s*=\s*yes\b",
            ),
        )

    def _direct_has_exact_clauses(
        self, text: str, patterns: Sequence[str], allow_blocks: bool = False
    ) -> bool:
        if not allow_blocks and list(self._iter_direct_child_blocks(text)):
            return False
        residual = self._direct_block_text(text)
        for pattern in patterns:
            residual, count = re.subn(pattern, "", residual, count=1)
            if count != 1 or re.search(pattern, residual):
                return False
        return not residual.strip()

    def _exact_not_terms(self, text: str, expected: Iterable[str]) -> bool:
        children = list(self._iter_direct_child_blocks(text))
        if any(name.upper() != "NOT" for name, _s, _e, _body in children):
            return False
        actual = [" ".join(body.split()) for _name, _s, _e, body in children]
        return sorted(actual) == sorted(expected)

    def _is_exact_hp_2000_limit(self, limit: str) -> bool:
        return bool(
            self._direct_has_exact_clauses(
                limit,
                (
                    r"\bcountry_exists\s*=\s*USA\b",
                    r"\bhas_start_date\s*<\s*2000\.1\.2\b",
                ),
                allow_blocks=True,
            )
            and self._exact_not_terms(limit, ("has_start_date < 2000.1.1",))
        )

    def _is_exact_e3_2000_limit(self, limit: str) -> bool:
        return bool(
            self._direct_has_exact_clauses(
                limit,
                (r"\bhas_start_date\s*<\s*2000\.1\.2\b",),
                allow_blocks=True,
            )
            and self._exact_not_terms(
                limit,
                (
                    "has_start_date < 2000.1.1",
                    "has_country_flag = USA_e3_opening_context_seen",
                ),
            )
        )

    def _is_exact_ibm_queue_limit(
        self, limit: str, scheduled_flag: str, resolved_flag: str
    ) -> bool:
        return bool(
            not self._direct_block_text(limit).strip()
            and self._exact_not_terms(
                limit,
                (
                    f"has_country_flag = {scheduled_flag}",
                    f"has_country_flag = {resolved_flag}",
                ),
            )
        )

    def _scheduler_has_replay_guard(
        self, scheduler: BlockDef, event_id: str, scheduled_flag: str
    ) -> bool:
        candidates = [
            (end, body)
            for name, _start, end, body in self._iter_direct_child_blocks(
                scheduler.body
            )
            if name == "if" and self._event_delays_in_body(body, event_id)
        ]
        if len(candidates) != 1:
            return False
        outer_end, outer_body = candidates[0]
        limit = self._direct_child_block(outer_body, "limit") or ""
        if not self._is_exact_country_flag_guard(limit, scheduled_flag):
            return False
        pattern = re.compile(rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b")
        clear_pattern = re.compile(
            rf"\bclr_country_flag\s*=\s*{re.escape(scheduled_flag)}\b"
        )
        all_sets = list(pattern.finditer(scheduler.body))
        direct_sets = list(pattern.finditer(self._direct_block_text(scheduler.body)))
        return bool(
            len(all_sets) == 1
            and len(direct_sets) == 1
            and all_sets[0].start() >= outer_end
            and not clear_pattern.search(scheduler.body)
        )

    def _is_exact_country_flag_guard(self, limit: str, flag: str) -> bool:
        children = list(self._iter_direct_child_blocks(limit))
        if len(children) != 1 or children[0][0].upper() != "NOT":
            return False
        return bool(
            not self._direct_block_text(limit).strip()
            and re.fullmatch(
                rf"\s*has_country_flag\s*=\s*{re.escape(flag)}\s*",
                children[0][3],
            )
        )

    def _is_exact_gpu_2000_limit(self, limit: str) -> bool:
        if not self._direct_has_exact_clauses(
            limit,
            (r"\bhas_start_date\s*<\s*2000\.1\.2\b",),
            allow_blocks=True,
        ):
            return False
        not_terms: List[str] = []
        owner_sets: List[Set[str]] = []
        for name, _start, _end, body in self._iter_direct_child_blocks(limit):
            upper = name.upper()
            if upper == "NOT" and not list(self._iter_direct_child_blocks(body)):
                not_terms.append(" ".join(body.split()))
                continue
            if upper == "OR" and not list(self._iter_direct_child_blocks(body)):
                tags = re.findall(r"\boriginal_tag\s*=\s*([A-Z]{3})\b", body)
                residual = re.sub(r"\boriginal_tag\s*=\s*[A-Z]{3}\b", "", body)
                if residual.strip() or len(tags) != len(set(tags)):
                    return False
                owner_sets.append(set(tags))
                continue
            return False
        return bool(
            sorted(not_terms)
            == sorted(
                (
                    "has_country_flag = collapsed_nation",
                    "has_start_date < 2000.1.1",
                    "has_country_flag = gpu_development_1_resolved",
                )
            )
            and owner_sets == [{"USA", "CAN", "TAI"}]
        )

    def _is_exact_global_flag_guard(self, limit: str, flag: str) -> bool:
        children = list(self._iter_direct_child_blocks(limit))
        if len(children) != 1 or children[0][0].upper() != "NOT":
            return False
        if self._direct_block_text(limit).strip():
            return False
        not_body = children[0][3]
        return bool(
            re.fullmatch(rf"\s*has_global_flag\s*=\s*{re.escape(flag)}\s*", not_body)
        )

    def _direct_block_text(self, body: str) -> str:
        residual: List[str] = []
        cursor = 0
        for _child, start, end, _nested in self._iter_direct_child_blocks(body):
            residual.append(body[cursor:start])
            cursor = end
        residual.append(body[cursor:])
        return "".join(residual)

    def _event_delays_in_body(self, body: str, event_id: str) -> List[int]:
        delays: List[int] = []
        for match in _EVENT_LONG_CALL_RE.finditer(body):
            call, end = extract_block_from_text(body, match.end() - 1)
            if end == -1:
                continue
            id_match = _ID_RE.search(call)
            if not id_match or id_match.group(1) != event_id:
                continue
            days_match = re.search(r"\bdays\s*=\s*(\d+)\b", call)
            if days_match:
                delays.append(int(days_match.group(1)))
        return delays

    def _direct_event_calls(
        self, body: str, event_id: str
    ) -> List[Tuple[int, Optional[int]]]:
        calls: List[Tuple[int, Optional[int]]] = []
        for child, start, _end, call in self._iter_direct_child_blocks(body):
            if child not in _EVENT_KEYWORDS:
                continue
            id_match = _ID_RE.search(call)
            if not id_match or id_match.group(1) != event_id:
                continue
            days_match = re.search(r"\bdays\s*=\s*(\d+)\b", call)
            calls.append((start, int(days_match.group(1)) if days_match else None))
        short_pattern = re.compile(
            rf"\b(?:{_EVENT_ALT})\s*=\s*{re.escape(event_id)}\b(?!\s*\{{)"
        )
        direct_text = self._direct_block_text(body)
        for match in short_pattern.finditer(direct_text):
            calls.append((match.start(), None))
        return calls

    def _event_guard_branches(self, body: str, event_id: str) -> List[str]:
        branches: List[str] = []
        for child, _start, _end, branch in self._iter_direct_child_blocks(body):
            if child not in ("if", "else_if"):
                continue
            if self._direct_event_calls(branch, event_id):
                branches.append(branch)
            branches.extend(self._event_guard_branches(branch, event_id))
        return branches

    def _has_direct_negated_country_flag(self, trigger: str, flag: str) -> bool:
        for child, _start, _end, body in self._iter_direct_child_blocks(trigger):
            if child.upper() != "NOT":
                continue
            if re.fullmatch(rf"\s*has_country_flag\s*=\s*{re.escape(flag)}\s*", body):
                return True
        return False

    def _event_is_owned_and_collapse_guarded(
        self, event: Optional[EventDef], tag: str
    ) -> bool:
        if event is None:
            return False
        trigger = self._direct_child_block(event.body, "trigger")
        if trigger is None:
            return False
        return bool(
            self._has_positive_original_tag(trigger, tag)
            and self._has_direct_negated_country_flag(trigger, "collapsed_nation")
        )

    def _event_matches_exact_trigger(
        self,
        event: Optional[EventDef],
        direct_clauses: Sequence[str],
        negated_terms: Sequence[str],
    ) -> bool:
        if event is None:
            return False
        trigger = self._direct_child_block(event.body, "trigger")
        if trigger is None:
            return False
        return bool(
            self._direct_has_exact_clauses(trigger, direct_clauses, allow_blocks=True)
            and self._exact_not_terms(trigger, negated_terms)
        )

    def _gpu_event_matches_exact_trigger(self, event: Optional[EventDef]) -> bool:
        if event is None:
            return False
        trigger = self._direct_child_block(event.body, "trigger")
        if trigger is None or self._direct_block_text(trigger).strip():
            return False
        not_terms: List[str] = []
        owners: List[Set[str]] = []
        for name, _start, _end, body in self._iter_direct_child_blocks(trigger):
            upper = name.upper()
            if upper == "NOT" and not list(self._iter_direct_child_blocks(body)):
                not_terms.append(" ".join(body.split()))
                continue
            if upper == "OR" and not list(self._iter_direct_child_blocks(body)):
                tags = re.findall(r"\boriginal_tag\s*=\s*([A-Z]{3})\b", body)
                residual = re.sub(r"\boriginal_tag\s*=\s*[A-Z]{3}\b", "", body)
                if residual.strip() or len(tags) != len(set(tags)):
                    return False
                owners.append(set(tags))
                continue
            return False
        return bool(
            sorted(not_terms)
            == sorted(
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = gpu_development_1_resolved",
                )
            )
            and owners == [{"USA", "CAN", "TAI"}]
        )

    def _has_positive_original_tag(
        self, trigger: str, tag: str, negated: bool = False
    ) -> bool:
        direct = self._direct_block_text(trigger)
        if not negated and re.search(
            rf"\boriginal_tag\s*=\s*{re.escape(tag)}\b", direct
        ):
            return True
        for name, _start, _end, body in self._iter_direct_child_blocks(trigger):
            upper = name.upper()
            if upper == "NOT":
                if self._has_positive_original_tag(body, tag, not negated):
                    return True
            elif upper in ("AND", "OR") and self._has_positive_original_tag(
                body, tag, negated
            ):
                return True
        return False

    def _validate_usa_2000_startup_schedule(
        self,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        bootstrap: Optional[BlockDef],
        startup: Optional[BlockDef],
        full_branch: str,
        full_usa_body: str,
    ) -> List[Tuple[str, str, int]]:
        findings: List[Tuple[str, str, int]] = []

        def sole_effect(name: str) -> Optional[BlockDef]:
            definitions = effect_defs.get(name, [])
            if len(definitions) != 1:
                findings.append(
                    (
                        f"USA 2000 startup schedule requires exactly one {name}; found {len(definitions)}",
                        "common/scripted_effects",
                        definitions[0].line if definitions else 0,
                    )
                )
                return None
            return definitions[0]

        gpu_scheduler = sole_effect("gpu_development_schedule_current_year_events")
        ibm_scheduler = sole_effect("USA_ibm_schedule_prehistory")
        e3_scheduler = sole_effect("USA_e3_schedule_current_year_events")
        scheduled_flag_owners = {
            "gpu_development_start_year_events_scheduled": gpu_scheduler,
            "USA_e3_start_year_events_scheduled": e3_scheduler,
            "USA_ibm_event_12_scheduled": ibm_scheduler,
            "USA_ibm_event_13_scheduled": ibm_scheduler,
        }
        scheduled_flag_writes = self._country_flag_write_sites(scheduled_flag_owners)
        for flag, owner in scheduled_flag_owners.items():
            sets, clears = scheduled_flag_writes[flag]
            expected_file = owner.file.replace("\\", "/") if owner else ""
            actual_files = [path.replace("\\", "/") for path, _line in sets]
            if len(sets) != 1 or actual_files != [expected_file] or clears:
                rendered_sets = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}" for path, line in sets
                )
                rendered_clears = ", ".join(
                    f"{path.replace(os.sep, '/')}:{line}" for path, line in clears
                )
                findings.append(
                    (
                        f"{flag} must be set only by {owner.name if owner else 'its scheduler'} and never cleared; sets {rendered_sets or 'none'}, clears {rendered_clears or 'none'}",
                        owner.file if owner else "common/scripted_effects",
                        owner.line if owner else 0,
                    )
                )
        for scheduler, event_id, scheduled_flag in (
            (
                gpu_scheduler,
                "gpu_development.1",
                "gpu_development_start_year_events_scheduled",
            ),
            (
                e3_scheduler,
                "USA_e3_events.1",
                "USA_e3_start_year_events_scheduled",
            ),
        ):
            if scheduler and not self._scheduler_has_replay_guard(
                scheduler, event_id, scheduled_flag
            ):
                findings.append(
                    (
                        f"{scheduler.name} must guard all start-year queues with {scheduled_flag} and set it directly after dispatch",
                        scheduler.file,
                        scheduler.line,
                    )
                )
        for scheduler, event_id in (
            (gpu_scheduler, "gpu_development.1"),
            (e3_scheduler, "USA_e3_events.1"),
        ):
            if scheduler and self._scheduler_window_years(scheduler, event_id) != {
                2000
            }:
                findings.append(
                    (
                        f"{scheduler.name} must schedule {event_id} only in the 2000 January 1 window",
                        scheduler.file,
                        scheduler.line,
                    )
                )

        if gpu_scheduler:
            gpu_branches = self._event_guard_branches(
                gpu_scheduler.body, "gpu_development.1"
            )
            gpu_guard_valid = False
            if len(gpu_branches) == 1:
                gpu_limit = self._direct_child_block(gpu_branches[0], "limit") or ""
                gpu_guard_valid = bool(
                    self._is_exact_gpu_2000_limit(gpu_limit)
                    and self._has_positive_original_tag(gpu_limit, "USA")
                )
            if not gpu_guard_valid:
                findings.append(
                    (
                        "gpu_development.1 must be directly scheduled by one exact 2000 window that permits USA and excludes collapsed nations",
                        gpu_scheduler.file,
                        gpu_scheduler.line,
                    )
                )

        if e3_scheduler:
            e3_branches = self._event_guard_branches(
                e3_scheduler.body, "USA_e3_events.1"
            )
            e3_limit = (
                self._direct_child_block(e3_branches[0], "limit") or ""
                if len(e3_branches) == 1
                else ""
            )
            if len(e3_branches) != 1 or not self._is_exact_e3_2000_limit(e3_limit):
                findings.append(
                    (
                        "USA_e3_events.1 must be directly scheduled by one exact 2000 January 1 window",
                        e3_scheduler.file,
                        e3_scheduler.line,
                    )
                )

        sources = {
            "USA_oem_events.13": (bootstrap, bootstrap.body if bootstrap else "", 90),
            "gpu_development.1": (
                gpu_scheduler,
                gpu_scheduler.body if gpu_scheduler else "",
                110,
            ),
            "USA_ibm_events.90": (
                startup,
                full_usa_body,
                1,
            ),
            "USA_e3_events.90": (
                startup,
                full_usa_body,
                1,
            ),
            "USA_hp_events.1": (
                startup,
                full_usa_body,
                153,
            ),
            "USA_ibm_events.12": (
                ibm_scheduler,
                ibm_scheduler.body if ibm_scheduler else "",
                30,
            ),
            "USA_ibm_events.13": (
                ibm_scheduler,
                ibm_scheduler.body if ibm_scheduler else "",
                120,
            ),
            "USA_e3_events.1": (
                e3_scheduler,
                e3_scheduler.body if e3_scheduler else "",
                131,
            ),
        }
        delays: Dict[str, int] = {}
        for event_id, (owner, body, expected_delay) in sources.items():
            actual_delays = self._event_delays_in_body(body, event_id)
            if actual_delays != [expected_delay]:
                findings.append(
                    (
                        f"USA 2000 startup schedule requires {event_id} at days = {expected_delay}; found {', '.join(str(value) for value in actual_delays) or 'none'}",
                        owner.file if owner else "common/scripted_effects",
                        owner.line if owner else 0,
                    )
                )
            if len(actual_delays) == 1:
                delays[event_id] = actual_delays[0]

        ibm_anchor = event_defs.get("USA_ibm_events.90")
        ibm_early_branch = False
        if ibm_anchor:
            for immediate in ibm_anchor.immediates:
                for child, _start, _end, body in self._iter_direct_child_blocks(
                    immediate.body
                ):
                    limit = self._direct_child_block(body, "limit") or ""
                    if (
                        child == "if"
                        and self._direct_has_exact_clauses(
                            limit, (r"\bdate\s*<\s*2000\.2\.1\b",)
                        )
                        and "USA_ibm_initialize_state = yes"
                        in self._direct_block_text(body)
                        and "USA_ibm_schedule_prehistory = yes"
                        in self._direct_block_text(body)
                    ):
                        ibm_early_branch = True
        if not ibm_early_branch:
            findings.append(
                (
                    "USA_ibm_events.90 does not initialize IBM and call its prehistory scheduler on an early-2000 start",
                    ibm_anchor.file if ibm_anchor else "events/USA_ibm_events.txt",
                    ibm_anchor.line if ibm_anchor else 0,
                )
            )

        e3_anchor = event_defs.get("USA_e3_events.90")
        e3_immediate = (
            "\n".join(
                self._direct_block_text(immediate.body)
                for immediate in e3_anchor.immediates
            )
            if e3_anchor
            else ""
        )
        if not (
            len(re.findall(r"\bUSA_e3_reconstruct_history\s*=\s*yes\b", e3_immediate))
            == 1
            and len(
                re.findall(
                    r"\bUSA_e3_schedule_current_year_events\s*=\s*yes\b",
                    e3_immediate,
                )
            )
            == 1
        ):
            findings.append(
                (
                    "USA_e3_events.90 does not reconstruct E3 and call its current-year scheduler",
                    e3_anchor.file if e3_anchor else "events/USA_e3_events.txt",
                    e3_anchor.line if e3_anchor else 0,
                )
            )

        trigger_contracts = {
            "USA_oem_events.13": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
            "USA_ibm_events.12": (
                (
                    r"\boriginal_tag\s*=\s*USA\b",
                    r"\bhas_country_flag\s*=\s*USA_ibm_event_12_scheduled\b",
                ),
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = USA_ibm_event_12_resolved",
                ),
            ),
            "USA_ibm_events.13": (
                (
                    r"\boriginal_tag\s*=\s*USA\b",
                    r"\bhas_country_flag\s*=\s*USA_ibm_event_13_scheduled\b",
                ),
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = USA_ibm_event_13_resolved",
                ),
            ),
            "USA_ibm_events.90": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
            "USA_e3_events.1": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                (
                    "has_country_flag = collapsed_nation",
                    "has_country_flag = USA_e3_opening_context_seen",
                ),
            ),
            "USA_e3_events.90": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
            "USA_hp_events.1": (
                (r"\boriginal_tag\s*=\s*USA\b",),
                ("has_country_flag = collapsed_nation",),
            ),
        }
        for event_id, (direct_clauses, negated_terms) in trigger_contracts.items():
            event = event_defs.get(event_id)
            if event and not self._event_matches_exact_trigger(
                event, direct_clauses, negated_terms
            ):
                findings.append(
                    (
                        f"{event_id} must retain its exact viable USA 2000 trigger contract",
                        event.file,
                        event.line,
                    )
                )

        gpu_event = event_defs.get("gpu_development.1")
        if gpu_event and not self._gpu_event_matches_exact_trigger(gpu_event):
            findings.append(
                (
                    "gpu_development.1 must retain its exact viable 2000 owner and replay trigger contract",
                    gpu_event.file,
                    gpu_event.line,
                )
            )

        if ibm_scheduler:
            for number in (12, 13):
                event_id = f"USA_ibm_events.{number}"
                scheduled_flag = f"USA_ibm_event_{number}_scheduled"
                resolved_flag = f"USA_ibm_event_{number}_resolved"
                branches = self._event_guard_branches(ibm_scheduler.body, event_id)
                valid_branch = False
                if len(branches) == 1:
                    branch = branches[0]
                    limit = self._direct_child_block(branch, "limit") or ""
                    direct = self._direct_block_text(branch)
                    set_match = re.search(
                        rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                        direct,
                    )
                    direct_set_count = len(
                        re.findall(
                            rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                            direct,
                        )
                    )
                    calls = self._direct_event_calls(branch, event_id)
                    event_position = calls[0][0] if len(calls) == 1 else -1
                    before_event = (
                        self._direct_block_text(branch[:event_position])
                        if event_position >= 0
                        else ""
                    )
                    before_set_count = len(
                        re.findall(
                            rf"\bset_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                            before_event,
                        )
                    )
                    valid_branch = bool(
                        set_match
                        and direct_set_count == 1
                        and before_set_count == 1
                        and event_position >= 0
                        and self._is_exact_ibm_queue_limit(
                            limit, scheduled_flag, resolved_flag
                        )
                    )
                if not valid_branch:
                    findings.append(
                        (
                            f"{event_id} must set {scheduled_flag} directly before queueing under scheduled/resolved replay guards",
                            ibm_scheduler.file,
                            ibm_scheduler.line,
                        )
                    )

                event = event_defs.get(event_id)
                trigger = (
                    self._direct_child_block(event.body, "trigger") if event else None
                )
                trigger_direct = self._direct_block_text(trigger or "")
                resolved_direct = (
                    "\n".join(
                        self._direct_block_text(immediate.body)
                        for immediate in event.immediates
                    )
                    if event
                    else ""
                )
                if not re.search(
                    rf"\bhas_country_flag\s*=\s*{re.escape(scheduled_flag)}\b",
                    trigger_direct,
                ) or not re.search(
                    rf"\bset_country_flag\s*=\s*{re.escape(resolved_flag)}\b",
                    resolved_direct,
                ):
                    findings.append(
                        (
                            f"{event_id} must consume {scheduled_flag} and directly set {resolved_flag}",
                            event.file if event else "events/USA_ibm_events.txt",
                            event.line if event else 0,
                        )
                    )

        hp_guarded = False
        for limit, scope in self._oem_startup_country_branches(full_branch, "USA"):
            hp_calls = self._direct_event_calls(scope, "USA_hp_events.1")
            if (
                len(hp_calls) == 1
                and hp_calls[0][1] == 153
                and self._is_exact_hp_2000_limit(limit)
            ):
                hp_guarded = True
        if full_branch and not hp_guarded:
            findings.append(
                (
                    "USA_hp_events.1 is not guarded to the exact 2000.1.1 bookmark",
                    startup.file if startup else "common/scripted_effects",
                    startup.line if startup else 0,
                )
            )

        if len(delays) == len(sources):
            start = date(2000, 1, 1)
            ibm_anchor_date = start + timedelta(days=delays["USA_ibm_events.90"])
            e3_anchor_date = start + timedelta(days=delays["USA_e3_events.90"])
            actual_schedule = {
                "USA_ibm_events.90": ibm_anchor_date,
                "USA_e3_events.90": e3_anchor_date,
                "USA_ibm_events.12": ibm_anchor_date
                + timedelta(days=delays["USA_ibm_events.12"]),
                "USA_oem_events.13": start
                + timedelta(days=delays["USA_oem_events.13"]),
                "gpu_development.1": start
                + timedelta(days=delays["gpu_development.1"]),
                "USA_ibm_events.13": ibm_anchor_date
                + timedelta(days=delays["USA_ibm_events.13"]),
                "USA_e3_events.1": e3_anchor_date
                + timedelta(days=delays["USA_e3_events.1"]),
                "USA_hp_events.1": start + timedelta(days=delays["USA_hp_events.1"]),
            }
            expected_schedule = {
                "USA_ibm_events.90": date(2000, 1, 2),
                "USA_e3_events.90": date(2000, 1, 2),
                "USA_ibm_events.12": date(2000, 2, 1),
                "USA_oem_events.13": date(2000, 3, 31),
                "gpu_development.1": date(2000, 4, 20),
                "USA_ibm_events.13": date(2000, 5, 1),
                "USA_e3_events.1": date(2000, 5, 12),
                "USA_hp_events.1": date(2000, 6, 2),
            }
            for event_id, expected_date in expected_schedule.items():
                if actual_schedule[event_id] != expected_date:
                    findings.append(
                        (
                            f"USA 2000 startup schedule resolves {event_id} on {actual_schedule[event_id].isoformat()}; expected {expected_date.isoformat()}",
                            (
                                sources[event_id][0].file
                                if sources[event_id][0]
                                else "common/scripted_effects"
                            ),
                            sources[event_id][0].line if sources[event_id][0] else 0,
                        )
                    )

        return findings

    def _startup_full_branch(self, startup_body: str) -> str:
        """The Full-rule arm of corporate_history_on_startup, or an empty string.

        Outcomes Only always reconstructs; only the Full arm proves a later start
        still catches its chain up without the hidden .90 anchor.
        """
        for name, _start, _end, body in self._iter_direct_child_blocks(startup_body):
            if name != "if":
                continue
            limit = self._direct_child_block(body, "limit")
            if limit and self._is_exact_yes_trigger(
                limit, "corporate_history_full_enabled"
            ):
                return body
        return ""

    def _startup_outcomes_branch(self, startup_body: str) -> str:
        for name, _start, _end, body in self._iter_direct_child_blocks(startup_body):
            if name != "else_if":
                continue
            limit = self._direct_child_block(body, "limit")
            if limit and self._is_exact_yes_trigger(
                limit, "corporate_history_outcomes_only_enabled"
            ):
                return body
        return ""

    def _startup_reaches_scheduler(
        self, chain: ChainConfig, startup_body: str, event_defs: Dict[str, EventDef]
    ) -> bool:
        if f"{chain.scheduler_effect} = yes" in startup_body:
            return True
        anchor = event_defs.get(chain.hidden_ninety_id)
        if anchor is None or chain.hidden_ninety_id not in startup_body:
            return False
        return any(
            f"{chain.scheduler_effect} = yes" in immediate.body
            for immediate in anchor.immediates
        )

    def _script_effect_call_sites(self, effect_name: str) -> List[Tuple[str, int]]:
        if self._effect_call_parents_cache is None:
            effect_defs = self._load_top_level_blocks(
                ["common/scripted_effects/**/*.txt"]
            )
            self._effect_call_parents_cache = self._effect_call_parents(effect_defs)
            self._effect_call_children_cache = self._effect_call_children(effect_defs)
        parents = self._effect_call_parents_cache
        children = self._effect_call_children_cache or {}

        reachable = {effect_name}
        pending = [effect_name]
        while pending:
            target = pending.pop()
            for parent in parents.get(target, set()):
                if parent in reachable:
                    continue
                reachable.add(parent)
                pending.append(parent)

        callers: List[Tuple[str, int, str, int]] = []
        if self._on_action_texts_cache is None:
            self._on_action_texts_cache = []
            for filepath in self._collect_text_files(["common/on_actions/**/*.txt"]):
                try:
                    text = strip_comments(
                        Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                    )
                except OSError:
                    continue
                self._on_action_texts_cache.append((filepath, text))
        on_action_texts = self._on_action_texts_cache
        for filepath, text in on_action_texts:
            rel = self._relpath(filepath)
            for name in reachable:
                pattern = re.compile(rf"\b{re.escape(name)}\s*=\s*yes\b")
                path_count = self._effect_path_count(name, effect_name, children)
                for match in pattern.finditer(text):
                    callers.extend(
                        (rel, self._line(text, match.start()), name, match.start())
                        for _path in range(path_count)
                    )
        return [(path, line) for path, line, _name, _offset in sorted(callers)]

    def _effect_call_parents(
        self, effect_defs: Dict[str, List[BlockDef]]
    ) -> Dict[str, Set[str]]:
        parents: Dict[str, Set[str]] = {}
        for owner, definitions in effect_defs.items():
            for definition in definitions:
                for match in _EFFECT_YES_RE.finditer(definition.body):
                    parents.setdefault(match.group(1), set()).add(owner)
        return parents

    def _effect_call_children(
        self, effect_defs: Dict[str, List[BlockDef]]
    ) -> Dict[str, List[str]]:
        effect_names = set(effect_defs)
        children: Dict[str, List[str]] = {}
        for owner, definitions in effect_defs.items():
            for definition in definitions:
                for match in _EFFECT_YES_RE.finditer(definition.body):
                    child = match.group(1)
                    if child in effect_names:
                        children.setdefault(owner, []).append(child)
        return children

    def _effect_path_count(
        self,
        source: str,
        target: str,
        children: Dict[str, List[str]],
        visiting: Optional[FrozenSet[str]] = None,
    ) -> int:
        if source == target:
            return 1
        active = visiting or frozenset()
        if source in active:
            return 0
        active = active | {source}
        count = 0
        for child in children.get(source, []):
            count += self._effect_path_count(child, target, children, active)
            if count >= 2:
                return 2
        return count

    def _mixed_script_descendants(
        self,
        body: str,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
    ) -> Tuple[Set[str], Set[str]]:
        reachable_effects: Set[str] = set()
        reachable_events: Set[str] = set()
        pending_bodies = [body]
        while pending_bodies:
            current = pending_bodies.pop()
            for match in _EFFECT_YES_RE.finditer(current):
                name = match.group(1)
                if name in reachable_effects or name not in effect_defs:
                    continue
                reachable_effects.add(name)
                pending_bodies.extend(
                    definition.body for definition in effect_defs[name]
                )
            for event_id, _line in self._find_event_calls(current, 1, frozenset()):
                if event_id in reachable_events:
                    continue
                reachable_events.add(event_id)
                event = event_defs.get(event_id)
                if event is not None:
                    pending_bodies.append(event.body)
        return reachable_effects, reachable_events

    def _raw_script_call_sites(
        self, effect_name: str, patterns: Sequence[str]
    ) -> List[Tuple[str, int]]:
        pattern = re.compile(rf"\b{re.escape(effect_name)}\s*=\s*yes\b")
        needle = effect_name.encode("ascii")
        callers: List[Tuple[str, int]] = []
        for filepath in self._collect_text_files(patterns):
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            if needle not in raw:
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            callers.extend(
                (self._relpath(filepath), self._line(text, match.start()))
                for match in pattern.finditer(text)
            )
        return callers

    def _global_flag_write_sites(
        self, flag: str
    ) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
        paths = [
            "common/**/*.txt",
            "events/**/*.txt",
            "history/**/*.txt",
        ]
        patterns = {
            "set": re.compile(
                rf"\bset_global_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
            ),
            "clear": re.compile(
                rf"\bclr_global_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
            ),
        }
        writes: Dict[str, List[Tuple[str, int]]] = {"set": [], "clear": []}
        marker = flag.encode("ascii")
        for filepath in self._collect_text_files(paths):
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            if marker not in raw:
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            for kind, pattern in patterns.items():
                writes[kind].extend(
                    (self._relpath(filepath), self._line(text, match.start()))
                    for match in pattern.finditer(text)
                )
        return writes["set"], writes["clear"]

    def _country_flag_write_sites(
        self, flags: Iterable[str]
    ) -> Dict[str, Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]]:
        tracked = tuple(flags)
        writes = {flag: ([], []) for flag in tracked}
        needles = {flag: flag.encode("ascii") for flag in tracked}
        for filepath in self._collect_text_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        ):
            try:
                raw = Path(filepath).read_bytes()
            except OSError:
                continue
            present = [flag for flag in tracked if needles[flag] in raw]
            if not present:
                continue
            text = strip_comments(raw.decode("utf-8-sig", errors="replace"))
            for flag in present:
                set_pattern = re.compile(
                    rf"\bset_country_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
                )
                clear_pattern = re.compile(
                    rf"\bclr_country_flag\s*=\s*(?:{re.escape(flag)}\b|\{{\s*flag\s*=\s*{re.escape(flag)}\b)"
                )
                sets, clears = writes[flag]
                sets.extend(
                    (self._relpath(filepath), self._line(text, match.start()))
                    for match in set_pattern.finditer(text)
                )
                clears.extend(
                    (self._relpath(filepath), self._line(text, match.start()))
                    for match in clear_pattern.finditer(text)
                )
        return writes

    def _chain_is_registered_in_startup(self, chain: ChainConfig, body: str) -> bool:
        markers = (
            f"{chain.reconstruct_effect} = yes",
            f"{chain.scheduler_effect} = yes",
            chain.hidden_ninety_id,
            f"{chain.namespace}.1",
        )
        return any(marker in body for marker in markers)

    def _has_terminal_resolver(
        self, chain: ChainConfig, effect_defs: Dict[str, List[BlockDef]]
    ) -> bool:
        """The reconstruct ladder must silently land one of the chain's outcomes.

        A name check (``*resolve*``) says nothing about behaviour and misses the
        player-choice capstones that resolve inline in the ladder.
        """
        reconstruct = effect_defs.get(chain.reconstruct_effect)
        if not reconstruct or not chain.outcome_idea_prefixes:
            return False
        return bool(self._outcome_ideas_added(reconstruct[0].body, chain, effect_defs))

    def _outcome_ideas_added(
        self,
        body: str,
        chain: ChainConfig,
        effect_defs: Dict[str, List[BlockDef]],
        seen: FrozenSet[str] = frozenset(),
    ) -> Set[str]:
        found = {
            match.group(1)
            for match in _ADD_IDEA_RE.finditer(body)
            if (
                match.group(1) in chain.outcome_ideas
                if chain.outcome_ideas
                else any(
                    match.group(1).startswith(prefix)
                    for prefix in chain.outcome_idea_prefixes
                )
            )
        }
        for match in _EFFECT_YES_RE.finditer(body):
            name = match.group(1)
            if (
                not name.startswith(chain.root)
                or name in seen
                or name not in effect_defs
            ):
                continue
            found |= self._outcome_ideas_added(
                effect_defs[name][0].body, chain, effect_defs, seen | {name}
            )
        return found

    def _outcome_ideas_for_chain(
        self, chain: ChainConfig, idea_defs: Dict[str, IdeaDef]
    ) -> Set[str]:
        if chain.outcome_ideas:
            return set(chain.outcome_ideas)
        results = set()
        for idea_id in idea_defs:
            if any(
                idea_id.startswith(prefix) for prefix in chain.outcome_idea_prefixes
            ):
                results.add(idea_id)
        return results

    def _has_cleanup_path(
        self,
        chain: ChainConfig,
        effect_defs: Dict[str, List[BlockDef]],
        event_defs: Dict[str, EventDef],
        outcome_ids: Set[str],
    ) -> bool:
        """A chain must clear competing outcomes somewhere it can act atomically.

        The cleanup may live in a chain-owned effect or directly in a capstone
        option; what matters is that one block drops at least two competing
        outcome ideas, not which file it sits in.
        """
        if not outcome_ids:
            return False
        bodies = [
            effect.body
            for defs in effect_defs.values()
            for effect in defs
            if effect.name.startswith(chain.root)
        ]
        bodies.extend(
            option.body
            for event in event_defs.values()
            if event.event_id.startswith(chain.namespace + ".")
            for option in event.options
        )
        for body in bodies:
            if "remove_ideas" not in body:
                continue
            removed = sum(
                1
                for idea_id in outcome_ids
                if re.search(r"\b" + re.escape(idea_id) + r"\b", body)
            )
            if removed == len(outcome_ids):
                return True
        return False

    def _trace_mutation_path(
        self,
        text: str,
        chain: ChainConfig,
        effect_lookup: Dict[str, BlockDef],
        seen: Set[str],
        pending: bool = False,
    ) -> Tuple[bool, bool, bool]:
        ops: List[Tuple[int, str, str]] = []
        effect_names = set(effect_lookup)
        for match in _SET_VAR_RE.finditer(text):
            variable = match.group(1)
            if variable in chain.variables:
                ops.append((match.start(), "mutate", variable))
        for match in _CLAMP_VAR_RE.finditer(text):
            variable = match.group(1)
            if variable in chain.variables:
                ops.append((match.start(), "clamp", variable))
        for match in _SET_TEMP_CORP_RE.finditer(text):
            variable = match.group(1)
            if variable in chain.variables:
                ops.append((match.start(), "prepare-clamp", variable))
        for match in _DIRECT_CORP_CLAMP_RE.finditer(text):
            ops.append((match.start(), "direct-clamp", "corp"))
        for match in _EFFECT_YES_RE.finditer(text):
            name = match.group(1)
            if name in effect_names:
                ops.append((match.start(), "call", name))
        ops.sort(key=lambda item: item[0])

        used_clamp = False
        mutated = False
        prepared = False
        for _pos, kind, value in ops:
            if kind == "mutate":
                pending = True
                mutated = True
            elif kind == "clamp":
                if pending:
                    pending = False
                    used_clamp = True
            elif kind == "prepare-clamp":
                if pending:
                    prepared = True
            elif kind == "direct-clamp":
                if pending and prepared:
                    pending = False
                    used_clamp = True
                    prepared = False
            elif kind == "call":
                if value == chain.clamp_effect:
                    if pending:
                        pending = False
                        used_clamp = True
                    continue
                if value in seen:
                    continue
                callee = effect_lookup[value]
                pending, callee_used, callee_mutated = self._trace_mutation_path(
                    callee.body, chain, effect_lookup, seen | {value}, pending
                )
                used_clamp = used_clamp or callee_used
                mutated = mutated or callee_mutated
        return pending, used_clamp, mutated

    def _block_has_state_change(self, body: str, chain: ChainConfig) -> bool:
        if re.search(r"\bset_country_flag\b|\badd_ideas\b|\bremove_ideas\b", body):
            return True
        return any(variable in body for variable in chain.variables)

    def _has_marker_guard(self, body: str) -> bool:
        # Special case: reconstruction-complete flag setting is always valid
        if "set_country_flag = " in body and "_reconstruct_complete" in body:
            return True
        limit = self._direct_child_block(body, "limit")
        if limit is None:
            return False
        return self._negated_marker_in_trigger(limit)

    def _iter_direct_child_blocks(
        self, text: str
    ) -> Iterable[Tuple[str, int, int, str]]:
        pos = 0
        while True:
            match = _BLOCK_HEADER_RE.search(text, pos)
            if not match:
                return
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                pos = match.end()
                continue
            yield match.group(1), match.start(), end, body
            pos = end

    def _direct_child_block(self, text: str, name: str):
        matches = [
            body
            for child, _start, _end, body in self._iter_direct_child_blocks(text)
            if child == name
        ]
        return matches[0] if len(matches) == 1 else None

    def _negated_marker_in_trigger(
        self, text: str, negated: bool = False, disjunction: bool = False
    ) -> bool:
        """True when a sibling-marker check sits under an odd number of NOTs.

        Only ``NOT``/``OR``/``AND`` are descended into: a marker read inside a
        scope switch guards a different country, and a positive marker check is
        a branch selector rather than a replay guard. Siblings of a conjunction
        are AND-ed, so two bare markers under one ``NOT`` mean "not both at
        once" and still let the branch replay; only ``OR`` may carry a set.
        """
        residual: List[str] = []
        cursor = 0
        markers = 0
        for name, start, end, body in self._iter_direct_child_blocks(text):
            residual.append(text[cursor:start])
            cursor = end
            upper = name.upper()
            if upper == "NOT":
                if self._negated_marker_in_trigger(body, not negated):
                    return True
            elif upper in ("OR", "AND"):
                if self._negated_marker_in_trigger(body, negated, upper == "OR"):
                    return True
            elif upper in ("HAS_COUNTRY_FLAG", "HAS_IDEA"):
                markers += 1
        residual.append(text[cursor:])
        markers += len(_MARKER_TRIGGER_RE.findall("".join(residual)))
        if not negated:
            return False
        return markers >= 1 if disjunction else markers == 1

    def _line_is_cross_write(
        self, line: str, owner: ChainConfig, stack: Sequence[str]
    ) -> bool:
        if any(keyword in line for keyword in _WRITE_KEYWORDS):
            return True
        if any(keyword in line for keyword in _EVENT_KEYWORDS):
            return True
        if any(context in ("ai_chance", "trigger") for context in stack):
            return False
        return bool(
            re.search(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b", line)
            and any(prefix in line for prefix in owner.owned_prefixes)
        )

    def _line_is_cross_read(self, line: str, stack: Sequence[str]) -> bool:
        if any(keyword in line for keyword in _READ_KEYWORDS):
            return True
        return bool(
            any(context in ("ai_chance", "trigger") for context in stack)
            and re.search(r"\b[A-Za-z0-9_]+\s*=\s*yes\b", line)
        )

    def _is_allowed(self, token: str, patterns: Sequence[str]) -> bool:
        """Exact match only, so an exception never covers a neighbouring symbol."""
        return token in patterns

    def _dedupe_findings(
        self, findings: Sequence[Tuple[str, str, int]]
    ) -> List[Tuple[str, str, int]]:
        seen: Set[Tuple[str, str, int]] = set()
        deduped: List[Tuple[str, str, int]] = []
        for finding in findings:
            if finding not in seen:
                seen.add(finding)
                deduped.append(finding)
        return deduped

    def _relpath(self, path: os.PathLike | str) -> str:
        return os.path.relpath(str(path), self.mod_path)

    @staticmethod
    def _line(text: str, pos: int) -> int:
        return text.count("\n", 0, pos) + 1


if __name__ == "__main__":
    run_validator_main(Validator, "Validate the corporate-history framework contract")
