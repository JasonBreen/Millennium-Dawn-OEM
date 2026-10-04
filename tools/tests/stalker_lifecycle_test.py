from collections import Counter
from pathlib import Path

import pytest
from great_ai_race_state_model_test import _parse_race_script
from targeted_operations_core_test import TargetScript

ROOT = Path(__file__).resolve().parents[2]


def _event(event_id, filename):
    blocks = _parse_race_script(
        "source = {" + (ROOT / filename).read_text(encoding="utf-8") + "}"
    )["source"]
    return next(
        body
        for kind, _, body in blocks
        if kind == "country_event" and ("id", "=", event_id) in body
    )


def _option(event_id, name, filename):
    return next(
        body
        for key, _, body in _event(event_id, filename)
        if key == "option" and ("name", "=", name) in body
    )


class StalkerScript(TargetScript):
    """Execute story effects with the shared scope and timed-flag interpreter."""

    def __init__(self):
        super().__init__()
        for filename in (
            "99_STALKER_world_effects.txt",
            "99_STALKER_strelok_effects.txt",
            "99_STALKER_intel_effects.txt",
            "99_STALKER_faction_wars_effects.txt",
            "99_FBC_europe_effects.txt",
        ):
            self.effects.update(
                _parse_race_script(
                    (ROOT / "common/scripted_effects" / filename).read_text(
                        encoding="utf-8"
                    )
                )
            )
        self.triggers.update(
            {
                name: [("always", "=", "yes")]
                for name in (
                    "STALKER_scenario_enabled",
                    "FBC_scenario_enabled",
                    "STALKER_is_active_zone_anchor",
                )
            }
        )
        self.stubs.update(
            {
                "STALKER_target_zone",
                "STALKER_refresh_zone_administration",
                "small_expenditure",
            }
        )
        self.external = Counter()
        self.actor = 1
        for identifier, tag in enumerate(
            ("ENG", "FRA", "SOV", "IND", "BEL", "GER"), 900
        ):
            if self.tag(tag) is None:
                self.country(identifier, tag=tag)
            identifier = self.tag(tag)
            self.countries[identifier].update(states=[], ideas={"EU_member"})
        self.countries[self.tag("CHI")]["ideas"] = {"EU_member"}
        self.countries[698]["vars"]["STALKER_zone_id"] = 1
        self.countries[698]["controller"] = 2
        self.globals["p5_sc_members"] = [
            self.tag(tag) for tag in ("USA", "ENG", "FRA", "SOV", "CHI", "IND")
        ]
        self.goto(2012, 1)

    def value(self, name, identifier):
        if name == "ROOT":
            return self.actor
        if name == "event_target:STALKER_zone_event_target":
            return 698
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        key, _, operand = statement
        if key.isdigit():
            return self.scoped(operand, identifier, int(key), condition=True)
        if key == "event_target:STALKER_zone_event_target":
            return self.scoped(operand, identifier, 698, condition=True)
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "every_country":
            limits = next(body for name, _, body in operand if name == "limit")
            body = [entry for entry in operand if entry[0] != "limit"]
            for country, data in self.countries.items():
                if "controller" not in data and data["exists"]:
                    if self.scoped(limits, identifier, country, condition=True):
                        self.scoped(body, identifier, country)
        elif key in {"ROOT", "event_target:STALKER_zone_event_target"}:
            self.scoped(operand, identifier, self.value(key, identifier))
        elif key == "FROM":
            self.scoped(operand, identifier, 698)
        elif key == "set_temp_variable_to_random":
            fields = {name: value for name, _, value in operand}
            self.temps[fields["var"]] = float(fields["max"])
        elif key.isdigit():
            self.scoped(operand, identifier, int(key))
        else:
            super().execute_statement(statement, identifier)

    def hidden_option(self, event_id, name, filename):
        self.execute(
            next(
                body
                for key, _, body in _option(event_id, name, filename)
                if key == "hidden_effect"
            ),
            self.actor,
        )


@pytest.mark.parametrize("permanent_controller", [False, True])
def test_council_queues_the_live_permanent_roster_once(permanent_controller):
    script = StalkerScript()
    zone_controller = script.tag("IND") if permanent_controller else 2
    script.countries[698]["controller"] = zone_controller
    script.run("STALKER_schedule_security_council", 1)
    recipients = [country for country, event in script.events if event == "STALKER.137"]
    expected = set(script.globals["p5_sc_members"]) | {zone_controller}
    assert set(recipients) == expected
    assert len(recipients) == len(expected)
    assert script.globals["STALKER_unsc_expected"] == len(expected)
    script.run("STALKER_schedule_security_council", 1)
    assert len(script.events) == len(expected)


def test_council_keeps_the_assigned_zone_seat_when_control_changes():
    script = StalkerScript()
    script.run("STALKER_schedule_security_council", 1)
    script.countries[698]["controller"] = 3
    script.run("STALKER_refresh_unsc_expected", 1)
    assert script.globals["STALKER_unsc_expected"] == 7
    for member in script.globals["p5_sc_members"]:
        script.countries[member]["flags"]["STALKER_unsc_voted"] = None
    script.globals["STALKER_unsc_ballots"] = 6
    script.run("STALKER_finish_security_council", 1)
    assert "STALKER_unsc_resolved" not in script.global_flags
    script.countries[2]["flags"]["STALKER_unsc_voted"] = None
    script.globals["STALKER_unsc_ballots"] = 7
    script.run("STALKER_finish_security_council", 1)
    assert "STALKER_unsc_resolved" in script.global_flags


@pytest.mark.parametrize("voted,expected", [(False, 6), (True, 7)])
def test_annexed_seats_drop_only_uncast_ballots(voted, expected):
    script = StalkerScript()
    script.run("STALKER_schedule_security_council", 1)
    member = script.tag("IND")
    script.countries[member]["exists"] = False
    if voted:
        script.countries[member]["flags"]["STALKER_unsc_voted"] = None
        script.globals["STALKER_unsc_ballots"] = 1
    script.run("STALKER_refresh_unsc_expected", 1)
    assert script.globals["STALKER_unsc_expected"] == expected


@pytest.mark.parametrize("phase,tag,option", [(5, "BEL", "b"), (6, "GER", "c")])
def test_delegated_customs_records_and_recovers_an_annexed_handler(phase, tag, option):
    script = StalkerScript()
    script.countries[1]["ideas"] = {"EU_member"}
    script.globals.update(FBC_eu_phase=0, FBC_eu_capacity=1, FBC_eu_committed=0)
    script.global_flags["FBC_eu_dispatched"] = None
    script.hidden_option("FBC.10", f"FBC.10.{option}", "events/FBC_europe.txt")
    handler = script.tag(tag)
    assert script.globals["FBC_eu_phase"] == phase
    assert script.globals["FBC_eu_recipient"] == handler
    script.run("FBC_monthly_europe_pulse", 1)
    assert script.globals["FBC_eu_phase"] == phase
    script.countries[handler]["exists"] = False
    script.run("FBC_monthly_europe_pulse", 1)
    assert script.globals["FBC_eu_phase"] == 0
    assert script.globals["FBC_eu_recipient"] == script.tag("FRA")
    assert script.globals["FBC_eu_capacity"] == 1
    assert (script.tag("FRA"), "FBC.10") in script.events


@pytest.mark.parametrize("coordinator", ["commission", "FRA", "GER", "BEL"])
def test_initial_customs_dispatch_retries_only_after_the_recipient_disappears(
    coordinator,
):
    script = StalkerScript()
    script.globals["FBC_eu_phase"] = 0
    if coordinator == "commission":
        recipient = script.actor
        script.countries[recipient]["ideas"] = {"EU_member"}
        script.global_flags["EU_commission_taken_flag"] = None
        script.globals["eu_commission"] = recipient
    else:
        recipient = script.tag(coordinator)
        for tag in ("FRA", "GER", "BEL"):
            if tag == coordinator:
                break
            script.countries[script.tag(tag)]["exists"] = False
    script.run("FBC_schedule_eu_customs", script.actor)
    assert script.events == [(recipient, "FBC.10")]
    assert script.globals["FBC_eu_recipient"] == recipient
    script.run("FBC_monthly_europe_pulse", script.actor)
    assert len(script.events) == 1
    script.countries[recipient]["exists"] = False
    fallback = script.tag("IND")
    script.global_flags["EU_commission_taken_flag"] = None
    script.globals["eu_commission"] = fallback
    script.run("FBC_monthly_europe_pulse", script.actor)
    assert script.events[-1] == (fallback, "FBC.10")
    assert script.globals["FBC_eu_recipient"] == fallback
    assert len(script.events) == 2


@pytest.mark.parametrize("option", ["a", "b", "c"])
@pytest.mark.parametrize("invalid", ["controller", "zone_id", "inactive", "resolved"])
def test_stale_raid_options_cannot_choose_a_route_or_charge_the_former_controller(
    option, invalid
):
    script = StalkerScript()
    script.actor = 2
    script.countries[2]["vars"]["political_power"] = 100
    body = _option("STALKER.161", f"STALKER.161.{option}", "events/STALKER_strelok.txt")
    trigger = next(value for key, _, value in body if key == "trigger")
    assert script.condition(trigger, script.actor)
    if invalid == "controller":
        script.countries[698]["controller"] = 3
    elif invalid == "zone_id":
        script.countries[698]["vars"]["STALKER_zone_id"] = 2
    elif invalid == "inactive":
        script.triggers["STALKER_is_active_zone_anchor"] = [("always", "=", "no")]
    else:
        script.global_flags["STALKER_2012_resolved"] = None
    assert not script.condition(trigger, script.actor)
    before = script.countries[698]["vars"].copy()
    script.hidden_option(
        "STALKER.161", f"STALKER.161.{option}", "events/STALKER_strelok.txt"
    )
    assert "STALKER_2012_route" not in script.globals
    assert script.countries[2]["vars"]["political_power"] == 100
    assert script.countries[698]["vars"] == before


@pytest.mark.parametrize("mercenaries,intel,leader", [(39, 100, 11), (41, 0, 6)])
def test_intel_drift_refreshes_the_leader_when_mercenaries_gain_or_lose_the_lead(
    mercenaries, intel, leader
):
    script = StalkerScript()
    script.globals["STALKER_active_zone_anchors"] = [698]
    variables = script.countries[698]["vars"]
    script.run("STALKER_initialize_zone_society", 698)
    variables.update(
        STALKER_zone_military=40,
        STALKER_zone_mercenaries=mercenaries,
        STALKER_zone_foreign_intel=intel,
        STALKER_zone_exploitation=0,
    )
    script.countries[698]["flags"].update(
        STALKER_mercenary_cooldown=None, STALKER_foreign_agents_cooldown=None
    )
    script.run("STALKER_update_zone_leader", 698)
    assert variables["STALKER_zone_leader"] != leader
    script.run("STALKER_monthly_intel_pulse", 1)
    assert variables["STALKER_zone_leader"] == leader


@pytest.mark.parametrize(
    "case,event_id,option,active_phases,integrity_gain",
    [
        ("floor", "FBC.2", "c", {1, 2}, 5),
        ("wing", "FBC.5", "a", {2, 3}, 4),
    ],
)
@pytest.mark.parametrize("phase", range(7))
def test_archive_reports_require_an_active_phase_and_reward_only_once(
    case, event_id, option, active_phases, integrity_gain, phase
):
    script = StalkerScript()
    script.country(1182, tag="---")
    script.countries[1182]["controller"] = script.actor
    variables = script.countries[script.actor]["vars"]
    variables.update(FBC_floor_knowledge=0, FBC_wing_knowledge=0)
    variables.update(
        {
            f"FBC_{case}_phase": phase,
            f"FBC_{case}_knowledge": 20,
            f"FBC_{case}_committed": 1,
            "FBC_response_capacity": 1,
            "FBC_containment_integrity": 50,
            "FBC_exposure": 10,
        }
    )
    body = _option(event_id, f"{event_id}.{option}", "events/FBC.txt")
    trigger = next(value for key, _, value in body if key == "trigger")
    assert script.condition(trigger, script.actor) == (phase in active_phases)
    script.hidden_option(event_id, f"{event_id}.{option}", "events/FBC.txt")
    assert variables[f"FBC_{case}_phase"] == (4 if phase in active_phases else phase)
    assert variables["FBC_containment_integrity"] == 50 + (
        integrity_gain if phase in active_phases else 0
    )
    before = variables.copy()
    script.hidden_option(event_id, f"{event_id}.{option}", "events/FBC.txt")
    assert variables == before


@pytest.mark.parametrize("phase", range(7))
@pytest.mark.parametrize("knowledge", [0, 20])
@pytest.mark.parametrize("controlled", [False, True])
def test_floor_after_action_report_revalidates_phase_and_control(
    phase, knowledge, controlled
):
    script = StalkerScript()
    script.country(769, tag="---")
    script.countries[769]["controller"] = script.actor if controlled else 2
    variables = script.countries[script.actor]["vars"]
    variables.update(
        FBC_floor_phase=phase,
        FBC_floor_knowledge=knowledge,
        FBC_wing_knowledge=0,
        FBC_floor_committed=1,
        FBC_response_capacity=1,
        FBC_containment_integrity=50,
        FBC_exposure=10,
    )
    option = "a" if controlled else "b"
    body = _option("FBC.3", f"FBC.3.{option}", "events/FBC.txt")
    trigger = next(value for key, _, value in body if key == "trigger")
    active = phase in {2, 3}
    assert script.condition(trigger, script.actor) == active
    before = variables.copy()
    script.hidden_option("FBC.3", f"FBC.3.{option}", "events/FBC.txt")
    if active:
        success = phase == 3 or knowledge > 14
        assert variables["FBC_floor_phase"] == (
            (4 if success else 5) if controlled else 6
        )
        assert variables["FBC_containment_integrity"] == 50 + (
            (5 if success else -8) if controlled else 0
        )
        assert variables["FBC_exposure"] == 10 + (
            (-4 if success else 6) if controlled else 0
        )
        assert variables["FBC_floor_committed"] == 0
    else:
        assert variables == before
    before = variables.copy()
    script.hidden_option("FBC.3", f"FBC.3.{option}", "events/FBC.txt")
    assert variables == before


def test_lost_2012_carrier_reaches_the_new_controller_once_after_the_due_date():
    script = StalkerScript()
    script.global_flags["STALKER_2012_dispatched"] = None
    script.countries[2]["exists"] = False
    script.countries[698]["controller"] = 3
    script.goto(2012, 3)
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert not script.events
    script.goto(2012, 4)
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert script.events == [(3, "STALKER.161")]
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert len(script.events) == 1
    script.countries[698]["controller"] = 4
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert script.events[-1] == (4, "STALKER.161")
    script.global_flags["STALKER_2012_resolved"] = None
    script.countries[698]["controller"] = 5
    script.run("STALKER_monthly_strelok_pulse", 1)
    assert len(script.events) == 2


@pytest.mark.parametrize("zone_id", [1, 2, 27])
@pytest.mark.parametrize(
    "event_id,option,filename",
    [
        ("STALKER.27", "a", "events/STALKER_international.txt"),
        ("STALKER.27", "b", "events/STALKER_international.txt"),
        ("STALKER.46", "a", "events/STALKER_regional.txt"),
        ("STALKER.47", "b", "events/STALKER_regional.txt"),
    ],
)
def test_generic_zone_options_cannot_populate_original_only_factions(
    zone_id, event_id, option, filename
):
    script = StalkerScript()
    script.actor = 2
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_initialize_zone_society", 698)
    for field in ("activity", "containment", "exploitation", "mutants"):
        variables[f"STALKER_zone_{field}"] = 50
    before = variables.copy()
    script.hidden_option(event_id, f"{event_id}.{option}", filename)
    assert variables["STALKER_zone_duty"] == (
        before["STALKER_zone_duty"]
        + (
            10
            if event_id == "STALKER.27" and option == "a"
            else 5 if event_id == "STALKER.46" else 0
        )
        if zone_id == 1
        else 0
    )
    assert variables["STALKER_zone_freedom"] == (
        before["STALKER_zone_freedom"]
        + (
            10
            if event_id == "STALKER.27" and option == "b"
            else 5 if event_id == "STALKER.47" else 0
        )
        if zone_id == 1
        else 0
    )
    assert variables != before


@pytest.mark.parametrize("zone_id", [1, 2, 27])
def test_trader_rewards_keep_freedom_in_the_original_zone(zone_id):
    script = StalkerScript()
    script.actor = 2
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_initialize_zone_society", 698)
    variables.update(STALKER_zone_containment=50, STALKER_zone_exploitation=50)
    category = _parse_race_script(
        (ROOT / "common/decisions/STALKER_decisions.txt").read_text(encoding="utf-8")
    )
    decision = next(
        body
        for decisions in category.values()
        for key, _, body in decisions
        if key == "STALKER_license_cordon_trader"
    )
    complete = next(body for key, _, body in decision if key == "complete_effect")
    hidden = next(body for key, _, body in complete if key == "hidden_effect")
    script.execute(hidden, 2)
    assert variables["STALKER_zone_freedom"] == (25 if zone_id == 1 else 0)
    assert variables["STALKER_zone_stalkers"] == 30
    assert variables["STALKER_zone_exploitation"] == 60


@pytest.mark.parametrize("zone_id", [1, 2, 27])
@pytest.mark.parametrize("backed", [2, 3])
def test_tearling_gathering_cannot_make_absent_factions_win(zone_id, backed):
    script = StalkerScript()
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_initialize_zone_society", 698)
    script.run("STALKER_start_tearling_drive", 698)
    variables["STALKER_zone_tearling_backed"] = backed
    script.run("STALKER_gather_tearlings", 698)
    duty = (15 if backed == 2 else 10) if zone_id == 1 else 0
    freedom = (15 if backed == 3 else 10) if zone_id == 1 else 0
    assert variables["STALKER_zone_tearlings_duty"] == duty
    assert variables["STALKER_zone_tearlings_freedom"] == freedom
    assert variables["STALKER_zone_tearlings_stalkers"] == 10


@pytest.mark.parametrize("zone_id", [1, 2, 27])
@pytest.mark.parametrize("option,backed", [("b", 2), ("c", 3)])
def test_absent_factions_cannot_accept_paid_tearling_backing(zone_id, option, backed):
    script = StalkerScript()
    script.actor = 2
    script.countries[2]["vars"]["political_power"] = 50
    variables = script.countries[698]["vars"]
    variables["STALKER_zone_id"] = zone_id
    script.run("STALKER_start_tearling_drive", 698)
    body = _option(
        "STALKER.150", f"STALKER.150.{option}", "events/STALKER_faction_wars.txt"
    )
    trigger = next(value for key, _, value in body if key == "trigger")
    assert script.condition(trigger, 2) == (zone_id == 1)
    script.hidden_option(
        "STALKER.150", f"STALKER.150.{option}", "events/STALKER_faction_wars.txt"
    )
    assert variables["STALKER_zone_tearling_backed"] == (backed if zone_id == 1 else 0)
    assert script.countries[2]["vars"]["political_power"] == (
        25 if zone_id == 1 else 50
    )
