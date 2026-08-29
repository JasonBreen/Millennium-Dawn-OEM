# Great AI Race Architecture

Status: architecture contract for a future implementation campaign. This document does not authorize gameplay implementation, commits, pushes, or publication.

## Purpose

The Great AI Race is a multinational strategic subsystem for Millennium Dawn OEM. It should feel mechanically closer to the dense decision-tab systems used by TNO and TFR than to a normal focus reward chain: persistent national state, competing laboratories, timed projects, gauges, rankings, alerts, and policy tradeoffs presented through a bespoke dashboard.

The feature remains an OEM system. TNO and TFR are references for interaction design and information density, not sources for copied script, localisation, art, fonts, or assets.

The target is a small game inside the Decisions interface, not a narrative total conversion and not an `AI Level 7` research bonus.

## Locked design principles

1. **One global subsystem, multiple national participants.** The Great AI Race is not an enlargement of the USA AI Industry Core.
2. **Existing systems retain ownership.** Country histories, companies, technologies, ideas, and economic systems keep their canonical state. The race reads those systems through documented adapters.
3. **No duplicate authority.** Race totals are rebuilt from race-owned stock plus read-only external contributions. External chains never write race variables directly.
4. **Bounded simulation.** Project work may update monthly; national aggregation, frontier movement, rankings, and race temperature update quarterly. There is no daily global poll.
5. **Data drives repeated UI.** Countries use scope-backed arrays. Laboratories and projects use stable numeric registries rendered through reusable dynamic-list cards.
6. **The dashboard observes canonical state.** GUI selection, visible arrays, and dirty variables are presentation state only.
7. **Runtime modes are architectural.** Full, Outcomes Only, and Off share one rule contract and are tested separately.
8. **Foreign knowledge is not omniscient.** The simulation may store exact foreign values, but the normal player surface shows estimates, ranges, or unknown states when intelligence does not justify precision.
9. **Debug is separate from play.** Raw values and force controls are visible only in an explicitly labelled debug surface gated by `is_debug = yes`.
10. **Every phase remains reviewable.** No phase may combine a new state model, a complete GUI, content for many countries, and world integration in one diff.

## Existing ownership boundary

The repository already has a USA-specific AI Industry Core:

- `.claude/docs/ai-industry-core-plan.md`
- `common/scripted_effects/USA_ai_core_effects.txt`
- `events/USA_ai_core_events.txt`
- `events/USA_openai_events.txt`
- `events/USA_anthropic_events.txt`
- `localisation/english/MD_focus_USA_l_english.yml`

That system owns its six USA axes, historical event chain, national ideas, and company integrations. The Great AI Race must not rename, move, duplicate, or directly mutate `USA_ai_core_*`, OpenAI, Anthropic, Palantir, or other company-owned state.

The race owns only:

- race-specific national stock and derived totals;
- global frontier, pressure, temperature, and ranking state;
- laboratory simulation state introduced by the race;
- training projects, releases, policy choices, alerts, and outcomes introduced by the race;
- race-specific GUI and presentation state.

### Authority ledger

| State | Authoritative owner | Great AI Race access |
|---|---|---|
| `USA_ai_core_*` axes and milestones | USA AI Industry Core | Read through the USA adapter |
| Existing company ideas, flags, and milestones | Their existing event/effect files | Read through country or company adapters |
| Existing technology, economy, semiconductor, and research state | Existing MD/OEM systems | Read-only input where explicitly documented |
| Race-owned national stock | Great AI Race country scope | Read and write |
| Effective national race metrics | Great AI Race rebuild effect | Derived cache; never an external write target |
| Lab registry and lab state | Great AI Race country scope | Read and write |
| Global frontier and rankings | Great AI Race global scope | Read and write through one dispatcher |
| Selected tab, selected card, visible-list cache, dirty counter | Great AI Race GUI layer | Presentation only |

### Adapter formula

Each national metric follows the same ownership shape:

```text
effective metric = clamp(race-owned stock + rebuilt external contribution, 0, 100)
```

For example:

```text
ai_race_capability = clamp(
    ai_race_capability_stock
    + ai_race_capability_external,
    0,
    100
)
```

The quarterly adapter effect must:

1. Reset every `*_external` contribution to zero.
2. Read canonical external state.
3. Rebuild the contribution from the current canonical state.
4. Calculate and clamp the effective metric.
5. Never feed the derived total back into an owner system.

This permits late-start reconstruction and save repair without bidirectional synchronization or milestone double-counting. Debug actions change race-owned stock or owner-specific fixtures, not the derived total.

## Mechanical references

### OEM patterns to reuse

| Need | Repository precedent | Translation |
|---|---|---|
| Full / Outcomes Only / Off rule | `common/game_rules/00_game_rules.txt`, `common/scripted_triggers/MD_corporate_history_triggers.txt` | A separate `rule_ai_race` and three non-overlapping scripted triggers |
| Central low-frequency scheduling | `common/on_actions/MD_on_actions.txt`, `common/scripted_effects/00_power_ranking_effects.txt` | One call from the existing global monthly singleton, with month gates for quarterly work |
| Sorted country ranking | `common/scripted_effects/00_power_ranking_effects.txt` | Scope-backed participant array and derived ranked array |
| Decision-category GUI | `common/decisions/categories/00_agrarian_economics_category.txt`, `common/scripted_guis/01_agri_scripted_gui.txt` | Embed the main dashboard in a decision category |
| Dense status dashboard | Protests GUI in `common/scripted_guis/01_expected_spending.txt` and `interface/MD_protest_decision.gui` | Mutually exclusive status banner plus compact live metrics |
| Reusable cards | MIO Catalog in `common/scripted_guis/00_mio_unlock_catalog.txt` | One reusable lab/project card rendered from a visible array |
| Growing country list | EU scope arrays in `common/scripted_guis/01_european_union_guis.txt` | Generic country rows with `change_scope = yes` |
| Alerts | `common/scripted_guis/00_MD_alerts_scripted_gui.txt` | Major danger and attention tokens, not routine event spam |
| 100-step gauge | Czech GUI in `common/scripted_guis/99_CZE_scripted_gui.txt` and `interface/cze_scripted_gui.gfx` | Normalized, clamped metric and progress frames |
| Dirty-variable refresh | `.claude/docs/scripted-gui-patterns.md` | Refresh derived visible arrays on player interaction, not per tick for every AI |
| Mode-aware reports | Corporate Systems dashboards | Explicit Outcomes Only and unavailable states, never misleading zeros |

### Local TNO references

Installed Workshop source inspected through the local descriptor for item `2438003901`, version `1.10.0b`.

| Reference | Useful element | OEM translation |
|---|---|---|
| `common/scripted_guis/TNO_alertbar.txt` | Tokenized alerts with click and dismiss behavior | Use MD Alerts or a dashboard-local attention strip |
| `common/scripted_guis/TNO_GNG_Product_Decisions_GUI.txt` | Product progress, release history, active/inactive panels | Training-project and model-release panels |
| `common/scripted_guis/TNO_GNG_Research_Team_GUI.txt` | Selectable project cards and active-project state | Laboratory project selection with reusable cards |
| `interface/Guangdong/TNO_GNG_Research_Team.gui` | Card hierarchy, progress, selection pop-out | Information architecture only; author OEM-native layout and assets |
| `common/scripted_guis/TNO_Cold_War_GUI.txt` | Comparison between strategic actors | Global frontier and rival comparison view |

Do not reproduce TNO's full top-bar replacement, total-conversion shell, or GUI-owned AI work on a ten-day interval. The race belongs inside OEM's Decisions experience and uses central game logic.

### Primary local TFR reference: the Cognoscenti

Installed Workshop source inspected through the local descriptor for item `3350890356`, version `1.0.8.3`. The Cognoscenti content, rather than TFR's generic reform bars or strategic maps, is the primary TFR design reference for this feature.

The Cognoscenti is useful because it combines two distinct management loops:

1. **Internal power:** three mutually dependent actors compete for a fixed pool of influence.
2. **External pressure:** two coupled risk meters rise on recurring clocks and require costly interventions.

| Cognoscenti element | Local source | Great AI Race translation |
|---|---|---|
| Decision-category dashboard | `common/decisions/categories/TFR_decision_categories_USB.txt:26-37`, `common/scripted_guis/TFR_scripted_guis_USB.txt:6-180` | A decision-category race dashboard whose GUI presents, but does not own, gameplay state |
| Three actor columns | `interface/TFR_USB_cogno.gui:7-89` | Distinct lab cards with identity, leadership, agenda, current share, and strategic effect |
| Cabinet/appointment strip | `interface/TFR_USB_cogno.gui:91-277` | Later laboratory-director or government-liaison layer; not part of the MVP |
| Influence shares | `localisation/english/TFR_country_localisation_USB_l_english.yml:939-988` | A bounded national support or compute-allocation pool across active laboratories |
| Influence-balancing effect | `common/scripted_effects/TFR_scripted_effects_USB.txt:5652-5897` | Deterministic redistribution whose shares always total exactly `100`; do not copy TFR's random normalization |
| Scaling actor benefit | `common/dynamic_modifiers/TFR_dynamic_modifiers_USB.txt:615-636` | Each lab's support share contributes one small, legible national effect or project specialty |
| Actor-themed actions | `common/decisions/TFR_decisions_USB.txt:3796-4599` | Decisions and missions visibly aligned with a lab; completing them shifts support and produces an immediate strategic result |
| Influence-gated project | `common/decisions/TFR_decisions_USB.txt:4393-4428` | Frontier projects may require a minimum lab share, control capacity, compute allocation, or policy posture |
| Separate Masquerade loop | `common/decisions/categories/TFR_decision_categories_USB.txt:52-63` | Keep external race pressure conceptually separate from laboratory politics |
| Recurring risk missions | `common/decisions/TFR_decisions_USB.txt:8906-8965` | Native missions periodically raise public alarm and control debt; investments can lengthen the interval |
| Coupled tradeoff decisions | `common/decisions/TFR_decisions_USB.txt:8967-9687` | Interventions may reduce one danger while consuming capacity or worsening another |
| Tiered risk state | `common/scripted_effects/TFR_scripted_effects_USB.txt:5436-5650`, `common/scripted_localisation/TFR_scripted_loc_USB.txt:788-993` | Clamp meters, map them to explicit bands, and drive readable status plus bounded consequences |
| Explicit terminal crisis chain | `common/decisions/TFR_decisions_USB.txt:3752-3794`, `events/TFR_events_USB.txt:18114-18200` | A separately activated emergency mission owns terminal resolution; a high pressure band alone does not silently collapse the country |

The direct design lesson is not `three labs forever`. It is that actors become strategically legible when each has an identity, a share of a constrained resource, a scaling specialty, its own actions, and influence-gated projects. The Great AI Race applies that pattern to a data-driven lab roster.

The Masquerade's second lesson is equally important: public reaction and technical control are different pressures. The race therefore derives `public alarm` and `control debt` rather than collapsing both into race temperature. In TFR, the `0.8+` pressure bands swap to maximum penalty ideas; the hard-collapse events belong to separately triggered failure chains. The Great AI Race preserves that separation.

### TFR implementation patterns not to copy

- Do not hardcode overlapping buttons for every possible lab leader. Use a fixed-ID lab registry and reusable cards.
- Do not normalize a fixed-sum pool through an unseeded `random_list`. Use deterministic redistribution and a documented rounding remainder rule.
- Do not expose a kitchen-sink dynamic modifier with dozens of independently accumulated variables. Keep the lab-share payoff small and readable.
- Do not put strategic effects directly in GUI clicks. Use logged decisions or scripted effects that the AI can also call.
- Do not duplicate long prose blocks in the dashboard. Use compact summaries and tooltips.
- Do not copy TFR's missing scripted-localisation fallbacks, empty blocks, or project-specific scripting conventions.
- Do not turn a full risk meter directly into national collapse. Enter a visible crisis state with a response window and exactly-once resolution.

Other TFR GUIs remain secondary presentation references: `TFR_PRC_GUI` for embedded progress bars and `war_escalation_scripted_gui` for a segmented track. They do not define the race's core loop.

## State model

All core metrics are integers from `0` to `100`. Every writer clamps its result. A displayed percentage is the actual normalized value, not a `0..10` value placed on a 100-step bar.

### Country-scope state

| Variable | Meaning | High value |
|---|---|---|
| `ai_race_capability` | Effective frontier algorithm and model capability | Beneficial, but increases pressure |
| `ai_race_compute` | Available training and inference compute | Beneficial |
| `ai_race_talent` | Research, engineering, and operator base | Beneficial |
| `ai_race_deployment` | Ability to integrate models into the economy and state | Beneficial, with transition risks |
| `ai_race_control_capacity` | Institutional ability to evaluate and govern advanced systems | Beneficial |
| `ai_race_public_confidence` | Social and political legitimacy for continued deployment | Beneficial |

Each core metric also has:

- `*_stock`: race-owned persistent progress;
- `*_external`: derived contribution rebuilt by adapters;
- the unsuffixed effective value used by the simulation and UI.

Additional country state:

- `ai_race_frontier_gap`: signed distance from the global frontier;
- `ai_race_rank`: current global rank;
- `ai_race_policy_posture`: stable numeric policy ID;
- `ai_race_public_alarm`: derived pressure from incidents, disclosure, disruptive deployment, and weak public confidence;
- `ai_race_control_debt`: derived pressure from the gap between capability/deployment and control capacity;
- `ai_race_public_alarm_interval`: quarters between automatic public-pressure pulses;
- `ai_race_public_alarm_pulse_remaining`: quarters until the next public-pressure pulse;
- `ai_race_control_debt_interval`: quarters between automatic technical-risk pulses;
- `ai_race_control_debt_pulse_remaining`: quarters until the next technical-risk pulse;
- `ai_race_crisis_id`: `0` outside a crisis, otherwise a stable crisis ID;
- `ai_race_crisis_epoch`: exactly-once guard for the active/resolved crisis instance;
- `ai_race_selected_tab`: UI-only tab ID;
- `ai_race_selected_lab`: UI-only lab ID;
- `AI_RACE_state_initialized`: idempotent initialization flag;
- `AI_RACE_active`: participant is eligible, initialized, and currently registered in the headless simulation; a later presentation gate will own the public competitive-activation threshold;
- `AI_RACE_outcomes_reconstructed`: Outcomes Only state is available;
- `AI_RACE_dashboard_open`: player-only presentation flag if the selected GUI pattern requires it.

The exact set of stock/external variables may be reduced if a metric has no external adapter. The three-part ownership contract must remain wherever a canonical external system contributes.

### Global state

| State | Purpose |
|---|---|
| `global.ai_race_frontier_capability` | Highest current effective capability |
| `global.ai_race_temperature` | Competitive pressure and escalation, `0..100`; high is dangerous |
| `global.ai_race_frontier_pressure` | Rate at which laggards are pushed toward risky choices |
| `global.ai_race_leader_id` | Country ID of the current leader |
| `global.ai_race_epoch` | Count of completed scheduled quarterly reconciliations |
| `global.ai_race_last_processed_quarter` | Replay guard encoded as `current year * 4 + quarter index` |
| `global.ai_race_dirty_update_var` | Player presentation refresh counter |
| `GLOBAL_ai_race_initialized` | Global initialization guard |
| `global.ai_race_participants` | Country-scope array of eligible participants |
| `global.ai_race_ranked_participants` | Derived country-scope array sorted by effective capability |

The ranked array is derived and may be rebuilt. It never becomes the only record of participation or national values.

### Laboratory registry

Laboratories are authored identities with stable, never-reused numeric IDs. A country owns its laboratory state. The GUI renders a filtered array of lab IDs through one reusable card.

Minimum lab fields:

| Field | Range or type |
|---|---|
| Active/known state | Boolean or bounded enum |
| Capability | `0..100` |
| Compute access | `0..100` |
| Capital access | `0..100` |
| Talent | `0..100` |
| Momentum | `0..100` |
| Openness | `0..100`, with explicit polarity in tooltips |
| National support share | `0..100`; active lab shares total exactly `100` |
| Current project | Stable project ID or `0` |
| Project phase | Bounded enum |
| Project progress | `0..100` |
| Release posture | Bounded enum |

Recommended storage is parallel country-scope arrays indexed by lab ID, following the repository's fixed-ID dynamic-list patterns. Confirm the exact array syntax against a live OEM precedent before Phase 4.

Adding a lab may require registry data, localisation dispatch, activation history, and art. It must not require another hand-authored GUI container.

### Laboratory politics and constrained support

The Cognoscenti pattern is translated as a constrained national support pool, not as a second capability score.

- Active laboratories divide `100` points of national support.
- Support represents the government's marginal attention, preferred contracting channel, and discretionary compute access, not ownership of all national compute.
- An action that grants support to one lab redistributes the same amount from the other active labs by a deterministic rule.
- The sum is repaired to exactly `100` after every change. The remainder goes to the explicitly selected lab, never a random lab.
- A lab's support share gives one small, speciality-aligned benefit and affects access to its projects.
- Capability, talent, and momentum remain independent. A politically favored lab is not automatically the most capable.
- Support thresholds may unlock projects or policy offers, but no core national outcome requires maintaining a permanently dominant lab.
- At least one authored branch must reward a dominant lab with a unique option, while a genuinely balanced ecosystem exposes a different coalition or shared-evaluation option. TFR's influence-dependent succession choices demonstrate this at `events/TFR_events_USB.txt:15983-16199`.

The first laboratory phase should use two or three labs in one country and prove redistribution, threshold behavior, AI choice, and save/reload before expanding the roster.

### Coupled pressure loop

The Masquerade pattern is translated into two separate danger tracks:

| Pressure | Primary causes | Typical response | Bad response tradeoff |
|---|---|---|---|
| Public alarm | Disruptive deployment, visible failures, secrecy breaches, labor shock, weak public confidence | Transparency, compensation, standards, slower deployment | May reveal more information or sacrifice race momentum |
| Control debt | Capability and deployment outpacing evaluation, rushed releases, opaque labs, underfunded testing | Evaluations, pauses, audits, control research | Costs compute/time and may widen the frontier gap |

These are bounded `0..100` variables with explicit bands and threshold consequences. The central quarterly reducer advances stored interval counters and applies a pressure pulse when a counter expires. Investments may lengthen the interval or reduce pulse size, while aggressive race posture shortens it. Do not create Cognoscenti-style 20- or 25-day self-reactivating missions for every participant.

At an extreme threshold, the track may satisfy one prerequisite for an emergency crisis mission. The crisis is activated explicitly by its full trigger, not by the UI or the pressure-band effect alone. Normal pressure pulses pause while `ai_race_crisis_id` is nonzero. The player receives a visible response window and can trade momentum, compute, confidence, or political resources for recovery. Success, cancellation, and timeout resolve mutually exclusive authored outcomes exactly once. Recoverable failure is the default; a genuinely terminal branch needs a separately approved design brief and natural-runtime acceptance. A full meter never silently applies national collapse.

Race temperature remains global. Public alarm and control debt are national. They interact, but none is a renamed duplicate of another.

### Project registry and lifecycle

Projects use stable numeric IDs and a bounded state machine:

```text
available -> selected -> preparation -> training -> evaluation -> release choice -> resolved
                                  \-> blocked
                                  \-> failed
```

Required persistent fields are project ID, owner lab ID, phase, progress, resource commitment, start marker, completion marker, and pending release posture. A save/reload cannot replay phase entry or completion effects.

The initial project catalog should be small and generic. Country- or lab-specific variants are added only after the lifecycle is stable.

## Global ranking and intelligence

The simulation maintains exact internal values. Presentation follows a separate knowledge contract:

- The player's own country is exact.
- Public releases and confirmed breakthroughs may be exact or tightly bounded.
- Foreign private capability is estimated from intelligence, openness, and observed releases.
- Insufficient information displays a band or `Unknown`, never a fabricated precise number.
- Debug may display exact internal values and the estimate delta.

Participant rows must be country scopes, not a localisation matrix keyed by every country and metric. The ranking rebuild should reuse the proven `common/scripted_effects/00_power_ranking_effects.txt` temporary-array selection pattern unless a simpler, already-validated sort exists when implementation begins.

## Update cadence

| Cadence | Work |
|---|---|
| First enabled monthly pulse / reconstruction | Gate the rule, initialize global state, register eligible participants, initialize or reconstruct country state idempotently; the same path repairs late bookmarks and loaded saves |
| Event-driven | Player actions, lab activation, policy change, project start, release choice, major breakthrough, owner-system changes that do not need polling |
| Monthly | Advance only active projects and bounded lab work; resolve completed phase transitions once |
| Quarterly | Rebuild external contributions, update effective national values, advance national pressure counters, compute frontier and gaps, rebuild rankings, update race temperature and pressure |
| Yearly or explicit repair | Optional consistency audit and late-participant registration; no narrative event polling |
| GUI interaction | Rebuild player-visible filtered arrays and advance the dirty counter |

Implementation should add one narrow, enabled-mode-gated call to the existing global monthly singleton. It must not create a second global `on_monthly` owner, a global daily event, or `every_country` work. Quarterly country work iterates only the registered participant array. A normal Off game does not enter the race dispatcher.

Derived-state repair and scheduled advancement are separate effects. The pure rebuild may be called by initialization, late-start recovery, and debug repair. Only the replay-guarded quarterly wrapper advances epochs, pressure counters, project clocks, or other interval state.

GUI dirty-variable effects must be guarded so AI countries do not continually refresh player presentation arrays.

## Runtime modes

The Great AI Race gets a separate fixed-at-setup game rule, `rule_ai_race`. It must not reuse `rule_corporate_history`.

| Surface | Full | Outcomes Only | Off |
|---|---|---|---|
| Core state | Initialized and simulated | Initialized or reconstructed and simulated autonomously | Not created |
| National/global outcomes | Yes | Yes | No |
| Dashboard | Full interactive dashboard | Read-only summary with persistent mode banner | Hidden |
| Lab/project controls | Interactive | Hidden; AI/autonomous policy resolves them | Hidden |
| Routine alerts and clocks | Yes | Hidden | Hidden |
| Major outcome notices | Yes | Yes, bounded | No |
| Debug surface | Available under `is_debug = yes` | Available under `is_debug = yes` | Hidden |
| Dispatcher work | Monthly and quarterly | Monthly and quarterly using autonomous choices | None |

Full and Outcomes Only use the same state machine and resolution effects. Outcomes Only suppresses micromanagement and routine presentation; it does not maintain a second simplified history chain. Off must leave no participant arrays, country initialization flags, project state, dashboard placeholders, alerts, or events.

## GUI architecture

### Shell

The MVP is a hybrid decision-category dashboard:

- A dedicated decision category owns visibility and attaches the scripted GUI.
- A `decision_category`-context scripted GUI renders the primary panel.
- Normal decisions beneath the panel remain available for actions that fit the Decisions model.
- A `player_context` pop-out is permitted only for a selected lab/project detail panel that cannot fit cleanly in the category.
- The system does not replace the top bar or diplomacy view.

### Tabs

Planned tabs:

1. **Overview:** national metrics, status banner, global position, bottleneck, alerts.
2. **Laboratories:** dynamic lab cards and selected-lab details.
3. **Projects:** active/available projects, phase, clock, commitment, release history.
4. **Global Race:** ranked countries, frontier, estimates, intelligence confidence.
5. **Policy:** national posture, compute allocation, talent, release, and control choices.

Only the Overview shell belongs in the first visual implementation. Empty placeholder tabs are not acceptable player content; a tab is added when its backing state exists.

### Repeated content

- Labs/projects: fixed numeric ID registry, reusable dynamic-list card, filtered visible array.
- Countries/rivals: scope-backed dynamic list with `change_scope = yes`.
- Status/tier names: `defined_text` dispatchers with most-specific branches first and an explicit fallback.
- Requirements tooltips: direct flat `[!trigger]` calls where needed; do not dispatch a key that is expected to re-evaluate a trigger.
- No event targets in scripted GUI. Use variable scopes or scope arrays.
- No nested-container `_visible` filtering. Rebuild the backing visible array.

### Presentation hierarchy

1. System title and mode badge.
2. One mutually exclusive race-status banner.
3. Six headline national metrics, each with numeric value/cap and a tier adjective.
4. Global position and estimated frontier.
5. One current bottleneck or strategic pressure.
6. Compact alert strip.
7. Tabs and reusable cards.
8. Secondary selected-entity detail panel.

Labels are short. Mechanical explanation belongs in immediate/delayed tooltips or secondary panels. Every clock states what happens when it reaches zero. Every gauge has text as well as color/length.

## Localisation ownership

Shared cross-country presentation belongs in:

- `localisation/english/MD_great_ai_race_l_english.yml`
- `common/scripted_localisation/00_great_ai_race_scripted_localisation.txt`

Game-rule copy belongs in:

- `localisation/english/MD_game_rules_l_english.yml`

Country-owned event, idea, and decision copy remains in each existing:

- `localisation/english/MD_focus_TAG_l_english.yml`

Recommended shared key root: `AI_RACE_`. Recommended rule root: `RULE_AI_RACE_`. Do not reuse `USA_ai_core_*` or the USA Corporate Systems scripted-localisation file.

The shared English file must be UTF-8 BOM with LF, start with `l_english:`, and use one-space indentation. Do not create or update non-English localisation.

Every scripted-localisation dispatcher requires a fallback. Unknown, unavailable, uninitialized, and an actual numeric zero are distinct states.

## AI control

The game AI acts through scripted effects and decisions, never by clicking or evaluating the GUI.

- Full-mode AI participants use the same policy and project effects as the player.
- Outcomes Only participants use the same effects with autonomous selections and suppressed routine presentation.
- AI weighting is deterministic from state where practical.
- Any probabilistic outcome uses one authoritative owner scope, a saved pending state, and an approved deterministic random pattern.
- Decision `ai_will_do` roots use `base`, and player-facing effect blocks follow repository logging rules.
- No GUI update loop performs simulation work for AI countries.

## Save, reload, and multiplayer contract

- Initialization and reconstruction effects are idempotent.
- Persistent gameplay state uses variables, arrays, timed flags, and flags owned by stable scopes.
- Event targets are not persistence infrastructure and are not used by the GUI.
- Derived ranking and visible arrays can be rebuilt from canonical state.
- Phase entry and project completion have explicit one-time guards.
- A stored last-processed quarter prevents duplicate dispatcher work after reload.
- Late participant activation uses the same country initialization effect.
- A collapsed or annexed participant is removed or marked inactive without destroying historical results.
- All authoritative writes occur in one known scope; multiplayer clients do not maintain competing copies.
- Random outcomes, if any, must satisfy the repository's deterministic-random validation conventions.

## MVP implementation map

The first playable vertical slice is USA and China only, with one national overview, exact self values, estimated rival values, a global frontier, race temperature, and debug controls. It does not yet include selectable lab projects.

Expected files over the first three phases:

| File | Responsibility |
|---|---|
| `common/game_rules/00_game_rules.txt` | Separate Great AI Race runtime rule |
| `common/scripted_triggers/MD_great_ai_race_triggers.txt` | Mode, participant, initialization, and threshold gates |
| `common/scripted_effects/00_great_ai_race_effects.txt` | Initialization, adapters, clamps, update cadence, frontier, ranking |
| `common/on_actions/MD_on_actions.txt` | One call from the existing global monthly singleton |
| `common/decisions/categories/MD_great_ai_race_categories.txt` | Category visibility and later scripted-GUI attachment |
| `common/decisions/MD_great_ai_race_decisions.txt` | Debug-only controls in Phase 1; later normal actions remain mode-gated |
| `common/scripted_guis/01_great_ai_race_scripted_gui.txt` | Dashboard properties, visibility, clicks, and dynamic lists |
| `common/scripted_localisation/00_great_ai_race_scripted_localisation.txt` | Status, tier, mode, lab/project dispatchers |
| `interface/MD_great_ai_race.gui` | OEM-native dashboard layout |
| `interface/MD_great_ai_race.gfx` | New OEM-native sprites and progress-bar definitions |
| `localisation/english/MD_great_ai_race_l_english.yml` | Shared cross-country English copy |
| `localisation/english/MD_game_rules_l_english.yml` | Rule name and authoritative mode descriptions |
| `localisation/english/MD_focus_USA_l_english.yml` | USA-owned event/decision copy only |
| `localisation/english/MD_focus_CHI_l_english.yml` | China-owned event/decision copy only |
| `tools/tests/great_ai_race_state_model_test.py` | State ownership, modes, cadence, clamps, and lifecycle contract |

The exact filenames may be adjusted to avoid collisions or match a stronger nearby convention found at implementation time. Ownership boundaries may not be adjusted silently.

## Validation and acceptance model

Before editing implementation files, read `.claude/docs/validation-pipeline.md`. Validation is scoped to modified files and the applicable tool entry points. Never use `pre-commit run --all-files`.

Likely relevant static validators include:

- `tools/validation/validate_scripted_gui.py`
- `tools/validation/validate_scripted_localisation.py`
- `tools/validation/validate_decisions.py`
- `tools/validation/validate_on_actions.py`
- `tools/validation/validate_variables.py`
- `tools/validation/validate_set_variables.py`
- `tools/validation/validate_localisation.py`
- `tools/validation/validate_gfx_references.py`
- `tools/validation/validate_common_mistakes.py`

Static validation is not rendered GUI evidence and is not natural HOI4 runtime acceptance.

Each implementation phase needs its own evidence tier:

1. **Contract evidence:** ownership, IDs, scale, state transitions, and mode matrix are documented and tested.
2. **Static evidence:** applicable validators and focused regression tests pass.
3. **Console-fixture evidence:** debug actions exercise initialization, boundaries, transitions, and repair.
4. **Rendered evidence:** every panel, longest label, tooltip, progress boundary, and list population renders without raw keys, clipping, or overlap.
5. **Natural runtime evidence:** Full, Outcomes Only, Off, late start, save/reload, and AI behavior progress without force commands.

Do not report a later tier from evidence belonging to an earlier tier.

## Phase gates

### State gate

- Every variable has one owner, range, initialization path, writer list, and clamp path.
- Full, Outcomes Only, and Off behavior is explicit.
- Initialization, quarterly update, and project resolution are idempotent.
- Existing AI Core and company state is read-only.

### GUI gate

- Repeated labs/projects use one entry template.
- Participant countries use scopes.
- No event targets are used.
- No simulation work runs in click or visibility properties.
- Dirty updates are player-only and derived arrays rebuild cleanly.
- Empty, one-entry, normal, and maximum populations render.

### Localisation gate

- Shared and country-owned strings are in their correct files.
- English file encoding and line endings match repository rules.
- Every dispatcher has a fallback.
- Values, adjectives, colors, thresholds, and metric polarity agree.
- Outcomes Only and unavailable states never appear as zero.
- No raw keys, getters, missing icons, or broken color terminators render.

### Runtime gate

- Full supports interaction and normal outcomes.
- Outcomes Only advances autonomously and shows a read-only summary.
- Off creates no state or presentation.
- Save/reload does not replay initialization or completion.
- AI countries do not depend on GUI evaluation.
- The bounded update cadence produces no new daily or global-loop performance hotspot.

## Known risks and mitigations

| Risk | Mitigation |
|---|---|
| Duplicate authority with USA AI Core | Read-only quarterly adapter and explicit authority ledger |
| Dashboard becomes a wall of text | Short labels, tier adjectives, tooltips, tabs, selected-entity panels |
| Country x lab x metric explosion | Scope-backed countries, fixed-ID labs, one selected-entity detail panel |
| Per-tick performance cost | Participant array, monthly active-project work, quarterly aggregation, no daily poll |
| GUI refresh work runs for AI | Guard dirty effects and rebuild only player-visible arrays |
| Save/reload replays projects | Persistent phase IDs, completion guards, last-processed quarter |
| Multiplayer divergence | One owner scope and deterministic resolution effects |
| Foreign UI leaks exact values | Separate exact simulation state from intelligence-derived display state |
| Progress bar lies about scale | Normalize to `0..100`, clamp, display value/cap, test boundary frames |
| Hardcoded TFR-style participant branches | Generic country-scope rows and filtered arrays |
| TNO-style total UI replacement | Decision-category shell with optional bounded pop-out only |
| Localisation parses but does not fit | Render tests at the smallest supported resolution and 1920x1080 |
| TNO/TFR asset or code copying | Mechanical references only; create OEM-native script, copy, and art |

## Open design decisions

These do not block the core state contract, but must be settled before their named phase:

1. **Competitive presentation date or threshold.** Phase 1 initializes foundations on the first enabled monthly pulse and uses `AI_RACE_active` only for headless simulation membership. Before the normal dashboard is exposed, lock a separate documented date/capability condition and optional threshold-based early activation.
2. **Initial participant eligibility.** The MVP is USA and China. Later participants should enter through one eligibility trigger and adapter registry, not country-specific GUI work.
3. **First lab roster and activation history.** Lock before laboratory implementation. Do not author every modern lab during the core-state phase.
4. **Outcomes Only visibility.** This architecture recommends a read-only summary. If the product decision changes to hidden, update the game-rule description and acceptance matrix together.
5. **Alert surface.** Prefer MD Alerts for major warnings; use a dashboard-local strip if opening the precise race panel cannot be expressed cleanly through the shared system.
6. **Art direction.** Establish OEM-native dimensions and a restrained visual language after the dashboard wireframe, before final GFX production.
7. **Probability model.** Breakthrough randomness must be deterministic, bounded, transparent enough to debug, and absent from the first state-only phase.

## Phase 1 locked contract

The first implementation slice freezes these decisions so later work does not reinterpret the kernel:

- Full and Outcomes Only enter the same headless state machine. Outcomes Only adds only its reconstruction/presentation marker in this phase.
- Off is gated at the existing monthly singleton caller. It creates no state or debug category and performs no normal race callback.
- The first enabled monthly pulse is the sole bootstrap and late-start recovery path. No event namespace, hidden event, or second startup owner is added.
- USA and China are the only eligible participants. The participant registry stores country scopes in that order, excludes `collapsed_nation`, and rebuilds rather than mutating an array during iteration.
- All six stock, external, and effective metric slots initialize to `0`. Phase 1 resets every external slot to `0`; owner-system adapters remain Phase 2 work.
- Ranking uses effective capability only. China leads only when strictly greater; USA wins an exact tie because it is first in the fixed registry.
- `ai_race_frontier_gap` is signed `capability - frontier`, so the leader is `0` and lagging participants are negative.
- `global.ai_race_last_processed_quarter` stores `year * 4 + quarter index`. The replay-guarded wrapper alone advances `global.ai_race_epoch` and the dirty counter.
- `ai_race_rebuild_derived_state` is pure and repeatable. Debug repair calls it without advancing scheduled state.
- Temperature and frontier pressure remain bounded zero-valued placeholders until their formulas are approved.
- Phase 1 has no normal dashboard, laboratory, project, policy, pressure pulse, alert, modifier, or event content.

## Next implementation slice

The first code slice should implement only the separate game rule, mode triggers, USA/China initialization, six clamped country metrics, global initialization, a quarterly debug update, and debug-only readout/repair controls. It should not add the final dashboard, laboratories, selectable projects, model-release events, new art, or world effects.

The phased Claude campaign is defined in `.claude/docs/great-ai-race-implementation-campaign.md`.
