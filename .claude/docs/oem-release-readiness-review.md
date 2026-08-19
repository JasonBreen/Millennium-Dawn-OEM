# OEM Release Readiness Review

Adversarial pre-contribution review of Millennium Dawn OEM against
`MillenniumDawn/Millennium-Dawn`. Scope: upstream compatibility, architecture
consistency, runtime risk, save/reload risk, Corporate History lifecycle,
Full / Outcomes Only / Off isolation, reconstruction idempotence, cross-chain
ownership, stale artifacts, localisation and UX, AI behaviour, balance,
historical wording, PR reviewability.

**Reviewed:** OEM `main` @ `761cbca6f2` (verified identical to `origin/main`)
**Upstream:** `7098b472c4` — merge-base `17b6988d51`, upstream +49 / OEM +640 commits
**Scale:** 556 files, +133,134 / -5,621 lines (excluding `resources/`)

**Release state: NO-GO.** Re-review after H1-H6 below.

---

## 1. What was proven correct

These are the properties most likely to be wrong in a system this size. Each was
verified independently, not taken from the contract validator's word.

| Property | Result | Evidence |
| --- | --- | --- |
| Reconstruction idempotence | CLEAN | 390/390 relative writes inside `*_reconstruct_history` sit inside an `if` whose `limit` negates a flag the same branch sets |
| Double-fire of visible events | CLEAN | 353 `_pending` / `country_event` pairs all have positive margin including `random_days`; the only 19 zero-margin pairs are upstream files |
| Monthly updater inflating state | CLEAN | 0 `add_to_variable` and 0 reward effects across all 13 `*_monthly_outcomes` |
| Capstone ideas mutually exclusive | CLEAN | 113 declared outcome ideas, all granted, all sibling-guarded; every chain has a terminal marker |
| Read-only dashboard effect-bearing | CLEAN | 10/11 dashboards have zero stateful ops; USA's 7 display decisions are `cost = 0` with no `complete_effect` |
| Adapter mutating source subsystem | CLEAN | Contract declares 91 `allowed_native_reads` / 10 `native_write_prefixes`, enforced by `validate_corporate_history_contract.py` and `linux_national_adapter_contract_test.py` |

What blocks the release is not core engineering. It is one release-hygiene
failure that would damage upstream on merge (G1), a player-facing scope boundary
that is deliberate but undocumented (B1), a single point of failure in the
dispatch host (B2), and a contribution shape no maintainer will accept
(section 9).

---

## 2. Architecture as built

```
on_startup --+-- ABK = { OEM_corporate_history_startup_bootstrap }
             +-- ABK = { linux_system_startup_bootstrap }

OEM_corporate_history_startup_bootstrap        00_corporate_history_effects.txt:185
  | guard: NOT has_global_flag GLOBAL_oem_corporate_history_startup_dispatched
  +-- corporate_history_on_startup    GATED (full | outcomes_only)
  +-- ISR = { ISR_oem_events.90 }     UNGATED  <-- B1
  +-- {USA,CAN,TAI,KOR,CHI,JAP} gpu_development reconstruct + schedule
                                      UNGATED (by design, bridge is gated)

on_daily_ABK --+-- 26 yearly blocks 2000-2026, each latched on
               |   set_global_flag OEM_upstream_sync_year_YYYY_dispatched
               |   -> TAG_corporate_trigger_year_YYYY
               +-- linux_system_trigger_year_YYYY + milestone latches

on_monthly_TAG -> TAG_corporate_history_monthly_outcomes   SPLIT AUTHORITY <-- B3
```

### B1 - SERIOUS: "Off" does not mean off to a player

Three OEM namespaces fire visible events regardless of the Corporate History
rule, including when it is set to `disabled`:

| Namespace | Visible events | Dispatched from | Rule-gated? |
| --- | --- | --- | --- |
| `ISR_oem_events` | 10 of 11 | CH bootstrap + CH yearly dispatcher | No |
| `USA_oem_events` | `.1-.12` mostly | CH yearly dispatcher | Partial - `.13`/`.14` gate on `corporate_history_full_enabled`, `.16-.23` on `linux_system_full_enabled`, the rest not at all |
| `gpu_development` | `.1-.9` | CH bootstrap + CH yearly dispatcher | No, by design - its *bridge* into CH is gated (`00_gpu_development_effects.txt:113`, `events/00_gpu_development.txt:752`) |

Dispatch sites for ISR:

- `common/scripted_effects/00_corporate_history_effects.txt:196` -
  `ISR = { country_event = ISR_oem_events.90 }`, outside the mode gate
- `common/on_actions/01_oem_corporate_history_on_actions.txt:44` -
  `ISR = { ISR_oem_schedule_2001_events = yes }`

`events/ISR_oem_events.txt` and `common/scripted_effects/ISR_oem_effects.txt`
contain zero occurrences of `corporate_history_*` or `has_game_rule`.

**This is deliberate, not an oversight.**
`.claude/docs/noncontract-oem-chain-audit.md:24` classifies `ISR_oem_events` as
decision **5, standalone historical flavour** ("a national multi-company
electronics survey rather than one corporate owner"), and `USA_oem_events` as
decision 5 likewise; `gpu_development` is decision 2. The scope boundary was
chosen on purpose.

The defect is therefore **player-facing, not architectural.** The rule reads
"Corporate History: Off", and its description
(`localisation/english/MD_game_rules_l_english.yml:879`) says *"Rule-gated
corporate-history chains are fully disabled"*. That sentence is circular -
rule-gated chains are disabled by the rule - and tells a player nothing about
the three namespaces that keep firing. Someone who switches Corporate History off
to get a cleaner campaign will still receive the Israeli electronics survey, the
legacy USA OEM events and the GPU chain, with no way to predict that from the UI.

**Fix (pick one, do not leave it implicit):**

1. Reword `RULE_CORPORATE_HISTORY_OFF_DESC` to name what stays on, and add the
   same clarification to the Outcomes Only description; or
2. Extend the rule with a fourth option, or add a companion rule, that also
   suppresses the standalone namespaces; or
3. Fold ISR and `USA_oem_events` under the existing gate and accept the
   reclassification.

Whichever is chosen, the boundary must be machine-checked - see H3.

### B2 - SERIOUS: both dispatchers hosted on an annexable micronation

`on_daily_ABK` is the sole date driver for Corporate History and the Linux
ecosystem. This is an OEM invention: `git grep on_daily_ABK upstream/main`
returns nothing, and every other `on_daily_TAG` in `common/on_actions/` appears
exactly once as that country's own hook.

Abkhazia is a single-state nation bordered by Georgia and Russia. No scripted
`annex_country = ABK` exists (Georgia and Russia focuses use `puppet = ABK`,
which preserves the tag), but war and peace-conference annexation is available to
player and AI. If ABK ceases to exist, every remaining yearly dispatch stops
silently, worldwide, for the rest of the campaign. The monthly drivers provide
only partial catch-up: `USA_corporate_history_monthly_outcomes` documents itself
as recovering Google/Oracle/IBM-Lenovo/TI/Micron/Motorola/Dell specifically, not
the whole schedule.

**Fix - must stay country-scoped.** AGENTS.md:35 requires `on_daily_TAG` over
global triggers, so moving these date checks into a global on_action trades one
defect for a worse one (a daily poll for every country). Two options that respect
the rule:

1. **Distribute the dispatch to the chain owners.** Each participating tag
   already has an `on_monthly_TAG` hook running its
   `TAG_corporate_history_monthly_outcomes` driver. Move that country's slice of
   the yearly dispatch into it, latched on the existing
   `OEM_upstream_sync_year_YYYY_dispatched` global flags. This removes the shared
   host entirely, adds no new hook, and degrades per-country instead of globally.
   Cost: up to ~30 days of dispatch latency, which the chains already tolerate -
   the monthly drivers are documented as "<= ~31 days lag".
2. **Keep a daily host, add bounded recovery.** Leave `on_daily_ABK` as the fast
   path but teach the existing per-country monthly drivers to detect a missing
   `OEM_upstream_sync_year_YYYY_dispatched` flag for an elapsed year and run the
   catch-up. A lost host then degrades to monthly instead of failing silently.

Option 1 is preferred: it eliminates the single point of failure rather than
compensating for it.

### B3 - SERIOUS: split monthly dispatch authority

`common/on_actions/02_oem_corporate_history_monthly_on_actions.txt` states it
exists so upstream changes do not repeatedly conflict with Corporate History. It
wires 6 countries (FIN, TAI, JAP, CAN, ENG, UKR). The other 7 are wired inside
upstream-owned files:

| File | Line |
| --- | --- |
| `common/on_actions/99_CHI_on_actions.txt` | 64 |
| `common/on_actions/99_FRA_on_actions.txt` | 49 |
| `common/on_actions/99_GER_on_actions.txt` | 772 |
| `common/on_actions/99_POL_on_actions.txt` | 103 |
| `common/on_actions/99_SOV_on_actions.txt` | 74 |
| `common/on_actions/99_SWE_on_actions.txt` | 4 |
| `common/on_actions/99_USA_on_actions.txt` | 76 |

The stated conflict-isolation benefit is only half realised, and no single file
answers "where is the monthly driver registered?". Note also that
`SOV_corporate_history_monthly_outcomes` is the only driver defined outside
`00_corporate_history_effects.txt`
(`common/scripted_effects/SOV_computing_sovereignty_effects.txt:2362`).

### B4 - SERIOUS: tautological OR in 3 of 4 USA real-options policy gates

`common/decisions/USA_corporate_systems_dashboard.txt` lines 146, 353, 457:

```
visible = {
	has_country_flag = USA_ibm_state_initialized     # hard AND
	OR = {
		has_country_flag = USA_ibm_state_initialized # makes the OR always true
		has_country_flag = USA_apple_state_initialized
		has_country_flag = USA_nvidia_state_initialized
	}
}
```

The sibling at line 244 (`USA_corporate_policy_domestic_capacity_grants`) proves
the intent: its `OR` correctly excludes IBM, so the gate reads "IBM and at least
one other chain". In the other three the `OR` collapses to "IBM only", so the
policies unlock earlier and more broadly than authored.

**Fix:** delete the duplicated `has_country_flag = USA_ibm_state_initialized`
from inside each `OR` (lines 149, 356, 460).

### B5 - POLISH: redundant double reconstruction on Canada

`common/scripted_effects/CAN_ati_effects.txt:188` calls
`gpu_development_reconstruct_history`, and the bootstrap calls it again for CAN
at `common/scripted_effects/00_corporate_history_effects.txt:217`. Harmless -
`gpu_development_reconstruct_history` is flag-latched per milestone
(`gpu_development_N_resolved`) - but it is wasted work and makes ownership
ambiguous. Pick one owner.

### B6 - POLISH: naming and structural inconsistencies

- `rule_corporate_history` uses option name `disabled`; `rule_linux_ecosystem`
  uses `off`. Same concept, two spellings, two trigger files.
- `USA_corporate_systems_dashboard.txt` holds both the read-only dashboard and
  the four real-options policy decisions. The filename describes half its
  contents.
- Country-existence guarding is inconsistent inside the yearly dispatcher: the
  2001 GPU dispatches are wrapped in `country_exists`, but the `USA = { ... }`
  storage/Linux block immediately below is not
  (`common/on_actions/01_oem_corporate_history_on_actions.txt:54`).

---

## 3. Upstream-sync risks

True two-sided conflict surface: **40 files**. No GFX sprite-name collisions
(62 upstream vs 76 OEM additions to `MD_eventpictures.gfx`, disjoint). No
semantic collision in `99_CHI_on_actions.txt` (OEM at line 61, upstream at 358+)
or `00_game_rules.txt` (OEM at 854, upstream at 1180).

### 3.1 `tools/validation/validate_gfx_references.py`

- **UPSTREAM CHANGE:** +617/-85 (#3026, "Exempt engine-resolved sprites and split
  GFX case checks"). Adds `_GFX_TEXTUREFILE` and `_SPRITE_TEMPLATE_REF` for
  engine-built names, adds an `MD_GFX_HIDE_UNUSED` env switch, removes
  `_UNUSED_SPRITE_LIMIT`, and renames the manifest generator from
  `gen_vanilla_*_manifest.py` to `refresh_vanilla_data.py`.
- **OEM CHANGE:** +6/-6. A typing cleanup: `staged_rel` changed from
  `Optional[Set]` to an always-`Set`, with the `is not None` test replaced by
  `self.staged_only`.
- **SEMANTIC CONFLICT:** None. OEM's change is local to `Validator.validate()`;
  upstream's is a capability expansion. But OEM still ships the four
  `gen_vanilla_*_manifest.py` scripts upstream deleted, and
  `.claude/docs/validation-pipeline.md` - required reading per AGENTS.md -
  documents the old regeneration flow.
- **RECOMMENDED RESOLUTION:** Take upstream wholesale; re-apply OEM's 6-line
  typing cleanup on top (that block is untouched by #3026). Delete the four
  `gen_vanilla_*` scripts and update `validation-pipeline.md` to name
  `refresh_vanilla_data.py`. Do not attempt a 3-way merge - the file was
  restructured.

### 3.2 `tools/standardization/{standardize_focus_tree,standardize_ideas,common_utils}.py`

- **UPSTREAM CHANGE:** #3023 "Enforce brace and `=` spacing in standardizer
  output" - `standardize_ideas.py` +17/-3, the other two +2/-1 each.
- **OEM CHANGE:** `standardize_focus_tree.py` +26/-12 - reworks `_split_block()`
  to take `allow_trailing_comment`, so a single-line block carrying an inline
  comment can be expanded with the log landing inside the braces and the comment
  reattached to the closing brace.
- **SEMANTIC CONFLICT:** Real. Both sides change how the standardizer emits
  braces. Upstream now normalises spacing around `{`, `}` and `=` on output;
  OEM's `_split_block` builds `close = f"{close} {comment.lstrip()}"` by hand.
  Upstream's normaliser may rewrite that reattached comment, and OEM's regression
  tests (`standardize_focus_tree_test.py`, `standardize_events_test.py`, both
  OEM-modified) encode the pre-#3023 output shape.
- **RECOMMENDED RESOLUTION:** Merge upstream first, then re-apply OEM's
  `allow_trailing_comment` work and re-run both test files, regenerating expected
  strings against upstream's new spacing. Neither side is wrong; the tests are
  the arbiter and must be regenerated, not hand-patched.

### 3.3 `tools/validation/tests/config_drift_test.py`

- **UPSTREAM CHANGE:** +19/-12 (#2997) - wraps assertions for Black 26.5.1.
- **OEM CHANGE:** +12/-12, overlapping region.
- **SEMANTIC CONFLICT:** Formatting-driven on both sides; a textual conflict is
  near-certain and a naive resolution will silently drop one side's assertions.
- **RECOMMENDED RESOLUTION:** Take upstream verbatim, then diff OEM's assertion
  set against it and re-add any OEM-only assertion. Resolve by asserted
  behaviour, never by hunk.

### 3.4 `common/national_focus/*` - upstream #3042

- **UPSTREAM CHANGE:** "Remove political power costs from focus completion
  rewards" - upstream has decided PP-malus-in-completion-reward is an
  anti-pattern.
- **OEM CHANGE:** OEM's four real-options decisions charge PP inside
  `complete_effect` via `hidden_effect { add_political_power = -50 }` alongside
  `cost = 50` and `custom_cost_trigger`.
- **SEMANTIC CONFLICT:** None functionally. These are decisions, not focuses, and
  `cost` is inert once `custom_cost_trigger` is present, so this is a single
  charge, not a double one. But 71 of the validator run's 1501 warnings are
  `[pp-malus-completion-reward]` on upstream focus files, and syncing #3042
  clears them.
- **RECOMMENDED RESOLUTION:** Sync #3042 and confirm the 71 warnings drop to
  zero. Add a one-line comment at each OEM decision noting the
  `custom_cost_trigger` + manual-deduct pattern is deliberate (the trigger gates,
  the effect charges). Do not "fix" the OEM decisions - the pattern is correct.

### 3.5 `common/game_rules/00_game_rules.txt`

- **UPSTREAM CHANGE:** Flips `allow_fictional_content` from `default = no` to
  `default = yes` (line ~1180).
- **OEM CHANGE:** Inserts `rule_corporate_history` and `rule_linux_ecosystem` at
  line 854, both `default = full`.
- **SEMANTIC CONFLICT:** No textual overlap, but a policy conflict. OEM defaults
  every existing MD player into ~45,000 lines of new event content with no
  opt-in. The `full` default correctly omits `allow_achievements` per MD
  convention (matches `historic_events` directly above). Loc keys are complete
  (`localisation/english/MD_game_rules_l_english.yml:873-886`).
- **RECOMMENDED RESOLUTION:** Auto-merge is safe. Separately, raise the default
  with maintainers before submitting - `default = full` is a product decision and
  the single most likely thing to stall the PR.

### 3.6 Lower risk

- Upstream #2994 "Removing Meta Effects/Triggers" - OEM ships
  `.claude/docs/meta-effect-patterns.md`, stale doctrine post-sync.
- Upstream #3015/#3018 unified vanilla data refresh - regenerate manifests after
  merging.

---

## 4. Static validation results

- `python tools/validation/run_all_validators.py` - **0 errors, 1501 warnings**,
  exit 0.
- `python tools/validation/validate_corporate_history_contract.py` - **no issues**,
  13 check groups, 47.7s.

### SERIOUS

**12 pytest failures.** AGENTS.md requires the validator suite stay green
permanently. Two verified in detail:

- `tools/tests/cleanup_effect_tooltip_test.py::test_single_line_wrapper_collapses`
  -> `ValueError: path is on mount 'C:', start on mount 'G:'`
- `tools/validation/tests/validate_scripted_localisation_test.py::test_english_yml_keeps_undefined_bracketed_invocation`
  -> asserts `localisation/english/...`, receives OS-native separators

The other 10 are in files unchanged from upstream and share both signatures.

**Classification: FALSE POSITIVE / UPSTREAM** - Windows-only, CI is Linux. The
operational consequence is real: the AGENTS.md pre-merge gate `python -m pytest`
cannot be satisfied on a Windows worktree on a drive other than the temp drive,
so `tools/` changes ship on CI's word alone.

### POLISH - the only four OEM-attributable warnings in the entire run

- `common/scripted_effects/POL_industrial_sovereignty_effects.txt:191` -
  `[unused-scripted-effect] POL_industrial_sovereignty_resolve_terminal`. A dead
  terminal resolver on a chain that has a declared `terminal_marker`; confirm the
  chain can actually terminate.
- `common/scripted_triggers/FIN_nokia_triggers.txt:41,46` -
  `[unused-scripted-trigger] FIN_nokia_has_customer_concentration_risk`,
  `FIN_nokia_has_china_exposure`.
- `events/CAN_matrox_events.txt:861` - `[simplification] NOT with 5 children is
  ambiguous`. Per `.claude/rules/general-rules.md`, `NOT = { A B C D E }` is NAND,
  almost never intended. **This is the one OEM warning that can be a real logic
  bug - read it.**

### FALSE POSITIVE / UPSTREAM

- 71 x `[pp-malus-completion-reward]` - all upstream focus files, cleared by #3042.
- 2 x `[missing-cross-country-tooltip]` - `france.txt:2332`,
  `gulf_shared.txt:1179`, both upstream.
- The bulk of the 1501 is the upstream GFX orphan-sprite backlog; #3026 adds
  `MD_GFX_HIDE_UNUSED` specifically because it buries real findings.

### Encoding / BOM

Clean. No `.txt` BOM violations, no `.yml` missing BOM.

---

## 5. Runtime-test priorities

Issues #24, #25, #26, #27, #28, #45 and #112 are open with zero recorded results.
None are marked passed here.

**#112 is stale.** It reports `CAN_matrox_events.1/.2` rendering `GFX_computer`.
On current main they render `GFX_matrox_g400` and `GFX_matrox_parhelia`
(`events/CAN_matrox_events.txt:8,69`). The specific defect is fixed; the class of
defect is not - see section 6.3.

| # | Test | Statically provable? | Requires game? | Console command | Expected state | Save/reload? | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | Corporate History = Off produces no OEM content | No - proven false statically for ISR | Yes | New game rule Off; `tag ISR`; advance to 2001-06 | Zero ISR OEM events. Currently fails (B1) | No | 0 `has_game_rule` in ISR files; 10 visible events |
| P2 | Annex ABK, yearly dispatch survives | No | Yes | `tag GEO`; annex ABK; advance past next 1 Jan | Next `OEM_upstream_sync_year_YYYY_dispatched` set. Expected to fail (B2) | Yes, before/after annex | Sole `on_daily_ABK` host for both subsystems |
| P3 | Full-mode startup, `error.log` clean | Partial | Yes | New game Full; wait 10 days; read `logs/error.log` | No unknown-modifier, unknown-effect or script_math errors | No | Contract validator clean; engine side unproven |
| P4 | Outcomes Only reconstructs every chain Full does | Partial | Yes | New game Outcomes Only; `tag USA`; open dashboard | Same 32 chains reconstructed | No | Contract enforces both branches; HP/Google/Oracle/Sun-MS have empty `outcome_idea_prefixes` - verify intentional |
| P5 | Save before a scheduled event, reload, fires once | No | Yes | Full; `tag CHI`; save 2014-06-01 (`CHI_lenovo_events.7` pending, fires +190d, flag +230d); reload; advance 250d | Fires exactly once | Yes - this is the test | 353/353 pending pairs have positive margin |
| P6 | Save after a selection, reload, no replay | No | Yes | Pick a capstone option; save; reload; advance 60d | No duplicate idea, no doubled variable | Yes | 113 capstone grants all sibling-guarded |
| P7 | Run hidden reconstruction twice | YES - proven idempotent | Optional confirm | See note below - **not** `event USA_ibm_events.90` | Identical state both runs | No | 390/390 relative writes flag-guarded. Confirm, do not discover |
| P8 | Cross-country receiver, remove secondary country | No | Yes | `tag SWE`; annex/release FIN; advance a Nokia->Ericsson beat | Ericsson reads Finland without writing it; no error on missing tag | No | Contract declares read-only adapters; #24 requires this for Sony/Sweden |
| P9 | Collapse event recipient mid-chain | Partial | Yes | Force `collapsed_nation` on FRA; advance | FRA chain halts cleanly | No | FRA startup guards on `collapsed_nation` + `original_tag`; other chains uneven |
| P10 | 2005 / 2017 / 2026 starts | N/A - no such bookmark | Yes | Only `blitzkrieg.txt` @ 2000.1.1 exists (`default = yes`) | - | - | Retarget to `.90` reconstruction events fired at date |

**On P7 - `.90` events cannot be re-fired.** 27 of the 44 `.90` reconstruction
events carry `fire_only_once = yes`, `USA_ibm_events.90` among them
(`events/USA_ibm_events.txt`). A second console invocation is suppressed by the
engine, so unchanged state proves nothing about idempotence - it only proves the
event did not run. HOI4's console has no command to invoke a scripted effect
directly. To confirm the property at runtime, add a scratch debug event in a
local build with no `fire_only_once` whose `immediate` calls the reconstruct
effect, fire it twice, and diff the dashboard. Note this is confirmation only:
idempotence is already statically proven at 390/390 guarded writes, so a runtime
failure here would indicate a *new* unguarded write, not a flaw in the existing
analysis.

**On P10 - late-start reconstruction needs a clean state.** MD ships exactly one
bookmark, so the "2005/2017/2026 start" requirement in #24-#28 cannot be executed
as written. Advancing a normal 2000 campaign to the target date is **not** an
equivalent: the campaign sets the same `*_resolved` / `*_delivered` flags that
guard every reconstruction write, so a later `.90` would hit no-op branches even
if it could fire. What that tests is "reconstruction is inert over already-lived
history", which is worth knowing but is not the late-start property.

The real test needs a state where the elapsed history was never dispatched:

1. Add a temporary local bookmark at the target date (test build only, not
   shipped).
2. Start there and let the startup bootstrap reconstruct.
3. Compare the resulting chain state against a control save advanced normally
   from 2000 to the same date.

Equivalence between the two is the acceptance criterion. Without the temporary
bookmark, the late-start path is untestable in game and only the static
reconstruction analysis stands behind it.

**Execution order:** P1, P2, P3, P7, P5, P6, P4, P8, P9. P1 and P2 are
known-or-suspected failures and should be fixed before any branch-level testing;
running the exhaustive per-chain matrices in #24-#28 before P1-P3 wastes the
effort.

---

## 6. Content and presentation findings

Treating #45 as a hard gate: **it is not met.**

### 6.1 SERIOUS - player voice is inconsistent across chains

Options must be government levers, not board decisions. Some chains follow this;
some do not.

Correct, Nintendo (JAP): "Extend industrial credit to both platforms",
"Fund the developer transition", "Promote the launches abroad".

Correct, AIG (USA): "Authorize emergency support", "Take the equity stake",
"Lend on punitive terms only", "Open the securities facility".

Wrong, Google (USA): "Lock in the dual-class charter", "Acquire YouTube and scale
first", "Give Android away and build scale". The United States government cannot
lock in Alphabet's share charter or acquire YouTube. These are board votes with
no instrument.

Wrong, Huawei (CHI): "Buy our way into the standards club", "Win China first",
"Build security and storage ourselves". First-person "our/we" makes the state
speak as the firm. Huawei's state entanglement is a partial defence for the
decisions; it is not a defence for the voice.

**Minimal fix - do not rewrite the chains.** Recast option verbs only, at the
chains that need it:

- "Lock in the dual-class charter" -> "Decline to challenge the dual-class listing"
- "Acquire YouTube and scale first" -> "Clear the acquisition without conditions"
- "Buy our way into the standards club" -> "Fund standards-body participation"

Roughly 30 loc strings across Google and Huawei, not a content pass.

### 6.2 POLISH - Oracle descriptions overrun the house limit

51 OEM `.d` keys scanned; 9 over the ~3-sentence cap, all Oracle, 396-486
characters: `USA_oracle_events.1.d` (4), `.2.d` (4), `.3.d` (4), `.4.d` (4),
`.5.d` (4), `.6.d` (4), `.7.d` (5, 468 chars), `.8.d` (4), `.11.d` (4).

Every other OEM chain sampled holds at or under 3. Trim the fourth sentence,
which in each case restates the option set the buttons already show.

### 6.3 SERIOUS - event art is majority-generic

493 picture assignments across OEM event files use 111 distinct sprites. Three
generic images cover roughly 53%:

| Sprite | Uses |
| --- | --- |
| `GFX_computer` | 131 |
| `GFX_generic_factory` | 65 |
| `GFX_stock_market` | 65 |
| `GFX_cyber_attack` | 18 |
| `GFX_USA_generic` | 15 |

Issue #112 was filed against exactly this pattern for Matrox and was fixed by
adding three dedicated sprites. 131 uses of `GFX_computer` is the same defect at
40x the scale. OEM added 80 event pictures; it needs materially more before #45
can close, or a deliberate stated policy that generic art is acceptable for
non-marquee beats.

### 6.4 Clean

- No espionage or wrongdoing language: zero hits for spy, espionage, backdoor,
  stole, fraud or criminal across sampled OEM loc.
- No hindsight framing: zero hits for "would later", "in hindsight", "proved to
  be", "little did".
- Descriptions present real trade-offs. `USA_google_events.5.d` on China entry is
  even-handed: entry offers user access but requires concessions on speech, while
  refusal leaves the market to domestic competitors.
- No announcement-as-investment or review-as-guilt patterns in the sample.

---

## 7. Stale artifacts

### G1 - BLOCKER: six upstream-shipped files deleted and gitignored

The two most recent commits on main (`761cbca6f2`, `c90a85fea1`, "Ignore
upstream-only compatibility and vanilla music files") delete these and add them
to `.gitignore`:

| File | In upstream/main? |
| --- | --- |
| `events/Vietnam.txt` | YES |
| `common/on_actions/99_VIE_on_actions.txt` | YES |
| `common/national_focus/00_music_dlc_compatibility.txt` | YES |
| `common/scripted_triggers/00_music_dlc_compatibility_triggers.txt` | YES |
| `common/special_projects/projects/zz_vanilla_music_compatibility_projects.txt` | YES |
| `localisation/english/replace/replaced_from_constructions_l_english.yml` | YES |

Contributing OEM's tree upstream would delete Vietnam's content and the music-DLC
compatibility layer. The `.gitignore` entries mean a sync cannot restore them -
the deletion is self-sealing. The `music/*.txt` entries in the same block are
legitimately absent upstream and can stay ignored; these six cannot.

**Fix - do not revert both commits.** `761cbca6f2` is a merge commit whose
parents are `[ac3fcbd35e, c90a85fea1]`; the deletion enters main exactly once,
through that merge. Reverting both would apply the same inverse deletion twice
and conflict. Either:

- `git revert -m 1 761cbca6f2` (revert the merge once against the correct
  mainline), or
- **preferred:** restore the six paths and narrow the `.gitignore` block in a
  single new commit. `761cbca6f2` is GPG-signed by GitHub's merge machinery, and
  a forward-fixing commit is easier to review than a merge revert.

### G2 - tracked but gitignored (OEM-only)

| File | Why it must go |
| --- | --- |
| `.mcp.json` | Local MCP server config (`md-mcp serve --mod-root .`). Editor tooling, not mod content. Already ignored - untrack it. |
| `.vscode/hoi4_millennium_dawn.code-workspace` | Personal editor workspace. Already ignored - untrack it. |

The three tracked `.psd` files matching `*.psd` are upstream-inherited art
sources - leave them.

### G3 - fork-specific automation

| Path | Why |
| --- | --- |
| `.github/workflows/temp-aug8-upstream-sync.yml` | Named "temp". One-off fork sync automation, meaningless upstream. |
| `.github/workflows/temp-aug8-sync-diagnose.yml` | Same. |
| `.github/workflows/pylint.yml` | OEM-added. Upstream has its own lint policy - propose, do not impose. |

### G4 - generated diagnostics with developer-machine paths

`runtime_evidence/copilot-third-pass/556b403.../` (8 files) embeds absolute local
paths including `C:/Users/New/repos/...`, `G:/Millennium-Dawn-OEM` and a local
Steam library path. A point-in-time snapshot from 2026-08-01, already stale.
Delete the directory.

### G5 - internal planning docs (12 OEM-added under `.claude/docs/`)

Genuine references, keep and propose upstream:
`linux-system-reference.md`, `linux-national-adapters.md`,
`oem-real-options-economic-layer.md`, `usa-oem-economic-bridge-map.md`.

One-off planning/audit scratch, drop before contribution:
`ai-industry-core-plan.md`, `france-corporate-systems-plan.md`,
`nintendo-corporate-history-plan.md`, `poland-industrial-sovereignty-plan.md`,
`oem-chronology-audit.md`, `oem-event-prose-audit.md`,
`noncontract-oem-chain-audit.md`,
`russian-computing-sovereignty-source-register.md`.

`noncontract-oem-chain-audit.md` is worth reading first - its name suggests it
already documents the ISR gap in B1.

### G6 - `resources/` dump: 658 files

| Directory | Files |
| --- | --- |
| `deprecated-tech-graphics` | 263 |
| `Old Tank Builder Icons` | 149 |
| `deprecated-missile-graphics` | 70 |
| `GFX Counter Icons` | 65 |
| `Old MD Tech Icons - Bird Save` | 53 |
| `consolidated-graphics-branch` | 36 |
| `User Interface`, `Power projection`, misc | 22 |

`resources/` is reference-only and unshipped, so this is not a runtime risk. But
658 files under directories named "Old" and "deprecated-" in an upstream PR reads
as an unswept working directory and will draw review time away from the code.
Exclude entirely from the contribution branch.

### G7 - fork-local changelog

`Changelog-OEM.txt` is OEM-only and should not ship upstream as a parallel
changelog. Do **not** pre-emptively write entries into `Changelog.txt`: AGENTS.md
prohibits touching that file unless explicitly asked, and notes a system new in
2.0.0 needs no entry for its own changes. Leave changelog wording to whatever the
maintainers request at submission time, and drop `Changelog-OEM.txt` from the
contribution branch. `changelog.d/google.md` and `changelog.d/oracle.md` are two
orphaned fragments - delete them.

---

## 8. Fixes in priority order

| # | Sev | Fix | Where |
| --- | --- | --- | --- |
| H1 | BLOCKER | Restore the 6 upstream files and narrow `.gitignore` in one forward-fixing commit (not a double revert - see G1) | `.gitignore`, 6 files |
| H2 | SERIOUS | Resolve the "Off is not off" boundary for `ISR_oem_events`, `USA_oem_events` and `gpu_development`: reword the rule descriptions, add a suppressing option, or fold the first two under the gate | `MD_game_rules_l_english.yml:876-879`, `00_corporate_history_effects.txt:196`, `01_oem_..._on_actions.txt:44` |
| H3 | SERIOUS | Add an explicit `independent_subsystems` allowlist to the contract and make the validator fail on any namespace dispatched from a Corporate History entry point that is neither registered nor allowlisted | `corporate_history_contract.json`, `validate_corporate_history_contract.py` |
| H4 | SERIOUS | Move the yearly dispatch off `on_daily_ABK` into the per-country monthly drivers (country-scoped per AGENTS.md:35 - do not use a global on_action) | `01_oem_..._on_actions.txt:12`, `02_linux_system_on_actions.txt:12` |
| H5 | SERIOUS | Delete the duplicated `USA_ibm_state_initialized` from inside the `OR` in 3 policy `visible` blocks | `USA_corporate_systems_dashboard.txt:149,356,460` |
| H6 | SERIOUS | Consolidate all 13 monthly drivers into `02_oem_corporate_history_monthly_on_actions.txt` | 7 x `99_TAG_on_actions.txt` |
| H7 | SERIOUS | Recast Google and Huawei option verbs to government instruments (~30 loc strings) | `MD_OEM_google_l_english.yml`, Huawei loc |
| H8 | SERIOUS | Dedicated art for the top `GFX_computer` beats; state a policy for the rest | `events/`, `MD_eventpictures.gfx` |
| H9 | POLISH | Read `CAN_matrox_events.txt:861` - 5-child `NOT` is NAND, likely a real bug | `events/CAN_matrox_events.txt:861` |
| H10 | POLISH | Resolve `POL_industrial_sovereignty_resolve_terminal` and 2 unused FIN triggers | POL / FIN files |
| H11 | POLISH | Trim 9 Oracle descriptions to 3 sentences | `MD_OEM_oracle_l_english.yml` |
| H12 | POLISH | Unify rule option naming (`disabled` vs `off`) | `00_game_rules.txt`, both trigger files |
| H13 | POLISH | Split policy decisions out of `*_dashboard.txt` into `USA_corporate_policies.txt` | `common/decisions/` |
| H14 | POLISH | Remove `gpu_development_reconstruct_history` from either CAN_ati or the bootstrap | `CAN_ati_effects.txt:188` |
| H15 | POLISH | Delete `runtime_evidence/`, `temp-aug8-*.yml`; untrack `.mcp.json`, `.vscode/*`; drop 8 planning docs | repo root |
| H16 | POLISH | Make pytest path assertions OS-agnostic so the AGENTS.md gate is runnable on Windows | `tools/**/tests/` |

---

## 9. Upstream PR decomposition

A 556-file, +133k-line PR will be closed unread.

```
PR1 FRAMEWORK --+-- PR2 VALIDATORS --+-- PR4 GPU --+-- PR6 USA CHAINS -- PR7 USA ECONOMY
                |                    |             |
                +-- PR3 GFX ---------+-- PR5 LINUX-+-- PR8 ASIA -- PR9 EUROPE -- PR10 DOCS
```

| PR | Purpose | Depends on | Scope | Risky files | Validation evidence | Runtime evidence | Reviewable independently because |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 FRAMEWORK | Game rules, gate triggers, dispatch skeleton, bootstrap, `corporate_history_apply_delta` / `clamp_value`. No chains. | - | `00_game_rules.txt` (+46), `MD_corporate_history_triggers.txt`, `01/02_oem_*_on_actions.txt`, framework half of `00_corporate_history_effects.txt`. ~6 files, ~800 lines | `00_game_rules.txt` (upstream also edits), dispatcher host | run_all_validators clean | P1, P2, P3 | Two rules and an empty dispatch skeleton; pure infrastructure with no content to judge |
| 2 VALIDATORS | Contract validator + contract JSON + 11 model tests | 1 | `validate_corporate_history_contract.py`, `corporate_history_contract.json`, `tools/tests/*` (~28k lines, tool-only) | The 7k-line validator itself | `python -m pytest` green on Linux | none | Pure tooling, gated by `tools-validation.yml`, zero game impact - mergeable on tests alone |
| 3 GFX | 80 event pictures + `MD_eventpictures.gfx` entries | - | `gfx/event_pictures/**`, `interface/MD_eventpictures.gfx` (+367) | `MD_eventpictures.gfx` (upstream +246 concurrently) | `validate_gfx_references.py`, `validate_unused_textures.py` | none | Verified zero sprite-name collision with upstream's 62 additions |
| 4 GPU | `gpu_development` chain - cross-national, no CH dependency | 1, 3 | `00_gpu_development.txt`, `00_gpu_development_effects.txt`, `MD_gpu_development_l_english.yml`. ~3 files | Bridge gates at `:113` / `:752` | contract validator | P3 | Self-contained; its CH bridge is already correctly gated - good exemplar to land first |
| 5 LINUX | Shared Linux ecosystem + national adapters | 1, 2, 3 | `MD_linux_system_*`, `02_linux_system_on_actions.txt`, `MD_linux_system_triggers.txt`. ~6 files | Adapter read/write boundary | `linux_national_adapter_contract_test.py` (91 reads / 10 write prefixes) | P8 | Contract-enforced read-only adapters make the blast radius provable |
| 6 USA CHAINS | IBM, Microsoft/Sun, Apple, Google, Oracle, HP, Dell, NVIDIA, Micron, TI, Motorola, AIG, Xbox, E3, BlackBerry | 1-5 | 16 event + 16 effect files + loc. ~40 files, ~50k lines | `USA_ibm_effects.txt`, cross-chain `USA_ibm_faction_*` writes from Microsoft | contract cross-chain ownership check | #25, #28, P5-P7 | Still large - split by chain if maintainers ask. IBM + Sun/Microsoft must land together (shared faction vars); the rest are independent |
| 7 USA ECONOMY | Real-options layer, dynamic modifiers, dashboard, 4 policy decisions | 6 | `USA_oem_real_options_effects.txt`, `05_USA_oem_economic_dynamic_modifiers.txt`, `USA_corporate_systems_dashboard.txt`, `USA_corporate_systems_ideas.txt`. ~6 files | Policy `visible` gates (fix H5 first), `modify_treasury_effect` balance | contract real-options check | P4 | Sits entirely on PR6's state; balance is the whole review and is isolated to one file |
| 8 ASIA | Nintendo, Sony, TSMC, Foxconn, TAI PC Giants, Lenovo, Huawei | 1-5 | ~14 files | `TAI_pc_industry` (merged via #198) | contract validator | #24, P8 | No dependency on USA chains |
| 9 EUROPE + ISR | Nokia, Ericsson, Siemens, ARM, France, Poland, Ukraine, Russia, ATI/Matrox, ISR | 1-5 | ~22 files | ISR (fix H2 first), FRA `collapsed_nation` guards | contract validator | #26, #27, P9 | No dependency on USA/Asia. ISR must be gated before this PR opens |
| 10 DOCS | 4 reference docs + `validation-pipeline.md` refresh | all | `.claude/docs/` x4, `docs/src/content/resources/` x2 | - | `docs-quality.yml` | - | Documentation only |

**Landing order:** 1, 2, 3, 4, 5, 6, 7, then 8 and 9 in parallel, then 10.
PRs 1-5 are about 45 files total and give maintainers the whole architecture
before a single company chain arrives.

---

## 10. Definition of done for "submit upstream"

All fourteen must be true. Current state: 0 of 14.

1. Six upstream files restored; `.gitignore` no longer deletes upstream content (H1)
2. Corporate History = Off either produces zero OEM events, or the rule text states exactly what stays on; verified in game (H2, P1)
3. Contract carries an explicit `independent_subsystems` allowlist and the validator fails on anything dispatched from a CH entry point that is neither registered nor allowlisted (H3)
4. Yearly dispatch survives the loss of its host country (H4, P2)
5. `error.log` clean after 10 in-game days in each of Full / Outcomes Only / Off (P3)
6. Save before scheduled event, reload, fires exactly once (P5)
7. Save after selection, reload, no reward replay (P6)
8. Upstream merged to `7098b472c4`, all 40 overlap files resolved per section 3, validators re-run
9. `python -m pytest` green on Linux CI and runnable on Windows (H16)
10. Contribution split per section 9; no PR over ~50 files
11. Stale artifacts removed (H15)
12. Issue #45 closed on evidence - voice fixed on Google/Huawei, generic-art share materially reduced or policy stated (H7, H8)
13. Issues #24-#28 have recorded results on their PRs, or are explicitly descoped with maintainer agreement
14. `rule_corporate_history` default (`full`) agreed with MD maintainers

---

## 11. Assessment

The parts of this system that are usually wrong are right. Idempotence,
event-fire discipline, capstone exclusivity, monthly-driver purity and adapter
read-only boundaries are mechanically enforced by a 7,000-line contract validator
with a 32-chain manifest, and each was confirmed independently rather than taken
on the validator's word. That infrastructure is the strongest argument for this
contribution and should lead the upstream conversation.

What blocks it is everything around the code: a `.gitignore` that silently
deletes upstream content, a scope boundary that is deliberate in the design docs
but invisible to the player at the rule switch, a dispatcher parked on a country
the player can erase, and a diff no human will read. All are fixable in days, not
months.

One structural note worth carrying forward. The contract validator is the reason
this system's hard properties hold, and it is also the reason B1 went unnoticed
for so long: it validates the 32 chains that opted in, so the three namespaces
that opted out are invisible to it. A contract that only checks its own members
cannot tell you what it is not covering. H3 exists to close that specifically -
the allowlist matters less as a gate than as a forced, reviewable statement of
what sits outside the rule.

Fix H1-H6, land PRs 1-5, and this becomes a strong contribution.
