# Economic Forum System

Economic forums are yearly summits that compete for governments, companies and
headline speakers (Issue #4802). The World Economic Forum is the incumbent. The
St. Petersburg International Economic Forum runs from the start. Six more forums
wait for a founder: the Visegrád Economic Conference, the Boao Forum for Asia, the
Global South Economic Forum, the African Development Conference, the Arctic
Economic Forum and the Transatlantic Technology Forum. A great power boycotting a
forum can found a seventh, the Independent Economic Forum, as a breakaway.
A forum is a registry slot, not an event chain, so a new forum is data plus
localisation.

Files:

- `common/scripted_effects/01_econ_forum_effects.txt`: registry, cycle, scoring.
- `common/scripted_triggers/01_econ_forum_triggers.txt`: core members, track
  identity and interest, invitations.
- `common/decisions/econ_forum_decisions.txt`: founding, preparation, program
  tracks and scheduling.
- `events/EconomicForums.txt`: `econ_forum.1-11`, `econ_forum_news.1-12`.
- `common/scripted_localisation/01_econ_forum_scripted_localisation.txt`: names,
  standings and the program view.
- Hooks: `econ_forum_setup` in `on_startup` (`00_on_actions.txt`),
  `econ_forum_monthly_update` in the global monthly block (`MD_on_actions.txt`)
  and the `econ_forum_deal@PREV` bonus in `AI_country_selection_calculation`
  (`99_AI_investment_scripted_effects.txt`).

## Registry

Global arrays share one index, the forum id. Every effect takes the id in the
temp variable `ef_i`, and a program track id in `ef_t`.

| Array                       | Meaning                                         |
| --------------------------- | ----------------------------------------------- |
| `econ_forum_host`           | Host country id; 0 until founded                |
| `econ_forum_seat`           | Seat state: the host's capital when registered  |
| `econ_forum_state_led`      | 1 when a government runs it and gains from it   |
| `econ_forum_prestige`       | 0-100 standing                                  |
| `econ_forum_month`          | Summit month (1-12)                             |
| `econ_forum_preparing`      | 1 from preparation until the summit             |
| `econ_forum_invites_left`   | Personal invitations left this cycle            |
| `econ_forum_sponsors`       | Corporate points bought this cycle (max 25)     |
| `econ_forum_speakers`       | Headline speakers booked this cycle (max 3)     |
| `econ_forum_track_count`    | Tracks on this cycle's program (max 3)          |
| `econ_forum_tracks`         | Track on the program, index `forum * 6 + track` |
| `econ_forum_track_prestige` | Sector prestige, index `forum * 6 + track`      |
| `econ_forum_last_heads`     | Heads of government at the last summit          |
| `econ_forum_last_ministers` | Ministerial delegations at the last summit      |
| `econ_forum_last_score`     | Score of the last summit                        |
| `econ_forum_cycle`          | Preparations opened; a guest action's cycle id  |
| `econ_forum_ceremonies`     | Signing ceremonies booked this cycle (max 3)    |
| `econ_forum_last_ceremonies`| Ceremonies signed at the last summit            |
| `econ_forum_council`        | Council track + 1; 0 until launched             |
| `econ_forum_message`        | This cycle's summit message (0 none, 1-3)       |
| `econ_forum_controversial`  | This cycle's controversial speaker (0 none, 1-7) |
| `econ_forum_star`           | This cycle's star speaker: track + 1 (0 none)   |
| `econ_forum_room_seats`     | Private room seats given this cycle (max 4)     |

| Id  | Forum                               | Month | Founder            | Core members        |
| --- | ----------------------------------- | ----- | ------------------ | ------------------- |
| 0   | World Economic Forum                | 1     | SWI, prestige 80   | None                |
| 1   | Visegrád Economic Conference        | 9     | POL, CZE, HUN, SLO | V4                  |
| 2   | St. Petersburg Intl. Economic Forum | 6     | SOV, prestige 35   | BLR KAZ ARM KYR TAJ |
| 3   | Boao Forum for Asia                 | 3     | CHI, from 2001     | Asian nations       |
| 4   | Global South Economic Forum         | 11    | Developing power   | Developing powers   |
| 5   | African Development Conference      | 5     | Sub-Saharan power  | Sub-Saharan         |
| 6   | Arctic Economic Forum               | 10    | Arctic nation      | Arctic nations      |
| 7   | Transatlantic Technology Forum      | 4     | NATO power         | NATO members        |
| 8   | Independent Economic Forum          | Set   | Boycotting GP      | Host's faction      |

Only the World Economic Forum is private; the rest are state-led. Founded forums
start at 15 prestige. A developing power is a regional power with GDP per capita
under 20. The Arctic nations are NRY, DEN, ICE, FIN, SWE, CAN, SOV and USA.
Founding costs 100 PP (Boao 50) and needs stability above 40% and peace.

A forum follows its seat. When the seat state's owner is not the host, the old
host loses the forum, alive or not, and the cycle in progress is cancelled. The
seat owner takes it over and `econ_forum_news.6` fires, unless it already hosts a
forum; then the forum stands vacant, still listed with its prestige, until its seat
owner is free. Each invitation event keeps its forum's seat, so a reply answered
after its forum changed hands or closed is refunded and does nothing.

Per-country arrays use the same forum index:

- `econ_forum_status`: this cycle. 0 none, 1 standing invitation, 2 personal
  invitation, 3 ministers attend, 4 head of government attends, -1 declined.
- `econ_forum_last`: level at that forum's last summit (0, 3 or 4).
- `econ_forum_streak`: consecutive summits attended.
- `econ_forum_agenda`: this cycle's delegation agenda. 0 none, 1 investors, 2 deals, 3 showcase.
- `econ_forum_sponsor_cycle`, `econ_forum_bid_cycle`, `econ_forum_request_cycle`: the forum cycle a guest last
  sponsored, bid or requested an invitation in.
- `econ_forum_boycott`: 1 while the country boycotts that forum.
- `econ_forum_walkout_host`, `econ_forum_walkout_forum` (plain variables): the leader of the latest walkout this
  country followed while that leader hosts a forum, and the forum it walked out of; cleared when the country
  rejoins that forum.

A host carries `econ_forum_hosted` (its forum id), the flag `econ_forum_preparing`
while preparing, and `econ_forum_view_selected` / `econ_forum_view_prestige`, a
six-slot copy of its program that the decision text reads. One country hosts at
most one forum.

## Program Tracks

| Track | Name                     | Interested governments                        |
| ----- | ------------------------ | --------------------------------------------- |
| 0     | AI and technology        | GDP per capita 20 or more                     |
| 1     | Energy                   | Energy deficit, or oil exports above 1        |
| 2     | Finance                  | GDP 500 or more, or GDP per capita 50 or more |
| 3     | Defense industry         | At war, or defence spending law 04 or higher  |
| 4     | Infrastructure and trade | GDP per capita under 20                       |
| 5     | Development              | GDP per capita under 7                        |

A host puts up to three tracks on each program (10 PP each). An AI host runs its
forum's three strongest tracks. Each forum starts with three identity tracks at its
prestige and the rest at half, so an AI host opens with its identity and then
follows whatever its summits build:

| Forum          | Identity tracks                      |
| -------------- | ------------------------------------ |
| WEF            | AI, finance, development             |
| Visegrád       | Energy, defense, infrastructure      |
| St. Petersburg | Energy, finance, infrastructure      |
| Boao           | AI, infrastructure, development      |
| Global South   | Energy, infrastructure, development  |
| African        | Finance, infrastructure, development |
| Arctic         | Energy, defense, infrastructure      |
| Transatlantic  | AI, finance, defense                 |

After each summit a track on the program moves 40% toward the score; a track off
it keeps 95% of its prestige.

## Yearly Cycle

1. **Preparation** opens two months before the summit month. The host gets
   `3 + prestige / 25` personal invitations. Standing invitations go to last
   year's attendees, core members and, at 60 prestige or more, every country in
   `global.PR_regional_or_greater_powers`. A human invitee gets `econ_forum.2`,
   Each invitation queues its forum id in `econ_forum_invite_queue` and each
   event claims the oldest one in `immediate`, saving the host as
   `econ_forum_inviter`, so invitations from several forums never collide. A human host gets
   `econ_forum.1` and the decisions. An AI host runs `econ_forum_ai_prepare`.
2. **Host decisions** (human host):
   - Invite a regional power (15 PP) or a neighbor outside that pool (10 PP),
     +15 attendance chance. Invitations close a
     month before the summit so every reply resolves in time.
   - Paid replies to an invitation need the political power they cost.
   - Buy a sponsor package: 3.0 treasury and 10 PP for 5 corporate points.
   - Book a headline speaker: 50 PP, a roll of `60 + (ours - rival) / 2`,
     clamped to 20-90. A speaker landed while the WEF is also preparing is taken
     from it. `econ_forum.4` reports the result.
   - Add a program track: 10 PP, up to three.
3. **Summit** in the summit month. AI invitees roll attendance, every invitee is
   tallied, the score is computed and prestige moves 30% toward it.

Outside preparation a host can reschedule once every two years (50 PP): the month
after its strongest rival's (counter-programming) or six months after it. Founding
or rescheduling a summit one or two months away opens preparation at once; one
month away leaves no time for personal invitations, for AI hosts too. A reschedule
that lands on the current month refunds its 50 PP and starts no cooldown.

AI hosts reschedule through `econ_forum_ai_reschedule`, run after the monthly
timing pass. A host with over 50 PP and no reschedule in two years whose summit
falls within a month of a stronger rival's pays 50 PP and moves six months past
it. The AI never counter-programs, which would only set up the next clash.

An AI host of a state-led forum buys one sponsor package (3.0 treasury) when its
treasury is above 10 and one speaker attempt (50 PP) when it has more than 150 PP.
The World Economic Forum is private: its partners fund 15 corporate points and two
speaker attempts every cycle, whatever Switzerland can afford.

A summit always comes at least 11 months after the forum's previous one
(`econ_forum_months_since`, which counts calendar months for every founded forum,
vacant or not), so rescheduling right after a summit waits for the next cycle
instead of holding a second summit that year.

## AI Attendance

`econ_forum_ai_decide_attendance`, clamped to 0-95:

| Factor                                          | Chance                 |
| ----------------------------------------------- | ---------------------- |
| Forum prestige                                  | × 0.6                  |
| Personal invitation                             | +15                    |
| Streak                                          | +3 each, max +15       |
| Opinion of host above 25 / below -25            | +10 / -15              |
| Same faction as host                            | +10                    |
| Core member                                     | +15                    |
| At war with host                                | -100                   |
| NATO or EU member, host under Western sanctions | set to 0 after all     |
| Host and guest both in BRICS                    | +15                    |
| BRICS or Asian guest of a host pivoting East    | +10                    |
| Each track on the program that interests them   | + track prestige × 0.1 |
| Led a delegation to each other forum last cycle | -10 each               |
| More prestigious forum within one month         | -20                    |

A roll under the chance attends. A roll under 40% of the chance sends the head of
government, but only to forums with prestige 30 or more, or as a core member.

### Russia and BRICS

- A host with `SOV_western_sanctions` is boycotted: a NATO or EU AI government's
  attendance chance is set to 0 after every other factor. The first summit it holds
  with no NATO or EU delegation recorded fires `econ_forum_news.7` once
  (`econ_forum_boycott_reported` on the host).
- A full BRICS member (`RAJ_BRICS`) hosting sends standing invitations to every other
  full member; full and associate members get +15 toward each other's forums.
- A sanctioned host can take **Pivot to the East** (50 PP) outside preparation, since
  invitations go out when preparation opens: for 365 days
  (`econ_forum_pivot_east`), BRICS members and Asian nations get standing
  invitations and +10 attendance. The AI takes it with 100 PP or more.

## Delegation Agenda

A human guest who accepts an invitation (`econ_forum.2`) gets `econ_forum.5` and picks what its delegation
pushes. The event inherits the invitation's inviter and seat, and `econ_forum_resolve_invitation` checks both
again, so the agenda lands on the forum that invited it or not at all. An AI guest picks when it decides to
attend: GDP per capita under 20 courts investors, a great or super power showcases, any other country deals.

After the summit score and the track update, `econ_forum_apply_agendas` pays every attending guest (the host has no agenda),
then clears its agenda:

| Agenda    | Payoff                                                                                         |
| --------- | ---------------------------------------------------------------------------------------------- |
| Investors | `econ_forum_investor_pitch_modifier` for 365 days: the delegation bonus again, stronger kept     |
| Deals     | `econ_forum_summit_deal` (+15, decay 1) both ways with the host and every other attending guest |
| Showcase  | Influence in the host, `prestige × 0.02`%, doubled for a head of government; +2 to each program track that interests the guest |

## Guest Actions

Each forum row in the International Systems Forums tab has four buttons for any player who does not host it
(`econ_forum_guest_row`).

| Button  | Requirements                                                           | Effect                                                                                                                |
| ------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Sponsor | Preparing, under 25 sponsor points, once a cycle, not boycotting, at peace with the host; $1.5B, 10 PP | +3 sponsor points (cap 25); the host gains `econ_forum_session_sponsor` (+10) toward us                                  |
| Speak   | Preparing, our delegation going (status 3 or 4), under 3 speakers, once a cycle; 25 PP | 40% chance, +20 with a head of government, +10 as a great or super power. A win books a speaker (`econ_forum_keynote_booked`, counted in `global.econ_forum_guest_speakers`, which WEF poaching cannot take). `econ_forum_deliver_keynotes` pays at the summit, to an attending booker only: `econ_forum_keynote_modifier` (foreign influence, `prestige × 0.002`, the stronger value kept) for 365 days. `econ_forum.6` reports the bid either way |
| Request | Preparing with invitations open (the first month, not the last), an AI host at peace with us, no invitation or refusal yet, not boycotting, once a cycle; 15 PP | Chance `30 + (100 - prestige) × 0.3`, +20 as a great or super power, +15 if the host's opinion of us is above 25, -20 below -25, clamped 5-95. A yes sends a standing invitation (`econ_forum.2`); a no fires `econ_forum.7` |
| Boycott | 25 PP to start; ending is free                                         | Cancels our delegation and its agenda, and releases a keynote booked for the summit in preparation; the forum loses 2 prestige (5 for a great or super power); the host gains `econ_forum_boycotted` (-30) toward us; no invitations reach us until we rejoin; a great or super power fires `econ_forum_news.8`. The prestige loss and news land once a cycle (`econ_forum_boycott_cycle`); boycotters cannot be invited (`econ_forum_can_be_invited`) |

### Walkouts

A great or super power's first boycott of a forum in a cycle (`econ_forum_start_boycott` sets `ef_boycott_news`)
runs `econ_forum_lead_walkout`. Every AI government in the boycotter's faction follows it out half the time if it:

- does not host the forum and is not in the host's faction,
- does not like the host (opinion 25 or less),
- can afford a boycott (`econ_forum_can_boycott`).

Each follower pays and counts as its own boycott: 25 PP, prestige loss, the host's opinion modifier, a booked
keynote released. If the leader hosts a forum of its own, that forum gains 1 prestige per follower, and each
follower gets `econ_forum_walkout_host` and a standing invitation to the leader's summits until it rejoins.

The news is `econ_forum_news.9` when anyone followed, naming the leader's forum when there is one (via
`econ_forum_news_rival` on the host), and `econ_forum_news.8` otherwise.

### Summit Messages

A player host picks one message per summit during preparation (25 PP each, reset when preparation opens).
An AI host picks in `econ_forum_ai_prepare`, paying 25 PP for a state-led forum when it has over 75:
Strategic Autonomy under Western sanctions or Pivot to the East, Open for Business below 50 prestige, and a Media
Blitz for a state-led forum whose last summit scored above its prestige, with treasury over 30. The Forums tab row
tooltip shows each forum's message, council and last ceremonies.

| Message            | Decision                     | Effect                                                                                  |
| ------------------ | ---------------------------- | --------------------------------------------------------------------------------------- |
| Open for Business  | `econ_forum_message_open`     | Every invited AI government +10 attendance; score +3                                   |
| Strategic Autonomy | `econ_forum_message_autonomy` | Core members and the host's faction +15 attendance, every other AI invitee -10          |
| Media Blitz        | `econ_forum_message_media`    | $2B more; score +5, and prestige moves 50% toward the score instead of 30%, both ways |

### Private Room

Each summit can hold an invitation-only private room: a closed session where a few heads of state meet chief
executives and investors, as Davos does. Seats are recorded on the guest as `econ_forum_room^forum = 1` and reset
when preparation opens; a boycott or a declined invitation gives the seat back.

- **AI organizers**, the WEF's included, seat `1 + prestige / 30` invited governments (max 4) in
  `econ_forum_ai_prepare`: great or super powers, or governments the host likes (opinion above 50), never one at
  war with the host.
- **Player host:** `econ_forum_invite_to_private_room`, 10 PP, an invited regional or greater power, up to 4 seats.
- **Human guest:** `econ_forum.11` offers the seat (queued like invitations, host saved as `econ_forum_room_host`);
  declining (`econ_forum_decline_room`) frees it, only at the forum whose seat the event saved
  (`econ_forum_room_seat`) and while it is preparing.
- **AI guest:** +10 attendance while seated.

At the summit, after attendance, `econ_forum_hold_private_room` gathers every seated government that attended plus
the host. Each gets `econ_forum_private_room_modifier` (5% cheaper investment) for 365 days and
`econ_forum_private_room` (+15, decay 1) toward everyone else in the room, and each seated attendee adds 2 to the
score. 15% of sessions leak (`econ_forum_news.12`): the forum gains 2 prestige and everyone in the room loses 2%
stability.

### Star Speakers

A player host takes `econ_forum_book_star_speaker` (75 PP, a free speaker slot, once a summit) and picks the star in
`econ_forum.10`; cancelling refunds the 75 PP. Like the controversial speaker, the choice is snapshotted and
only open while `econ_forum_speaker_choice_open` holds. Unlike `econ_forum_book_speaker` there is no roll and no poaching.
`econ_forum_book_star` fills a speaker slot, adds 3 to the star's sector at once and stores the track in
`econ_forum_star`. At the summit, AI governments interested in that track (`econ_forum_interested_in_track`) are
10 more likely to attend. The AI does not book stars.

| Star | Available | Sector |
| --- | --- | --- |
| Jensen Huang | Always | AI and Technology |
| Demis Hassabis | 2010 | AI and Technology |
| Dario Amodei | 2021 | AI and Technology |
| Fatih Birol | 2015 | Energy |
| Warren Buffett | Always | Finance |
| Christine Lagarde | 2011 | Finance |
| Jens Stoltenberg | 2014 | Defense Industry |
| Ngozi Okonjo-Iweala | 2021 | Infrastructure and Trade |
| Muhammad Yunus | Always | Development |
| Bill Gates | Always | Development |

### Controversial Speakers

A player host takes `econ_forum_book_controversial_speaker` (25 PP, a free speaker slot, once a summit), and
`econ_forum.9` picks the speaker; cancelling refunds the 25 PP. The decision snapshots the forum and cycle
(`econ_forum_speaker_forum`, `econ_forum_speaker_cycle`), and a speaker can only be picked while that booking is
still open (`econ_forum_speaker_choice_open`); otherwise only the refund remains. `econ_forum_book_controversial` fills a speaker
slot and adds 5 to the speaker's sector at once. At the summit the speaker adds 4 to the score, AI governments that
object (`econ_forum_objects_to_speaker`) are 15 less likely to attend, and objecting regional powers take
`econ_forum_controversial_speaker` (-10) toward the host.

| Id  | Speaker          | Available | Sector                   | Objectors                             |
| --- | ---------------- | --------- | ------------------------ | ------------------------------------- |
| 1   | Nick Land        | Always    | AI and Technology        | Democratic governments                |
| 2   | Reza Negarestani | 2008      | Energy                   | Oil exporters (`oil_exports` above 1) |
| 3   | Neema Parvini    | 2019      | Finance                  | EU members                            |
| 4   | Aleksandr Dugin  | Always    | Defense Industry         | NATO members                          |
| 5   | Slavoj Žižek     | Always    | Development              | Nationalist and fascist governments   |
| 6   | Jamie Dimon      | 2006      | Finance                  | Communist governments                 |
| 7   | Howard Lutnick   | 2024      | Infrastructure and Trade | BRICS members and associates          |

An AI host from the Soviet tag books Dugin 30% of the time when it has over 100 PP and a free slot.

A player guest whose bid wins can take a hard line in `econ_forum.6` (`econ_forum_keynote_hard`), while that keynote
is still booked (`econ_forum_bid_tag`): at delivery its
keynote bonus is 50% larger, and the host takes `econ_forum_hard_line` (-15) toward it.

### Councils

A forum with 50 or more prestige can launch one standing council, for good, on its strongest track at that moment
(`econ_forum_launch_council`): the player host of a state-led forum takes a 100 PP decision, an AI host pays 100 PP
when it has over 150 (before its speaker purchase), and the WEF's partners launch it free when preparation opens,
whoever hosts it. `econ_forum_news.11` announces it.

Members are governments that attended the forum's last two summits (`econ_forum_streak` 2 or more; a boycott resets
the streak):

- AI attendance +10.
- `econ_forum_council_session`, after attendance: each member present, the host included, gets its track's
  modifier for 365 days and adds 1 to the summit score, up to 10 (`econ_forum_council_member_present`).

| Track          | Modifier                           | Bonus |
| -------------- | ---------------------------------- | ----- |
| AI             | `research_speed_factor`            | +2%   |
| Energy         | `energy_gain_multiplier`           | +3%   |
| Finance        | `receiving_investment_cost_modifier` | -5% |
| Defense        | `production_factory_efficiency_gain_factor` | +3% |
| Infrastructure | `production_speed_infrastructure_factor` | +5% |
| Development    | `stability_factor`                 | +2%   |

### Signing Ceremonies

The host of a state-led forum books ceremonies with invited governments during preparation: up to three a summit,
recorded on the guest as `econ_forum_ceremony^forum = 1` and cleared when the next preparation opens.

- **Player host:** `econ_forum_plan_ceremony`, 15 PP, targeting an invited regional or greater power (status above
  0) at peace.
- **AI host:** after its invitations, with over 100 PP, up to two invitees it likes (opinion above 25), 15 PP each.
- **Human guest:** `econ_forum.8` announces it, claiming its forum from `econ_forum_ceremony_queue` and saving the
  host as `econ_forum_ceremony_host`; declining (`econ_forum_decline_ceremony`) frees that slot.
- **Boycott or decline:** a guest that boycotts the forum (`econ_forum_start_boycott`) or declines its invitation
  (`econ_forum_answer_invitation`) loses its ceremony, and the slot frees.
- **AI guest:** +10 attendance chance while a ceremony is booked.

At the summit, after attendance, `econ_forum_close_ceremonies` signs one for each attending guest with a booking:
`econ_forum_signed_agreement` (+20, decay 1) both ways, and the guest gets `econ_forum_deal@<host>`, so the host's
investors favour it for 365 days, the reverse of the agreement every attendee signs. Each ceremony adds 3 to the
summit score. `econ_forum_last_ceremonies` feeds the standing lines and the host's summit report.

### Breakaway Forum

`econ_forum_found_breakaway` (150 PP, stability above 40%, peace) is open to a great or super power that boycotts a
forum and hosts none, while slot 8 is unfounded. It founds the Independent Economic Forum against the most
prestigious founded forum the country boycotts, hosted or vacant:

- Prestige starts at 15 plus 15% of that forum's prestige, which the old forum loses.
- Each sector starts at half the old forum's sector prestige, so the AI host runs what the old forum was known for.
- The summit meets six months after the old forum's, so the two never clash.
- The host's faction are core members (`econ_forum_is_core_member`, through `var:ef_host`), so they are always
  invited and attend more often.
- `econ_forum_news.10` names both forums (the old one through `econ_forum_news_rival` on the founder).

The AI takes it with 200 PP or more. Slot 8 has no identity tracks and is founded once per campaign; after that it
follows its seat like any other forum.

### AI Guests

AI regional and greater powers use Sponsor, Speak and Boycott on the same terms as a player. Request stays
player-only, since AI attendance comes from invitations.

- **Rejoin** (`econ_forum_ai_guests_rejoin`, before invitations go out): any AI boycotter, minor walkout followers
  included, whose opinion of the host is above -10 rejoins, so it is invited to that summit.
- **Preparation** (`econ_forum_ai_guest_preparation`, after the host prepares): one with opinion below -50, outside
  the host's faction and with over 74 PP boycotts 20% of the time. Otherwise, an invitee with opinion above 25, over 49 PP and treasury over 20 sponsors
  30% of the time, only while the forum has under 15 sponsor points. The WEF's partners already fund 15, so AI
  guests top up lesser forums.
- **Summit** (`econ_forum_convene_summit`): an AI delegation that decides to attend, with over 99 PP, bids for a
  free headline slot 40% of the time, before attendance is recorded. A win counts toward that summit's score and
  pays its keynote with the others.

`econ_forum_open_preparation` increments `econ_forum_cycle`, which resets the once-a-cycle limits.

## Score

- Governments: each attendee adds its share of world power ranking in percent
  (`percentage_of_global_factories × 100`), doubled for a head of government.
  The sum × 0.6 caps at 60.
- Corporate: `prestige × 0.15 + sponsors + 3 per track the forum leads`, capped at
  30. A forum leads a track when its sector prestige beats every other active
  forum's.
- Speakers: `5 per speaker + prestige × 0.1`.
- Counter-programming: +5 when a more prestigious forum met the month before, or
  earlier in the same month's tick.
- Score = the sum, capped at 100. New prestige = `old + (score - old) × 0.3`.

## Rewards and Rivalry

- Every attendee, host included, gets `econ_forum_delegation_modifier` for 365
  days: `receiving_investment_cost_modifier` of `-prestige × 0.0005`, doubled for a
  head of government. The best forum of the year sets the value.
- State-led hosts gain `prestige × 0.02`% influence in each attendee (doubled for a
  head of government), a +10 opinion modifier from each, and
  `econ_forum_host_modifier` for 365 days: `prestige × 0.005` political power gain
  and `prestige × 0.002` foreign influence.
- Each attendee of a state-led forum signs an investment agreement: the host gets
  `econ_forum_deal@<attendee>` for 365 days, which adds 25 to that attendee's AI
  investment score for the host, like a trade agreement.
- Each head of government a counter-programmed summit draws who did not lead a
  delegation to the rival that just met costs the rival 1 prestige, up to 5. If one of
  them is a great or super power, `econ_forum_news.3` fires.
- Once per campaign: `econ_forum_news.5` when a challenger reaches 50 prestige,
  `econ_forum_news.2` when one passes the WEF, and `econ_forum_news.4` when the
  WEF retakes first place, checked after every summit. Before 21 April 2025 the
  WEF news names Klaus Schwab.

## Adding a Forum

1. Append one entry to every registry array in `econ_forum_setup`, raise every
   `size = 9` and `^num < 9` in the effects and triggers (registry, country arrays,
   `econ_forum_open_preparation`, `econ_forum_can_be_invited`), and the `size = 54`
   track arrays by six.
2. Add its core members to `econ_forum_is_core_member` and its identity to
   `econ_forum_track_in_identity`.
3. Add the name key and a branch to each `econ_forum_name_*` scripted loc, a
   `econ_forum_preparation_<id>` key and branch, and a standing line to
   `econ_forum_category_desc`.
4. Add a founding decision calling `econ_forum_found`, or register a startup
   host with `econ_forum_register_host`, and make the founder see
   `econ_forum_category`.

## Known Limits and Next Phases

- A seat owner that already hosts a forum cannot inherit a second one, so that
  forum stands vacant until the seat changes hands or its owner stops hosting.

Next, from #4802: a company roster once #4357 lands, a native runtime test of the
full cycle, and the upstream port below.

## Upstream Port

Not started. The #4802 roadmap gates it on an OEM runtime test of the full cycle.
OEM keeps the whole system; upstream gets it as draft PRs in the order below, each
playable on its own.

**Upstream already has** everything the forums call outside their own files:

- the International Systems screen and its tab scaffolder (#5007);
- `global.PR_regional_or_greater_powers`, `global.nato_members` and `global.EU_member`;
- `SOV_western_sanctions`, `RAJ_BRICS` and `RAJ_BRICS_associate`;
- `change_influence_percentage`, `modify_treasury_effect`, `energy_gain_multiplier`;
- the event picture `GFX_economic_forum_aze`.

**Upstream lacks:**

- the 12 forum files (about 4,700 lines);
- the Forums tab icon `ledger_icon_small_forums.dds`;
- five hooks into shared files:
  - `econ_forum_setup` in the `on_startup` block of `00_on_actions.txt`;
  - `econ_forum_monthly_update` in the global monthly block of `MD_on_actions.txt`;
  - the `econ_forum_deal@PREV` bonus in `AI_country_selection_calculation`
    (`99_AI_investment_scripted_effects.txt`);
  - `clear_array = econ_forum_deal_inserted` and `econ_forum_add_deal_targets` at the end of
    `yearly_investment_targets_routine` (`00_investment_targets_effects.txt`), so the yearly
    target rebuild keeps live agreement hosts;
  - `econ_forum_build_screen` in `00_missiles_scripted_guis.txt`;
- the Forums tab wiring. Run the #5007 scaffolder (`tools/generators/add_international_system.py`)
  instead of copying it: it edits `MD_countrymissilesview.gui` and `.gfx`,
  `00_missiles_scripted_guis.txt` and the title in `01_international_scripted_localisation.txt`,
  and builds `missiles_gui_ledger_btn_narrow.dds` once the tab row overflows. Then drop the forum
  window, scripted GUI and loc into the stubs it writes.

OEM-only and skipped: `clear_variable = var_open_MD_forums_gui` in `01_targeted_operations_view.txt`
belongs to the fork's targeted operations screen, which upstream does not have.

| PR  | Slice                                                                                                          | OEM source                       |
| --- | -------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 1   | Registry, yearly cycle, invitations, AI attendance, score and prestige, host decisions, the startup and monthly hooks | #429                             |
| 2   | Program tracks, scheduling, investment agreements with the AI investment and yearly target hooks, speaker poaching, rivalry news, SPIEF and Boao | #430                             |
| 3   | The four foundable forums, seat succession, AI rescheduling, Russia and BRICS                                  | #431, #443, #449                 |
| 4   | The Forums tab through the scaffolder, delegation agendas, guest actions, invitation requests, AI guests      | #440, #442, #458-#461            |
| 5   | Walkouts and the breakaway forum                                                                               | #463, #464                       |
| 6   | Signing ceremonies, councils, summit messages, the tab tooltip                                                 | #466-#468, #470, #471            |

Port notes:

- Port the final code, not the history: every review fix since #429 is already in it.
- Size the registry to 9 slots from PR 1, so PR 5 adds the breakaway without
  resizing every array.
- Re-check `econ_forum.*` and `econ_forum_news.*` against every open upstream
  branch at port time, and leave a gap.
- Cut explanatory script comments and put the reasons in the PR body; upstream
  review strips them.
- Each PR adds one `Changelog.txt` line under upstream's current version.
