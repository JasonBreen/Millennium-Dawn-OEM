#!/usr/bin/env python3
"""Audit an opt-in scenario's AI coverage and delayed-event context.

Reports, for one scenario key (STALKER, SILENTHILL, ...):
- decisions with no ai_will_do, or a zero weight, that are not player-only;
- multi-option events whose options lack ai_chance;
- events whose options carry AI weights but whose every dispatch site is
  player-only, so the weights never run (the STALKER.2 bug);
- delayed dispatches (days =) and whether the event reads a shared
  global.<KEY>_event_* variable, which a later dispatch can overwrite.

It is advisory: it always exits 0 and prints findings for a reviewer.

Usage:
    python tools/analysis/scenario_ai_audit.py STALKER
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.paths import REPO_ROOT
from shared_utils import blank_quoted_strings, read_text_strict, strip_comments

BLOCK_RE = re.compile(r"([\w.@:\-]+)\s*=\s*\{")
PLAYER_ONLY_RE = re.compile(r"\bis_ai\s*=\s*no\b")
DELAY_RE = re.compile(r"\b(?:days|hours|random_days|random_hours)\s*=")
GATE_KEYS = ("allowed", "visible", "available", "target_root_trigger", "target_trigger")
DECISION_KEYS = (
    "complete_effect",
    "remove_effect",
    "timeout_effect",
    "ai_will_do",
    "available",
    "cost",
    "days_mission_timeout",
)
# Blocks whose children are not all required, so an is_ai = no inside them
# does not prove the AI is excluded.
NOT_REQUIRED = {"NOT", "OR", "NOR", "NAND", "count_triggers"}
# Blocks that keep the acting country (ROOT) in scope.
ACTOR_BLOCKS = {"AND", "ROOT", "hidden_trigger", "custom_trigger_tooltip"}
DISPATCH_ROOTS = ("common", "events", "history")
EVENT_KINDS = ("country_event", "news_event", "state_event")
# Fields only an event definition has; a dispatch block has id and timing only.
DEFINITION_RE = re.compile(
    r"\b(?:title|desc|option|picture|is_triggered_only|trigger|mean_time_to_happen)\s*="
)
# Effect blocks that run their contents in the same scope.
SAME_SCOPE = {"if", "else_if", "else", "hidden_effect", "random_list", "random", "AND"}
ADD_RE = re.compile(r"\badd\s*=")
NAME_BEFORE_RE = re.compile(r"([\w.@:\-]+)\s*=\s*$")


def read_script(path):
    """Read script with comments removed and quoted text blanked, offsets kept."""
    return blank_quoted_strings(strip_comments(read_text_strict(str(path))))


def top_level(text):
    """Return text with every nested { ... } block removed."""
    out, depth = [], 0
    for ch in text:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def blocks(text):
    """Yield (name, body, start) for each top-level `key = { ... }` in text."""
    i, n = 0, len(text)
    while True:
        m = BLOCK_RE.search(text, i)
        if not m:
            return
        depth, j = 1, m.end()
        while j < n and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        yield m.group(1), text[m.end() : j - 1], m.start()
        i = j


def child(body, key):
    for name, inner, _ in blocks(body):
        if name == key:
            return inner
    return None


def requires_player(text, follow_scopes=True):
    """True when the triggers in text, read as an AND, require is_ai = no.

    NOT, OR and similar are never followed, because an is_ai = no inside them
    does not exclude the AI. With follow_scopes=False only blocks that keep the
    acting country in scope are followed, so a target's is_ai = no (FROM,
    controller, ...) does not count; use that for decision gates.
    """
    if PLAYER_ONLY_RE.search(top_level(text)):
        return True
    return any(
        requires_player(inner, follow_scopes)
        for name, inner, _ in blocks(text)
        if name not in NOT_REQUIRED and (follow_scopes or name in ACTOR_BLOCKS)
    )


def scenario_files(repo, folder, key):
    base = repo / folder
    return sorted([*base.glob(f"{key}.txt"), *base.glob(f"{key}_*.txt")])


def audit_decisions(repo, key):
    findings = []
    for path in scenario_files(repo, "common/decisions", key):
        text = read_script(path)
        for _category, cat_body, _ in blocks(text):
            for name, body, _ in blocks(cat_body):
                if not any(re.search(rf"\b{k}\s*=", body) for k in DECISION_KEYS):
                    continue
                if any(
                    requires_player(child(body, k) or "", follow_scopes=False)
                    for k in GATE_KEYS
                ):
                    continue
                ai = child(body, "ai_will_do")
                if ai is None:
                    findings.append((path.name, name, "decision has no ai_will_do"))
                elif always_zero(ai):
                    findings.append(
                        (
                            path.name,
                            name,
                            "decision ai_will_do is 0; the AI never takes it",
                        )
                    )
    return findings


def events(repo, key):
    """Map event id -> (file name, event body) for the scenario's events."""
    found = {}
    for path in scenario_files(repo, "events", key):
        text = read_script(path)
        for kind, body, _ in blocks(text):
            if kind not in EVENT_KINDS:
                continue
            match = re.search(r"\bid\s*=\s*([\w.]+)", body)
            if match:
                found[match.group(1)] = (path.name, body)
    return found


def options(body):
    return [inner for name, inner, _ in blocks(body) if name == "option"]


def has_weights(body):
    return any(child(opt, "ai_chance") is not None for opt in options(body))


def audit_event_options(event_map):
    findings = []
    for eid, (fname, body) in sorted(event_map.items()):
        if re.search(r"\bhidden\s*=\s*yes", body):
            continue
        opts = options(body)
        if len(opts) < 2:
            continue
        missing = sum(1 for opt in opts if child(opt, "ai_chance") is None)
        if missing:
            findings.append(
                (fname, eid, f"{missing} of {len(opts)} options have no ai_chance")
            )
    return findings


def always_zero(ai):
    """True when ai_will_do starts at 0 and no modifier can add to it."""
    start = re.search(r"\b(?:base|factor)\s*=\s*(-?\d+(?:\.\d+)?)", top_level(ai))
    return bool(start) and float(start.group(1)) == 0 and not ADD_RE.search(ai)


def gated_for_player(text, pos):
    """True when a condition around pos requires is_ai = no of the receiving scope.

    Walks the enclosing blocks from the inside out. Each limit is read through
    the scope blocks between it and the dispatch (controller = { ... } and the
    like); a scope it does not name, such as every_country, breaks the chain.
    """
    path, depth = [], 0
    for i in range(pos - 1, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
            continue
        if ch != "{":
            continue
        if depth:
            depth -= 1
            continue
        name_match = NAME_BEFORE_RE.search(text[max(0, i - 200) : i])
        name = name_match.group(1) if name_match else ""
        end, level = i + 1, 1
        while end < len(text) and level:
            level += {"{": 1, "}": -1}.get(text[end], 0)
            end += 1
        limit = child(text[i + 1 : end - 1], "limit")
        for scope in path:
            if limit is None:
                break
            limit = child(limit, scope)
        if limit is not None and requires_player(limit, follow_scopes=False):
            return True
        if name not in SAME_SCOPE and not name.isdigit():
            path.insert(0, name)
    return False


def dispatching_files(repo, key):
    """Read once every script file that mentions one of the scenario's event IDs.

    Each entry also carries the start offsets of the file's own top-level event
    definitions, so a definition is never mistaken for a dispatch.
    """
    needle = f"{key}."
    texts = []
    for folder in DISPATCH_ROOTS:
        for path in (repo / folder).rglob("*.txt"):
            if needle in read_text_strict(str(path)):
                text = read_script(path)
                definitions = {
                    start
                    for kind, body, start in blocks(text)
                    if kind in EVENT_KINDS and DEFINITION_RE.search(body)
                }
                texts.append((path.name, text, definitions))
    return texts


def dispatch_sites(texts, eid):
    """Yield (file name, text, position, delayed) for every dispatch of eid."""
    command = r"\b(?:country|news|state)_event"
    plain = re.compile(rf"{command}\s*=\s*{re.escape(eid)}\b")
    full = re.compile(
        rf"{command}\s*=\s*\{{[^}}]*\bid\s*=\s*{re.escape(eid)}\b[^}}]*\}}"
    )
    for name, text, definitions in texts:
        if eid not in text:
            continue
        for m in plain.finditer(text):
            yield name, text, m.start(), False
        for m in full.finditer(text):
            if m.start() in definitions:
                continue
            yield name, text, m.start(), bool(DELAY_RE.search(m.group(0)))


def audit_dispatch(repo, key, event_map):
    findings = []
    shared = re.compile(rf"global\.{re.escape(key)}_event_\w+")
    texts = dispatching_files(repo, key)
    for eid, (fname, body) in sorted(event_map.items()):
        sites = list(dispatch_sites(texts, eid))
        trigger = child(body, "trigger") or ""
        player_only_event = requires_player(trigger, follow_scopes=False)
        if sites and has_weights(body) and not player_only_event:
            if all(gated_for_player(t, p) for _, t, p, _ in sites):
                findings.append(
                    (
                        fname,
                        eid,
                        "has AI weights but every dispatch is player-only (is_ai = no)",
                    )
                )
        for site_file, _, _, delayed in sites:
            if delayed and shared.search(body):
                findings.append(
                    (
                        fname,
                        eid,
                        f"delayed dispatch in {site_file} and the event reads a shared global",
                    )
                )
    return findings


def audit(repo, key):
    repo = Path(repo)
    event_map = events(repo, key)
    return {
        "decisions": audit_decisions(repo, key),
        "event options": audit_event_options(event_map),
        "dispatch": audit_dispatch(repo, key, event_map),
    }, len(event_map)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("key", help="scenario key, e.g. STALKER")
    parser.add_argument("--repo", default=str(REPO_ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    results, event_count = audit(args.repo, args.key)
    total = sum(len(v) for v in results.values())
    print(f"{args.key}: {event_count} events checked, {total} finding(s)")
    for section, findings in results.items():
        print(f"\n## {section} ({len(findings)})")
        for fname, name, message in findings:
            print(f"- {fname}: {name}: {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
