#!/usr/bin/env python3
"""Scaffold an opt-in scenario, or add a subsystem to one, the way STALKER is built.

A scenario owns its files and its event-ID blocks. Its only edits to shared files
are its game rule and the rule's English loc. Its own on_actions file records the
rule in a global flag at startup (game rules cannot be read while load-time
triggers resolve) and runs its monthly pulse.

Usage:
    python tools/generators/add_scenario.py new SILENTHILL "Silent Hill" \
        --description "The town of Silent Hill, Maine, has always been wrong."
    python tools/generators/add_scenario.py subsystem SILENTHILL order "The Order"

`subsystem` also works on STALKER: it takes the next free event-ID block from the
scenario's doc, writes the subsystem's event, loc and effects files, adds its
monthly pulse and records it in the doc.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.paths import REPO_ROOT
from shared_utils import atomic_write_text, read_text_strict

RULES = "common/game_rules/00_game_rules.txt"
RULES_LOC = "localisation/english/MD_game_rules_l_english.yml"
DOC_INDEX = ".claude/docs/documentation-references.md"
INDEX_ANCHOR = "| `stalker-scenario.md`"

KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{1,15}$")
SUBSYSTEM_RE = re.compile(r"^[a-z][a-z0-9_]{1,30}$")
NEXT_BLOCK_RE = re.compile(r"The next free block is (\d+)[–-](\d+)\.")
BLOCK_SIZE = 10


class ToolError(Exception):
    pass


def paths(key):
    lower = key.lower()
    return {
        "triggers": f"common/scripted_triggers/99_{key}_scripted_triggers.txt",
        "effects": f"common/scripted_effects/99_{key}_scripted_effects.txt",
        "pulse": f"common/scripted_effects/99_{key}_pulse_effects.txt",
        "on_actions": f"common/on_actions/99_{key}_on_actions.txt",
        "events": f"events/{key}.txt",
        "loc": f"localisation/english/MD_{key}_l_english.yml",
        "doc": f".claude/docs/{lower}-scenario.md",
    }


def single_line(value, field):
    if not value.strip() or "\n" in value or '"' in value:
        raise ToolError(f"{field} must be one line of text without double quotes")
    return value.strip()


def read(repo, rel):
    return read_text_strict(str(repo / rel)).replace("\r\n", "\n")


def write(repo, rel, text, bom=False):
    atomic_write_text(str(repo / rel), text, bom=bom)


def namespace_taken(repo, key):
    pattern = re.compile(rf"^\s*add_namespace\s*=\s*{re.escape(key)}\s*$", re.M)
    for path in (repo / "events").glob("*.txt"):
        if pattern.search(read_text_strict(str(path))):
            return path.name
    return None


def rule_block(key):
    lower = key.lower()
    return (
        f"\nrule_{lower}_scenario = {{\n"
        f'\tname = "RULE_{key}_SCENARIO"\n'
        '\tgroup = "MD_CUSTOM_SCENARIO_RULES"\n'
        '\ticon = "GFX_production_licenses"\n'
        "\n"
        "\tdefault = {\n"
        "\t\tname = DISABLED\n"
        f'\t\ttext = "RULE_{key}_SCENARIO_DISABLED"\n'
        f'\t\tdesc = "RULE_{key}_SCENARIO_DISABLED_DESC"\n'
        "\t}\n"
        "\toption = {\n"
        "\t\tname = ENABLED\n"
        f'\t\ttext = "RULE_{key}_SCENARIO_ENABLED"\n'
        f'\t\tdesc = "RULE_{key}_SCENARIO_ENABLED_DESC"\n'
        "\t\tallow_achievements = no\n"
        "\t}\n"
        "}\n"
    )


def rule_loc(key, name, description):
    return (
        f' RULE_{key}_SCENARIO: "{name} Scenario"\n'
        f' RULE_{key}_SCENARIO_DISABLED: "Disabled"\n'
        f' RULE_{key}_SCENARIO_DISABLED_DESC: "The {name} scenario remains inactive."\n'
        f' RULE_{key}_SCENARIO_ENABLED: "Enabled"\n'
        f' RULE_{key}_SCENARIO_ENABLED_DESC: "{description}"\n'
    )


def scenario_files(key, name):
    lower = key.lower()
    p = paths(key)
    flag = f"GLOBAL_{key}_scenario_enabled"
    return {
        p["triggers"]: (
            "# The rule is unavailable while load-time triggers resolve; startup records it in a flag.\n"
            f"{key}_scenario_enabled = {{\n\thas_global_flag = {flag}\n}}\n"
        ),
        p["effects"]: (
            f"{key}_initialize_scenario = {{\n"
            "\tif = {\n"
            "\t\tlimit = {\n"
            f"\t\t\thas_game_rule = {{ rule = rule_{lower}_scenario option = ENABLED }}\n"
            f"\t\t\tNOT = {{ has_global_flag = {flag} }}\n"
            "\t\t}\n"
            f"\t\tset_global_flag = {flag}\n"
            "\t}\n"
            "}\n"
        ),
        p["pulse"]: (
            f"# The {name} monthly entry point; each subsystem adds its monthly pulse here.\n"
            f"{key}_monthly_pulse = {{\n}}\n"
        ),
        p["on_actions"]: (
            "on_actions = {\n"
            "\ton_startup = {\n"
            "\t\teffect = {\n"
            f"\t\t\trandom_country = {{ {key}_initialize_scenario = yes }}\n"
            "\t\t}\n"
            "\t}\n"
            "\n"
            "\t# on_monthly fires for every country; the flag runs the pulse once a month.\n"
            "\ton_monthly = {\n"
            "\t\teffect = {\n"
            "\t\t\tif = {\n"
            "\t\t\t\tlimit = {\n"
            f"\t\t\t\t\t{key}_scenario_enabled = yes\n"
            f"\t\t\t\t\tNOT = {{ has_global_flag = {key}_monthly_pulse_done }}\n"
            "\t\t\t\t}\n"
            f"\t\t\t\tset_global_flag = {{ flag = {key}_monthly_pulse_done value = 1 days = 27 }}\n"
            f"\t\t\t\t{key}_monthly_pulse = yes\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t}\n"
            "}\n"
        ),
        p["events"]: f"add_namespace = {key}\n",
        p["loc"]: "l_english:\n",
        p["doc"]: scenario_doc(key, name),
    }


def scenario_doc(key, name):
    lower = key.lower()
    p = paths(key)
    return f"""# {name} Scenario

The opt-in {name} scenario. It is split into subsystems; each owns its own files and its own block of
event IDs, so parallel work does not collide. It ships on OEM only. Built like STALKER: see
[STALKER Scenario](stalker-scenario.md) for the patterns this follows.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's files.
  Add a subsystem with `python tools/generators/add_scenario.py subsystem {key} <name> "<Display>"`.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Gate everything** on `{key}_scenario_enabled = yes`. It reads a global flag that startup sets from
  `rule_{lower}_scenario`; never read the rule from a trigger that can run at load.
- **Monthly work.** Add a line to `{key}_monthly_pulse` in `{p["pulse"]}`. It runs once a month,
  in the scope of whichever country ticks first, so scope explicitly into what it touches.
- **AI.** Every decision and event option gets AI weights, and the AI must actually receive the
  content. If something is player-only, say so here. Check with `/scenario-audit {key}`.
- **Context.** Bind delayed events to a fixed state or a per-event target. Never read a shared
  "current site" global from a queued event.
- **Changelog.** Each PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.

## Subsystems

- **Core (1–9):** `{p["events"].split("/")[-1]}`; loc `{p["loc"].split("/")[-1]}`;
  `{p["effects"].split("/")[-1]}`, `{p["pulse"].split("/")[-1]}`, `{p["on_actions"].split("/")[-1]}`.

Localisation file names are `MD_{key}_<subsystem>_l_english.yml`.

The next free block is 10–19.

## Hooks into shared files

- `{RULES}`: `rule_{lower}_scenario`, off by default.
- `{RULES_LOC}`: the rule's five keys.

Everything else lives in the scenario's own files, including its on_actions.
"""


def add_scenario(repo, key, name, description):
    repo = Path(repo)
    if not KEY_RE.match(key):
        raise ToolError(
            "KEY must be 2-16 uppercase letters or digits, starting with a letter, e.g. SILENTHILL"
        )
    name = single_line(name, "name")
    description = single_line(description, "description")
    lower = key.lower()
    rules = read(repo, RULES)
    if re.search(rf"^rule_{lower}_scenario\s*=", rules, re.M):
        raise ToolError(f"rule_{lower}_scenario already exists in {RULES}")
    rules_loc = read(repo, RULES_LOC)
    for suffix in ("", "_DISABLED", "_DISABLED_DESC", "_ENABLED", "_ENABLED_DESC"):
        loc_key = f"RULE_{key}_SCENARIO{suffix}"
        if re.search(rf"^\s*{loc_key}:", rules_loc, re.M):
            raise ToolError(f"{loc_key} already exists in {RULES_LOC}")
    taken = namespace_taken(repo, key)
    if taken:
        raise ToolError(f"event namespace {key} is already used in events/{taken}")
    files = scenario_files(key, name)
    existing = [rel for rel in files if (repo / rel).exists()]
    if existing:
        raise ToolError("refusing to overwrite: " + ", ".join(existing))

    write(repo, RULES, rules.rstrip("\n") + "\n" + rule_block(key))
    write(
        repo,
        RULES_LOC,
        rules_loc.rstrip("\n") + "\n" + rule_loc(key, name, description),
        bom=True,
    )
    for rel, text in files.items():
        write(repo, rel, text, bom=rel.endswith(".yml"))
    written = [RULES, RULES_LOC, *files]
    index_path = repo / DOC_INDEX
    if index_path.exists():
        index = read(repo, DOC_INDEX)
        row = f"| `{lower}-scenario.md` | {name} scenario files, event-ID blocks, hooks |\n"
        if INDEX_ANCHOR in index and row not in index:
            at = index.index(INDEX_ANCHOR)
            index = index[:at] + row + index[at:]
            write(repo, DOC_INDEX, index)
            written.append(DOC_INDEX)
    return written


def add_subsystem(repo, key, subsystem, display):
    repo = Path(repo)
    if not KEY_RE.match(key):
        raise ToolError("KEY must be the scenario's uppercase key, e.g. STALKER")
    if not SUBSYSTEM_RE.match(subsystem):
        raise ToolError(
            "subsystem must be lowercase letters, digits and underscores, e.g. order"
        )
    display = single_line(display, "display name")
    p = paths(key)
    if not (repo / p["doc"]).exists() or not (repo / p["pulse"]).exists():
        raise ToolError(f"no {key} scenario here: expected {p['doc']} and {p['pulse']}")
    doc = read(repo, p["doc"])
    match = NEXT_BLOCK_RE.search(doc)
    if not match:
        raise ToolError(f"{p['doc']} has no 'The next free block is N–M.' line")
    first, last = int(match.group(1)), int(match.group(2))
    id_re = re.compile(rf"\bid\s*=\s*{re.escape(key)}\.(\d+)\b")
    for path in sorted(
        [*repo.glob(f"events/{key}.txt"), *repo.glob(f"events/{key}_*.txt")]
    ):
        used = [int(n) for n in id_re.findall(read_text_strict(str(path)))]
        clash = [n for n in used if first <= n <= last]
        if clash:
            raise ToolError(
                f"event-ID block {first}–{last} is already used in {path.name} "
                f"({key}.{clash[0]}); fix the doc's next free block line"
            )
    events = f"events/{key}_{subsystem}.txt"
    loc = f"localisation/english/MD_{key}_{subsystem}_l_english.yml"
    effects = f"common/scripted_effects/99_{key}_{subsystem}_effects.txt"
    pulse_name = f"{key}_monthly_{subsystem}_pulse"
    existing = [rel for rel in (events, loc, effects) if (repo / rel).exists()]
    if existing:
        raise ToolError("refusing to overwrite: " + ", ".join(existing))
    pulse = read(repo, p["pulse"])
    if f"{pulse_name} = yes" in pulse:
        raise ToolError(f"{pulse_name} is already in {p['pulse']}")
    definition = re.compile(rf"^\s*{re.escape(pulse_name)}\s*=\s*\{{", re.M)
    for path in sorted((repo / "common/scripted_effects").glob("*.txt")):
        if definition.search(read_text_strict(str(path))):
            raise ToolError(f"{pulse_name} is already defined in {path.name}")
    head = re.search(rf"^{key}_monthly_pulse\s*=\s*\{{", pulse, re.M)
    if not head:
        raise ToolError(f"{p['pulse']} does not define {key}_monthly_pulse")
    close = pulse.find("\n}", head.end())
    if close < 0:
        raise ToolError(f"{key}_monthly_pulse in {p['pulse']} is not closed")
    pulse = pulse[:close] + f"\n\t{pulse_name} = yes" + pulse[close:]

    bullet = (
        f"- **{display} ({first}–{last}):** `{key}_{subsystem}.txt`; loc `_{subsystem}_`;\n"
        f"  `99_{key}_{subsystem}_effects.txt`.\n"
    )
    section = doc.find("## Subsystems")
    marker = doc.find("\nLocalisation file names are", section)
    if section < 0 or marker < 0:
        raise ToolError(
            f"{p['doc']} needs a '## Subsystems' list followed by 'Localisation file names are'"
        )
    body = doc[:marker].rstrip("\n") + "\n" + bullet + doc[marker:]
    body = NEXT_BLOCK_RE.sub(
        f"The next free block is {last + 1}–{last + BLOCK_SIZE}.", body, count=1
    )

    write(repo, events, f"add_namespace = {key}\n")
    write(repo, loc, "l_english:\n", bom=True)
    write(repo, effects, f"{pulse_name} = {{\n}}\n")
    write(repo, p["pulse"], pulse)
    write(repo, p["doc"], body)
    return (first, last), [events, loc, effects, p["pulse"], p["doc"]]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repo", default=str(REPO_ROOT), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="scaffold a new opt-in scenario")
    new.add_argument("key", help="uppercase key and event namespace, e.g. SILENTHILL")
    new.add_argument("name", help='display name, e.g. "Silent Hill"')
    new.add_argument(
        "--description", required=True, help="the rule's Enabled description"
    )
    subsystem = sub.add_parser(
        "subsystem", help="add a subsystem with the next free event-ID block"
    )
    subsystem.add_argument("key", help="the scenario's key, e.g. STALKER")
    subsystem.add_argument("name", help="lowercase subsystem name, e.g. order")
    subsystem.add_argument("display", help='display name for the doc, e.g. "The Order"')
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            written = add_scenario(args.repo, args.key, args.name, args.description)
            print(f"Scaffolded the {args.key} scenario:")
        else:
            (first, last), written = add_subsystem(
                args.repo, args.key, args.name, args.display
            )
            print(
                f"Added {args.key} subsystem '{args.name}' with event IDs {first}-{last}:"
            )
    except (ToolError, OSError, UnicodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for rel in written:
        print(f"  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
