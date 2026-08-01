# Claude second pass — verification results at `61bee3a1ac`

**Runtime status up front:** desktop control was requested and **denied**
(`mcp__computer-use__request_access` → `user_denied` for Hearts of Iron IV, Steam and File
Explorer). **No HOI4 session was launched, driven, saved, reloaded, or screenshotted in this
pass.** Nothing below is marked as runtime-passed on the strength of source tracing. The only
runtime evidence available is the log set from the previous session, described in
`environment.txt`, which reached 2000.01.06 and therefore never exercised the bridge, the
policies, or any ATI event.

Legend: **SRC-PASS** verified from source · **RT-PASS** verified from runtime artefacts ·
**RT-BLOCKED** requires a live game that could not be run · **FAIL** demonstrated defect ·
**ADVISORY** correct as written, worth a maintainer decision.

---

## D — U.S. Corporate Systems dashboard

`common/decisions/USA_corporate_systems_dashboard.txt`,
`common/decisions/categories/99_USA_decision_categories.txt:15`,
`common/scripted_localisation/USA_corporate_systems_dashboard_scripted_localisation.txt`

| Check | Result |
| --- | --- |
| Five status entries present (Compute Stack, Platform/Cloud, Hardware/OEM, Physical Compute, IBM) | SRC-PASS |
| Category `allowed = { original_tag = USA }` — country-stable, survives civil-war retag | SRC-PASS |
| `visible = { corporate_history_enabled = yes }` → Full and Outcomes Only show it, Off suppresses | SRC-PASS |
| Collapsed USA suppressed (`NOT = { has_country_flag = collapsed_nation }` on the category) | SRC-PASS |
| No IBM-only gate on the category — it uses `corporate_history_enabled`, and entries use `USA_corporate_systems_has_meaningful_state` (14 flags across 8 companies) | SRC-PASS |
| Status entries read-only: `available = { custom_trigger_tooltip { always = no } }`, `cost = 0`, `ai_will_do = { base = 0 }`, no `complete_effect` | SRC-PASS |
| No duplicate decision identifiers | SRC-PASS (`validate_decisions.py` clean) |
| No blank/invalid icons | SRC-PASS (`validate_gfx_references.py` reports no missing sprite for these) |
| No raw localisation | SRC-PASS (`validate_localisation.py` and `validate_scripted_localisation.py` both clean) |
| No stale selectors to removed entries | SRC-PASS (`validate_scripted_localisation.py` unused-check clean) |
| Opening the tab does not initialize or recalculate | SRC-PASS — every entry is inert; the bridge is driven from `on_monthly_USA` only |
| Scripted-loc band ordering (`>7`, `>5`, `=5`, `>2`, fallback) — no general trigger shadows a specific one | SRC-PASS — traced all five axes for values 0–10 |
| IBM "Active Problems" composes correctly | SRC-PASS — `risk_summary` prints "no active risks" only when all seven crisis ideas are absent, else empty, then each crisis status appends its own line |
| Google / Oracle / HP / Microsoft-Sun honesty | SRC-PASS — the entry descriptions explicitly disclose that Oracle has no bounded variables or capstone and that HP reports route milestones only |
| Renders correctly in-game | **RT-BLOCKED** |

## E — Corporate Systems economic bridge

Formula, thresholds, tier modifiers and stacking: see `stacking-review.md`. Behavioural checks:

| Check | Result |
| --- | --- |
| Five shared axes are canonical, initialized to 5 in `USA_ibm_effects.txt:5-9` | SRC-PASS |
| Each axis bounded 0..10 before use | SRC-PASS — every `add_to_variable` on the axes in `USA_ibm_effects.txt` and `USA_microsoft_effects.txt` is followed by `USA_ibm_clamp_state`; the reconstruction ladder clamps once at the end of `USA_ibm_reconstruct_history` before the capstone resolver reads it. Checked programmatically over all 35 mutation sites. |
| Default 5/10 → 25 → Balanced | SRC-PASS |
| Physical-compute adjustment cannot leave `0..50` | SRC-PASS (`score < 50` / `score > 0` guards) |
| The `−1` branch is reachable, not dead | SRC-PASS — physical capstone needs three `*_viable` flags **and** `seam_count > 1` beyond the three pillar capstones |
| Exactly one tier idea active | SRC-PASS — each branch calls `USA_corporate_systems_clear_economic_bridge_ideas` (removes all five) before `add_ideas` |
| Malformed duplicate tier membership repaired | SRC-PASS — the per-tier `OR` fires when the correct idea is missing **or** any wrong idea is present, so a duplicated pair self-heals on the next monthly tick |
| No needless monthly remove/re-add | SRC-PASS — when state already matches, the `OR` is false and nothing runs |
| Off removes stale bridge ideas | SRC-PASS — `USA_corporate_history_monthly_outcomes` is called **unconditionally** from `on_monthly_USA` (`99_USA_on_actions.txt:76`), and the updater's `else` branch clears all five ideas |
| Outcomes Only reconstructs before evaluating | SRC-PASS — the reconstruction block runs earlier in the same effect; the bridge call is the last statement (`00_corporate_history_effects.txt:357`) |
| Civil war follows precedent | SRC-PASS — `allowed = { original_tag = USA }` + `allowed_civil_war = { always = yes }` on all five ideas, matching MD idea convention |
| No global or daily polling | SRC-PASS — single monthly caller, plus one call per policy decision |
| No direct GDP/debt/tax-law/unemployment/cycle mutation | SRC-PASS — the bridge only adds/removes ideas |
| Modifier names valid | SRC-PASS — all three exist in `common/modifier_definitions/`; `validate_modifiers.py` clean |
| Signs correct, tiers monotonic | SRC-PASS |
| Tier changes observed live, save/reload | **RT-BLOCKED** |

**ADVISORY (E-1).** The updater's guard is
`has_country_flag = USA_ibm_state_initialized` **and** `USA_corporate_systems_has_meaningful_state = yes`,
but that trigger's first `OR` member is `USA_ibm_state_initialized`
(`MD_corporate_history_triggers.txt:22-39`). The conjunction therefore reduces to the IBM flag
alone and the second condition can never change the result. Harmless today, but it hides the
fact that the bridge is IBM-gated: a USA game in which IBM never initializes gets no tier idea
at all while the dashboard still reports axis values. Worth either dropping the redundant
trigger or, if the intent was "any company", changing the gate.

**ADVISORY (E-2).** `USA_corporate_systems_economic_integration_3` (Balanced) carries
`modifier = { corporate_tax_income_multiplier_modifier = 0 }`. This is the only zero-valued
instance of that key in the entire mod. It exists to give the idea a body, but HOI4 renders a
zero modifier in the idea tooltip, so Balanced will show a literal "+0.00%" line rather than
nothing. Cosmetic; flagged because it will be visible on the most common tier.

## F — Corporate Systems policy decisions

All four in `common/decisions/USA_corporate_systems_dashboard.txt:111-312`.

| Policy | PP | Treasury | Cooldown | Bankruptcy guard |
| --- | --- | --- | --- | --- |
| Federal Open Systems Procurement | 50 | 10.0bn | `days_re_enable = 365` | yes |
| Domestic Compute Capacity Grants | 75 | 25.0bn | 365 | yes |
| Secure Federal Systems Contracts | 50 | 15.0bn | 365 | yes |
| Advanced Computing Consortium | 50 | 20.0bn | 365 | yes |

| Adversarial check | Result |
| --- | --- |
| 1. Charge treasury but fail to apply effects? | SRC-PASS — no. Charge and effects are consecutive statements in one `hidden_effect`, no intervening conditional. |
| 2. Apply effects without charging? | SRC-PASS — no, same block. |
| 3. Clickable while unaffordable? | SRC-PASS — `custom_cost_trigger` requires `has_political_power > cost-1` **and** `check_variable = { treasury > cost-0.01 }`; HOI4 blocks selection when a custom cost trigger is false. |
| 4. Repeatable through save/reload? | SRC-PASS on script (`days_re_enable` is engine-persisted state, not a script flag). **RT-BLOCKED** for confirmation. |
| 5. Cooldown duration | SRC-PASS — 365 days, and the `_desc` loc states "once every 365 days" for all four. |
| 6. Uninitialized company receiving deltas? | SRC-PASS — every company-specific `*_apply_*` effect is wrapped in `if = { limit = { has_country_flag = <TAG>_<company>_state_initialized } }`. |
| 7. More than one unintended delta? | SRC-PASS — each `apply` effect names its own variables only; traced all 20 apply effects. |
| 8. Clamped immediately? | SRC-PASS — shared axes go through `corporate_history_apply_delta` (clamps 0..10 inline); company variables are followed by `<company>_clamp_state`. |
| 9. Can a policy force a route or capstone? | SRC-PASS — no policy sets a route, outcome, or capstone flag; they move variables only. |
| 10. Does any policy initialize a company chain? | SRC-PASS — no. Every company effect is gated on an existing init flag; nothing calls `*_initialize_state`. |
| 11. Off leaks the category or decisions? | SRC-PASS — category `visible` requires `corporate_history_enabled`. |
| 12. Outcomes Only support | SRC-PASS — reconstruction sets the same `*_state_initialized` flags, so the policies gate identically. |
| 13. Bankruptcy shows a misleading available button? | SRC-PASS — `available = { NOT = { has_active_mission = bankruptcy_incoming_collapse } }` greys it with the standard MD reason. |
| 14. Tooltip matches actual effect | SRC-PASS — compared each `_tt` string line-by-line against its apply effects; all axis and company deltas match, including the negatives (`Vertical Integration −1`, `Open Standards −1`, `Apple Ecosystem Control −1`). |
| 15. Treasury unit displayed == unit charged | SRC-PASS — `custom_cost_text` says "10.0" and "§Hbillions§!"; the effect sets `treasury_change = -10` through `modify_treasury_effect`, the same unit MD uses everywhere else (`check_variable = { treasury > 1.4 }` / `cost_1_5` in `05_CHI_decisions.txt`). |
| 16. Bridge updated after all mutations? | SRC-PASS — `USA_corporate_systems_update_economic_bridge = yes` is the last statement in every one of the four `hidden_effect` blocks. |
| 17. Already-maxed variable creating hidden excess? | SRC-PASS — clamping happens on write, so a variable at 10 stays at 10 with no shadow surplus. |
| 18. Save/reload duplicating charge or cooldown | **RT-BLOCKED** |
| AI weighting | SRC-PASS — `ai_will_do = { base = 0 }` on all four, so the AI never takes them. Deliberate: these are player tools. `ai_hint_pp_cost` is set correctly on each. |
| Logging | SRC-PASS — all four log with the decision's own ID. |
| Cost vs MD precedent | SRC-PASS — 10–25bn against MD's existing treasury decisions (0.5–2.0bn for SCO bilaterals, but tens of billions for national programmes); 50–75 PP matches MD's large-programme band. |

**ADVISORY (F-1) — no double charge, but the code reads like one.** All four decisions declare
both `cost = N` *and* `add_political_power = -N`. These are the **only four decisions in the
entire mod** that do so under a `custom_cost_trigger` (scanned every decision in `common/decisions`
and in vanilla `common/decisions`: MD has 48 such decisions, vanilla 85+, and none combine the
two). Per the Paradox decision-modding documentation — *"a custom cost will not actually cost
anything, and what you set it to cost will have to be subtracted within the `complete_effect`"*,
and *"the custom cost can't be used in conjunction with the regular cost"* — the `cost = N` field
is **inert** here and the manual deduction is the real charge. So the behaviour is correct and
the player pays 50/75/50/50 once. But the redundant `cost` line is a maintenance trap: it reads
as a double charge to anyone auditing it. Recommend deleting the four `cost` lines (`ai_hint_pp_cost`
already carries the AI signal). No behavioural change.

**ADVISORY (F-2) — dead sub-clause in three `visible` blocks.** `open_systems_procurement`,
`secure_federal_systems` and `advanced_computing_consortium` all read:

```
visible = {
    has_country_flag = USA_ibm_state_initialized
    OR = { has_country_flag = USA_ibm_state_initialized  ... }   # IBM repeated inside the OR
}
```

The `OR` is tautological given the outer condition, so the gate is just "IBM initialized".
`domestic_capacity_grants` shows the intended shape (IBM outside, the *other* five companies
inside the `OR`) and is correct. Behaviour is right either way — IBM effects always apply, so
IBM-initialized is a sufficient gate — but the dead clause should be removed.

## G — ATI/AMD corporate history

`common/scripted_effects/CAN_ati_effects.txt`, `events/CAN_ati_events.txt`,
`common/ideas/CAN_ati_ideas.txt`, `common/scripted_triggers/MD_corporate_history_triggers.txt:41-71`.

| Check | Result |
| --- | --- |
| Dedicated namespace `CAN_ati_events` | SRC-PASS |
| 12 visible events, `.1`–`.12`, all `is_triggered_only = yes` + `fire_only_once = yes` | SRC-PASS |
| Dates: 2002, 2003, 2007, 2010, 2011, 2013, 2015, 2016, 2019, 2020, 2023, 2026 — all plausible (R300, Xbox, AMD acquisition, Radeon brand, Fusion, console semicustom, RTG, Polaris, RDNA, RDNA2, MI300, capstone) | SRC-PASS |
| Exactly one scheduling owner per event | SRC-PASS — `CAN_corporate_trigger_year_<YYYY>` in `00_corporate_history_dispatch_effects.txt`, all 12 wired from `00_yearly_effects.txt`; `CAN_ati_schedule_current_year_events` is a late-start-only bridge gated on `has_start_date` |
| Every event has ≥1 valid AI option, logging, `custom_effect_tooltip` | SRC-PASS |
| Five bounded variables, init 4/5/0/1/1, clamped after every write | SRC-PASS — every `CAN_ati_record_*` ends with `CAN_ati_clamp_state`; both inline event mutations do too |
| Variables written but never read / read before init | SRC-PASS — all five are read by the four `*_qualified` triggers and by the dashboard loc; `CAN_ati_initialize_state` runs in every entry point (`immediate` of every event, the reconstruct ladder, and the capstone resolver) |
| Reconstruction is deterministic and reward-free | SRC-PASS — `CAN_ati_reconstruct_history` sets flags and variables only; no `add_tech_bonus`, `add_political_power`, or timed idea |
| Reconstruction idempotent | SRC-PASS — every step is guarded by "neither route flag set" |
| Five outcomes, mutually exclusive | SRC-PASS — `CAN_ati_clear_capstone_outcome` removes all five ideas and clears `CAN_ati_capstone_resolved` before each `add_ideas` |
| Player may choose among qualified outcomes | SRC-PASS — `CAN_ati_events.12` offers one option per qualified outcome, plus a fallback option whose trigger is "none of the four qualify". At least one option is always available. |
| Resolver fallback for silent catch-up | SRC-PASS — `CAN_ati_resolve_capstone` uses the same qualification order with `else = absorbed_legacy` |
| No route unreachable through a dead threshold | SRC-PASS — walked the historical ladder: final state `arch 10 / research base 10 / synergy 7 / semicustom 9 / compute 8`, which qualifies for **all four** primary outcomes, so the 2026 event presents four real choices. Divergent routes drop individual axes below their gates as intended. |
| Contract registration | SRC-PASS — `validate_corporate_history_contract.py` clean, including its reachability, dispatcher-integrity, clamp-coverage, reconstruction-safety and cross-chain-ownership passes |
| Off does not initialize ATI through shared GPU events | SRC-PASS — `gpu_development.3.a_can`/`.b_can` wrap `CAN_ati_normalize_legacy_gpu_history` in `if = { limit = { corporate_history_enabled = yes } }`, and that effect only sets a flag; no variable is touched |
| Live event order, popups, save/reload | **RT-BLOCKED** |

### Legacy compatibility (`CAN_ati_research_autonomy` / `CAN_ati_amd_integration`)

| Check | Result |
| --- | --- |
| Old saves stay meaningful | SRC-PASS — both flags still read by `events/CAN_matrox_events.txt:264-322` and by `00_gpu_development_effects.txt` |
| Normal choices cannot leave both active | SRC-PASS — they are two options of the same `gpu_development.3`, each setting `gpu_development_3_resolved` |
| Reconstruction cannot leave both active | SRC-PASS — `00_gpu_development_effects.txt:96-105` sets `research_autonomy` only when neither flag is present |
| Matrox still understands them | SRC-PASS — read-only; Matrox writes no `CAN_ati_*` state (verified by grep over both Matrox files) |
| Canonical ATI state does not contradict them | SRC-PASS — `CAN_ati_normalize_legacy_gpu_history` maps *either* legacy flag to the neutral `CAN_ati_post_acquisition_autonomy`, and the loc string is deliberately route-neutral ("post-acquisition structure recorded from the legacy GPU history"), so an AMD-integration save is not relabelled as autonomy |
| Migration does not replay 2000/2006 rewards | SRC-PASS — normalize sets one flag and nothing else |

## H — Canadian Corporate Systems dashboard

| Check | Result |
| --- | --- |
| Three entries: ATI/AMD, Matrox, BlackBerry/QNX, plus an initializing placeholder | SRC-PASS |
| `allowed = { original_tag = CAN }` on the category | SRC-PASS |
| Full/Outcomes Only visible, Off suppressed, collapsed suppressed | SRC-PASS (`99_CAN_decision_categories.txt:41`) |
| No ATI-only category gate | SRC-PASS — `CAN_corporate_systems_has_meaningful_state` spans ATI, Matrox and four BlackBerry/QNX flags |
| Temporary initialization entry | SRC-PASS |
| All entries read-only, no effect calls | SRC-PASS |
| No raw keys | SRC-PASS |
| No fake Matrox or BlackBerry variables | SRC-PASS — the Matrox and BlackBerry entries report **flags and ideas only**; the ATI entry is the only one printing numbers, and those are the five real variables |
| ATI values and capstone update live | SRC-PASS — loc reads `[?CAN_ati_*]` and the two scripted-loc selectors directly |
| BlackBerry/QNX reports honestly | SRC-PASS — `CAN_corporate_systems_blackberry_status` has an explicit `corporate_history_outcomes_only_enabled` branch printing "no reconstructed state in Outcomes Only", matching the framework TODO that BlackBerry has no reconstruction effect |
| Tooltip length usable | SRC-PASS — longest Canadian entry is ~9 short lines, well under the USA entries |
| Renders in-game | **RT-BLOCKED** |

## I — Cross-company and cross-country ownership

Programmatic scan: every write statement (`set/clr_country_flag`, `set/add_to/subtract_from_variable`,
`add/remove_ideas`) occurring inside an explicit `TAG = { }` scope across all corporate effect
and event files. 33 hits, all reviewed.

| Seam | State owner | Reader | Writer | Verdict |
| --- | --- | --- | --- | --- |
| ATI ↔ Matrox | CAN (ATI) | Matrox events | ATI only | clean, read-only |
| ATI ↔ NVIDIA | CAN (ATI) | `USA_nvidia_events.10/.11` `ai_chance` | ATI only | clean — wrapped in `country_exists = CAN` + `CAN = { }`, so Canada-absent is safe |
| ATI ↔ shared GPU | CAN | `gpu_development_reconstruct_history` (own scope) | ATI/GPU chain in CAN scope | clean |
| Matrox ↔ QNX / AlexNet | CAN | Matrox | BlackBerry / AlexNet chains | clean, read-only |
| NVIDIA ↔ TSMC | TAI | `USA_nvidia_events` via `TAI = { }` | TSMC | clean, read-only |
| Sony ↔ Ericsson | SWE | JAP Sony events | Ericsson | clean (no JAP write into SWE found) |
| Nokia ↔ Siemens / France | FIN | GER/FRA | Nokia | clean |
| IBM ↔ Lenovo | split by design | both | dispatcher writes `CHI_lenovo_event_7_pending` into `CHI = { }` from the yearly dispatcher | acceptable — the dispatcher is the declared scheduling owner |
| Motorola ↔ Lenovo | CHI | USA | Lenovo | clean |
| Apple ↔ IBM/Microsoft | USA | Apple `ai_chance` | IBM/Microsoft | clean, read-only |
| **Foxconn ↔ USA** | TAI (Foxconn owns both sides of the Wisconsin record) | Foxconn | `TAI_foxconn_effects.txt:79` writes `USA_foxconn_wisconsin_full_support` into `USA = { }` | **acceptable, single-writer** — no USA chain writes these three flags; the write is guarded on "no response flag yet" and on `USA` not collapsed. Documented here so it is not mistaken for a violation later. |
| GPU ↔ Microchip | shared | GPU chain | GPU chain | clean apart from the `stability` defect below |

**No ownership violation found.** Nothing replaces a source outcome, replays a source reward,
or clears source-country state.

## FAIL — demonstrated defect (repaired)

**`events/00_gpu_development.txt` — 12 invalid `stability` AI-weighting triggers.**

* Runtime evidence (pre-fix): `error.log` contains 12× `Invalid trigger 'stability' in
  events/00_gpu_development.txt` and 12× `Unknown trigger-type: stability`, from the
  2026-07-31 session against a tree byte-identical to `61bee3a1ac`.
* Static reproduction: `grep -cE '^\s*stability [<>] ' events/00_gpu_development.txt` → 12,
  exactly matching the log count. The 18 further hits in `99_IRQ_scripted_effects.txt` are
  inside `check_variable = { }` and are valid.
* Root cause: `stability` is a variable, not a trigger. The HOI4 trigger is `has_stability`.
  The engine rejects the whole `modifier` block at load, so the intended low-stability AI
  preference never applies to any GPU option — including `gpu_development.3.b_can`, the
  AMD-integration route that feeds the Canadian ATI legacy state.
* Fix: `stability <|> X` → `has_stability <|> X`, 12 sites, on branch
  `claude/fix-gpu-chain-invalid-stability-trigger` @ `3e616d76ce`.
* Post-fix validation: `validate_events.py`, `check_common_mistakes.py`,
  `validate_corporate_history_contract.py` all clean for this file; `git diff --check` clean;
  no BOM introduced.
* Post-fix runtime: **RT-BLOCKED.** The proof that the log lines disappear needs one game
  launch, which could not be performed. This is the single highest-value runtime check
  outstanding and takes about two minutes once someone can start the game.

## Not verified — full list of RT-BLOCKED items

Live U.S. dashboard render · all five bridge tiers observed · malformed-duplicate-tier repair ·
repeated monthly ticks · bridge save/reload · collapsed-USA behaviour · each of the four
policies before/after (treasury, PP, axes, company variables, tier, cooldown) · insufficient
treasury · bankruptcy · uninitialized company · variable at bound · cooldown expiry ·
Outcomes Only and Off for the policies · ATI Full 2000 playthrough · ATI Outcomes Only later
starts · ATI Off · the 2015 route split · all five ATI capstones · Matrox compatibility text ·
cross-border ATI/NVIDIA with Canada collapsed · post-fix error.log delta.

Note for whoever runs these: MD ships **one** bookmark (`common/bookmarks/blitzkrieg.txt`,
2000.1.1). Every "later start" test in the open issues therefore requires either a new bookmark
or console date manipulation — the `has_start_date` branches in
`CAN_ati_schedule_current_year_events` and its siblings are currently unreachable in normal play.
