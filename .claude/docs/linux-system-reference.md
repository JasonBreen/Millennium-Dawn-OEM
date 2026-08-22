# Linux System Reference

## Authority and modes

The Linux system is a shared country-scoped framework. Each eligible country runs `linux_system_monthly_driver` from the generic country-scope `on_monthly` pulse. There is no singleton date host, participant array, or global milestone latch.

`rule_linux_ecosystem` has these options in this order:

1. `full`: authored events and economic programs are available.
2. `outcomes_only`: due history is reconstructed without events, political power or treasury changes, technology bonuses, or temporary option ideas.
3. `off`: Linux-owned ideas, decisions, delivery and route flags, active-program artifacts, and state variables are removed.

Off preserves native non-Linux state and the one-time legacy-storage import metadata, but it leaves no initialized Linux participant, milestone history, effective variables, or program state. Re-enabling the rule in a migrated save therefore reconstructs from the current date and native route inputs instead of relying on global history.

The public gates are `linux_system_full_enabled`, `linux_system_outcomes_only_enabled`, and `linux_system_enabled`. They read the game rule directly on the country-local monthly path.

## Registration and dispatch

`linux_system_monthly_driver` is the authoritative country-scope entry point. It accepts every normal existing playable country except ABK, ZOM, `MD_special_countries`, and countries carrying `collapsed_nation`. The country-local `linux_system_initialized` flag is the participation marker.

Generic `on_monthly` reaches each current country without `every_country` or `random_country`. Collapsed countries retain state but perform no initialization, reconstruction, scheduling, or event recovery. A restored or recreated country catches up from its own date and markers on its next monthly pass; no other country can consume that work.

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

`linux_system_mark_dirty` sets `linux_system_dirty`. `linux_system_recalculate_state` clamps base state, calls `linux_system_refresh_adapter`, rebuilds effective state, derives `linux_system_milestone_stage` from resolved flags, refreshes ideas, and clears the dirty flag. USA recalculation refreshes `USA_corporate_systems_update_economic_bridge` after Linux effective state is current only while Corporate History is enabled. The country-local monthly pass compares current and newly computed adapter values, then marks state dirty only when a native adapter changed.

Cross-system consumers read Linux base variables. National adapters may read native state into Linux adapter variables. This one-way direction prevents effective-state feedback loops.

## Historical milestones

Full-mode January scheduling sets permanent `expected`, sets timed `pending` for the offset plus a 60-day delivery window, and queues the authored event. Monthly due-date recovery does nothing while expected and pending still represent that queue. It restores a missing `expected` marker when an older save retains only `pending`. If expected survives after pending expires, recovery sets a new 60-day pending flag and queues one delivery for the next day.

A fresh late participant with no delivery markers receives state-only reconstruction for passed milestones and sees only future events. A country present before a future due date receives its expected marker and single delivery from the local schedule/recovery path. Full preserves an old save's expected or pending authored delivery instead of replacing it. Outcomes Only reconstructs due state on its next monthly pass. Reconstruction never spends money or political power, grants technology bonuses, adds temporary event ideas, or replays native rewards.

| Stage | Event                   | Due date   | January 1 offset | Initial pending duration |
| ----- | ----------------------- | ---------- | ---------------: | -----------------------: |
| 1     | `linux_system_events.1` | 2001-01-04 |                3 |                  63 days |
| 2     | `linux_system_events.2` | 2008-06-01 |              152 |                 212 days |
| 3     | `linux_system_events.3` | 2015-12-10 |              343 |                 403 days |
| 4     | `linux_system_events.4` | 2019-07-09 |              189 |                 249 days |
| 5     | `linux_system_events.5` | 2024-04-30 |              120 |                 180 days |

Generic reconstruction uses a neutral absolute baseline. Sourced historical countries reconstruct their route's durable state without costs or temporary rewards. The values below are base Deployment, Stewardship, Assurance, and Support Model after each due milestone.

| Date band         | Generic state | Upstream state | National state | USA Enterprise state |
| ----------------- | ------------- | -------------- | -------------- | -------------------- |
| Before 2001-01-04 | 2 / 3 / 3 / 0 | 2 / 3 / 3 / 0  | 2 / 3 / 3 / 0  | 2 / 3 / 3 / 0        |
| From 2001-01-04   | 3 / 3 / 3 / 0 | 3 / 5 / 3 / 1  | 4 / 3 / 4 / 2  | 4 / 3 / 4 / 2        |
| From 2008-06-01   | 4 / 3 / 3 / 0 | 4 / 6 / 4 / 1  | 5 / 3 / 6 / 3  | 5 / 3 / 6 / 2        |
| From 2015-12-10   | 5 / 3 / 4 / 0 | 4 / 7 / 5 / 1  | 5 / 3 / 8 / 3  | 6 / 3 / 8 / 2        |
| From 2019-07-09   | 6 / 3 / 4 / 0 | 6 / 9 / 6 / 1  | 6 / 3 / 10 / 3 | 8 / 3 / 10 / 2       |
| From 2024-04-30   | 7 / 3 / 5 / 0 | 6 / 10 / 7 / 1 | 6 / 3 / 10 / 3 | 8 / 3 / 10 / 2       |

ENG, GER, and BRA use the Upstream route. FRA, RAJ, SOV, and CHI use Enterprise for milestone 1 because no National option exists, then National for milestones 2 through 5. USA uses Enterprise throughout. Exact native reads, adapter bounds, and sources are documented in `linux-national-adapters.md`.

Each event `N` owns country-local `linux_system_event_N_expected`, `_pending`, and `_resolved` markers. Authored live options and sourced historical variants for milestones 2 through 4 also set one route flag from the choices that milestone actually offers; neutral reconstruction leaves route flags unset. Milestone 1 has no route-specific downstream presentation, and milestone 5 is terminal, so their support-model variables and resolved markers are authoritative instead of duplicate route flags. Dates and local resolved markers replace the retired global milestone flags. Terminal historical state is `linux_system_milestone_stage = 5` together with `linux_system_event_5_resolved`.

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

`linux_system_refresh_usa_adapter` reads IBM and legacy storage outcomes only while Corporate History is enabled. Corporate History Off yields no IBM or storage adapter contribution. Adapter refresh never writes IBM or storage state.

Legacy storage history is governed only by the Corporate History rule. Corporate History Full permits its authored events even when Linux is Off, Outcomes Only reconstructs reached storage history silently, and Corporate History Off leaves storage scheduling and reconstruction inert. When Linux is enabled, it reads the resulting storage state through its adapter. Linux Off does not initialize Linux state through storage events, while Corporate History Off leaves the independent generic Linux base route available.

The one-time storage import preserves an old save's `USA_oem_storage_policy` without continuing to read that legacy scalar. A nonzero legacy value becomes `linux_system_usa_storage_legacy_import_level`, an absolute value clamped from 1 through 2; zero creates no route. Its Upstream route adds that level to Stewardship and supplies Support 1 when base support is Mixed. Its Enterprise route adds that level to Deployment and Assurance and supplies Support 2. The imported marker, level, and route survive Linux Off.

Storage event 18 is not folded into the generic storage adapter groups. Its Enterprise route adds Assurance 1, subtracts Stewardship 1, and supplies Support 2. Its Upstream compatibility route adds Deployment 1 and Stewardship 1, subtracts Assurance 1, and supplies Support 1 when base support is Mixed.

Full-mode generic-event suppression is limited to these native overlaps:

- Event 1: `USA_ibm_event_13_scheduled` or `USA_ibm_event_13_resolved`
- Event 3: `USA_ibm_event_31_scheduled`, `USA_ibm_event_31_resolved`, `USA_oem_storage_event_19_pending`, or `USA_oem_storage_event_19_resolved`
- Event 4: `USA_ibm_event_34_scheduled` or `USA_ibm_event_34_resolved`

Suppression resolves the generic milestone through its Enterprise route and applies that event's durable Enterprise delta only. This preserves any earlier live choice. Event 2 always remains available. Event 5 remains one settlement event after `USA_ibm_event_39_resolved`. Corporate History Off allows every unresolved generic Linux milestone without creating IBM or storage state.

`USA_oem_storage_reconstruct_history` is the only coordinated native-state reconstruction call. The USA monthly owner reaches it whenever Corporate History is enabled. Full calls `USA_oem_storage_schedule_due_events`, which repairs pending deliveries through `USA_oem_storage_recover_pending_events`; Outcomes Only reconstructs without event calls. Linux initialization, dirty markers, and recalculation remain guarded by the Linux rule, so storage history can run without synthesizing Linux state. Off cleanup may clear old pending artifacts for save compatibility, but it may not initialize, schedule, reconstruct, or adapt new storage state.

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

`common/decisions/categories/MD_linux_system_categories.txt` owns the `linux_system_programs` category. The container has exactly four repeatable Full-mode programs. Only one can be active. A decision remains active for its program duration, and its `remove_effect` removes any surviving program idea. The shared slot reopens when that lifecycle ends; no separate post-program cooldown extends the lock. Availability also requires no bankruptcy-collapse mission. Public procurement is not visible to USA.

| Decision                                   |  PP | Treasury | Duration | Durable base change   | Active modifier                                             |
| ------------------------------------------ | --: | -------: | -------: | --------------------- | ----------------------------------------------------------- |
| `linux_system_fund_upstream_maintenance`   |  25 | 0.1% GDP | 180 days | S +1, A +1            | Research +1%; bureaucracy cost +1%                          |
| `linux_system_contract_enterprise_support` |  25 | 0.1% GDP | 180 days | D +1, A +1, Support 2 | Productivity growth +1%; bureaucracy cost -1%               |
| `linux_system_harden_lifecycle`            |  35 | 0.1% GDP | 365 days | A +2                  | Cyber defense +2; bureaucracy cost +1%                      |
| `linux_system_public_procurement`          |  50 | 0.2% GDP | 180 days | D +1, S +1, A +1      | Research +1%; productivity growth +1%; bureaucracy cost +2% |

The treasury helpers are `linux_system_pay_gdp_0_1_percent` and `linux_system_pay_gdp_0_2_percent`. Matching affordability triggers include the bankruptcy guard.

## Source register

Only approved official sources belong in this core reference. National adapter research and repository-native read contracts are recorded in `linux-national-adapters.md`.

| Source                                                                  | Contract use                                          |
| ----------------------------------------------------------------------- | ----------------------------------------------------- |
| https://www.kernel.org/pub/linux/kernel/v2.4/                           | Linux 2.4 archive and the 2001-01-04 milestone anchor |
| https://www.ibm.com/investor/news/ibm-completes-acquisition-of-red-hat  | IBM and Red Hat integration anchor dated 2019-07-09   |
| https://www.ibm.com/support/pages/ibm-powerlinux-backed-linux-community | IBM PowerLinux and Linux community commitment context |
