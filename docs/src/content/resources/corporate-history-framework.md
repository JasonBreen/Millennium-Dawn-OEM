---
title: Corporate History Framework
description: Millennium Dawn corporate-history chains - framework effects, game rule, start-date policy, tier budgets, and integration rules
---

The corporate-history framework powers the dated company chains (IBM, Sun/Microsoft, HP, Apple, NVIDIA, Google, Oracle, E3, Lenovo, Sony, Matrox, Nokia, TSMC, and, at dispatch level only, Siemens, Ericsson, and BlackBerry). It centralizes control flow, value bounds, and game-rule gating; each company binds its own names, dates, and deltas in thin wrapper effects.

The authoritative chain list is `tools/corporate_history_contract.json`, enforced by `tools/validation/validate_corporate_history_contract.py`. This page must match the manifest; the validator gates the manifest, not the prose.

# File Map

> **Location**: `common/scripted_effects/00_corporate_history_effects.txt` (core), `00_corporate_history_dispatch_effects.txt` (yearly dispatch), `common/scripted_triggers/MD_corporate_history_triggers.txt` (rule gates)

| Piece                                                                                                                        | File                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Primitives (`corporate_history_apply_delta`, `corporate_history_clamp_value`), startup driver, monthly Outcomes-Only drivers | `common/scripted_effects/00_corporate_history_effects.txt`                                                                                                                                                                                                                                                 |
| `<TAG>_corporate_trigger_year_<YYYY>` yearly dispatch (one effect per country per year)                                      | `common/scripted_effects/00_corporate_history_dispatch_effects.txt`                                                                                                                                                                                                                                        |
| Google/Oracle catch-up drivers (`USA_google_extension_catchup`, `USA_oracle_chain_catchup`)                                  | `common/scripted_effects/00_corporate_history_dispatch_effects.txt`                                                                                                                                                                                                                                        |
| Rule gates `corporate_history_full_enabled` / `corporate_history_outcomes_only_enabled`                                      | `common/scripted_triggers/MD_corporate_history_triggers.txt`                                                                                                                                                                                                                                               |
| Per-company wrappers (init/clamp/reconstruct/schedule/capstone)                                                              | `common/scripted_effects/USA_ibm_effects.txt`, `USA_apple_effects.txt`, `USA_microsoft_effects.txt`, `USA_nvidia_effects.txt`, `USA_e3_effects.txt`, `USA_google_effects.txt`, `CHI_lenovo_effects.txt`, `JAP_sony_effects.txt`, `CAN_matrox_effects.txt`, `FIN_nokia_effects.txt`, `TAI_tsmc_effects.txt` |
| Machine-readable chain manifest                                                                                              | `tools/corporate_history_contract.json`                                                                                                                                                                                                                                                                    |
| Game rule `rule_corporate_history`                                                                                           | `common/game_rules/00_game_rules.txt`                                                                                                                                                                                                                                                                      |

# Game Rule Semantics

`rule_corporate_history` has three options, fixed at game setup (no mid-game transitions):

- **Full** (default): story events, decision windows, and the IBM crisis engine run exactly as authored.
- **Outcomes Only**: no corporate story events fire. The historical path (flags, state variables, outcome ideas, and monotonic delivery stages) is applied silently by the per-company `*_reconstruct_history` effects, invoked at startup and then from per-country monthly drivers. Each milestone lands on the **first monthly tick after its historical date** (≤ ~31 days lag, the same order of slop as the yearly dispatcher's early-January day offsets). Lenovo's reconstruction terminates after its PC route, brand route, and System x route are resolved. The IBM crisis engine is Full-only (its events are popups), so no crisis ideas appear in this mode. HP, Google, Oracle, Siemens, Ericsson, and BlackBerry are suppressed without replacement (no reconstruction exists for them).
- **Off**: rule-gated dispatchers never run, so those chains create no story events, reconstructed state, or outcome ideas.

**Gating happens only at dispatcher level**: the startup driver, the `<TAG>_corporate_trigger_year_*` effects, the monthly drivers, and the `USA_ibm_monthly_crisis_checks` call site in `99_USA_on_actions.txt`. Never add rule checks inside individual events: an event that was never scheduled needs no gate, and per-event gates rot.

Two mechanisms are easy to confuse, and they are not interchangeable:

|                   | Visible catch-up (Full)                      | Silent reconstruction (Outcomes Only)             |
| ----------------- | -------------------------------------------- | ------------------------------------------------- |
| Applies to        | Google 16-20, Oracle 1-12                    | every chain with a `*_reconstruct_history` ladder |
| Effect            | queues the real event; the player answers it | sets flags/variables/ideas directly, no popup     |
| Outcome chosen by | the player (or AI `ai_chance`)               | the historical branch, hard-coded in the ladder   |
| Terminates on     | the chain's terminal outcome flags           | `<chain>_reconstruct_complete`                    |

Catch-up never runs in Outcomes Only or Off: it is called from the `corporate_history_full_enabled` arm of `USA_corporate_history_monthly_outcomes`, so both non-Full modes stay popup-free.

# Start-Date Policy (January-1 Invariant)

The yearly dispatcher (`on_monthly` → `trigger_year_[year]_events`) fires on the first monthly tick of each calendar year, and **the start year's own block never runs**; startup scheduling covers it. Every milestone `days = N` offset therefore assumes its clock starts on January 1 (bookmark start) or the early-January dispatch tick.

The framework handles start dates with a **hard guard, not day-of-year math**:

- A chain that has milestones in a potential start year ships a `*_schedule_current_year_events` effect whose blocks are guarded by the per-year window `NOT = { has_start_date < Y.1.1 }` + `has_start_date < Y.1.2` (i.e. they only queue events when the campaign starts **exactly on January 1 of that year**), keeping all offsets calendar-correct. `USA_apple_schedule_current_year_events` is the reference implementation.
- For any later start, the per-company `*_reconstruct_history` effects silently apply every milestone whose date has passed (each step is `date >` + marker-flag guarded, idempotent, and event-free).
- Non-January-1 starts are **deliberately not scheduled**: passed milestones reconstruct; the start year's remaining milestones are skipped rather than fired on wrong dates. MD ships a single 2000.1.1 bookmark, so this path is theoretical.

## Catch-up drivers (Google, Oracle)

Google and Oracle have no reconstruction ladder, so a missed milestone cannot be applied silently. Instead their chain steps are owned by a persistent monthly driver, `USA_google_extension_catchup` / `USA_oracle_chain_catchup`, called from the Full arm of `USA_corporate_history_monthly_outcomes` (which runs on `on_monthly_USA`). They are the **sole** scheduling owner of those event ids; the yearly dispatchers do not schedule them, because the yearly dispatchers stop at 2026 and a 2026+ start or a save first updated after 2025 would otherwise strand the chain permanently.

The two drivers cover different spans, and the reason is structural:

- **Google** owns events **16-20** only. Event 16's arm needs no predecessor (its guard is "no cables outcome yet"), so the extension seeds itself from any start date. Events 1-15 stay on the yearly dispatchers and are simply missed by a campaign that starts after their milestone year.
- **Oracle** owns the **whole chain, 1-12**. Every Oracle event requires its predecessor's `_resolved` flag, so the chain cannot be entered part-way: while events 1-7 sat on the yearly dispatchers, a campaign starting after 2005 never set `USA_oracle_event_1_resolved` and _nothing_ in the chain could ever fire, extension included. Event 1 has no predecessor, so moving the whole ladder onto the driver lets it seed itself.

Each ladder step is a single `else_if` arm gated on three things: the predecessor outcome flags, the step's own fire marker (`USA_<co>_event_<N>_resolved`, set in the event's `immediate`), and `date >` the last day before its milestone year. Within an arm:

- **first monthly tick of the milestone year** (`date < <Y>.2.1`): queue with the canonical `days = N` offset, reproducing the historical date exactly.
- **any later tick**: queue with `days = 5`, so a late start or an updated save walks the remaining steps one per monthly tick instead of dumping them at once.

A chain-level pending flag (`USA_google_extension_pending` / `USA_oracle_chain_pending`) is set when a step is queued and cleared in the queued event's `immediate`, so at most one event per chain is in flight. It is set as a timed flag (`days = 400`, longer than the largest canonical offset) so a step whose event never fires cannot deadlock the ladder.

Canonical offsets, all measured from January 1 of the listed year:

| Chain  | Event | Year | `days` |
| ------ | ----- | ---- | ------ |
| Google | `.16` | 2010 | 250    |
| Google | `.17` | 2016 | 350    |
| Google | `.18` | 2021 | 200    |
| Google | `.19` | 2023 | 150    |
| Google | `.20` | 2024 | 200    |
| Oracle | `.1`  | 2005 | 154    |
| Oracle | `.2`  | 2008 | 119    |
| Oracle | `.3`  | 2009 | 223    |
| Oracle | `.4`  | 2010 | 202    |
| Oracle | `.5`  | 2012 | 144    |
| Oracle | `.6`  | 2019 | 287    |
| Oracle | `.7`  | 2020 | 260    |
| Oracle | `.8`  | 2020 | 300    |
| Oracle | `.9`  | 2021 | 350    |
| Oracle | `.10` | 2022 | 150    |
| Oracle | `.11` | 2023 | 100    |
| Oracle | `.12` | 2024 | 150    |

Once a chain reaches its terminal outcome (a Google antitrust flag, or `USA_oracle_event_12_resolved`) no arm matches and the driver stops doing work; the outer `if` in the monthly driver skips both calls when both chains are terminal.

# Wrapper Contract

HOI4 cannot parameterize identifier names (variables, flags, ideas, event ids) without meta_effect renames, so the framework owns **control flow, bounds, and gates**, and each company binds its names in wrapper effects that contain data, not logic:

| Wrapper                                   | Shape                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<TAG>_<co>_initialize_state`             | flag-guarded `set_variable` defaults + trailing clamp call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `<TAG>_<co>_clamp_state`                  | per variable: `set_temp_variable = { corp_value = X }` → `corporate_history_clamp_value = yes` → `set_variable = { X = corp_value }`                                                                                                                                                                                                                                                                                                                                                                                                                |
| `<TAG>_<co>_reconstruct_history`          | date-ascending ladder; every step `date > D` + `NOT` on **all** sibling outcome markers; `add_ideas` steps guarded by `NOT has_idea` on all alternatives; no event fires; ends with silent capstone resolution where the chain has one, then sets `<TAG>_<co>_reconstruct_complete` once the final milestone date has passed (the monthly driver's only terminal check). A ladder can end _after_ its capstone (IBM's integrations run to 2027.6.1, past the 2026.6.2 capstone), so the completion date is the last step's date, not the capstone's |
| `<TAG>_<co>_events.90`                    | hidden, `fire_only_once` event whose immediate is a thin call to the reconstruct effect (IBM's also keeps its `date < 2000.2.1` prehistory-scheduling branch)                                                                                                                                                                                                                                                                                                                                                                                       |
| `<TAG>_<co>_schedule_current_year_events` | per-year Jan-1 window guard + `country_event` offsets (implemented for Apple, E3, Lenovo, NVIDIA, Nokia, and TSMC, matching `requires_current_year_scheduler` in the manifest)                                                                                                                                                                                                                                                                                                                                                                      |
| capstone family                           | `clear_capstone_outcome` (remove all competing ideas + flags) / `apply_*_capstone` (clear, add one idea, set outcome + resolved flags) / `resolve_capstone` (threshold ladder)                                                                                                                                                                                                                                                                                                                                                                      |

The primitives:

```hoiscript
set_temp_variable = { corp_value = USA_apple_ecosystem_control }
set_temp_variable = { corp_delta = 2 }
corporate_history_apply_delta = yes # adds, then clamps to the 0..10 band
set_variable = { USA_apple_ecosystem_control = corp_value }
```

`corporate_history_apply_delta` is the single owner of the 0..10 band; `corporate_history_clamp_value` is the delta-0 binding of it. Event options keep plain `add_to_variable` + `<TAG>_<co>_clamp_state`; do not rewrite option bodies onto the primitives.

AI weighting on event options follows the house pattern: `is_historical_focus_on` and `has_active_mission = bankruptcy_incoming_collapse` appear as **separate** `factor = 0` modifiers, never combined in one modifier block. (Existing chains vary in idiom, `base`+`add` vs `factor`, and keep their authored numbers; new chains should use separate `factor = 0` guards.)

# Interaction Policy

A chain may read **only its own flags and variables**, plus the cross-links declared in the table below. Cross-chain **writes** are forbidden except through the owning chain's scripted effects (the Sun/Microsoft → IBM write-through is the grandfathered exception). External reads require exact manifest declarations and a documented context here; transaction satellites may use those reads in event triggers and reconstruction, while flavor-only links stay in `ai_chance` / flavor triggers.

| Reader        | State read                                                                                                                                                                                                                                                                                                                                                                                                                         | Where                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Sun/Microsoft | IBM shared state `USA_oem_*`, `USA_ibm_faction_*` (write-through + `ai_chance` reads); calls `USA_ibm_initialize_state`/`USA_ibm_clamp_state`                                                                                                                                                                                                                                                                                      | `events/USA_sun_microsoft_events.txt`                                            |
| Apple         | IBM outcome flags `USA_ibm_watson_enterprise`, `USA_ibm_x86_divested`; Microsoft outcome flags `USA_microsoft_azure_*`, `USA_microsoft_cloud_*` (`ai_chance` only)                                                                                                                                                                                                                                                                 | `events/USA_apple_events.txt`                                                    |
| Lenovo        | IBM PC, CFIUS, x86, and transition-route flags; Motorola Mobility ownership (reconstruction, event triggers, and owner-effect handoffs)                                                                                                                                                                                                                                                                                            | `events/CHI_lenovo_events.txt`, `common/scripted_effects/CHI_lenovo_effects.txt` |
| NVIDIA        | GPU mirrors `USA_gpu_2007_cuda_*`, `USA_gpu_2012_alexnet_*`, `USA_gpu_2017_volta_*`, `USA_gpu_2020_shortage_*`, `USA_gpu_2022_hopper_*`, `USA_gpu_2024_*`; IBM state `USA_oem_open_standards`, `USA_oem_national_compute_stack`, `USA_ibm_outcome_open_hybrid`, `USA_ibm_outcome_systems_ministry`; TSMC flag `TAI_tsmc_advanced_packaging_expanded`; Nokia flag `FIN_nokia_nvidia_ai_ran_partnership` (`ai_chance` / flavor only) | `events/USA_nvidia_events.txt`                                                   |
| TSMC          | GPU mirrors `TAI_gpu_2000_*`, `TAI_gpu_2017_*`, `TAI_gpu_2020_*`, `TAI_gpu_2022_*`, `TAI_gpu_2024_*`; US CHIPS idea `USA_chips_act`; ASML group `HOL_asml_tsmc_group`; existing MIO variables `tai_tsmc_const_boost_var`, `tai_tsmc_prod_boost_var` (`ai_chance` only)                                                                                                                                                             | `events/TAI_tsmc_events.txt`                                                     |
| Nokia         | Receiver-owned GER flags `GER_nokia_nsn_jv_accepted`, `GER_nokia_nsn_jv_declined`, `GER_nokia_siemens_sale_accepted`, `GER_nokia_siemens_sale_declined`; FRA flags `FRA_nokia_alu_commitments_accepted`, `FRA_nokia_alu_commitments_enhanced`, `FRA_nokia_alu_transaction_blocked` (transaction callbacks only)                                                                                                                    | `events/FIN_nokia_events.txt`, `common/scripted_effects/FIN_nokia_effects.txt`   |
| Siemens       | Nokia NSN flags `FIN_nokia_siemens_networks_formed`, `FIN_nokia_networks_wholly_owned`, `FIN_nokia_exited_networks` (option triggers)                                                                                                                                                                                                                                                                                              | `events/GER_siemens_events.txt`                                                  |
| Sony          | GPU-chain flags `JAP_gpu_*` (capstone option triggers/`ai_chance`)                                                                                                                                                                                                                                                                                                                                                                 | `events/JAP_sony_events.txt`                                                     |
| Matrox        | BlackBerry/AI flags `CAN_blackberry_qnx_embedded`, `CAN_ai_public_research_network` (capstone option triggers)                                                                                                                                                                                                                                                                                                                     | `events/CAN_matrox_events.txt`                                                   |
| IBM (inbound) | US politics via `USA_ibm_*_administration` triggers, reads non-corporate state, allowed                                                                                                                                                                                                                                                                                                                                            | `common/scripted_triggers/MD_oem_triggers.txt`                                   |

`gpu_development`, `USA_oem_events`, BlackBerry, and Ericsson read **no** state of the covered chains, so gating the chains cannot strand them. The global GPU chain is independent of `rule_corporate_history`; its USA/TAI mirrors are inputs only. The three Nokia NSN flags are a stable API; Siemens depends on them; do not rename.

Nokia's `FIN_nokia_fwa_cpe_sale_confirmed` and `FIN_nokia_ai_ran_trial_confirmed` flags are future external confirmations. No dated event or reconstruction step sets them. In Full mode, the Finnish monthly driver dispatches `.106` or `.107` only after another system supplies the matching confirmation; it never infers a close, trial, or deployment date.

# Tier Budgets

New chains must fit one of three budgets. Anything larger needs maintainer sign-off.

- **Tier 1**: full chain, ~12-15 events, bounded 0..10 state variables, full capstone set (mutually exclusive outcome ideas + resolved flag), reconstruction, monthly-driver coverage.
- **Tier 2**: focused chain, 4-6 events, a single outcome idea, flag-based state, reconstruction.
- **Tier 3**: flavor, 1-2 events, no persistent state, no reconstruction needed.

Classification of the existing chains (chains predating the budgets are marked _grandfathered_; do not copy their scale):

| Chain                                               | Tier                | Notes                                                                                                                                                                                                           |
| --------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Apple (USA)                                         | 1                   | Reference implementation: 15 events, 7 variables, 5 outcome ideas, scheduler + reconstruction                                                                                                                   |
| NVIDIA (USA)                                        | 1                   | 12 visible events, 4 bounded variables, 5 outcome ideas, scheduler + reconstruction                                                                                                                             |
| E3 (USA)                                            | 1                   | 23 visible events, 10 variables incl. lifecycle stages, outcome ideas, scheduler + reconstruction                                                                                                               |
| Sony (JAP)                                          | 1                   | 15 events, flag-based state, 4 outcome ideas, player-choice capstone                                                                                                                                            |
| Matrox (CAN)                                        | 1                   | 12 events, flag-based state, 4 outcome ideas, player-choice capstone                                                                                                                                            |
| TSMC (TAI)                                          | 1                   | 15 visible events, 4 bounded variables, monotonic facility callbacks, 5 outcome ideas                                                                                                                           |
| Nokia (FIN)                                         | 1                   | 15 visible events, 4 bounded variables, staged GER/FRA transactions, 6 outcome ideas                                                                                                                            |
| IBM (USA)                                           | 1 _(grandfathered)_ | 50 events, 13 ideas, consequence schedulers, monthly crisis engine, over every budget                                                                                                                           |
| Sun/Microsoft (USA)                                 | 2 _(satellite)_     | 11 events, no own state or ideas; declared write-through into IBM state                                                                                                                                         |
| Lenovo (CHI)                                        | 2 _(satellite)_     | 8 events, flag-and-idea reconstruction, and IBM/Motorola owner-effect handoffs                                                                                                                                  |
| Google (USA)                                        | 2 _(grandfathered)_ | 20 events and 3 bounded variables, over the Tier-2 event budget; no outcome ideas and no reconstruction. Events 16-20 run on `USA_google_extension_catchup`; 1-15 stay on the yearly dispatchers                |
| Oracle (USA)                                        | 2 _(grandfathered)_ | 12 events, over the Tier-2 event budget; no outcome ideas and no reconstruction. Its state variables are undeclared in the manifest and therefore unclamped. The whole chain runs on `USA_oracle_chain_catchup` |
| HP (USA)                                            | 3 _(grandfathered)_ | 13 events but no persistent corporate state, no reconstruction; flavor economics only                                                                                                                           |
| Siemens (GER), Ericsson (SWE), BlackBerry (CAN/USA) | 2                   | Dispatch-moved + rule-gated only; internals not yet on the framework                                                                                                                                            |

# New-Chain Checklist

1. Wrapper effect file in `common/scripted_effects/` with the contract set above (init, clamp, reconstruct; capstone family for Tier 1; scheduler if the chain has potential start-year milestones).
2. Hidden `.90` event whose immediate is a thin reconstruct call.
3. Schedule entries added to the matching `<TAG>_corporate_trigger_year_<YYYY>` effects (create new ones as needed; never schedule inline in `00_yearly_effects.txt`), plus the startup entry in `corporate_history_on_startup` (both branches).
4. Monthly-driver coverage: add the reconstruct call to `<TAG>_corporate_history_monthly_outcomes`; the driver terminates on the chain's `*_reconstruct_complete` flag, so the ladder must set that flag at its true final milestone (create the `on_monthly_<TAG>` hook if the country has none).
5. Outcome ideas: `allowed = { original_tag = <TAG> }` **and** `allowed_civil_war = { always = yes }`.
6. Guard audit on every reconstruct step: `date >` gate; `NOT` on the step's own marker **and all sibling markers**; `add_ideas` guarded by `NOT has_idea` on all alternatives; no event fires inside reconstruction; single-child `NOT`s only.
7. Cross-links declared in the table above; localisation; changelog.

# TODO Register

- **Siemens / Ericsson / BlackBerry**: no reconstruction effects; Outcomes Only suppresses their events with no silent replacement. Ericsson's existing `SWE_ericsson_events.90` is the natural first extraction; Siemens and BlackBerry have no `.90` at all and need ladders authored from their option effects.
- **Google / Oracle**: no reconstruction effects either, so Outcomes Only suppresses them without replacement. In Full mode Oracle 1-12 is fully covered by its catch-up driver, but Google 1-15 is still yearly-dispatch only, so a campaign starting after one of those milestone years misses those events; only the 16-20 extension seeds itself. Google's per-year blocks schedule two events in some years, so moving them onto the one-arm-per-tick ladder would need a different shape.
- **Oracle state variables** (`USA_oracle_platform_scale`, `policy_access`, `integration_debt`, `ecosystem_openness`, `execution_discipline`, `infrastructure_depth`): mutated by every event, never initialized and never clamped, and undeclared in the manifest so the contract's clamp check skips them. Only `policy_access` and `integration_debt` are ever read, and only against one-sided thresholds, so the drift is currently inert. Declaring them in the manifest requires an `USA_oracle_initialize_state` / `USA_oracle_clamp_state` pair first.
- **Google extension variables** (`USA_google_ecosystem_openness`, `USA_google_policy_access`, `USA_google_platform_scale`): written by events 18-20, never read, never initialized, and not covered by `USA_google_clamp_state`. Either wire them into the clamp and the manifest or drop the writes.
- **`USA_google_events` namespace** is declared in two files (`USA_google_events.txt` and `USA_google_events_extension.txt`), the only split namespace in the repo. The contract's cross-chain ownership check only reads `events/<namespace>.txt`, so the extension file escapes that check. Merging the files would close the gap.
- **`USA_apple_events.90`** is defined but has no caller: `corporate_history_on_startup` calls `USA_apple_reconstruct_history` directly in both rule branches. Dead anchor, harmless, safe to delete.
- **Start-year schedulers** for IBM, Sun/Microsoft, Sony, and Matrox (Apple-pattern; inert while MD ships only the 2000.1.1 bookmark).
- **HP**: no persistent corporate state by design; decide whether to formalize as Tier 3 or extend to Tier 2 with an outcome idea.
- **Sun/Microsoft**: consider its own capstone/state if ever split from the IBM substrate; the current write-through is the declared exception.
