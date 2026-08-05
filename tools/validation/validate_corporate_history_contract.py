#!/usr/bin/env python3
"""Validate the corporate-history framework contract."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Mapping, Sequence, Set, Tuple

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
    r"\bclamp_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z0-9_]+)\s+min\s*=\s*(-?\d+)\s+max\s*=\s*(-?\d+)"
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


@dataclass(frozen=True)
class Bound:
    minimum: int
    maximum: int


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

    def run_validations(self):
        self._log_section("loading manifest")
        chains = self._load_manifest()
        if not chains:
            return
        chain_by_namespace = {chain.namespace: chain for chain in chains}
        chain_by_root = {chain.root: chain for chain in chains}

        self._log_section("indexing corporate history")
        effect_defs = self._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
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
                    name: Bound(int(cfg["min"]), int(cfg["max"]))
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

    def _scheduler_window_years(self, scheduler: BlockDef, event_id: str) -> Set[int]:
        years: Set[int] = set()
        for name, _start, _end, body in self._iter_direct_child_blocks(scheduler.body):
            if name not in ("if", "else_if"):
                continue
            targets = {
                target
                for target, _line in self._find_event_calls(
                    body, scheduler.line, frozenset()
                )
            }
            if event_id not in targets:
                continue
            limit = self._direct_child_block(body, "limit") or ""
            lower = re.search(
                r"NOT\s*=\s*\{\s*has_start_date\s*<\s*(\d{4})\.1\.1\s*\}",
                limit,
            )
            upper = re.search(r"\bhas_start_date\s*<\s*(\d{4})\.1\.2\b", limit)
            if lower and upper and lower.group(1) == upper.group(1):
                years.add(int(lower.group(1)))
        return years

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
            call_count = len(callers)
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
                if callers[0][2] != expected_owner:
                    findings.append(
                        (
                            f"{name} must be called by {expected_owner}; found {callers[0][2]}",
                            callers[0][0],
                            callers[0][1],
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
                    startup_callers[0][0]
                    if startup_callers
                    else "common/on_actions/00_on_actions.txt",
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
                declared_bounds: Dict[str, Tuple[int, int]] = {}
                for effect in reachable_clamps.values():
                    declared_bounds.update(
                        {
                            match.group(1): (int(match.group(2)), int(match.group(3)))
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
        for filepath in self._collect_text_files(["localisation/english/*.yml"]):
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

    def _startup_full_branch(self, startup_body: str) -> str:
        """The Full-rule arm of corporate_history_on_startup, or an empty string.

        Outcomes Only always reconstructs; only the Full arm proves a later start
        still catches its chain up without the hidden .90 anchor.
        """
        for name, _start, _end, body in self._iter_direct_child_blocks(startup_body):
            if name != "if":
                continue
            limit = self._direct_child_block(body, "limit")
            if limit and "corporate_history_full_enabled" in limit:
                return body
        return ""

    def _startup_outcomes_branch(self, startup_body: str) -> str:
        for name, _start, _end, body in self._iter_direct_child_blocks(startup_body):
            if name != "else_if":
                continue
            limit = self._direct_child_block(body, "limit")
            if limit and "corporate_history_outcomes_only_enabled" in limit:
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
        pattern = re.compile(r"\b" + re.escape(effect_name) + r"\s*=\s*yes\b")
        callers: List[Tuple[str, int]] = []
        on_action_texts: List[Tuple[str, str]] = []
        for filepath in self._collect_text_files(["common/on_actions/**/*.txt"]):
            try:
                text = strip_comments(
                    Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
                )
            except OSError:
                continue
            on_action_texts.append((filepath, text))
            for match in pattern.finditer(text):
                callers.append(
                    (self._relpath(filepath), self._line(text, match.start()))
                )
        if callers:
            return callers

        intermediary_effects: Set[str] = set()
        effect_defs = self._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
        for name, definitions in effect_defs.items():
            if name == effect_name:
                continue
            if any(pattern.search(definition.body) for definition in definitions):
                intermediary_effects.add(name)
        for intermediary in intermediary_effects:
            intermediary_pattern = re.compile(
                r"\b" + re.escape(intermediary) + r"\s*=\s*yes\b"
            )
            for filepath, text in on_action_texts:
                for match in intermediary_pattern.finditer(text):
                    callers.append(
                        (self._relpath(filepath), self._line(text, match.start()))
                    )
        return callers

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
        for child, _start, _end, body in self._iter_direct_child_blocks(text):
            if child == name:
                return body
        return None

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
