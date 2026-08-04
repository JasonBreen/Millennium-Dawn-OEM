# U.S. OEM Economic Bridge Map

How U.S. corporate-history chains reach the national economy. Read this before
changing `common/scripted_effects/USA_corporate_systems_effects.txt` or any
`USA_oem_*` variable.

## Layers

```
base axes (USA_oem_*)            written by the IBM and Sun/Microsoft chains
  + company contributions        USA_oem_contribution_* temp vars, rebuilt every bridge call, capped -3..+3
  = effective axes               USA_oem_effective_*, clamped 0..10
  -> integration score           sum of the five effective axes (0..50)
  -> one economic idea           USA_corporate_systems_economic_integration_1..5
```

Two persistent variable sets survive a bridge call: `USA_oem_effective_*` and
`USA_oem_applied_*`, the post-clamp delta (`effective - base`). The dashboard
shows the applied delta, not the raw capped contribution, so `base + shown
delta = effective` holds even when an axis sits on the `0` or `10` boundary and
part of the contribution is absorbed. The accumulators themselves are temp
variables and never persist.

`USA_corporate_systems_update_economic_bridge` is the only place any of this is
computed. It never writes the base axes, so every existing event, policy,
reconstruction effect and tooltip that mutates `USA_oem_*` keeps working
unchanged.

### Idempotency

`USA_corporate_systems_rebuild_company_contributions` sets all five temp
accumulators to `0` and rebuilds them from current flags and ideas on every call.
Nothing accumulates across monthly ticks, reloads, or repeated Outcomes Only
catch-up. `USA_corporate_systems_rebuild_effective_axes` likewise recomputes each
effective axis and each applied delta with `set_variable`, never `add_to`.

### Update triggers

| Trigger                                                                                                                              | Call site                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| Monthly U.S. Corporate History driver                                                                                                | `USA_corporate_history_monthly_outcomes`                     |
| Each of the four Corporate Systems government policies                                                                               | `common/decisions/USA_corporate_systems_dashboard.txt`       |
| Apple, Dell and NVIDIA capstones                                                                                                     | `USA_<chain>_resolve_capstone`                               |
| TI, Micron and Motorola capstones (shared exit)                                                                                      | `USA_physical_compute_stack_resolve`                         |

Google, Oracle and HP have no capstone resolver - their terminal flags land in
event options - so they refresh on the next monthly tick (at most ~31 days).

## Chain-to-axis mapping

Axes: **OS** open standards, **VI** vertical integration, **SR** supply
resilience, **SC** security control, **NCS** national compute stack.
Every branch is mutually exclusive within its chain unless noted.

| Chain    | Outcome/state used                                                          | Axis contribution | Rationale                                                                        | Max impact |
| -------- | --------------------------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------- | ---------- |
| Apple    | `USA_apple_outcome_private_computing`                                        | VI +1, SR +1      | Capstone gate requires `USA_apple_silicon_autonomy >= 6`: own silicon, own stack | 2          |
| Apple    | `USA_apple_outcome_integrated_device`                                        | VI +1, OS -1      | Gate requires ecosystem control >= 8 and services dependence >= 7                | 2          |
| Apple    | `USA_apple_outcome_resilient_silicon`                                        | SR +1             | Gate requires supply resilience >= 7 and China exposure <= 4                      | 1          |
| Apple    | `USA_apple_outcome_regulated_services`                                       | OS +1, VI -1      | Regulatory unbundling opens interfaces and breaks integration                     | 2          |
| Apple    | `USA_apple_outcome_premium_device`                                           | none              | Residual consumer-hardware outcome; no national compute consequence               | 0          |
| HP       | `USA_hp_full_enterprise_stack`                                               | VI +1, NCS +1     | Services and software retained inside one enterprise systems vendor               | 2          |
| HP       | `USA_hp_services_and_software_spun_off`                                      | VI -1             | Enterprise estate broken up; historical default                                   | 1          |
| NVIDIA   | idea `USA_nvidia_cuda_fortress`                                              | NCS +1, OS -1     | Fortress route sets `USA_nvidia_ecosystem_openness -2`                            | 2          |
| NVIDIA   | idea `USA_nvidia_open_accelerator_commonwealth`                              | OS +1, NCS +1     | Open accelerator ecosystem with retained depth                                    | 2          |
| NVIDIA   | idea `USA_nvidia_sovereign_compute_stack`                                    | NCS +1            | State-aligned capacity without an openness change                                 | 1          |
| NVIDIA   | idea `USA_nvidia_hybrid_national_champion`                                   | OS +1             | Hybrid route sets `USA_nvidia_ecosystem_openness +1`                              | 1          |
| NVIDIA   | idea `USA_nvidia_commodity_decline`                                          | NCS -1            | Accelerator leadership lost                                                       | 1          |
| Dell     | `USA_dell_outcome_ai_backbone`                                               | NCS +1, SR +1     | Gate requires enterprise pivot >= 8 plus an AI server buildout flag               | 2          |
| Dell     | `USA_dell_outcome_integrated_federation`                                     | NCS +1            | Integrated infrastructure federation                                              | 1          |
| Dell     | `USA_dell_outcome_direct_manufacturer`                                       | SR +1             | Gate requires direct-model strength >= 7: domestic build-to-order capacity        | 1          |
| Dell     | `USA_dell_outcome_founder_empire`                                            | none              | Ownership structure, not an industrial-capacity outcome                           | 0          |
| Dell     | `USA_dell_outcome_leveraged_restructurer`                                    | SR -1             | Fallback outcome: leverage without manufacturing depth                            | 1          |
| TI       | `USA_ti_capstone_resolved` + `USA_stack_ti_foundational_viable`              | SR +1, NCS +1     | Foundational analog/embedded pillar viable                                        | 2          |
| TI       | `USA_ti_capstone_resolved` without the viability flag                        | NCS -1            | Capstone reached with a foundational capability gap                               | 1          |
| Micron   | `USA_micron_capstone_resolved` + `USA_stack_micron_memory_viable`            | SR +1, VI +1      | Domestic memory pillar viable                                                     | 2          |
| Micron   | `USA_micron_capstone_resolved` without the viability flag                    | SR -1             | Memory supply hollow at the capstone                                              | 1          |
| Motorola | `USA_motorola_capstone_resolved` + `USA_stack_motorola_communications_viable`| SC +1             | Mission-critical and public-safety communications retained                        | 2 combined |
| Motorola | `USA_motorola_capstone_resolved` + `USA_stack_motorola_embedded_viable`      | NCS +1            | Embedded/semiconductor pillar retained (`intact`, `embedded` capstones)           | (see above)|
| Google   | `USA_google_antitrust_structural_separation`                                 | NCS -1            | Break-up removes a coherent national platform                                     | 2 combined |
| Google   | `USA_google_tpu_sovereign_scale` (no structural separation)                  | NCS +1            | Owned accelerator fleet at national scale                                         | (see above)|
| Google   | `USA_google_android_licensing_rentier`                                       | OS -1             | Licensing rent extraction closes the mobile platform                              | (see above)|
| Google   | `USA_google_android_open_stack` (not rentier)                                | OS +1             | Open mobile stack                                                                 | (see above)|
| Oracle   | `USA_oracle_event_12_resolved` + maturity (see below)                        | VI +1             | Migrated maturity bonus: database, middleware and cloud under one vendor          | 2 combined |
| Oracle   | `USA_oracle_java_api_victory`                                                | OS -1             | API copyright control closes a shared runtime                                     | (see above)|
| Oracle   | `USA_oracle_sun_commons` (no Java API victory)                               | OS +1             | Sun estate released to the commons                                                | (see above)|

Motorola, Google and Oracle each evaluate two independent gates on two different
axes, so their combined absolute impact is still capped at two points. Every
other chain resolves one mutually exclusive branch.

Oracle's maturity gate is `USA_oracle_event_12_resolved` plus any of
`USA_oracle_cloud_public_sector`, `USA_oracle_platform_scale > 8`,
`USA_oracle_execution_discipline > 5`, `USA_oracle_infrastructure_depth > 5`.
The three variables are only written by `events/USA_oracle_events.txt`; neither
reconstruction path sets them, so `USA_oracle_cloud_public_sector` - which
`USA_oracle_reconstruct_history` does set at 2019.10.15 - carries the same
maturity meaning for reconstructed games and keeps Full and Outcomes Only in
step.

## Deliberate exclusions

| Chain             | Why it is not in the contribution layer                                                                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IBM               | Owns the base axes (`tools/corporate_history_contract.json` lists `USA_oem_*` under IBM's `owned_prefixes`). Its whole ladder already moves the base; a contribution would count the same state twice. |
| Sun/Microsoft     | Declared `allowed_writes` include all five `USA_oem_*`. Every terminal option in `events/USA_sun_microsoft_events.txt` writes base axes directly (cross-platform, Windows primacy, OpenAI triad, security-first). Adding a contribution would double count. |
| Xbox              | Consumer entertainment platform. Its national effect is already delivered by its own five outcome ideas, and its parent's platform posture is in the base through Sun/Microsoft.                       |
| E3                | Trade-show and industry-convening chain. No industrial-compute state; forcing it onto a compute axis would be coverage theatre.                                                                        |
| AIG               | Financial-crisis resolution regime. Belongs to bank-resolution policy, not the compute economy.                                                                                                       |
| Foreign chains    | Lenovo, Sony, Nintendo, ATI/AMD, Matrox, BlackBerry, Nokia, Siemens, Ericsson, TSMC, Foxconn and Polish Industrial Sovereignty are other nations' industrial models and never enter the U.S. score.    |

## Retired scalar adjustments

The pre-existing bridge applied three ad hoc adjustments directly to the score.
All three are gone; the same underlying facts now move axes:

| Retired adjustment                                                                     | Replacement                                                                                        |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `USA_stack_physical_capstone_resolved` -> score +1; three capstones without it -> score -1 | Per-pillar viability contributions from TI, Micron and Motorola                                     |
| `USA_oracle_event_12_resolved` + platform/execution/infrastructure thresholds -> score +1 | Same gate, widened with `USA_oracle_cloud_public_sector`, now VI +1                                  |
| `USA_google_antitrust_structural_separation` + `USA_google_platform_scale < 0` -> score -1 | `USA_google_antitrust_structural_separation` -> NCS -1                                              |

None of the three survives as a scalar score adjustment, and no fact is counted
in both places.

The retired Oracle and Google adjustments read variables
(`USA_oracle_platform_scale`, `USA_oracle_execution_discipline`,
`USA_oracle_infrastructure_depth`, `USA_google_platform_scale`) that only the
Full-mode event files ever write. Neither `USA_oracle_reconstruct_history` nor
`USA_google_reconstruct_history` sets them, so in Outcomes Only they always read
`0` and the adjustments could never fire. Oracle's gate now also accepts a
reconstructed flag, and Google's is flag-only, so Full and Outcomes Only reach
the same effective state for the same reconstructed history.

`USA_google_platform_scale` no longer gates anything. It is one-shot state that
only the structural-separation option writes and its tooltip advertises, so it
is surfaced on the dashboard instead
(`USA_corporate_systems_google_separation`).

## Balance

Method: `USA_*_reconstruct_history` ladders traced deterministically over monthly
Outcomes Only ticks from 2000.1 to 2027.3, then
`USA_corporate_systems_update_economic_bridge` evaluated against the resulting
state. Alternative routes steer IBM/Sun-Microsoft option deltas and company
terminal flags from the same source files. These are script-level traces, not
in-game measurements.

Axis order below: OS / VI / SR / SC / NCS.

| Case                       | Base           | Contribution (capped) | Applied delta  | Effective      | Score | Tier           |
| -------------------------- | -------------- | --------------------- | -------------- | -------------- | ----- | -------------- |
| Historical default, before | 10/3/2/10/10   | -                     | -              | -              | 36    | 4 Integrated   |
| Historical default, after  | 10/3/2/10/10   | 0/+2/+3/+1/+3         | 0/+2/+3/0/0    | 10/5/5/10/10   | 40    | 5 Strategic    |
| Open and interoperable     | 10/2/2/10/10   | +2/+2/+2/+1/+3        | 0/+2/+2/0/0    | 10/4/4/10/10   | 38    | 5 Strategic    |
| Integrated but closed      | 10/2/2/10/10   | -3/+3/+3/+1/+3        | -3/+3/+3/0/0   | 7/5/5/10/10    | 37    | 4 Integrated   |
| Fragmented / adverse       | 10/3/1/10/10   | -3/-1/-2/+1/-1        | -3/-1/-1/0/-1  | 7/2/0/10/9     | 28    | 3 Balanced     |

The applied-delta column is what the dashboard shows: the gap between it and the
capped contribution is the part absorbed by the `0..10` axis clamp.

Aggregate bounds after the `-3..+3` per-axis cap, enumerated over every
combination of mutually exclusive branches:

- maximum **+13** (`+3/+3/+3/+1/+3`)
- minimum **-8** (`-2/-1/-2/0/-3`)

The cap binds on four axes before it is applied (raw open standards reaches
`+-4`, raw vertical integration `+4`, raw supply resilience `+4`, raw national
compute stack `+6`), so `-3..+3` is doing real work rather than sitting
unreachable. A narrower cap was evaluated and rejected: at `-2..+2` the
historical default still scores 39 and the open route still scores 38, because
the binding constraint is the `0..10` axis clamp, not the cap.

### Thresholds

Unchanged at `<15 / <22 / <29 / <38 / >=38`. The historical default moves from
36 (Integrated) to 40 (low Strategic), which is the intended correction: nine
mature chains that previously contributed nothing now do, and that route ends
with an operational physical compute stack, a resolved Dell AI backbone, a
sovereign Google TPU fleet, a mature Oracle platform and viable
TI/Micron/Motorola pillars. Strategic is not automatic - the closed route lands
at 37 and the adverse route at 28, two tiers below where its own base sits - and
the open route sits exactly on the 38 boundary, so a single bad company outcome
still drops it back to Integrated.

### Known concentration

The IBM/Sun-Microsoft base ladders drive open standards, security control and
national compute stack to the `10` ceiling on essentially every long route.
Positive contributions on those three axes are therefore usually absorbed by the
`0..10` clamp - Motorola's security-control point in particular is almost always
invisible - and the contribution layer's visible upside concentrates on vertical
integration and supply resilience, the two axes the base leaves low. Negative
contributions still bite on all five. This is a property of the base layer, not
of the aggregation, and is the main reason the cap value barely moves any traced
outcome.
