# Deus Ex Scenario

The opt-in Deus Ex scenario. It is split into subsystems; each owns its own files and its own block of
event IDs, so parallel work does not collide. It ships on OEM only. Built like STALKER: see
[STALKER Scenario](stalker-scenario.md) for the patterns this follows.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's files.
  Add a subsystem with `python tools/generators/add_scenario.py subsystem DEUSEX <name> "<Display>"`.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Gate everything** on `DEUSEX_scenario_enabled = yes`. It reads a global flag that startup sets from
  `rule_deusex_scenario`; never read the rule from a trigger that can run at load.
- **Monthly work.** Add a line to `DEUSEX_monthly_pulse` in `common/scripted_effects/99_DEUSEX_pulse_effects.txt`. It runs once a month,
  in the scope of whichever country ticks first, so scope explicitly into what it touches.
- **AI.** Every decision and event option gets AI weights, and the AI must actually receive the
  content. If something is player-only, say so here. Check with `/scenario-audit DEUSEX`.
- **Context.** Bind delayed events to a fixed state or a per-event target. Never read a shared
  "current site" global from a queued event.
- **Changelog.** Each PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.

## Subsystems

- **Core (1–9):** `DEUSEX.txt`; loc `MD_DEUSEX_l_english.yml`;
  `99_DEUSEX_scripted_effects.txt`, `99_DEUSEX_pulse_effects.txt`, `99_DEUSEX_on_actions.txt`.

Localisation file names are `MD_DEUSEX_<subsystem>_l_english.yml`.

The next free block is 10–19.

## Hooks into shared files

- `common/game_rules/00_game_rules.txt`: `rule_deusex_scenario`, off by default.
- `localisation/english/MD_game_rules_l_english.yml`: the rule's five keys.

Everything else lives in the scenario's own files, including its on_actions.
