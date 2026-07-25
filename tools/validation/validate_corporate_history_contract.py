#!/usr/bin/env python3
"""Validate the corporate-history framework contract."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

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
    r"\b(?:set_variable|add_to_variable|subtract_from_variable)\s*=\s*\{\s*([A-Za-z0-9_]+)"
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
    allow_multiple_completion_producers: bool = False

    @property
    def completion_flag(self) -> str:
        return f"{self.root}_reconstruct_complete"

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
        return f"{self.tag}_corporate_history_monthly_outcomes"


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
    STAGED_EXTENSIONS = [".txt", ".json"]

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

        self._log_section("manifest coverage")
        self._report(
            self._validate_manifest_coverage(core_namespaces, chain_by_namespace),
            "Corporate-history manifest covers current namespaces",
            "Corporate-history manifest coverage issues:",
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
            self._validate_reconstruction_safety(chains, effect_defs),
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
            self._validate_cross_chain_ownership(chains, chain_by_root),
            "Cross-chain ownership stays within the declared contract",
            "Corporate-history cross-chain ownership issues:",
            category="Corporate-history cross-chain ownership",
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

        chains = []
        for raw in payload.get("chains", []):
            bounds = {
                name: Bound(int(cfg["min"]), int(cfg["max"]))
                for name, cfg in raw.get("variables", {}).items()
            }
            chains.append(
                ChainConfig(
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
                    allow_multiple_completion_producers=bool(
                        raw.get("allow_multiple_completion_producers", False)
                    ),
                )
            )
        return chains

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
        self, core_namespaces: Set[str], chain_by_namespace: Dict[str, ChainConfig]
    ) -> List[Tuple[str, str, int]]:
        findings = []
        for namespace in sorted(core_namespaces):
            if namespace not in chain_by_namespace:
                findings.append(
                    (f"Unregistered corporate-history namespace {namespace}", "", 0)
                )
        return findings

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
                if not event_id.startswith(chain.namespace + ".") or event.hidden:
                    continue
                callers = self._dedupe_callers(call_sites.get(event_id, []))
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
            call_count = len(yearly_calls.get(name, []))
            if call_count != 1:
                findings.append(
                    (
                        f"{name} requires exactly one yearly-dispatch caller; found {call_count}",
                        definition.file,
                        definition.line,
                    )
                )
            if "corporate_history_full_enabled = yes" not in definition.body:
                findings.append(
                    (
                        f"{name} is missing the corporate_history_full_enabled gate",
                        definition.file,
                        definition.line,
                    )
                )
            scheduled = self._find_event_calls(
                definition.body, definition.line, frozenset()
            )
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
        monthly_defs = {
            name: defs[0] for name, defs in effect_defs.items() if len(defs) == 1
        }

        for chain in chains:
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
            saw_clamped_option = False
            saw_mutating_option = False
            for event in event_defs.values():
                if not event.event_id.startswith(chain.namespace + ".") or event.hidden:
                    continue
                for option in event.options:
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

    def _validate_reconstruction_safety(
        self, chains: Sequence[ChainConfig], effect_defs: Dict[str, List[BlockDef]]
    ) -> List[Tuple[str, str, int]]:
        findings = []
        effect_lookup = {name: defs[0] for name, defs in effect_defs.items() if defs}
        for chain in chains:
            reconstruct = effect_lookup.get(chain.reconstruct_effect)
            if reconstruct is None:
                continue
            for label, pattern in _CUSTOM_EFFECT_REWARDS:
                if pattern.search(reconstruct.body):
                    findings.append(
                        (
                            f"{chain.reconstruct_effect} replays {label}",
                            reconstruct.file,
                            reconstruct.line,
                        )
                    )
            event_calls = self._find_event_calls(
                reconstruct.body, reconstruct.line, frozenset()
            )
            for _target, line in event_calls:
                findings.append(
                    (
                        f"{chain.reconstruct_effect} fires a visible event during reconstruction",
                        reconstruct.file,
                        line,
                    )
                )
            if not self._flag_is_produced(
                chain.completion_flag, {chain.reconstruct_effect: [reconstruct]}
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
            if chain.completion_flag in discovered_flags:
                owners.setdefault(chain.completion_flag, []).append(chain)
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
        self, chains: Sequence[ChainConfig], chain_by_root: Dict[str, ChainConfig]
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
            paths = [
                self._root / "events" / f"{chain.namespace}.txt",
                self._root
                / "common"
                / "scripted_effects"
                / f"{chain.root}_effects.txt",
            ]
            for path in paths:
                if not path.exists():
                    continue
                try:
                    text = strip_comments(
                        path.read_text(encoding="utf-8-sig", errors="replace")
                    )
                except OSError:
                    continue
                stack: List[str] = []
                line_no = 0
                for raw_line in text.splitlines():
                    line_no += 1
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
                    if tokens:
                        rel = self._relpath(path)
                        for owner, token in sorted(tokens, key=lambda item: item[1]):
                            if self._line_is_cross_write(code, owner):
                                if not self._is_allowed(token, chain.allowed_writes):
                                    findings.append(
                                        (
                                            f"{chain.name} writes {token}, owned by {owner.name}, outside declared exceptions",
                                            rel,
                                            line_no,
                                        )
                                    )
                            elif self._line_is_cross_read(code):
                                if not self._is_allowed(token, chain.allowed_reads):
                                    label = (
                                        "read-only AI/flavour use"
                                        if any(
                                            ctx in ("ai_chance", "trigger")
                                            for ctx in stack
                                        )
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
        return self._dedupe_findings(findings)

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
        seen: Set[str] = frozenset(),
    ) -> Set[str]:
        found = {
            match.group(1)
            for match in _ADD_IDEA_RE.finditer(body)
            if any(
                match.group(1).startswith(prefix)
                for prefix in chain.outcome_idea_prefixes
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
            if removed >= 2:
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

    def _line_is_cross_write(self, line: str, owner: ChainConfig) -> bool:
        if any(keyword in line for keyword in _WRITE_KEYWORDS):
            return True
        return bool(
            re.search(r"\b([A-Za-z0-9_]+)\s*=\s*yes\b", line)
            and any(prefix in line for prefix in owner.owned_prefixes)
        )

    def _line_is_cross_read(self, line: str) -> bool:
        return any(keyword in line for keyword in _READ_KEYWORDS)

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
