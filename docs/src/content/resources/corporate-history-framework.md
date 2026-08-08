---
title: Corporate History Framework
description: Millennium Dawn corporate-history chains - framework effects, game rule, start-date policy, tier budgets, and integration rules
---

The corporate-history framework powers the dated company chains (IBM, Sun/Microsoft, HP, Apple, NVIDIA, Dell, Google, Oracle, E3, Texas Instruments, Micron, Motorola, AIG, Lenovo, Huawei, Sony, Nintendo, ATI/AMD, Matrox, Nokia, France Corporate Systems, TSMC, Foxconn, and Russian Computing Sovereignty, plus Siemens, Ericsson, and BlackBerry at dispatch level only). France Corporate Systems combines Alcatel, STMicroelectronics, and France Télécom/Orange under one national state model. The framework centralizes control flow, value bounds, and game-rule gating; each company or national ecosystem binds its own names, dates, and deltas in thin wrapper effects.

The authoritative chain list is `tools/corporate_history_contract.json`, enforced by `tools/validation/validate_corporate_history_contract.py`. This page must match the manifest; the validator gates the manifest, not the prose.

# File Map

> **Location**: `common/scripted_effects/00_corporate_history_effects.txt` (core), `00_corporate_history_dispatch_effects.txt` (yearly dispatch), `common/scripted_triggers/MD_corporate_history_triggers.txt` (rule gates)

| Piece                                                                                                                        | File                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Primitives (`corporate_history_apply_delta`, `corporate_history_clamp_value`), startup driver, monthly Outcomes-Only drivers | `common/scripted_effects/00_corporate_history_effects.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `<TAG>_corporate_trigger_year_<YYYY>` yearly dispatch (one effect per country per year)                                      | `common/scripted_effects/00_corporate_history_dispatch_effects.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Google/Oracle catch-up drivers (`USA_google_extension_catchup`, `USA_oracle_chain_catchup`)                                  | `common/scripted_effects/00_corporate_history_dispatch_effects.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Rule gates `corporate_history_full_enabled` / `corporate_history_outcomes_only_enabled`                                      | `common/scripted_triggers/MD_corporate_history_triggers.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Per-company wrappers (init/clamp/reconstruct/schedule/capstone)                                                              | Per-chain files in `common/scripted_effects/`, including `FRA_corporate_systems_effects.txt`, `SOV_computing_sovereignty_effects.txt`; exact inventory is enforced by `tools/corporate_history_contract.json`                                                                                                                                                                                                                                                                                                                                                       |
| National economic bridge; chain-to-axis map: `.claude/docs/usa-oem-economic-bridge-map.md`                                   | `common/scripted_effects/USA_corporate_systems_effects.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| U.S. real-options economic layer, dynamic tiers, temporary programs, and reference simulator                                 | `common/scripted_effects/USA_oem_real_options_effects.txt`, `common/dynamic_modifiers/05_USA_oem_economic_dynamic_modifiers.txt`, `tools/analysis/simulate_oem_real_options.py`                                                                                                                                                                                                                                                                                                                                                                                     |
| Machine-readable chain manifest                                                                                              | `tools/corporate_history_contract.json`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Game rule `rule_corporate_history`                                                                                           | `common/game_rules/00_game_rules.txt`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

# National Real-Options Economy

The U.S. economic bridge delegates once to
`USA_oem_update_real_options_economy` after it rebuilds the effective compute
axes. That updater values the option to invest in national compute capacity,
then derives exercise readiness, innovation diffusion, industrial depth, and
infrastructure pressure. It assigns one member from each of four mutually
exclusive dynamic-modifier families and clears every output and modifier when
Corporate History is Off or the country is collapsed.

HOI4 has no confirmed logarithm, exponential, square-root, or normal-CDF
operator. The script therefore uses bounded arithmetic approximations. Variable
bounds, CDF constants, tier thresholds, and policy timings are declared under
the schema-v3 `economic_layers` section of
`tools/corporate_history_contract.json`. The strict corporate-history validator
checks ownership, clamps, bridge reachability, tier replacement, policy timing
and non-stacking, dashboard parity, and English localisation.
`tools/analysis/simulate_oem_real_options.py` compares the approximation against
Python's high-precision reference and provides named balance scenarios. Those
results are static evidence, not an in-game runtime test.

The four U.S. policies now add visible programs: 365 days for procurement and
security, and 730 days for capacity and consortium. They preserve their existing
Political Power, Treasury, and corporate-state effects. AI weights use reserve,
debt, interest, energy, labor, bankruptcy, and shared cadence guards.
The three automation and employment-outlook scores are dashboard placeholders
only; this layer does not alter employment laws.

Full derivation, tier, policy, AI, and smoke-test notes are maintained in
`.claude/docs/oem-real-options-economic-layer.md`.

# Game Rule Semantics

`rule_corporate_history` has three options, fixed at game setup (no mid-game transitions):

- **Full** (default): story events, decision windows, and the IBM crisis engine run exactly as authored.
- **Outcomes Only**: no corporate story events fire. The historical path (flags, state variables, outcome ideas, national technologies, and monotonic delivery stages) is applied silently by the per-chain `*_reconstruct_history` effects, invoked at startup and then from per-country monthly drivers. Each milestone lands on the **first monthly tick after its historical date** (≤ ~31 days lag, the same order of slop as the yearly dispatcher's early-January day offsets). Lenovo's reconstruction terminates after its PC route, brand route, and System x route are resolved. Huawei independently reconstructs its seven bounded axes and resolves Sovereign Full Stack after its 2026 terminal date. Russian Computing Sovereignty reconstructs its historical design, software, procurement, and foundry state but never grants advanced domestic HVM by date. France reconstructs the reward-free historical Alcatel, STMicroelectronics, Orange, and Nokia transaction state before resolving its national outcome. The IBM crisis engine is Full-only (its events are popups), so no crisis ideas appear in this mode. ATI/AMD reconstructs after the global GPU history so its compatibility bridge sees the generic acquisition choice. HP, Google, and Oracle reconstruct silently; Siemens, Ericsson, and BlackBerry are suppressed without replacement because they have no reconstruction effects.
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

Dell also preserves four older `USA_oem_events` interfaces. Full mode alone schedules `.13`, `.14`, and `.19`; its January-start scheduler covers `.14` and `.19` when the yearly block is skipped. The duplicated Perot event `.15` has no active caller. Dell reconstruction silently supplies the historical Round Rock, server-ecosystem, Perot-services, and 2015 firmware-policy state for Outcomes Only and late starts. The Perot path uses `USA_dell_apply_perot_services_path` / `USA_dell_apply_hardware_focus_path`, so both the Dell-owned outcome and the legacy consumer flag are set once. A queued `.15` from an old save calls the same wrappers and is blocked when either sibling path already exists.

The firmware-policy bridge uses `USA_oem_storage_firmware_2015_resolved` as its resolution marker and `USA_dell_storage_bridge_initialized` to distinguish a campaign that loaded Dell before the milestone from an older save first updated afterward. Both visible `.19` options set the resolution marker alongside their signed policy delta. When it is absent, a campaign initialized before the milestone or started in 2015 or later receives the historical `+1`; an older pre-2015 save first updated after the milestone sets only the markers, conservatively avoiding a second delta where `.19` may already have fired.

After 2026-06-15, the Full-mode USA monthly driver calls Dell's reward-free reconstruction only while `USA_dell_reconstruct_complete` is absent and the country is not collapsed. This recovers a lost or collapse-blocked capstone without adding a second visible caller.

# Start-Date Policy (January-1 Invariant)

The yearly dispatcher (`on_monthly` → `trigger_year_[year]_events`) fires on the first monthly tick of each calendar year, and **the start year's own block never runs**; startup scheduling covers it. Every milestone `days = N` offset therefore assumes its clock starts on January 1 (bookmark start) or the early-January dispatch tick.

The framework handles start dates with a **hard guard, not day-of-year math**:

- A chain that has milestones in a potential start year ships a `*_schedule_current_year_events` effect whose blocks are guarded by the per-year window `NOT = { has_start_date < Y.1.1 }` + `has_start_date < Y.1.2` (i.e. they only queue events when the campaign starts **exactly on January 1 of that year**), keeping all offsets calendar-correct. `USA_apple_schedule_current_year_events` is the reference implementation.
- For any later start, the per-company `*_reconstruct_history` effects silently apply every milestone whose date has passed (each step is `date >` + marker-flag guarded, idempotent, and event-free).
- Non-January-1 starts are **deliberately not scheduled**: passed milestones reconstruct; the start year's remaining milestones are skipped rather than fired on wrong dates. MD ships a single 2000.1.1 bookmark, so this path is theoretical.

## Per-event delivery markers (Nintendo)

Nintendo is the first chain that distinguishes _skipped_ from _lost_ milestones instead of relying on a single fire marker. Each visible event `.N` owns four flags:

| Marker                                     | Lifetime   | Set by                                                  | Cleared by                              |
| ------------------------------------------ | ---------- | ------------------------------------------------------- | --------------------------------------- |
| `JAP_nintendo_event_<N>_resolved`          | persistent | the event's `immediate`, reconstruction, silent advance | never                                   |
| `JAP_nintendo_event_<N>_delivery_expected` | persistent | whichever site queued the event                         | the event's `immediate`                 |
| `JAP_nintendo_event_<N>_pending`           | timed      | every queue site, `days = offset + 60`                  | the event's `immediate`, or flag expiry |
| `JAP_nintendo_event_<N>_startup_skipped`   | persistent | the scheduler's non-January startup pass                | `JAP_nintendo_advance_startup_skipped`  |

The pending flag is what stops a save/reload duplicating a queued popup; its lifetime deliberately outlives the delivery offset so that expiry _plus_ a surviving `delivery_expected` marker is unambiguous evidence of a lost delivery. A non-January start marks the rest of that year's milestones `startup_skipped` **without** `delivery_expected`, so the two recovery paths can never both claim the same milestone:

- `JAP_nintendo_recover_missing_events` (Full monthly driver) re-queues a lost delivery through `JAP_nintendo_schedule_current_year_events` in recovery mode.
- `JAP_nintendo_advance_startup_skipped` (Full monthly driver, and every Nintendo yearly dispatcher before its own check) silently applies the canonical option of a due skipped milestone so the next year's predecessor gate opens. It fires no event and grants no one-time reward.

Both helper effects are event-call-free; the yearly dispatcher and the current-year scheduler remain the only two direct callers of any Nintendo event, which is what `allow_yearly_scheduler_duplicates` permits.

## Chains gated on non-corporate MD state (AIG)

AIG is the first chain whose opening event depends on content outside the framework. `USA_aig_events.1` requires `has_global_flag = USA_great_financial_crisis` and one of the Lehman-outcome flags (`usa_nationalize_one` / `usa_bailout_one` / `usa_nothing_one`) set by `usa_economic_events.1` in `events/United States.txt`. That crisis is mean-time-to-happen driven, not date-locked, so the 2008 yearly dispatcher can reach 16 September before the gate is satisfiable. The Full arm of `USA_corporate_history_monthly_outcomes` therefore calls `USA_aig_schedule_current_year_events` in recovery mode between 2008-09-16 and 2010-01-01 until `USA_aig_event_1_resolved` is set. A queued opening owns `USA_aig_event_1_pending`, which prevents reconstruction from applying a second opening before the player answers it; reconstruction claims the milestone with `USA_aig_event_1_resolved` when it applies the historical opening instead. AIG reads the Lehman flags and never writes them; the Lehman chain has no knowledge of AIG.

Reconstruction is gated the same way: a campaign where the crisis never fired receives no reconstructed AIG state, but `USA_aig_reconstruct_complete` is still set unconditionally after the 2012 milestone so the monthly driver always terminates.

The reconstructed historical path (rescue with the equity stake, securities facility, November restructuring, Maiden Lane III at par, Maiden Lane II, forced disclosure, bonuses honoured, methodical divestment, full repayment, Treasury sale) lands on `USA_aig_moral_hazard_settlement`, not `USA_aig_taxpayer_vindication`. That is deliberate: the money came back with a profit, but the precedent it left did not. Vindication requires a cleaner run than history managed: the concession route untaken, disclosure published, bonuses clawed back, and both federal exposure and public anger held down.

## Catch-up drivers (Google, Oracle)

In Full mode, Google and Oracle use persistent monthly drivers, `USA_google_extension_catchup` / `USA_oracle_chain_catchup`, called from `USA_corporate_history_monthly_outcomes` (which runs on `on_monthly_USA`). They are the **sole** scheduling owner of those visible event ids; the yearly dispatchers do not schedule them, because the yearly dispatchers stop at 2026 and a 2026+ start or a save first updated after 2025 would otherwise strand the chain permanently. In Outcomes Only, their separate `USA_google_reconstruct_history` and `USA_oracle_reconstruct_history` effects apply dated historical state without firing events.

The two drivers cover different spans, and the reason is structural:

- **Google** owns events **16-20** only. Event 16's arm needs no predecessor (its guard is "no cables outcome yet"), so the extension seeds itself from any start date. Events 1-15 stay on the yearly dispatchers and are simply missed by a campaign that starts after their milestone year.
- **Oracle** owns the **whole chain, 1-12**. Event 1 seeds the ladder; events 3-4 run only when Sun was acquired by Oracle, while a terminal independent or Microsoft Sun path lets the ladder reconverge at event 5. Moving the whole ladder off the yearly dispatchers prevents late starts from missing event 1 and stranding every dependent event.

Each ladder step is a single `else_if` arm gated on three things: the predecessor outcome flags, the step's own fire marker (`USA_<co>_event_<N>_resolved`, set in the event's `immediate`), and `date >` the last day before its milestone year. Within an arm:

- **first monthly tick of the milestone year** (`date < <Y>.2.1`): queue with the canonical `days = N` offset, reproducing the historical date exactly.
- **same-year sequential milestone**: queue from the first monthly tick after its predecessor resolves, using the remaining delay to preserve the canonical date.
- **any later tick**: queue with `days = 5`, so a late start or an updated save walks the remaining steps one per monthly tick instead of dumping them at once.

A chain-level pending flag (`USA_google_extension_pending` / `USA_oracle_chain_pending`) is set when a step is queued and cleared in the queued event's `immediate`, so at most one event per chain is in flight. It is set as a timed flag (`days = 400`, longer than the largest canonical offset) so a step whose event never fires cannot deadlock the ladder.

Canonical dates and queue delays:

| Chain  | Event | Milestone  | Canonical queue       |
| ------ | ----- | ---------- | --------------------- |
| Google | `.16` | 2010-03-31 | January 1 + 89 days   |
| Google | `.17` | 2016-12-13 | January 1 + 347 days  |
| Google | `.18` | 2021-05-18 | January 1 + 137 days  |
| Google | `.19` | 2023-03-21 | January 1 + 79 days   |
| Google | `.20` | 2025-04-21 | January 1 + 110 days  |
| Oracle | `.1`  | 2003-06-09 | January 1 + 159 days  |
| Oracle | `.2`  | 2008-04-29 | January 1 + 119 days  |
| Oracle | `.3`  | 2010-01-27 | January 1 + 26 days   |
| Oracle | `.4`  | 2010-07-22 | February 1 + 171 days |
| Oracle | `.5`  | 2012-05-24 | January 1 + 144 days  |
| Oracle | `.6`  | 2019-10-15 | January 1 + 287 days  |
| Oracle | `.7`  | 2020-09-17 | January 1 + 260 days  |
| Oracle | `.8`  | 2020-10-27 | October 1 + 26 days   |
| Oracle | `.10` | 2020-12-11 | November 1 + 40 days  |
| Oracle | `.11` | 2021-05-25 | January 1 + 144 days  |
| Oracle | `.9`  | 2021-12-20 | June 1 + 202 days     |
| Oracle | `.12` | 2024-06-11 | January 1 + 162 days  |

Once a chain reaches its terminal outcome (a Google antitrust flag, or `USA_oracle_event_12_resolved`) no arm matches and the driver stops doing work; the outer `if` in the monthly driver skips both calls when both chains are terminal.

# Wrapper Contract

HOI4 cannot parameterize identifier names (variables, flags, ideas, event ids) without meta_effect renames, so the framework owns **control flow, bounds, and gates**, and each company binds its names in wrapper effects that contain data, not logic:

| Wrapper                                   | Shape                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<TAG>_<co>_initialize_state`             | flag-guarded `set_variable` defaults + trailing clamp call                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `<TAG>_<co>_clamp_state`                  | per variable: `set_temp_variable = { corp_value = X }` → `corporate_history_clamp_value = yes` → `set_variable = { X = corp_value }`                                                                                                                                                                                                                                                                                                                                                                                                                |
| `<TAG>_<co>_reconstruct_history`          | date-ascending ladder; every step `date > D` + `NOT` on **all** sibling outcome markers; `add_ideas` steps guarded by `NOT has_idea` on all alternatives; no event fires; ends with silent capstone resolution where the chain has one, then sets `<TAG>_<co>_reconstruct_complete` once the final milestone date has passed (the monthly driver's only terminal check). A ladder can end _after_ its capstone (IBM's integrations run to 2027.6.1, past the 2026.6.2 capstone), so the completion date is the last step's date, not the capstone's |
| `<TAG>_<co>_events.90`                    | optional hidden, `fire_only_once` event whose immediate is a thin call to the reconstruct effect; a chain reconstructed synchronously from startup does not need this anchor                                                                                                                                                                                                                                                                                                                                                                        |
| `<TAG>_<co>_schedule_current_year_events` | per-year Jan-1 window guard + `country_event` offsets (implemented for Apple, Dell, E3, Texas Instruments, Micron, Motorola, Lenovo, Huawei, NVIDIA, ATI/AMD, Nokia, TSMC, and Foxconn, matching `requires_current_year_scheduler` in the manifest)                                                                                                                                                                                                                                                                                                 |
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

For the reusable bounded-state pattern, capstone-priority rules, dashboard contract, and Huawei worked example, see [Seven-Axis Corporate Strategy Model](/dev-resources/corporate-history-seven-axis-design/).

# Interaction Policy

A chain may read **only its own flags and variables**, plus the cross-links declared in the table below. Cross-chain **writes** are forbidden except through the owning chain's scripted effects (the Sun/Microsoft → IBM write-through is the grandfathered exception). External reads require exact manifest declarations and a documented context here; transaction satellites may use those reads in event triggers and reconstruction, while flavor-only links stay in `ai_chance` / flavor triggers.

| Reader        | State read                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Where                                                                            |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Sun/Microsoft | IBM shared state `USA_oem_*`, `USA_ibm_faction_*` (write-through + `ai_chance` reads); calls `USA_ibm_initialize_state`/`USA_ibm_clamp_state`                                                                                                                                                                                                                                                                                                                                                                                                  | `events/USA_sun_microsoft_events.txt`                                            |
| Apple         | IBM outcome flags `USA_ibm_watson_enterprise`, `USA_ibm_x86_divested`; Microsoft outcome flags `USA_microsoft_azure_*`, `USA_microsoft_cloud_*` (`ai_chance` only)                                                                                                                                                                                                                                                                                                                                                                             | `events/USA_apple_events.txt`                                                    |
| Dell bridge   | Legacy `USA_oem_events.15` calls the Dell-owned Perot/hardware wrappers; Dell reconstruction mirrors those outcomes into the exact legacy consumer flags and preserves the 2015 firmware-policy step                                                                                                                                                                                                                                                                                                                                           | `events/United States.txt`, `common/scripted_effects/USA_dell_effects.txt`       |
| TI            | Micron event `.15` and the exact Lehi transaction flags; Micron may call TI event `.17` to hand off the transaction                                                                                                                                                                                                                                                                                                                                                                                                                            | `events/USA_ti_events.txt`, `events/USA_micron_events.txt`                       |
| Micron        | Calls TI event `.17`; the TI chain remains the owner of the receiving milestone                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `events/USA_micron_events.txt`                                                   |
| Motorola      | Lenovo's Mobility integration flag; calls `CHI_lenovo_update_motorola_mobility` and `CHI_lenovo_reward_motorola_mobility` so Lenovo retains ownership of its state                                                                                                                                                                                                                                                                                                                                                                             | `common/scripted_effects/USA_motorola_effects.txt`                               |
| Lenovo        | IBM PC, CFIUS, x86, and transition-route flags; Motorola Mobility ownership (reconstruction, event triggers, and owner-effect handoffs)                                                                                                                                                                                                                                                                                                                                                                                                        | `events/CHI_lenovo_events.txt`, `common/scripted_effects/CHI_lenovo_effects.txt` |
| IBM (Lenovo)  | Reads `CHI_lenovo_pc_path_chosen`, is the sole scheduler of `CHI_lenovo_events.1`, and calls `CHI_lenovo_schedule_cfius_followup` so Lenovo retains ownership of its transaction state                                                                                                                                                                                                                                                                                                                                                         | `common/scripted_effects/USA_ibm_effects.txt`                                    |
| Foxconn       | Apple supplier-diversification state for customer-strategy context                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `events/TAI_foxconn_events.txt`                                                  |
| NVIDIA        | GPU mirrors `USA_gpu_2007_cuda_*`, `USA_gpu_2012_alexnet_*`, `USA_gpu_2017_volta_*`, `USA_gpu_2020_shortage_*`, `USA_gpu_2022_hopper_*`, `USA_gpu_2024_*`; IBM state `USA_oem_open_standards`, `USA_oem_national_compute_stack`, `USA_ibm_outcome_open_hybrid`, `USA_ibm_outcome_systems_ministry`; TSMC flag `TAI_tsmc_advanced_packaging_expanded`; Nokia flag `FIN_nokia_nvidia_ai_ran_partnership`; initialized ATI/AMD MI300 and ROCm state (`ai_chance` / flavor only)                                                                   | `events/USA_nvidia_events.txt`                                                   |
| TSMC          | GPU mirrors `TAI_gpu_2000_*`, `TAI_gpu_2017_*`, `TAI_gpu_2020_*`, `TAI_gpu_2022_*`, `TAI_gpu_2024_*`; US CHIPS idea `USA_chips_act`; ASML group `HOL_asml_tsmc_group`; existing MIO variables `tai_tsmc_const_boost_var`, `tai_tsmc_prod_boost_var` (`ai_chance` only)                                                                                                                                                                                                                                                                         | `events/TAI_tsmc_events.txt`                                                     |
| Nokia         | Receiver-owned GER flags `GER_nokia_nsn_jv_accepted`, `GER_nokia_nsn_jv_declined`, `GER_nokia_siemens_sale_accepted`, `GER_nokia_siemens_sale_declined`; FRA flags `FRA_nokia_alu_commitments_accepted`, `FRA_nokia_alu_commitments_enhanced`, `FRA_nokia_alu_transaction_blocked` (transaction callbacks only)                                                                                                                                                                                                                                | `events/FIN_nokia_events.txt`, `common/scripted_effects/FIN_nokia_effects.txt`   |
| France        | The existing `FRA_nokia_response_events.1` remains the France-owned transaction interface. France adapters record only local state; FIN events `.95` / `.96` remain the only cross-country callbacks, and no France effect writes FIN state directly.                                                                                                                                                                                                                                                                                          | `events/FRA_nokia_response_events.txt`, `common/scripted_effects/FRA_*`          |
| Siemens       | Nokia NSN flags `FIN_nokia_siemens_networks_formed`, `FIN_nokia_networks_wholly_owned`, `FIN_nokia_exited_networks` (option triggers)                                                                                                                                                                                                                                                                                                                                                                                                          | `events/GER_siemens_events.txt`                                                  |
| Sony          | GPU-chain flags `JAP_gpu_*` (capstone option triggers/`ai_chance`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `events/JAP_sony_events.txt`                                                     |
| Nintendo      | Sony platform outcomes `JAP_sony_playstation_platform`, `JAP_sony_open_media_ecosystem`, `JAP_sony_ps5_platform_scale`; Japanese GPU flags `JAP_gpu_2001_*`, `JAP_gpu_2020_*`, `JAP_gpu_2024_*`; NVIDIA `USA_nvidia_graphics_priority_retained`; TSMC `TAI_tsmc_mobile_anchor_strategy`, `TAI_tsmc_advanced_packaging_expanded`; E3 `USA_e3_direct_broadcast_protocol`, `USA_e3_digital_common_stage_enabled`, `USA_e3_permanently_retired` (visible-event availability, `ai_chance` and contextual option effects only, never reconstruction) | `events/JAP_nintendo_events.txt`                                                 |
| ATI/AMD       | Generic GPU compatibility inputs `CAN_ati_research_autonomy`, `CAN_ati_amd_integration`; both normalize to the corporate chain's post-acquisition compatibility marker without changing the generic flags. The global GPU event remains the sole acquisition choice.                                                                                                                                                                                                                                                                           | `common/scripted_effects/CAN_ati_effects.txt`, `events/00_gpu_development.txt`   |
| Matrox        | BlackBerry/AI flags `CAN_blackberry_qnx_embedded`, `CAN_ai_public_research_network`; legacy generic GPU flags `CAN_ati_research_autonomy`, `CAN_ati_amd_integration` (read-only event context and capstone triggers)                                                                                                                                                                                                                                                                                                                           | `events/CAN_matrox_events.txt`                                                   |
| OEM bridge    | Read-only terminal outcomes of Apple, HP, NVIDIA, Dell, TI, Micron, Motorola, Google and Oracle, plus the IBM-owned `USA_oem_*` base axes. Writes only its own derived variables and the five `USA_corporate_systems_economic_integration_*` ideas, never chain state. Chain-to-axis table: `.claude/docs/usa-oem-economic-bridge-map.md`                                                                                                                                                                                                      | `common/scripted_effects/USA_corporate_systems_effects.txt`                      |
| IBM (inbound) | US politics via `USA_ibm_*_administration` triggers, reads non-corporate state, allowed                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `common/scripted_triggers/MD_oem_triggers.txt`                                   |

`gpu_development`, BlackBerry, and Ericsson read **no** state of the covered chains, so gating the chains cannot strand them. The Dell bridge above is the only retained `USA_oem_events` write-through. The global GPU chain is independent of `rule_corporate_history`; its USA/TAI mirrors are inputs only. The three Nokia NSN flags are a stable API; Siemens depends on them; do not rename.

Nokia's `FIN_nokia_fwa_cpe_sale_confirmed` and `FIN_nokia_ai_ran_trial_confirmed` flags are future external confirmations. No dated event or reconstruction step sets them. In Full mode, the Finnish monthly driver dispatches `.106` or `.107` only after another system supplies the matching confirmation; it never infers a close, trial, or deployment date.

# Tier Budgets

New chains must fit one of three budgets. Anything larger needs maintainer sign-off.

- **Tier 1**: full chain, ~12-15 events, bounded 0..10 state variables, full capstone set (mutually exclusive outcome ideas + resolved flag), reconstruction, monthly-driver coverage.
- **Tier 2**: focused chain, 4-6 events, a single outcome idea, flag-based state, reconstruction.
- **Tier 3**: flavor, 1-2 events, no persistent state, no reconstruction needed.

Classification of the existing chains (chains predating the budgets are marked _grandfathered_; do not copy their scale):

| Chain                                               | Tier                          | Notes                                                                                                                                                                                                                                                          |
| --------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Apple (USA)                                         | 1                             | Reference implementation: 15 events, 7 variables, 5 outcome ideas, scheduler + reconstruction                                                                                                                                                                  |
| NVIDIA (USA)                                        | 1                             | 12 visible events, 4 bounded variables, 5 outcome ideas, scheduler + reconstruction                                                                                                                                                                            |
| Dell (USA)                                          | 1                             | 15 events, 5 bounded variables, 5 outcome ideas, Alienware brand branch, scheduler + reconstruction, legacy `USA_oem_events` bridge                                                                                                                            |
| E3 (USA)                                            | 1                             | 23 visible events, 10 variables incl. lifecycle stages, outcome ideas, scheduler + reconstruction                                                                                                                                                              |
| Sony (JAP)                                          | 1                             | 15 events, flag-based state, 4 outcome ideas, player-choice capstone                                                                                                                                                                                           |
| Nintendo (JAP)                                      | 1                             | 15 visible events, 5 bounded variables, 5 outcome ideas, scheduler + reconstruction, per-event delivery markers with skipped-milestone advance and lost-delivery recovery                                                                                      |
| AIG (USA)                                           | 1                             | 14 visible events plus two hidden anchors, 4 bounded variables, 5 outcome ideas, scheduler + reconstruction; gated on MD's existing Great Financial Crisis state                                                                                               |
| ATI/AMD (CAN)                                       | 1                             | 12 visible events, 5 bounded variables, 5 outcome ideas, scheduler + reconstruction, generic GPU compatibility bridge                                                                                                                                          |
| Matrox (CAN)                                        | 1                             | 12 events, flag-based state, 4 outcome ideas, player-choice capstone                                                                                                                                                                                           |
| TSMC (TAI)                                          | 1                             | 15 visible events, 4 bounded variables, monotonic facility callbacks, 5 outcome ideas                                                                                                                                                                          |
| Nokia (FIN)                                         | 1                             | 15 visible events, 4 bounded variables, staged GER/FRA transactions, 6 outcome ideas                                                                                                                                                                           |
| France Corporate Systems (FRA)                      | 1 _(national module)_         | 24 new visible events plus the existing Nokia response, 10 bounded variables, 5 outcome ideas, scheduler + reconstruction, read-only national dashboard                                                                                                        |
| Huawei (CHI)                                        | 1                             | 15 visible events, 7 bounded variables, 4 lifecycle eras, 5 temporary burdens, 6 outcome ideas, scheduler + reconstruction                                                                                                                                     |
| Russian Computing Sovereignty (SOV)                 | 1                             | 18 visible events, 9 bounded axes plus 3 bounded auxiliary variables, 19 SOV-only technologies, industrial projects, 7 outcome ideas, scheduler + reconstruction; approved above the normal Tier-1 event guideline                                             |
| Texas Instruments (USA)                             | 1                             | 9 visible events plus reconstruction anchors, 4 bounded variables, 6 outcome ideas, scheduler + reconstruction                                                                                                                                                 |
| Micron (USA)                                        | 1                             | 15 visible events, 4 bounded variables, 6 outcome ideas, scheduler + reconstruction                                                                                                                                                                            |
| Motorola (USA)                                      | 1                             | 13 visible events plus reconstruction anchors, 4 bounded variables, 7 outcome ideas, scheduler + reconstruction                                                                                                                                                |
| Foxconn (TAI)                                       | 1 _(grandfathered)_           | 19 visible milestones, 4 bounded variables, 4 terminal outcomes, scheduler + reconstruction                                                                                                                                                                    |
| IBM (USA)                                           | 1 _(grandfathered)_           | 50 events, 13 ideas, consequence schedulers, monthly crisis engine, over every budget                                                                                                                                                                          |
| Sun/Microsoft (USA)                                 | 2 _(satellite)_               | 11 events, no own state or ideas; declared write-through into IBM state                                                                                                                                                                                        |
| Lenovo (CHI)                                        | 2 _(grandfathered satellite)_ | 8 events, flag-and-idea reconstruction, and IBM/Motorola owner-effect handoffs                                                                                                                                                                                 |
| Google (USA)                                        | 2 _(grandfathered)_           | 20 events and 3 bounded variables, over the Tier-2 event budget; no outcome ideas; reconstruction covers the historical path. In Full mode, events 16-20 run on `USA_google_extension_catchup` while 1-15 stay on the yearly dispatchers                       |
| Oracle (USA)                                        | 2 _(grandfathered)_           | 12 events, over the Tier-2 event budget; no outcome ideas; marker-based reconstruction covers the historical path. Its state variables are undeclared in the manifest and therefore unclamped. In Full mode the whole chain runs on `USA_oracle_chain_catchup` |
| HP (USA)                                            | 3 _(grandfathered)_           | 13 events with flag-based historical reconstruction but no bounded variables or outcome ideas; flavor economics only                                                                                                                                           |
| Siemens (GER), Ericsson (SWE), BlackBerry (CAN/USA) | 2                             | Dispatch-moved + rule-gated only; internals not yet on the framework                                                                                                                                                                                           |

## Poland: Industrial Sovereignty

Poland's Tier 1 chain is intentionally state-policy-only. Its five bounded values are domestic
control, technological depth, export capacity, systems integration, and supply resilience.
`corporate_history_on_startup` initializes and schedules its current year in Full mode, while
Outcomes Only invokes hidden `POL_industrial_sovereignty_events.90` and the existing Polish
monthly hook retries the silent dated ladder. The yearly file calls only the
`POL_corporate_trigger_year_<year>` wrappers; it never schedules visible Polish events itself.
The chain has no external contract reads or writes: pre-existing Polish procurement, MIO,
energy, Rail Baltica, and foreign-country content remains independent context.

## France: Corporate Systems

France's Tier 1 national module combines three interdependent chains: Alcatel supplies telecom
equipment and the consolidation story, STMicroelectronics supplies semiconductor capacity and
European research cooperation, and France Télécom/Orange supplies operator demand, debt,
infrastructure, and procurement choices. Ten variables on a 0-10 scale feed five mutually
exclusive national outcome ideas. The source specification's larger 0-100 deltas are scaled by
0.1 before clamping for nine axes. Chinese vendor dependency is deliberately amplified because
it represents concentrated supplier lock-in and nonlinear replacement exposure; this sole scale
exception keeps the China-connected outcome reachable without a repeatable policy.

`corporate_history_on_startup` initializes France and schedules the current start year in Full
mode, then uses hidden `FRA_corporate_systems_events.90` to reconstruct earlier milestones.
Outcomes Only reconstructs synchronously without firing an event; `on_monthly_FRA` retries
reward-free reconstruction and Full-mode lost-delivery repair. The yearly dispatcher calls only
`FRA_corporate_trigger_year_<year>` wrappers. The existing `FRA_nokia_response_events.1` ID and
FIN callbacks remain stable, with France-owned adapter effects translating its three choices into
the national state model. The read-only decisions dashboard exposes the bounded strategic axes,
three company scorecards, lifecycle status, and capstone outcome.

Implementation and artwork provenance are recorded in
`.claude/docs/france-corporate-systems-plan.md`.
## Russia: Computing Sovereignty

Russia's Tier 1 ecosystem separates processor design, foreign-foundry availability, and domestic
high-volume manufacture. Its nine bounded axes cover architecture, fabrication, software, systems
integration, supply and tooling, foreign access, human capital, procurement, and shortage pressure.
The chain owns the `SOV_computing_sovereignty_*` state and technology branch while treating the
existing `microchips` resource, `microchip_plant`, Russian sanctions, Taiwan technology transfer,
Yandex, Kaspersky Lab, and Parallel Import decision as authoritative external context.

Full mode enables the 18 events, research branch, industrial projects, and policy decisions.
Outcomes Only reconstructs historical state and SOV-only technologies without popups or projects;
Off creates no state or technology access. The hidden `.90` event remains the reconstruction anchor.

# New-Chain Checklist

1. Wrapper effect file in `common/scripted_effects/` with the contract set above (init, clamp, reconstruct; capstone family for Tier 1; scheduler if the chain has potential start-year milestones).
2. Hidden `.90` event whose immediate is a thin reconstruct call, or a direct synchronous startup reconstruct call.
3. Schedule entries added to the matching `<TAG>_corporate_trigger_year_<YYYY>` effects (create new ones as needed; never schedule inline in `00_yearly_effects.txt`), plus the startup entry in `corporate_history_on_startup` (both branches).
4. Monthly-driver coverage: add the reconstruct call to `<TAG>_corporate_history_monthly_outcomes`; the driver terminates on the chain's `*_reconstruct_complete` flag, so the ladder must set that flag at its true final milestone (create the `on_monthly_<TAG>` hook if the country has none).
5. Outcome ideas: `allowed = { original_tag = <TAG> }` **and** `allowed_civil_war = { always = yes }`.
6. Guard audit on every reconstruct step: `date >` gate; `NOT` on the step's own marker **and all sibling markers**; `add_ideas` guarded by `NOT has_idea` on all alternatives; no event fires inside reconstruction; single-child `NOT`s only.
7. Cross-links declared in the table above; localisation; changelog.

# TODO Register

- **Siemens / Ericsson / BlackBerry**: no reconstruction effects; Outcomes Only suppresses their events with no silent replacement. Ericsson's existing `SWE_ericsson_events.90` is the natural first extraction; Siemens and BlackBerry have no `.90` at all and need ladders authored from their option effects.
- **Google / Oracle reconstruction parity**: both have Outcomes Only reconstruction. Oracle's reconstruction records milestone resolution and its historical cloud route without replaying every event-side variable or reward. Google's reconstruction covers the historical flags and bounded state. In Full mode, Oracle 1-12 remains fully covered by its catch-up driver, while Google 1-15 remains yearly-dispatch only and can be missed by a late Full-mode start.
- **Oracle state variables** (`USA_oracle_platform_scale`, `policy_access`, `integration_debt`, `ecosystem_openness`, `execution_discipline`, `infrastructure_depth`): mutated by every event, never initialized and never clamped, and undeclared in the manifest so the contract's clamp check skips them. Only `policy_access` and `integration_debt` are ever read, and only against one-sided thresholds, so the drift is currently inert. Declaring them in the manifest requires an `USA_oracle_initialize_state` / `USA_oracle_clamp_state` pair first.
- **Google extension variables** (`USA_google_ecosystem_openness`, `USA_google_policy_access`, `USA_google_platform_scale`): written by events 18-20, never read, never initialized, and not covered by `USA_google_clamp_state`. Either wire them into the clamp and the manifest or drop the writes.
- **`USA_google_events` namespace** is declared in two files (`USA_google_events.txt` and `USA_google_events_extension.txt`), the only split namespace in the repo. The contract discovers every file from its event definitions, so both files receive the same ownership checks.
- **Start-year schedulers** for IBM, Sun/Microsoft, Sony, and Matrox (Apple-pattern; inert while MD ships only the 2000.1.1 bookmark).
- **HP**: flag-based reconstruction exists, but the chain has no bounded variables or outcome idea; decide whether to keep its grandfathered Tier-3 classification or extend it to Tier 2.
- **Sun/Microsoft**: consider its own capstone/state if ever split from the IBM substrate; the current write-through is the declared exception.

# ATI/AMD Primary Sources

ATI/AMD milestone dates and historical framing use primary company or regulator records:

- [ATI fiscal 2002 Form 6-K](https://www.sec.gov/Archives/edgar/data/1065331/000119439603000004/ati_form6k-ann.htm)
- [Microsoft and ATI Xbox technology agreement](https://news.microsoft.com/source/2003/08/14/microsoft-and-ati-technologies-announce-technology-development-agreement/)
- [AMD acquisition filing](https://ir.amd.com/sec-filings/filter/current-reports/content/0001193125-06-217735/0001193125-06-217735.pdf)
- [AMD Fusion APU launch](https://ir.amd.com/news-events/press-releases/detail/168/amd-fusion-apu-era-begins)
- [Radeon Technologies Group formation](https://ir.amd.com/news-events/press-releases/detail/634/amd-forms-radeon-technologies-group-to-enhance-focus-on-graphics-and-immersive-computing-under-the-leadership-of-raja-koduri)
- [AMD RDNA launch](https://www.amd.com/en/newsroom/press-releases/2019-7-7-amd-unleashes-ultimate-pc-gaming-platform-with-wor.html)
- [AMD MI300 portfolio launch](https://www.amd.com/en/newsroom/press-releases/2023-12-6-amd-delivers-leadership-portfolio-of-data-center-a.html)
