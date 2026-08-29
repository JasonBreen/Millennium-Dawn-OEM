# Great AI Race Claude Implementation Campaign

Status: phased implementation prompts. Run one prompt at a time. Stop after its acceptance report and obtain approval before beginning the next phase.

Architecture contract: `.claude/docs/great-ai-race-architecture.md`

Reference study: `.claude/docs/great-ai-race-reference-study.md`

## How to use this campaign

Each prompt is a dependency-complete, reviewable slice. A phase may refine the file map after current-repository reconnaissance, but it may not silently change state ownership, runtime modes, scales, or the TNO/TFR inspiration boundary.

Do not concatenate the prompts into one large implementation request. The campaign deliberately proves the headless state model before the GUI, proves a small lab roster before participant expansion, and proves one pressure/crisis loop before world integration.

### Common instruction block

Prepend this block to every implementation prompt:

> You are working in the Millennium Dawn OEM repository. Read `AGENTS.md`, `.claude/docs/great-ai-race-architecture.md`, `.claude/docs/great-ai-race-reference-study.md`, and every repository reference named by this phase before editing. Preserve the architecture's ownership ledger: existing national, corporate, technology, economic, and AI Core systems remain authoritative; the Great AI Race reads them through adapters. TNO and TFR are mechanical references only. Do not copy their script, localisation, art, fonts, layouts, or assets. Use tabs, repository naming, English-only localisation, scoped validation, and the established monthly singleton. Never use a daily global poll, `every_country`, GUI-owned AI logic, event targets in scripted GUI, `pre-commit run --all-files`, or an unseeded/random fixed-sum balancer. Do not edit non-English localisation, `resources/`, or `Changelog.txt`. Do not commit, push, open a PR, or mutate GitHub unless separately authorized. Preserve unrelated worktree changes.

### Required handoff after every phase

Claude must end each phase with:

1. Exact files inspected.
2. Exact files changed.
3. State objects added or changed, with owner, scope, range, and writer list.
4. Mode behavior for Full, Outcomes Only, and Off.
5. Static tests or validators run, including exact commands and results.
6. Runtime evidence actually obtained, clearly separated from static or console-fixture evidence.
7. Known limitations and unresolved questions.
8. A one-paragraph dependency handoff for the next phase.
9. Current branch, `HEAD`, and concise worktree status.

Never call static parsing, a console fixture, or a rendered mockup natural HOI4 runtime acceptance.

## Campaign dependency map

```text
0 Contract freeze
  -> 1 Headless kernel and runtime modes
    -> 2 National adapters, frontier, and ranking
      -> 3 Overview dashboard vertical slice
        -> 4 Laboratory politics and support shares
          -> 5 Training projects and model releases
            -> 6 Public alarm, control debt, and crisis windows
              -> 7 Compute and semiconductor economy
                -> 8 Policy, talent, and foreign intelligence
                  -> 9 Breakthroughs, race temperature, and alerts
                    -> 10 Deployment and world integration
                      -> 11 Participant expansion and AI balance
                        -> 12 Runtime hardening and release evidence
```

## Prompt 0 - Contract Freeze and Current-Checkout Audit

### Objective

Confirm that the architecture remains implementable against the current checkout and turn every code-blocking design question into a locked contract. Do not implement gameplay.

### Work

- Re-run collision searches for `AI_RACE_`, `ai_race_`, `rule_ai_race`, and planned filenames.
- Verify the USA AI Industry Core and company receiver ownership boundaries.
- Verify the exact ordered call site in the existing global monthly singleton.
- Verify current examples for country-scope arrays, fixed-ID arrays, sorted arrays, native mission clocks, dynamic lists, decision-category scripted GUIs, alert tokens, and deterministic random validation.
- Freeze the initial participants: USA and China.
- Freeze the activation rule: startup foundation state plus the exact date/capability rule that makes the competitive dashboard active.
- Freeze the six national metric names, polarity, scale, initial source, stock owner, adapter inputs, and clamp path.
- Freeze the two national pressure metrics: public alarm and control debt.
- Freeze the global score formula, frontier definition, ranking tie-break, race-temperature thresholds, and update order.
- Freeze the Full / Outcomes Only / Off visibility and simulation matrix.
- Freeze the initial debug surface and the exact runtime scenarios it must support.
- Record any departure from the architecture as a proposed document change, not an implicit implementation choice.

### Deliverables

- Update the architecture/reference documents only where live evidence requires it.
- Add a compact state dictionary to the architecture if any owner/writer/range is still ambiguous.
- Produce a phase-by-phase file allowlist for Prompts 1-3.

### Acceptance

- No unresolved question changes the implementation of Prompt 1.
- Corporate History and Great AI Race mode combinations are explicitly orthogonal.
- No TNO/TFR source is named as a dependency at runtime.
- No gameplay file is changed.

### Frozen Phase 1 result

The current checkout resolves Prompt 1's previously open implementation choices as follows:

- Bootstrap occurs on the first enabled call from OEM's existing guarded global monthly singleton. The same idempotent path repairs late bookmarks and loaded saves; there is no hidden event or second startup owner.
- `AI_RACE_active` means eligible and registered in the headless kernel. The later public dashboard activation date or capability threshold remains a separate product decision.
- USA and China are registered as country scopes in that fixed order. Exact capability ties resolve to USA; the signed frontier gap is `capability - frontier`.
- Phase 1 external slots are explicit zero-valued scaffolding. Prompt 2 replaces those zeros with read-only canonical adapters.
- The replay guard is encoded as `year * 4 + quarter index`.
- `ai_race_rebuild_derived_state` is pure and repeatable. Only the scheduled quarterly wrapper advances the epoch, dirty counter, and future interval state.
- The enabled-mode gate is at the singleton caller, so Off performs no Great AI Race callback and exposes no debug category.
- Phase 1 contains no event namespace or event file.

### Prompt 1-3 file allowlist

| Prompt | Files allowed to change |
|---|---|
| 1 | `common/game_rules/00_game_rules.txt`; `common/on_actions/MD_on_actions.txt`; `common/scripted_triggers/MD_great_ai_race_triggers.txt`; `common/scripted_effects/00_great_ai_race_effects.txt`; `common/decisions/categories/MD_great_ai_race_categories.txt`; `common/decisions/MD_great_ai_race_decisions.txt`; `localisation/english/MD_game_rules_l_english.yml`; `localisation/english/MD_great_ai_race_l_english.yml`; these three planning documents |
| 2 | Great AI Race trigger/effect/debug/localisation files above; explicitly approved read-only owner files may be inspected but not edited |
| 3 | Great AI Race category/decision/trigger/effect/localisation files plus new `common/scripted_guis/01_great_ai_race_scripted_gui.txt`, `interface/MD_great_ai_race.gui`, and `interface/MD_great_ai_race.gfx` |

## Prompt 1 - Headless Kernel and Runtime Modes

### Objective

Implement the smallest headless Great AI Race kernel for USA and China. There is no normal player dashboard in this phase.

### Required scope

- Add a separate `rule_ai_race` with Full, Outcomes Only, and Off options.
- Add scripted triggers for Full, Outcomes Only, enabled, disabled, eligible participant, initialized country, active race, and debug visibility.
- Add an idempotent global initializer.
- Add an idempotent country initializer for USA and China.
- Add the six `0..100` national metrics with the stock/external/effective ownership shape where external adapters will exist.
- Add public alarm and control debt as bounded country state, but do not yet add their recurring missions.
- Add global frontier, temperature, pressure, leader, epoch, participant array, and ranked-array placeholders.
- Add one clamp/repair effect and one debug-only readout/repair surface.
- Reset the six external-contribution slots to zero without reading or writing any owner system.
- Rebuild participants and derived ranking state deterministically for USA and China; capability-only ranking is an explicit Phase 1 scaffold, not the final national score formula.
- Store `year * 4 + quarter index` as a replay guard and separate pure derived-state repair from scheduled state advancement.
- In Off, create no race variables, arrays, flags, ideas, missions, alerts, or categories.
- Gate one initialization/quarterly call at the existing global monthly singleton; Off must not enter the dispatcher.

### Out of scope

- Final score formula.
- External-system adapters.
- Normal GUI.
- Labs, projects, releases, events, alerts, policies, or modifiers.
- Participant expansion beyond USA and China.

### Files

Expected primary files:

- `common/game_rules/00_game_rules.txt`
- `common/scripted_triggers/MD_great_ai_race_triggers.txt`
- `common/scripted_effects/00_great_ai_race_effects.txt`
- `common/on_actions/MD_on_actions.txt`
- `common/decisions/categories/MD_great_ai_race_categories.txt`
- `common/decisions/MD_great_ai_race_decisions.txt`
- `localisation/english/MD_game_rules_l_english.yml`
- `localisation/english/MD_great_ai_race_l_english.yml`

If a `tools/tests` regression test is added, run the full `python -m pytest` gate required by repository policy.

### Acceptance

- Full and Outcomes Only initialize exactly once.
- Off leaves no race state.
- Re-running every initializer and repair effect is safe.
- The six national metrics, public alarm, and control debt repair to `0..100`; signed frontier gap repairs to `-100..0`.
- USA/China registration produces country scopes, not stored tags or event targets.
- Save/reload does not repeat initialization effects.
- Debug repair does not advance the quarterly epoch or replay guard.
- A fresh Off game does not call the race dispatcher or expose the debug category.
- No normal player-facing feature is claimed complete.

## Prompt 2 - National Adapters, Frontier, and Ranking

### Objective

Make the headless kernel compute meaningful national values and a deterministic two-country race without mutating existing systems.

### Required scope

- Implement a USA adapter that reads the USA AI Industry Core and other explicitly approved canonical inputs.
- Implement a China adapter from canonical Chinese technology, industrial, research, energy, semiconductor, and national state actually present in the repository.
- Provide deterministic fallbacks when Corporate History is disabled or a canonical optional source is absent.
- Rebuild every external contribution from zero.
- Calculate all effective metrics from stock plus external contribution, then clamp.
- Replace or explicitly retain the Phase 1 capability-only scaffold with one documented national score formula.
- Extend the existing frontier maximum, leader, signed frontier gap, deterministic rank, and fixed tie-break without changing their ownership contract.
- Rebuild `global.ai_race_ranked_participants` without sorting a shared generic array in place.
- Extend the ordered monthly/quarterly reducer defined by the architecture.
- Preserve the existing replay guard and pure-rebuild/scheduled-advance split.
- Extend debug readouts to show canonical input, external contribution, stock, effective total, score, rank, and frontier gap.

### Out of scope

- Foreign-intelligence fog.
- Player dashboard.
- Lab or project state.
- Random breakthroughs.

### Acceptance

- Existing owner variables/flags/ideas are never written.
- Rebuilding twice with unchanged inputs is exactly stable.
- Changing a canonical fixture changes the external contribution once, without accumulation.
- Rankings are deterministic at exact ties.
- Full and Outcomes Only use the same reducer.
- Off does no adapter or reducer work.
- Corporate History Full / Outcomes Only / Off combinations all produce documented race inputs.
- Late-start initialization reaches a valid current-era state without replaying historical popup events.

## Prompt 3 - Overview Dashboard Vertical Slice

### Objective

Build an OEM-native decision-category Overview dashboard for the two-country headless kernel.

### Required scope

- Add a dedicated decision category with a `decision_category` scripted GUI.
- Show system title, mode badge, one status banner, six national metrics, exact self score/rank, estimated rival state placeholder, frontier gap, race temperature, current bottleneck, and a close/help interaction only if required by the chosen shell.
- Use normalized `0..100` gauges with numeric value/cap and tier adjectives.
- Add explicit states for uninitialized, dormant, active, Outcomes Only, unavailable, and repair needed.
- Add an Overview tab only. Do not render empty Labs, Projects, Global Race, or Policy tabs.
- Use a player-only dirty variable and keep all strategic calculation out of GUI properties.
- Outcomes Only displays a persistent read-only mode banner.
- Off displays no category or GUI.
- Keep debug readouts outside the normal dashboard.

### OEM presentation references

- Protests for the status banner and compact metric/tooltips.
- Czech GUI for 100-step progress rendering.
- Corporate Systems for mode-aware fallback text.
- Agrarian decision category for the attachment pattern.

### Acceptance

- Every metric renders correctly at `0`, `1`, each threshold boundary, `99`, `100`, and repaired overcap.
- Harmful high values use harmful color semantics.
- `Unknown` and `Unavailable` never render as zero.
- No event target is used.
- No raw loc key, getter, scripted-loc token, missing sprite, clipping, or overlap appears in a rendered test.
- The smallest supported test resolution and 1920x1080 are both inspected.
- Save/reload refreshes values and tier names without player repair.

## Prompt 4 - Laboratory Politics and Support Shares

### Objective

Add the Cognoscenti-derived inner politics loop: distinct laboratories compete for a fixed pool of national support while retaining independent capability, talent, compute access, and momentum.

### Required scope

- Freeze a deliberately small prototype roster: two or three USA labs and two or three Chinese labs with historically valid activation gates.
- Assign stable, never-reused numeric lab IDs.
- Store lab fields in country scope and render them through a filtered dynamic list with one reusable card.
- Add national support share to active labs. Shares total exactly `100`.
- Implement deterministic redistribution. When one lab gains support, named/eligible donors lose the exact amount under a documented rule; any rounding remainder goes to the selected lab.
- Give each lab one clear specialty payoff from support, with a strict cap and no kitchen-sink modifier.
- Add lab-aligned decisions or missions whose normal effects matter immediately and whose completion shifts support.
- Add one support-threshold offer per prototype country.
- Add one balanced-ecosystem offer whose requirements exclude a dominant lab and whose strategic result differs from the threshold offer.
- Add a selected-lab detail panel with identity, leader, agenda, current share, specialty, capability, compute, talent, momentum, openness, and current project status.
- AI participants use the same support-change effects through weighted decisions, not GUI clicks.

### Cognoscenti translation rules

- Reuse the actor identity -> constrained share -> scaling specialty -> actor action -> gated project loop.
- Do not copy the three permanent Cognoscenti factions, names, portraits, prose, or ideology.
- Do not use `random_list` to repair share totals.
- Do not hardcode one GUI container per lab.
- Do not make political support equal capability.
- Do not add an appointment/cabinet replacement minigame yet.

### Acceptance

- Zero, one, typical, and maximum prototype lab populations render.
- Every support change preserves a total of exactly `100`.
- A deactivated lab transfers or freezes its share under a documented deterministic rule.
- Capability and support remain independently testable.
- Dominance and balance each unlock at least one meaningful, mutually legible option.
- Lab activation and removal survive save/reload.
- A new participant country requires no new GUI container.
- A new authored lab requires registry/mapping/content changes but no copied GUI layout.
- Full provides interactions; Outcomes Only resolves the same choices autonomously and shows read-only results; Off has no labs.

## Prompt 5 - Training Projects and Model Releases

### Objective

Implement one complete project lifecycle per prototype country before expanding the catalog.

### Required scope

- Add stable project IDs and the bounded lifecycle: available, selected, preparation, training, evaluation, release choice, resolved, blocked, failed.
- Use native missions or timed flags as the authoritative clock. The GUI must not decrement a second clock.
- Make compute commitment, lab capability, talent, momentum, and control capacity affect duration or outcome through documented formulas.
- Implement one active project slot per prototype country.
- Add pause/block handling for lost prerequisites.
- Add release choices with clear tradeoffs: open, controlled, restricted, or delayed, using only the subset justified by the project.
- Add a release-history list that is derived from persistent completed outcomes.
- Add exactly-once guards for phase entry, completion, timeout, and release effects.
- Add AI selection and release weighting through the same effects.

### TNO translation rules

- Use Guangdong's active project, selection card, progress, and history concepts.
- Do not copy TNO's GUI, asset paths, ten-day GUI AI loop, text, or project implementation.

### Acceptance

- Start, progress, pause, resume, block, complete, fail, cancel, and release states are distinguishable.
- Every clock tooltip names the phase, days remaining, pause reason, and expiry consequence.
- Save/reload at every phase does not replay or skip effects.
- Outcomes Only runs the same lifecycle with autonomous selections and no active player clock controls.
- Off creates no project state or missions.

## Prompt 6 - Public Alarm, Control Debt, and Crisis Windows

### Objective

Implement the Cognoscenti-derived outer pressure loop without reproducing the Masquerade's fiction or its direct-collapse behavior.

### Required scope

- Implement public alarm and control debt as separate `0..100` dangers.
- Derive their normal pressures from capability, deployment, public confidence, control capacity, lab openness, release posture, incidents, and race temperature.
- Add one stored quarterly interval and countdown for each pressure. The central participant dispatcher applies the pulse and resets the countdown.
- Allow infrastructure, standards, audits, public policy, and institutional investment to lengthen the interval or reduce pulse size.
- Add a small intervention set where some actions reduce one pressure at a cost, and at least one action improves one while worsening the other.
- Map each danger to explicit bands with one source of truth for threshold values.
- Apply bounded consequences through race-owned ideas or effects only when the band changes.
- Reaching the extreme band applies severe bounded consequences and can satisfy one crisis prerequisite; it does not activate or resolve the crisis by itself.
- Add an explicit crisis ID/epoch transition that pauses ordinary pressure pulses and starts a visible emergency mission.
- Implement one recoverable incident/crisis per pressure and mutually exclusive, exactly-once success/cancellation/timeout outcomes.
- Suppress routine missions and interventions in Outcomes Only while preserving autonomous resolution and major outcome reporting.

### Cognoscenti translation rules

- Reuse the two coupled meters, variable pressure intervals, intervention tradeoffs, tier names, and escalation to a timed emergency.
- Do not copy Public Awareness, Extremist Activity, the Masquerade, its prose, institutions, or its event chain.
- Do not tie a full meter directly to government collapse.
- Do not duplicate thresholds across effects, scripted localisation, and GUI properties.

### Acceptance

- Both pressures clamp and render at every threshold boundary.
- Quarterly countdowns survive save/reload, pulse once at zero, and reset to the current persistent interval.
- Interval improvements have a documented policy for the live countdown and apply consistently.
- Each action's requirement and tradeoff are visible before selection.
- Reaching `100` remains the extreme band and never silently ends the system.
- Normal pressure pulses pause during a crisis and resume under an explicit recovery rule.
- Crisis success, cancellation, timeout, and recovery are deterministic, mutually exclusive, and exactly once.
- Recoverable failure is the default. A terminal branch is out of scope without a separately approved design brief.
- Full, Outcomes Only, and Off follow the architecture matrix.

## Prompt 7 - Compute and Semiconductor Economy

### Objective

Turn compute into a constrained strategic resource connected to existing MD/OEM energy, semiconductor, industrial, and corporate systems.

### Required scope

- Define physical compute capacity, allocatable training compute, committed compute, and inference/deployment demand without duplicating canonical buildings or technologies.
- Build read-only adapters for approved semiconductor, GPU, datacenter, energy, and corporate state.
- Add one national allocation decision among active projects/labs, control/evaluation work, and deployment.
- Add scarcity, energy, import, and sanctions constraints.
- Make active projects reserve and release compute exactly once.
- Add a small compute panel and bottleneck tooltip to existing tabs.
- Provide deterministic fallback values when optional corporate systems are disabled.
- Keep all resource scales bounded and documented.

### Acceptance

- Allocation never exceeds available compute.
- Reserved compute is released on completion, cancellation, failure, participant loss, and repair.
- External contributions rebuild from zero.
- Existing semiconductor/GPU/corporate owners are never written.
- AI allocation obeys affordability and does not depend on the GUI.
- Save/reload preserves commitments and does not duplicate capacity.

## Prompt 8 - Policy, Talent, and Foreign Intelligence

### Objective

Add strategic national posture and make global comparison respect uncertainty.

### Required scope

- Add a bounded, mutually exclusive national policy posture with clear tradeoffs among frontier speed, openness, deployment, public confidence, control capacity, and talent attraction.
- Add talent recruitment, retention, migration, and training actions that read existing migration/education/research state where available.
- Add intelligence confidence for each displayed rival using a scalable scope/index pattern.
- Convert exact foreign state into estimated bands or ranges based on intelligence, lab openness, public releases, and observed outcomes.
- Add Global Race and Policy tabs only when their backing systems are functional.
- Preserve exact internal values for simulation and debug.

### Acceptance

- Normal UI never displays unjustified exact foreign capability.
- Adding a participant requires no country x metric localisation matrix.
- Policy changes use one authoritative transition effect and respect cooldown/affordability.
- Talent changes have bounded sources and sinks.
- Outcomes Only resolves policy autonomously and retains a read-only summary.

## Prompt 9 - Breakthroughs, Race Temperature, and Alerts

### Objective

Make the global race react to national advances and surface pressure through bounded, actionable alerts.

### Required scope

- Implement discrete breakthrough classes and exactly-once registration.
- Recalculate global frontier and race temperature from documented inputs.
- Add explicit temperature bands and threshold-entry effects.
- Use an approved deterministic random pattern only where a breakthrough outcome genuinely requires uncertainty.
- Add major yellow/red MD Alert tokens or the approved dashboard-local equivalent.
- Alerts must answer what changed, why it matters now, and where the player can act.
- Add a compact segmented temperature track inspired by TFR's escalation presentation, using OEM-native assets.
- Trigger events only for major breakthroughs, crises, or strategic choices; batch routine information.

### Acceptance

- Temperature transitions fire once per band entry and recover cleanly.
- Alerts do not duplicate, dismiss/restore correctly, and open the intended surface.
- Full shows normal alerts/events; Outcomes Only suppresses routine items and reports major outcomes; Off shows none.
- Breakthrough randomness is deterministic and save-safe.
- No undefined event picture or copied Workshop asset is introduced.

## Prompt 10 - Deployment, Automation, and World Integration

### Objective

Connect the race to the wider game through bounded, observable consequences.

### Required scope

- Define deployment channels such as civilian productivity, administration, intelligence, military support, and scientific research.
- Require capability, compute, control capacity, public confidence, and policy prerequisites appropriate to each channel.
- Add benefits through a small number of race-owned ideas/modifiers with clear caps.
- Add transition costs, labor/public effects, exposure, and incident risks.
- Add approved read-only inputs from existing economy, intelligence, military, and research systems.
- Do not write canonical economy, corporate-history, or technology owner variables.
- Add a selected deployment panel rather than another country x channel matrix.

### Acceptance

- Every world modifier traces to a visible deployment state and can be removed/repaired.
- Benefits do not stack without a documented cap.
- Deployment creates meaningful pressure tradeoffs.
- AI behavior is affordable, bounded, and mode-aware.
- Removing a participant or disabling the system through a test fixture does not strand modifiers.

## Prompt 11 - Participant Expansion and AI Balance

### Objective

Expand beyond USA/China only after the data model, GUI, projects, and pressure loops are stable.

### Required scope

- Freeze the next small participant cohort from actual OEM country content.
- Add one read-only adapter per participant.
- Register participants through the generic eligibility/initialization path.
- Add authored labs with stable IDs and historical activation.
- Add no participant-specific GUI container.
- Add no display-only country x metric localisation keys.
- Validate collapse, annexation, subject status, tag change, release, late activation, and missing adapter inputs.
- Balance AI choices through shared scripted factors plus narrowly scoped country preferences.

### Acceptance

- Every new participant passes the same contract tests and mode matrix.
- Missing optional content falls back safely.
- Ranking, intelligence, cards, and selected-entity panels scale without GUI edits.
- AI participants remain within compute, money, political power, and project limits.
- No new global loop is introduced.

## Prompt 12 - Runtime Hardening and Release Evidence

### Objective

Close the gap between parseable implementation and a shippable subsystem.

### Static scope

- Run the applicable validators named in the architecture after reading `.claude/docs/validation-pipeline.md`.
- Scope pre-commit to modified files only.
- If any `tools/` file changed, run the full `python -m pytest` suite and fix the test or implementation without weakening the gate.
- Verify all GUI properties, dynamic entries, scripted-localisation branches, variables, decisions, on-actions, GFX references, and English localisation.

### Runtime matrix

Record exact build identity, commit SHA, launcher mod identity, scenario, and evidence for:

- 2000 start and at least one later start.
- Full, Outcomes Only, and Off.
- Human USA, human China, and observer/AI play.
- Corporate History Full, Outcomes Only, and Off crossed with the race modes where meaningful.
- Initialization and activation threshold.
- Quarterly update and ranking tie.
- Lab activation, support redistribution, and threshold project.
- Project start, pause, completion, failure, cancel, and release.
- Both recurring pressure missions and both crisis outcomes.
- Save/reload before and after every exactly-once transition.
- Participant collapse, annexation, and late registration.
- Smallest supported UI resolution and 1920x1080.
- Error log, raw loc/GFX failures, checksum behavior, and performance/tick impact.

### Acceptance

- No matrix cell is marked passed without matching evidence.
- Static, console-fixture, rendered, and natural-runtime evidence are reported separately.
- Off has no state, category, alerts, events, missions, ideas, or dispatcher work.
- Outcomes Only is autonomous, quiet, and outcome-equivalent where the contract requires it.
- Full is playable without debug actions.
- Save/reload and later starts require no console repair.
- The implementation has no known unbounded loop, per-frame strategic work, undefined GFX, raw localisation, or copied Workshop asset.

## Final release boundary

Completion of this campaign does not itself authorize a commit, push, pull request, release, or Changelog entry. Publication and release acceptance remain separate user decisions.
