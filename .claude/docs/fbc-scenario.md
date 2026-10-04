# Federal Bureau of Control Scenario

The opt-in Federal Bureau of Control scenario. It is split into subsystems; each owns its own files and its own block of
event IDs, so parallel work does not collide. It ships on OEM only. Built like STALKER: see
[STALKER Scenario](stalker-scenario.md) for the patterns this follows.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's files.
  Add a subsystem with `python tools/generators/add_scenario.py subsystem FBC <name> "<Display>"`.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Gate everything** on `FBC_scenario_enabled = yes`. It reads a global flag that startup sets from
  `rule_fbc_scenario`; never read the rule from a trigger that can run at load.
- **Monthly work.** Add a line to `FBC_monthly_pulse` in `common/scripted_effects/99_FBC_pulse_effects.txt`. It runs once a month,
  in the scope of whichever country ticks first, so scope explicitly into what it touches.
- **AI.** Every decision and event option gets AI weights, and the AI must actually receive the
  content. If something is player-only, say so here. Check with `/scenario-audit FBC`.
- **Context.** Bind delayed events to a fixed state or a per-event target. Never read a shared
  "current site" global from a queued event.
- **Changelog.** Each PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.

## Subsystems

- **Core (1–9):** `FBC.txt`; loc `MD_FBC_l_english.yml`;
  `99_FBC_scripted_effects.txt`, `99_FBC_pulse_effects.txt`, `99_FBC_on_actions.txt`.
- **European Anomaly Desk (10–19):** `FBC_europe.txt`; loc `_europe_`;
  `99_FBC_europe_effects.txt`.

Localisation file names are `MD_FBC_<subsystem>_l_english.yml`.

The next free block is 20–29.

## Hooks into shared files

- `common/game_rules/00_game_rules.txt`: `rule_fbc_scenario`, off by default.
- `localisation/english/MD_game_rules_l_english.yml`: the rule's five keys.
- `common/scripted_effects/07_targeted_operations_organization_cases.txt`: `FBC_apply_top_organization_sabotage` beside the STALKER sabotage call.
- Targeted Operations organizations 39 and 40 in `tools/data/targeted_operations.json`. Both are public state-security records at the host capital, which is what that class allows.

The Bureau is its own scenario. It does not read STALKER state, and STALKER does not read Bureau state. The two Targeted Operations rows are the only shared runtime hook.

## Playable slice

Original cases, not a recreation of another game's plot. The United States holds two fixed sites: the Unscheduled Floor in New York (state 769) and the Sealed Wing in Washington (state 1182). Each case keeps its own phase and commitment. Response capacity starts at 2.

The European Anomaly Desk is an original body attached to the EU. Its name is provisional. The customs case uses Brussels (state 51) and the Ruhr (state 39). The coordinator is the Commission president when that office is filled, otherwise France, then Germany, then Belgium. Shared capacity is global because the coordinator can change. A queued customs event is bound to the country that received it.

Patriots content is not part of this scenario.
