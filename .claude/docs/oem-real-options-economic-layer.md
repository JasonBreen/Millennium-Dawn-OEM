# OEM Real-Options Economic Layer

The U.S. Corporate Systems layer treats a large compute-sector investment as a
real option: the country may preserve a valuable opportunity even when current
financing or infrastructure makes immediate construction unattractive. It is a
strategic abstraction for semiconductor, cloud, data-center, and national
compute capacity. It is not a stock-price or daily financial-market model.

## Ownership and cadence

`USA_corporate_systems_update_economic_bridge` rebuilds the five effective OEM
axes and calls `USA_oem_update_real_options_economy` exactly once. The new
updater is the sole owner of all `USA_oem_option_*`, diffusion, industrial,
infrastructure, readiness, and employment-outlook outputs. It also owns all
four dynamic-modifier families.

The existing bridge already runs:

- monthly through `USA_corporate_history_monthly_outcomes`;
- after each Corporate Systems policy;
- after corporate capstones that refresh the bridge;
- during startup and Outcomes Only reconstruction through the shared monthly
  path.

No daily or global polling was added. Every output is rebuilt from current
source state. Corporate History Off, collapsed nations, and incomplete U.S.
state clear the outputs and remove all OEM economic dynamic modifiers.

## Real-options formula

The high-precision reference is the Black-Scholes call formula:

```text
C = S * N(d1) - K * exp(-rT) * N(d2)
d1 = (ln(S/K) + (r + sigma^2/2)T) / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)
```

HOI4 script math has no confirmed natural logarithm, exponential, square root,
or normal CDF. The game implementation therefore uses only supported
arithmetic, comparisons, branches, and clamps:

- `S` and `K` are clamped to `1..100`.
- `r` converts `interest_rate` from percentage points with `* 0.01`, then
  clamps to `0..0.25`.
- `sigma` clamps to `0.05..1.00`.
- `T` is an integer lookup from `1..5`.
- `ln(S/K)` uses the first five terms of the atanh series after clamping the
  ratio to `0.25..4`: `2z(1 + z^2/3 + z^4/5 + z^6/7 + z^8/9)`, where
  `z = (S/K - 1) / (S/K + 1)`.
- `sqrt(T)` uses constants for the five permitted horizons.
- `exp(-rT)` uses the bounded Pade `[2/2]` approximation
  `(1 - x/2 + x^2/12) / (1 + x/2 + x^2/12)`, with `x = rT` clamped to
  `0..1.25`.
- `N(d)` is a symmetric, monotonic, piecewise-linear lookup at
  `|d| = 0, 0.5, 1, 1.5, 2, 2.5, 3`, using values
  `0.5, 0.69146, 0.84134, 0.93319, 0.97725, 0.99379, 0.99865`.
  Inputs saturate outside `-3..3`, and every CDF output clamps to `0..1`.

`USA_oem_option_call_value` is clamped to `0..S`. Because `S` and `K` are
already normalized scores, raw `C` is itself bounded to `0..100` and is copied
to both `USA_oem_option_value` and `USA_oem_option_value_normalized`. It should
not be read as a dollar return.

## Input derivation

| Output             | Main sources                                                                                       |     Bounds |
| ------------------ | -------------------------------------------------------------------------------------------------- | ---------: |
| Asset value `S`    | Effective Open Standards, National Compute Stack, Supply Resilience, productivity, active programs |     1..100 |
| Exercise cost `K`  | Vertical Integration, Supply Resilience, Security Control, debt ratio, treasury relief             |     1..100 |
| Financing `r`      | Current `interest_rate` converted from percentage points                                           |    0..0.25 |
| Volatility `sigma` | Supply, security, openness, energy shortfall, debt, unemployment                                   | 0.05..1.00 |
| Horizon `T`        | Vertical Integration plus National Compute Stack, with consortium support                          |       1..5 |

The model reads the effective axes, not individual company outcome flags. Those
outcomes have already been aggregated by the economic bridge, so rereading them
would double-count corporate history.

Live-input weights are scaled against the 2000 U.S. baseline rather than small-
country counts. Productivity contributions use `(overall_productivity - 500)`
with slopes of `0.01..0.02`; the initial U.S. value of 1200 therefore retains
growth headroom. Industrial complexes, offices, microchip plants, and internet
stations use weights of `0.15`, `0.2`, `0.75..1`, and `0.1` respectively. The
microchip components cap at 40 plants, leaving room for the capacity program to
reinforce building growth across the 2000-2026 span.

## Secondary scores and tiers

All secondary scores are rebuilt and clamped to `0..100`.

- Innovation Diffusion combines Open Standards, National Compute Stack,
  productivity, internet capacity, and relevant active programs. Its four
  tiers begin at 0, 25, 50, and 75.
- Industrial Depth combines Vertical Integration, Supply Resilience,
  industrial facilities, microchip plants, and capacity grants. Its four tiers
  begin at 0, 25, 50, and 75.
- Compute Demand combines National Compute Stack, offices, civilian chip use,
  productivity, and demand created by active programs.
- Compute Capacity combines Supply Resilience, Security Control, microchip
  plants, internet infrastructure, energy fulfillment, and capacity programs.
- Infrastructure Pressure is `demand - capacity + 50`. Its five tiers begin at
  0, 20, 40, 60, and 80.
- Investment Readiness combines option value, diffusion, industrial depth,
  infrastructure capacity, and security, then subtracts pressure above the
  balanced midpoint. Volatility may therefore raise the value of waiting while
  current readiness remains low.

The investment-climate family uses investment readiness at 0, 20, 40, 60, and
80, so uncertainty alone cannot produce an investment boom. Modifier effects
are intentionally small. Diffusion and the computing consortium share the
percentage-typed country productivity modifier, reaching at most `+3%`
together. Existing Corporate
Systems ideas remain the authority for corporate-tax and investment-cost
effects; the climate family mainly adjusts project duration and bureaucracy.
The diffusion, depth, and pressure families provide separate economy-wide
spillovers and bottleneck effects. Every refresh removes all siblings before
adding exactly one tier. No `force_update_dynamic_modifier` is used.

## Government programs and AI

Each Corporate Systems policy preserves its existing Political Power, Treasury,
and long-term company-state effects, and now grants one visible timed idea.
Procurement and security run for 180 days; the larger capacity and consortium
programs run for 365 days. Each decision uses the same re-enable period as its
timed idea and blocks renewal while active, so timed ideas never stack.

| Policy                        | Temporary emphasis                                     | Principal tradeoff                       |
| ----------------------------- | ------------------------------------------------------ | ---------------------------------------- |
| Open Systems Procurement      | Incoming investment, office construction, research     | Bureaucracy and migration cost           |
| Domestic Capacity Grants      | Chip and industrial construction, domestic chip output | Chip demand, energy use, consumer burden |
| Secure Federal Systems        | Cyber defense and federal office construction          | Bureaucracy and compliance cost          |
| Advanced Computing Consortium | Productivity, research, and office construction        | Chip demand and data-center power use    |

AI weights prefer the policy that repairs the weakest relevant axis. Terminal
zero-weight guards cover Corporate History Off, collapse, incomplete state,
bankruptcy, severe fiscal stress, insufficient reserves, and an active copy of
the program. A shared 180-day AI purchase flag prevents policy-family hopping.
Open and Secure routes also set opposing 730-day commitment flags to prevent
oscillation. The capacity policy checks chip shortage, energy fulfillment, and
labor availability; the consortium requires sufficient option value and
readiness.

## Employment outlook

`USA_oem_automation_pressure`, `USA_oem_labor_displacement_pressure`, and
`USA_oem_high_skill_labor_demand` are bounded dashboard outputs only. They make
the later labor-transition interface explicit without altering upstream
employment laws, worker requirements, stability, or social spending in this
change. Displacement gives automation and unemployment equal 50-point ranges;
the fractional unemployment input reaches its component cap at 10 percent.

## Historical balance audit

The static audit follows year-end Outcomes Only reconstruction with normal U.S.
territorial ownership. It does not claim historical policy use.

| Year | Existing permanent route                                                         | Representative new tiers                          |
| ---: | -------------------------------------------------------------------------------- | ------------------------------------------------- |
| 2005 | Integrated bridge and E3 World Industry Marketplace                              | readiness T2, diffusion T3, depth T2, pressure T3 |
| 2010 | Integrated bridge and restored E3 expo                                           | readiness T2, diffusion T3, depth T2, pressure T3 |
| 2015 | Balanced bridge, restored E3 expo, and AIG moral-hazard settlement               | readiness T2, diffusion T3, depth T2, pressure T3 |
| 2020 | Integrated bridge, E3 public hybrid, and AIG settlement                          | readiness T2, diffusion T3, depth T2, pressure T4 |
| 2026 | Strategic bridge, ten company outcomes, E3/IICON, and the physical-compute stack | maximum tier from every family for stress testing |

The simulator adds an all-four-program envelope to every row to expose exact-key
overlaps even though this is not asserted as historical behavior. In the 2026
maximum-stack row, notable totals are research speed `+13%`, office productivity
`+16%`, maximum factory efficiency `+25%`, microchip-plant construction `+20%`,
industrial-infrastructure construction `+13%`, country productivity growth
`+3%`, microchip-plant energy use `+13%`, civilian chip demand `+27%`, cyber
defense `+8`, and receiving-investment cost `-8%`. These are static
balance-model totals, not runtime observations.

## Verification and limitations

`tools/analysis/simulate_oem_real_options.py` implements both the exact Python
reference and the script-compatible approximation. Its no-argument run sweeps
the full input grid, checks bounds and monotonic behavior, exercises eight named
economic scenarios, and reports a static historical modifier-stack audit for
2005, 2010, 2015, 2020, and 2026. JSON output is available for automation.

Static validation cannot prove that HOI4 accepts every nested math expression.
An in-game run must still check `error.log`, first-month initialization,
modifier replacement, policy expiry, save and reload, Full and Outcomes Only
parity, Off behavior, and collapse cleanup. The Python tool measures numerical
agreement; it is not runtime evidence.

Possible future work includes Taiwan foundry and electronics capacity, Finnish
communications diffusion, and gameplay effects for the three employment
outlook variables. Those extensions should consume this layer rather than copy
its U.S. model.
