"""Execute investment source with native event and construction boundaries modeled."""

import copy
import re
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

import pytest
from great_ai_race_state_model_test import (
    RaceScript,
    _extract_block,
    _named_block,
    _parse_race_script,
)

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = ROOT / "common/scripted_effects/99_investment_scripted_effects.txt"
TRIGGERS = ROOT / "common/scripted_triggers/00_investment_scripted_triggers.txt"
EVENTS = ROOT / "events/investments_events.txt"
BUILDING_NAMES = (
    "industrial_complex",
    "arms_factory",
    "dockyard",
    "infrastructure",
    "offices",
    "anti_air_building",
    "radar_station",
    "air_base",
    "fuel_silo",
    "internet_station",
    "renewable_energy_infra",
    "fossil_powerplant",
    "nuclear_reactor",
    "agriculture_district",
)


class InvestmentScript(RaceScript):
    """Keep proposal, quote, response, charge, and cleanup effects under test."""

    def __init__(self, mode="full"):
        super().__init__(mode)
        self.effects.update(_parse_race_script(EFFECTS.read_text(encoding="utf-8")))
        self.triggers.update(_parse_race_script(TRIGGERS.read_text(encoding="utf-8")))
        self.event_definitions = {}
        source = EVENTS.read_text(encoding="utf-8")
        for match in re.finditer(r"(?m)^country_event = \{", source):
            body = _parse_race_script(_extract_block(source, match.start()))[
                "country_event"
            ]
            event_id = next(value for key, _op, value in body if key == "id")
            self.event_definitions[event_id] = body
        self.root = self.sender = self.current = None
        self.previous = []
        self.event_targets = {}
        self.queue, self.popups, self.project_starts, self.influence = [], [], [], []
        self.invoke("init_investment_system", 1, create=True)

    @contextmanager
    def scoped(self, identifier):
        self.previous.append(self.current)
        self.current = int(identifier)
        try:
            yield
        finally:
            self.current = self.previous.pop()

    def identifier(self, name, identifier):
        if name == "THIS":
            return int(identifier)
        if name == "ROOT":
            return self.root
        if name == "FROM":
            return self.sender
        if name == "CONTROLLER":
            return self.countries[identifier]["controller"]
        if re.fullmatch(r"PREV(?:\.PREV)*", name):
            return self.previous[-len(name.split("."))]
        if name.startswith("event_target:"):
            return self.event_targets[name[13:]]
        if name.startswith("var:"):
            return int(self.value(name[4:], identifier))
        raise AssertionError(f"Unsupported scope {name}")

    def qualified(self, name, identifier):
        if name.startswith("event_target:") and "." in name:
            scope, name = name.split(".", 1)
            return self.identifier(scope, identifier), name
        match = re.match(r"^((?:PREV\.)*PREV|ROOT|FROM|THIS)\.(.*)$", name)
        if match:
            return self.identifier(match[1], identifier), match[2]
        return identifier, name

    def _scope(self, name, identifier):
        identifier, name = self.qualified(name, identifier)
        if "^" in name:
            base, index = name.rsplit("^", 1)
            name = f"{base}^{int(self.value(index, identifier))}"
        return super()._scope(name, identifier)

    def value(self, name, identifier):
        if isinstance(name, str):
            identifier, name = self.qualified(name, identifier)
            if name == "id":
                return identifier
            if name == "num_days":
                return self.globals["num_days"]
        return super().value(name, identifier)

    def flag_name(self, name, identifier):
        return re.sub(
            r"@(FROM|ROOT|PREV|THIS)$",
            lambda match: "@" + str(self.identifier(match[1], identifier)),
            name,
        )

    def condition(self, statements, identifier):
        results = []
        matched = False
        for key, op, value in statements:
            if key in {"if", "else_if", "else"}:
                data = {k: v for k, _o, v in value}
                if key == "if":
                    matched = False
                if not matched and (
                    key == "else" or self.condition(data["limit"], identifier)
                ):
                    matched = True
                    results.append(
                        self.condition(
                            [entry for entry in value if entry[0] != "limit"],
                            identifier,
                        )
                    )
                continue
            if key in {
                "ROOT",
                "FROM",
                "PREV",
                "PREV.PREV",
                "CONTROLLER",
            } or key.startswith(("var:", "event_target:")):
                with self.scoped(self.identifier(key, identifier)):
                    result = self.condition(value, self.current)
            elif key in {"set_temp_variable", "subtract_from_temp_variable"}:
                self.execute([(key, op, value)], identifier)
                result = True
            elif key == "country_exists":
                result = self.countries[self.identifier(value, identifier)]["exists"]
            elif key == "has_event_target":
                result = value in self.event_targets
            elif key == "is_controlled_by":
                result = self.countries[identifier]["controller"] == self.identifier(
                    value, identifier
                )
            elif key == "state":
                result = identifier == self.value(value, identifier)
            elif key == "free_building_slots":
                data = {k: v for k, _o, v in value}
                comparison = next(o for k, o, _v in value if k == "size")
                result = self.comparisons[comparison](
                    self.countries[identifier]["slots"].get(data["building"], 0),
                    self.value(data["size"], identifier),
                )
            elif key == "ai_race_ai_expansion_permitted":
                country = self.countries[identifier]
                result = (
                    self.mode == "full"
                    and country["ai"]
                    and country.get("planning", True)
                    and not country.get("war", False)
                ) == (value == "yes")
            elif key == "has_country_flag":
                result = self._flag(
                    self.countries[identifier]["flags"],
                    self.flag_name(value, identifier),
                )
            else:
                result = super().condition([(key, op, value)], identifier)
            results.append(result)
        return all(results)

    def run(self, name, identifier):
        if name == "precompute_state_construction_data":
            assert identifier < 0
            assert self.previous[-1] > 0
            self.temps["test_project_duration"] = self.countries[identifier].get(
                "duration", 100
            )
        elif name == "calculate_project_duration":
            duration = self.temps["test_project_duration"]
            self.countries[identifier]["vars"][
                "project_construction_duration^-2"
            ] = duration
            self.countries[identifier]["vars"][
                f"project_construction_duration^{int(self.value('project', identifier))}"
            ] = duration
        elif name == "get_available_project":
            variables = self.countries[identifier]["vars"]
            variables.pop("new_project", None)
            for index in range(15):
                if not variables.get(f"project_array^{index}", 0):
                    variables["new_project"] = index
                    break
        elif name == "initialize_start_project_decisions":
            self.project_starts.append((identifier, self.value("project", identifier)))
        elif name == "change_influence_percentage":
            self.influence.append((identifier, self.value("tag_index", identifier)))
        elif name == "refresh_investment_gui":
            pass
        else:
            super().run(name, identifier)

    def execute(self, statements, identifier):
        # Base execution retains its branch-chain state when delegated as one block.
        ordinary = []
        for key, op, value in statements:
            if key in {"if", "else_if", "else"}:
                ordinary.append((key, op, value))
                continue
            if ordinary:
                super().execute(ordinary, identifier)
                ordinary = []
            if key in {
                "ROOT",
                "FROM",
                "PREV",
                "PREV.PREV",
                "CONTROLLER",
            } or key.startswith(("var:", "event_target:")):
                with self.scoped(self.identifier(key, identifier)):
                    self.execute(value, self.current)
            elif key == "random_state":
                data = {k: v for k, _o, v in value}
                for candidate in self.countries:
                    if candidate >= 0:
                        continue
                    with self.scoped(candidate):
                        if self.condition(data["limit"], candidate):
                            self.execute(
                                [entry for entry in value if entry[0] != "limit"],
                                candidate,
                            )
                            break
            elif key == "save_event_target_as":
                self.event_targets[value] = identifier
            elif key == "country_event":
                event_id = (
                    value
                    if isinstance(value, str)
                    else next(v for k, _o, v in value if k == "id")
                )
                self.queue.append(
                    (event_id, identifier, self.root, copy.deepcopy(self.event_targets))
                )
            elif key in {"hidden_effect", "effect_tooltip"}:
                self.execute(value, identifier)
            elif key in {"newline", "custom_effect_tooltip"}:
                pass
            elif key == "change_influence_percentage":
                self.run(key, identifier)
            elif key in {"set_country_flag", "clr_country_flag"}:
                if isinstance(value, str):
                    value = self.flag_name(value, identifier)
                else:
                    value = [
                        (k, o, self.flag_name(v, identifier) if k == "flag" else v)
                        for k, o, v in value
                    ]
                super().execute([(key, op, value)], identifier)
            elif (
                key.endswith("variable")
                and isinstance(value, list)
                and value[0][0] == "var"
                and key not in {"clamp_variable", "clamp_temp_variable"}
            ):
                data = {k: v for k, _o, v in value}
                super().execute(
                    [(key, op, [(data["var"], "=", data["value"])])], identifier
                )
            else:
                super().execute([(key, op, value)], identifier)
        if ordinary:
            super().execute(ordinary, identifier)

    def invoke(
        self, name, identifier, *, sender=None, targets=None, temps=None, create=False
    ):
        if create:
            self.country(identifier, ai=True)
        self.root = self.current = identifier
        self.sender = sender
        self.previous = []
        self.event_targets = copy.deepcopy(targets or {})
        self.temps = dict(temps or {})
        self.run(name, identifier)

    def deliver(self):
        while self.queue:
            event_id, recipient, sender, targets = self.queue.pop(0)
            definition = self.event_definitions[event_id]
            self.root = self.current = recipient
            self.sender, self.event_targets, self.previous, self.temps = (
                sender,
                targets,
                [],
                {},
            )
            immediate = next((v for k, _o, v in definition if k == "immediate"), [])
            self.execute(immediate, recipient)
            if any(key == "option" for key, _op, _v in definition):
                self.popups.append(
                    {
                        "id": event_id,
                        "recipient": recipient,
                        "sender": sender,
                        "targets": copy.deepcopy(targets),
                        "day": self.globals["num_days"],
                    }
                )

    def respond(self, popup, option=0):
        self.root = self.current = popup["recipient"]
        self.sender = popup["sender"]
        self.event_targets = copy.deepcopy(popup["targets"])
        self.previous, self.temps = [], {}
        options = [
            v for k, _o, v in self.event_definitions[popup["id"]] if k == "option"
        ]
        self.execute(
            [
                entry
                for entry in options[option]
                if entry[0] not in {"name", "ai_chance", "trigger"}
            ],
            self.current,
        )
        if popup in self.popups:
            self.popups.remove(popup)

    def advance(self, days):
        today = self.today + timedelta(days=days)
        self.goto(today.year, today.month, today.day)
        for popup in list(self.popups):
            definition = self.event_definitions[popup["id"]]
            timeout = int(
                next((v for k, _o, v in definition if k == "timeout_days"), 13)
            )
            if (
                popup["day"] + timeout <= self.globals["num_days"]
                and self.countries[popup["recipient"]]["exists"]
            ):
                self.respond(popup)


def world(*, treasury=100, reserve=50, building=1, modifier=0):
    model = InvestmentScript()
    investor = model.countries[1]
    investor["vars"].update(treasury=treasury, ai_race_ai_savings_target=reserve)
    receiver = model.country(2)
    receiver["vars"]["modifier@receiving_investment_cost_modifier"] = modifier
    state = model.country(-100)
    state.update(
        controller=2, slots={name: 10 for name in BUILDING_NAMES}, duration=100
    )
    chosen = {
        "AI_best_target": -100,
        "AI_best_country": 2,
        "AI_best_type": building,
        "AI_best_score": 200,
    }
    return model, investor["vars"], receiver["vars"], chosen


def propose(model, chosen):
    model.invoke("investment_ai_propose_project", 1, temps=chosen)


def pending(model, identifier=1):
    return model.condition(model.triggers["investment_ai_offer_pending"], identifier)


@pytest.mark.parametrize(
    "treasury, expected", [(61.999, False), (62, True), (62.001, True)]
)
def test_exact_affordability_preserves_reserve_and_allows_equality(treasury, expected):
    model, investor, receiver, chosen = world(treasury=treasury)
    propose(model, chosen)
    assert pending(model) is expected
    assert bool(model.queue) is expected
    assert investor["treasury"] == treasury
    assert "recently_failed_to_invest" not in model.countries[2]["flags"]
    if not expected:
        assert "investments_state_target" not in investor
        assert "investments_nation_target" not in investor
        assert "recently_accepted_an_investment" not in model.countries[2]["flags"]


@pytest.mark.parametrize(
    "treasury, expected", [(50, False), (50.001, True), (5, False)]
)
def test_source_event_early_gate_precedes_scoring(treasury, expected):
    model, _investor, _receiver, _chosen = world(treasury=treasury)
    gate = next(
        v
        for k, _o, v in model.event_definitions["investments_event.500"]
        if k == "trigger"
    )
    model.root = model.current = 1
    assert model.condition(gate, 1) is expected


@pytest.mark.parametrize(
    "mode, ai, war, planning",
    [
        ("off", True, False, True),
        ("outcomes_only", True, False, True),
        ("full", False, False, True),
        ("full", True, True, True),
        ("full", True, False, False),
    ],
)
def test_stale_reserve_is_ignored_when_live_expansion_stops(mode, ai, war, planning):
    model, investor, _receiver, chosen = world(treasury=12, reserve=10000)
    model.mode = mode
    model.countries[1].update(ai=ai, war=war, planning=planning)
    propose(model, chosen)
    assert pending(model)
    assert investor["investment_ai_offer_cost"] == 12


@pytest.mark.parametrize("modifier, expected", [(0, 12), (0.5, 18), (-0.25, 9)])
def test_quote_uses_chosen_state_controller(modifier, expected):
    model, investor, _receiver, chosen = world(modifier=modifier)
    model.countries[1]["vars"]["modifier@receiving_investment_cost_modifier"] = 8
    propose(model, chosen)
    assert investor["investment_ai_offer_cost"] == expected
    assert investor["investment_ai_offer_target"] == 2
    assert investor["investment_ai_offer_state"] == -100


def test_staging_building_slot_check_ignores_active_slot_with_matching_type_number():
    model, investor, _receiver, chosen = world(building=10)
    investor["project_building_type^10"] = 1
    model.countries[-100]["slots"]["industrial_complex"] = 0
    propose(model, chosen)
    assert investor["investment_ai_offer_type"] == 10
    assert investor["investment_ai_offer_cost"] == 4.65


def test_missing_selected_slot_suppresses_proposal_even_if_other_slot_is_free():
    model, investor, _receiver, chosen = world(building=10)
    investor["project_building_type^10"] = 1
    model.countries[-100]["slots"]["internet_station"] = 0
    propose(model, chosen)
    assert not pending(model)
    assert not model.queue
    assert model._flag(model.countries[2]["flags"], "recently_failed_to_invest")


def test_duplicate_proposal_cannot_overwrite_pending_terms():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    before = copy.deepcopy(investor)
    propose(model, {**chosen, "AI_best_type": 5})
    assert investor == before
    assert len(model.queue) == 1


def test_dispatch_and_acceptance_use_frozen_terms_after_staging_changes():
    model, investor, receiver, chosen = world()
    receiver.update(
        pending_offer_total_cost=900, pending_offer_state=-999, pending_offer_type=5
    )
    receiver_before = copy.deepcopy(receiver)
    propose(model, chosen)
    investor.update(
        investments_nation_target=1,
        investments_state_target=-999,
        **{"project_monetary_cost^-1": 900, "project_building_type^-1": 5},
    )
    model.deliver()
    popup = model.popups[0]
    assert popup["recipient"] == 2
    assert receiver == receiver_before
    assert pending(model)
    model.respond(popup)
    assert investor["treasury"] == 88
    assert receiver["treasury"] == pytest.approx(receiver_before["treasury"] - 1.2)
    assert receiver["pending_offer_total_cost"] == 900
    assert investor["project_monetary_cost^0"] == 12
    assert investor["project_array^0"] == -100
    assert not pending(model)
    assert model.project_starts == [(1, 0)]
    model.respond(popup)
    assert investor["treasury"] == 88
    assert len(model.project_starts) == 1


def test_acceptance_preserves_approval_after_cash_or_reserve_changes():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    investor.update(treasury=1, ai_race_ai_savings_target=100000)
    model.respond(model.popups[0])
    assert investor["treasury"] == -11
    assert not pending(model)


def test_two_investors_do_not_overwrite_each_others_terms():
    model, first, receiver, chosen = world()
    second = model.country(3, ai=True)["vars"]
    second.update(treasury=100, ai_race_ai_savings_target=50)
    propose(model, chosen)
    model.invoke(
        "investment_ai_propose_project", 3, temps={**chosen, "AI_best_type": 5}
    )
    model.deliver()
    assert len(model.popups) == 2
    for popup in list(reversed(model.popups)):
        model.respond(popup)
    assert first["treasury"] == 88
    assert second["treasury"] == 80
    assert receiver["treasury"] == pytest.approx(99996.8)
    assert not pending(model, 1) and not pending(model, 3)


def test_refusal_releases_immediately_without_waiting_for_notification():
    model, investor, receiver, chosen = world()
    receiver["pending_offer_total_cost"] = 900
    propose(model, chosen)
    model.deliver()
    popup = model.popups[0]
    model.respond(popup, option=1)
    assert not pending(model)
    assert investor["treasury"] == 100
    assert receiver["pending_offer_total_cost"] == 900
    assert model.queue[0][0] == "investments_event.11"
    assert not model.charges and not model.influence
    count = len(model.queue)
    model.respond(popup, option=1)
    assert len(model.queue) == count


def test_auto_accept_route_clears_record_without_leaving_pulse_lock():
    model, investor, _receiver, chosen = world()
    model.countries[2]["flags"]["int_auto_accept_investment_flag"] = None
    propose(model, chosen)
    model.deliver()
    assert not pending(model)
    assert "investments_ai_pending" not in model.countries[1]["flags"]
    assert investor["treasury"] == 88
    assert not model.popups


def test_native_timeout_accepts_after_thirteen_days_and_survives_reload():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    model.advance(7)
    assert pending(model)
    assert not model._flag(model.countries[1]["flags"], "investments_ai_pending")
    reloaded = copy.deepcopy(model)
    reloaded.advance(5)
    assert pending(reloaded)
    reloaded.advance(1)
    assert not pending(reloaded)
    assert reloaded.countries[1]["vars"]["treasury"] == 88
    reloaded.advance(30)
    assert len(reloaded.project_starts) == 1
    assert investor["treasury"] == 100


def test_orphan_cleanup_waits_for_popup_deadline_and_blocks_late_charge():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    popup = copy.deepcopy(model.popups[0])
    model.countries[2]["exists"] = False
    model.advance(14)
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert pending(model)
    model.advance(1)
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert not pending(model)
    model.countries[2]["exists"] = True
    model.respond(popup)
    assert investor["treasury"] == 100
    assert not model.charges and not model.project_starts


def test_live_recipient_is_never_released_by_orphan_timer():
    model, _investor, _receiver, chosen = world()
    propose(model, chosen)
    model.globals["num_days"] += 20
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert pending(model)


def test_annexation_and_release_between_weekly_passes_retires_lost_dialog():
    model, investor, receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    popup = copy.deepcopy(model.popups[0])
    model.advance(7)
    model.invoke("investment_ai_record_recipient_annexation", 2)
    assert receiver["investment_ai_annex_generation"] == 1
    # The recipient exists again before the next weekly cleanup observes it.
    model.popups.clear()
    model.advance(7)
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert pending(model)
    reloaded = copy.deepcopy(model)
    reloaded.advance(1)
    reloaded.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert not pending(reloaded)
    reloaded.respond(popup)
    assert reloaded.countries[1]["vars"]["treasury"] == 100
    assert not reloaded.project_starts and not reloaded.charges
    assert investor["investment_ai_offer_target_generation"] == 0


def test_native_annex_hook_records_recipient_history_without_scanning_investors():
    source = (ROOT / "common/on_actions/MD_on_actions.txt").read_text(encoding="utf-8")
    annex = _parse_race_script(_named_block(source, "on_annex"))["on_annex"]
    effects = next(value for key, _op, value in annex if key == "effect")
    hook = next(
        entry
        for entry in effects
        if entry[0] == "FROM"
        and ("investment_ai_record_recipient_annexation", "=", "yes") in entry[2]
    )
    model, investor, recipient, _chosen = world()
    model.root = model.current = 1
    model.sender = 2
    model.execute([hook], 1)
    assert recipient["investment_ai_annex_generation"] == 1
    assert "investment_ai_annex_generation" not in investor
    assert not model.queue and not model.charges


def test_new_offer_to_previously_annexed_recipient_uses_current_generation():
    model, investor, _receiver, chosen = world()
    model.invoke("investment_ai_record_recipient_annexation", 2)
    propose(model, chosen)
    assert investor["investment_ai_offer_target_generation"] == 1
    model.globals["num_days"] += 20
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert pending(model)


def test_returned_recipient_can_honor_existing_offer_before_orphan_deadline():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    model.invoke("investment_ai_record_recipient_annexation", 2)
    model.advance(12)
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert pending(model)
    model.respond(model.popups[0])
    assert investor["treasury"] == 88
    assert not pending(model)


def test_target_removed_before_delivery_does_not_dispatch_to_stale_country():
    model, _investor, _receiver, chosen = world()
    propose(model, chosen)
    model.countries[2]["exists"] = False
    model.deliver()
    assert not model.popups
    model.advance(15)
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    assert not pending(model)


def test_changed_controller_resolves_without_charging_or_building_elsewhere():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    model.countries[-100]["controller"] = 1
    model.respond(model.popups[0])
    assert not pending(model)
    assert investor["treasury"] == 100
    assert not model.project_starts and not model.charges


def test_unrelated_response_does_not_release_or_charge_pending_investor():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    popup = copy.deepcopy(model.popups[0])
    model.country(3)
    popup["recipient"] = 3
    model.respond(popup)
    assert pending(model)
    assert investor["treasury"] == 100
    assert not model.charges


def test_full_project_slots_do_not_charge_recipient_or_award_influence():
    model, investor, receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    investor.update({f"project_array^{index}": -100 for index in range(15)})
    model.respond(model.popups[0])
    assert investor["treasury"] == 100
    assert receiver["treasury"] == 100000
    assert not pending(model)
    assert not model.charges and not model.influence


def test_untracked_scripted_offer_keeps_original_cost_and_receiver_snapshot_path():
    model, investor, receiver, _chosen = world(treasury=10, reserve=10000)
    investor.update(
        investments_state_target=-100,
        project_monetary_cost_effect=-12,
        **{
            "project_monetary_cost^-1": 12,
            "project_building_type^-1": 1,
            "project_build_amount^-1": 1,
            "project_construction_duration^-1": 100,
        },
    )
    model.queue.append(("investments_event.10", 2, 1, {}))
    model.deliver()
    assert receiver["pending_offer_total_cost"] == 12
    model.respond(model.popups[0])
    assert investor["treasury"] == -2
    assert receiver["treasury"] == pytest.approx(99998.8)
    assert "pending_offer_total_cost" not in receiver


def test_tracked_description_and_building_name_use_frozen_sender_only():
    model, _investor, _receiver, _chosen = world()
    descriptions = [
        v for k, _o, v in model.event_definitions["investments_event.10"] if k == "desc"
    ]
    assert any(
        ("text", "=", "ai_race_investment_offer_desc") in desc for desc in descriptions
    )
    helper = (
        ROOT
        / "common/scripted_localisation/02_great_ai_race_investment_localisation.txt"
    ).read_text(encoding="utf-8")
    assert "pending_offer_" not in helper
    for index, building in enumerate(BUILDING_NAMES, 1):
        assert f"FROM.investment_ai_offer_type = {index}" in helper
        assert f"localization_key = {building}" in helper


@pytest.mark.parametrize("option", (0, 1))
@pytest.mark.parametrize("reload", (False, True))
def test_retired_popup_cannot_resolve_new_offer_to_same_recipient_and_state(
    option, reload
):
    model, _investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    old_popup = copy.deepcopy(model.popups[0])
    model.invoke("investment_ai_record_recipient_annexation", 2)
    model.countries[2]["exists"] = False
    model.advance(15)
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    model.countries[2]["exists"] = True
    propose(model, chosen)
    model.deliver()
    new_popup = copy.deepcopy(model.popups[-1])
    if reload:
        model = copy.deepcopy(model)
    before = copy.deepcopy((model.countries, model.queue))
    model.respond(old_popup, option=option)
    assert (model.countries, model.queue) == before
    assert pending(model)
    assert not model.charges and not model.project_starts and not model.influence
    model.respond(new_popup)
    assert not pending(model)
    assert model.countries[1]["vars"]["treasury"] == 88
    assert model.project_starts == [(1, 0)]


def test_retired_dispatch_cannot_deliver_new_offer_a_second_time():
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.invoke("investment_ai_record_recipient_annexation", 2)
    model.globals["num_days"] += 15
    model.invoke("investment_ai_cleanup_orphaned_offer", 1)
    propose(model, chosen)
    model.deliver()
    assert len(model.popups) == 1
    assert investor["investment_ai_offer_generation"] == 2
    model.respond(model.popups[0])
    assert investor["treasury"] == 88
    assert model.project_starts == [(1, 0)]


@pytest.mark.parametrize("bit", (0, 10, 20))
def test_missing_saved_generation_bit_cannot_charge_or_release_offer(bit):
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    popup = model.popups[0]
    popup["targets"].pop(f"investment_ai_offer_bit_{bit}")
    model.respond(popup)
    assert pending(model)
    assert investor["treasury"] == 100
    assert not model.charges and not model.project_starts


@pytest.mark.parametrize("generation", [2**bit for bit in range(21)] + [2097151])
def test_saved_generation_bits_accept_at_each_integer_boundary(generation):
    model, investor, _receiver, chosen = world()
    investor["investment_ai_offer_generation"] = generation - 1
    propose(model, chosen)
    model.deliver()
    reloaded = copy.deepcopy(model)
    reloaded.respond(reloaded.popups[0])
    assert reloaded.countries[1]["vars"]["investment_ai_offer_generation"] == generation
    assert reloaded.countries[1]["vars"]["treasury"] == 88
    assert not pending(reloaded)


def test_exhausted_generation_defers_without_wrap_spending_or_failure_penalties():
    model, investor, _receiver, chosen = world()
    investor["investment_ai_offer_generation"] = 2097151
    before = copy.deepcopy(model.countries)
    propose(model, chosen)
    assert model.countries == before
    assert not pending(model)
    assert not model.queue and not model.charges


@pytest.mark.parametrize("legacy", (False, True))
def test_refusal_notification_cannot_clear_new_offer_lock(legacy):
    model, investor, _receiver, chosen = world()
    propose(model, chosen)
    model.deliver()
    model.respond(model.popups[0], option=1)
    propose(model, chosen)
    model.deliver()
    notification = next(
        popup for popup in model.popups if popup["id"] == "investments_event.11"
    )
    if legacy:
        notification["targets"] = {}
    before = copy.deepcopy(model.countries)
    model.respond(notification)
    assert model.countries == before
    assert pending(model)
    assert model._flag(model.countries[1]["flags"], "investments_ai_pending")
    assert investor["investment_ai_offer_generation"] == 2


def test_self_investment_cannot_create_ambiguous_scope_identity():
    model, investor, _receiver, chosen = world()
    model.countries[-100]["controller"] = 1
    propose(model, {**chosen, "AI_best_country": 1})
    assert not pending(model)
    assert investor.get("investment_ai_offer_generation", 0) == 0
    assert not model.queue and not model.charges
