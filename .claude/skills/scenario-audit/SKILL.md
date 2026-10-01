---
name: scenario-audit
description: 'Audit an opt-in scenario (STALKER, SILENTHILL, ...) for AI coverage and delayed-event context: decisions without AI weights, options without ai_chance, AI weights on events the AI never receives, and delayed events that read a shared global. Optionally checks it against a design doc. Use when asked whether the AI uses a scenario properly, to audit a scenario, or to check a scenario against a design spec, e.g. "/scenario-audit STALKER".'
---

Audit an opt-in scenario.

Arguments: $ARGUMENTS. Expect a scenario KEY (e.g. `STALKER`), optionally followed by the path to a design document. Ask for the KEY if it is missing.

1. Run:
   ```
   python tools/analysis/scenario_ai_audit.py KEY
   ```
2. Verify every finding by reading the code before reporting it. The tool is a heuristic:
   - **Player-only dispatch.** It flags events with AI weights whose every dispatch sits under `is_ai = no`. Read the dispatch and decide whether the gate is deliberate, as with crossover jokes, or a bug, as with `STALKER.2` before #451. Run `git log -S` on the gate first.
   - **Zero weights.** A decision with weight 0 may be deliberate. For example, the AI sells artifacts rather than giving them away.
   - **Delayed events.** A delayed event that reads `global.KEY_event_*` can be retargeted by a later dispatch. Prefer a fixed state or a per-event target.
3. Before trusting a clean run, prove the check can fire. Run it against a commit with a known finding, or against a fixture, using `--repo <path>`:
   ```
   git archive <commit> common events | tar -x -C <dir>
   ```
4. If a design document was given, add a requirement crosswalk. For each requirement, record its status (done, partial, not started or blocked) and the verified file or symbol. Name anything in today's code that conflicts with the spec. Keep the crosswalk off the issue tracker unless the user asks for it there.
5. Report in BLUF form:
   - confirmed bugs, with `path:line`
   - deliberate gates, which should be written down in the scenario doc
   - the smallest next fix
   
   Fix confirmed bugs as their own small PRs.
