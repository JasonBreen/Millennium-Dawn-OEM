# Metal Gear Scenario

The opt-in Metal Gear scenario. It is split into subsystems; each owns its own files and its own block of
event IDs, so parallel work does not collide. It ships on OEM only. Built like STALKER: see
[STALKER Scenario](stalker-scenario.md) for the patterns this follows.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's files.
  Add a subsystem with `python tools/generators/add_scenario.py subsystem METALGEAR <name> "<Display>"`.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Gate everything** on `METALGEAR_scenario_enabled = yes`. It reads a global flag that startup sets from
  `rule_metalgear_scenario`; never read the rule from a trigger that can run at load.
- **Monthly work.** Add a line to `METALGEAR_monthly_pulse` in `common/scripted_effects/99_METALGEAR_pulse_effects.txt`. It runs once a month,
  in the scope of whichever country ticks first, so scope explicitly into what it touches.
- **AI.** Every decision and event option gets AI weights, and the AI must actually receive the
  content. If something is player-only, say so here. Check with `/scenario-audit METALGEAR`.
- **Context.** Bind delayed events to a fixed state or a per-event target. Never read a shared
  "current site" global from a queued event.
- **Changelog.** Each PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.

## Subsystems

- **Core (1–9):** `METALGEAR.txt`; loc `MD_METALGEAR_l_english.yml`;
  `99_METALGEAR_scripted_effects.txt`, `99_METALGEAR_pulse_effects.txt`, `99_METALGEAR_on_actions.txt`,
  `99_METALGEAR_scripted_triggers.txt`, `99_METALGEAR_scripted_localisation.txt`, `METALGEAR_decisions.txt` and
  `00_METALGEAR_network_category.txt`. Used: 1 (briefing), 2 (quarterly report), 3 (audit findings).
- **Shadow Moses (10–19):** `METALGEAR_shadow_moses.txt`; loc `_shadow_moses_`;
  `99_METALGEAR_shadow_moses_effects.txt`. Used: 10 (dossier), 11 (complication), 12 (after action), 13 (news).

Localisation file names are `MD_METALGEAR_<subsystem>_l_english.yml`.

The next free block is 20–29.

## Hooks into shared files

- `common/game_rules/00_game_rules.txt`: `rule_metalgear_scenario`, off by default.
- `localisation/english/MD_game_rules_l_english.yml`: the rule's five keys.
- `common/scripted_effects/99_JAP_scripted_effects.txt`: the 2001, 2015 and 2021 Konami milestones skip their
  events while the scenario is on and set the historical Outcomes Only flag instead, because those beats treat
  Metal Gear as a game.

Everything else lives in the scenario's own files, including its on_actions.

## Controller and gating

- **Owner decisions (2026-10-04):** the United States' controller, human or AI, runs the Patriots, and no other
  country sees their content (O01). The scenario is off while Event Horizon is on (O07): `METALGEAR_initialize_scenario`
  checks `EH_scenario_enabled`, which reads its game rule directly and so works at startup. Konami's Metal Gear beats are
  suppressed under the rule.
- `METALGEAR_is_controller` (USA, scenario on, network set up) gates the category, every decision and every country
  event. The monthly pulses scope into `USA`; with no United States the network waits.
- `METALGEAR_setup_network` runs once (`GLOBAL_METALGEAR_network_ready`), separate from the enabled flag, and sends the
  briefing `METALGEAR.1`.

## Network state (MG-01)

All state is global and scenario-owned. Nothing duplicates queryable country state.

| Variable                      | Start | Meaning                                                    |
| ----------------------------- | ----- | ---------------------------------------------------------- |
| `METALGEAR_coherence`         | 70    | Whether the network can act consistently                   |
| `METALGEAR_reach`             | 50    | Where it has access                                        |
| `METALGEAR_exposure`          | 10    | Evidence that has escaped; -1 a month, +2 per compromised node (+1 compartmentalized) |
| `METALGEAR_capacity`          | 2     | Free commitments; audits, repairs and the incident hold them |

Nodes are fixed records 0 defense procurement, 1 special operations oversight, 2 information control, in arrays:
`METALGEAR_node_true` (0 secure, 1 strained, 2 compromised; oversight starts strained), `_known` (what the network
believes), `_confirmed` (months left on a confirmation), `_audit` and `_repair` (months left), `_audited` (audit just
finished, for `METALGEAR.3`).

- **Quarterly** (`METALGEAR_network_quarter`, months 1, 4, 7 and 10): each node not under repair degrades one step with
  chance `20 + exposure / 5 - coherence / 5`, halved while compartmentalized, clamped 2-40. Degradation is hidden: the
  known value only changes through an audit, a repair or the incident. Compartmentalized, coherence and reach fall by 1;
  otherwise reach rises by 1 while coherence is above 60, up to 80. A human controller gets `METALGEAR.2`.
- **Decisions** (`METALGEAR_network_category`, the dashboard): audit a node (25 PP, one commitment, two months, confirms
  it for six); repair a known strained or compromised node (50 PP, one commitment, three months, one step);
  compartmentalize or end it. AI weights: audits favor unconfirmed nodes, repairs favor known compromised ones,
  compartmentalization starts above 40 exposure and ends below 20.

## Shadow Moses (MG-01)

Opens in February 2004 (`METALGEAR_monthly_shadow_moses_pulse`), once (`METALGEAR_shadow_moses_started`). A debug-only
decision starts it early. One incident, so its delayed events read globals safely.

1. **Dossier** (`METALGEAR.10`): the first priority is the weapons program (1), the story (2) or the response (3, $2B).
   Each holds one commitment, or costs 10 coherence when none is free.
2. **Complication** (`METALGEAR.11`, 10 days later): commit a second line (also covers the next objective), cut the
   priority loose (commitments return now, +5 coherence, -5 exposure), or hold the course (50% the priority is lost).
3. **After action** (`METALGEAR.12`, 14 days later): `METALGEAR_resolve_shadow_moses` records the milestone once and
   applies the outcome. Secure oversight going in holds the response on its own.

| Objective | Kept                                  | Lost                                              |
| --------- | ------------------------------------- | ------------------------------------------------- |
| Program   | reach +5                              | reach -5, procurement one step worse              |
| Story     | exposure +10                          | exposure +25, USA stability -2%                   |
| Response  | coherence +5, oversight one step better | coherence -10, oversight one step worse         |

The incident confirms procurement and oversight, returns every commitment and opens one follow-on decision: move the
design data into the network (program kept), bury the program (story held), or publish an official account. Every
country gets the news event `METALGEAR.13`, whose text depends on whether the story held.

The recognizable beat is the same every time: the facility is retaken, the prototype destroyed and the rebellion's
leader dead. Choices change what the network keeps, not the canon.

## AI

The United States receives every country event whether human or AI, and every option and decision has weights. The
quarterly report and audit findings go only to a human, since they carry no choices.

## Not yet verified

- No in-game run: startup, the briefing, the pulses, the incident and save/reload are untested.
- Canon: the dossier names FOXHOUND, Metal Gear REX and the remains demand, and frames FOXHOUND as under the network's
  oversight. That framing and the complication's intermediary need the canon review in handoff §16.1.
- Balance values are first-pass.
