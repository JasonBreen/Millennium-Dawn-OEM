# Metal Gear Scenario

The opt-in OEM scenario combines the existing USA-controlled Patriots network with finite national preparation cases for the United States, Japan and Russia. Shadow Moses occurs in 2005. Its tactical outcome stays recognizable; player choices change national authorization, disclosure and relations.

## Subsystems

- Core IDs 1-9: existing network events 1-3 in `METALGEAR.txt`; new USA preparation events 4-8 in `METALGEAR_preparation.txt`. Core English strings remain in `MD_METALGEAR_l_english.yml`.
- Shadow Moses IDs 10-19: briefing 10, aftermath 12 and news 13 in `METALGEAR_shadow_moses.txt`. ID 11 is retired and must not be reused. English strings use `MD_METALGEAR_shadow_moses_l_english.yml`.
- Japan IDs 20-29: introduction 20, review 21, crisis response 22, outgoing return 23, incoming USA request 24 and crisis report 25. Files use `METALGEAR_japan` and `99_METALGEAR_japan_effects.txt`.
- Russia IDs 30-39: introduction 30, review 31, crisis response 32, outgoing return 33, incoming Japan request 34 and crisis report 35. Files use `METALGEAR_russia` and `99_METALGEAR_russia_effects.txt`.
- Operations IDs 40-49: scandal 40 in `METALGEAR_operations.txt`. Files use `METALGEAR_operations`, `99_METALGEAR_operations_effects.txt` and `METALGEAR_operations_decisions.txt`, whose decisions join the existing `METALGEAR_network_category`.
- **Proliferation (50–59):** `METALGEAR_proliferation.txt`; loc `_proliferation_`;
  `99_METALGEAR_proliferation_effects.txt`.
- **Tanker and Big Shell (60–69):** `METALGEAR_incidents.txt`; loc `_incidents_`;
  `99_METALGEAR_incidents_effects.txt`.

Localisation file names are kept per subsystem.

- The next free block is 70–79. Every subsystem keeps its own events, effects, decisions and English localisation.
- Shared hooks: `rule_metalgear_scenario` in the game rules and its English keys; `METALGEAR_dispatch_shadow_moses` in the 2005 yearly effect; the existing Konami milestone guards in `99_JAP_scripted_effects.txt`.

The scenario reads its rule only in the startup initializer. Runtime gates read `GLOBAL_METALGEAR_scenario_enabled`. Event Horizon's existing host conflict remains. There are no authored crossovers or dependencies on Deus Ex.

## Existing Patriots network

The United States' controller, human or AI, still runs the network. Japan and Russia receive their own government preparation and diplomatic cases; they do not become network controllers. The earlier USA-only ownership decision applies to the network dashboard, not these new national cases.

The existing core remains intact: global coherence starts at 70, reach at 50, exposure at 10 and capacity at 2. Its three fixed nodes are defense procurement, special operations oversight and information control. Audits cost 25 Political Power and hold a commitment for two months; repairs cost 50 and hold one for three months. Quarterly degradation, confirmation, compartmentalization and monthly exposure retain their existing behavior.

## National preparation and exchanges

Startup schedules introductions after 15 days for each existing fixed country. No replacement recipient or reannexation bootstrap is used. These procurement and record-review cases are original scenario bridges, not claims of dated canon incidents.

Each country has one review costing 25 Political Power and lasting 60 days. The timed decision stays visible while running and uses its phase to prevent repeat use. Its report offers cooperative review, which enables one outgoing request, or classified review, which grants 1% Stability and closes that outgoing branch.

Country-owned `METALGEAR_review_phase` is 1 available, 2 running, 3 report awaiting choice and 4 completed. `METALGEAR_review_policy` records 1 cooperative or 2 classified. An unset phase is an introduction not yet acknowledged. No new zero-valued variables need startup initialization.

The fixed exchange cycle is USA to Japan, Japan to Russia and Russia to USA. Each one-time request costs 15 Political Power. The recipient accepts for 10 Political Power and gives mutual `diplomatic_support` (+20 opinion), or refuses for free without a penalty. Benefits apply in the recipient's guarded option; the sender's return is only a notification.

Country-owned `METALGEAR_request_phase` is 0 unused, 1 pending, 2 accepted, 3 refused or 4 interrupted. The once-monthly fixed-country checks quietly close a pending request if its partner disappears or war begins. They send a return notification when the sender exists. No request is resent or rewarded twice.

## Network payoff and risk

The network now pays the United States and can hurt it. The monthly operations pulse runs after the network pulse,
adds the `METALGEAR_patriots` dynamic modifier to the USA and refreshes it from the three meters:

- political power per day: (coherence - 50) x 0.005, so +0.10 at the starting 70 and -0.25 at 0;
- stability: reach x 0.04% minus exposure x 0.1%, so +1% at the start;
- civilian intelligence: reach x 0.2%, so +10% at the start.

Three operations join the network category. Each costs 25 Political Power, holds one commitment for 60 days and can
be repeated after 120. Each adds 3 exposure when it starts, or 6 if the node it runs through is really compromised,
whatever the estimate says. The result arrives when it ends:

- Steer Defense Procurement (defense procurement node): a one-use 50% research bonus for armor and military electronics.
- Manage the News Cycle (information control node): +3% popularity for the ruling party.
- Influence a Foreign Desk (special operations oversight node), targeted at 21 fixed countries at peace with the
  USA: +3% American influence there.

Operations compete with audits and repairs for the same two commitments. When exposure passes 60, the USA gets
`METALGEAR.40` at most once a year. Burying the story costs 50 Political Power, 10 coherence and removes 20 exposure.
Letting it break costs 5% stability, 25 coherence and 15 reach, and resets exposure to 10.

The AI runs operations only while exposure is 45 or lower. These operations are original scenario mechanics, not
dated canon incidents.

## Shadow Moses in 2005

The 2005 yearly dispatcher calls `METALGEAR_dispatch_shadow_moses`. It schedules the briefing one day later. January placement is scenario timing at year-level canon fidelity, not a claim about an exact canonical day.

Alaska state 814 is a coarse control guard, not an exact island map. Missing USA or missing USA control at dispatch marks the incident unavailable once. Losing the host or its control while the crisis is pending interrupts the chain without a replay after annexation.

The USA briefing authorizes a compartmentalized response, authorizes limited partner disclosure, or refuses discretionary support. Authorization costs 25 Political Power if the national review completed, otherwise 50. Solid Snake's operation against the FOXHOUND nuclear threat remains the recognizable story; no option grants equipment, nuclear stockpiles, states or war goals.

Japan and Russia receive their own requests for records. Providing records costs 10 Political Power; withholding is free. Earlier accepted exchanges affect AI willingness. Their contributions are local historical choices, not remote control of the tactical operation.

The aftermath arrives 30 days after the briefing choice. A prepared authorized response costs 1% Stability; an unprepared or unsupported response costs 2%. If the USA promised disclosure, it can honor the agreement with cooperating partners for mutual +20 opinion or suppress the promised report for mutual -10 `diplomatic_insults`. Relations are applied only to existing cooperating partners at peace with USA. Each partner receives a terminal report describing its contribution and the resulting disclosure policy.

USA-owned `METALGEAR_crisis_phase` is 1 briefing, 2 response pending, 3 aftermath awaiting choice and 4 terminal. `METALGEAR_crisis_route` is 1 compartmentalized, 2 partner disclosure or 3 unsupported. `METALGEAR_crisis_disclosure` records 1 honored or 2 suppressed. Each partner's `METALGEAR_crisis_records` is 1 supplied, 2 withheld or 3 interrupted.

The only new shared crisis result is `global.METALGEAR_shadow_moses_result`: 1 prepared authorized resolution, 2 unprepared or unsupported resolution, 3 interrupted or 4 unavailable. The existing started flag records the historical dispatch and prevents repeated activation. The old 2004 monthly start, lost-step replay, commitment flow, follow-on decisions and debug start are retired.

## AI and acceptance

Human and AI USA, Japan and Russia receive the same choice events. Cost-aware weights consider bankruptcy; diplomatic choices also consider opinion and the completed national policy. Pure return reports use minor flavor notifications. Monthly work stays under the scenario's existing once-monthly entrypoint and explicitly scopes fixed countries.

Native acceptance remains required: disabled isolation, enabled introduction timing, all national review choices, reciprocal requests under cooperation/refusal/war/annexation, 2005 dispatch, all authorization/disclosure outcomes, Alaska control loss, rapid annexation and restoration between monthly checks, and save/reload during a timed review or delayed crisis. Rapid annexation and restoration between monthly checks has no authored timeout or resend; delivery recovery is unverified. Source checks and CI do not establish gameplay balance or rendered UI behavior. Development saves receive no migration support.

## Proliferation, Tanker and Big Shell

Events 50-58 cover national procurement trails, American proliferation intake, consenting Japanese/Russian exchanges and terminal reports. Event 59 briefs Tanker. Events 60-64 cover Tanker aftermath, Big Shell and national incident returns; 65-69 remain reserved. The generator owns both subsystem hooks. The dated incidents follow [Konami's chronology](https://www.konami.com/mg/archive/mgs_tlc/sp/index.html): Tanker 2007 and Big Shell 2009. Government cases are original scenario material; tactical protagonists and the manipulated information story remain recognizable.

After each opening review, a national procurement decision costs 25 PP and takes 60 days. USA reserves one existing network commitment; partners use national investigators. Each report records cooperation, national retention or concealment. Unfinished preparation closes unprepared in 2005. Country-owned pf_phase is 2 work, 3 report, 4 complete or 5 interrupted/unprepared. pf_policy records the historical handling choice.

The proliferation inquiry opens after the Shadow Moses result, with a 2006 fallback for incomplete records. USA chooses a 25 PP/60-day inquiry holding one commitment, with or without partner requests, or free concealment. Each partner consents for 25 PP or refuses without penalty. pf_exchange is 1 pending, 2 delivered, 3 refused or 4 interrupted/unanswered. War/disappearance closes only that exchange. A completed inquiry adds 5 exposure and 5 reach per accepted partner. Concealment reduces exposure by 10. Partner reports do not replay rewards.

Tanker and Big Shell each own phase, route, commitment, disclosure, timer and result. Phase 1 is intake, 2 response, 3 aftermath, 4 closed or 5 host disappeared. Independent command costs 50 PP, refunded by 25 with usable national procurement or proliferation findings. Each existing cooperating partner at peace refunds another 5 PP from independent authorization; affordability checks the actual discounted cost. Existing channels cost 25 PP and add 5 exposure. Both hold one commitment for 60 days. Local emergency authority costs no PP or capacity and remains available after New York loss. Loss during work releases its commitment and downgrades only that incident to emergency aftermath. Missing USA closes active work without transfer or replay. Every release is idempotent.

Independent verification loses 5 coherence; compromised channels lose 10 coherence and reach; local emergency response loses 10 coherence and 2% stability. Disclosure adds 10 exposure and loses 10 reach, improves consenting partners' relations and adds 1% stability with a completed inquiry. Restriction adds 5 exposure. Earlier evidence changes authorization and credibility; disclosure history remains visible and influences partner AI willingness. No tactical result, state, equipment or focus tree is selected.

Acceptance includes both partners accepting/refusing, war/annexation while pending, full network capacity, missing Shadow Moses records, New York loss, duplicate deliveries and separate Tanker/Big Shell results. Pending-work save/reload and native AI/rendering remain required separately from Python source execution. All rules remain independent and disabled by default.
