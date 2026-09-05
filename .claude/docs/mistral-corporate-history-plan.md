# France — Mistral AI Corporate History (2023–2025)

Scope: OEM Corporate History module modelling Mistral AI from founding through the Mixtral open-weight release, the Microsoft partnership, its largest funding rounds, Le Chat and government adoption, and the ASML-led round, ending in a 2025 capstone. Not a new focus tree, not Great AI Race. English localisation only. Namespace `FRA_mistral_events`. Root prefix `FRA_mistral`. Owner tag `FRA` (`original_tag = FRA` in every trigger).

Mistral is founded in April 2023, so like Anduril this is a short chain: six visible beats and a capstone, all inside three calendar years. No content is scheduled in 2026 or later.

Game-rule semantics:

- Full: initialize, reconstruct only elapsed history, schedule current-year beats, deliver 6 visible beats plus a capstone, then complete
- Outcomes Only: silent reconstruction picks the historical route at each beat, then applies exactly one capstone idea after 2025-12-31
- Off: creates no `FRA_mistral_*` state, schedules nothing, changes nothing outside this chain

Do not write any other chain's identifiers (FRA Corporate Systems/Nokia, AI Core, OpenAI, Anthropic, Palantir, Anduril, Great AI Race). This chain declares no `allowed_reads` and no `allowed_writes` — it is self-contained, distinct from `FRA_corporate_systems`, which already owns France's Alcatel/Nokia 5G sovereignty arc.

## State model (persistent axes, 0..10)

All integers clamped 0..10 by `FRA_mistral_clamp_state`. Owner effects only.

| Variable | Meaning | 2023 start |
| --- | --- | --- |
| `FRA_mistral_model_capability` | Frontier model quality relative to the leading labs | 3 |
| `FRA_mistral_open_weights` | Depth of the open-weight release strategy | 6 |
| `FRA_mistral_compute_sovereignty` | Share of training run on European infrastructure | 2 |
| `FRA_mistral_commercial_scale` | Enterprise and consumer revenue base | 1 |
| `FRA_mistral_strategic_independence` | Freedom from foreign capital and cloud dependency | 6 |

The opening state matches the company's actual starting position: an open-weight-first laboratory with almost no compute of its own and no foreign investor yet on the cap table.

Required owner effects (all idempotent): `initialize_state`, `clamp_state`, `reconstruct_history`, `recover_prior_year_history`, `schedule_current_year_events`, `resolve_capstone`, `terminal_callback`.

Lifecycle flags: `FRA_mistral_state_initialized`, `FRA_mistral_reconstruct_complete`, `FRA_mistral_start_year_events_scheduled` (declared for contract symmetry; this chain's primary firing path is the once-per-year `FRA_corporate_trigger_year_N` dispatcher, matching `FRA_corporate_systems`' own wiring — no separate monthly-bootstrap guard was added), `FRA_mistral_capstone_resolved`.

## Routes

Five shared route effects, applied by both visible options and silent reconstruction, so Full and Outcomes Only move the same axes:

- `apply_capability_route` — capability +2, commercial +1, open weights -1, independence -1
- `apply_open_route` — open weights +2, capability +1, commercial -1, sovereignty -1
- `apply_sovereign_route` — sovereignty +2, independence +1, commercial -1, capability -1
- `apply_commercial_route` — commercial +2, capability +1, independence -1, open weights -1
- `apply_independence_route` — independence +2, sovereignty +1, commercial -1, capability -1

Every beat offers the independence route as its first option. That option is the AI's bankruptcy escape hatch: it alone omits the `bankruptcy_incoming_collapse` / `ai_has_major_economic_problems` / `treasury < 0` zeroes, so no beat can present the AI with an all-zero `ai_chance` set.

## Visible beats (is_triggered_only), 6 + capstone

`days` is day-of-year minus one, because the yearly dispatcher fires on 1 January and `days = N` lands on day-of-year N+1.

| # | Year | Anchor | days | Historical route |
| --- | --- | --- | --- | --- |
| 1 | 2023 | Mistral AI founded, 105M euro seed round | 163 | open |
| 2 | 2023 | Mixtral open-weight release, 385M euro round | 344 | open |
| 3 | 2024 | Microsoft partnership and Azure distribution | 56 | commercial |
| 4 | 2024 | 600M euro round | 162 | capability |
| 5 | 2025 | Le Chat and French government adoption | 36 | sovereign |
| 6 | 2025 | ASML leads a 1.3B euro round | 251 | capability |
| 7 | 2025 | Capstone — what Mistral became | 334 | — |

Options are written as government levers, not board decisions: the player is France deciding how to treat the company, not Mistral deciding its own strategy. Events never spend treasury or political power, grant research bonuses, place buildings, or alter opinions.

## Capstone

`FRA_mistral_events.7` offers five options in collision order. Four are gated on axis thresholds; the fifth is always available so the event can never dead-end. Option letters skip `d` (the description key) — `a b c e f`, matching the Anduril/Palantir convention.

| Option | Idea | Gate |
| --- | --- | --- |
| `.a` | `FRA_mistral_european_champion` | capability > 6 and independence > 5 |
| `.b` | `FRA_mistral_open_weights_standard` | open weights > 6 |
| `.c` | `FRA_mistral_sovereign_compute_stack` | compute sovereignty > 6 |
| `.e` | `FRA_mistral_hyperscaler_annex` | independence < 4 |
| `.f` | `FRA_mistral_credible_challenger` | always (fallback) |

Each option shows `effect_tooltip = { add_ideas = ... }` plus a `_tt` line, then sets `FRA_mistral_capstone_choice` as a **temp** variable inside `hidden_effect` and calls `resolve_capstone` in the same block — the choice is transient by design and is not a declared contract variable.

Outcomes Only never opens the popup: `reconstruct_history` applies the historical route at every elapsed beat and, after 2025-12-31, resolves the capstone from the accumulated axes.

## Balance

The five outcome ideas are permanent, matching the module's convention for chains that describe industrial or research capacity a country owns rather than a market position it merely holds. `hyperscaler_annex` is the deliberate risk outcome: the strongest research bonus in the set paired with the only negative political power and stability terms — Mistral succeeding as a product while France loses the strategic argument for having backed it.

## Files and ownership

- `events/FRA_mistral_corporate_events.txt` — 6 visible beats + capstone
- `common/scripted_effects/FRA_mistral_corporate_effects.txt` — state, routes, recorders, reconstruction, schedulers, capstone resolver
- `common/ideas/FRA_mistral_corporate_ideas.txt` — 5 capstone ideas
- `localisation/english/MD_focus_FRA_l_english.yml` — 70 keys
- `tools/corporate_history_contract.json` — contract entry
- `common/scripted_effects/00_corporate_history_dispatch_effects.txt` — `FRA_corporate_trigger_year_2023` through `_2025` (new; FRA's own yearly dispatch previously stopped at 2020)
- `common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt` — bootstrap reconstruction call and the three new yearly dispatch-caller lines
- `common/scripted_effects/00_corporate_history_effects.txt` — Outcomes Only driver call in `FRA_corporate_history_monthly_outcomes`

No entry is needed in `00_corporate_history_midyear_recovery_effects.txt`: that file serves chains without native recovery, and this chain owns `FRA_mistral_recover_prior_year_history`.

## Sources (dates verified)

- Founded: April 2023, Paris — Arthur Mensch, Guillaume Lample, Timothee Lacroix; 105M euro seed round, then reported the largest European seed round at the time
- Mixtral 8x7B released under Apache 2.0; 385M euro Series A: December 2023
- Microsoft partnership and Azure distribution announced: February 2024
- 600M euro Series B (Andreessen Horowitz-led): June 2024
- Le Chat launched: February 2024; French government and public-sector adoption discussion through 2025
- ASML-led 1.3B euro round, becoming Mistral's largest shareholder: September 2025

Dates are scheduler anchors only; no policy claims beyond public funding announcements and product releases.
