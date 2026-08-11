# Linux System Reference

## Authority and modes

The Linux system is a shared country-scoped framework. ABK owns date dispatch only. Country state remains on each participant, and the bounded registry is `global.linux_system_participants`.

`rule_linux_ecosystem` has these options in this order:

1. `full`: authored events and economic programs are available.
2. `outcomes_only`: due history is reconstructed without events, political power or treasury changes, technology bonuses, or temporary option ideas.
3. `off`: Linux-owned ideas, expected and pending delivery flags, dirty and cooldown flags, active-program artifacts, and participant entries are removed.

Off preserves initialization and reconstruction markers, resolved and route history, imported native state, all state variables, milestone stage, and `GLOBAL_linux_system_milestone_N_reached`. This keeps an existing save reversible without erasing authoritative history.

The public gates are `linux_system_full_enabled`, `linux_system_outcomes_only_enabled`, and `linux_system_enabled`. They read the game rule directly because cached game-rule flags are unavailable during early startup on-actions.

## Registration and dispatch

`linux_system_register_country` is the public country-scope entry point. It accepts every normal existing playable country except ABK, ZOM, `MD_special_countries`, and countries carrying `collapsed_nation`. It deduplicates `THIS` before adding it to `global.linux_system_participants`.

Generic `on_weekly` self-registration discovers new and missing-array participants without `every_country` or `random_country`. Collapsed participants remain in the array and retain state, while milestone scheduling, activation, and the monthly driver skip all active work for them. On restoration, the next monthly bounded-array pass reconstructs milestones missed during collapse and prepares an expected-only marker for any milestone still due later that year. ABK runs only startup, daily date dispatch, and the monthly bounded-array driver.

## State model

Deployment, Stewardship, and Assurance use a 0 to 10 scale. Support Model uses a 0 to 3 categorical scale.

| Layer     | Deployment                          | Stewardship                          | Assurance                          | Support Model                          |
| --------- | ----------------------------------- | ------------------------------------ | ---------------------------------- | -------------------------------------- |
| Base      | `linux_system_base_deployment`      | `linux_system_base_stewardship`      | `linux_system_base_assurance`      | `linux_system_base_support_model`      |
| Adapter   | `linux_system_adapter_deployment`   | `linux_system_adapter_stewardship`   | `linux_system_adapter_assurance`   | `linux_system_adapter_support_model`   |
| Effective | `linux_system_effective_deployment` | `linux_system_effective_stewardship` | `linux_system_effective_assurance` | `linux_system_effective_support_model` |

New state begins at Deployment 2, Stewardship 3, Assurance 3, and Support Model 0. Numeric adapters clamp from -2 through 2. The support adapter clamps from 0 through 3. Effective support uses nonzero base support when present; otherwise it uses the authoritative adapter category. Support is not additive.

Support Model values are:

- 0: Mixed Linux Estate
- 1: Upstream Partnership
- 2: Enterprise Distribution
- 3: National Baseline

`linux_system_mark_dirty` sets `linux_system_dirty`. `linux_system_recalculate_state` clamps base state, calls `linux_system_refresh_adapter`, rebuilds effective state, derives `linux_system_milestone_stage` from resolved flags, refreshes ideas, and clears the dirty flag. USA recalculation immediately refreshes `USA_corporate_systems_update_economic_bridge` after Linux effective state is current.

Cross-system consumers read Linux base variables. National adapters may read native state into Linux adapter variables. This one-way direction prevents effective-state feedback loops.

## Historical milestones

Full-mode January 1 scheduling sets permanent `expected`, sets timed `pending` for the offset plus a 60-day delivery window, and queues the authored event. The due-date dispatcher does nothing while expected and pending still represent that queue. Startup and monthly recovery restore a missing `expected` marker when an older save retains only `pending`. If expected survives after pending expires, recovery sets a new 60-day pending flag and queues one delivery for the next day.

A fresh late participant with no delivery markers receives state-only reconstruction and sees only future events. A country registered or restored after January 1 receives an expected-only marker for a milestone still due later that year; the due-date dispatcher then queues its single delivery. Outcomes Only also reconstructs due state. Full preserves an old save's expected or pending authored delivery instead of replacing it. Reconstruction never spends money or political power, grants technology bonuses, adds temporary event ideas, or replays native rewards.

| Stage | Event                   | Due date   | January 1 offset | Initial pending duration |
| ----- | ----------------------- | ---------- | ---------------: | -----------------------: |
| 1     | `linux_system_events.1` | 2001-01-04 |                3 |                  63 days |
| 2     | `linux_system_events.2` | 2008-06-01 |              152 |                 212 days |
| 3     | `linux_system_events.3` | 2015-12-10 |              343 |                 403 days |
| 4     | `linux_system_events.4` | 2019-07-09 |              189 |                 249 days |
| 5     | `linux_system_events.5` | 2024-04-30 |              120 |                 180 days |

Generic reconstruction uses a neutral absolute baseline. USA reconstruction uses its historical Enterprise route state. The values below are base Deployment, Stewardship, Assurance, and Support Model after each due milestone.

| Date band         | Generic state | USA state      | USA route  |
| ----------------- | ------------- | -------------- | ---------- |
| Before 2001-01-04 | 2 / 3 / 3 / 0 | 2 / 3 / 3 / 0  | None       |
| From 2001-01-04   | 3 / 3 / 3 / 0 | 4 / 3 / 4 / 2  | Enterprise |
| From 2008-06-01   | 4 / 3 / 3 / 0 | 5 / 3 / 6 / 2  | Enterprise |
| From 2015-12-10   | 5 / 3 / 4 / 0 | 6 / 3 / 8 / 2  | Enterprise |
| From 2019-07-09   | 6 / 3 / 4 / 0 | 8 / 3 / 10 / 2 | Enterprise |
| From 2024-04-30   | 7 / 3 / 5 / 0 | 8 / 3 / 10 / 2 | Enterprise |

Each event `N` owns `linux_system_event_N_expected`, `_pending`, and `_resolved`. Authored live options and sourced historical variants for milestones 2 through 4 also set one route flag from the choices that milestone actually offers; neutral reconstruction leaves route flags unset. Milestone 1 has no route-specific downstream presentation, and milestone 5 is terminal, so their support-model variables and resolved markers are authoritative instead of duplicate route flags. ABK owns `GLOBAL_linux_system_milestone_N_reached`. Terminal historical state is `linux_system_milestone_stage = 5` together with `linux_system_event_5_resolved`.

The authored live-event deltas are:

| Event | Upstream         | Enterprise | National    | Mixed       |
| ----- | ---------------- | ---------- | ----------- | ----------- |
| 1     | D +1, S +2       | D +2, A +1 | Not offered | S -1, A -1  |
| 2     | D +1, S +1, A +1 | D +1, A +2 | D +1, A +2  | A -1        |
| 3     | S +1, A +1       | D +1, A +2 | A +2        | A -1        |
| 4     | D +2, S +2, A +1 | D +2, A +2 | D +1, A +2  | Not offered |
| 5     | S +2, A +1       | A +2       | A +2        | D -1, A -2  |

## USA integration

USA never receives the four generic adoption ideas or four support-model ideas. Its persistent economic contribution is owned by `USA_corporate_systems_linux_contribution`; Linux recalculation refreshes that bridge immediately.

If Corporate History is Off, the bridge ignores native company outcomes and uses its own neutral derived-axis baseline of 5 on each axis plus the Linux contribution. It does not initialize or write IBM or Corporate Systems base state. This preserves USA economic integration while keeping the two rules independent.

`linux_system_refresh_usa_adapter` reads IBM outcomes only while Corporate History is enabled. Corporate History Off yields no IBM adapter contribution. Storage events 16 through 23 are Linux-owned and may contribute whenever Linux is enabled. Adapter refresh never writes IBM or storage state.

The one-time storage import preserves an old save's `USA_oem_storage_policy` without continuing to read that legacy scalar. A nonzero legacy value becomes `linux_system_usa_storage_legacy_import_level`, an absolute value clamped from 1 through 2; zero creates no route. Its Upstream route adds that level to Stewardship and supplies Support 1 when base support is Mixed. Its Enterprise route adds that level to Deployment and Assurance and supplies Support 2. The imported marker, level, and route survive Linux Off.

Storage event 18 is not folded into the generic storage adapter groups. Its Enterprise route adds Assurance 1, subtracts Stewardship 1, and supplies Support 2. Its Upstream compatibility route adds Deployment 1 and Stewardship 1, subtracts Assurance 1, and supplies Support 1 when base support is Mixed.

Full-mode generic-event suppression is limited to these native overlaps:

- Event 1: `USA_ibm_event_13_scheduled` or `USA_ibm_event_13_resolved`
- Event 3: `USA_ibm_event_31_scheduled`, `USA_ibm_event_31_resolved`, `USA_oem_storage_event_19_pending`, or `USA_oem_storage_event_19_resolved`
- Event 4: `USA_ibm_event_34_scheduled` or `USA_ibm_event_34_resolved`

Suppression resolves the generic milestone through its Enterprise route and applies that event's durable Enterprise delta only. This preserves any earlier live choice. Event 2 always remains available. Event 5 remains one settlement event after `USA_ibm_event_39_resolved`. Corporate History Off allows every unresolved generic milestone.

`USA_oem_storage_reconstruct_linux_history` is the only coordinated native-state reconstruction call. Registration calls it for USA in Outcomes Only or late-start state recovery, then refreshes the read-only adapter. The monthly Full-mode USA pass calls `USA_oem_storage_recover_pending_events`. Linux Off calls `USA_oem_storage_clear_linux_pending_markers`, which clears expected and pending delivery state but preserves resolved routes and the one-time import.

## Persistent ideas

Adoption is selected from effective Deployment. Support is selected from effective Support Model. Exactly one idea from each family applies to non-USA participants.

| Deployment | Idea                                   | Modifiers                                                                                 |
| ---------- | -------------------------------------- | ----------------------------------------------------------------------------------------- |
| 0 to 2     | `linux_system_experimental_adoption`   | None                                                                                      |
| 3 to 5     | `linux_system_institutional_adoption`  | Research +0.5%; offices productivity +0.5%                                                |
| 6 to 8     | `linux_system_infrastructure_standard` | Research +0.5%; productivity growth +0.5%; offices productivity +1%; cyber defense +1     |
| 9 to 10    | `linux_system_broad_economic_adoption` | Research +1%; productivity growth +1%; offices productivity +2%; corporate-tax income +1% |

| Support | Idea                                   | Modifiers                                                                          |
| ------: | -------------------------------------- | ---------------------------------------------------------------------------------- |
|       0 | `linux_system_mixed_linux_estate`      | Research -1%; cyber defense -1; bureaucracy cost +1%                               |
|       1 | `linux_system_upstream_partnership`    | Research +1%; incoming-investment cost -2.5%; bureaucracy cost +1%                 |
|       2 | `linux_system_enterprise_distribution` | Offices productivity +1%; corporate-tax income +1%; internal-investment cost +2.5% |
|       3 | `linux_system_national_baseline`       | Research -0.5%; cyber defense +2; bureaucracy cost +2%                             |

## Economic programs

`common/decisions/categories/MD_linux_system_categories.txt` owns the `linux_system_programs` category. The container has exactly four repeatable Full-mode programs. Only one can be active. A decision remains active for its program duration; its `remove_effect` removes any surviving program idea and starts `linux_system_program_cooldown` for 365 days. Availability also requires no bankruptcy-collapse mission. Public procurement is not visible to USA.

| Decision                                   |  PP | Treasury | Duration | Durable base change   | Active modifier                                             |
| ------------------------------------------ | --: | -------: | -------: | --------------------- | ----------------------------------------------------------- |
| `linux_system_fund_upstream_maintenance`   |  25 | 0.1% GDP | 365 days | S +1, A +1            | Research +1%; bureaucracy cost +1%                          |
| `linux_system_contract_enterprise_support` |  25 | 0.1% GDP | 365 days | D +1, A +1, Support 2 | Productivity growth +1%; bureaucracy cost -1%               |
| `linux_system_harden_lifecycle`            |  35 | 0.1% GDP | 365 days | A +2                  | Cyber defense +2; bureaucracy cost +1%                      |
| `linux_system_public_procurement`          |  50 | 0.2% GDP | 730 days | D +1, S +1, A +1      | Research +1%; productivity growth +1%; bureaucracy cost +2% |

The treasury helpers are `linux_system_pay_gdp_0_1_percent` and `linux_system_pay_gdp_0_2_percent`. Matching affordability triggers include the bankruptcy guard.

## Source register

Only approved official sources belong in this core reference. National adapter research belongs with its owning content.

| Source                                                                  | Contract use                                          |
| ----------------------------------------------------------------------- | ----------------------------------------------------- |
| https://www.kernel.org/pub/linux/kernel/v2.4/                           | Linux 2.4 archive and the 2001-01-04 milestone anchor |
| https://www.ibm.com/investor/news/ibm-completes-acquisition-of-red-hat  | IBM and Red Hat integration anchor dated 2019-07-09   |
| https://www.ibm.com/support/pages/ibm-powerlinux-backed-linux-community | IBM PowerLinux and Linux community commitment context |
