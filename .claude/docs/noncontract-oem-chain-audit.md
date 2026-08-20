# Non-Contract OEM Chain Audit

This audit covers the namespaces that began outside the owner-chain contract and
the shared physical-compute aggregate. Schema v6 now registers the remaining
independent systems explicitly, so "non-contract" describes their origin rather
than a validation exemption.

## Inventory and contract decisions

Decision key:

1. Add to `tools/corporate_history_contract.json`.
2. Add a separate lighter-weight validation contract.
3. Leave outside with documented reasons.
4. Refactor into an existing owner chain.
5. Treat as standalone historical flavour.

| Namespace             | Range and dates                                                    | Scheduling and direct calls                                                                                                                                                                                                                                                                                                                                                 | Persistent state and terminal state                                                                                                                                                                                                                               | Cross-chain API and late-start behaviour                                                                                                                                                                                                                                                                    | Decision                                                                                                                                                             |
| --------------------- | ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CHI_lenovo_events`   | `.1-.8`, legacy hidden `.90`; 2004-12-09 to 2014                   | IBM's owner effect is the sole caller of `.1` after the PC transaction; CHI's local bootstrap invokes Lenovo's reconstruction and scheduler directly; the 2014 dispatcher and current-year scheduler own `.7`, with the CHI monthly driver recovering lost delivery; `.1` branches into `.2`, `.5` or `.6`, while `.7` can lead to `.8`. The legacy `.90` is not scheduled. | No bounded variables. Lenovo owns the PC, System x and Motorola Mobility route flags and six milestone ideas. The durable terminal marker is `CHI_lenovo_reconstruct_complete`, set after the PC, brand, and System x routes resolve.                             | Reads exact IBM transaction routes and Motorola ownership. IBM and Motorola invoke narrow Lenovo owner effects. Outcomes Only reconstructs silently and idempotently; Full retries lost follow-ups and interrupted stages; Off creates no Lenovo state.                                                     | **1.** Registered as a Tier-2 IBM/Motorola satellite with exact bilateral owner-effect permissions.                                                                  |
| `USA_ti_events`       | `.12-.20`, legacy hidden `.90`; 1997-07-02 to 2026-02-04           | USA's local bootstrap, monthly recovery, and yearly dispatcher own the Full-mode schedule for `.14-.16` and `.18-.20`; Micron `.15` calls TI `.17`. `.12/.13` are reconstruction-only pre-bookmark anchors, and legacy `.90` is not scheduled.                                                                                                                              | Four bounded variables: embedded reach, DSP leadership, manufacturing control and defence integration. Six mutually exclusive outcomes; `.20` is terminal and reconstruction ends at `USA_ti_reconstruct_complete`.                                               | Reads Micron's `.15` marker and the three exact Lehi transaction flags. Outcomes Only reconstructs silently after Micron; Full performs one terminal recovery if a milestone was missed while collapsed. Off creates no TI state.                                                                           | **1.** Added as Tier 1.                                                                                                                                              |
| `USA_micron_events`   | `.6-.20`, legacy hidden `.90`; 1998-12-31 to 2025-06-12            | USA's local bootstrap, monthly recovery, and yearly dispatcher own the Full-mode schedule for `.8-.20`; `.15` calls TI `.17`. `.6/.7` are reconstruction-only pre-bookmark anchors, and legacy `.90` is not scheduled.                                                                                                                                                      | Four bounded variables: process lead, cycle discipline, US fab commitment and HBM position. Six mutually exclusive outcomes; `.20` is terminal and reconstruction ends at `USA_micron_reconstruct_complete`.                                                      | Canonically owns `USA_stack_txn_lehi_*`; the only cross-write is the declared call to `USA_ti_events.17`. Outcomes Only is silent and idempotent. Full performs one terminal recovery after collapse. Off creates no Micron state.                                                                          | **1.** Added as Tier 1.                                                                                                                                              |
| `USA_motorola_events` | `.12-.24`, legacy hidden `.90`; 1991-01-01 to 2025-08-06           | USA's local bootstrap, monthly recovery, and yearly dispatcher own the Full-mode schedule for `.17-.24`; the scheduler also restores 2000 `.16`. `.12-.15` are reconstruction-only pre-bookmark anchors, legacy `.90` is not scheduled, and a monthly USA owner effect completes the Lenovo Mobility transfer.                                                              | Four bounded variables: radio depth, semiconductor control, software integration and brand cohesion. Seven mutually exclusive outcomes; `.24` is terminal and reconstruction ends at `USA_motorola_reconstruct_complete`.                                         | Motorola owns its transaction and seam flags and invokes exact Lenovo owner effects for the bilateral transfer. Outcomes Only reconstructs silently; Full performs one terminal recovery. Off creates no Motorola state.                                                                                    | **1.** Added as Tier 1.                                                                                                                                              |
| `TAI_foxconn_events`  | `.1-.15`, `.20-.23`, legacy hidden `.90`; 2000-01-31 to 2026-05-31 | Taiwan's local bootstrap, monthly recovery, and yearly dispatcher own every Full-mode dated call. `.7` opens the USA-scoped Wisconsin response `.8`, which returns to Taiwan through `.9`; legacy `.90` is not scheduled.                                                                                                                                                   | Four bounded variables: geographic resilience, customer diversification, technology depth and labour governance. Twelve ideas include four mutually exclusive terminal outcomes; `.15` is terminal and reconstruction ends at `TAI_foxconn_reconstruct_complete`. | Reads only `USA_apple_supplier_diversification`. Taiwan owns company state; the USA owns its recipient-local Wisconsin response flags. Outcomes Only is silent and idempotent; Full has terminal recovery that defers while the capstone choice is open. The old duplicate `.1` queue in `.90` was removed. | **1.** Added as a grandfathered Tier 1 chain because its nineteen visible milestones exceed the nominal event budget but otherwise satisfy the full contract.        |
| `ISR_oem_events`      | `.1-.10`, legacy hidden `.90`; 2000-03-01 to 2001-10-28            | Israel's native monthly owner reconstructs passed state and schedules or recovers future milestones. Full is the only event-dispatch mode; legacy `.90` is not scheduled.                                                                                                                                                                                                   | Three bounded strategy scores, ten milestone resolution flags, four baseline ideas and three mutually exclusive strategy ideas. `ISR_oem_resolve_strategy` is the terminal resolver.                                                                              | No external reads or writes. Outcomes Only reconstruction is silent and idempotent; Off reaches neither scheduling nor reconstruction.                                                                                                                                                                      | **Schema v6 independent subsystem.** National multi-company electronics flavour with explicit event IDs, ISR ownership, reconstruction, scheduler, and effect roots. |
| `gpu_development`     | `.1-.9`; 2000-04-20 to 2024-04-30                                  | The shared GPU dispatcher is the only reconstruction and scheduling owner. Native monthly hosts cover USA, CAN, TAI, KOR, CHI, and JAP as applicable; ATI/AMD no longer nests a second GPU reconstruction.                                                                                                                                                                  | No bounded variables. Each country owns `gpu_development_N_resolved` plus its selected route flags; three shared ideas model demand and capacity. `.9` is the final milestone, not a corporate capstone.                                                          | Crosses six declared owner tags. Full schedules visible events, Outcomes Only reconstructs local durable state silently, and Off is inert.                                                                                                                                                                  | **Schema v6 independent subsystem.** Exact event IDs and a single authoritative effect root are validated.                                                           |
| `USA_oem_events`      | `.1-.23`; 2000-2026                                                | USA's native monthly owner is the only external scheduling host; `.4→.5`, `.6→.7` and `.8→.9` remain internal subchains. Dell and storage handoffs use their declared USA roots.                                                                                                                                                                                            | Mixed Palantir, defence-technology, Dell and storage flags plus bounded or guarded legacy state. Explicit reconstruction roots record reached durable history without replaying player rewards.                                                                   | Full schedules eligible events, Outcomes Only reconstructs reached state silently, and Off creates no legacy OEM/storage state. Linux's base route remains independent and cannot synthesize storage history while Corporate History is Off.                                                                | **Schema v6 independent subsystem.** Legacy heterogeneous flavour remains one registered unit for RC safety; a later namespace split is still desirable.             |

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
(decision 4), not independent chains. Israel OEM, GPU Development, and legacy
U.S. OEM/storage now have explicit schema-v6 ownership; no unregistered direct
on-action dispatch or reconstruction root is permitted.

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

The aggregate is registered as the schema-v6 `derived_only` Physical Compute
Stack subsystem. Validation requires its declared producer/reconstruction roots,
exact prerequisite flags, seam threshold, four shared ideas, and single-writer
success flag while forbidding an independent event scheduler.

## Localisation and validation coverage

English localisation coverage is complete for the audited namespaces: 748
referenced target-prefixed keys, 748 definitions, zero missing keys, zero
orphans and zero duplicate target-prefixed keys. All relevant English files
retain their UTF-8 BOM and `l_english:` header. Non-English localisation was not
reviewed or modified.

The strict corporate-history validator covers owner chains and the schema-v6
independent registry for caller ownership, explicit event IDs, scheduling,
reconstruction, mode separation, bounded state where applicable, outcome
cleanup, completion markers, and exact cross-chain exceptions. It rejects
ABK/global singleton hosting, undeclared direct dispatch, duplicate GPU/ATI
ownership, and a derived aggregate with an event scheduler.
