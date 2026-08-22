---
title: OEM Release-Candidate Runtime Matrix
description: Exact-head acceptance plan for Corporate History chronology, reconstruction, save safety, presentation, and marquee artwork
---

This matrix is the runtime gate for the OEM release candidate. Static validation does not close a runtime item.

**Candidate under test:** PR #209, branch `codex/oem-2.0-rc-remediation`, head `2d3de527d7a45467a01ca7c6ca70af1f600d9363`, tree `c6e78722e6dffab55cf28a4f57627a927ab09b02`, fork base `6aede79ae624d8b0512cc662787234c8a6f4dd3f`, upstream freeze `dfa37942892e4cbc8743e4eba8c48736e77d6307`.

**Status at this revision:** static and CI gates are green on the exact head. A substantial body of earlier runtime evidence exists and has been recovered and catalogued below, but none of it was captured on this candidate, and the candidate replaced the dispatch architecture those runs exercised. Zero acceptance layers currently pass on the exact head. See [Coverage Summary](#coverage-summary) and [Remaining Acceptance Set](#remaining-acceptance-set).

# Coverage Summary

Status on the exact candidate head `2d3de527d7`. `SUPERSEDED` means credible evidence exists at an earlier commit but the gameplay logic it exercised changed afterwards.

| Layer                                        | Status on RC head | Evidence count on RC head | Prior evidence recovered | Remaining gap                                                               |
| -------------------------------------------- | ----------------- | ------------------------: | -----------------------: | --------------------------------------------------------------------------- |
| A. Full natural chronology                   | SUPERSEDED        |                         0 |                        3 | Yearly dispatcher and per-country hosts were replaced; rerun natural Full   |
| B. Outcomes Only                             | SUPERSEDED        |                         0 |                        4 | Mode gate moved into every event trigger; rerun Outcomes Only               |
| C. Corporate History Off                     | SUPERSEDED        |                         0 |                        3 | Off now also suppresses ISR/USA legacy/GPU chains; rerun Off and Independence |
| D. Later start reconstruction                | NO EVIDENCE       |                         0 |                        1 | 2017 start never run at any commit; ATI 2026 fixtures are not a later start |
| E. Scheduled-event save/reload               | SUPERSEDED        |                         0 |                        2 | Reloads were dashboard-state only, never around a pending scheduled event   |
| F. Hidden callback and reconstruction reload | NO EVIDENCE       |                         0 |                        0 | No `.90` callback or repeat-reconstruction reload has ever been run         |
| G. Terminal/capstone                         | SUPERSEDED        |                         0 |                        1 | Only ATI/AMD capstone was observed, at a superseded commit                  |
| H. Collapsed and absent countries            | NO EVIDENCE       |                         0 |                        0 | Never run; new January-window dispatcher makes this higher risk, not lower  |
| I. Representative counterfactuals            | NO EVIDENCE       |                         0 |                        0 | No counterfactual terminal save exists for any chain                        |
| J. `error.log`                               | SUPERSEDED        |                         0 |                        4 | Prior loads isolated exactly one OEM error class, since repaired; reload    |
| K. UI/GFX/localisation                       | PARTIAL           |                         1 |                        8 | Only the PS2 picture is byte-identical; 12 sprites are new and unrendered   |

## Priority chain coverage

| Chain                     | Best evidence recovered                                          | Class  | Validity on RC head |
| ------------------------- | ---------------------------------------------------------------- | ------ | ------------------- |
| IBM (#25)                 | `USA_ibm_events.12` natural at 2000.02.01; `.12` console fixture | `N`+`C` | SUPERSEDED          |
| Sony (#24)                | `JAP_sony_events.1` natural twice; repaired artwork fixture      | `N`+`C` | PARTIAL (art only)  |
| Matrox (#26/#112)         | `CAN_matrox_events.1` natural at 2000.03.17; `.1` console        | `N`+`C` | SUPERSEDED          |
| Nokia (#27)               | none                                                              | -      | NO EVIDENCE         |
| Ericsson (#27)            | `SWE_ericsson_events.1` console fixture                          | `C`    | SUPERSEDED          |
| Siemens (#27)             | none                                                              | -      | NO EVIDENCE         |
| Broader USA/OEM smoke (#28) | `USA_oem_events.13.b`, `ISR_oem_events.1.b`/`.6.a` natural     | `N`    | SUPERSEDED          |
| Game-rule modes           | Full / Outcomes Only / Off across three campaign phases          | `N`    | SUPERSEDED          |
| Save/reload               | Dashboard-state reload only                                       | `N+reload` | SUPERSEDED      |
| Later start               | none                                                              | -      | NO EVIDENCE         |
| UI/GFX                    | Dashboards, tiers, ATI capstone, repaired PS2 art                | `C`/`N` | PARTIAL            |
| `error.log`               | Four archived load logs                                           | `S`    | SUPERSEDED          |

# Evidence Rules

Each result must identify the exact tested commit and any uncommitted deployment content. Capture:

- Git commit, `git status --short`, and hashes of all deployed changed files.
- Hearts of Iron IV version and checksum.
- Start date, country, AI setting, Corporate History rule, and Linux rule.
- Whether the run was natural (`N`), a targeted console fixture (`C`), or natural with save/reload (`N+reload`).
- Pre-choice and post-choice screenshots, relevant `game.log` lines, and a fresh `error.log`.
- Before/after flags, variables, ideas, Political Power, Stability, treasury, factories, and research bonuses.
- Save name and checkpoint date for every reload test.

Evidence classes:

- **Natural (`N`)**: no `event`, `effect`, or `date` command. This is the only evidence that proves ordinary scheduling, triggers, chronology, AI choice, and duplicate suppression.
- **Targeted console (`C`)**: proves a branch predicate, payload, rendered event, or idempotence property only. The `event` command bypasses normal delivery.
- **Natural with reload (`N+reload`)**: natural delivery with a save/reload before or after a pending event, callback, or terminal choice.
- **Static (`S`)**: source, validator, or asset evidence. It cannot close a runtime checkbox.

Retake the Git and deployment hashes immediately before testing. A commit hash alone is insufficient if the deployed build contains uncommitted changes.

# Rule Presets

Corporate History and Linux are independent:

| Preset            | Corporate History | Linux | Purpose                                                          |
| ----------------- | ----------------- | ----- | ---------------------------------------------------------------- |
| Full isolated     | Full              | Off   | Visible Corporate History chronology without Linux-system noise  |
| Outcomes isolated | Outcomes Only     | Off   | Silent historical reconstruction and idempotence                 |
| Off isolated      | Off               | Off   | Absence of chain-owned Corporate History state                   |
| Independence      | Off               | Full  | Linux still initializes while Corporate History remains disabled |

Off permits no Corporate History bootstrap marker or chain/subsystem-owned scheduling, resolution, reconstruction, route, crisis, dashboard, adapter, or outcome state. Native BRI and the Linux base route must remain usable without creating that state.

# Test Order

Run the smallest high-signal checks first:

1. Matrox UI/GFX fixtures and restart check for issues #26 and #112.
2. IBM scheduled-event and terminal/reconstruction boundaries for issue #25.
3. Sony chronology, Ericsson dependency, and capstone for issue #24.
4. Nokia, Ericsson, and Siemens integration for issue #27.
5. Outcomes Only, Off, later-start, reload, and collapsed-country coverage across representative countries.
6. The complete 2000-2027 release smoke required by issue #28.
7. Human presentation and balance review required by issue #45.

# Eleven-Layer Acceptance Matrix

| Layer                                        | Evidence                                                         | Setup and execution                                                                                                                                                                                                                                                                  | Required result                                                                                                                                                                                                                                     |
| -------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A. Full natural chronology                   | `N`                                                              | Start historical-AI games on 2000.1.1 as USA, JAP, CAN, FIN, SWE, and GER with Full isolated. Run USA through 2027.1.28, JAP through 2025.6.6, CAN through 2026.5.26, FIN through 2026.7.23, SWE through 2022.7.21, and GER through 2025.11.12.                                      | Every scheduled event arrives once, in source order, only after its predecessor. Historical routes resolve to the expected terminal ideas or flags. No event requires console delivery.                                                             |
| B. Outcomes Only                             | `N`, optional terminal `C` comparison                            | Start normal 2000.1.1 games as USA, JAP, CAN, and FIN. Cross representative milestones and the final monthly reconstruction boundary. A separate disposable `date 2027.2.1` fixture may compare the final state, but does not count as natural evidence.                             | No Corporate History popup. Durable historical flags and bounded variables appear within the monthly-driver window. No reward is replayed. Exactly one historical terminal idea exists. Repeated monthly ticks are stable.                          |
| C. Corporate History Off                     | `N`                                                              | Start 2000.1.1 with Off isolated and cross startup, yearly, and monthly milestones. Repeat once with the Independence preset.                                                                                                                                                        | No chain/subsystem-owned initialized, scheduled, resolved, reconstruction-complete, route, crisis, dashboard, adapter, or outcome state. No Corporate History popup. GPU and legacy U.S. OEM/storage are inert; native BRI and Linux remain usable. |
| D. Later start reconstruction                | `N`, then disposable `C`                                         | Start the normal 2017 bookmark as USA, JAP, CAN, FIN, SWE, and GER with Full isolated. Use separate late-date fixtures only to compare deterministic terminal state.                                                                                                                 | Elapsed history is reconstructed without popups or historical rewards. Only future visible milestones schedule. No duplicate elapsed event appears.                                                                                                 |
| E. Scheduled-event save/reload               | `N+reload`                                                       | Save before and after IBM `.12` (owner scheduler `+30`), Sony `.1` (bootstrap `+63`), Matrox `.1` (bootstrap `+75`), Nokia `.1` (2003 delay `288`), Ericsson `.1` (2001 delay `273`), and Siemens `.1` (2000 delay `120`). Reload both saves.                                        | One popup, one option log, one state/reward delta, no second queued copy, and no replay from the post-choice save.                                                                                                                                  |
| F. Legacy callback and reconstruction reload | `N+reload`, then `C`                                             | Save/reload around a naturally pending authored callback. For Nokia, include a save while a German or French receiver response is pending. In disposable saves, load or invoke a legacy queued `.90` sink, invoke each reconstruction effect twice, reload, and invoke it once more. | Legacy callbacks show no popup and create no second schedule. Receiver callbacks advance once. Flags, variables, terminal ideas, and economic values are identical after the first and later reconstruction calls.                                  |
| G. Terminal/capstone                         | `N+reload`, branch `C` saves                                     | Save before and after Sony `.14`, Matrox `.10`, Nokia capstone resolution, Ericsson `.5`, Siemens `.6`, IBM's 2026 capstone, and IBM's later 2027 reconstruction-complete boundary. Fork clean pre-capstone saves for the selectable alternatives.                                   | Exactly one mutually exclusive terminal idea or flag, one terminal marker, and no requeue after reload. IBM's capstone-resolved and reconstruction-complete dates remain distinct.                                                                  |
| H. Collapsed and absent countries            | Natural where possible; destructive `C` only in disposable saves | Before a naturally due event, set `collapsed_nation`, cross the due date, clear it, and observe recovery. In disposable saves, remove SWE before a Sony dependency, FIN before a Siemens dependency, and GER or FRA before Nokia receiver milestones.                                | Collapsed actors receive no popup or economic work. Recovery occurs once without reward replay. Missing countries cause no invalid scope, stuck pending marker, duplicate payment, or foreign-state write.                                          |
| I. Representative counterfactuals            | `C`, preferably forked natural pre-choice saves                  | Exercise Sony Open/Cell/Hardware outcomes; Matrox domestic-core success and failure plus four capstones; one nonhistorical IBM capstone; Nokia Open Mobile and fallback; Ericsson retained/full-control alternatives; Siemens with Nokia wholly owned versus exited.                 | Correct option availability, route flags, variables, downstream text, and exactly one terminal outcome. A forced event closes branch/payload/UI checks only.                                                                                        |
| J. `error.log`                               | Every `N` and `C` run                                            | Archive or clear logs before each run. Retain fresh `error.log` and `game.log`, and compare them with an unmodified-launch baseline.                                                                                                                                                 | No new feature-specific parse, scope, trigger, effect, localisation, sprite, texture, or modifier error. Separate unrelated baseline errors rather than omitting them.                                                                              |
| K. UI/GFX/localisation                       | `C` presentation fixtures plus natural screenshots               | Render IBM `.12`; Sony `.1/.14`; Matrox `.1/.2/.10/.11`; Nokia `.1/.14`; Ericsson `.1/.5`; Siemens `.1/.6`; terminal ideas; and the USA dashboard. Restart before final Matrox captures.                                                                                             | No raw key, blank or mis-cropped image, unreadable conditional description, tooltip mismatch, truncation, invalid color code, or stacked terminal idea.                                                                                             |

# Priority Chain Ledger

| Issue           | Country and horizon     | Events                                              | Historical terminal                                                                                              | State to inspect                                                                                                                          |
| --------------- | ----------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| #25 IBM         | USA, through 2027.1.28  | `USA_ibm_events.1-.49`, `.90`; prehistory `.12-.16` | `USA_ibm_open_hybrid_flywheel`; `USA_ibm_capstone_resolved`, then `USA_ibm_reconstruct_complete` after 2027.1.27 | Five `USA_oem_*` compute axes and five `USA_ibm_faction_*` variables; exactly one of six terminal ideas                                   |
| #24 Sony        | JAP, through 2025.6.6   | `JAP_sony_events.1-.14`, `.90`                      | `JAP_sony_one_sony_ecosystem`; `JAP_sony_reconstruct_complete`                                                   | Sony route flags, final idea, and Ericsson handset-state dependency                                                                       |
| #26/#112 Matrox | CAN, through 2026.5.26  | `CAN_matrox_events.1-.11`, `.90`                    | `CAN_matrox_certified_visual_systems`; `CAN_matrox_reconstruct_complete`                                         | Professional/Parhelia/certification, ownership, driver, machine-vision, QNX/ATI dependency, domestic-core success or architecture failure |
| #27 Nokia       | FIN, through 2026.7.23  | `FIN_nokia_events.0-.14`, `.90-.116`                | `FIN_nokia_trusted_network_state`; `FIN_nokia_capstone_resolved`, then `FIN_nokia_reconstruct_complete`          | Seven bounded Nokia variables; German and French receiver callbacks; exactly one of six terminal ideas                                    |
| #27 Ericsson    | SWE, through 2022.7.21  | `SWE_ericsson_events.1-.5`, `.90`                   | `SWE_ericsson_vonage_platform`; `SWE_ericsson_reconstruct_complete`                                              | Handset exit/retention state and one terminal route                                                                                       |
| #27 Siemens     | GER, through 2025.11.12 | `GER_siemens_events.1-.6`                           | Historical integrated/network/Healthineers/Energy route; `GER_siemens_reconstruct_complete`                      | Nokia wholly-owned/exited dependency and one-time synchronous reconstruction                                                              |

Issue #28 is broader than issues #24-#27. Its complete smoke also covers Apple, Dell, Google, HP, AIG, NVIDIA, Nintendo, TSMC, Texas Instruments, Micron, Motorola, Foxconn, every other owner chain, and all four schema-v6 independent subsystems declared in `tools/corporate_history_contract.json`.

# State Assertions

## IBM

Inspect these bounded variables before the capstone, immediately after it, after the 2027 reconstruction-complete boundary, and after reload:

- `USA_oem_open_standards`
- `USA_oem_vertical_integration`
- `USA_oem_supply_resilience`
- `USA_oem_security_control`
- `USA_oem_national_compute_stack`
- `USA_ibm_faction_systems`
- `USA_ibm_faction_services`
- `USA_ibm_faction_open_platform`
- `USA_ibm_faction_financial`
- `USA_ibm_faction_research`

For the canonical historical reconstruction while USA owns North Carolina (state 790), the terminal values are:

| Variable                         | Expected | Bounds |
| -------------------------------- | -------: | -----: |
| `USA_oem_open_standards`         |       10 |   0-10 |
| `USA_oem_vertical_integration`   |        0 |   0-10 |
| `USA_oem_supply_resilience`      |        2 |   0-10 |
| `USA_oem_security_control`       |       10 |   0-10 |
| `USA_oem_national_compute_stack` |       10 |   0-10 |
| `USA_ibm_faction_systems`        |        9 |   0-10 |
| `USA_ibm_faction_services`       |       10 |   0-10 |
| `USA_ibm_faction_open_platform`  |       10 |   0-10 |
| `USA_ibm_faction_financial`      |       10 |   0-10 |
| `USA_ibm_faction_research`       |       10 |   0-10 |

If USA does not own state 790 when event 17 first resolves, `USA_ibm_faction_systems` is 10 and `USA_ibm_lenovo_cfius_safeguards` replaces `USA_ibm_rtp_transition_managed`; the other terminal values are unchanged.

Historical reconstruction must produce `USA_ibm_open_hybrid_flywheel`. The alternatives are `USA_ibm_american_systems_ministry`, `USA_ibm_big_blue_intact`, `USA_ibm_cloud_without_iron`, `USA_ibm_fortress_z`, and `USA_ibm_stack_in_name_only`. Event `.11` is the failure notification and must not appear in a healthy stack.

## Sony

Historical reconstruction must produce `JAP_sony_one_sony_ecosystem`. Counterfactual terminal saves must separately produce:

- `JAP_sony_open_digital_commonwealth`
- `JAP_sony_cell_sovereign_compute`
- `JAP_sony_hardware_federation`

Remove SWE only in a disposable save. Sony must retain a valid fallback when Ericsson's handset-state owner is absent.

## Matrox

Historical reconstruction must produce `CAN_matrox_certified_visual_systems`. Counterfactual terminal saves must separately produce:

- `CAN_matrox_sovereign_visual_compute`
- `CAN_matrox_secure_vision_stack`
- `CAN_matrox_open_graphics_commonwealth`

For the domestic-core branch, choose `.8.b` with the complete predicate and expect `CAN_matrox_domestic_gpu_core` with no `.11`. From a clean save lacking the complete predicate, choose `.8.b` and expect `.11` after one day, `CAN_matrox_architecture_failed`, and no domestic core.

## Nokia, Ericsson, and Siemens

Inspect Nokia's seven bounded variables:

- `FIN_nokia_device_position`
- `FIN_nokia_platform_autonomy`
- `FIN_nokia_network_capability`
- `FIN_nokia_standards_leverage`
- `FIN_nokia_platform_debt_stage`
- `FIN_nokia_service_platform_stage`
- `FIN_nokia_nsn_integration_stage`

The canonical historical terminal values are:

| Variable                           | Expected | Bounds |
| ---------------------------------- | -------: | -----: |
| `FIN_nokia_device_position`        |        1 |   0-10 |
| `FIN_nokia_platform_autonomy`      |        4 |   0-10 |
| `FIN_nokia_network_capability`     |        9 |   0-10 |
| `FIN_nokia_standards_leverage`     |        9 |   0-10 |
| `FIN_nokia_platform_debt_stage`    |        3 |    0-3 |
| `FIN_nokia_service_platform_stage` |        1 |    0-4 |
| `FIN_nokia_nsn_integration_stage`  |        4 |    0-4 |

Historical Nokia reconstruction must produce `FIN_nokia_trusted_network_state`. Receiver tests must cover `GER_nokia_response_events.1/.2/.90/.91` and `FRA_nokia_response_events.1`.

Historical Ericsson state must include `SWE_ericsson_exited_handsets` and terminate at `SWE_ericsson_vonage_platform`. Test retained/full-control handset alternatives from clean saves.

Historical Siemens reconstruction must retain its integrated conglomerate, networks strategy, listed Healthineers, and spun-off Energy states. Removing FIN must not invalidate Siemens reconstruction.

# Targeted Console Fixtures

Use only disposable saves. These commands do not prove natural scheduling:

```text
tag USA
event USA_ibm_events.12 USA
effect USA_ibm_reconstruct_history = yes

tag JAP
event JAP_sony_events.14 JAP
effect JAP_sony_reconstruct_history = yes

tag CAN
event CAN_matrox_events.1 CAN
event CAN_matrox_events.2 CAN
event CAN_matrox_events.8 CAN
event CAN_matrox_events.10 CAN
effect CAN_matrox_reconstruct_history = yes

tag FIN
effect FIN_nokia_reconstruct_history = yes

tag SWE
effect SWE_ericsson_reconstruct_history = yes

tag GER
effect GER_siemens_reconstruct_history = yes

effect set_country_flag = collapsed_nation
effect clr_country_flag = collapsed_nation
date 2027.2.1
reloadinterface
```

## Marquee Artwork Check

Static registration is necessary but not sufficient. Verify:

| Event                   | Expected sprite                   |
| ----------------------- | --------------------------------- |
| `USA_ibm_events.12`     | `GFX_ibm_consulting_boardroom`    |
| `JAP_sony_events.1`     | `GFX_JAP_sony_playstation_2`      |
| `JAP_sony_events.14`    | `GFX_JAP_sony_playstation_5`      |
| `CAN_matrox_events.1`   | `GFX_matrox_g400`                 |
| `CAN_matrox_events.2`   | `GFX_matrox_parhelia`             |
| `CAN_matrox_events.10`  | `GFX_matrox_qid`                  |
| `CAN_matrox_events.11`  | `GFX_matrox_parhelia`             |
| `FIN_nokia_events.1`    | `GFX_nokia_3310`                  |
| `FIN_nokia_events.14`   | `GFX_nokia_headquarters`          |
| `SWE_ericsson_events.1` | `GFX_ericsson_sony_joint_venture` |
| `SWE_ericsson_events.5` | `GFX_ericsson_kista`              |
| `GER_siemens_events.1`  | `GFX_siemens_himbeerpalast`       |
| `GER_siemens_events.6`  | `GFX_siemens_somatom_ct`          |

Run `reloadinterface` as an exploratory check if supported, then fully restart the game before the acceptance screenshots. Capture the events, the four terminal-idea families that exist for IBM, Sony, Matrox, and Nokia, and the dedicated USA Corporate Systems dashboard art at the common test resolution and UI scale. Ericsson and Siemens expose terminal state through flags rather than idea objects, so their visual acceptance is limited to the event pictures above. Inspect the fresh `error.log` for sprite or texture errors.

The remaining non-marquee generic Corporate History event pictures are intentional RC scope. This release replaces the agreed IBM, Sony, Matrox, Nokia, Ericsson, and Siemens milestones, the applicable IBM, Sony, Matrox, and Nokia terminal ideas, and the dashboard; a broad replacement of all generic references is deferred rather than treated as a release blocker.

# Recovered Evidence Inventory

Every runtime artefact produced for this project before the release candidate was located and catalogued. The corpus is 122 files preserved in the local-only annotated tags `archive/matrox-runtime-evidence` (`c484be18d8f5ef6e995655b97a2f9a3c4f79c9cc`) and `archive/main-premerge-evidence` (`f5111571bd09bd5ace083736bf5f2da31f28cfd2`) under the path prefix `runtime_evidence/`. Commit `0603a1d28f` removed that directory from the tracked tree when the release candidate was prepared, so the tags are the only remaining source.

Retrieve any file with `git show <tag>:runtime_evidence/<path>`, or extract the whole corpus with `git archive archive/matrox-runtime-evidence runtime_evidence | tar -x -C <destination>`.

**Preservation warning.** Neither archive tag exists on `origin`. Three distinct `.hoi4` saves in the corpus are 145 MB, 145 MB, and 153 MB, so the tags cannot be pushed to GitHub as they stand. The 118 non-save files total 19.4 MB and would push cleanly; the saves need an off-repository archive.

| Evidence ID | Tested SHA   | Country | Mode                  | Start / range         | Class           | System                                       | Result            |
| ----------- | ------------ | ------- | --------------------- | --------------------- | --------------- | -------------------------------------------- | ----------------- |
| E1          | `680d24909e` | JAP     | Full                  | 2000.1.1 to 2000.4.12 | `N`             | Sony, Matrox, IBM, Israel, USA legacy OEM    | PASS with defect  |
| E2          | `3dc86a2c31` | JAP     | Full                  | 2000.1.1 to 2000.3.11 | `N` + `C`       | Sony `.1`, Nintendo `.1`, `gpu_development.2` | PASS with defect  |
| E3          | `9370598428` | JAP     | Full                  | 2000.1.6 paused       | `C`             | IBM `.12`, Matrox `.1`, Ericsson `.1`        | PASS              |
| E4          | `9370598428` | JAP     | Full                  | 2000.1.17             | `C`             | Sony `.1` repaired artwork and option payload | PASS             |
| E5          | `f344f9a37f` | USA     | Full / Outcomes / Off | 2000.1.1              | `N`, `N+reload` | Corporate Systems dashboard, mode gates      | PASS after repair |
| E6          | `6176ab485a` | USA     | Full / Outcomes / Off | 2000.1.1 to 2000.2.19 | `N`, `N+reload` | Economic bridge tiers, tier repair, monthly  | PASS              |
| E7          | `cd9b14b5b3` | USA     | Full                  | 2000.1.17             | `C`             | Four Corporate Systems policies and costs    | PASS              |
| E8          | `bf6e8496db` | CAN     | Full / Outcomes / Off | 2026.9 to 2026.12     | `N`             | ATI/AMD dashboard, capstone, Off suppression | PASS              |
| E9          | `d27eb699c9` | USA     | Full                  | 2000.1.1              | `N`             | Baseline dashboard, tooltips, read-only rows | PASS              |
| E10         | `680d24909e` | n/a     | n/a                   | menu only             | `S`             | Load-time `error.log` and `system.log`       | PASS with defect  |

Evidence files, by ID and path under `runtime_evidence/`:

| ID  | Files                                                                                                                                                                                                                       |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1  | `issue-driven-release-sweep/680d.../issue-24/logs/natural-full-game-after-ps2-auto-option-2000-04-12.log`; `.../issue-24/saves/acceptance_680d2490_JAP_full_2000_01_01_natural.hoi4`; `.../issue-24/screenshots/natural-full-ps2-event-2000-03-09-generic-computer.jpg` |
| E2  | `current-main-smoke-3dc86a2/2026-08-03-japan-full.md`                                                                                                                                                                        |
| E3  | `issue-driven-release-sweep/9370.../fixture-smoke-results.md`                                                                                                                                                                |
| E4  | `.../9370.../issue-104/screenshots/fixture-driven-ps2-event-repaired-art-2000-01-17.jpg`; `.../issue-104/logs/fixture-driven-game-after-ps2-option-a-2000-01-17.log`; `.../issue-104/saves/acceptance_93705984_JAP_ps2_fixture_option_a.hoi4` |
| E5  | `corporate-systems-campaign/phase0-pr96/f344.../runtime_results.md`; screenshots `02` to `08`; `logs/01-load-blocker-error.log`; `logs/02-clean-repaired-load-error.log`                                                      |
| E6  | `corporate-systems-campaign/phase-1/working-tree/runtime-results.md`; screenshots `02` to `09`                                                                                                                               |
| E7  | `corporate-systems-campaign/phase-2/working-tree/runtime-results.md`; `screenshots/01-policy-list-and-rename.jpg`                                                                                                            |
| E8  | `corporate-systems-campaign/phase-3/working-tree/runtime-results.md`; screenshots `01`, `02`                                                                                                                                 |
| E9  | `corporate-systems-campaign/baseline/d27e.../baseline_results.md`; screenshots `01` to `03`; `environment.txt`                                                                                                               |
| E10 | `issue-driven-release-sweep/680d.../runtime/logs/menu-error.log`; `.../runtime/logs/menu-system.log`; `.../runtime/screenshots/issue-24-menu-99ba.jpg`; `.../runtime/menu-launch.md`                                          |

Runtime environment for E1, E3, E4, and E10: Hearts of Iron IV Operation Postern `v1.19.2.0.a729`, modded checksum `99ba`, one enabled descriptor pointing at `G:/Millennium-Dawn-OEM-acceptance-20260731`. E2 recorded checksum `3a41`. E5 to E9 ran on the same HOI4 build with a `G:/Millennium-Dawn-OEM` descriptor at 3440x1440, UI scale 1.0, DirectX 11.

## Selected hashes

| Artefact                                                          | SHA-256                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| E1 `game.log`                                                     | `792166e65f4d7154b77ac0cb4d3c72fd0bc3fa2e675c505e311443e27aadc132` |
| E1 save, the same file also filed under E4 as the pre-popup save  | `bc458f178f03b7ae39bc7a5d1e45f50e21c448b25622ba8182193522b5da5967` |
| E1 PS2 popup screenshot, pre-repair generic art                   | `2767fb85f6b383acb17655f717759b82936d70aa2c507d4970c711da81d7d5c9` |
| E4 repaired-art screenshot                                        | `a16412689069e55c0ac906d613d6ae91dedb1fe674c4869b960479e53de4b2ca` |
| E4 `game.log`                                                     | `1ca012a1bd55a0ea33fef7ea879d9316233a1690a28c7a83a7437b8ec2f991cf` |
| E10 `error.log`                                                   | `6905f84cc82f335a62e29524fc87f34736f1b02a8a78b61b00633e6cd974708d` |
| E10 `system.log`                                                  | `840d5ea2835b7a5609b016c10a0357e708a0bffc0cc1fd8c7a129cf652451033` |
| Pre-fixture debug `error.log` at `9370598428`                     | `ceec57cc5804585c0a11e38382a94133b84a38aa8545a91e952976197bca08b0` |

## Events observed naturally

E1 `game.log` records these OEM option executions in an unpaused game with no `event`, `effect`, or `date` command:

| Date       | Country       | Log line                         |
| ---------- | ------------- | -------------------------------- |
| 2000.02.01 | United States | `USA_ibm_events.12.a executed`   |
| 2000.03.02 | Israel        | `ISR_oem_events.1.b executed`    |
| 2000.03.17 | Canada        | `CAN_matrox_events.1.a executed` |
| 2000.03.18 | Japan         | `JAP_sony_events.1.a executed`   |
| 2000.04.01 | United States | `USA_oem_events.13.b executed`   |
| 2000.04.05 | Israel        | `ISR_oem_events.6.a executed`    |

E2 separately observed `JAP_sony_events.1` rendering on 2000.03.06, with the option applying its displayed `-10` political power exactly once.

# Evidence Validity Against This Candidate

Validity was decided by comparing the blob of every gameplay file each test exercised, at its tested SHA, against the same path at head `2d3de527d7`.

| Tested SHA   | Files identical to RC head | Files changed by RC | Classification                                        |
| ------------ | -------------------------: | ------------------: | ----------------------------------------------------- |
| `3dc86a2c31` |           1, PS2 art only  |                  13 | PARTIALLY VALID for PS2 artwork, SUPERSEDED otherwise |
| `680d24909e` |                          0 |                  13 | SUPERSEDED                                            |
| `9370598428` |           1, PS2 art only  |                  13 | PARTIALLY VALID for PS2 artwork, SUPERSEDED otherwise |
| `f344f9a37f` |                          0 |                  12 | SUPERSEDED                                            |
| `6176ab485a` |                          0 |                  12 | SUPERSEDED                                            |
| `cd9b14b5b3` |                          0 |                  12 | SUPERSEDED                                            |
| `bf6e8496db` |                          0 |                  13 | SUPERSEDED                                            |
| `d27eb699c9` |                          0 |                  12 | SUPERSEDED                                            |

## Why the older evidence is superseded rather than merely old

The candidate did not simply move past those commits. It replaced the mechanism those tests measured:

- `common/on_actions/01_oem_corporate_history_on_actions.txt` is **deleted**. That file was the single 662-line `on_daily_ABK` host holding every yearly dispatch block from 2000 to 2026. Every naturally observed delivery in E1 and E2 was scheduled by it.
- `common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt` is **new**, 611 lines. Yearly dispatch is now per-country, gated to a January window, and watermarked by `corporate_history_last_dispatched_year`.
- `common/scripted_effects/00_corporate_history_midyear_recovery_effects.txt` is **new**, 3,718 lines. Date-based catch-up recovery did not exist when any prior run was made.
- `common/scripted_effects/00_corporate_history_effects.txt` and `00_corporate_history_dispatch_effects.txt` changed by 439 and 318 lines.
- Every visible OEM event gained `corporate_history_full_enabled = yes` in its trigger, so mode isolation is now enforced at a different layer than the one E5 to E9 tested.

## What does survive

- **PS2 artwork.** `gfx/event_pictures/asia/japan - JAP/JAP_sony_playstation_2.dds` is blob `32ad6f857ede3dfac0198d3975c05a33ba159be9` at the repair commit, at `main`, and at the candidate head. The sprite registration and the `picture = GFX_JAP_sony_playstation_2` reference are unchanged. E4 therefore remains DIRECT evidence for that one asset, and issue #104 is correctly closed.
- **GPU trigger repair.** E1 and E10 both isolated the only OEM-caused entry in the load-time `error.log`: `Invalid trigger 'stability'` at 12 sites in `events/00_gpu_development.txt`. Commit `3e616d76ce` replaced them with `has_stability < 0.5`. The candidate has 12 `has_stability` sites and zero bare `stability` triggers, so the defect is repaired in source. A fresh `error.log` is still required because the candidate modified that file again.
- **Baseline error separation.** The archived logs establish that the remaining load-time errors belong to inherited Millennium Dawn and vanilla DLC content, chiefly `common/dynamic_modifiers/*` and `common/scripted_guis/02_conditional_peace_deals_scripted_gui.txt`, or to unrelated third-party Workshop descriptors. That separation carries forward as the baseline to diff against.

# Runtime Defects Found and Their Repair State

| Issue | Defect                                                              | Found at          | Repair                | Repaired | Retested           | In candidate        |
| ----- | ------------------------------------------------------------------- | ----------------- | --------------------- | -------- | ------------------ | ------------------- |
| #104  | Sony PS2 launch event rendered generic computer artwork             | `680d24909e`, E1  | `11cdddf471`, PR #105 | Yes      | Yes, E4 fixture    | Yes, byte-identical |
| #112  | Matrox events rendered generic computer artwork                     | `680d24909e`, E1  | source fix on `main`  | Yes      | No                 | Yes, unrendered     |
| n/a   | `Invalid trigger 'stability'` at 12 sites in `00_gpu_development.txt` | `680d24909e`, E10 | `3e616d76ce`          | Yes      | No                 | Yes                 |
| n/a   | `has_start_date = 2000.1.1` rejected at load                        | PR #96 branch     | in PR #96             | Yes      | Yes, E5 clean load | Yes                 |
| n/a   | Malformed economic tier membership not repaired                     | PR #97 branch     | in PR #97             | Yes      | Yes, E6            | Yes                 |
| #111  | `gpu_development.2` used a generic laptop photograph                | `3dc86a2c31`, E2  | not located           | Unknown  | No                 | Unresolved          |

Issue #111 could not be retrieved: the number does not resolve in `JasonBreen/Millennium-Dawn-OEM`. It is recorded in the E2 notes and on issue #24 as a presentation defect for `gpu_development.2`. It belongs to the same picture-selection family as #104 and #112 and is treated as deferred presentation polish rather than a functional blocker.

Two static review findings raised on this candidate remain open and land directly on acceptance layers that have no runtime evidence. They are listed here so the runs are designed to exercise them:

- A country carrying `collapsed_nation` for the whole of January never enters `corporate_history_monthly_dispatch`, so its January-only yearly window closes unused. Midyear recovery is wired at `00_corporate_history_monthly_dispatch_effects.txt:608` and covers milestones from 2001 onward by date, so the exposure is bounded, but that recovery path has never been executed. This is Layer H.
- `USA_oem_legacy_effects.txt:55` queues the event-5 follow-up without setting the event-4 pending marker that the same branch later reads, which a reviewer flagged as a possible double queue on a post-2015 start. This is Layer D.

# Remaining Acceptance Set

The eleven-layer matrix above is the full gate. The following is the smallest set of runs that closes it on this candidate. It is deliberately shorter than the accumulated checklists on issues #24 to #28 and #45, most of which are development regression coverage rather than release gates.

| Run | Setup                                                                                                                                     | Closes                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| R1  | Fresh load to the main menu, archive `error.log` and `system.log`, diff against the E10 baseline                                          | Layer J, plus the `has_stability` and new-sprite regressions |
| R2  | USA 2000.1.1, Full isolated, natural to at least 2001.2.1, saving either side of IBM `.12` and reloading both                             | Layers A and E, and the IBM entry conditions for Layer G     |
| R3  | JAP 2000.1.1, Full isolated, natural past Sony `.1`, with a save and reload while `.1` is queued but unanswered                           | Layers A and E on a second host, duplicate suppression       |
| R4  | CAN 2000.1.1, Full isolated, natural past Matrox `.1` and `.2`, screenshots at the common test resolution                                 | Layers A and K, closes #112                                  |
| R5  | USA 2000.1.1, Outcomes Only isolated, cross the first monthly reconstruction boundary twice                                               | Layer B                                                      |
| R6  | USA 2000.1.1, Off isolated, then one repeat with the Independence preset                                                                  | Layer C, including the new ISR, USA legacy, and GPU suppression |
| R7  | USA 2017 bookmark, Full isolated, one monthly pass, then save and reload                                                                  | Layers D and F, and the `USA_oem_legacy_effects.txt:55` concern |
| R8  | Disposable save: set `collapsed_nation` on a chain owner before its January window, cross into February, clear the flag, run to the next monthly pass | Layer H and the January-window concern            |
| R9  | Console fixtures for the 13 marquee sprites in the Marquee Artwork Check, after a full restart                                            | Layer K                                                      |
| R10 | Disposable forked saves for one counterfactual per priority chain                                                                         | Layer I                                                      |

R1 is cheap and should run first: it revalidates the only OEM error class ever observed and covers 12 sprite registrations that have never been loaded.

# Result Record

Ten evidence bundles are recorded in the Recovered Evidence Inventory above. None was captured on this candidate, so no row below is filled.

Record one row per run on the exact candidate head:

| Field                                  | Value |
| -------------------------------------- | ----- |
| Test ID / issue                        |       |
| Git commit and worktree status         |       |
| Deployed changed-file hashes           |       |
| HOI4 version and checksum              |       |
| Evidence class (`N`, `C`, `N+reload`)  |       |
| Country, start date, AI, and rules     |       |
| Save/reload checkpoints                |       |
| Events observed and option logs        |       |
| Flags and variables before/after       |       |
| Ideas and economic values before/after |       |
| Screenshots                            |       |
| `game.log` / `error.log` archive       |       |
| Pass, fail, or blocked                 |       |
| Notes and unrelated baseline errors    |       |

An issue remains open until its required natural, reload, log, and presentation rows pass on the exact release-candidate build.
