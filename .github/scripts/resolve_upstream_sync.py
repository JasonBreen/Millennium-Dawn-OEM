#!/usr/bin/env python3
"""Resolve the exact August 5 OEM/upstream merge conflict set."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

EXPECTED_CONFLICTS = [
    "common/scripted_effects/00_yearly_effects.txt",
    "localisation/english/MD_focus_JAP_l_english.yml",
    "localisation/french/MD_focus_CHI_l_french.yml",
    "localisation/french/MD_techs_l_french.yml",
    "localisation/german/MD_focus_CHI_l_german.yml",
    "localisation/german/MD_techs_l_german.yml",
    "localisation/japanese/MD_countries_cosmetic_l_japanese.yml",
    "localisation/japanese/MD_focus_CHI_l_japanese.yml",
    "localisation/japanese/MD_money_l_japanese.yml",
    "localisation/japanese/MD_techs_l_japanese.yml",
    "localisation/japanese/MD_tooltips_l_japanese.yml",
    "localisation/japanese/MD_traits_l_japanese.yml",
    "localisation/korean/MD_cats_generic_defcomp_l_korean.yml",
    "localisation/korean/MD_countries_cosmetic_l_korean.yml",
    "localisation/korean/MD_focus_CHI_l_korean.yml",
    "localisation/korean/MD_formable_nations_l_korean.yml",
    "localisation/korean/MD_global_reaction_l_korean.yml",
    "localisation/korean/MD_operations_l_korean.yml",
    "localisation/korean/MD_techs_l_korean.yml",
    "localisation/korean/MD_tooltips_l_korean.yml",
    "localisation/korean/replace/replaced_from_doctrines_l_korean.yml",
    "localisation/polish/MD_focus_CHI_l_polish.yml",
    "localisation/polish/MD_techs_l_polish.yml",
    "localisation/russian/MD_countries_cosmetic_l_russian.yml",
    "localisation/russian/MD_country_politics_view_l_russian.yml",
    "localisation/russian/MD_focus_JAP_l_russian.yml",
    "localisation/russian/MD_focus_USA_l_russian.yml",
    "localisation/russian/MD_techs_l_russian.yml",
    "localisation/russian/MD_tooltips_l_russian.yml",
    "localisation/simp_chinese/MD_focus_CHI_l_simp_chinese.yml",
    "localisation/simp_chinese/MD_focus_USA_l_simp_chinese.yml",
    "localisation/simp_chinese/MD_opinion_modifiers_l_simp_chinese.yml",
    "localisation/simp_chinese/MD_techs_l_simp_chinese.yml",
    "localisation/simp_chinese/MD_tooltips_l_simp_chinese.yml",
    "localisation/spanish/MD_focus_CHI_l_spanish.yml",
    "localisation/spanish/MD_techs_l_spanish.yml",
]

NON_ENGLISH_LOCALISATION = [
    path
    for path in EXPECTED_CONFLICTS
    if path.startswith("localisation/")
    and path != "localisation/english/MD_focus_JAP_l_english.yml"
]

YEARLY_EFFECTS = "common/scripted_effects/00_yearly_effects.txt"
ENGLISH_JAPAN = "localisation/english/MD_focus_JAP_l_english.yml"
KEY_RE = re.compile(r"^\s*([^#\s][^:]*):")


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else ""


def script_brace_delta(lines: list[str]) -> int:
    delta = 0
    for line in lines:
        quoted = False
        escaped = False
        for char in line:
            if escaped:
                escaped = False
                continue
            if char == "\\" and quoted:
                escaped = True
                continue
            if char == '"':
                quoted = not quoted
                continue
            if char == "#" and not quoted:
                break
            if not quoted:
                if char == "{":
                    delta += 1
                elif char == "}":
                    delta -= 1
    return delta


def resolve_yearly_effects() -> None:
    path = Path(YEARLY_EFFECTS)
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    output: list[str] = []
    index = 0
    resolved = 0

    while index < len(lines):
        if lines[index].lstrip().startswith("<<<<<<< "):
            index += 1
            ours: list[str] = []
            while index < len(lines) and not lines[index].lstrip().startswith("======="):
                ours.append(lines[index])
                index += 1
            if index >= len(lines):
                raise RuntimeError("unterminated yearly-effects conflict before separator")
            index += 1

            theirs: list[str] = []
            while index < len(lines) and not lines[index].lstrip().startswith(">>>>>>> "):
                theirs.append(lines[index])
                index += 1
            if index >= len(lines):
                raise RuntimeError("unterminated yearly-effects conflict after separator")
            index += 1

            delta = script_brace_delta(ours)
            if delta < 0 or delta > 2:
                raise RuntimeError(
                    f"unexpected fork-side brace delta in yearly conflict: {delta}"
                )

            output.extend(ours)
            output.extend("\t}\n" for _ in range(delta))
            output.extend(theirs)
            resolved += 1
        else:
            output.append(lines[index])
            index += 1

    text = "".join(output)
    if resolved != 5:
        raise RuntimeError(
            f"expected five yearly-effects conflict regions, resolved {resolved}"
        )
    if any(marker in text for marker in ("<<<<<<<", "=======", ">>>>>>>")):
        raise RuntimeError("yearly-effects conflict marker remains")
    if script_brace_delta(output) != 0:
        raise RuntimeError("yearly-effects braces are unbalanced after resolution")

    path.write_text(text, encoding="utf-8")
    run("git", "add", YEARLY_EFFECTS)


def read_stage(number: int, path: str) -> tuple[list[str], bool]:
    raw = subprocess.check_output(["git", "show", f":{number}:{path}"])
    return raw.decode("utf-8-sig").splitlines(), raw.startswith(b"\xef\xbb\xbf")


def catalogue(lines: list[str], label: str) -> tuple[dict[str, str], list[str]]:
    mapping: dict[str, str] = {}
    order: list[str] = []
    for line in lines:
        match = KEY_RE.match(line)
        if not match:
            continue
        key = match.group(1)
        if key in mapping:
            raise RuntimeError(f"duplicate localisation key in {label}: {key}")
        mapping[key] = line
        order.append(key)
    return mapping, order


def oem_owned(key: str) -> bool:
    lowered = key.lower()
    return (
        key.startswith(("JAP_sony", "JAP_nintendo", "JAP_oem"))
        or "_sony_" in lowered
        or "_nintendo_" in lowered
        or "playstation" in lowered
    )


def resolve_english_japan() -> None:
    base_lines, _ = read_stage(1, ENGLISH_JAPAN)
    ours_lines, _ = read_stage(2, ENGLISH_JAPAN)
    theirs_lines, theirs_bom = read_stage(3, ENGLISH_JAPAN)

    base, _ = catalogue(base_lines, "merge base")
    ours, ours_order = catalogue(ours_lines, "fork")
    theirs, _ = catalogue(theirs_lines, "upstream")

    result: list[str | None] = list(theirs_lines)
    positions: dict[str, int] = {}
    for index, line in enumerate(theirs_lines):
        match = KEY_RE.match(line)
        if match:
            positions[match.group(1)] = index

    additions: list[str] = []
    all_keys = set(base) | set(ours) | set(theirs)
    ours_rank = {key: index for index, key in enumerate(ours_order)}

    for key in sorted(all_keys, key=lambda item: (ours_rank.get(item, 10**9), item)):
        base_line = base.get(key)
        ours_line = ours.get(key)
        theirs_line = theirs.get(key)
        ours_changed = ours_line != base_line
        theirs_changed = theirs_line != base_line

        target = theirs_line
        if ours_changed and not theirs_changed:
            target = ours_line
        elif ours_changed and theirs_changed:
            if ours_line == theirs_line:
                target = ours_line
            elif oem_owned(key):
                target = ours_line
            else:
                target = theirs_line

        if target == theirs_line:
            continue
        if key in positions:
            result[positions[key]] = target
        elif target is not None:
            additions.append(target)

    merged = [line for line in result if line is not None]
    if additions:
        while merged and not merged[-1].strip():
            merged.pop()
        merged.extend(
            [
                "",
                "# OEM fork localisation preserved during upstream synchronization",
                *additions,
            ]
        )

    final, _ = catalogue(merged, "resolved output")
    expected_keys = {
        key
        for key in all_keys
        if (
            theirs.get(key) is not None
            or (ours.get(key) != base.get(key) and ours.get(key) is not None)
        )
    }
    missing = sorted(expected_keys - set(final))
    if missing:
        raise RuntimeError(f"resolved localisation lost keys: {missing[:20]}")

    payload = ("\n".join(merged) + "\n").encode("utf-8")
    if theirs_bom:
        payload = b"\xef\xbb\xbf" + payload
    Path(ENGLISH_JAPAN).write_bytes(payload)
    run("git", "add", ENGLISH_JAPAN)


def main() -> int:
    actual = sorted(
        line
        for line in run(
            "git", "diff", "--name-only", "--diff-filter=U", capture=True
        ).splitlines()
        if line
    )
    if actual != EXPECTED_CONFLICTS:
        print("unexpected conflict set", file=sys.stderr)
        print("expected:", *EXPECTED_CONFLICTS, sep="\n  ", file=sys.stderr)
        print("actual:", *actual, sep="\n  ", file=sys.stderr)
        return 2

    for path in NON_ENGLISH_LOCALISATION:
        run("git", "checkout", "--theirs", "--", path)
        run("git", "add", path)

    resolve_yearly_effects()
    resolve_english_japan()

    remaining = run(
        "git", "diff", "--name-only", "--diff-filter=U", capture=True
    ).strip()
    if remaining:
        raise RuntimeError(f"unresolved paths remain:\n{remaining}")

    print(
        "Resolved 36 known conflicts: 34 exact upstream translations, "
        "yearly dispatcher union, and semantic English Japan localisation merge."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
