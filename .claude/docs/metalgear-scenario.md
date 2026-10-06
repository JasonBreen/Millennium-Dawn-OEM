# Metal Gear Scenario

The opt-in OEM scenario combines the existing USA-controlled Patriots network with finite national preparation cases for the United States, Japan and Russia. Shadow Moses occurs in 2005. Its tactical outcome stays recognizable; player choices change national authorization, disclosure and relations.

## Ownership and hooks

- Core IDs 1-9: existing network events 1-3 in `METALGEAR.txt`; new USA preparation events 4-8 in `METALGEAR_preparation.txt`. Core English strings remain in `MD_METALGEAR_l_english.yml`.
- Shadow Moses IDs 10-19: briefing 10, aftermath 12 and news 13 in `METALGEAR_shadow_moses.txt`. ID 11 is retired and must not be reused. English strings use `MD_METALGEAR_shadow_moses_l_english.yml`.
- Japan IDs 20-29: introduction 20, review 21, crisis response 22, outgoing return 23, incoming USA request 24 and crisis report 25. Files use `METALGEAR_japan` and `99_METALGEAR_japan_effects.txt`.
- Russia IDs 30-39: introduction 30, review 31, crisis response 32, outgoing return 33, incoming Japan request 34 and crisis report 35. Files use `METALGEAR_russia` and `99_METALGEAR_russia_effects.txt`.
- The next free block is 40-49. Every subsystem keeps its own events, effects, decisions and English localisation.
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
