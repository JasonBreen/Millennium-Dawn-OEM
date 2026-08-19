---
title: OEM Upstream Packaging Plan
description: Dependency-ordered pull-request slices for contributing OEM systems to Millennium Dawn
---

The OEM release candidate must not be proposed upstream as one pull request. At the synchronized baseline, the fork delta contains hundreds of paths, shared dispatchers that name nearly every chain, a 32-chain schema-v5 contract, and a large artwork tranche. Focused submissions require a generic kernel first, followed by incremental chain registration.

This is a packaging plan, not a claim that any slice is runtime-accepted. Refresh the path counts and base commit when extraction begins.

# Dependency Shape

Two current strongly connected components are atomic unless their cross-write seams are extracted:

- IBM, Sun/Microsoft, Lenovo, and Motorola.
- Texas Instruments and Micron.

The main acyclic dependencies are:

```text
BlackBerry
└─ Matrox
   └─ IBM / Sun-Microsoft / Lenovo / Motorola
      ├─ Apple
      │  ├─ Foxconn
      │  └─ Arm Holdings
      ├─ Oracle
      └─ NVIDIA
         └─ Nintendo

HP ───────────────────────────────────────┘
ATI/AMD ───────────────────────> NVIDIA
Nokia ─────────────────────────> NVIDIA
  ├─ Siemens
  ├─ France Corporate Systems
  └─ Arm Holdings
TSMC
  ├─ NVIDIA
  ├─ Russian Computing Sovereignty
  ├─ Arm Holdings
  └─ Nintendo
Ericsson ──> Sony ─────────────> Nintendo
E3 ────────────────────────────> Nintendo
```

The generic GPU system is an additional substrate for ATI/AMD, Matrox, NVIDIA, Sony, and other GPU integrations. The physical-compute stack depends on completed TI, Micron, and Motorola outcomes. Linux and the USA Corporate Systems economy are late aggregators and must not precede their input chains.

# Proposed Pull-Request Series

| Slice                                              | Prerequisites                                                               | Owned files and shared-file boundary                                                                                                                                                                                        | Why it is reviewable                                                                                        | Required runtime evidence                                                                                                                            | Static gates and likely conflicts                                                                                                                                                 |
| -------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0. Fork-only RC hygiene                            | None; do not submit upstream                                                | Restore authoritative upstream compatibility/Vietnam files; remove temporary sync workflows, local MCP/editor state, obsolete evidence bundles, and stale ignore rules                                                      | Separates fork sanitation from feature review                                                               | None beyond launcher/load smoke if deployment changes                                                                                                | `git diff --check`, exact upstream blob hashes; conflicts in `.gitignore`, workflows, and workspace settings                                                                      |
| 1. Generic idea-validator fix                      | Current upstream tools                                                      | `tools/validation/validate_ideas.py` and its icon regression test                                                                                                                                                           | Generic tuple-to-sprite-name correctness; no gameplay dependency                                            | None                                                                                                                                                 | Targeted tests plus full `python -m pytest`, Ruff, Black, Pylint, and Mypy; low conflict                                                                                          |
| 2. Corporate History kernel                        | Validator fix may land before or after                                      | Game rule, generic on-actions, rule triggers, bounds helpers, empty/incremental registry, contract validator/schema tests, minimal English rule loc and docs                                                                | Establishes Full/Outcomes Only/Off and idempotent dispatch without referring to absent chains               | All three rules, repeated startup/monthly calls, save/reload, no visible event in Outcomes Only                                                      | Full tools tests, strict empty/incremental contract, event/effect reference checks; highest conflicts in `00_corporate_history_effects.txt`, dispatcher, manifest, and game rules |
| 3A. Generic GPU development                        | Kernel only if registered through it                                        | Generic GPU events/effects/ideas, English loc, event picture, sprite definition, attribution                                                                                                                                | Cross-country substrate with no company-chain payload                                                       | Natural GPU delivery, representative branch, reload, UI image, clean log                                                                             | Event, variable, idea, loc, GFX, attribution checks; conflicts in shared event-picture registration                                                                               |
| 3B. Legacy USA OEM foundation                      | Kernel and any required upstream USA hooks                                  | Extract OEM additions from `events/United States.txt` into coherent Palantir/storage/defence namespaces; USA English loc and narrow hooks                                                                                   | Removes a large mixed diff from an upstream-owned event file and gives later IBM/Linux reads a stable owner | USA portion of issue #28, save/reload, absent/collapsed guards                                                                                       | Caller/namespace/variable/loc checks; high conflict in `United States.txt` and USA loc                                                                                            |
| 3C. Israel electronics                             | Kernel                                                                      | Israel events, effects, ideas, owner on-action, English loc                                                                                                                                                                 | Standalone national flavour with no contracted prerequisite                                                 | Full/Outcomes/Off, one later start, fallback AI under bankruptcy, clean UI/log                                                                       | Event, idea, variable, caller, loc checks; low shared conflict                                                                                                                    |
| 4. Independent chain wave                          | Kernel; GPU substrate for ATI/AMD                                           | Separate PRs for Dell, E3, Google, AIG, Taiwan PC Giants, ATI/AMD, BlackBerry, HP, Nokia, TSMC, Xbox, Huawei, Ericsson, Poland, Ukraine; keep TI+Micron atomic unless their callback is deferred                            | Each chain owns its events/state/ideas/loc and adds one manifest/dispatcher registration                    | Natural segment, counterfactual, three rules, later start, repeated reconstruction, schedule/callback/terminal reload, UI/log                        | Strict incremental contract, state-model tests, event/caller/variable/flag/idea/loc/GFX checks; conflicts limited to manifest, dispatcher, country loc, sprites, attribution      |
| 5. Dependency chain wave                           | Prior named inputs                                                          | Matrox after BlackBerry plus GPU/ATI integration; Siemens and France after Nokia; Sony after Ericsson; Russia after TSMC                                                                                                    | Each consumes already-landed read-only state and can be reviewed against explicit fallbacks                 | Issues #24, #26, #27, and #112 as applicable; missing-country and cross-owner tests mandatory                                                        | Same chain gates plus dependency-order/write-permission checks; Matrox/Sony art must be atomic with code and attribution                                                          |
| 6. IBM transaction component                       | BlackBerry, Matrox, HP, legacy USA storage                                  | Current atomic form: IBM, Sun/Microsoft, Lenovo, Motorola, bilateral mirrors, ideas, artwork, loc, manifest entries, declared cross-writes. Preferred alternative: four fallback-safe base PRs plus one integration-seam PR | Atomic only because current transactions form a real cycle; seam extraction is preferable                   | Full issue #25 matrix through 2027, ten bounded variables, transaction handoffs, all capstones/crises, later starts, reload, collapsed/absent owners | Strict contract/write ownership, simulator/state tests, event/caller/loc/GFX; extreme conflicts in USA/CHI loc, manifest, dispatcher, attribution                                 |
| 7. Dependent company wave                          | IBM component and named graph inputs                                        | Apple, Oracle, Foxconn, NVIDIA, Arm, then Nintendo; each owns its chain registration, loc, ideas, art, and attribution                                                                                                      | Acyclic order makes each consumer reviewable against stable prerequisites                                   | Per-chain full matrix; Nintendo retains issue #45 presentation and AI coverage                                                                       | Normal chain gates; art-heavy conflicts in `MD_eventpictures.gfx` unless chain-specific GFX files are introduced                                                                  |
| 8. Physical-compute integration                    | TI, Micron, Motorola                                                        | Aggregate effect and ideas plus narrow producer calls; no company capstone replacement                                                                                                                                      | Shared aggregate is reviewed after all producers, not hidden in one producer PR                             | Three outcomes resolved, two qualifying seams, stale-success removal, reconstruction order/idempotence, exactly one aggregate outcome                | State/ownership/simulator tests; conflicts in three producer effects and aggregate files                                                                                          |
| 9. National dashboards                             | All displayed chains for each country                                       | Country decision/category, scripted localisation, unified English loc. Fold small dashboards into the final country chain; keep USA separate                                                                                | UI is reviewed only after its source state exists                                                           | Correct visibility, collapse suppression, reload, labels, no raw/empty rows or invalid icon                                                          | Decision, icon, loc, scripted-loc checks; conflicts in `99_TAG_decision_categories.txt` and unified country loc                                                                   |
| 10. Linux ecosystem                                | IBM, Dell/storage, Huawei, Arm, France, Russia, Poland, and native adapters | Prefer Linux core, then national adapters, then USA bridge; own game rule, events, decisions, ideas, triggers/effects, loc                                                                                                  | Prevents a global aggregator from carrying placeholders for absent systems                                  | Full/Outcomes/Off, participant lifecycle, five milestones, recovery, program expiry, collapse, save/reload, no USA feedback loop                     | Contract shared-system tests, event/decision/idea/loc checks; broad country adapter and game-rule conflicts                                                                       |
| 11. USA Corporate Systems and real-options economy | All USA contributors, USA dashboard, Linux bridge                           | USA dashboard, aggregation effects, real-options effects, dynamic modifiers, ideas, scripted loc, USA loc, simulator/tests, contract lifecycle/economic entries                                                             | Late integration PR with stable inputs and explicit anti-feedback boundary                                  | Four policy lifecycles, no refresh/stack, modifier replacement, bounds, bankruptcy/collapse, expiry, reload/civil war, no Linux feedback             | Simulator plus decision/modifier/idea/loc/contract checks; highest USA shared-file conflict                                                                                       |
| 12. Final documentation                            | Stable live contract and runtime results                                    | Framework page, mechanics/current-state page, dependency snapshot, runtime matrix, navigation                                                                                                                               | Documents the system that actually landed, with evidence classes kept distinct                              | None inferred from docs; attach exact-head evidence already produced by prior slices                                                                 | Docs-quality links/build; conflicts in navigation and issue-state wording                                                                                                         |

# Per-Chain Ownership Rule

Every content PR owns:

- Its event namespace.
- Its owner-specific scripted effects and triggers.
- Its ideas and English localisation.
- One narrow manifest entry and one dispatcher registration.
- State-model or simulator coverage.
- Its artwork, dedicated sprite definition, and attribution when applicable.

Do not parallel-edit branches that each carry full copies of the manifest or dispatchers. Stack them and rebase after every prerequisite lands.

# Shared Hot Spots

| File or surface                                                     | Risk                                             | Extraction rule                                                |
| ------------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------- |
| `tools/corporate_history_contract.json`                             | 32 chains plus lifecycle/shared/economic schemas | One narrow manifest delta per stacked PR                       |
| `common/scripted_effects/00_corporate_history_dispatch_effects.txt` | Names almost every chain                         | Reduce to a generic registry; one registration block per chain |
| `common/scripted_effects/00_corporate_history_effects.txt`          | Generic helpers mixed with owner reconstruction  | Move owner wrappers to owner files                             |
| `common/scripted_triggers/MD_corporate_history_triggers.txt`        | Generic gates mixed with chain predicates        | Split rule gates from owner predicates                         |
| `localisation/english/MD_focus_USA_l_english.yml`                   | Many independently owned systems                 | Stack USA PRs; never develop competing edits in parallel       |
| `interface/MD_eventpictures.gfx`                                    | Multiple art tranches                            | Prefer chain-specific GFX registration files                   |
| `ATTRIBUTIONS.md`                                                   | Art provenance for multiple chains               | Ship each attribution with the asset that requires it          |
| `events/United States.txt`                                          | Upstream event file plus mixed OEM namespace     | Extract owner-coherent namespaces before submission            |
| USA dashboard/economy effects                                       | Reads many company roots                         | Land only after contributors and keep adapters read-only       |

# Minimum Acceptance Per Content PR

Static:

- Strict Corporate History validation for the incremental manifest.
- Relevant state-model and simulator tests.
- Full pytest whenever `tools/` changes.
- Event caller, variable, flag, localisation, modifier, idea, decision-icon, and GFX-reference checks.
- English localisation BOM, header, and duplicate-key checks.
- `git diff --check`.
- Asset definition, texture existence, and attribution consistency.
- No non-English localisation changes.

Runtime:

- One natural historical segment.
- Representative counterfactual branches.
- Full, Outcomes Only, and Off.
- One later start.
- Repeated reconstruction.
- Save/reload around scheduling, callbacks, and terminal state.
- Collapse and absent-country fallback where applicable.
- Exactly one terminal outcome and no duplicated reward or foreign-state write.
- UI screenshots for events, ideas, options, and tooltips.
- Fresh `error.log` without new namespace, scope, localisation, modifier, or GFX errors.
- Exact tested commit, checksum, date, country, route, and evidence class.

Issue mapping remains: #24 Sony, #25 the IBM transaction component, #26 Matrox logic, #27 Nokia/Ericsson/Siemens, #28 the broad North American smoke, #45 presentation/balance/AI, #112 Matrox visual acceptance, and #194 mechanics documentation.
