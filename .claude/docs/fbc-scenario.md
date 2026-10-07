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
  Altered World Event in the core (`FBC.20`, to the station's controller). The pulse waits for an initialized
  Bureau. The United States keeps that controller in `FBC_polar_country` and the station in
  `FBC_polar_station_id` from dispatch until the case closes; a result applies only while
  `FBC_polar_case_rig_stands` still finds the rig there. Sealing the
  borehole costs 25 PP and ends it. Reporting it sends `FBC.21` to the United States. A response team contains it three times in four (`FBC.22`: +5 containment, a
  one-use excavation bonus for the controller), or fails (`FBC.24`). Declining or failing breaks it out
  (`FBC.23`): `FBC_polar_rig_down` stops the rig's laboratory output, iteration progress and iteration rewards,
  read in Antarctica's `antarctica_process_station_research_progress`,
  `antarctica_apply_single_laboratory_module_effect` and `antarctica_apply_single_laboratory_iteration_reward`, so
  blizzard damage and repairs are untouched. Hidden `FBC.25` ends it after 30 days and recalculates at once; the
  flag lapses after 31 days on its own if `FBC.25` is lost. Every close starts a 1,095-day cooldown. If the
  United States stops existing with a result queued, or the controller stops existing before a team is
  committed, the pulse closes the case and returns the team.
- **Silent Hill (30–39):** `FBC_silenthill.txt`; loc `_silenthill_`;
  `99_FBC_silenthill_effects.txt`.

Localisation file names are `MD_FBC_<subsystem>_l_english.yml`.

The next free block is 40–49.

## Silent Hill

A Bureau case in Maine (state 764), from 2000. It is part of this scenario, not one of its own (owner decision,
2026-10-06; OEM issue #453). Konami IP: text is original, names appear only as references, and it never goes
upstream.

The fog lives on state 764 as `FBC_sh_fog`, 0-100. The first pulse sets it to 10 and adds the state-scoped
`FBC_silent_hill_fog` modifier, which `FBC_update_silenthill_fog` drives from it:

- local supplies: fog x -0.004, so -0.4 at 100;
- construction speed: fog x -0.3%, so -30% at 100;
- local resources: fog x -0.2%, so -20% at 100;
- attrition for the controller: fog x +0.2%, so +20% at 100.

Each month the fog rises by 1. While a response team is in town it falls by 1 instead, and while a cover-up runs it
rises by 2.

The case lives on USA beside the Bureau's other cases. `FBC_sh_phase` runs 0 quiet, 1 reported, 2 intervention running
and 3 answered, and `FBC_sh_intervention` records 1 team, 2 quarantine or 3 cover-up for later slices. At 25 fog,
with USA holding Maine, `FBC.30` brings three contradictory reports:

- Send a response team: one of the two Bureau teams, -10 fog, answered after 6 months.
- Quarantine Toluca County: 50 PP and 2% stability, answered after 8 months.
- Lose the reports: -5 exposure, answered after 10 months.

The town answers the intervention it was given:

- The team comes back (`FBC.31`, 60%): +5 containment, -15 fog.
- The team does not come back (`FBC.32`, 40%): -10 containment, +5 fog, and either +5 exposure or 2% stability for
  -5 exposure.
- The quarantine line breaks (`FBC.33`): 25 PP for -5 fog, or lift it for +5 exposure and +10 fog.
- The cover-up surfaces (`FBC.34`): 50 PP to hold exposure to +5, or 2% stability and +15 exposure.

Losing Maine pauses the case's timer and frees its team. Back in Maine, a team intervention recommits a free team
before its timer resumes, and waits while none is free. `FBC.30` needs USA to hold Maine on arrival. It sets phase 1
itself, so reports lost to a change of control go out again a week later.

The Bureau dashboard (`FBC_bureau_category_desc`) gains a Toluca County line from
`99_FBC_silenthill_scripted_localisation.txt`. The fog shows in bands (thin, heavy, thick, covering the town), read
straight from the state.

### The Siren, visitors and the Order

Two more values live on state 764, both 0-100:

- `FBC_sh_visitors`: from 25 fog, letters draw a twentieth of the fog in visitors each month, half that under
  quarantine. The town feeds on them: every 50 visitors add 1 fog a month.
- `FBC_sh_order`: from 50 fog, the Order grows by 1 a month plus 1 for every 50 visitors, half that once the Bureau
  has someone inside (`FBC_sh_order_watched`).

`FBC_silenthill_town_events_month` runs on USA once the case is on file and USA holds Maine:

- The Siren (`FBC.35`) from 40 fog, at 0.15% a month per point of fog (6% at 40, 15% at 100), 180 days apart. It costs
  1% stability, adds 10 fog and the Otherworld (`FBC_silent_hill_otherworld`: -0.5 supply, -50% construction, +25%
  attrition) for 30 days. A team in town can hold and record it (70%: +5 containment; 30%: lost, -10 containment, +5
  exposure). During an intervention the Bureau can pull back for 25 PP, which delays the town's answer by 2 months
  and adds 5 fog. It can always call it a weather alert for +5 exposure and +10 visitors.
- Letters (`FBC.36`) at 20 visitors, 180 days apart. Turning visitors back costs 1 PP for each visitor on record when
  the letters arrive and sends three quarters of that same count home (+2 exposure). Tracking them gives +3
  containment and +5 Order. Letting them come costs +5 exposure and +5 fog.

The Siren, the letters and the Rite start their cooldowns when they arrive. A 7-day pending flag covers each while it
is queued, so one lost to a change of control goes out again.
- The Order (`FBC.37`) at 40, once; it marks the Order known on arrival, so a lost notice goes out again a week later.
  A raid needs a free team and works half the time, 65% above 59 containment and 35% below 30 (success: -40 Order,
  -10 fog, +5 containment; failure: -10 containment, +10 exposure, +10 Order). Putting someone inside costs 50 PP for
  -15 Order and halves its growth for good. Leaving it alone costs nothing now.
- The Rite (`FBC.38`) at 80 Order once it is known, a year apart. Stopping it needs a free team at even odds
  (success: -50 Order, -20 fog, +5 containment; failure: the rite is finished). Evacuating the county costs 100 PP
  and 3% stability, clears every visitor and takes 30 Order for +10 fog. Letting it happen, or failing to stop it,
  finishes the rite: -10 or -15 containment, more exposure, less Order, +20 or +25 fog and 60 days of the Otherworld.

The dashboard adds visitor bands (few, steady, many) and, once the Bureau knows of it, Order bands (quiet, gathering,
ready).

Next slice (#453): the Leave, In Water and Rebirth endings, with the UFO and Dog jokes behind their own sub-rule. The
block has one free ID left (39), so the endings need the next free block.

## Hooks into shared files

- `common/game_rules/00_game_rules.txt`: `rule_fbc_scenario`, off by default.
- `localisation/english/MD_game_rules_l_english.yml`: the rule's five keys.
- `common/scripted_effects/07_targeted_operations_organization_cases.txt`: `FBC_apply_top_organization_sabotage` beside the STALKER sabotage call.
- Targeted Operations organizations 39 and 40 in `tools/data/targeted_operations.json`. Both are public state-security records at the host capital, which is what that class allows.

The Bureau is its own scenario. It does not read STALKER state, and STALKER does not read Bureau state. The two Targeted Operations rows are the only shared runtime hook.

The Polar Desk reads Antarctica's station state and never writes it. Its hooks in Antarctica are the `FBC_polar_rig_down` checks on the rig's lab count, laboratory output and iteration reward in `00_antarctica_effects.txt`, plus a call to `antarctica_recalculate_country_laboratory_effects`.

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
