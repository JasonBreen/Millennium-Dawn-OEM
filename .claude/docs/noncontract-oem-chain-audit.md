# Non-Contract OEM Chain Audit

This audit covers the eight namespaces named in the hardening task and the shared
physical-compute aggregate. It records the architecture after the chronology,
ownership, and release-blocker repairs were integrated.

## Inventory and contract decisions

Decision key:

1. Add to `tools/corporate_history_contract.json`.
2. Add a separate lighter-weight validation contract.
3. Leave outside with documented reasons.
4. Refactor into an existing owner chain.
5. Treat as standalone historical flavour.

| Namespace             | Range and dates                                             | Scheduling and direct calls                                                                                                                                                                                                                                                                                                 | Persistent state and terminal state                                                                                                                                                                                                                               | Cross-chain API and late-start behaviour                                                                                                                                                                                                                                                                    | Decision                                                                                                                                                                   |
| --------------------- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CHI_lenovo_events`   | `.1-.8`, hidden `.90`; 2004-12-09 to 2014                   | IBM's owner effect is the sole caller of `.1` after the PC transaction; the central startup driver invokes Lenovo's scheduler and `.90`; the 2014 dispatcher and current-year scheduler own `.7`, with the CHI monthly driver recovering lost delivery; `.1` branches into `.2`, `.5` or `.6`, while `.7` can lead to `.8`. | No bounded variables. Lenovo owns the PC, System x and Motorola Mobility route flags and six milestone ideas. The durable terminal marker is `CHI_lenovo_reconstruct_complete`, set after the PC, brand, and System x routes resolve.                             | Reads exact IBM transaction routes and Motorola ownership. IBM and Motorola invoke narrow Lenovo owner effects. Outcomes Only reconstructs silently and idempotently; Full retries lost follow-ups and interrupted stages; Off creates no Lenovo state.                                                     | **1.** Registered as a Tier-2 IBM/Motorola satellite with exact bilateral owner-effect permissions.                                                                        |
| `USA_ti_events`       | `.12-.20`, hidden `.90`; 1997-07-02 to 2026-02-04           | Full mode owns `.90`, the January 1 scheduler and yearly `.14-.16`, `.18-.20` dispatch. Micron `.15` calls TI `.17`. `.12/.13` are reconstruction-only pre-bookmark anchors.                                                                                                                                                | Four bounded variables: embedded reach, DSP leadership, manufacturing control and defence integration. Six mutually exclusive outcomes; `.20` is terminal and reconstruction ends at `USA_ti_reconstruct_complete`.                                               | Reads Micron's `.15` marker and the three exact Lehi transaction flags. Outcomes Only reconstructs silently after Micron; Full performs one terminal recovery if a milestone was missed while collapsed. Off creates no TI state.                                                                           | **1.** Added as Tier 1.                                                                                                                                                    |
| `USA_micron_events`   | `.6-.20`, hidden `.90`; 1998-12-31 to 2025-06-12            | Full mode owns `.90`, the January 1 scheduler and yearly `.8-.20` dispatch. `.15` calls TI `.17`; `.6/.7` are reconstruction-only pre-bookmark anchors.                                                                                                                                                                     | Four bounded variables: process lead, cycle discipline, US fab commitment and HBM position. Six mutually exclusive outcomes; `.20` is terminal and reconstruction ends at `USA_micron_reconstruct_complete`.                                                      | Canonically owns `USA_stack_txn_lehi_*`; the only cross-write is the declared call to `USA_ti_events.17`. Outcomes Only is silent and idempotent. Full performs one terminal recovery after collapse. Off creates no Micron state.                                                                          | **1.** Added as Tier 1.                                                                                                                                                    |
| `USA_motorola_events` | `.12-.24`, hidden `.90`; 1991-01-01 to 2025-08-06           | Full mode owns `.90`, the January 1 scheduler and yearly `.17-.24` dispatch; the scheduler also restores 2000 `.16`. `.12-.15` are reconstruction-only pre-bookmark anchors. A monthly USA owner effect completes the Lenovo Mobility transfer.                                                                             | Four bounded variables: radio depth, semiconductor control, software integration and brand cohesion. Seven mutually exclusive outcomes; `.24` is terminal and reconstruction ends at `USA_motorola_reconstruct_complete`.                                         | Motorola owns its transaction and seam flags and invokes exact Lenovo owner effects for the bilateral transfer. Outcomes Only reconstructs silently; Full performs one terminal recovery. Off creates no Motorola state.                                                                                    | **1.** Added as Tier 1.                                                                                                                                                    |
| `TAI_foxconn_events`  | `.1-.15`, `.20-.23`, hidden `.90`; 2000-01-31 to 2026-05-31 | Full mode owns `.90`, the January 1 scheduler and every dated yearly call. `.7` opens the USA-scoped Wisconsin response `.8`, which returns to Taiwan through `.9`.                                                                                                                                                         | Four bounded variables: geographic resilience, customer diversification, technology depth and labour governance. Twelve ideas include four mutually exclusive terminal outcomes; `.15` is terminal and reconstruction ends at `TAI_foxconn_reconstruct_complete`. | Reads only `USA_apple_supplier_diversification`. Taiwan owns company state; the USA owns its recipient-local Wisconsin response flags. Outcomes Only is silent and idempotent; Full has terminal recovery that defers while the capstone choice is open. The old duplicate `.1` queue in `.90` was removed. | **1.** Added as a grandfathered Tier 1 chain because its nineteen visible milestones exceed the nominal event budget but otherwise satisfy the full contract.              |
| `ISR_oem_events`      | `.1-.10`, hidden `.90`; 2000-03-01 to 2001-10-28            | `.90` reconstructs and delegates to an exact January 1 current-year scheduler. The 2001 yearly driver provides the next-year anchor; a bounded daily ISR hook recovers unresolved milestones on their exact dates for non-January starts.                                                                                   | Three bounded strategy scores, ten milestone resolution flags, four baseline ideas and three mutually exclusive strategy ideas. `ISR_oem_resolve_strategy` is the terminal resolver.                                                                              | No external reads or writes. Reconstruction is silent. Per-milestone scheduled/resolved guards prevent the January scheduler and exact-date recovery from double-queuing; the next calendar year is still scheduled normally.                                                                               | **5.** This is a national multi-company electronics survey rather than one corporate owner, so it remains standalone historical flavour.                                   |
| `gpu_development`     | `.1-.9`; 2000-04-20 to 2024-04-30                           | `00_yearly_effects.txt` dispatches per participating tag. Startup reconstruction and a per-tag January 1 scheduler cover USA, CAN, TAI, KOR, CHI and JAP as applicable. There are no event-to-event calls.                                                                                                                  | No bounded variables. Each country owns `gpu_development_N_resolved` plus its selected route flags; three shared ideas model demand and capacity. `.9` is the final milestone, not a corporate capstone.                                                          | Deliberately crosses six country scopes and is independent of the Corporate History rule. Reconstruction applies only local durable state and suppresses already-resolved calls.                                                                                                                            | **2 recommended.** A future lighter contract should check per-tag dispatch parity, milestone uniqueness and reconstruction coverage without inventing one corporate owner. |
| `USA_oem_events`      | `.1-.23`; 2000-2026                                         | Mixed yearly anchors in `00_yearly_effects.txt`; `.4→.5`, `.6→.7` and `.8→.9` are direct subchains. The 2000 Dell anchor `.13` is now date-gated so late bookmarks do not receive an obsolete popup.                                                                                                                        | Mixed Palantir, defence-technology, Dell and storage flags plus unbounded `USA_oem_storage_policy`. It has no ideas, reconstruction effect or common terminal marker; `.23` is only the final storage event.                                                      | No formal covered-chain reads. Late starts intentionally do not synthesize this heterogeneous namespace's prior player rewards or choices; storage policy therefore defaults when its earlier events were not played.                                                                                       | **5.** Keep as legacy standalone flavour. A future refactor should split Dell, Palantir and storage into owner-coherent namespaces before contract adoption.               |

## Ownership declarations

- TI owns `USA_ti*` and `USA_stack_ti*`.
- Micron owns `USA_micron*`, `USA_stack_micron*` and the neutral
  `USA_stack_txn_lehi*` transaction state.
- Motorola owns `USA_motorola*`, `USA_stack_motorola*`,
  `USA_stack_seam_motorola*` and `USA_stack_txn_motorola*`.
- Foxconn company state is TAI-owned (`TAI_foxconn*`); `USA_foxconn*` is the
  explicitly scoped recipient response.
- IBM's manifest ownership was narrowed from the broad `USA_oem*` prefix to its
  five exact bounded `USA_oem_*` variables. This prevents the unrelated legacy
  `USA_oem_events` flags from being claimed by IBM.
- Lenovo owns `CHI_lenovo*`. Its IBM and Motorola integrations use exact
  manifest-declared reads and owner-effect calls; IBM remains the sole scheduler
  for Lenovo event `.1`.

Nokia's French and German response namespaces remain Nokia-owned callbacks
(decision 4), not independent chains. No other unregistered reconstruction root
was found beyond Israel OEM and the deliberately independent GPU system.

## Physical compute stack

`USA_physical_compute_stack_resolve` is a recalculated shared aggregate, not a
fourth company chain.

- TI must have a resolved capstone and `USA_stack_ti_foundational_viable`.
- Micron must have a resolved capstone and `USA_stack_micron_memory_viable`.
- Motorola must have a resolved capstone and
  `USA_stack_motorola_communications_viable`.
- The aggregate then requires more than one of four seams: the TI/Micron Lehi
  bridge, TI/Motorola embedded interoperability, Motorola interoperable
  communications, and Motorola PowerPC continuity.
- Only the shared resolver writes `USA_stack_physical_capstone_resolved`.
  Failure remains possible when the three supplier outcomes or two required
  seams are absent; the resolver removes the aggregate idea and clears success.
- Reconstruction calls the aggregate from each supplier resolver. Micron is
  reconstructed before TI in Outcomes Only, and terminal Full-mode recovery
  prevents a milestone missed during collapse from permanently blocking the
  stack.

The aggregate's recommended disposition is decision 2 for future focused validation: check its three
producer calls, exact prerequisite flags, seam threshold, four shared ideas and
the single-writer success flag.

## Localisation and validation coverage

English localisation coverage is complete for the audited namespaces: 748
referenced target-prefixed keys, 748 definitions, zero missing keys, zero
orphans and zero duplicate target-prefixed keys. All relevant English files
retain their UTF-8 BOM and `l_english:` header. Non-English localisation was not
reviewed or modified.

The existing strict corporate-history validator now covers TI, Micron, Motorola,
Foxconn, and Lenovo for caller ownership, scheduling, reconstruction, bounded
state where applicable, outcome cleanup, completion markers, and exact
cross-chain exceptions. Israel OEM, GPU development, and the legacy USA
namespace remain explicitly outside that formal contract for the reasons above.
