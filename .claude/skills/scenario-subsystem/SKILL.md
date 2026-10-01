---
name: scenario-subsystem
description: 'Add a subsystem to an opt-in scenario (STALKER, or one made with /new-scenario): claims the next free event-ID block, writes its event, loc and effects files, wires its monthly pulse and records it in the scenario doc. Use when asked to add a subsystem, module or event-ID block to a scenario, e.g. "/scenario-subsystem STALKER silent_hill Silent Hill".'
---

Add a subsystem to a scenario.

Arguments: $ARGUMENTS. Expect the scenario KEY (e.g. `STALKER`), a lowercase subsystem name (e.g. `order`) and a display name for the doc (e.g. `The Order`). Ask for any that are missing.

1. Read `.claude/docs/<key>-scenario.md`, and confirm the work belongs in a new subsystem rather than an existing one. A new subsystem gets new files; content for an existing one goes in that subsystem's files.
2. Check the doc's next free block against every remote branch before claiming it. Another open PR may already use those IDs:
   ```
   git fetch origin
   for r in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin); do git grep -h -oE 'id = KEY\.[0-9]+' $r -- events; done | sort -u
   ```
   If the block is taken on a branch, stop and tell the user.
3. Run:
   ```
   python tools/generators/add_scenario.py subsystem KEY name "Display"
   ```
4. Report the claimed block and the files written:
   - `events/KEY_<name>.txt`
   - `MD_KEY_<name>_l_english.yml`
   - `99_KEY_<name>_effects.txt`, containing an empty `KEY_monthly_<name>_pulse`
   - the new line in `KEY_monthly_pulse`
   - the doc entry and the advanced "next free block" line
5. Remind the user:
   - Delete the empty pulse effect, and its line in `KEY_monthly_pulse`, if the subsystem has no monthly work.
   - Bind delayed events to a fixed state or a per-event target, never to a shared "current site" global.
   - Run `/scenario-audit KEY` before opening the PR.
