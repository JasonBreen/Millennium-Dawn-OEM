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
from shared_utils import read_text_strict

BLOCK_RE = re.compile(r"([\w.@:\-]+)\s*=\s*\{")
PLAYER_ONLY_RE = re.compile(r"\bis_ai\s*=\s*no\b")
ZERO_RE = re.compile(r"^(?:base|factor)\s*=\s*0(?:\.0+)?$")
GATE_KEYS = ("allowed", "visible", "available", "target_root_trigger", "target_trigger")


def strip_comments(text):
    return re.sub(r"#[^\n]*", "", text)


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


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def scenario_files(repo, folder, key):
    base = repo / folder
    return sorted([*base.glob(f"{key}.txt"), *base.glob(f"{key}_*.txt")])


def audit_decisions(repo, key):
    findings = []
    for path in scenario_files(repo, "common/decisions", key):
        text = strip_comments(read_text_strict(str(path)))
        for _category, cat_body, _ in blocks(text):
            for name, body, _ in blocks(cat_body):
                if not any(
                    k in body for k in ("complete_effect", "ai_will_do", "available")
                ):
                    continue
                gate = " ".join(squash(child(body, k)) for k in GATE_KEYS)
                if PLAYER_ONLY_RE.search(gate):
                    continue
                ai = child(body, "ai_will_do")
                if ai is None:
                    findings.append((path.name, name, "decision has no ai_will_do"))
                elif ZERO_RE.match(squash(ai)):
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
        text = strip_comments(read_text_strict(str(path)))
        for kind, body, _ in blocks(text):
            if kind not in ("country_event", "news_event", "state_event"):
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


def enclosing_limits(text, pos):
    """Return the limit bodies of every block that encloses pos."""
    limits, depth, starts = [], 0, []
    for i in range(pos - 1, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            if depth:
                depth -= 1
            else:
                starts.append(i)
    for start in starts:
        depth, j = 1, start + 1
        while j < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        limit = child(text[start + 1 : j - 1], "limit")
        if limit is not None:
            limits.append(limit)
    return limits


def dispatching_files(repo, key):
    """Read once every script file that mentions one of the scenario's event IDs."""
    needle = f"{key}."
    texts = []
    for folder in ("common", "events"):
        for path in (repo / folder).rglob("*.txt"):
            raw = read_text_strict(str(path))
            if needle in raw:
                texts.append((path.name, strip_comments(raw)))
    return texts


def dispatch_sites(texts, eid):
    """Yield (file name, text, position, delayed) for every dispatch of eid."""
    plain = re.compile(rf"\bcountry_event\s*=\s*{re.escape(eid)}\b")
    full = re.compile(
        rf"\bcountry_event\s*=\s*\{{[^}}]*\bid\s*=\s*{re.escape(eid)}\b[^}}]*\}}"
    )
    for name, text in texts:
        if eid not in text:
            continue
        for m in plain.finditer(text):
            yield name, text, m.start(), False
        for m in full.finditer(text):
            if re.search(r"\b(?:title|is_triggered_only|picture)\s*=", m.group(0)):
                continue  # the event's own definition, not a dispatch
            yield name, text, m.start(), bool(re.search(r"\bdays\s*=", m.group(0)))


def audit_dispatch(repo, key, event_map):
    findings = []
    shared = re.compile(rf"global\.{re.escape(key)}_event_\w+")
    texts = dispatching_files(repo, key)
    for eid, (fname, body) in sorted(event_map.items()):
        sites = list(dispatch_sites(texts, eid))
        trigger = child(body, "trigger") or ""
        player_only_event = bool(PLAYER_ONLY_RE.search(trigger))
        if sites and has_weights(body) and not player_only_event:
            if all(
                any(PLAYER_ONLY_RE.search(lim) for lim in enclosing_limits(t, p))
                for _, t, p, _ in sites
            ):
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
