---
title: Seven-Axis Corporate Strategy Model
description: Design bounded corporate-history state, route transitions, reconstruction, deterministic capstones, AI weighting, dashboards, and tests
---

The seven-axis corporate strategy model is a Tier 1 corporate-history pattern for companies whose long-term identity cannot be represented by one route flag. It turns dated player choices into bounded strategic state, preserves the historical route for later starts, and resolves that state into one permanent capstone.

Huawei is the complete worked example. Its implementation is intentionally independent of China's national semiconductor economy, existing focus rewards, Lenovo's transaction state, and foreign corporate chains.

# When to Use Seven Axes

Use this pattern when a company has all of the following:

- Twelve to fifteen dated choices with meaningful alternative strategies.
- Several strategic dimensions that can move independently.
- A final identity determined by accumulated choices rather than one event flag.
- Full, Outcomes Only, and Off behavior under the Corporate History game rule.
- Enough player-facing state to justify a read-only dashboard.

Prefer Tier 2 when four to six milestones and one outcome flag describe the company adequately. Prefer Tier 3 for one or two flavor events with no persistent state. Extra axes are not free detail: every axis expands localisation, reconstruction, AI, dashboard, and regression-test obligations.

# Axis Design

Each axis should answer a distinct strategic question. Avoid two meters that rise and fall together on nearly every route. Use integer values bounded from 0 to 10 so players can read them directly and thresholds remain easy to audit.

Initialization should represent the company's position before its first visible milestone, not a neutral midpoint by default. Ordinary choices should move an axis by one or two points. A three- or four-point delta should represent a defining commitment and should usually carry a compensating loss elsewhere.

The company owns its variables, route flags, era ideas, capstone ideas, and reconstruction marker. Other systems may read that state only when the machine-readable contract declares the dependency. They must not duplicate or overwrite it.

# Persistent and Transient State

Reconstruction reproduces durable strategic history, not missed rewards.

| Reconstructable | Visible-event-only |
| --- | --- |
| Route flag | Treasury change |
| Bounded axis delta | Political Power |
| Era transition | Research bonus |
| Capstone selection | Timed burden |
| Initialization and completion markers | GPU-demand refresh |
| Clamp and resolver state | Opinion, buildings, events, and other one-shots |

Every historical step must:

1. Check its date.
2. Require that none of its sibling route flags is set.
3. Set the historical route flag.
4. Apply only permanent deltas and the relevant era transition.
5. Clamp every bounded value.

Reapplying initialization, a historical step, reconstruction, or capstone resolution must change nothing after its state is already present. If the framework cannot reconstruct the remaining duration of a temporary burden exactly, omit the burden instead of granting a fresh full-duration penalty.

# Era and Capstone Lifecycles

Era ideas describe the company's current phase. Every era setter first removes every competing era. Every choice at an era boundary calls the new setter, including nonhistorical routes, so alternatives cannot leave a stale phase active.

Capstones replace eras. Every capstone applicator removes all eras and all competing capstones before adding exactly one outcome. `has_idea` is authoritative; do not create flags that merely duplicate which outcome idea is active.

Several outcomes may qualify simultaneously. Silent reconstruction therefore uses a documented priority ladder. A visible capstone event may show every qualified threshold outcome to the player, but its AI weighting must follow the same priority. The fallback is available only when none of the threshold outcomes qualifies.

# Full, Outcomes Only, and Off

- **Full:** reconstruct already-passed milestones, schedule only the exact January 1 start year's future milestones, and display later events normally. A bounded monthly recovery may repair a missed terminal outcome after its visible window.
- **Outcomes Only:** never display a corporate story event. Reconstruct the historical route at startup and monthly until the terminal marker is set.
- **Off:** do not initialize variables, schedule events, reconstruct state, add ideas, or expose dashboard entries.

The start year's annual dispatcher does not run. A current-year scheduler therefore handles exact January 1 starts. Non-January starts reconstruct passed milestones and deliberately skip the remainder of that start year rather than applying January-based offsets to the wrong date.

# AI Weighting

Historical AI should be deterministic unless its historical option is financially impossible. Give the historical route a strong positive multiplier and zero the alternatives. Every treasury-spending option separately receives a zero factor during `bankruptcy_incoming_collapse`.

If the historical option spends treasury, keep one affordable alternative positive during bankruptcy. Otherwise all options can reach zero and the engine no longer has a valid strategic choice.

Nonhistorical AI may read current axes and completed focuses for preference only. Use modest, grouped multipliers. A completed focus must never make an option available, resolve a milestone, or alter reconstruction. Group related focuses inside one `OR` block to prevent late-game multiplier explosions.

Keep the read set explicit in the machine-readable contract and regression test. Test historical, nonhistorical, and bankrupt contexts separately. For an expensive historical option, verify both that bankruptcy disables the cost and that one intended fallback remains positive; a merely nonzero fallback is not enough when another alternative can receive a larger contextual multiplier.

# Dashboard Presentation

A seven-axis dashboard is read-only. Display each value as an integer out of 10, then show the current era and exact resolved capstone. Resolve era and outcome text from ideas instead of caching duplicate variables or flags. Keep unresolved and not-initialized states explicit.

Do not present a predicted capstone as certain. If a directional tendency is useful, label it as non-binding because later choices and priority overlap can change the result.

# Huawei Worked Example

## Initial State

| Abbreviation | Axis | Initial |
| --- | --- | ---: |
| CR | Carrier Reach | 4 |
| SL | Standards Leverage | 2 |
| CP | Consumer Position | 1 |
| SA | Silicon Autonomy | 2 |
| SE | Software Ecosystem | 2 |
| SR | Supply Resilience | 3 |
| TM | Trusted Market Access | 5 |

All seven values are clamped to 0 through 10 after every visible route and historical step.

## Milestone Routes

Option A is historical in every ordinary milestone.

| Event | A flag and delta | B flag and delta | C flag and delta |
| ---: | --- | --- | --- |
| 1 | `CHI_huawei_global_rnd_network`: CR +1, SL +1, TM +1 | `CHI_huawei_domestic_network_priority`: CR +1, SR +1, TM -1 | `CHI_huawei_acquisition_led_expansion`: CR +2, CP +1, SR -1 |
| 2 | `CHI_huawei_h3c_exit`: CR +1, SR +1 | `CHI_huawei_h3c_control`: SE +1, CP +1, SR -1 | `CHI_huawei_open_enterprise_networking`: SL +2, TM +1, CR -1 |
| 3 | `CHI_huawei_symantec_joint_stack`: SL +1, SE +1, TM +1 | `CHI_huawei_carrier_pure_play`: CR +1, SR +1, SE -1 | `CHI_huawei_internal_security_storage`: SE +2, SR +1, TM -1 |
| 4 | `CHI_huawei_lte_scale_leadership`: CR +1, SL +1, TM +1 | `CHI_huawei_lte_standards_licensing`: SL +2, SE +1 | `CHI_huawei_lte_trusted_market_model`: TM +2, CR +1, SR -1 |
| 5 | `CHI_huawei_integrated_ict_group`: SE +1, SR +1 | `CHI_huawei_carrier_network_core`: CR +2, CP -1 | `CHI_huawei_consumer_first_reorganization`: CP +2, SE +1, TM -1 |
| 6 | `CHI_huawei_global_assurance_response`: SR +1, TM -2 | `CHI_huawei_us_ringfence`: TM +1, SR +1, CR -1 | `CHI_huawei_confrontational_substitution`: SA +1, SR +2, TM -3 |
| 7 | `CHI_huawei_5g_moonshot`: CR +1, SL +2 | `CHI_huawei_open_interoperability_5g`: SL +2, TM +1, SE +1 | `CHI_huawei_cloud_enterprise_priority`: SE +2, CP +1, SL -1 |
| 8 | `CHI_huawei_premium_consumer_kirin`: CP +3, SA +2 | `CHI_huawei_honor_mass_market`: CP +4, SR -1, TM -1 | `CHI_huawei_carrier_device_ecosystem`: CR +1, CP +2, SE +1 |
| 9 | `CHI_huawei_device_cloud_chip_stack`: CP +1, SA +1, SE +2 | `CHI_huawei_open_cloud_partnership`: TM +1, SE +2, SR -1 | `CHI_huawei_mobile_ai_specialization`: SA +2, CP +1, SL -1 |
| 10 | `CHI_huawei_full_stack_ai`: SL +1, SA +1, SE +1 | `CHI_huawei_separated_business_discipline`: SR +1, TM +1 | `CHI_huawei_open_ai_ecosystem`: SE +2, TM +1, SL -1 |
| 11 | `CHI_huawei_continuity_legal_defense`: SR +2, TM -3 | `CHI_huawei_compliance_settlement`: TM +2, SL -1, SA -1 | `CHI_huawei_domestic_market_retreat`: SR +2, SA +1, CR -2, TM -2 |
| 12 | `CHI_huawei_harmony_hms_full_ecosystem`: CP +1, SE +2, TM -1 | `CHI_huawei_openharmony_federation`: SE +2, SL +1, TM +1, CP -1 | `CHI_huawei_android_compatibility_bridge`: TM +2, CP +1 |
| 13 | `CHI_huawei_honor_divested_core_preserved`: CP -2, SA +1, SR +1 | `CHI_huawei_honor_retained_rationed`: CP +1, SR -2, SA -1 | `CHI_huawei_consumer_stack_spun_out`: SR +2, SE +1, CP -1, TM -1 |
| 14 | `CHI_huawei_mate60_full_stack_return`: CP +2, SA +2, SR +1 | `CHI_huawei_cautious_yield_ramp`: SA +1, SR +2, CP -1 | `CHI_huawei_ascend_cloud_redirection`: SA +2, SE +1, SL -1 |

The historical A route ends at `(8, 8, 6, 9, 9, 10, 2)` in CR, SL, CP, SA, SE, SR, TM order.

## Delivery Dates

| Event | Date | January 1 offset | Delivery |
| ---: | --- | ---: | --- |
| 1 | 2000-06-15 | 166 | Startup scheduler only |
| 2 | 2006-11-28 | 331 | 2006 aggregate and scheduler |
| 3 | 2007-05-22 | 141 | 2007 aggregate and scheduler |
| 4 | 2009-12-14 | 347 | 2009 aggregate and scheduler |
| 5 | 2011-11-14 | 317 | 2011 aggregate and scheduler |
| 6 | 2012-10-08 | 281 | 2012 aggregate and scheduler |
| 7 | 2013-11-06 | 309 | 2013 aggregate and scheduler |
| 8 | 2016-04-06 | 96 | 2016 aggregate and scheduler |
| 9 | 2017-09-02 | 244 | 2017 aggregate and scheduler |
| 10 | 2018-10-10 | 282 | 2018 aggregate and scheduler |
| 11 | 2019-05-16 | 135 | 2019 aggregate and scheduler |
| 12 | 2019-08-09 | 220 | 2019 aggregate and scheduler |
| 13 | 2020-11-17 | 321 | 2020 aggregate and scheduler |
| 14 | 2023-09-03 | 245 | 2023 aggregate and scheduler |
| 15 | 2026-03-31 | 89 | 2026 aggregate and scheduler |

There is no 2000 annual corporate dispatcher. Event 1 is startup-scheduler-only.

## Mode Data Flow

| Mode and start | Huawei flow |
| --- | --- |
| Full, exact January 1 | Reconstruct milestones whose dates have passed, schedule the current year's unelapsed events, then queue hidden reconstruction anchor `.90` for day 3 |
| Full, non-January | Reconstruct passed milestones synchronously; do not schedule the remainder of that start year with incorrect January offsets |
| Full, after 2026-03-31 | Resolve the historical capstone synchronously with no backdated popup and set the terminal marker |
| Full, missed visible capstone | After the April grace window, monthly recovery reconstructs once; a visible selection remains authoritative and the recovery records completion without replacing it |
| Outcomes Only | Reconstruct independently beside Lenovo at startup and monthly until `CHI_huawei_reconstruct_complete` exists; never queue a popup |
| Off | Create no Huawei variables, route flags, ideas, events, terminal state, or dashboard surface |

The visible event 15 sets `CHI_huawei_capstone_resolved` through its selected capstone applicator. It deliberately does not write `CHI_huawei_reconstruct_complete`; reconstruction is the sole producer and records completion after the visible-event grace window.

## Visible One-Shots

Research bonuses have one use. Treasury values are billions.

| Event | A | B | C |
| ---: | --- | --- | --- |
| 1 | Internet 0.10 | Industry 0.10 | Treasury -4; Computing 0.15 |
| 2 | Treasury +2 | Treasury -3; Computing 0.15 | Internet 0.15 |
| 3 | Encryption 0.10 | Industry 0.10 | Treasury -4; Encryption 0.15 |
| 4 | Internet 0.10 | Internet 0.15; Political Power +5 | Treasury -3; Security Scrutiny 730 days |
| 5 | Computing 0.10 | Internet 0.10 | Treasury -3; Computing 0.15 |
| 6 | Security Scrutiny 1,095 days | Security Scrutiny 730 days | Encryption 0.10; Security Scrutiny 1,460 days |
| 7 | Treasury -4; Internet 0.15 | Internet 0.10; Political Power +5 | Computing 0.15 |
| 8 | Microchips 0.15 | Treasury +2 | Computing 0.10 |
| 9 | AI 0.10 | Computing 0.15 | AI 0.15 |
| 10 | AI 0.15; GPU-demand refresh | Computing 0.10; Political Power +5 | Internet 0.15 |
| 11 | Entity List Shock 1,825 days | Treasury -3; Political Power -10; shock 730 days | Microchips 0.15; shock 1,460 days |
| 12 | Computing 0.15; Ecosystem Migration 1,460 days | Internet 0.15; migration 730 days | Internet 0.10; migration 365 days |
| 13 | Treasury +1; Foundry Chokepoint 1,825 days | Treasury -2; chokepoint 2,555 days | Treasury +2; chokepoint 1,095 days |
| 14 | Microchips 0.15; Domestic Yield Ramp 1,095 days | Microchips 0.10; yield ramp 730 days | AI 0.15; GPU-demand refresh |

## Eras and Burdens

| Era | Modifiers |
| --- | --- |
| Global Telecom Challenger | Offices +3%; research speed +1% |
| Integrated ICT Champion | Offices +5%; production-efficiency gain +3%; research speed +2% |
| Contested Technology Champion | Cyber defense rating +2; research speed +3%; consumer goods +1% |
| Full-Stack Return | Research speed +4%; industry chip consumption -3%; production-efficiency gain +3% |

| Burden | Modifiers |
| --- | --- |
| Security Scrutiny | Offices -3%; foreign-influence defense -5% |
| Entity List Shock | Microchip export -10%; maximum production efficiency -3%; consumer goods +1% |
| Ecosystem Migration | Offices -3%; civilian chip consumption +5% |
| Foundry Chokepoint | Industry chip consumption +8%; microchip export -10%; production-efficiency gain -5% |
| Domestic Yield Ramp | Industry chip consumption +4%; maximum production efficiency -2%; research speed +2% |

## Capstone Priority

| Priority | Outcome | Qualification | Modifiers |
| ---: | --- | --- | --- |
| 1 | Global Connectivity Federation | CR 8+, SL 8+, TM 7+ | Offices +6%; Political Power +4%; foreign-influence defense +5% |
| 2 | Consumer Ecosystem Power | CP 8+, SE 8+ | Offices +7%; microchip export +6%; consumer goods -1% |
| 3 | Carrier Cloud Utility | CR 9+, SE 7+, SA 6 or lower | Offices +5%; production-efficiency gain +5%; industry chip consumption -4% |
| 4 | Patent Standards House | SL 9+ | Research speed +5%; Political Power +5%; microchip export +4% |
| 5 | Sovereign Full Stack | SA 7+, SE 7+, SR 6+ | Research speed +5%; cyber defense rating +3; civilian and industry chip consumption -4% |
| 6 | Resilient Technology Fortress | Fallback | Cyber defense rating +4; foreign-influence defense +10%; research speed +3%; consumer goods +2% |

Representative routes prove every outcome is reachable and exercise priority overlap:

| Outcome | Route | Final state |
| --- | --- | --- |
| Global Connectivity | `AAAAAAAAAABBAA` | `(8, 8, 4, 8, 9, 8, 9)` |
| Consumer Ecosystem | `AAAAAAAAAAAABA` | `(8, 8, 9, 7, 9, 7, 2)` |
| Carrier Cloud | `AAAAAAACAAAAAB` | `(9, 8, 2, 6, 10, 10, 2)` |
| Patent Standards | `AAAAAAAAAAABAA` | `(8, 9, 4, 9, 9, 10, 4)` |
| Sovereign Full Stack | `AAAAAAAAAAAAAA` | `(8, 8, 6, 9, 9, 10, 2)` |
| Resilient Fortress | `AAAAAAAAAAAABB` | `(8, 8, 6, 6, 9, 8, 2)` |

## Huawei AI Context

Huawei reads ten existing Chinese national focuses as preference-only context. Carrier and global routes group `CHI_Digital_Silk_Road` with `CHI_huawei_zte_export`; integration routes read `CHI_hisilicon_kirin`; cloud and AI routes read `CHI_cloud_computing_triumvirate`. Events 13 and 14 group `CHI_smic_advanced_node`, `CHI_domestic_eda`, `CHI_smee_lithography`, and `CHI_sicarrier_euv` in one autonomy `OR`, while `CHI_hua_hong_mature_node` and `CHI_mature_node_counter_offensive` form the cautious-resilience `OR`. These focuses affect weights only.

# Implementation Checklist

1. Register the namespace, owned prefix, axes, outcomes, callers, reads, terminal date, and monthly driver in `tools/corporate_history_contract.json`.
2. Implement initialization, clamping, era setters, capstone applicators, resolver, historical steps, reconstruction, and current-year scheduling in the company wrapper.
3. Wire Full and Outcomes Only startup, annual aggregates, and independent monthly completion guards.
4. Keep all events triggered-only and give every effectful option an exact log and explicit effect tooltip.
5. Put every country-specific string in the unified English localisation file and preserve its UTF-8 BOM.
6. Add a read-only dashboard only after the underlying state exists.
7. Add delivery scenarios plus parser-backed tests for arithmetic, clamps, priority, idempotence, callers, AI affordability, and reconstruction safety.
8. Verify the exact pushed CI head. Record natural HOI4 runtime separately.

# Regression-Test Template

Use parser-backed assertions against the real event, effect, trigger, idea, dispatch, and contract files rather than maintaining a second hand-authored simulation alone.

| Contract facet | Required assertion |
| --- | --- |
| Initialization | Exact initial vector; every variable has 0-10 bounds and reaches the shared clamp |
| Routes | Exactly three sibling flags per ordinary milestone; each of the 42 route blocks applies its declared delta then clamps |
| Historical reconstruction | Historical vector is exact; a second initialization, step, reconstruction, and resolution pass is a no-op |
| Permanent/transient boundary | Reconstruction call graph contains no treasury, Political Power, research bonuses, timed ideas, GPU refreshes, buildings, or event calls |
| Capstones | Every representative vector reaches its expected threshold result; overlapping qualifications obey priority; exactly one idea survives |
| Delivery | No invented annual caller; all dates and offsets match; same-year dual events have independent guards |
| AI | Ordinary bases and historical multipliers are exact; every negative-treasury route has a bankruptcy guard; every tested context retains a positive legal choice |
| Contract and dashboard | Focus reads equal the declared allowlist; dashboard values are read-only and derive era/outcome text from authoritative state |
| Evidence | Static, CI, console-fixture, and natural-runtime results are recorded as separate evidence classes |

For each representative route string, start from the declared initial vector, apply one delta per character, clamp after every step, assert the terminal vector, then run the same priority resolver used by script. Include at least one vector per capstone and at least one overlapping-qualification case.

# Source and Attribution Notes

Use primary or clearly attributed technical sources for dated claims. The H3C sale is supported by the [3Com SEC filing](https://www.sec.gov/Archives/edgar/data/738076/000095013506007143/b63210cme8vk.htm). The 2019 restrictions are grounded in the [official BIS Entity List rule](https://www.bis.gov/84-fr-22961-addition-entities-entity-list). Describe the Mate 60 chip as a [TechInsights teardown finding](https://www.techinsights.com/blog/techinsights-finds-smic-7nm-n2-huawei-mate-60-pro), not proof of national semiconductor self-sufficiency. Attribute the 2025 figures to Huawei's [annual-report release](https://www.huawei.com/en/news/2026/3/annual-report-2025).

# Evidence Boundaries

Static validators establish script and localisation structure. CI establishes that the exact pushed head passes repository gates. Console fixtures can establish event rendering and one option execution. Only a natural HOI4 campaign establishes calendar timing, save and reload behavior, AI selection, dashboard rendering, and long-running interaction with other systems. Never present one evidence class as another.
