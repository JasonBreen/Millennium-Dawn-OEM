# United States — Anduril Corporate History (2017–2025)

Scope: OEM Corporate History module modelling Anduril Industries from founding through border sensor towers, allied counter-drone trials, the counter-UAS program of record, the Area-I acquisition, the SOCOM award, Roadrunner, Collaborative Combat Aircraft, and a 2025 capstone. Not a new focus tree, not Great AI Race. English localisation only. Namespace `USA_anduril_events`. Root prefix `USA_anduril`. Owner tag `USA` (`original_tag = USA` in every trigger).

Anduril is founded in 2017, so this is a short chain by the module's standards: eight visible beats and a capstone, against SpaceX's twelve. There is no pre-2017 history to reconstruct.

Game-rule semantics:

- Full: initialize, reconstruct only elapsed history, schedule current-year beats, deliver 8 visible beats plus a capstone, then complete
- Outcomes Only: silent reconstruction picks the historical route at each beat, then applies exactly one capstone idea after 2025
- Off: creates no `USA_anduril_*` state, schedules nothing, changes nothing outside this chain

Do not write any other chain's identifiers (Palantir, AI Core, OpenAI, Anthropic, NVIDIA, Great AI Race). This chain declares no `allowed_reads` and no `allowed_writes` — it is deliberately self-contained, unlike Palantir, which syncs to AI Core.

## State model (persistent axes, 0..10)

All integers clamped 0..10 by `USA_anduril_clamp_state`. Owner effects only.

| Variable | Meaning | 2017 start |
| --- | --- | --- |
| `USA_anduril_autonomy_depth` | Lattice and autonomy software maturity | 3 |
| `USA_anduril_production_scale` | Mass-manufacture capacity | 1 |
| `USA_anduril_procurement_reform` | Leverage of non-traditional vendors over the primes | 4 |
| `USA_anduril_allied_integration` | Depth of allied programs | 1 |
| `USA_anduril_civil_oversight` | Public and congressional legitimacy | 5 |

The opening state is the argument the company was founded on: high procurement leverage, real software, almost no factory, and an oversight position it has not yet spent.

Required owner effects (all idempotent): `initialize_state`, `clamp_state`, `reconstruct_history`, `recover_prior_year_history`, `schedule_current_year_events`, `resolve_capstone`, `terminal_callback`.

Lifecycle flags: `USA_anduril_state_initialized`, `USA_anduril_reconstruct_complete`, `USA_anduril_start_year_events_scheduled`, `USA_anduril_capstone_resolved`.

## Routes

Five shared route effects, applied by both visible options and silent reconstruction, so Full and Outcomes Only move the same axes:

- `apply_autonomy_route` — autonomy +2, scale +1, procurement −1, oversight −1
- `apply_scale_route` — scale +2, procurement +1, allied −1, oversight −1
- `apply_procurement_route` — procurement +2, scale +1, allied −1, oversight −1
- `apply_allied_route` — allied +2, autonomy +1, scale −1, procurement −1
- `apply_oversight_route` — oversight +2, procurement +1, autonomy −1, scale −1

Every beat offers the oversight route as its first option. That option is the AI's bankruptcy escape hatch: it alone omits the `bankruptcy_incoming_collapse` / `ai_has_major_economic_problems` / `treasury < 0` zeroes, so no beat can present the AI with an all-zero `ai_chance` set.

## Visible beats (is_triggered_only), 8 + capstone

`days` is day-of-year minus one, because the yearly dispatcher fires on 1 January and `days = N` lands on day-of-year N+1.

| # | Year | Anchor | days | Historical route |
| --- | --- | --- | --- | --- |
| 1 | 2017 | Anduril founded | 151 | procurement |
| 2 | 2018 | Sentry towers fielded by CBP | 155 | autonomy |
| 3 | 2019 | Allied counter-drone trials | 252 | allied |
| 4 | 2020 | Counter-UAS becomes a program of record | 196 | autonomy |
| 5 | 2021 | Area-I acquisition brings Altius in house | 95 | scale |
| 6 | 2022 | SOCOM counter-UAS award | 10 | procurement |
| 7 | 2023 | Roadrunner reusable interceptor unveiled | 334 | scale |
| 8 | 2024 | Fury selected for Collaborative Combat Aircraft | 114 | autonomy |
| 9 | 2025 | Capstone — Arsenal-1 and the IVAS handover | 41 | — |

Options are written as government levers, not board decisions: the player is the United States deciding how to treat the company, not the company deciding its own strategy. Events never spend treasury or political power, grant research bonuses, place buildings, or alter opinions.

## Capstone

`USA_anduril_events.9` offers five options in collision order. Four are gated on axis thresholds; the fifth is always available so the event can never dead-end.

| Option | Idea | Gate |
| --- | --- | --- |
| `.a` | `USA_anduril_autonomous_arsenal` | scale > 6 and autonomy > 6 |
| `.b` | `USA_anduril_allied_autonomy_bloc` | allied > 5 |
| `.c` | `USA_anduril_procurement_insurgency` | procurement > 6 |
| `.e` | `USA_anduril_unaccountable_platform` | oversight < 4 |
| `.f` | `USA_anduril_disciplined_challenger` | always (fallback) |

Option letters skip `d`: `.d` is the description key, and a fourth option named `.d` collides with it. This is the module's existing convention, not a new one.

Each option shows `effect_tooltip = { add_ideas = ... }` plus a `_tt` line, then sets `USA_anduril_capstone_choice` as a **temp** variable inside `hidden_effect` and calls `resolve_capstone` in the same block. The choice is transient by design and is therefore not a declared contract variable.

Outcomes Only never opens the popup: `reconstruct_history` applies the historical route at every elapsed beat and, after 2025-12-31, resolves the capstone from the accumulated axes.

## Balance

The five outcome ideas are permanent, which the module allows because they describe industrial capacity the United States owns rather than a market position it merely holds. `unaccountable_platform` is the deliberate risk outcome: the strongest industrial modifier in the set paired with the only negative stability and political power terms.

## Files and ownership

- `events/USA_anduril_corporate_events.txt` — 8 visible beats + capstone
- `common/scripted_effects/USA_anduril_corporate_effects.txt` — state, routes, recorders, reconstruction, schedulers, capstone resolver
- `common/ideas/USA_anduril_corporate_ideas.txt` — 5 capstone ideas
- `localisation/english/MD_focus_USA_l_english.yml` — 86 keys
- `tools/corporate_history_contract.json` — contract entry
- `common/scripted_effects/00_corporate_history_dispatch_effects.txt` — scheduler call in `USA_corporate_trigger_year_2017` through `_2025`
- `common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt` — bootstrap reconstruction and start-year scheduling
- `common/scripted_effects/00_corporate_history_effects.txt` — Outcomes Only driver call in `USA_corporate_history_monthly_outcomes`

No entry is needed in `00_corporate_history_midyear_recovery_effects.txt`: that file serves chains without native recovery, and this chain owns `USA_anduril_recover_prior_year_history`.

## Sources (dates verified)

- Founded: 2017 — Anduril Industries, Irvine, California
- Sentry towers with CBP: 2018
- Allied counter-drone trials including Royal Navy: 2019
- Counter-UAS moves to a program of record: 2020
- Area-I acquisition (Altius launched effects): 2021
- SOCOM counter-UAS systems integrator award, up to ~$1B over ten years: January 2022
- Roadrunner and Roadrunner-M unveiled: December 2023
- Fury (YFQ-44A) selected for CCA Increment 1: April 2024
- Arsenal-1 announced (Ohio): January 2025; IVAS program taken over from Microsoft: February 2025

Dates are scheduler anchors only; no policy claims beyond public announcements.
