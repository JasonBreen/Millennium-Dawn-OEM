# Repository state — Copilot third-pass integration review

Captured 2026-08-01. All SHAs verified with `git rev-parse`.

## Absolute paths

| Role | Path |
| --- | --- |
| Review worktree (this pass) | `C:/Users/New/repos/copilot-worktrees/Millennium-Dawn-OEM/jasonbreen-vigilant-enigma` |
| Canonical main checkout | `G:/Millennium-Dawn-OEM` |
| Acceptance worktree (Codex) | `G:/Millennium-Dawn-OEM-acceptance-20260731` (branch `codex/local-release-acceptance-integration-2026-07-31` @ `9370598428`) |
| HOI4 install | `G:/steamlbirary/steamapps/common/Hearts of Iron IV` |
| HOI4 mod descriptor loaded | `G:/Millennium-Dawn-OEM-acceptance-20260731` (points at acceptance worktree, NOT main) |

## Heads

| Ref | SHA | Note |
| --- | --- | --- |
| `origin/main` | `556b403bca6ecb408d9af9f492a521325ee8a79f` | Merge PR #106 GPU fix, 2026-08-01T15:12Z |
| `main` (local) | `556b403bca` | 0 ahead/behind origin |
| `upstream/main` | `00846ea779` | 2 commits ahead of last sync (PR #2677 Variable Validation, PR #2676 Devolution) |
| `codex/local-release-acceptance-integration-2026-07-31` | `9370598428` | Diverged at `11cdddf471` — STALE (missing PR #106) |
| `claude/second-pass-evidence-61bee3a` | `ac1a7b0b72` | Evidence at `61bee3a1ac` — also stale, but GPU fix doesn't invalidate most tests |

## Summary of open PRs

`gh pr list --state open` → `[]` — **no open PRs**. All feature work merged into main.

## Recently merged PRs (relevant)

| PR | Title | Merged at |
| --- | --- | --- |
| #106 | Fix twelve invalid stability triggers in GPU chain | 2026-08-01T15:12Z |
| #105 | Fix Sony PS2 launch event artwork | 2026-08-01T13:20Z |
| #103 | Sync fork with upstream Millennium Dawn | 2026-08-01T13:19Z |
| #97 | Integrate Corporate Systems with MD economy | 2026-08-01T13:20Z |
| #96 | Fix Corporate Systems Runtime Behavior | 2026-07-31T17:01Z |
| #99 | Add ATI and AMD graphics corporate history | via #96 stack |
| #98 | Add economy-backed Corporate Systems policies | via #97 stack |
| #95 | Add actionable USA corporate systems policies | 2026-07-30T05:38Z |
| #94 | Expand USA Corporate Systems company coverage | 2026-07-30T03:54Z |
| #91 | Improve USA Corporate Systems Dashboard | 2026-07-29T14:04Z |

## CI status at current main (556b403b)

| Workflow | Status |
| --- | --- |
| Pylint | ✅ success |
| Validator Cache (main) | ✅ success |
| GitHub Pages Deployment | ✅ success (at this SHA; failure was at `a2f9db3f`) |

## Open issues (all testing/acceptance)

| # | Title | Status |
| --- | --- | --- |
| #24 | Sony corporate-history runtime acceptance | Untested (fixture smoke only at day 6) |
| #25 | IBM Phase III full runtime acceptance | Untested (event .12 console only) |
| #26 | Matrox event chain regression | Untested (event .1 console only) |
| #27 | Nokia–Ericsson–Siemens integration | Untested (SWE event .1 console only) |
| #28 | North American OEM release smoke sweep | Wide open (no playthrough) |
| #45 | Release polish pass | Open; editorial pass requires human |

## Upstream drift

2 upstream commits not yet synced:
- `00846ea779` — Fixed Variable Validation (#2677)
- `ac7d85d3bb` — Stopped Devolution Mechanics when USoE (#2676)

No OEM feature regressions expected from these upstream commits. A sync PR is required before the 2026-08-30 release date.

## Local release candidate assessment

`codex/local-release-acceptance-integration-2026-07-31` @ `9370598428` diverges from main at `11cdddf471` (PS2 artwork commit). It is missing:
1. `events/00_gpu_development.txt` — PR #106 GPU stability trigger fix
2. `Changelog.txt` — PR #106 changelog entries

`diff codex/local-release-acceptance-integration..main` shows only these two files.
**Current `main` @ `556b403b` is the correct integration head.** The local acceptance branch is stale and should not be used as a release candidate.
