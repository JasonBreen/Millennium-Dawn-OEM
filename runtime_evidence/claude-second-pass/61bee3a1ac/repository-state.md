# Repository state — Claude second pass

Captured 2026-08-01. All SHAs verified with `git rev-parse`, not taken from any report.

## Absolute paths

| Role | Path |
| --- | --- |
| Canonical repo | `G:/Millennium-Dawn-OEM` (branch `main` @ `61bee3a1ac`) |
| Review worktree (this pass) | `G:/Millennium-Dawn-OEM/.claude/worktrees/corporate-history-framework-973bb0` |
| **Worktree HOI4 actually loads** | `G:/Millennium-Dawn-OEM-acceptance-20260731` |
| HOI4 install | `G:/steamlbirary/steamapps/common/Hearts of Iron IV` |
| HOI4 logs | `C:/Users/New/Documents/Paradox Interactive/Hearts of Iron IV/logs` |

## Heads

| Ref | SHA | Note |
| --- | --- | --- |
| `origin/main` | `61bee3a1aca500867627fbf3607b863e249bf8d2` | Merge PR #97 |
| `main` (local) | `61bee3a1ac` | identical, 0 ahead / 0 behind |
| review branch `claude/millennium-dawn-codex-qa-c851a6` | `61bee3a1ac` | 0 ahead / 0 behind `origin/main` |
| `upstream/main` (MillenniumDawn/Millennium-Dawn) | `00846ea77915638f59eae7982341d2e138cac85f` | **ahead of the last fork sync** |
| `codex/local-release-acceptance-integration-2026-07-31` | `9370598428` | committed 2026-07-31 22:46 EDT |
| repair branch `claude/fix-gpu-chain-invalid-stability-trigger` | `3e616d76ce` | this pass, 1 commit off `61bee3a1ac` |

Working tree: clean at capture time (only this evidence directory is untracked).

## Integration head determination (Phase C)

`gh pr list --state open` returns `[]` — **there are no open pull requests**. Every Codex
feature branch named in the brief is merged:

| PR | Title | Merged into | Merged at (UTC) |
| --- | --- | --- | --- |
| #89 | Add visible USA corporate systems dashboard | main | 2026-07-29 11:41 |
| #91 | Improve USA Corporate Systems Dashboard | main | 2026-07-29 14:04 |
| #92 / #93 | Dashboard visibility fix, then reverted | main | 2026-07-30 02:18 / 02:20 |
| #94 | Expand USA Corporate Systems company coverage | main | 2026-07-30 03:54 |
| #95 | Add actionable USA corporate systems policies | main | 2026-07-30 05:38 |
| #96 | Fix Corporate Systems Runtime Behavior | main | 2026-07-31 17:01 |
| #99 | Add ATI and AMD graphics corporate history | **#96's branch** | 2026-07-31 17:01 |
| #98 | Add economy-backed Corporate Systems policies | **#97's branch** | 2026-07-31 17:03 |
| #97 | Integrate Corporate Systems with the MD economy | main | 2026-08-01 13:20 |
| #103 | Sync fork main with upstream Millennium Dawn | main | 2026-08-01 13:19 |
| #105 | Fix Sony PS2 launch event artwork | main | 2026-08-01 13:19 |

No local integration branch was needed. **The correct integration head is `origin/main` @ `61bee3a1ac`.**

### Dependency graph (as merged)

```
origin/main @ 61bee3a1ac
├── #89  dashboard (base)
├── #91  dashboard improvements
├── #93  revert of #92
├── #94  company coverage
├── #95  policy decisions
├── #96  runtime behaviour fixes
│    └── #99  ATI/AMD corporate history      (stacked on #96, merged with it)
├── #97  economic bridge
│    └── #98  economy-backed policies        (stacked on #97, merged with it)
├── #103 upstream sync
└── #105 Sony PS2 artwork
```

Two of the branches the brief lists as "possibly open" (#98, #99) were **stacked**, not
based on `main`; they entered `main` only through their parents (#97, #96). Their content
is present at `61bee3a1ac` — verified by reading the files, not the PR list.

## Runtime checkout provenance — important

`C:/Users/New/Documents/Paradox Interactive/Hearts of Iron IV/mod/Millennium-Dawn-OEM.mod`
declares `path="G:/Millennium-Dawn-OEM-acceptance-20260731"`, i.e. HOI4 does **not** load
`main` or any worktree of this review branch. That checkout sits on
`codex/local-release-acceptance-integration-2026-07-31` @ `9370598428`, which is **not** an
ancestor of `main`.

Verified content equivalence rather than trusting the branch name:

```
git diff --quiet origin/main codex/local-release-acceptance-integration-2026-07-31   -> identical
origin/main^{tree}   = 28737f74e6b3faaadcef33473345e7912b53b6e0
acceptance^{tree}    = 28737f74e6b3faaadcef33473345e7912b53b6e0
```

The two commits differ only in merge topology; the **trees are byte-identical**, and the
acceptance worktree is clean. Any runtime evidence produced from that checkout is therefore
valid for `61bee3a1ac`. This equivalence must be re-verified before trusting future
screenshots, because nothing enforces it.

## Upstream drift

`upstream/main` has advanced to `00846ea779` since PR #103 synced at `9bd8b88ee0`. The fork
is behind upstream again. No open sync PR exists. This is not a regression in the Codex
work, but it means a fresh sync is required before the 2026-08-30 release and will need its
own re-test of the corporate-history dispatchers.

## Other worktrees present (not modified by this pass)

`jasonbreen-bookish-engine`, `jasonbreen-issue-28-...` (locked), `jasonbreen-implement-e3-chain`,
`pr-105-...`, `vibe/event-refactor-validation-...`, `claude/millennium-dawn-ci-errors-...`,
`claude/pr-89-system-improvements-...`, `claude/millennium-dawn-pr-22-issues-...`,
`pr-41-review-...` (detached), `claude/pr-43-fix-...`, `claude/tfr-gpu-ci-errors-...`,
`codex/local-release-acceptance-integration-2026-07-31`, `codex/ps2-event-artwork-repair`,
`codex/sync-upstream-main-2026-07-31`.
