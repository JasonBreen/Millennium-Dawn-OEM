# Netherlands — ASML Corporate History (2003–2026)

Scope: OEM Corporate History module modelling ASML from the immersion lithography pivot through XT:1250i shipment, Alpha Demo Tools, NXE:3100 first light, CCIP, Cymer acquisition, the Zeiss SMT stake, EUV HVM, China EUV license non‑renewal, advanced DUV licensing, High‑NA EXE, and a 2025–2026 capstone. Not a new focus tree. English localisation only. Namespace `HOL_asml_events`. Root prefix `HOL_asml`. Owner tag `HOL` (`original_tag = HOL` in every visible trigger).

Game‑rule semantics:

- Full: initialize, reconstruct only elapsed history, schedule current‑year beats, recover missed visible deliveries, deliver 12 visible beats plus a capstone, then complete
- Outcomes Only: silent reconstruction picks the historical‑A routes at each beat, then applies exactly one capstone idea
- Off: creates no `HOL_asml_*` state, schedules nothing, changes nothing outside this chain
  10|
  Hidden reconstruct sink: `HOL_asml_events.90` is a callerless Outcomes Only debug sink, not a lifecycle owner. The registered `HOL_asml_reconstruct_history` root delegates silent history only in Outcomes Only; Full monthly dispatch resolves only prior‑year history before generic recovery and never invokes silent reconstruction for a current‑year choice.

Do not write any other chain’s identifiers. Hard constraints for this series: writes are confined to `HOL_asml_*` only; no Samsung/KOR cross‑chain coupling; do not reopen or edit SpaceX `USA_spacex_*` material (tracked separately).

## State model (persistent axes, 0..10)

All variables are integers clamped to 0..10 by `corporate_history_clamp_value`. Owner effects only:

- `HOL_asml_lithography_leadership` — technology lead across immersion, EUV, and High‑NA
- `HOL_asml_supply_chain_depth` — optics, light‑source, and component chain depth and resilience
- `HOL_asml_export_alignment` — alignment with allied export‑control policy and licensing posture

Required owner effects (all idempotent):

- `HOL_asml_initialize_state`
  30|- `HOL_asml_clamp_state`
- `HOL_asml_reconstruct_history`
- `HOL_asml_reconstruct_outcomes_history`
- `HOL_asml_schedule_current_year_events`
- `HOL_asml_recover_prior_year_history`
- `HOL_asml_resolve_capstone`

Lifecycle flags:

- `HOL_asml_state_initialized`
  40|- `HOL_asml_reconstruct_complete`
- `HOL_asml_start_year_events_scheduled`
- `HOL_asml_capstone_resolved`

Completion: `HOL_asml_capstone_resolved` (idea‑applied) and `HOL_asml_reconstruct_complete` (history done).

## Visible beats (is_triggered_only), 12 + capstone

All dates are scheduler anchors. Events never spend treasury/PP, place buildings, or alter foreign state. Every option carries a real tradeoff following content‑guidelines balance rules. GFX reuse: `GFX_computer` or `GFX_generic_factory` (no new art).

    50|1. Immersion bet — 2003 (anchor 2003.06.01, days = 152)

- Choices: commit to immersion as the primary path; hedge with air and delay; accelerate shared supplier programs
- Axes: +lithography_leadership or +supply_chain_depth or (+/-) export_alignment

2. First immersion ship (XT:1250i) — 2004 (anchor 2004.04.01, days = 91)

- Choices: scale immersion deliveries; prioritize EUV research staffing; extend partner qualification
- Axes: +supply_chain_depth, (+/-) lithography_leadership, (+/-) export_alignment

  60|3. Alpha Demo Tools — 2006 (anchor 2006.10.01, days = 274)

- Choices: broaden early‑access program; restrict to top allied fabs; slow to focus on DUV revenue
- Axes: +lithography_leadership, (+/-) export_alignment, (+/-) supply_chain_depth

4. NXE:3100 first light — 2010 (anchor 2010.03.01, days = 60)

- Choices: push EUV light‑source ramp; harden mirror/contamination path; defer cadence in favour of yield
- Axes: +lithography_leadership, (+/-) supply_chain_depth

  70|5. Customer Co‑Investment Program (CCIP) — 2012 (anchor 2012.07.01, days = 182)

- Choices: expand CCIP scope; keep investment narrow; attach export‑policy covenants
- Axes: +supply_chain_depth, (+/-) export_alignment

6. Cymer acquisition — 2013 (anchor 2013.05.01, days = 121)

- Choices: integrate aggressively; retain supplier autonomy; dual‑track DUV/EUV sourcing
- Axes: +supply_chain_depth, (+/-) lithography_leadership

  80|7. Zeiss SMT 24.9% stake — 2016 (anchor 2016.11.01, days = 305)

- Choices: deepen optics JV integration; preserve arm’s‑length governance; expand allied optics capacity
- Axes: +supply_chain_depth, (+/-) export_alignment

8. EUV HVM milestone — 2019 (anchor 2019.07.01, days = 182)

- Choices: prioritize HVM cadence; slow for ecosystem hardening; reserve capacity for strategic allies
- Axes: +lithography_leadership, (+/-) export_alignment, (+/-) supply_chain_depth

  90|9. EUV China license non‑renewal — 2019 (anchor 2019.12.01, days = 335)

- Choices: align strictly with allied controls; pursue narrow carve‑outs; emphasize DUV alternatives
- Axes: +export_alignment, (-/+) supply_chain_depth

10. Advanced DUV licensing posture — 2023 (anchor 2023.03.01, days = 60)

- Choices: tighten advanced DUV exports; case‑by‑case licensing; broad commercial access
- Axes: (+/-) export_alignment, (+/-) supply_chain_depth

  100|11. High‑NA EXE (EXE:5200 family) — 2023–2025 (anchor 2024.06.01, days = 152)

- Choices: accelerate allied High‑NA deployments; strict risk‑gated cadence; broaden demo access
- Axes: +lithography_leadership, (+/-) export_alignment, (+/-) supply_chain_depth

12. Capstone — 2025–2026 window (deliver in `corporate_history_dispatch_year_2026`, days = 243)

- Evaluate axes and apply exactly one idea (mutually exclusive); no further variable mutation after resolution.

Priority order, then fallback:
110|

1. Allied EUV Chokepoint Steward — `HOL_asml_chokepoint_steward`
2. Triad Supply Sovereign — `HOL_asml_triad_supply_sovereign`
3. Commercial Open‑Market Maximizer — `HOL_asml_open_market_maximizer`
4. Strict Dual‑Use Gatekeeper — `HOL_asml_dual_use_gatekeeper`
5. Balanced Atlantic Semiconductor Anchor — `HOL_asml_balanced_atlantic_anchor` (fallback)

Authority: applied idea (checked via `has_idea`); completion flags kept for lifecycle only.

Full‑mode resolution
120|

- The capstone event `.12` presents five options in collision order only for Full:
  a Chokepoint Steward (gated)
  b Triad Supply Sovereign (gated)
  c Open‑Market Maximizer (gated)
  d Dual‑Use Gatekeeper (gated)
  e Balanced Atlantic Anchor (always available)
- Each option sets its route flag then calls `HOL_asml_resolve_capstone` to apply the idea and mark reconstruction complete.

Outcomes Only (no popup)
130|

- Reconstruction applies all historical‑A beat recorders. If `date > 2026.08.31` and no route flag is set, it silently sets the chokepoint‑steward route. After `2026.09.01`, `resolve_capstone` applies the chokepoint‑steward outcome and the reconstruction root sets its completion marker.
- `HOL_asml_resolve_capstone` contains no axis scoring: it switches on route flags only (steward/triad/open/gatekeeper/balanced) and falls back to balanced‑anchor when no route flag is present.

## Files and ownership

- `events/HOL_asml_events.txt` — 12 visible beats + `.90` hidden reconstruct sink (not dispatched)
- `common/scripted_effects/HOL_asml_effects.txt` — state init/clamp, per‑beat recorders, reconstruct, scheduler, capstone resolver
- `common/ideas/HOL_asml_ideas.txt` — 5 capstone ideas
- `localisation/english/MD_focus_HOL_l_english.yml` — all event titles/desc/options and idea names/desc
  140|- `tools/corporate_history_contract.json` — contract entry
- `common/scripted_effects/00_corporate_history_monthly_dispatch_effects.txt` — add HOL startup wiring (initialize/reconstruct; schedule_current_year_events in 2000 window)
- `common/scripted_effects/00_corporate_history_dispatch_effects.txt` — yearly scheduling owners for beats (2003, 2004, 2006, 2010, 2012, 2013, 2016, 2019×2, 2023×2, 2026)
- `common/scripted_effects/00_corporate_history_midyear_recovery_effects.txt` — guarded one‑day recovery delivery for all 12 visible events

## Contract (tools/corporate_history_contract.json)

- `name`: "ASML"
- `tag`: "HOL"
- `namespace`: "HOL_asml_events"
  150|- `root`: "HOL_asml"
- `tier`: 1
- `owned_prefixes`: only "HOL_asml"
- `variables`: the three axes above, each min 0, max 10
- `outcome_idea_prefixes`: ["HOL_asml_"]
- `requires_current_year_scheduler`: true
- `allow_yearly_scheduler_duplicates`: true
- `allowed_reads`: [] (none in first cut)
- `allowed_writes`: [] (none)
- `monthly_driver`: "HOL_corporate_history_monthly_outcomes"
  160|- `terminal_marker`: "HOL_asml_reconstruct_complete"
- `terminal_date`: "2026-09-01"
- `expected_callers`: events `.1` through `.12` map to their exact `HOL_asml_dispatch_*` owner effects; schema‑v6 recovery also permits the HOL midyear‑recovery host; `.90` maps to `[]`
- `effect_preview_policy`: "engine_or_explicit"
- `bridge_refresh_policy`: "none"

## Duplicated popup audit

- This chain uses only `country_event` with `is_triggered_only = yes` and reuses generic GFX; it does not introduce `news_event`s or re‑fire global industry‑news popups on the same dates. No duplicate global popups are added.

  170|## Sources (dates verified)

- Immersion lithography program: 2003 anchor
- First immersion ship (XT:1250i): 2004 anchor
- Alpha Demo Tools: 2006 anchor
- NXE:3100 first light: 2010 anchor
- CCIP: 2012
- Cymer acquisition: 2013
- Zeiss SMT 24.9% stake: 2016
- EUV HVM: 2019
  180|- EUV China license non‑renewal: 2019
- Advanced DUV licensing posture: 2023
- High‑NA EXE deployments: 2023–2025

Primary documents: ASML press releases and investor materials, Zeiss SMT corporate disclosures, EU and Dutch regulatory/export‑control communications. Dates are used only as scheduler anchors; no policy claims beyond public anchors.
