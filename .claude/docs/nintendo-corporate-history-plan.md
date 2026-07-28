# Nintendo Corporate-History Implementation Plan

## Purpose and boundaries

This document defines a Tier 1 corporate-history chain for Nintendo before any
gameplay implementation begins. The chain belongs to Japan, models public policy
around a privately directed entertainment company, and must not let the Japanese
government directly dictate Nintendo's product decisions.

This design reserves:

- Event namespace: `JAP_nintendo_events`
- Root prefix: `JAP_nintendo`
- Canonical owner: `JAP`
- Visible events: `JAP_nintendo_events.1` through `.15`
- Hidden startup event: `JAP_nintendo_events.90`

The implementation must not create a separate country, tag, MIO, character, or
decision category for Nintendo. It must not reuse the existing
`nintendo_world_domination` achievement identifiers or the `JAP_games_are_fun`
focus identifiers. English text belongs in the unified
`localisation/english/MD_focus_JAP_l_english.yml`.

## Repository findings

Nintendo currently appears in two player-facing systems:

- `JAP_games_are_fun` treats Nintendo and Sony as parts of Japan's broader
  entertainment industry.
- `nintendo_world_domination` is an achievement identifier.

No Nintendo event namespace, ideas, variables, MIO, characters, or decisions
exist. The neighboring Sony chain provides the relevant Japanese architecture:
startup dispatch through `corporate_history_on_startup`, annual dispatch effects,
silent reconstruction, and the single `JAP_corporate_history_monthly_outcomes`
hook. Japanese GPU history and the Sony chain already demonstrate guarded reads
of foreign or sibling state.

The future chain may reuse only verified generic picture categories already used
by neighboring event files: `GFX_computer`, `GFX_generic_factory`,
`GFX_stock_market`, `GFX_trade_agreement`, and `GFX_cyber_attack`. Picture
selection remains an implementation-time content review. No new picture or
binary asset is part of the chain.

## State model

All variables are country variables owned by Japan and clamped after every
mutation and reconstruction pass.

| Variable                           | Initial |  Bounds | Meaning                                                                                                                                |
| ---------------------------------- | ------: | ------: | -------------------------------------------------------------------------------------------------------------------------------------- |
| `JAP_nintendo_platform_strength`   |       4 | 0 to 10 | Installed-base durability, platform identity, and the ability to carry users between hardware generations.                             |
| `JAP_nintendo_developer_ecosystem` |       4 | 0 to 10 | Internal studio capacity plus the quality, accessibility, and diversity of third-party development support.                            |
| `JAP_nintendo_digital_services`    |       0 | 0 to 10 | Account infrastructure, distribution, online operations, subscriptions, and digital customer relationships.                            |
| `JAP_nintendo_ip_reach`            |       5 | 0 to 10 | Nintendo intellectual property's reach outside dedicated games through mobile, location-based media, film, and physical entertainment. |
| `JAP_nintendo_hardware_resilience` |       4 | 0 to 10 | Supply-chain depth, architecture continuity, manufacturability, and the capacity to absorb a failed generation.                        |

Required effects:

- `JAP_nintendo_initialize_state`
- `JAP_nintendo_clamp_state`
- `JAP_nintendo_reconstruct_history`
- `JAP_nintendo_schedule_current_year_events`
- `JAP_nintendo_recover_missing_events`
- `JAP_nintendo_advance_startup_skipped`
- `JAP_nintendo_clear_capstone_outcome`
- `JAP_nintendo_apply_integrated_entertainment_ecosystem`
- `JAP_nintendo_apply_hardware_platform_sovereignty`
- `JAP_nintendo_apply_open_developer_commonwealth`
- `JAP_nintendo_apply_global_ip_licensor`
- `JAP_nintendo_apply_disciplined_hybrid_platform`
- `JAP_nintendo_resolve_capstone`

Required framework flags:

- `JAP_nintendo_state_initialized`
- `JAP_nintendo_reconstruct_complete`
- `JAP_nintendo_start_year_events_scheduled`
- `JAP_nintendo_capstone_resolved`

Each visible event also owns one resolved marker,
`JAP_nintendo_event_<N>_resolved`, set in `immediate`, plus corresponding
`JAP_nintendo_event_<N>_delivery_expected`,
`JAP_nintendo_event_<N>_startup_skipped`, and
`JAP_nintendo_event_<N>_pending` markers. A scheduling site sets the persistent
delivery-expected flag and timed pending flag before queuing the event, keeping
the latter alive beyond the intended delivery date. The event's `immediate`
clears both scheduling markers while setting the resolved marker. If delivery
is lost, pending expiry leaves the delivery-expected evidence needed for
recovery. An off-January startup instead sets startup-skipped without setting
delivery-expected; after the milestone date, reward-free reconstruction clears
startup-skipped and resolves it silently. Each option owns a descriptive path
flag under `JAP_nintendo_`.
Reconstruction selects the first listed choice as the canonical historical path
only when no mutually exclusive option flag already exists.

## Event chronology

Variable shorthand in the table is `P` platform strength, `D` developer
ecosystem, `S` digital services, `I` IP reach, and `H` hardware resilience.
Dates use the historical milestone in Japan unless stated otherwise.

| ID and date                                                               | Purpose and state policy mechanism                                                                                                                                                                                                         | Three choice concepts and state direction                                                                                                                                                                                                                                                           | Persistent marker and later consequence                                                                                                                                                      | Picture category      | Research needed                                                                                                                          |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `.1`, 2001.09.14, `days = 256`: Game Boy Advance and GameCube             | Establish the dual handheld/home-console baseline. Japan can support supplier credit, shared component research, or export promotion without choosing Nintendo's product mix.                                                              | **Dual-platform industrial credit:** P+1, H+2. **Developer transition grants:** D+2, P+1. **Export-led launch support:** I+1, P+2, H-1.                                                                                                                                                             | `JAP_nintendo_dual_platform_generation`, `JAP_nintendo_developer_transition`, or `JAP_nintendo_export_launch`. Shapes the DS, Wii, and later platform-continuity options.                    | `GFX_computer`        | Confirm the earlier 2001.03.21 Japanese GBA launch from a primary Nintendo record.                                                       |
| `.2`, 2004.12.02, `days = 336`: Nintendo DS                               | Model touch, wireless, and dual-screen development as an ecosystem decision. METI may fund interface research, small-studio tooling, or manufacturing scale.                                                                               | **Interface research consortium:** D+2, I+1. **Accessible developer program:** D+3, H-1. **Mass-market production finance:** P+2, H+2, D-1.                                                                                                                                                         | `JAP_nintendo_ds_interface_research`, `JAP_nintendo_ds_developer_program`, or `JAP_nintendo_ds_scale`. Influences Wii accessibility and future open-developer eligibility.                   | `GFX_computer`        | Confirm the relevant contemporary Japanese digital-content and manufacturing programs.                                                   |
| `.3`, 2006.12.02, `days = 335`: Wii                                       | Represent the broad-audience strategy and supply pressure created by rapid demand. Government tools are export finance, accessibility research, and supplier-capacity support.                                                             | **Expand accessible play:** I+2, P+2. **Deepen motion-interface research:** D+2, P+1. **Secure component capacity:** H+3, P+1, S-1.                                                                                                                                                                 | `JAP_nintendo_wii_accessibility`, `JAP_nintendo_wii_interface_program`, or `JAP_nintendo_wii_supply_program`. Affects the recovery path and sovereign-hardware capstone.                     | `GFX_generic_factory` | Confirm suitable evidence for Japanese supply constraints.                                                                               |
| `.4`, 2008.11.01, `days = 305`: DSi and digital distribution              | Introduce downloadable software, accounts, and storefront governance. Policy choices cover digital-market rules, regional infrastructure, or conservative consumer protection.                                                             | **Fund digital distribution:** S+3, D+1. **Open a small-studio storefront:** S+2, D+2, P-1. **Regulate cautiously:** H+1, S+1, I-1.                                                                                                                                                                 | `JAP_nintendo_dsi_distribution`, `JAP_nintendo_dsi_open_storefront`, or `JAP_nintendo_dsi_cautious_rollout`. Conditions Switch Online and digital-commonwealth eligibility.                  | `GFX_computer`        | Verify the DSi Shop's account architecture and payment operations.                                                                       |
| `.5`, 2011.07.28, `days = 208`: 3DS price crisis                          | Cover the announced price reduction and Ambassador Program as a platform-confidence crisis. Government action is limited to supplier/workforce support, consumer remedies, or non-intervention.                                            | **Protect suppliers and employment:** H+2, P+1, S-1. **Back the consumer remedy:** P+2, S+1, H-1. **Require market discipline:** D+1, H+1, P-2.                                                                                                                                                     | `JAP_nintendo_3ds_supplier_support`, `JAP_nintendo_3ds_consumer_remedy`, or `JAP_nintendo_3ds_market_discipline`. Determines how much fiscal or industrial support is available after Wii U. | `GFX_stock_market`    | Separate company-funded remedies from plausible state support.                                                                           |
| `.6`, 2012.12.08, `days = 342`: Wii U                                     | Model the costly transition to a weakly differentiated platform. The state may support component restructuring, developer access, or leave the company to consolidate.                                                                     | **Restructure the hardware base:** H+2, P-1. **Subsidize developer conversion:** D+3, P+1, H-1. **Decline a rescue:** H+1, P-2, I+1.                                                                                                                                                                | `JAP_nintendo_wii_u_restructured`, `JAP_nintendo_wii_u_developer_bridge`, or `JAP_nintendo_wii_u_no_rescue`. Opens different recovery instruments and preserves a real failure path.         | `GFX_stock_market`    | Confirm third-party support problems and avoid implying a historical government bailout.                                                 |
| `.7`, 2013.01.31, `days = 30`: Recovery and internal development          | Represent the announced consolidation of handheld and home-console development after the weak Wii U launch. Policy instruments are R&D tax credits, training, or IP commercialization support.                                             | **Integrate hardware R&D:** H+2, D+1. **Build internal studio capacity:** D+3, I+1. **Commercialize established IP:** I+3, P+1, D-1.                                                                                                                                                                | `JAP_nintendo_integrated_hardware_rnd`, `JAP_nintendo_internal_studio_program`, or `JAP_nintendo_ip_recovery`. Feeds Switch architecture and the IP-licensor route.                          | `GFX_generic_factory` | Verify the effective date and scope of Nintendo's development reorganization after its January 31 policy briefing.                       |
| `.8`, 2015.03.17, `days = 75`: DeNA and mobile services                   | Treat the DeNA alliance as an account, service, and mobile-distribution decision rather than a transfer of Nintendo IP control. Government tools are interoperability standards, investment review, or mobile-sector support.              | **Build a shared service backbone:** S+3, D+1. **Keep Nintendo accounts sovereign:** H+1, S+2, P+1. **Use mobile as an IP funnel:** I+3, S+1, P-1.                                                                                                                                                  | `JAP_nintendo_dena_service_backbone`, `JAP_nintendo_dena_sovereign_accounts`, or `JAP_nintendo_dena_ip_funnel`. Controls later satellite/mobile and subscription options.                    | `GFX_trade_agreement` | Confirm cross-shareholding and which account services were assigned to each company.                                                     |
| `.9`, 2015.09.16, `days = 258`: Leadership after Iwata                    | Model succession and governance continuity after Satoru Iwata's death. The state may offer continuity support, governance reform incentives, or a broader creative-industry compact.                                                       | **Prioritize operational continuity:** H+2, P+1. **Support governance renewal:** D+2, S+1. **Create a creative-industry compact:** I+2, D+1, H-1.                                                                                                                                                   | `JAP_nintendo_kimishima_continuity`, `JAP_nintendo_governance_renewal`, or `JAP_nintendo_creative_industry_compact`. Modifies Switch launch readiness and capstone availability.             | `GFX_stock_market`    | Distinguish the September 14 appointment announcement from the September 16 management transition.                                       |
| `.10`, 2016.07.22, `days = 203`: Mobile and location-based IP             | Use Nintendo's Pokémon GO disclosure as evidence of location-based IP reach while preserving The Pokémon Company and Niantic's separate ownership. Policy tools are public-space coordination, safety rules, and location-tech research.   | **Coordinate public-space deployment:** I+2, S+1. **Fund location-platform research:** S+2, D+1, I+1. **Apply strict safety limits:** H+1, I+1, S-1.                                                                                                                                                | `JAP_nintendo_location_ip_coordination`, `JAP_nintendo_location_platform_research`, or `JAP_nintendo_location_safety_rules`. Influences theme-park and global-IP outcomes.                   | `GFX_computer`        | Preserve Nintendo, The Pokémon Company, and Niantic's separate responsibilities.                                                         |
| `.11`, 2017.03.03, `days = 61`: Nintendo Switch                           | Resolve whether hybrid hardware becomes an integrated platform, a supplier-led resilience program, or a developer-first ecosystem. State tools are manufacturing credit, export support, and development grants.                           | **Scale the integrated platform:** P+3, S+1, H+1. **Secure the hardware chain:** H+3, P+1, D-1. **Open the hybrid ecosystem:** D+3, P+1, S+1.                                                                                                                                                       | `JAP_nintendo_switch_integrated_platform`, `JAP_nintendo_switch_supply_resilience`, or `JAP_nintendo_switch_open_ecosystem`. Principal gate for three terminal outcomes.                     | `GFX_computer`        | Verify supplier relationships and use only guarded, declared supplier-state reads.                                                       |
| `.12`, 2018.09.19, `days = 261`: Nintendo Switch Online                   | Establish paid subscriptions, account continuity, cloud saves, and legacy-catalog policy. Government mechanisms are service-resilience standards, consumer portability rules, or domestic cloud support.                                   | **Build a durable subscription service:** S+3, P+1. **Require portability and developer access:** D+2, S+2, P-1. **Prioritize domestic service resilience:** H+2, S+2.                                                                                                                              | `JAP_nintendo_online_subscription`, `JAP_nintendo_online_portability`, or `JAP_nintendo_online_resilience`. Determines digital-services and open-commonwealth qualification.                 | `GFX_cyber_attack`    | Confirm the Japanese launch timestamp and limits of cloud-save coverage.                                                                 |
| `.13`, 2021.03.18, `days = 76`: Super Nintendo World                      | Treat physical entertainment as an IP-export and regional-development question. Government tools are tourism infrastructure, licensing support, or domestic creative-cluster investment.                                                   | **Back tourism infrastructure:** I+3, H+1. **Standardize global licensing:** I+2, S+1, P+1. **Reinvest in domestic creative clusters:** D+2, I+2.                                                                                                                                                   | `JAP_nintendo_theme_park_tourism`, `JAP_nintendo_global_licensing_framework`, or `JAP_nintendo_creative_cluster_reinvestment`. Opens film and global-IP capstone routes.                     | `GFX_trade_agreement` | Confirm ownership and investment shares between Nintendo and Universal.                                                                  |
| `.14`, 2023.04.28, `days = 117`: The Super Mario Bros. Movie              | Model the Japanese theatrical release as a choice between tightly supervised adaptation, broad licensing, or reinvestment in game development. State tools are co-production incentives and export promotion.                              | **Support supervised co-production:** I+3, P+1. **Expand global licensing:** I+3, S+1, H-1. **Recycle proceeds into studios:** D+3, I+1.                                                                                                                                                            | `JAP_nintendo_film_supervision`, `JAP_nintendo_global_media_licensing`, or `JAP_nintendo_film_studio_reinvestment`. Final input to IP, integrated-ecosystem, and developer outcomes.         | `GFX_trade_agreement` | Confirm the Japanese release from a primary record and Nintendo's production/governance role.                                            |
| `.15`, 2025.06.05, `days = 155`: Current platform transition and capstone | Use the Switch 2 launch as the final test of platform continuity, supply depth, digital migration, developer access, and IP expansion. The event resolves one national industrial strategy rather than forecasting an unannounced product. | **Integrated entertainment ecosystem:** requires P>=8, S>=7, I>=7. **Hardware platform sovereignty:** requires H>=8, P>=7. **Open developer commonwealth:** requires D>=8, S>=6. **Global IP licensor:** requires I>=9. **Disciplined hybrid platform:** always available as the balanced fallback. | Sets `JAP_nintendo_capstone_resolved`, one terminal path flag, and exactly one outcome idea. The chosen idea terminates all scheduling and reconstruction.                                   | `GFX_computer`        | Refresh launch performance and supply architecture immediately before implementation; treat all strategic outcomes as alternate history. |

## Capstone outcomes

Every capstone option removes the other four ideas before adding its own. The
event sets one matching path flag and `JAP_nintendo_capstone_resolved`. No other
event may award these ideas.

| Idea                                              | Narrative identity                                                                                           | Mechanical identity                                                                                                                   |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `JAP_nintendo_integrated_entertainment_ecosystem` | Hardware, accounts, services, and owned IP operate as one durable platform.                                  | Broad platform and digital-service benefits with moderate research and consumer-industry support; highest combined-state requirement. |
| `JAP_nintendo_hardware_platform_sovereignty`      | Japan prioritizes resilient hardware architecture, manufacturing continuity, and protected platform control. | Strong production, supply-resilience, and electronics-research benefits at the cost of weaker openness and licensing reach.           |
| `JAP_nintendo_open_developer_commonwealth`        | Tooling, portability, and third-party access become the platform's strategic center.                         | Strong research-sharing and software-development benefits with lower direct platform-control bonuses.                                 |
| `JAP_nintendo_global_ip_licensor`                 | Nintendo becomes the anchor of a global film, mobile, attraction, and licensing network.                     | Strong trade, tourism, cultural influence, and service-economy benefits with limited hardware bonuses.                                |
| `JAP_nintendo_disciplined_hybrid_platform`        | Nintendo preserves a balanced hybrid platform without committing the state to one maximal strategy.          | Smaller balanced benefits, low upkeep, and no extreme specialization; this is the deterministic fallback.                             |

In Full mode the player may choose any eligible outcome. In reconstruction and
Outcomes Only, resolve deterministically in the table order above, then use the
fallback. This precedence makes repeated reconstruction idempotent.

## Cross-chain API

All external state is read-only. A foreign read must first guard
`country_exists = TAG`, enter the owning country scope, test the exact flag, and
fall back to a neutral branch if the country or flag is absent. Nintendo must
never set, clear, or mutate any identifier in this table.

Reward-free reconstruction must not consume these foreign reads. It derives
every historical choice and the reconstructed capstone solely from
Nintendo-owned path markers and bounded variables, using the canonical choice
and outcome precedence above. Foreign reads may affect a visible event's
availability, AI weighting, or contextual effects when that event occurs in
live play, but they may not change a silently reconstructed outcome. This keeps
reconstruction deterministic and independent of whether Sony, GPU, NVIDIA,
TSMC, or E3 startup work has already completed.

| Exact read                              | Owner                | Nintendo context                                                                                  |
| --------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------- |
| `JAP_sony_playstation_platform`         | Sony                 | Measures domestic console-platform competition when scaling Wii, Switch, and the final ecosystem. |
| `JAP_sony_open_media_ecosystem`         | Sony                 | Supports open-media and interoperability context for digital distribution.                        |
| `JAP_sony_ps5_platform_scale`           | Sony                 | Calibrates the 2025 platform-transition environment.                                              |
| `JAP_gpu_2001_foundry_priority`         | Japanese GPU history | Improves early domestic component and hardware-resilience options.                                |
| `JAP_gpu_2001_systems_priority`         | Japanese GPU history | Improves developer and systems-integration options.                                               |
| `JAP_gpu_2020_foundry_resilience`       | Japanese GPU history | Supports sovereign hardware and supply-resilience eligibility.                                    |
| `JAP_gpu_2020_fiscal_restraint`         | Japanese GPU history | Strengthens the disciplined fallback and limits unconditional subsidy logic.                      |
| `JAP_gpu_2024_advanced_packaging`       | Japanese GPU history | Supports the 2025 hardware-resilience assessment.                                                 |
| `JAP_gpu_2024_ai_design_priority`       | Japanese GPU history | Supports developer tooling and next-generation systems research.                                  |
| `USA_nvidia_graphics_priority_retained` | NVIDIA               | Provides guarded context for graphics-oriented platform supply.                                   |
| `TAI_tsmc_mobile_anchor_strategy`       | TSMC                 | Provides guarded context for mobile and efficient system-on-chip supply.                          |
| `TAI_tsmc_advanced_packaging_expanded`  | TSMC                 | Provides guarded context for advanced packaging capacity in 2025.                                 |
| `USA_e3_direct_broadcast_protocol`      | E3                   | Supports direct digital presentation and publisher-controlled communication.                      |
| `USA_e3_digital_common_stage_enabled`   | E3                   | Supports shared digital-stage and developer-ecosystem options.                                    |
| `USA_e3_permanently_retired`            | E3                   | Shifts industry communication away from a central trade-show institution.                         |

Manifest `allowed_reads` must contain exactly these symbols. Manifest
`allowed_writes` is empty. If implementation research shows that one read has no
actual gameplay use, remove it from both code and manifest rather than keeping a
speculative dependency.

## Scheduling and game-rule semantics

### Full

- `corporate_history_on_startup` initializes Nintendo state and synchronously
  reconstructs every passed milestone before any current-year scheduling.
- A January 2000 start schedules `.1` once through the normal 2001 corporate
  dispatcher.
- Every later start invokes the current-year scheduler directly from startup
  after synchronous reconstruction. Its January 1 mode queues future milestones
  with calendar-anchored `days` offsets; its non-January startup mode records
  those milestones as startup-skipped without queuing them.
- A later start fires `.90` after two days as an idempotent reconstruction
  safety pass. It does not own current-year scheduling.
- The current-year scheduler queues still-future milestones only when the
  campaign began on January 1, so its `days` offsets remain calendar-correct,
  then sets `JAP_nintendo_start_year_events_scheduled`. A non-January start
  reconstructs passed milestones and marks the rest of that start year's
  milestones as startup-skipped without queuing them. Once each skipped
  milestone's date passes, the monthly Full-mode driver or the next annual
  Nintendo dispatch preflight resolves it silently through reward-free
  reconstruction so later years remain reachable.
- Within one scheduling pass, a predecessor is ready when it is resolved or
  already pending at an earlier offset. This allows both 2015 milestones to be
  queued in chronological order without pretending that `.8` has already
  resolved before `.9` is scheduled.
- Annual dispatch effects own normal-year calls. No visible event calls its
  chronological successor directly.
- Every visible event has its own resolved and timed pending guards, so an
  updated save cannot receive a second copy while one is queued.
- The existing Japanese monthly Full-mode driver also invokes a bounded
  Nintendo recovery effect. After a pending flag expires, the recovery effect
  invokes the current-year scheduler in recovery mode only for a due unresolved
  milestone that still has delivery-expected evidence and whose predecessor has
  resolved. Startup-skipped milestones use silent reconstruction instead. The
  startup scheduling-complete flag suppresses only another initial January 1
  pass; it does not suppress recovery of a lost delivery.
- A start after 2025.06.05 reconstructs a deterministic capstone and completes
  silently; it does not display fifteen historical popups.

### Outcomes Only

- Startup initializes state and calls `JAP_nintendo_reconstruct_history`
  directly.
- The existing `JAP_corporate_history_monthly_outcomes` effect calls Nintendo's
  reconstruction effect while `JAP_nintendo_reconstruct_complete` is absent.
- Reconstruction applies markers and state only. It never fires a visible
  event, grants an option-specific one-time reward, or writes foreign state.
- The driver becomes permanently inert after
  `JAP_nintendo_reconstruct_complete`.

### Disabled

- Startup, annual dispatch, current-year scheduling, and monthly reconstruction
  do nothing.
- No `JAP_nintendo_*` variable, flag, idea, or queued event is created.
- Existing Japanese focuses, Sony events, GPU history, technologies, and the
  achievement remain unaffected.

### Dispatch ownership

Add Nintendo calls to the existing corporate dispatch effects in
`common/scripted_effects/00_corporate_history_dispatch_effects.txt`; do not add a
second set of raw calls to `00_yearly_effects.txt`. Extend the existing Japanese
monthly effect rather than registering another `on_monthly_JAP` block.

The current-year scheduler must be a manifest-required effect. It checks the
calendar date, resolved marker, pending marker, and predecessor state for every
event in that year. It has January 1, non-January startup, and explicit recovery
modes. In January 1 mode, an earlier pending event satisfies the scheduling
dependency for a later event in that year. Non-January startup mode sets
startup-skipped on unresolved future milestones and makes no event call. At
delivery and in recovery mode, the predecessor must be resolved. Full-mode
startup invokes the scheduler directly rather than routing it through delayed
`.90`, and only after synchronous reconstruction has established all prior-year
predecessor state. It sets a timed pending flag before every event call and sets
the start-year scheduling flag after either startup-mode pass, even if the year
contains no remaining event. Recovery mode ignores that flag and never sets it.

Recovery mode accepts an exact target milestone from the recovery effect. It
does not require that target's milestone year equal the current calendar year;
it requires that the full historical date has passed. This allows a lost
December delivery whose pending buffer expires in January to recover without
opening unrelated prior-year milestones.

Before each annual Nintendo dispatch check,
`JAP_nintendo_advance_startup_skipped` silently resolves every due
startup-skipped predecessor in chronological order. The helper contains no
`country_event` call. The annual dispatcher then uses the same resolved and
pending guards and sets the same delivery-expected and timed pending flags
before queuing an event. Each pending lifetime must extend beyond its delivery
offset by a documented recovery buffer. Extend the existing Japanese monthly
Full-mode driver with
`JAP_nintendo_recover_missing_events`: it identifies a milestone whose
historical date has arrived, whose delivery-expected marker is present, whose
resolved and pending markers are both absent, and whose predecessor is resolved,
then invokes
`JAP_nintendo_schedule_current_year_events` in recovery mode. The recovery
effect itself contains no `country_event` call. Recovery mode uses a short
bounded delay and sets the pending flag again; it does not set the January 1
scheduling-complete flag. It must not bypass the game rule, grant
reconstruction rewards, or schedule a successor whose predecessor is merely
pending. Keeping all recovery event calls inside the scheduler preserves the
contract's exact annual-dispatcher plus current-year-scheduler caller pair.

The monthly Full-mode driver separately calls
`JAP_nintendo_advance_startup_skipped`. For a due marker that is startup-skipped
and not delivery-expected, that helper never queues a visible event or grants
its one-time reward; it applies the canonical Nintendo-owned choice, clears
startup-skipped, and sets resolved. Recovery and silent skipped-milestone
advancement are mutually exclusive. Running this helper before annual
dispatching prevents a skipped December event from blocking the following
January milestone even if monthly and annual on-actions execute in either
order.

## Future file map

Implementation is expected to create:

- `events/JAP_nintendo_events.txt`
- `common/scripted_effects/JAP_nintendo_effects.txt`
- `common/ideas/JAP_nintendo_ideas.txt`

Implementation is expected to modify:

- `common/scripted_effects/00_corporate_history_effects.txt`
- `common/scripted_effects/00_corporate_history_dispatch_effects.txt`
- `localisation/english/MD_focus_JAP_l_english.yml`
- `tools/corporate_history_contract.json`
- `tools/validation/validate_corporate_history_contract.py`
- `docs/src/content/resources/corporate-history-framework.md`
- Corporate-history validator unit tests
- `Changelog.txt`

No non-English localisation, picture assignment outside the event script,
sprite definition, texture, binary asset, or `resources/` file belongs in the
implementation.

## Contract and validation design

Add a Tier 1 manifest entry with:

- `tag`: `JAP`
- `namespace`: `JAP_nintendo_events`
- `root`: `JAP_nintendo`
- `owned_prefixes`: only `JAP_nintendo`
- all five bounded variables
- outcome idea prefix `JAP_nintendo_`
- `requires_current_year_scheduler`: `true`
- `allow_yearly_scheduler_duplicates`: `true`
- no callerless visible event
- exactly the permitted annual-dispatcher plus current-year-scheduler pair for
  each visible event
- the exact `allowed_reads` list above
- empty `allowed_writes`

Focused tests must prove:

1. All 15 visible IDs and `.90` are defined once and every visible event has
   exactly the permitted annual-dispatcher plus current-year-scheduler pair.
   The recovery effect calls only the scheduler and is never a third direct
   event caller.
2. A 2000 start reaches all events in order.
3. January 1 starts reconstruct every prior milestone before scheduling all
   remaining same-year events on their exact calendar dates. A 2015 start queues
   `.8` and `.9` once, in offset order, with `.8`'s pending marker satisfying
   `.9`'s same-pass scheduling dependency. Non-January starts schedule no
   offset-based current-year event; an upcoming start-year milestone receives
   startup-skipped but not delivery-expected, produces no later popup, and
   advances silently after its historical date so the following year remains
   reachable. A December 2012 skipped milestone advances before the January
   2013 dispatcher evaluates `.7`, independent of monthly/annual on-action
   order.
4. A 2026 start resolves exactly one capstone without visible catch-up.
5. Save/reload with a queued event does not duplicate the popup or reward, and
   an intentionally lost delivery is requeued only after its timed pending flag
   expires while delivery-expected remains set. Recovery runs through scheduler
   mode; successors wait for the recovered predecessor to resolve and caller
   validation still reports only the dispatcher/scheduler pair. A
   startup-skipped event is never eligible for this recovery path. A lost
   December event remains recoverable after its pending buffer expires in the
   following year.
6. Reconstruction is idempotent and its completion flag terminates the monthly
   driver.
7. Full, Outcomes Only, and Disabled satisfy the semantics above.
8. Every variable is initialized and clamped after all mutations.
9. Exactly one outcome idea can survive the capstone effect.
10. All foreign reads are guarded and declared; no foreign write is present.
    Reconstruction produces the same markers, variables, and capstone before or
    after foreign-owner startup effects and contains no foreign read.
11. Existing Sony, GPU, NVIDIA, TSMC, E3, `JAP_games_are_fun`, and achievement
    identifiers remain unchanged.
12. English localisation is complete and UTF-8 with BOM.

## Research sources

Implementation research should begin with primary material:

- [Nintendo company history](https://www.nintendo.co.jp/corporate/en/history/index.html)
- [Nintendo GameCube hardware history](https://www.nintendo.co.jp/ngc/thisis/index.html)
- [Nintendo DS launch release, 2004.09.21](https://www.nintendo.co.jp/corporate/release/2004/040921a.html)
- [Wii launch release, 2006.09.14](https://www.nintendo.co.jp/corporate/release/2006/060914.html)
- [Nintendo DSi launch and digital-service release, 2008.10.02](https://www.nintendo.co.jp/corporate/release/2008/081002.html)
- [Nintendo 3DS price-reduction notice, 2011.07.28](https://www.nintendo.co.jp/ir/pdf/2011/110728_3e.pdf)
- [Nintendo FY2012 financial statements and 3DS price-cut account](https://www.nintendo.co.jp/ir/pdf/2012/120426e.pdf)
- [Nintendo 2012 E3 analyst Q&A on 3DS and Wii U pricing](https://www.nintendo.co.jp/ir/en/events/120606qa/index.html)
- [Wii U launch release, 2012.09.13](https://www.nintendo.co.jp/corporate/release/en/2012/120913.html)
- [Nintendo integrated-development policy briefing, 2013.01.31](https://www.nintendo.co.jp/ir/en/events/130131/05.html)
- [Nintendo and DeNA alliance announcement, 2015.03.17](https://www.nintendo.co.jp/corporate/release/en/2015/150317/index.html)
- [Nintendo representative-director change, 2015.09.14](https://www.nintendo.co.jp/ir/pdf/2015/150914e.pdf)
- [Nintendo disclosure concerning Pokémon GO, 2016.07.22](https://www.nintendo.co.jp/ir/pdf/2016/160722e.pdf)
- [Super Mario Run announcement, 2016.09.08](https://www.nintendo.co.jp/corporate/release/en/2016/160908.html)
- [Nintendo Switch launch release, 2017.01.13](https://www.nintendo.co.jp/corporate/release/en/2017/170113.html)
- [Nintendo Switch Online official overview](https://www.nintendo.com/us/switch/online/)
- [Nintendo fiscal-year 2021 material covering Super Nintendo World](https://www.nintendo.co.jp/ir/pdf/2021/210506_4e.pdf)
- [Nintendo fiscal-year 2023 briefing covering the Mario film strategy](https://www.nintendo.co.jp/ir/pdf/2023/230510e.pdf)
- [Nintendo Switch 2 launch release, 2025.04.02](https://www.nintendo.co.jp/corporate/release/2025/250402.html)

Secondary sources may locate a milestone, but every exact date, ownership claim,
and government mechanism must be checked against primary company, regulatory, or
government material before event implementation.
