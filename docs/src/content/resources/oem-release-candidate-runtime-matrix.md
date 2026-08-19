---
title: OEM Release-Candidate Runtime Matrix
description: Exact-head acceptance plan for Corporate History chronology, reconstruction, save safety, presentation, and Matrox artwork
---

This matrix is the runtime gate for the OEM release candidate. Static validation does not close a runtime item. At the time this page was written, the synchronized release candidate had not completed this matrix.

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

The shared Corporate History startup marker may exist in Off mode. The Off assertion is the absence of chain-owned scheduling, resolution, reconstruction, route, crisis, and outcome state.

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

| Layer                                        | Evidence                                                         | Setup and execution                                                                                                                                                                                                                                                  | Required result                                                                                                                                                                                                                      |
| -------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A. Full natural chronology                   | `N`                                                              | Start historical-AI games on 2000.1.1 as USA, JAP, CAN, FIN, SWE, and GER with Full isolated. Run USA through 2027.1.28, JAP through 2025.6.6, CAN through 2026.5.26, FIN through 2026.7.23, SWE through 2022.7.21, and GER through 2025.11.12.                      | Every scheduled event arrives once, in source order, only after its predecessor. Historical routes resolve to the expected terminal ideas or flags. No event requires console delivery.                                              |
| B. Outcomes Only                             | `N`, optional terminal `C` comparison                            | Start normal 2000.1.1 games as USA, JAP, CAN, and FIN. Cross representative milestones and the final monthly reconstruction boundary. A separate disposable `date 2027.2.1` fixture may compare the final state, but does not count as natural evidence.             | No Corporate History popup. Durable historical flags and bounded variables appear within the monthly-driver window. No reward is replayed. Exactly one historical terminal idea exists. Repeated monthly ticks are stable.           |
| C. Corporate History Off                     | `N`                                                              | Start 2000.1.1 with Off isolated and cross startup, yearly, and monthly milestones. Repeat once with the Independence preset.                                                                                                                                        | No chain-owned initialized, scheduled, resolved, reconstruction-complete, route, crisis, or outcome state. No Corporate History popup. Linux still initializes in the Independence run. Rule-independent GPU history may still fire. |
| D. Later start reconstruction                | `N`, then disposable `C`                                         | Start the normal 2017 bookmark as USA, JAP, CAN, FIN, SWE, and GER with Full isolated. Use separate late-date fixtures only to compare deterministic terminal state.                                                                                                 | Elapsed history is reconstructed without popups or historical rewards. Only future visible milestones schedule. No duplicate elapsed event appears.                                                                                  |
| E. Scheduled-event save/reload               | `N+reload`                                                       | Save before and after IBM `.12` (`.90 +30`), Sony `.1` (startup `+63`), Matrox `.1` (startup `+75`), Nokia `.1` (2003 delay `288`), Ericsson `.1` (2001 delay `273`), and Siemens `.1` (2000 delay `120`). Reload both saves.                                        | One popup, one option log, one state/reward delta, no second queued copy, and no replay from the post-choice save.                                                                                                                   |
| F. Hidden callback and reconstruction reload | `N+reload`, then `C`                                             | Save/reload around hidden `.90` anchors on a 2017 start. For Nokia, include a save while a German or French receiver response is pending. In disposable saves, invoke each reconstruction effect twice, reload, and invoke it once more.                             | Hidden callbacks show no popup. Receiver callbacks advance once. Flags, variables, terminal ideas, and economic values are identical after the first and later reconstruction calls.                                                 |
| G. Terminal/capstone                         | `N+reload`, branch `C` saves                                     | Save before and after Sony `.14`, Matrox `.10`, Nokia capstone resolution, Ericsson `.5`, Siemens `.6`, IBM's 2026 capstone, and IBM's later 2027 reconstruction-complete boundary. Fork clean pre-capstone saves for the selectable alternatives.                   | Exactly one mutually exclusive terminal idea or flag, one terminal marker, and no requeue after reload. IBM's capstone-resolved and reconstruction-complete dates remain distinct.                                                   |
| H. Collapsed and absent countries            | Natural where possible; destructive `C` only in disposable saves | Before a naturally due event, set `collapsed_nation`, cross the due date, clear it, and observe recovery. In disposable saves, remove SWE before a Sony dependency, FIN before a Siemens dependency, and GER or FRA before Nokia receiver milestones.                | Collapsed actors receive no popup or economic work. Recovery occurs once without reward replay. Missing countries cause no invalid scope, stuck pending marker, duplicate payment, or foreign-state write.                           |
| I. Representative counterfactuals            | `C`, preferably forked natural pre-choice saves                  | Exercise Sony Open/Cell/Hardware outcomes; Matrox domestic-core success and failure plus four capstones; one nonhistorical IBM capstone; Nokia Open Mobile and fallback; Ericsson retained/full-control alternatives; Siemens with Nokia wholly owned versus exited. | Correct option availability, route flags, variables, downstream text, and exactly one terminal outcome. A forced event closes branch/payload/UI checks only.                                                                         |
| J. `error.log`                               | Every `N` and `C` run                                            | Archive or clear logs before each run. Retain fresh `error.log` and `game.log`, and compare them with an unmodified-launch baseline.                                                                                                                                 | No new feature-specific parse, scope, trigger, effect, localisation, sprite, texture, or modifier error. Separate unrelated baseline errors rather than omitting them.                                                               |
| K. UI/GFX/localisation                       | `C` presentation fixtures plus natural screenshots               | Render IBM `.12`; Sony `.1/.14`; Matrox `.1/.2/.10/.11`; Nokia `.1/.14`; Ericsson `.1/.5`; Siemens `.1/.6`; terminal ideas; and the USA dashboard. Restart before final Matrox captures.                                                                             | No raw key, blank or mis-cropped image, unreadable conditional description, tooltip mismatch, truncation, invalid color code, or stacked terminal idea.                                                                              |

# Priority Chain Ledger

| Issue           | Country and horizon     | Events                                              | Historical terminal                                                                                              | State to inspect                                                                                                                          |
| --------------- | ----------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| #25 IBM         | USA, through 2027.1.28  | `USA_ibm_events.1-.49`, `.90`; prehistory `.12-.16` | `USA_ibm_open_hybrid_flywheel`; `USA_ibm_capstone_resolved`, then `USA_ibm_reconstruct_complete` after 2027.1.27 | Five `USA_oem_*` compute axes and five `USA_ibm_faction_*` variables; exactly one of six terminal ideas                                   |
| #24 Sony        | JAP, through 2025.6.6   | `JAP_sony_events.1-.14`, `.90`                      | `JAP_sony_one_sony_ecosystem`; `JAP_sony_reconstruct_complete`                                                   | Sony route flags, final idea, and Ericsson handset-state dependency                                                                       |
| #26/#112 Matrox | CAN, through 2026.5.26  | `CAN_matrox_events.1-.11`, `.90`                    | `CAN_matrox_certified_visual_systems`; `CAN_matrox_reconstruct_complete`                                         | Professional/Parhelia/certification, ownership, driver, machine-vision, QNX/ATI dependency, domestic-core success or architecture failure |
| #27 Nokia       | FIN, through 2026.7.23  | `FIN_nokia_events.0-.14`, `.90-.116`                | `FIN_nokia_trusted_network_state`; `FIN_nokia_capstone_resolved`, then `FIN_nokia_reconstruct_complete`          | Seven bounded Nokia variables; German and French receiver callbacks; exactly one of six terminal ideas                                    |
| #27 Ericsson    | SWE, through 2022.7.21  | `SWE_ericsson_events.1-.5`, `.90`                   | `SWE_ericsson_vonage_platform`; `SWE_ericsson_reconstruct_complete`                                              | Handset exit/retention state and one terminal route                                                                                       |
| #27 Siemens     | GER, through 2025.11.12 | `GER_siemens_events.1-.6`                           | Historical integrated/network/Healthineers/Energy route; `GER_siemens_reconstruct_complete`                      | Nokia wholly-owned/exited dependency and one-time synchronous reconstruction                                                              |

Issue #28 is broader than issues #24-#27. Its complete smoke also covers Apple, Dell, Google, HP, AIG, NVIDIA, Nintendo, TSMC, Texas Instruments, Micron, Motorola, Foxconn, Israel, and every other chain declared in `tools/corporate_history_contract.json`.

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

## Matrox Artwork Check

Static registration is necessary but not sufficient. Verify:

| Event                  | Expected sprite       |
| ---------------------- | --------------------- |
| `CAN_matrox_events.1`  | `GFX_matrox_g400`     |
| `CAN_matrox_events.2`  | `GFX_matrox_parhelia` |
| `CAN_matrox_events.10` | `GFX_matrox_qid`      |
| `CAN_matrox_events.11` | `GFX_matrox_parhelia` |

Run `reloadinterface` as an exploratory check if supported, then fully restart the game before the acceptance screenshots. Capture both events at the common test resolution and UI scale and inspect the fresh `error.log` for sprite or texture errors.

# Result Record

Record one row per run:

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
