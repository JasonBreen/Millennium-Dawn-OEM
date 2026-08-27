#!/usr/bin/env python3
"""Preflight a corporate-history chain before it is pushed.

Extracting one chain out of the fork drops the siblings it used to sit beside,
and the breakages that follow stay invisible until CI runs. This reports the
four that have actually bitten:

* an outcome flag written by an option that nothing ever reads
* an ai_chance weight reading a flag no file writes, left behind by a sibling
  chain that was not extracted alongside it
* an option that records no country flag, which is the only thing upstream's
  outcomes_only rule can replay. Chains that keep their state in axis variables
  instead are exempted with --effect-outcomes
* a title, description or option name with no localisation key
"""

import argparse
import io
import os
import re
import sys

SET_FLAG = re.compile(r"\bset_country_flag = (\w+)")
SET_FLAG_TIMED = re.compile(r"\bset_country_flag = \{ flag = (\w+)")
HAS_FLAG = re.compile(r"\bhas_country_flag = (\w+)")
LOC_KEY = re.compile(r"^ ([A-Za-z0-9_.]+):", re.M)
EVENT_BLOCK = re.compile(r"country_event = \{.*?\n\}", re.S)
EVENT_ID = re.compile(r"\n\tid = (\S+)")
OPTION = re.compile(r"\n\toption = \{(.*?)\n\t\}", re.S)
OPTION_NAME = re.compile(r"\n\t\tname = (\S+)")
LOC_REF = re.compile(r"\n\t(?:title|desc) = (\S+)")
LOC_REF_INLINE = re.compile(r"text = (\S+?) \}")
EFFECT_CALL = re.compile(r"\b(\w+) = yes\b")
NOT_AN_EFFECT = frozenset(
    {
        "always",
        "hidden",
        "fire_only_once",
        "is_triggered_only",
        "is_ai",
        "is_historical_focus_on",
        "allowed_civil_war",
        "major",
        "minor_flavor",
        "ai_has_major_economic_problems",
    }
)


def read(path):
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with io.open(path, encoding=enc, newline="") as handle:
                return handle.read()
        except UnicodeDecodeError:
            continue
    return ""


def walk(root, *subdirs, **kwargs):
    suffix = kwargs.get("suffix", ".txt")
    for sub in subdirs:
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, sub)):
            dirnames[:] = [d for d in dirnames if d not in (".git", ".claude")]
            for name in filenames:
                if name.endswith(suffix):
                    yield os.path.join(dirpath, name)


def collect(root):
    written, used, loc = set(), set(), set()
    for path in walk(root, "events", "common"):
        text = read(path)
        written |= set(SET_FLAG.findall(text)) | set(SET_FLAG_TIMED.findall(text))
        used |= set(HAS_FLAG.findall(text))
    for path in walk(root, os.path.join("localisation", "english"), suffix=".yml"):
        loc |= set(LOC_KEY.findall(read(path)))
    return written, used, loc


def check(root, targets, prefix="", effect_outcomes=False):
    written, used, loc = collect(root)
    findings = []
    for path in targets:
        text = read(path)
        rel = os.path.relpath(path, root).replace("\\", "/")
        for block in EVENT_BLOCK.findall(text):
            ident = EVENT_ID.search(block)
            if not ident or (prefix and prefix not in block):
                continue
            event_id = ident.group(1)
            for key in LOC_REF.findall(block) + LOC_REF_INLINE.findall(block):
                if key not in loc:
                    findings.append((rel, event_id, "no localisation for %s" % key))
            for body in OPTION.findall(block):
                found = OPTION_NAME.search(body)
                name = found.group(1) if found else "(unnamed)"
                if found and name not in loc:
                    findings.append((rel, event_id, "no localisation for %s" % name))
                records = bool(SET_FLAG.search(body) or SET_FLAG_TIMED.search(body))
                if effect_outcomes:
                    records = records or any(
                        name not in NOT_AN_EFFECT for name in EFFECT_CALL.findall(body)
                    )
                if not records:
                    findings.append((rel, event_id, "%s records no outcome" % name))
                for flag in set(SET_FLAG.findall(body)) | set(
                    SET_FLAG_TIMED.findall(body)
                ):
                    if flag not in used:
                        findings.append(
                            (rel, event_id, "%s is written but never read" % flag)
                        )
                for flag in set(HAS_FLAG.findall(body)):
                    if flag not in written:
                        findings.append(
                            (rel, event_id, "%s is read but never written" % flag)
                        )
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=".", help="mod root")
    parser.add_argument(
        "--prefix", default="", help="only events mentioning this token"
    )
    parser.add_argument(
        "--effect-outcomes",
        action="store_true",
        help="count a scripted effect call as recording an outcome",
    )
    parser.add_argument("files", nargs="+", help="event files to preflight")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.path)
    targets = [f if os.path.isabs(f) else os.path.join(root, f) for f in args.files]
    missing = [t for t in targets if not os.path.isfile(t)]
    if missing:
        print("no such file: %s" % ", ".join(missing))
        return 2

    findings = check(root, targets, args.prefix, args.effect_outcomes)
    for rel, event_id, message in findings:
        print("%s: %s - %s" % (rel, event_id, message))
    print(
        "chain preflight: %s"
        % ("%d issue(s)" % len(findings) if findings else "no issues found")
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
