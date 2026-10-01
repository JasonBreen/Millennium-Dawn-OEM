---
name: new-scenario
description: 'Scaffold a new opt-in scenario built like STALKER: its own game rule (off by default), startup flag, monthly pulse, on_actions, event namespace, loc and scenario doc. Use when asked to start or scaffold a scenario such as Silent Hill, Deus Ex, the Overlook or Metal Gear, e.g. "/new-scenario SILENTHILL Silent Hill".'
---

Scaffold a new opt-in scenario.

Arguments: $ARGUMENTS. Expect a KEY (2-16 uppercase letters or digits, used as the event namespace and file prefix, e.g. `SILENTHILL`) and a display name (e.g. `Silent Hill`). If either is missing, ask for it. Also ask for the one-line text shown when the rule is enabled, unless the user already gave it.

1. Read `.claude/docs/stalker-scenario.md`. Every scenario follows its rules for file ownership, event-ID blocks and runtime traps.
2. Run:
   ```
   python tools/generators/add_scenario.py new KEY "Name" --description "Enabled text"
   ```
   The tool refuses an existing rule, loc key, event namespace or file before it writes anything. Report its error if it refuses.
3. Report what it wrote:
   - `rule_<key>_scenario` (off by default) and its loc
   - the startup flag and `KEY_scenario_enabled` trigger. Never read the rule directly in a trigger, because rules cannot be read while load-time triggers resolve.
   - `KEY_monthly_pulse`, called from the scenario's own `99_KEY_on_actions.txt`
   - the namespace, the loc file, and `.claude/docs/<key>-scenario.md`
4. Show the user the Enabled rule text. It is the author's voice, so let them change it.
5. Next steps for the user:
   - Add subsystems with `/scenario-subsystem KEY <name> "<Display>"`. Each takes the next free event-ID block.
   - Gate every decision and event on `KEY_scenario_enabled = yes`.
   - Give every decision and option AI weights, and make sure the AI actually receives them. `/scenario-audit KEY` checks this.
   - Scenarios ship on OEM only. Never open an upstream branch or PR for one unless the user says so.
   - The PR adds one BLUF line to `Changelog.txt`.
