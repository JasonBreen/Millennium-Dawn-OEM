# Experimental strategic contingencies

The implementation connects [MD #6404](https://github.com/MillenniumDawn/Millennium-Dawn/issues/6404)
and [OEM #548](https://github.com/JasonBreen/Millennium-Dawn-OEM/issues/548)
behind two separate default-Off game rules. It includes nuclear response and collapse,
prepared faction legacies, recorded research, resource-limited recurring crises,
and peaceful containment. It is a prototype awaiting native HOI4 and multiplayer testing.

Base: OEM `100154673f9a149b69df71054f1c6d6221bf48bb`, November 5, 2026.
Branch: `codex/nuclear-contingency-slice-20261105`.

## Nuclear response and collapse

Only the existing `strategic_nuclear_strike` raid enters the new path. All four
result levels currently devastate the entire victim in MD; this implementation
preserves that existing definition of a qualifying strategic strike. Tactical and
single-state raids remain unchanged. Götterdämmerung is required for this rule.

1. The raid records the attacker, victim, prepared-contingency state, and response
   status in global arrays before damage. The first attacker remains the response
   target when several countries strike the same victim. Every attacker is separately
   condemned once, including another attacker arriving during the pending window.
2. A surviving nuclear power with an eligible doctrine and a nuclear missile in its
   stockpile sets aside one missile. This is an abstract emergency strike package.
   It does not test range, launch-site survival, defenses, triad research or triad odds.
3. The victim chooses retaliation or restraint before this rule applies devastation.
   Unanswered offers close after seven days. Capitulation or annexation before the
   choice defaults to restraint; no event needs to reach an annexed country.
   A reserved missile is consumed even if the response is withheld or expires.
4. An approved response queues the same response window on a valid, surviving enemy.
   Each victim can receive one catastrophic episode per campaign. The response is
   claimed before queuing the counterstrike. Later strikes retain ordinary state
   devastation but do not refresh the new collapse or its response allowance.
5. The victim's episode is marked resolved before damage, collapse callbacks and
   aftermath. Any contingency that was armed at impact activates before damage.

With the rule Off, each original raid result's victim and actor effects are retained.
With it enabled, original actor costs and strike tracking still run. The response
package is in addition to the incoming raid's existing costs, not a refund or a new army.

| Collapse effect                     |         Balanced |            Chaos |
| ----------------------------------- | ---------------: | ---------------: |
| Factory and dockyard output         |             -75% |             -90% |
| Construction speed                  |             -60% |             -80% |
| Training time                       |            +100% |            +200% |
| Research speed                      |             -25% |             -50% |
| Population and corporate tax income |             -50% |             -75% |
| Immediate stability                 |       -20 points |       -20 points |
| Peaceful reconstruction             | 365 days, 200 PP | 730 days, 200 PP |

Existing state fallout lasts 1,095 days. Reconstruction removes the new national
penalty, while physical damage and fallout recover under their existing rules.
Each strategic attacker receives a three-year pariah spirit and a decaying -100
opinion modifier from surviving countries. A shared 365-day cooldown bounds the
worldwide production/construction shock; simultaneous collapses cannot stack it.
No territory transfer or direct population change is added.

## Prepared faction legacies

Eligibility requires an independent, uncapitulated faction leader with at least
50 factories, five faction members including itself, and a surviving partner on
another capital continent. Named alliances and country tags are not hard-coded.
An unresolved nuclear strike blocks preparation and arming.

Preparation costs 200 political power and requires 180 days of continued eligibility,
with +5% consumer goods and -10% research speed. Losing eligibility cancels preparation
without a refund. Successful preparation unlocks a separate 100-PP arming choice.
The preparing and armed spirits provide visible warning and ongoing opportunity costs.
Armed support costs +2% consumer goods and -5% research speed.

Arming registers one source country, reserves up to three unreserved surviving
partners in engine faction-array order, and records the source's Construction IV,
V or VI research. The source and its partners are never registered again in the
same roles. There are at most eight source records and 24 recipient records for
the campaign, including consumed, declined, missing and stood-down records.
A 25-PP stand-down decision ends support costs without freeing a replacement record.
These permanent limits are deliberate prototype anti-recycling rules, not final balance.

Qualifying collapse is capitulation, annexation or the completed strategic episode.
Government replacement, faction dissolution, rename and voluntary leadership transfer
do not activate the contingency. A previously qualified leader's armed legacy can
survive leadership transfer, but transfer alone does not count as defeat.

Global source status is `1 armed`, `2 consumed` or `3 stood down`. Activation claims
the record before delivering anything and copies the aggressor into each recipient
record. Capitulation followed by annexation cannot activate it twice. Research and
recipient records remain valid without querying the fallen source's continued existence.
Existing recipients missing at activation are closed without an event. Membership
is an arming-time snapshot; former partners receive an optional offer even if their
later faction membership changes. Crisis diplomacy is rechecked against current state.

Accepting a legacy costs 50 PP and applies political pressure through modifiers.
There is no ideology replacement, automatic war declaration, new tag, new unit or
equipment grant. Declining or ignoring the offer for fourteen days closes it permanently.
Player tag switching does not reset records. Restoring the same country does not rearm
it or replay an accepted archive. A genuinely new civil-war country is a separate
actor and must complete its own preparation. Preparation records the completing
country's identity; copying that variable cannot arm a new country. Ledger-bound
spirits do not pass to civil-war tags, and ledger mutations verify that the current
country owns its slot. Native civil-war inheritance remains part of the release matrix.

## Research, recurrence and containment

An accepted archive requires ten factories, an actual next-tech prerequisite,
50 PP, 90 days and -10% research speed during absorption. It grants one 25%
technology-specific bonus in Balanced or 50% in Chaos, only for the next unresearched
Construction IV, V or VI tech recorded at arming. The archive is consumed before
granting the bonus. There is no full-tree unlock, ahead-of-time reduction or instant
production capability. Lost prerequisites, capitulation or containment can prevent
delivery; later source research does not enlarge the snapshot.

| Recurring crisis control     | Value                                                             |
| ---------------------------- | ----------------------------------------------------------------- |
| Initial and maximum capacity | 3 per recipient in Balanced, 6 in Chaos                           |
| Cost to open a crisis        | 1 capacity, consumed before delivery                              |
| Pending crisis limits        | 1 per recipient, 4 shared globally                                |
| Minimum spacing              | 90 days between offers                                            |
| Unanswered offer             | Closes after 14 days                                              |
| Escalation choice            | 50 PP for a puppet war goal against the recorded aggressor        |
| Replenishment                | 100 PP, 90-day project at +5% consumer goods, restores 1 capacity |
| Support repeat cooldown      | 180 days                                                          |
| Permanent containment        | 200 PP and 180 days of peace; stability at least 30%              |

No response declares war for a human or AI. A war goal permits ordinary game diplomacy
and AI war planning to create later conflict. Existing wars, war goals, faction
membership, non-aggression pacts, subjects and absent or capitulated targets block new
crises. The global cap covers pending script crises, not independently declared wars.
The first target is the recorded collapsing country's aggressor; no fallback enemy
is invented if it disappears or becomes an ally.

Recurring notifications carry no gameplay actions. Escalation and defusal use live
decisions, so an old notification cannot authorize or consume a later crisis.
The paid decision charges 50 PP before the war-goal effect claims the pending slot.

At most one pulse is scheduled per accepted recipient. The global due date prevents
replayed or stale pulses from bypassing the cooldown. Capacity exhaustion stops new
pulses. Blocked diplomacy or a full global cap retries only after another 90 days,
without spending capacity. Continued paid support can sustain recurrence for the
campaign, with no automatic replenishment. Containment closes the archive, zeros
capacity, cancels future processing and releases a pending crisis slot once.
Annexation closes the recipient record and releases its slot before the tag disappears.
Delayed events cannot restart a contained or restored recipient.

There are no new daily or monthly country scans. The only world-country passes apply
rare first-use diplomatic condemnation and a cooldown-limited trade shock. Other
processing visits the eight sources, 24 recipients or the relevant faction members.
With both rules Off, no records, timers or periodic processing are created.

## Verification and release limits

Local verification on November 5, 2026:

- The focused contingency suite passes 48 tests.
- The broader tools suite initially reported 11,341 passed, 65 skipped and 17 failed.
  All 17 failures reproduced on unchanged `100154673f`. They then passed on the
  feature checkout after providing Git Bash host access, task-local Python command
  adapters and the omitted reference portrait. No unrelated repository code was changed.
- The original tactical/state raid source, all four strategic Off branches and all
  actor-effect bodies were compared with the base commit and preserved.
- Referenced idea, decision, category and event sprites resolve to existing base assets.

The focused content tests execute the actual new scripted effects and triggers with
native damage, opinion and equipment APIs modeled at their boundaries. They cover
recording, duplicate callbacks, reciprocal and simultaneous strikes, terminal choices,
snapshot research, JSON model save/restore, eligibility, exhaustion, shared caps,
cadence, replenishment, containment and annexation cleanup. This is script-level
regression evidence. It is not native engine serialization, scope dispatch or MP proof.

No game was started, interrupted or reconfigured. No playset, installed mod or save
was changed. No PR was published. New saves using fixed pregame rules are the supported
test target; no old-save migration or mid-campaign rule changes are supported.

The numbers are conservative implementation assumptions and require gameplay tuning.
Release remains gated on the following approximate native test plan, including
recorded game version, DLC set, exact commit and multiplayer participants.

### Test plan

**Playthrough A: USA and SOV, 2000, both rules Off**

- [ ] Confirm both rules default Off and no new decisions or records appear.
- [ ] Exercise each strategic raid result and compare state damage, fallout,
      actor costs and existing retaliation tracking with the base commit.
- [ ] Repeat without Götterdämmerung; confirm the nuclear rule and raids are unavailable
      while the independent faction rule remains available.

**Playthrough B: USA and SOV, 2000, Balanced**

- [ ] Prepare and arm an eligible leader; check all PP, civilian and research costs,
      warning visibility, 180-day cancellation and the separate arming action.
- [ ] Repeat with a qualifying player-created faction, a tiny faction, a same-continent
      faction, a leadership swap and a subject; confirm the documented eligibility policy.
- [ ] Launch a strategic strike with a valid missile reserve. Verify precisely one
      actual stockpiled missile is removed before damage, doctrine gates work, and the
      response event arrives before devastation or capitulation callbacks.
- [ ] Retaliate, withhold, ignore for seven days and annex the victim during the window
      in separate saves. Confirm the recorded target and default-restraint behavior.
- [ ] Strike one victim from two attackers and strike two nuclear powers simultaneously.
      Confirm each attacker is condemned once, first targets remain stable and responses
      terminate without repeated collapse or economic-shock stacking.
- [ ] Save and reload before preparation, while armed, during both response windows,
      during absorption, during a crisis and after containment. Re-click stale events.
- [ ] Capitulate and then annex the armed source. Restore it and capitulate it again.
      Confirm one activation and no duplicate research, capacity or offers.
- [ ] Remove a recipient before activation; move another to a different faction;
      remove or ally the aggressor. Verify valid messages, safe missing scopes and diplomacy.
- [ ] Accept, decline and time out separate successor offers. Test research prerequisites,
      later source research, the 90-day absorption cost and no repeat bonus.
- [ ] Exhaust capacity and verify new pulses stop. Fund repeated support in a separate
      uncontained run, and demonstrate recurring choices across resolved wars.
- [ ] Open crises from multiple contingencies, fill four shared slots, annex a carrier,
      and verify one release per slot. Check one pending crisis per recipient.
- [ ] Contain a recipient with a pending crisis and absorption in flight; verify future
      events, support and archive grants remain closed after restoration.
- [ ] Finish 365 days of peaceful reconstruction; verify only the new national collapse
      spirit is removed and state damage/fallout follow their ordinary recovery.

**Playthrough C: Chaos and multiplayer/observer**

- [ ] Confirm stronger penalties, six capacity, 50% bonus and 730-day reconstruction.
- [ ] Repeat simultaneous strikes, intentional defeat, annexation, restoration, faction
      swaps, civil-war succession, disconnect/rejoin and save/reload with two human clients.
- [ ] Verify both clients receive identical ledger statuses, reserve charges, deadlines,
      active-crisis counts, choices and synchronized AI randomness.
- [ ] Run an extended observer campaign and an equivalent Off baseline. Record queued
      events, active crises, tick performance, error.log and any desynchronization.
- [ ] Demonstrate an uncontained supported legacy and a separately contained one.
      Confirm human ideology, alliance obligations and war declarations retain agency.
