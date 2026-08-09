# Dependency graph — Copilot third-pass integration review

Integration head: `origin/main @ 556b403bca`

## PR dependency graph (as merged)

All PRs are merged. This is a historical reconstruction of the merge topology.

```
origin/main @ 556b403bca  [current]
└── PR #106: Fix GPU chain stability triggers (claude/fix-gpu-chain-invalid-stability-trigger)
    └── origin/main @ 61bee3a1ac
        ├── PR #97: Corporate Systems MD economy bridge (codex/integrate-corporate-systems-md-economy)
        │   └── PR #98: Economy-backed policies (stacked on #97, entered via #97)
        ├── PR #105: Sony PS2 artwork fix (codex/ps2-event-artwork-repair)
        └── PR #103: Upstream sync 2026-07-31 (codex/sync-upstream-main-2026-07-31)
            ├── PR #96: Fix Corporate Systems runtime (codex/fix-corporate-systems-runtime)
            │   └── PR #99: ATI/AMD corporate history (stacked on #96, entered via #96)
            ├── PR #95: USA corporate policy decisions
            └── PR #94: Expand USA Corporate Systems coverage
```

## No open PR stacking issues

No open PRs exist. No retargeting required. No stale base issues.

## Upstream tracking

```
upstream/main @ 00846ea779  [2 commits ahead of fork]
├── 00846ea779  Fixed Variable Validation (#2677)
└── ac7d85d3bb  Stopped Devolution Mechanics when USoE (#2676)

fork/main @ 556b403bca  [needs sync before release]
└── synced at: 9bd8b88ee0  (PR #103, merged 2026-08-01)
```

## Stale/obsolete branches (local-only, no open PR)

These branches exist locally but have no open PR and their remote refs are `[gone]`:

| Branch | Status | Safe action |
| --- | --- | --- |
| `codex/local-release-acceptance-integration-2026-07-31` | Missing PR #106 | Update to main or delete |
| `claude/second-pass-evidence-61bee3a` | Evidence at 61bee3a1ac | Keep for historical reference |
| `claude/fix-gpu-chain-invalid-stability-trigger` | Merged in #106 | Safe to delete |
| Various `[gone]` branches | All merged | Safe to prune |

## Release candidate recommendation

Current `main @ 556b403b` IS the correct release candidate.

The `codex/local-release-acceptance-integration-2026-07-31` branch is stale.
If HOI4 is still loading from `G:/Millennium-Dawn-OEM-acceptance-20260731`, the mod descriptor
must be updated to point at the current main checkout before any further runtime testing.
