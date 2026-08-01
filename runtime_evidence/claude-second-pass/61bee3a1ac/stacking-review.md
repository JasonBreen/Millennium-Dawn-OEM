# Economic-bridge stacking review — `61bee3a1ac`

Source-derived. Every number read from the file, not from any PR description.

## The bridge formula, as implemented

`common/scripted_effects/USA_corporate_systems_effects.txt:11` —
`USA_corporate_systems_update_economic_bridge`.

```
score = USA_oem_open_standards
      + USA_oem_vertical_integration
      + USA_oem_supply_resilience
      + USA_oem_security_control
      + USA_oem_national_compute_stack        # each 0..10, temp var, never persisted

if   USA_stack_physical_capstone_resolved  and score < 50   -> score += 1
elif not physical capstone
     and USA_ti_capstone_resolved
     and USA_micron_capstone_resolved
     and USA_stack_motorola_capstone_resolved
     and score > 0                                          -> score -= 1
```

Score domain is `0..50`; the guards keep the adjustment inside it. The `else if` is **live,
not dead**: `USA_physical_compute_stack_effects.txt:95` additionally requires three `*_viable`
flags and `USA_stack_seam_count > 1`, so all three pillar capstones can resolve without the
physical capstone.

### Thresholds and tiers

| Score | Idea | Name |
| --- | --- | --- |
| `< 15` | `USA_corporate_systems_economic_integration_1` | Fragmented |
| `15–21` | `..._2` | Exposed |
| `22–28` | `..._3` | Balanced |
| `29–37` | `..._4` | Integrated |
| `>= 38` | `..._5` | Strategic |

Default state is 5 on all five axes (`USA_ibm_effects.txt:5-9`) → score 25 → **Balanced**.
Confirmed by arithmetic; the brief's expected default holds.

### Tier modifiers (`common/ideas/USA_corporate_systems_ideas.txt`)

| Tier | `corporate_tax_income_multiplier_modifier` | `investment_cost_modifier` | `receiving_investment_cost_modifier` |
| --- | --- | --- | --- |
| 1 Fragmented | −0.05 | +0.05 | +0.05 |
| 2 Exposed | −0.02 | +0.02 | +0.02 |
| 3 Balanced | **0** (only modifier on the idea) | — | — |
| 4 Integrated | +0.02 | −0.02 | −0.02 |
| 5 Strategic | +0.05 | −0.05 | −0.05 |

Monotonic in every column, correct signs (lower investment cost is the bonus), no tier is
accidentally worse than the tier below it. All three modifier names verified present in
`common/modifier_definitions/`.

## Overlap analysis

No corporate-history capstone anywhere in the mod uses the bridge's three modifiers **except
the AIG chain**, which is the only real co-stack:

| Source | corporate tax | investment cost | receiving investment cost |
| --- | --- | --- | --- |
| Bridge, Strategic | +0.05 | −0.05 | −0.05 |
| `USA_aig_taxpayer_vindication` | +0.03 | — | — |
| `USA_aig_orderly_resolution_regime` | — | −0.05 | — |
| `USA_aig_liquidationist_precedent` | — | +0.10 | — |
| Bridge, Fragmented | −0.05 | +0.05 | +0.05 |

Plausible maximum combined stacks (AIG outcomes are mutually exclusive, so at most one):

* Best case: Strategic + Taxpayer Vindication → **+0.08 corporate tax**, −0.05/−0.05 investment.
* Best investment case: Strategic + Orderly Resolution → **−0.10 investment cost**, −0.05 receiving.
* Worst case: Fragmented + Liquidationist Precedent → **+0.15 investment cost**, −0.05 corporate tax.

Every other USA corporate capstone (IBM, Apple, Dell, NVIDIA, the three physical pillars and
the physical-stack capstone) operates on a **disjoint modifier set** — `offices_productivity`,
`research_speed_factor`, `research_bonus`, `production_factory_*`, `microchip_plant_*`,
`*_chip_consumption_modifier`, `cyber_defense_rating_modifier`, `intelligence_agency_defense`.
There is no double-count of the same economic lever.

## Verdict: no rebalance required

MD's own magnitude precedent for these keys:

* `corporate_tax_income_multiplier_modifier` across `common/ideas` + `common/national_focus`
  ranges −0.35 … +0.10, with ±0.05 by far the most common value (26 instances at −0.05).
* `investment_cost_modifier` ranges −0.50 … +0.10, with −0.05 and −0.10 the modal values.

A ±0.05 tier and an ±0.08/±0.15 worst-case stack sit inside the ordinary MD band. The brief's
guidance to prefer weakening the new bridge over rewriting established capstones does not need
to be exercised — **nothing here is excessive**, and no change is recommended.

## Canadian side

ATI and Matrox capstones can both be active (different chains, same country) and both are
permanent with no maintenance cost:

| | research | factory efficiency gain | other |
| --- | --- | --- | --- |
| `CAN_ati_integrated_amd_compute_engine` | +0.05 | +0.05 | microchip plant speed +0.05 |
| `CAN_matrox_sovereign_visual_compute` | +0.05 | — | plant speed +0.10, plant productivity +0.10, chip consumption +0.10/+0.15 (cost) |
| combined worst case | **+0.10 research_speed_factor** | +0.05 | plant speed +0.15 |

+10% research speed from two permanent country ideas is noticeable but not out of line with
MD national ideas, and Matrox carries an explicit chip-consumption cost. Advisory only.

One minor advisory: `CAN_ati_absorbed_brand_legacy` (+0.01 research, +0.01 stability) is the
`else`-branch **fallback**, not a failure state, so the right comparison is MD's other
fallbacks, not its failure outcomes:

| Outcome | Kind | Net |
| --- | --- | --- |
| `USA_ibm_stack_in_name_only` | failure | −0.03 research, −0.03 stability, −0.05 offices, −0.05 PP |
| `USA_nvidia_commodity_decline` | failure | −0.03 offices, −0.03 factory gain, +0.01 consumer goods |
| `USA_dell_leveraged_restructurer` | fallback | +0.03 factory gain, +0.01 stability, **+0.01 consumer goods (cost)** |
| `USA_apple_premium_device_economy` | fallback | +0.05 factory gain, +0.03 offices, **+0.05 chip consumption (cost)** |
| `CAN_ati_absorbed_brand_legacy` | fallback | +0.01 research, +0.01 stability, **no cost term** |

ATI's fallback is consistent in sign with the fallback precedent and is the weakest of the
set, but it is the only fallback in the family with no offsetting cost term. Advisory only —
not a defect, and not worth changing without the maintainer's call.
