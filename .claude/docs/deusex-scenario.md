# Deus Ex Scenario

The opt-in Deus Ex scenario. It is split into subsystems; each owns its own files and its own block of
event IDs, so parallel work does not collide. It ships on OEM only. Built like STALKER: see
[STALKER Scenario](stalker-scenario.md) for the patterns this follows.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's files.
  Add a subsystem with `python tools/generators/add_scenario.py subsystem DEUSEX <name> "<Display>"`.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Gate everything** on `DEUSEX_scenario_enabled = yes`. It reads a global flag that startup sets from
  `rule_deusex_scenario`; never read the rule from a trigger that can run at load.
- **Monthly work.** Add a line to `DEUSEX_monthly_pulse` in `common/scripted_effects/99_DEUSEX_pulse_effects.txt`. It runs once a month,
  in the scope of whichever country ticks first, so scope explicitly into what it touches.
- **AI.** Every decision and event option gets AI weights, and the AI must actually receive the
  content. If something is player-only, say so here. Check with `/scenario-audit DEUSEX`.
- **Context.** Bind delayed events to a fixed state or a per-event target. Never read a shared
  "current site" global from a queued event.
- **Changelog.** Each PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.

## Subsystems

- **Core (1–9):** `DEUSEX.txt`; loc `MD_DEUSEX_l_english.yml`;
  `99_DEUSEX_scripted_effects.txt`, `99_DEUSEX_pulse_effects.txt`, `99_DEUSEX_on_actions.txt`.
- **China (10–19):** `DEUSEX_china.txt`; loc `_china_`;
  `99_DEUSEX_china_effects.txt`.
- **Germany (20–29):** `DEUSEX_germany.txt`; loc `_germany_`;
  `99_DEUSEX_germany_effects.txt`.

Localisation file names are `MD_DEUSEX_<subsystem>_l_english.yml`.

The next free block is 30–39.

## Hooks into shared files

- `common/game_rules/00_game_rules.txt`: `rule_deusex_scenario`, off by default.
- `localisation/english/MD_game_rules_l_english.yml`: the rule's five keys.

Everything else lives in the scenario's own files, including its on_actions.

## Playable opening

This is an original 2000 bridge into the Deus Ex setting. It does not replay a
2027 incident early, introduce mature augmentation technology, or replace the
normal country focus trees. Metal Gear and Deus Ex have independent rules and
state; neither scenario reads the other's state.

The United States reviews a prosthetic-controller grant and its sponsor. China
checks imported research-controller shipments and their contracting authority.
Germany reviews a safety dossier and its undeclared sponsor. Each existing host
receives its introduction 15 days after startup, including AI hosts. The
introduction unlocks the shared preparation category.

Each country can purchase one audit for 25 political power. Its result arrives
60 days later. Public review costs one percentage point of stability; domestic
handling grants one percentage point. The selected outcome remains available for
future dated content. This slice implements no empty 2027 event, recurring audit,
new technology, or Targeted Operations integration.

After choosing public review, each country may request one records exchange for 15
political power. The fixed cycle is USA to Germany, Germany to China, and China
to USA. The counterpart must exist, have acknowledged its introduction, and be
at peace with the sender. The request arrives after one day. Domestic handling closes the local program without sharing. Accepting costs
the counterpart 10 political power and applies the existing `diplomatic_support`
opinion modifier in both directions, worth 20 opinion. Declining costs nothing.
The sender receives a report one day after the answer.

Every receipt option rechecks the sender's existence, pending request and peace
before applying costs or benefits. The country-scoped monthly hooks close a
pending request as interrupted if the counterpart disappears or the countries
go to war. Each transition sets the terminal phase before scheduling the
report. The report changes no gameplay state and grants no additional reward.
It retains the historical accepted result if relations end before delivery and
uses separate text to acknowledge that the counterpart is now unavailable.
No authority, program or request transfers to a civil-war tag or conquering
country. Missed introductions are not replayed if a host is restored later.

## Persistent state and event ownership

`DEUSEX_program_phase` lives on each fixed participating country: unset/0 before
the introduction, 1 ready to audit, 2 audit pending, 3 public review, 4 domestic
handling. `DEUSEX_exchange_phase` is country-owned: unset/0 unused, 1 pending,
2 accepted, 3 declined, 4 interrupted. Zero values are read without redundant
startup writes. Neither variable is clamped.

- Core USA: `.1` introduction, `.2` audit result, `.3` request from China,
  `.4` report about Germany.
- China: `.10` introduction, `.11` audit result, `.12` request from Germany,
  `.13` report about the United States.
- Germany: `.20` introduction, `.21` audit result, `.22` request from the
  United States, `.23` report about China.

Delayed events use literal national recipients and their country-owned phase.
They never read a mutable global recipient. Startup dispatch is owned by
`DEUSEX_initialize_scenario` after it records the enabled rule; it does not rely
on ordering against MD's shared startup-event dispatcher.

## Native acceptance checks

- Both rules off, each rule alone, and both enabled; no crossover behavior.
- Each of the three existing hosts receives one introduction after 15 days.
- One audit per host; result after 60 days; both stability outcomes are correct.
- Each fixed exchange route accepts, declines and closes on interruption.
- No 10-political-power charge or opinion benefit if receipt becomes invalid.
- No duplicated request cost, opinion benefit or report after save/reload.
- Absence or war while pending closes the sender on the next monthly pulse.
- Accepted history remains accepted if the counterpart disappears before report.
- AI hosts receive content and use weighted options and decisions.
- Normal focus trees, technology and Targeted Operations Off remain playable.

Source review and GitHub CI do not substitute for these in-game observations.
