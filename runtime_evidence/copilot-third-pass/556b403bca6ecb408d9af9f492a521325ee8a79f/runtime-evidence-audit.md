# Runtime evidence audit — Copilot third-pass

Integration head: `556b403bca6ecb408d9af9f492a521325ee8a79f`

## Codex evidence

### corporate-systems-campaign/phase-1 (working-tree)
- **Tested SHA**: `codex/improve-usa-corporate-dashboard` working tree (pre-merge)
- **Test type**: Full game session, Corporate Systems dashboard
- **Content**: Full/Outcomes Only/Off dashboard visibility; bridge tier display
- **Classification**: valid-but-stale (predates #103, #96, #97, #98, #99, #105, #106)
- **Invalidated by**: PRs #96/#97/#98 changed dashboard content and bridge; #106 changed gpu_development
- **Retest needed**: Yes — full Corporate Systems dashboard + policy test

### corporate-systems-campaign/phase-2 (working-tree)
- **Tested SHA**: working tree (pre-merge of #95)
- **Content**: Policy list visible screenshot
- **Classification**: valid-but-stale (predates final #95 merge head)
- **Note**: PR #95 final merge head added combined cost triggers; earlier evidence doesn't cover them

### corporate-systems-campaign/phase-3 (working-tree)
- **Tested SHA**: `bf6e8496dbcf` (branch `codex/add-ati-amd-corporate-history`, pre-merge)
- **Content**: ATI/AMD dashboard Full/Outcomes Only/Off; capstone reconstruction; Off suppression
- **Classification**: valid-but-stale — content correct, SHA predates #103/#105/#106
- **Invalidated by**: #106 changed `gpu_development.3.b_can` AI weighting (ATI route probability)
- **Retest needed**: Yes for ATI/AMD full chain; the dashboard reconstruction logic is untouched

### issue-driven-release-sweep/9370598428 (Codex)
- **Tested SHA**: `9370598428b1f2f84fe30f94ebbcb3b2f9e26438` (acceptance branch, diverges at `11cdddf471`)
- **Test type**: Console-assisted fixture smoke only
  - `USA_ibm_events.12` — rendered, option A executed, game.log confirmed
  - `CAN_matrox_events.1` — rendered, option A executed, game.log confirmed
  - `SWE_ericsson_events.1` — rendered, option A executed, game.log confirmed
- **Classification**: incomplete (fixture only, not natural chronology)
- **Invalidated by**: Does not cover IBM .13-.14, Matrox full chain, Ericsson full chain
- **Note**: SHA is NOT an ancestor of main; tree differs from main in `events/00_gpu_development.txt` and `Changelog.txt`

### issue-driven-release-sweep/680d24909e (Codex)
- **Tested SHA**: `680d24909edfc007aea2b5898f55cc025a699e3e`
- **Result**: "in progress — no runtime pass claimed"
- **Classification**: static-only-claim (results.md explicitly says no runtime pass)

### issue-driven-release-sweep/a53c94daa7 (Codex)
- **Tested SHA**: `a53c94daa7ce648047eea6ea54cd165e26a02ba2`
- **Result**: "superseded before runtime"
- **Classification**: unverifiable (explicitly abandoned)

## Claude second-pass evidence (claude/second-pass-evidence-61bee3a)

- **Tested SHA**: `61bee3a1aca500867627fbf3607b863e249bf8d2`
- **Runtime access**: DENIED (no HOI4 session launched)
- **Source confirmations only** (no runtime evidence):
  - No JAP→SWE state-write (33 TAG-scoped write sites, all confirmed)
  - No GER→FIN state-write (same scan)
  - IBM axes 0-10 bounded at all 35 mutation sites
  - IBM initialization guard (NOT has_country_flag wrapper)
  - Capstone atomicity (clear all siblings before add_ideas)
  - Apple axes 0-10 bounded (USA_apple_clamp_state after every mutation)
  - Physical-compute stack requires all 3 pillar ideas + seam_count > 1
  - PS2 sprite resolves (validate_gfx_references.py clean)
  - No raw localisation keys (validators clean)
- **Classification**: source-confirmed (not runtime)
- **Note**: Evidence is at `61bee3a1ac`, not current `556b403b`. GPU fix (#106) doesn't
  affect any of the above source confirmations.

## Evidence status summary

| Issue | Best available evidence | Valid for current main? | Retest required |
| --- | --- | --- | --- |
| #24 Sony | Day-6 fixture + source scan | Source: yes. Runtime: NO | Full Japan playthrough |
| #25 IBM | Day-6 fixture (event .12) + source scan | Source: yes. Runtime: NO | Full USA playthrough |
| #26 Matrox | Day-6 fixture + source scan | Source: yes. Runtime: NO (GPU fix relevant) | Canada playthrough after #106 |
| #27 Nokia/Ericsson | Day-6 fixture + source scan | Source: yes. Runtime: NO | Finland/Sweden/Germany playthrough |
| #28 NA smoke | Nothing | NO | Full USA/Canada campaign |
| #45 Polish | GPU fix merged, editorial open | Partial | Human editorial pass |
| ATI/AMD dashboard | Phase-3 screenshots at bf6e8496 | Content valid; SHA stale | Retest at 556b403b |
| Corporate Systems dashboard | Phase-1 screenshots | Stale (pre-#96/#97/#98) | Retest at 556b403b |
