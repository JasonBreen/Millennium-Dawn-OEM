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
- **Augmentation Boom (30–39):** `DEUSEX_augmentation.txt`; loc `_augmentation_`;
  `99_DEUSEX_augmentation_effects.txt`.
- **The Illuminati (40–49):** `DEUSEX_illuminati.txt`; loc `_illuminati_`;
  `99_DEUSEX_illuminati_effects.txt`.
- **A Traitor at the Table (50–59):** `DEUSEX_traitor.txt`; loc `_traitor_`;
  `99_DEUSEX_traitor_effects.txt`.

Localisation file names are `MD_DEUSEX_<subsystem>_l_english.yml`.

The next free block is 60–69.

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

## Augmentation Boom

The augmentation economy follows the games' timeline at year-level fidelity. The United States hosts Sarif
Industries and China hosts Tai Yong Medical. It does not read the opening's state. The monthly pulse offers
`DEUSEX.30` to the United States after 2007.1.1 (Sarif Industries was founded in Detroit in 2007) and `DEUSEX.31`
to China after 2009.1.1 (a scenario date, not a canon one). Each offer is spent on its date, and a host that does
not exist then never gets it.

Each host keeps `DEUSEX_aug_adoption` and `DEUSEX_aug_unrest`, both 0-100. Accepting the state contract costs 10
billion and starts adoption at 20; declining starts it at 10. Adoption only moves in steps of 10. Either way the host gets the `DEUSEX_augmentation_industry`
dynamic modifier, which `DEUSEX_update_augmentation` drives from the two values:

- research speed: adoption x 0.1%, up to +10%;
- factory output: adoption x 0.05%, up to +5%;
- army attack and defence: adoption x 0.08%, up to +8%, only after the military programme;
- stability: unrest x -0.15%, down to -15%.

Each month unrest grows by adoption x 0.05 and falls by 2. A funded Neuropozyne programme halves the growth and
costs 0.015 billion per point of adoption a month. At 20 adoption or more a host rolls 4% a month for a
Neuropozyne shortage (`DEUSEX.32`, one a year). At 60 unrest or more it gets anti-augmentation riots
(`DEUSEX.33`, one a year). Unrest is fractional, so unrest thresholds compare with `greater_than_or_equals`.

Decisions in `DEUSEX_augmentation_category`: fund research (10 billion, +10 adoption, every 180 days), the military
programme (50 PP, at 40 adoption, once), fund or end Neuropozyne (25 PP to start), and suppress anti-augmentation
groups (25 PP, -20 unrest, every 180 days).

After 2027.10.1 the Aug Incident hits every open host with adoption above 0 (`DEUSEX.34`), and one news event goes out to everyone
(`DEUSEX.35`). Stability falls by 3%, 6% or 10% depending on adoption, and unrest rises by 40. A biochip recall
costs 0.1 billion per point of adoption and cuts adoption by 30; a state of emergency costs 50 PP. After 2029.1.1 each
open host, even one at 0 adoption, chooses whether to adopt the Human Restoration Act (`DEUSEX.36`). Adopting it cuts adoption and unrest
by 50, sets `DEUSEX_aug_restricted` and closes every decision except the suppression decision.

The AI receives every event and decision. Treasury costs check `bankruptcy_incoming_collapse` and
`ai_has_high_deficit`; the AI never funds research at 50 unrest or more.

## The Illuminati

Eight major powers (USA, CHI, GER, ENG, FRA, SOV, JAP, RAJ) carry `DEUSEX_illum_influence`, 0-100. The first monthly
pulse sets it to 20 in the USA, 15 in China, Germany, Britain and France, and 10 elsewhere. Global state:

- three wings: `global.DEUSEX_illum_capital` (Page Industries), `global.DEUSEX_illum_media` (Picus Communications)
  and `global.DEUSEX_illum_security` (Belltower Associates), starting at 40, 30 and 30;
- `global.DEUSEX_illum_exposure`, the Masquerade's risk, starting at 10 and falling by 1 a month;
- `global.DEUSEX_illum_agenda`, stages 0-4;
- `global.DEUSEX_illum_member`, the one inner-circle government, if any.

Each month every target that is not the member gains 0.5 influence. It gains 0.5 more with an open augmentation
industry and 0.5 more once the agenda has started. The `DEUSEX_illuminati_grip` modifier costs it influence x 0.15%
political power and influence x 0.05% stability, doubled at agenda stage 4. At 40 influence or more a target
rolls 5% a month, at most every two years, for an offer (`DEUSEX.40`): 5 billion and +15 influence, or refuse for
2% stability and -5 influence.

Targets fight back in `DEUSEX_illuminati_category`:

- investigate the fronts: 25 PP, 60 days, -10 influence, +3 exposure, every 120 days;
- leak the files: 50 PP and 3% stability, -30 influence, +15 exposure, every 365 days.

A target with 30 influence can instead join the inner circle for 100 PP while the seat is empty. The member drops its
grip and gains `DEUSEX_inner_circle`:

- research speed: capital x 0.1%;
- political power per day: media x 0.004;
- civilian intelligence: security x 0.3%;
- stability: exposure x -0.1%.

Its decisions (`DEUSEX_inner_circle_category`):

- empower a wing: 25 PP; that wing +15 and the other two -3 each;
- direct the Illuminati at another target: 25 PP, +5 exposure, +10 influence there after 60 days;
- distribute enhancements, when it has an augmentation industry: 50 PP, +10 adoption, +10 unrest, +5 exposure;
- advance the agenda: 100 PP and 60 days per stage.

The agenda's stages, each with the requirement to reach it:

1. Shape the Narrative: media 40. Influence grows 0.5 a month faster.
2. The Control Biochip: capital 50, from 2025. Every augmentation host gains a fifth of its adoption as influence.
3. Restore Humanity: security 50, after the Aug Incident. The AI favors the Human Restoration Act three to one, and a
   target that adopts it gains 20 influence.
4. A New Order: every wing 40. The grip doubles.

At 70 exposure the Masquerade slips, at most once a year. A news event (`DEUSEX.41`) goes out and every target sheds
10 influence. The member then chooses (`DEUSEX.42`) to cut loose its strongest wing (-30, -40 exposure) or deny
everything (5% stability, -20 exposure). With no member, exposure falls by 30. A member that stops existing loses its
flag and modifier and frees the seat.

The wings' zero-sum balance, the Masquerade and the staged agenda take their shape from The Fire Rises: the
Cognoscenti's three factions and its public awareness meter, and Schwab's Agenda 2040 and cybernetic enhancements.
They are adapted to Deus Ex's canon, and no TFR text or script is reused. The Illuminati's inner circle, Page
Industries, Picus and Eliza Cassan, Belltower, the control biochip and the Human Restoration Act are canon. Governments
joining the inner circle is a scenario mechanic.

## A Traitor at the Table

Once per campaign, while the inner circle has a member and the agenda has started, the monthly pulse rolls 4% for a
traitor. `DEUSEX_start_traitor_hunt` picks one of five suspects into `global.DEUSEX_traitor` and copies their dossier
into `global.DEUSEX_traitor_wing`, `_stance` and `_face`. Hugh Darrow is excluded once the Aug Incident has happened,
because he is missing after Panchaea. The member gets `DEUSEX.50` and the `DEUSEX_traitor_category`.

The dossiers (wing; stance on augmentation; public face) are unique, so three clues always name one suspect:

| Suspect | Wing | Stance | Face |
| --- | --- | --- | --- |
| Bob Page | capital | for | corporate |
| Zhao Yun Ru | security | for | corporate |
| William Taggart | media | against | public |
| Elizabeth DuClare | media | for | public |
| Hugh Darrow | capital | against (privately) | corporate |

`global.DEUSEX_traitor_clock` starts at 18. Each month it falls by 1 and the traitor adds 3 exposure. Clue decisions
take 60 days each and set `DEUSEX_clue_wing`, `_stance` or `_face`. The category's text shows the revealed clues next
to the dossiers:

- Trace the Money: 50 PP, reveals the wing.
- Read the Leaks: 25 PP and +5 exposure, reveals the stance.
- Watch the Table: 25 PP and 1 month off the clock, reveals the face.

Accusing a suspect costs 50 PP, and each name can be accused again after 90 days. The right name ends the hunt: the
traitor's wing -10, exposure -20, +50 PP and +3% stability (`DEUSEX.53`). A wrong name costs the accused's wing 10,
adds 10 exposure and takes 3 months off the clock (`DEUSEX.54`). At 0 the traitor goes public: a news event names
them (`DEUSEX.52`), and the member (`DEUSEX.51`) loses its seat and falls back under the grip at 50 influence. Every
wing loses 10 and exposure rises 30. If the seat empties first, the hunt ends unsolved.

The AI reads only revealed clues. Each accusation's weight comes from `DEUSEX_<suspect>_fits`, which holds while
every revealed clue matches that dossier: 100 with all three clues, 20 with two, 5 when the clock is under 4.

The clock, the clue-gathering decisions and the dossier cross-check take their shape from The Fire Rises' Cognoscenti
traitor hunt. The suspects and their companies are canon. Their dossier traits other than Taggart's campaign and
Darrow's turn against augmentation are scenario inventions.

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
