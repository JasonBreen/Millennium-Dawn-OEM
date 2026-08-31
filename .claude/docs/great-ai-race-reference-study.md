# Great AI Race Mechanical Reference Study

Status: design evidence for the architecture and Claude implementation campaign. This is not a runtime dependency and does not authorize copying third-party code or assets.

## Source boundary

The local Workshop sources were inspected read-only:

- TNO: Workshop item `2438003901`, descriptor version `1.10.0b`.
- TFR: Workshop item `3350890356`, descriptor version `1.0.8.3`.

Paths below are relative to the applicable Workshop item root. The repository must not import, vendor, or reference those paths at runtime.

All transfers in this document are abstractions: interaction grammar, state topology, pacing, information hierarchy, and failure design. Millennium Dawn OEM must author its own script, localisation, art, layout, fonts, icons, and narrative.

## Design verdict

The strongest combination is:

- **TFR Cognoscenti** for competing internal actors, constrained influence, actor-aligned actions, coupled pressure tracks, threshold states, and explicit crisis transitions.
- **TNO Guangdong** for laboratory/project selection, active project presentation, release history, and dense card-based information.
- **TNO Cold War and alert systems** for rival comparison and attention routing.
- **OEM native systems** for authoritative state, scheduling, arrays, decisions, missions, alerts, modes, localisation, AI behavior, and performance.

The Great AI Race should not imitate the surface style of either total conversion. It should translate their mechanical clarity into an OEM-native decision dashboard.

## TFR Cognoscenti study

### System topology

The Cognoscenti is not one mechanic. It is three connected layers:

1. An internal power struggle among three fixed pillars.
2. A separate two-axis pressure-management loop called the Masquerade.
3. Explicit crisis missions and authored state transitions, including hard failure.

That separation is the main architectural lesson. Internal actor politics, normal systemic pressure, and crisis resolution use different state and surfaces.

### Unlock and initial balance

Completing the path's central focus installs three influence modifiers and seeds the pillars at `34 / 33 / 33`:

- Blood: corporate and financial interests.
- Body: intelligence and security institutions.
- Mind: military-industrial and technological institutions.

Evidence:

- `common/national_focus/TFR_national_focus_USB.txt:12145-12211`
- `common/decisions/categories/TFR_decision_categories_USB.txt:26-37`

The values form a constrained pool. They are not three unrelated progress bars.

### Dashboard composition

The decision category attaches a `decision_category` scripted GUI:

- `common/decisions/categories/TFR_decision_categories_USB.txt:26-37`
- `common/scripted_guis/TFR_scripted_guis_USB.txt:6-180`

The GUI presents:

- three horizontally aligned organization seals;
- one visible leader portrait and identity tooltip for each pillar;
- a fixed appointment strip for agencies/advisers;
- a large text summary with exact influence shares and each scaling payoff.

Evidence:

- headers and leaders: `interface/TFR_USB_cogno.gui:7-89`
- appointment strip: `interface/TFR_USB_cogno.gui:101-267`
- influence summary container: `interface/TFR_USB_cogno.gui:269-277`
- presentation text: `localisation/english/TFR_country_localisation_USB_l_english.yml:939-988`

The dashboard is visually legible because the actors have identities, leaders, colors, and specialties. Its implementation is not scalable: the appointment strip uses overlapping hardcoded buttons and one visibility trigger/effect branch per person.

### Actor-aligned decisions

The category groups decisions by pillar:

- Body actions emphasize security, intelligence, political control, and suppression: `common/decisions/TFR_decisions_USB.txt:3796-4038`.
- Blood actions emphasize finance, construction, corporate contribution, development, and manipulation: `common/decisions/TFR_decisions_USB.txt:4039-4268`.
- Mind actions emphasize research, DARPA, semiconductors, military industry, and special projects: `common/decisions/TFR_decisions_USB.txt:4269-4637`.

The typical action has three layers:

1. A visible actor identity through its icon/theme.
2. An immediate or timed national effect.
3. An influence change on completion.

The important part is that influence is the political consequence of doing useful actor-aligned work. The action is not a button whose only payload is `+5 influence`.

### Constrained influence and scaling payoff

Each influence writer calls a common balancer:

- writers: `common/scripted_effects/TFR_scripted_effects_USB.txt:5652-5713`
- clamp/balance: `common/scripted_effects/TFR_scripted_effects_USB.txt:5729-5897`

Each share also contributes one small, recognizable national effect:

- Blood: building construction speed.
- Body: Political Power gain.
- Mind: army organization.

Evidence: `common/dynamic_modifiers/TFR_dynamic_modifiers_USB.txt:615-636`.

This is a better model than making influence another capability score. A group can be politically dominant without being technically strongest.

### TFR balancing defect to avoid

TFR reduces the nonselected pillars, clamps all three, and then assigns any excess/deficit through an eligible `random_list`:

- `common/scripted_effects/TFR_scripted_effects_USB.txt:5818-5886`

That makes a conserved political pool partly stochastic and complicates save/debug reasoning. The Great AI Race must use integer shares and deterministic redistribution.

Recommended behavior to freeze in Prompt 0:

1. Calculate the selected lab's actual gain.
2. Deduct the same total from other active labs, proportionally to their current support.
3. Allocate rounding loss in a stable order, such as highest donor share then lowest stable lab ID.
4. Set the selected share from the actual deducted amount.
5. Assert/repair the total to exactly `100`, with any final remainder applied through one documented rule.

No random list is needed.

### Influence changes available outcomes

The pillar balance affects qualitative choices, not only modifiers. A later succession event exposes different candidates at `40%` and `50%` influence thresholds and exposes more moderate options when no pillar dominates:

- `events/TFR_events_USB.txt:15983-16199`

This is the strongest Cognoscenti pattern to transfer.

For the Great AI Race:

- a dominant lab may unlock its preferred high-risk project, release posture, procurement package, or crisis response;
- a balanced ecosystem must unlock a distinct coalition option, shared evaluation regime, multi-lab consortium, or cross-checking benefit;
- the balanced state is a deliberate strategy, not the absence of progress;
- support thresholds never replace capability, compute, talent, or control prerequisites.

### Influence-gated projects

The Cognoscenti includes longer projects that require actor influence. One special project requires at least `40%` Mind influence:

- `common/decisions/TFR_decisions_USB.txt:4393-4428`

For the race, a laboratory's support may gate access to a proposal, but the project still checks its actual resources and expertise. Political access creates the offer; it does not conjure technical feasibility.

### The Masquerade is a separate pressure loop

The Masquerade uses a second decision category:

- `common/decisions/categories/TFR_decision_categories_USB.txt:52-63`

Its setup creates two pressures with different starting values and recurrence intervals:

- Public Awareness begins at `20%`, with a 25-day mission interval.
- Extremist Activity begins at `30%`, with a 20-day mission interval.

Evidence: `common/national_focus/TFR_national_focus_USB.txt:12052-12105`.

Two self-reactivating missions add five points on expiry:

- `common/decisions/TFR_decisions_USB.txt:8907-8965`

The Great AI Race should transfer the two-axis topology but not the 20/25-day cadence. Its participant-wide pressure pulses belong in the central quarterly reducer.

### Intervention tradeoffs

Masquerade actions reduce one or both pressures but consume Political Power, impose timed modifiers, lock an agency action channel, trigger follow-up content, or raise the other pressure:

- `common/decisions/TFR_decisions_USB.txt:8967-9687`

A clear example lowers one pressure through censorship while raising the other; a prior infrastructure investment reduces the secondary penalty:

- `common/decisions/TFR_decisions_USB.txt:9169-9237`

This is the correct shape for AI Race policy:

- slow deployment to reduce control debt but widen the frontier gap;
- publish evaluations to improve control while increasing public alarm or revealing capability;
- subsidize displaced workers to improve confidence while consuming capital;
- classify a project to reduce public exposure while harming openness/talent;
- rush a release to gain momentum while increasing control debt and race temperature.

An intervention must not be a costless `lower danger` button.

### Explicit bands and material consequences

Both Masquerade variables are clamped and mapped to five bands:

- below `10%`;
- `10-30%`;
- `30-50%`;
- `50-80%`;
- `80%+`.

The same thresholds drive status names, national-spirit tiers, and increasingly serious consequences:

- state writers and idea swaps: `common/scripted_effects/TFR_scripted_effects_USB.txt:5436-5650`
- scripted status names: `common/scripted_localisation/TFR_scripted_loc_USB.txt:788-993`
- idea tiers: `common/ideas/TFR_ideas_USB.txt:4489-4645`
- displayed status/value: `localisation/english/TFR_country_localisation_USB_l_english.yml:984-985`

Important distinction: reaching the maximum band does not automatically collapse the Cognoscenti. It applies the maximum bounded penalty tier. Hard failure belongs to a separate transition.

The race must likewise keep threshold presentation, band consequences, crisis activation, and crisis resolution as distinct steps.

### A minigame can enter crisis mode

Later Cognoscenti content removes the ordinary Masquerade missions, creates a different set of pursuit variables, and starts a new countdown:

- caller: `common/national_focus/TFR_national_focus_USB.txt:13691-13705`
- transition event: `events/TFR_events_USB.txt:14982-15014`

The transferable lesson is not the content of that pursuit. It is the state transition:

```text
normal pressure loop -> explicit crisis mode -> crisis actions/deadline -> recovery or new state
```

Ordinary pressure pulses should pause during an AI Race crisis. The player sees a bounded crisis action set rather than the entire normal decision catalog plus another timer.

### Authored crisis outcomes

One Cognoscenti crisis mission runs for 250 days:

- mission: `common/decisions/TFR_decisions_USB.txt:3752-3794`
- recovery event after the conflict ends: `events/TFR_events_USB.txt:17655-17675`
- failure event after timeout/defeat: `events/TFR_events_USB.txt:18114-18200`

A different collapse event and comprehensive transition effect form a separate chain:

- collapse event: `events/TFR_events_USB.txt:17889-17913`
- collapse effect: `common/scripted_effects/TFR_scripted_effects_USB.txt:7204-7320`

These chains must not be conflated. The mechanical lesson is that a terminal state is explicit, visible, authored, and exactly once.

For the Great AI Race:

- recoverable failure is the default;
- extreme public alarm/control debt alone is nonterminal;
- a crisis requires an explicit trigger and stable crisis ID;
- the crisis mission states success, cancellation, and timeout consequences;
- mechanical payload resolves in the crisis effect; a later report event frames the result;
- a genuinely terminal national branch requires a separately approved brief and natural-runtime acceptance.

### Event usage

Cognoscenti uses many events to dramatize routine decisions. OEM should be more selective.

The Great AI Race event layer should:

- make every event `is_triggered_only = yes`;
- use events for major release choices, breakthroughs, severe incidents, crisis transitions, and final outcomes;
- deliver routine project payload at the project resolution site;
- batch routine notifications or use `minor_flavor = yes` where appropriate;
- keep Full visible, Outcomes Only silent except for major outcomes, and Off absent;
- never make the player click an event option merely to receive an already-decided routine effect.

### Cognoscenti patterns to transfer

- A constrained support pool among recognizable actors.
- Actor identity, leadership, specialty, support share, and aligned actions.
- Support thresholds that alter the available option space.
- A meaningful balanced-ecosystem outcome.
- Capability and political support as independent values.
- Two coupled but distinct pressure axes.
- Scheduled pressure pulses with investable pacing.
- Interventions with secondary tradeoffs.
- Explicit shared threshold bands for text and consequences.
- A bounded transition from normal play into crisis mode.
- A visible crisis deadline with authored recovery/failure.

### Cognoscenti patterns not to transfer

- Three permanent hardcoded columns as the complete lab model.
- One hardcoded button/trigger/effect branch per leader.
- Stochastic fixed-sum normalization.
- A giant dynamic-modifier variable surface.
- Long blank localisation used as layout spacing.
- A single category containing an ever-growing action catalog.
- 20/25-day recurring missions for every participant.
- GUI clicks that directly own strategic state.
- Routine broad `every_country` or state loops.
- Mass spirit deletion, focus-tree replacement, faction destruction, or country splintering as a normal AI incident.
- Maximum pressure as an automatic game over.

## TNO study

TNO is the secondary reference for the project/laboratory presentation layer.

### Alert bar

`common/scripted_guis/TNO_alertbar.txt:1-26` uses a tokenized dynamic list with name, description, image, normal click, and dismiss behavior.

Translation: use OEM's MD Alerts system for major race attention states or a bounded dashboard-local strip when a shared alert cannot navigate correctly.

### Guangdong project and release panels

`common/scripted_guis/TNO_GNG_Product_Decisions_GUI.txt:1-118` separates active work, progress, performance, release history, and inactive states.

Translation: the Great AI Race Projects tab separates active project state, phase/progress, evaluation/release choice, and a derived completed-release history.

### Guangdong research-team selection

`common/scripted_guis/TNO_GNG_Research_Team_GUI.txt:1-180` and `interface/Guangdong/TNO_GNG_Research_Team.gui:1-205` present active projects and selectable project cards through a dense custom surface.

Translation: use reusable OEM dynamic-list cards and native project clocks. Do not copy the fixed layout, art, fonts, project data, or GUI-owned AI interval.

### Cold War comparison

`common/scripted_guis/TNO_Cold_War_GUI.txt` demonstrates a strategic comparison surface between major actors.

Translation: the Global Race tab compares country scopes, frontier position, gap, observed releases, and intelligence confidence. It does not reveal unjustified exact foreign values.

### TNO patterns not to transfer

- Total top-bar or diplomacy-view replacement.
- Total-conversion visual language.
- Ten-day GUI AI evaluation.
- Strategic calculation in GUI properties.
- Unbounded narrative density.
- A second timer that duplicates a native mission/timed flag.

## Combined Great AI Race blueprint

### Inner national loop

```text
canonical national inputs
  -> effective national metrics
    -> laboratories with independent capability/talent/momentum
      -> constrained support shares
        -> actor-aligned actions and project offers
```

Source inspiration: Cognoscenti pillars.

OEM implementation: country state, stable lab IDs, deterministic redistribution, logged decisions/shared effects, AI-safe weights, reusable dynamic-list cards.

### Project loop

```text
project offer
  -> resource commitment
    -> preparation
      -> training
        -> evaluation
          -> release choice
            -> outcome and release history
```

Source inspiration: TNO Guangdong.

OEM implementation: native mission/timed-flag authority, exactly-once phase guards, persistent project IDs, AI actions outside GUI.

### Pressure loop

```text
capability/deployment/release choices
  -> public alarm + control debt
    -> quarterly pulse/band consequences
      -> intervention tradeoffs
        -> explicit crisis trigger
          -> crisis mission
            -> recovery or authored failure
```

Source inspiration: Cognoscenti Masquerade and crisis transitions.

OEM implementation: central participant reducer for routine pulses, native mission only for active crisis deadlines, explicit crisis ID/epoch, recoverable default.

### Global loop

```text
participant scores
  -> frontier and gaps
    -> ranked scope array
      -> race temperature
        -> global pressure and major alerts
```

Source inspiration: TNO actor comparison and TFR escalation presentation.

OEM implementation: existing monthly singleton, quarterly reducer, scope arrays, deterministic ranking, intelligence-derived display.

## UI composition

The complete dashboard should eventually contain:

1. Overview: headline metrics, race state, bottleneck, public alarm, control debt, alerts.
2. Laboratories: reusable actor cards, support shares, specialties, selected-lab details.
3. Projects: offers, active phase/clock, evaluation, release choice, history.
4. Global Race: ranked country scopes, frontier gap, estimates, intelligence confidence.
5. Policy: national posture, compute allocation, talent, deployment, control investment.
6. Crisis mode: a bounded replacement/overlay with its own deadline and actions, not another permanent tab full of ordinary controls.

The Cognoscenti's three-column identity is preserved in the cards. Its hardcoded cabinet grid is not. TNO's information density is preserved in tabs and selected-entity panels. Its total-conversion shell is not.

## Acceptance questions for every borrowed concept

Before implementing a reference-inspired element, Claude must answer:

1. What is the OEM-native authoritative owner?
2. Can the game AI use the same effect without opening the GUI?
3. Does the feature work in Full, Outcomes Only, and Off?
4. Does it survive save/reload and late start exactly once?
5. Does it add a bounded strategic choice rather than another passive number?
6. Can a new lab or participant be added without duplicating GUI containers?
7. Is routine work on the existing monthly/quarterly path?
8. Is every foreign value displayed with justified precision?
9. Is every string, layout, and asset original to OEM?
10. Is the evidence static, rendered, console-fixture, or natural runtime, and reported honestly?
