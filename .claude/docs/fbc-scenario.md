# Federal Bureau of Control Scenario

The opt-in Federal Bureau of Control scenario. It is split into subsystems; each owns its own files and its own block of
event IDs, so parallel work does not collide. It ships on OEM only. Built like STALKER: see
[STALKER Scenario](stalker-scenario.md) for the patterns this follows.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's files.
  Add a subsystem with `python tools/generators/add_scenario.py subsystem FBC <name> "<Display>"`.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Gate everything** on `FBC_scenario_enabled = yes`. It reads a global flag that startup sets from
  `rule_fbc_scenario`; never read the rule from a trigger that can run at load.
- **Monthly work.** Add a line to `FBC_monthly_pulse` in `common/scripted_effects/99_FBC_pulse_effects.txt`. It runs once a month,
  in the scope of whichever country ticks first, so scope explicitly into what it touches.
- **AI.** Every decision and event option gets AI weights, and the AI must actually receive the
  content. If something is player-only, say so here. Check with `/scenario-audit FBC`.
- **Context.** Bind delayed events to a fixed state or a per-event target. Never read a shared
  "current site" global from a queued event.
- **Changelog.** Each PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.

## Subsystems

- **Core (1–9):** `FBC.txt`; loc `MD_FBC_l_english.yml`;
  `99_FBC_scripted_effects.txt`, `99_FBC_pulse_effects.txt`, `99_FBC_on_actions.txt`.
- **European Anomaly Desk (10–19):** `FBC_europe.txt`; loc `_europe_`;
  `99_FBC_europe_effects.txt`.
- **Polar Desk (20–29):** `FBC_polar.txt`; loc `_polar_`;
  `99_FBC_polar_effects.txt`. One case at a time.
  `FBC_monthly_polar_pulse` gives each Antarctic Treaty member with a working Ice Core Deep Drilling Rig
  (`antarctica_lab_ice_tech_boost > 0`) at station tier 2 or higher its own 2% monthly roll; one of the hits gets an
  Altered World Event in the core (`FBC.20`, to the station's controller). Sealing the
  borehole costs 25 PP and ends it. Reporting it sends `FBC.21` to the United States, which keeps
  `FBC_polar_country`. A response team contains it three times in four (`FBC.22`: +5 containment, a
  one-use excavation bonus for the controller), or fails (`FBC.24`). Declining or failing breaks it out
  (`FBC.23`): `FBC_polar_rig_down` stops the rig's laboratory output and iteration rewards, read in Antarctica's
  `antarctica_apply_single_laboratory_module_effect` and `antarctica_apply_single_laboratory_iteration_reward`, so
  blizzard damage and repairs are untouched. Hidden `FBC.25` ends it after 30 days and recalculates at once. Every
  close starts a 1,095-day cooldown. If the United States stops existing with a result queued, the pulse
  closes the case and returns the team.

Localisation file names are `MD_FBC_<subsystem>_l_english.yml`.

The next free block is 30–39.

## Hooks into shared files

- `common/game_rules/00_game_rules.txt`: `rule_fbc_scenario`, off by default.
- `localisation/english/MD_game_rules_l_english.yml`: the rule's five keys.
- `common/scripted_effects/07_targeted_operations_organization_cases.txt`: `FBC_apply_top_organization_sabotage` beside the STALKER sabotage call.
- Targeted Operations organizations 39 and 40 in `tools/data/targeted_operations.json`. Both are public state-security records at the host capital, which is what that class allows.

The Bureau is its own scenario. It does not read STALKER state, and STALKER does not read Bureau state. The two Targeted Operations rows are the only shared runtime hook.

The Polar Desk reads Antarctica's station state and never writes it. Its hooks in Antarctica are the `FBC_polar_rig_down` checks on the rig's laboratory output and iteration reward in `00_antarctica_effects.txt`, plus a call to `antarctica_recalculate_country_laboratory_effects`.

## Playable slice

Original cases, not a recreation of another game's plot. The United States holds two fixed sites: the Unscheduled Floor in New York (state 769) and the Sealed Wing in Washington (state 1182). Each case keeps its own phase and commitment. Response capacity starts at 2.

The European Anomaly Desk is an original body attached to the EU. Its name is provisional. The customs case uses Brussels (state 51) and the Ruhr (state 39). The coordinator is the Commission president when that office is filled, otherwise France, then Germany, then Belgium. Shared capacity is global because the coordinator can change. A queued customs event is bound to the country that received it.

Patriots content is not part of this scenario.

## Owner decisions and FBC-01

- **Event Horizon (O07, 2026-10-04):** the scenario stays off while Event Horizon is on, because Event Horizon replaces
  the United States host. `FBC_initialize_scenario` checks `EH_scenario_enabled`, which reads its rule directly and so
  works at startup. The rule text says so.
- **Case phases**, both American cases: 0 reported, 1 on file with no team (New York only), 2 investigating, 3 active
  containment, 4 archived, 5 continuing burden, 6 suspended because the site is out of reach.
- **Lost sites keep their case.** Phase 6 releases the team, and the case keeps its knowledge. `FBC_reopen_floor` and
  `FBC_reopen_wing` (25 PP, AI weight 50) appear once the United States controls the site again. They return the case
  to phase 0 and send its intake event (`FBC.1` or `FBC.4`) in 7 days.
- **Dashboard:** `FBC_bureau_category_desc` shows free teams, containment integrity, exposure and each case's phase,
  team and site, through `99_FBC_scripted_localisation.txt`.
- **EU coordinator (O05, confirmed 2026-10-04):** the Commission president when that office is filled, otherwise France,
  then Germany, then Belgium, each only while an EU member. With none available, the case waits at intake and the
  pulse tries again each month; nothing stands in for the EU.

## FBC-EU-01

Customs case phases: 0 waiting for the coordinator, 2 joint inquiry, 3 route restricted, 4 archived with a handling
protocol, 5 Belgian national handling, 6 German national handling, 7 unresolved burden.

- **Membership changes (T10):** pooled work (phases 2 and 3) needs the handling country to stay an EU member. If it
  leaves, `FBC_monthly_europe_pulse` releases the shared team, keeps the desk's knowledge and exposure, and returns the
  case to intake under the current coordinator. `FBC.11` also requires its recipient to be an EU member when it fires, so a
  handler that leaves between the pulse and the queued result gets nothing, and the next pulse resets the case.
  National handling (5 and 6) stays with the national service, which keeps the case and its costs. A handler that stops
  existing resets the case in every active phase, as before.
- **Host changes:** each queued event stays bound to the country that received it, so a new Commission president does
  not take over a case in progress; it coordinates the next intake.
- **Dashboard:** `FBC_europe_category_desc`, visible to every EU member, shows the phase, team, handler, knowledge and
  exposure, and states the membership rule.
- **Not verified in game:** membership loss mid-inquiry, a Commission handover during a case, and annexation of
  Belgium or Germany during national handling.
