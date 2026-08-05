#!/usr/bin/env python3
"""Repair the two focused CI failures introduced by the upstream sync.

This script is intentionally one-shot. The workflow removes it before committing
its output to the synchronization branch.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM_JAP_LOC = ROOT / "localisation/english/MD_focus_JAP_l_english.yml"
OEM_JAP_OVERRIDE = ROOT / "localisation/english/replace/MD_OEM_JAP_l_english.yml"
CONTRACT_VALIDATOR = ROOT / "tools/validation/validate_corporate_history_contract.py"

LOC_KEY_RE = re.compile(r"^\s*([^\s:#][^:]*):\d*\s+")


def localisation_keys(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8-sig")
    keys: set[str] = set()
    for line in text.splitlines():
        match = LOC_KEY_RE.match(line)
        if match:
            keys.add(match.group(1))
    return keys


def filter_oem_japan_override() -> tuple[int, int]:
    upstream_keys = localisation_keys(UPSTREAM_JAP_LOC)
    raw = OEM_JAP_OVERRIDE.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")

    retained: list[str] = []
    removed = 0
    for line in text.splitlines():
        match = LOC_KEY_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        if key in upstream_keys:
            removed += 1
            continue
        retained.append(line)

    if not retained:
        raise RuntimeError("Japan override filtering removed every key")

    retained_keys = {
        match.group(1)
        for line in retained
        if (match := LOC_KEY_RE.match(line)) is not None
    }
    duplicates = retained_keys & upstream_keys
    if duplicates:
        raise RuntimeError(
            f"Japan override still duplicates upstream keys: {sorted(duplicates)[:20]}"
        )

    payload = "l_english:\n" + "\n".join(retained) + "\n"
    encoded = payload.encode("utf-8")
    if had_bom:
        encoded = b"\xef\xbb\xbf" + encoded
    OEM_JAP_OVERRIDE.write_bytes(encoded)
    return removed, len(retained_keys)


def patch_contract_validator() -> None:
    text = CONTRACT_VALIDATOR.read_text(encoding="utf-8")

    old_glob = 'for filepath in self._collect_text_files(["localisation/english/*.yml"]):'
    new_glob = 'for filepath in self._collect_text_files(["localisation/english/**/*.yml"]):'
    if old_glob not in text and new_glob not in text:
        raise RuntimeError("Could not locate corporate localisation glob")
    text = text.replace(old_glob, new_glob, 1)

    old_block = '''            callers = yearly_calls.get(name, [])
            call_count = len(callers)
            if call_count != 1:
                findings.append(
                    (
                        f"{name} requires exactly one yearly-dispatch caller; found {call_count}",
                        definition.file,
                        definition.line,
                    )
                )
            year_match = re.search(r"_corporate_trigger_year_(\\d{4})$", name)
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
'''

    new_block = '''            callers = yearly_calls.get(name, [])
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
            year_match = re.search(r"_corporate_trigger_year_(\\d{4})$", name)
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
                    if on_action_file.replace("\\\\", "/") != expected_on_action:
                        findings.append(
                            (
                                f"{name} must be called by {expected_owner} or the dedicated OEM yearly on-action; found {on_action_file}",
                                on_action_file,
                                on_action_line,
                            )
                        )
'''

    if old_block in text:
        text = text.replace(old_block, new_block, 1)
    elif new_block not in text:
        raise RuntimeError("Could not locate yearly-dispatch validation block")

    CONTRACT_VALIDATOR.write_text(text, encoding="utf-8")


def main() -> None:
    removed, retained = filter_oem_japan_override()
    patch_contract_validator()
    print(
        f"Filtered Japan override: removed {removed} upstream keys; "
        f"retained {retained} fork-only keys."
    )
    print("Updated corporate-history validation for recursive localisation and OEM on-action dispatch.")


if __name__ == "__main__":
    main()
