# United States — SpaceX Corporate History (2002–2026)

Scope: OEM Corporate History module modelling SpaceX from founding through Falcon 1, COTS/CRS, Falcon 9 + Dragon, reuse, Falcon Heavy, Starlink, Commercial Crew, NSSL, Starship HLS, iterative Starship licensing/tests, and a 2025–2026 capstone. Not a new focus tree, not Great AI Race. English localisation only. Namespace `USA_spacex_events`. Root prefix `USA_spacex`. Owner tag `USA` (`original_tag = USA` in every visible trigger).

Game-rule semantics:
- Full: initialize, reconstruct hidden history pre-start-date, schedule only current-year beats, deliver 11 visible beats plus a capstone, then complete
- Outcomes Only: silent reconstruction picks the historical-A routes at each beat, then applies exactly one capstone idea
- Off: creates no `USA_spacex_*` state, schedules nothing, changes nothing outside this chain

Hidden reconstruct sink: `USA_spacex_events.90` exists but is not scheduled from schema bootstrap; the monthly/USA startup calls the owner effect directly.

Do not write any other chain’s identifiers (NASA, ULA/Boeing, AI Core, NVIDIA, energy, microchip, Great AI Race). Reads of other satcom/5G state are deferred and not used in this first implementation.

## State model (persistent axes, 0..10)

All variables are integers clamped to 0..10 by `corporate_history_clamp_value`. Owner effects only:

- `USA_spacex_launch_cadence_reliability` — sustainable launch rate and mission reliability
- `USA_spacex_reusability_depth` — reuse engineering depth and operational maturity
- `USA_spacex_government_partnership` — federal/NASA/USSF partnership strength
- `USA_spacex_commercial_market_power` — commercial-market bargaining power and platform concentration
- `USA_spacex_leo_satcom_presence` — LEO satcom constellation deployment depth
- `USA_spacex_heavy_deep_space_lift` — heavy/very-heavy lift capability towards deep-space missions
- `USA_spacex_geostrategic_access` — U.S.-aligned strategic launch and regulatory access (range, licensing, allied access)

Required owner effects (all idempotent):
- `USA_spacex_initialize_state`
- `USA_spacex_clamp_state`
- `USA_spacex_reconstruct_history`
- `USA_spacex_schedule_current_year_events`
- `USA_spacex_resolve_capstone`

Lifecycle flags:
- `USA_spacex_state_initialized`
- `USA_spacex_reconstruct_complete`
- `USA_spacex_start_year_events_scheduled`
- `USA_spacex_capstone_resolved`

Completion: `USA_spacex_capstone_resolved` (idea-applied) and `USA_spacex_reconstruct_complete` (history done).

## Visible beats (is_triggered_only), 11 + capstone

All dates are scheduler anchors. Events never spend treasury/PP, grant research bonuses, place buildings, or alter opinions. Every option carries a real tradeoff following content-guidelines balance rules. GFX reuse: `GFX_computer` or `GFX_generic_factory` (no new art).

1) Founding — 14 Mar 2002 (days = 72)
- Choices: vertically integrate early; seek DoD/NASA contracting discipline; accelerate with foreign components
- Axes: +reusability_depth or +government_partnership or +launch_cadence_reliability (with a tradeoff)

2) Falcon 1 reaches orbit — 28 Sep 2008 (days = 271)
- Choices: iterate with flight test; nationalize risk with tight oversight; consolidate with legacy primes
- Axes: +launch_cadence_reliability, (+/-) government_partnership, (+/-) commercial_market_power

3) COTS/CRS — Aug 2006 (days ~ 227) / CRS 23 Dec 2008 (historical context, single 2006 anchor)
- Choices: dual-source cargo; single champion; stretch Shuttle logistics
- Axes: (+/-) government_partnership, (+/-) geostrategic_access, (+/-) commercial_market_power

4) Falcon 9 + Dragon — 4 Jun 2010 (days = 155) with 22–25 May 2012 in desc
- Choices: qualify Dragon for ISS cargo and civil missions vs slower certification vs narrow commercial focus
- Axes: +launch_cadence_reliability, +government_partnership, (-/+) commercial_market_power

5) First-stage reuse — 22 Dec 2015 landing (days = 356); 30 Mar 2017 reflight in desc
- Choices: aggressive reuse ramp; conservative cadence; protect single-use revenue
- Axes: +reusability_depth, (+/-) launch_cadence_reliability, (+/-) commercial_market_power

6) Falcon Heavy — 6 Feb 2018 (days = 37)
- Choices: qualify for national-security missions; commercial-only heavy; defer to competing heavies
- Axes: +heavy_deep_space_lift, (+/-) government_partnership, (+/-) geostrategic_access

7) Starlink large deployment — 23 May 2019 (days = 143)
- Choices: allied dual-use; aggressive commercial-only; security reservation
- Axes: +leo_satcom_presence, (+/-) commercial_market_power, (+/-) geostrategic_access

8) Crew Dragon Demo-2 — 30 May 2020 (days = 151)
- Choices: certify commercial crew; dual providers discipline; prolong Soyuz reliance
- Axes: +government_partnership, +launch_cadence_reliability, (-/+) commercial_market_power

9) NSSL composite — ~2021 anchor (days = 224)
- Choices: dual-source with SpaceX cadence; legacy-prime preference; SpaceX sole-source
- Axes: (+/-) government_partnership, (+/-) geostrategic_access, (+/-) commercial_market_power

10) Starship HLS — 16 Apr 2021 (days = 106)
- Choices: award Starship; split vendors; delay for alternative lander
- Axes: +heavy_deep_space_lift, +government_partnership, (-/+) commercial_market_power

11) Starship iterative licensing — 20 Apr 2023 (days = 110), IFT-5 catch 13 Oct 2024 in desc
- Choices: aggressive iterative licensing; slow environmental path; federalize Starbase infrastructure
- Axes: +reusability_depth, (+/-) geostrategic_access, (+/-) launch_cadence_reliability

12) Capstone — 2026 window (deliver in `corporate_history_dispatch_year_2026`, days = 243)
- Evaluate axes and apply exactly one idea (mutually exclusive); no further variable mutation after resolution.

Priority order, then fallback:
1. Assured Access Cadence Champion — `USA_spacex_cadence_champion`
2. Allied LEO Connectivity Bloc — `USA_spacex_allied_leo_connectivity`
3. Deep-Space Industrial Stack — `USA_spacex_deep_space_stack`
4. Commercial Launch Monopoly Risk — `USA_spacex_commercial_monopoly_risk`
5. Disciplined Mixed Provider Ecosystem — `USA_spacex_mixed_provider_ecosystem` (fallback)

Authority: applied idea (checked via `has_idea`); completion flags kept for lifecycle only.

Full-mode resolution (match NVIDIA split)
- The capstone event `.12` presents five options in collision order only for Full:
  a Cadence Champion (gated)
  b Allied LEO (gated)
  c Deep-Space (gated)
  d Monopoly Risk (gated)
  e Mixed-Provider (always available)
- Each option sets its route flag then calls `USA_spacex_resolve_capstone` to apply the idea and mark reconstruction complete.

Outcomes Only (no popup)
- Reconstruction applies all historical‑A beat recorders. If `date > 2026.08.31` and no route flag is set, it silently sets the cadence route. On/after `2026.09.01`, `resolve_capstone` applies the cadence outcome.
- `USA_spacex_resolve_capstone` contains no axis scoring: it switches on route flags only (cadence/starlink/starship/monopoly/mixed) and falls back to mixed‑provider when no route flag is present.

## Files and ownership

- `events/USA_spacex_events.txt` — 12 visible beats + `.90` hidden reconstruct sink (not dispatched)
- `common/scripted_effects/USA_spacex_effects.txt` — state init/clamp, per-beat recorders, reconstruct, scheduler, capstone resolver
- `common/ideas/USA_spacex_ideas.txt` — 5 capstone ideas
- `localisation/english/MD_focus_USA_l_english.yml` — all event titles/desc/options and idea names/desc
- `tools/corporate_history_contract.json` — contract entry
- `common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt` — add USA startup wiring (initialize/reconstruct; schedule_current_year_events in 2000 window)
- `common/scripted_effects/00_corporate_history_dispatch_effects.txt` — yearly scheduling owners for beats (2002, 2006, 2008, 2010, 2015, 2018, 2019, 2020, 2021×2, 2023, 2026)

## Contract (tools/corporate_history_contract.json)

- `name`: "SpaceX"
- `tag`: "USA"
- `namespace`: "USA_spacex_events"
- `root`: "USA_spacex"
- `tier`: 1
- `owned_prefixes`: only "USA_spacex"
- `variables`: the seven axes above, each min 0, max 10
- `outcome_idea_prefixes`: ["USA_spacex_"]
- `requires_current_year_scheduler`: true
- `allow_yearly_scheduler_duplicates`: true
- `allowed_reads`: [] (none in first cut)
- `allowed_writes`: [] (none)
- `monthly_driver`: "USA_corporate_history_monthly_outcomes"
- `terminal_marker`: "USA_spacex_reconstruct_complete"
- `terminal_date`: "2026-09-01"
- `expected_callers`: { "USA_spacex_events.90": [] }
- `effect_preview_policy`: "engine_or_explicit"
- `bridge_refresh_policy`: "none"

## Duplicated popup audit

- `events/Space_GFXlaunches.txt` contains generic space-flavour news popups (non-owner) including shuttle/rocket visuals. This chain uses only `country_event` with `is_triggered_only = yes` and reuses generic GFX; it does not introduce `news_event`s or re-fire global launch-news popups on the same dates. No duplicate global-space popups are added.

## Sources (dates verified)

- SpaceX founded: 14 Mar 2002 — California filing and company history
- Falcon 1 to orbit: 28 Sep 2008 — Flight 4
- COTS awards: Aug 2006 — NASA COTS SA; CRS award: 23 Dec 2008
- Falcon 9 first flight: 4 Jun 2010 — Dragon C2+/ISS berthing: 22–25 May 2012
- First landing: 22 Dec 2015 — First reflight: 30 Mar 2017
- Falcon Heavy demo: 6 Feb 2018
- First large Starlink: 23 May 2019
- Crew Dragon Demo‑2: 30 May 2020
- NSSL Phase 2 awards: Aug 2020 (dual-source with ULA) with 2021 operational ramp
- HLS Option A: 16 Apr 2021
- Starship IFT‑1: 20 Apr 2023; IFT‑5 catch: 13 Oct 2024

Primary documents: NASA program pages and press releases, USSF NSSL award releases, FCC filings for Starlink deployment, and SpaceX mission press kits. Dates are used only as scheduler anchors; no policy claims beyond public anchors.

