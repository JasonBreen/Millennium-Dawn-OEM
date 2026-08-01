# Merge order — Copilot third-pass

Integration head: `556b403bca6ecb408d9af9f492a521325ee8a79f`

## Status

**No open PRs.** All feature work is already on `main`.

The concept of a "merge order" applies to the planned upstream sync PR and any future
issue-driven repair branches only.

## Recommended next actions (in order)

### 1. Update descriptor for runtime testing (immediate)

The HOI4 mod descriptor at
`C:/Users/New/Documents/Paradox Interactive/Hearts of Iron IV/mod/Millennium-Dawn-OEM.mod`
currently points at `G:/Millennium-Dawn-OEM-acceptance-20260731` which runs
`codex/local-release-acceptance-integration-2026-07-31 @ 9370598428`.

Before any runtime testing, update the descriptor's `path=` to point at
`G:/Millennium-Dawn-OEM` (canonical main checkout, currently at `556b403b`).

Also verify: `git diff --quiet` clean on the main checkout.

### 2. Human runtime acceptance sweep (issues #24–#28)

All issues require human game sessions. No agent can substitute.

Order recommendation:
1. **#28** (North American smoke) — broadest coverage, surfaces cross-chain interactions
2. **#26** (Matrox) — now that GPU fix (#106) is merged, run the ATI/AMD + Matrox Canada pass
3. **#24** (Sony) — Japan full playthrough with corrected dates from PR #70
4. **#25** (IBM) — USA full playthrough through all prehistory and consequents
5. **#27** (Nokia/Ericsson/Siemens) — Finland/Sweden/Germany cross-country

### 3. Human editorial pass (issue #45)

Items 1 and 2 (editorial and historical audit) are explicitly human-only.
No agent has or will attempt these.

### 4. Upstream sync PR (before 2026-08-28)

Create a sync PR from `upstream/main @ 00846ea779` into fork main.
Review the two upstream commits for OEM regression risk:
- `ac7d85d3bb` — Stopped Devolution Mechanics when USoE (#2676) — likely safe
- `00846ea779` — Fixed Variable Validation (#2677) — may expand validation warnings

After merge, retest corporate-history dispatchers (yearly effects) for OEM callers.

## Merge order table (upstream sync only)

| Step | Action | Predecessor | Status |
| --- | --- | --- | --- |
| 1 | Update mod descriptor to point at main | None | Immediate/manual |
| 2 | Human runtime sweep #28 | Descriptor update | Pending human |
| 3 | Human runtime sweep #26/#24/#25/#27 | Descriptor update | Pending human |
| 4 | Human editorial pass #45 | None (independent) | Pending human |
| 5 | Upstream sync PR | Steps 2–4 not blocking, but sync before merge | Not started |
| 6 | Retest dispatch/yearly callers after upstream sync | Step 5 | After sync |
