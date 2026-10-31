"""Execute agenda scripts at the payment, delivery and party-credit boundaries."""

import itertools
import re
from pathlib import Path

import pytest
from shared.ai_race_test_support import RaceScript, _named_block, _parse_race_script
from validate_scripted_params import (
    _parse_effect_contracts_from_file,
    _validate_call_sites_in_file,
)
from validate_unused_scripted import extract_definitions

ROOT = Path(__file__).resolve().parents[2]
FACTION_EFFECTS_PATH = ROOT / "common/scripted_effects/00_internal_faction_effects.txt"
FOCUSES = (ROOT / "common/national_focus/05_usa.txt").read_text(encoding="utf-8")
DECISIONS = _parse_race_script(
    (ROOT / "common/decisions/USA_presidential_agenda.txt").read_text(encoding="utf-8")
)["USA_presidential_agenda_category"]
DECISIONS = {key: dict((k, v) for k, _, v in body) for key, _, body in DECISIONS}
IDEAS = _parse_race_script(
    (ROOT / "common/ideas/USA_presidential_agenda_ideas.txt").read_text(
        encoding="utf-8"
    )
)["ideas"]
IDEAS = {key: dict((k, v) for k, _, v in body) for key, _, body in IDEAS[0][2]}

POLICIES = {
    "democrat": (
        "reconnect_rural_america",
        "national_data_privacy_standard",
        "public_compute_commons",
    ),
    "republican": (
        "rebuild_strategic_fuel_reserve",
        "trade_adjustment_fund",
        "secure_critical_supply_chain",
    ),
}


def body(text, name):
    return _parse_race_script(_named_block(text, name))[name]


class AgendaScript(RaceScript):
    """Reuse the race interpreter; stub only existing owner-system effects."""

    def __init__(self, party="democrat", year=2028):
        super().__init__()
        self.effects.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_effects/USA_presidential_agenda_effects.txt"
                ).read_text(encoding="utf-8")
            )
        )
        faction_source = FACTION_EFFECTS_PATH.read_text(encoding="utf-8")
        for name in (
            "autocrats_opinion_change",
            "change_industrial_conglomerates_opinion",
        ):
            self.effects.update(_parse_race_script(_named_block(faction_source, name)))
        for filename in (
            "USA_presidential_agenda_triggers.txt",
            "99_USA_scripted_triggers.txt",
        ):
            self.triggers.update(
                _parse_race_script(
                    (ROOT / "common/scripted_triggers" / filename).read_text(
                        encoding="utf-8"
                    )
                )
            )
        self.party = party
        self.root = 1
        self.country(1, tag="USA")
        self.countries[1]["ideas"] = {"industrial_conglomerates"}
        self.country(2, tag="JAP")
        self.completed = {
            "USA_focus_working_majority",
            f"USA_focus_{year}_{party}_victory",
        }
        self.used = set()
        self.pending = set()
        self.popularity = []
        self.congress_calls = 0
        self.opinion_changes = []
        self.timed = {}
        self.dynamic = {}
        self.owned = {774, 787, 788, 900}
        self.controlled = set(self.owned)
        self.factories = {900}
        self.embargoes = set()
        self.factions = {"JAP"}
        self.wars = set()
        self.vars = self.countries[1]["vars"]
        self.vars.update(
            USA_agenda_majority=2,
            USA_agenda_review_day=0,
            treasury=100,
            political_power=500,
            industrial_conglomerates_opinion=50,
            ruling_party=2 if party == "democrat" else 1,
            senators_support=60,
            representatives_support=260,
            quorum_low=40,
            quorum_medium=50,
            quorum_high=60,
            fuel=100000,
            ai_race_stage=1,
            ai_race_capacity_settled=1,
            ai_race_current_readiness=1,
            ai_race_power_multiplier=1.25,
            energy_balance=5,
        )
        self.vars["resource@microchips"] = 10
        self.countries[1]["flags"]["AI_RACE_state_initialized"] = None

    def condition(self, statements, identifier=1):
        for key, comparison, operand in statements:
            if key == "custom_trigger_tooltip":
                result = self.condition(
                    [x for x in operand if x[0] != "tooltip"], identifier
                )
            elif key == "has_completed_focus":
                result = operand in self.completed
            elif key == "western_autocrats_are_in_power":
                result = operand == "no"
            elif key in {
                "western_liberals_are_in_power",
                "western_conservatism_are_in_power",
            }:
                expected = (
                    "democrat"
                    if key == "western_liberals_are_in_power"
                    else "republican"
                )
                result = (self.party == expected) == (operand == "yes")
            elif key.isdigit():
                result = self.condition(operand, int(key))
            elif key in {"is_owned_by", "is_controlled_by"}:
                result = identifier in (
                    self.owned if key == "is_owned_by" else self.controlled
                )
            elif key == "any_owned_state":
                result = any(self.condition(operand, state) for state in self.owned)
            elif key == "microchip_plant":
                result = self.comparisons[comparison](
                    int(identifier in self.factories), float(operand)
                )
            elif key in {"JAP", "KOR", "TAI"}:
                result = key == "JAP" and bool(self.factories)
            elif key in {"is_embargoed_by", "is_embargoing"}:
                result = operand in self.embargoes
            elif key == "is_in_faction_with":
                result = operand in self.factions
            elif key == "has_war_with":
                result = operand in self.wars
            elif key == "has_fuel":
                result = self.comparisons[comparison](self.vars["fuel"], float(operand))
            else:
                result = super().condition([(key, comparison, operand)], identifier)
            if not result:
                return False
        return True

    def execute(self, statements, identifier=1):
        for key, comparison, operand in self._active_statements(statements, identifier):
            if key == "custom_effect_tooltip":
                continue
            if key in {"if", "else_if", "else"}:
                self.execute(operand, identifier)
            elif key.isdigit():
                self.execute(operand, int(key))
            elif key == "add_timed_idea":
                data = dict((k, v) for k, _, v in operand)
                self.timed[data["idea"]] = self.value(data["days"], 1)
            elif key == "add_dynamic_modifier":
                data = dict((k, v) for k, _, v in operand)
                self.dynamic[(identifier, data["modifier"])] = int(data["days"])
            elif key == "add_fuel":
                self.vars["fuel"] += float(operand)
            elif key == "USA_congress_small_support":
                self.congress_calls += 1
            elif key == "apply_industrial_conglomerates_dynamic_effect_DYNMOD":
                self.opinion_changes.append(self.temps["temp_opinion_change"])
            elif key == "change_relative_party_popularity":
                self.popularity.append(
                    (self.temps["party_index"], self.temps["party_popularity_increase"])
                )
            else:
                super().execute([(key, comparison, operand)], identifier)

    def can_take(self, name):
        decision = DECISIONS[name]
        return (
            "USA_focus_deliver_legislative_agenda" not in self.completed
            and name not in self.used
            and self.condition(decision["visible"])
            and self.condition(decision["available"])
            and self.vars["political_power"] >= float(decision["cost"])
        )

    def take(self, name):
        assert self.can_take(name)
        self.vars["political_power"] -= float(DECISIONS[name]["cost"])
        self.execute(DECISIONS[name]["complete_effect"])
        self.used.add(name)
        if "remove_effect" in DECISIONS[name]:
            self.pending.add(name)

    def finish(self, name):
        assert name in self.pending
        self.pending.remove(name)
        self.execute(DECISIONS[name]["remove_effect"])

    def announce(self, slug):
        self.completed.add("USA_focus_" + slug)


@pytest.mark.parametrize(
    "year,party", tuple(itertools.product((2020, 2024, 2028), POLICIES))
)
def test_shared_opening_accepts_each_election_without_previous_administration(
    year, party
):
    game = AgendaScript(party, year)
    focus = FOCUSES[FOCUSES.index("id = USA_focus_working_majority") :].split(
        "\n\tfocus =", 1
    )[0]
    assert "prerequisite" not in focus
    assert ("USA_agenda_elected_government", "=", "yes") in body(focus, "available")
    assert game.condition(game.triggers["USA_agenda_elected_government"])
    game.party = "republican" if party == "democrat" else "democrat"
    assert not game.condition(game.triggers["USA_agenda_elected_government"])


def test_congress_agreement_costs_and_choices_are_mutually_exclusive():
    game = AgendaScript()
    game.vars.update(
        USA_agenda_majority=0, senators_support=45, representatives_support=200
    )
    assert game.can_take("USA_agenda_majority_1")
    assert not game.can_take("USA_agenda_majority_2")
    game.take("USA_agenda_majority_1")
    assert game.vars["political_power"] == 450
    assert game.congress_calls == 1
    assert not game.can_take("USA_agenda_majority_2")
    assert game.vars["USA_agenda_review_day"] == game.globals["num_days"] + 365


@pytest.mark.parametrize("mode,days", ((1, 365), (2, 730)))
def test_rural_contracts_pay_first_then_deliver_only_local_gradual_growth(mode, days):
    game = AgendaScript()
    game.vars["USA_agenda_majority"] = mode
    game.announce("reconnect_rural_america")
    for state in (774, 787, 788):
        name = f"USA_agenda_broadband_{state}"
        game.take(name)
        assert game.vars[f"USA_agenda_rural_{state}"] == 1
        assert (state, "USA_agenda_rural_broadband") not in game.dynamic
        game.finish(name)
        assert game.dynamic[(state, "USA_agenda_rural_broadband")] == days
        assert not game.can_take(name)
    assert game.vars["treasury"] == 85
    assert not game.timed


def test_lost_rural_state_spends_funding_without_delivery_or_retry():
    game = AgendaScript()
    game.announce("reconnect_rural_america")
    game.take("USA_agenda_broadband_774")
    game.controlled.remove(774)
    game.finish("USA_agenda_broadband_774")
    assert game.vars["treasury"] == 95
    assert game.vars["USA_agenda_rural_774"] == 3
    assert not game.dynamic


@pytest.mark.parametrize("choice", ("refill_reserve", "sell_reserve"))
def test_reserve_choice_cannot_create_a_money_or_fuel_loop(choice):
    game = AgendaScript("republican")
    game.announce("rebuild_strategic_fuel_reserve")
    if choice == "sell_reserve":
        game.vars["fuel"] = 99999
        assert not game.can_take("USA_agenda_sell_reserve")
        game.vars["fuel"] = 100000
    game.take("USA_agenda_" + choice)
    if choice == "refill_reserve":
        assert game.vars["fuel"] == 100000
        game.finish("USA_agenda_refill_reserve")
    assert (game.vars["treasury"], game.vars["fuel"]) == (
        (88, 200000) if choice == "refill_reserve" else (104, 0)
    )
    assert not game.can_take("USA_agenda_refill_reserve")
    assert not game.can_take("USA_agenda_sell_reserve")


@pytest.mark.parametrize(
    "name,cost,party,policy,status",
    (
        ("privacy_enforce", 8, "democrat", "national_data_privacy_standard", "privacy"),
        (
            "privacy_transition",
            3,
            "democrat",
            "national_data_privacy_standard",
            "privacy",
        ),
        ("trade_workers", 15, "republican", "trade_adjustment_fund", "trade"),
        ("trade_exemptions", 25, "republican", "trade_adjustment_fund", "trade"),
        ("compute_access", 30, "democrat", "public_compute_commons", "compute"),
        ("supply_allies", 20, "republican", "secure_critical_supply_chain", "supply"),
        ("supply_domestic", 40, "republican", "secure_critical_supply_chain", "supply"),
    ),
)
def test_projects_require_funding_and_finish_before_credit(
    name, cost, party, policy, status
):
    game = AgendaScript(party)
    game.announce(policy)
    game.vars["treasury"] = cost - 1
    assert not game.can_take("USA_agenda_" + name)
    game.vars["treasury"] = cost
    game.take("USA_agenda_" + name)
    assert game.vars["treasury"] == 0
    assert game.vars["USA_agenda_" + status] == 1
    assert not game.timed
    assert game.condition(DECISIONS["USA_agenda_" + name]["visible"])
    assert not game.can_take("USA_agenda_" + name)
    for other, decision in DECISIONS.items():
        if other != "USA_agenda_" + name and any(
            f"USA_agenda_{status}" in str(value)
            for key, value in decision.items()
            if key == "visible"
        ):
            assert not game.can_take(other)
    assert not game.condition(game.triggers["USA_agenda_no_projects_pending"])
    game.finish("USA_agenda_" + name)
    assert game.vars["USA_agenda_" + status] == 2
    assert len(game.timed) == 1
    assert not game.can_take("USA_agenda_" + name)


@pytest.mark.parametrize(
    "field,value",
    (
        ("ai_race_stage", 0),
        ("ai_race_capacity_settled", 0),
        ("ai_race_current_readiness", 0.5),
        ("energy_balance", 2),
        ("resource@microchips", 4),
    ),
)
def test_compute_capacity_is_required_at_approval_and_delivery(field, value):
    game = AgendaScript()
    game.announce("public_compute_commons")
    good = game.vars[field]
    game.vars[field] = value
    assert not game.can_take("USA_agenda_compute_access")
    game.vars[field] = good
    game.take("USA_agenda_compute_access")
    game.vars[field] = value
    game.finish("USA_agenda_compute_access")
    assert game.vars["USA_agenda_compute"] == 3
    assert game.vars["treasury"] == 70
    assert not game.timed


@pytest.mark.parametrize("mode", ("disabled", "outcomes_only"))
def test_compute_cannot_bypass_the_ai_race_rule(mode):
    game = AgendaScript()
    game.mode = mode
    game.announce("public_compute_commons")
    assert not game.can_take("USA_agenda_compute_access")


def test_compute_requires_power_after_energy_multipliers_and_stops_on_shortage():
    game = AgendaScript()
    game.announce("public_compute_commons")
    game.vars["ai_race_power_multiplier"] = 6
    assert not game.can_take("USA_agenda_compute_access")
    game.vars["ai_race_power_multiplier"] = 1.25
    game.take("USA_agenda_compute_access")
    game.finish("USA_agenda_compute_access")
    game.vars["energy_balance"] = -1
    assert game.condition(IDEAS["USA_agenda_compute_access_idea"]["cancel"])


@pytest.mark.parametrize("faction_present", (True, False))
def test_privacy_reuses_existing_corporate_opposition_effect(faction_present):
    game = AgendaScript()
    if not faction_present:
        game.countries[1]["ideas"].clear()
    game.temps["temp_opinion_change"] = 40
    game.announce("national_data_privacy_standard")
    game.take("USA_agenda_privacy_enforce")
    assert game.vars["industrial_conglomerates_opinion"] == (
        45 if faction_present else 50
    )
    assert game.opinion_changes == ([-5] if faction_present else [])
    assert not game.can_take("USA_agenda_privacy_transition")


@pytest.mark.parametrize(
    "setter,missing", (("temp_opinion", False), ("temp_opinion_change", True))
)
def test_agenda_faction_calls_use_helper_parameter_contract(tmp_path, setter, missing):
    source = (ROOT / "common/decisions/USA_presidential_agenda.txt").read_text(
        encoding="utf-8"
    )
    caller = tmp_path / "agenda.txt"
    with caller.open("w", encoding="utf-8", newline="") as stream:
        stream.write(source.replace("temp_opinion = -5", setter + " = -5"))
    issues = _validate_call_sites_in_file(
        (
            str(caller),
            _parse_effect_contracts_from_file(str(FACTION_EFFECTS_PATH)),
            str(tmp_path),
            frozenset(),
            frozenset(),
            frozenset(
                name
                for path in (ROOT / "common/scripted_effects").glob("*.txt")
                for name, _, _ in extract_definitions((str(path), str(ROOT)))
            ),
        )
    )
    failures = [
        message
        for category, message, _ in issues
        if category == "missing-required-param"
    ]
    assert bool(failures) == missing


def test_allied_embargo_exposure_differs_from_domestic_qualification():
    game = AgendaScript("republican")
    game.announce("secure_critical_supply_chain")
    game.embargoes.add("JAP")
    assert not game.can_take("USA_agenda_supply_allies")
    assert game.can_take("USA_agenda_supply_domestic")
    game.take("USA_agenda_supply_domestic")
    game.finish("USA_agenda_supply_domestic")
    assert not game.condition(IDEAS["USA_agenda_domestic_sourcing"]["cancel"])
    assert game.condition(IDEAS["USA_agenda_allied_sourcing"]["cancel"])


@pytest.mark.parametrize("party", POLICIES)
@pytest.mark.parametrize(
    "promised,delivered", tuple((p, d) for p in range(1, 4) for d in range(p + 1))
)
def test_delivery_credit_is_capped_and_awarded_only_to_governing_party(
    party, promised, delivered
):
    game = AgendaScript(party)
    statuses = (
        ("rural_774", "privacy", "compute")
        if party == "democrat"
        else ("reserve", "trade", "supply")
    )
    for i, (slug, status) in enumerate(zip(POLICIES[party], statuses)):
        if i < promised:
            game.announce(slug)
        if i < delivered:
            game.vars["USA_agenda_" + status] = 2
    game.run("USA_agenda_deliver", 1)
    if delivered:
        expected = 0.02 if delivered >= 2 and delivered == promised else 0.01
        assert game.popularity == [(2 if party == "democrat" else 1, expected)]
        assert game.timed["USA_agenda_delivery_legacy"] == (
            365 if expected == 0.02 else 180
        )
    else:
        assert not game.popularity
        assert game.timed == {"USA_agenda_unfulfilled_promises": 180}
    game.completed.add("USA_focus_deliver_legislative_agenda")
    assert not any(game.can_take(name) for name in DECISIONS)
    assert not game.condition(game.triggers["USA_agenda_delivery_available"])


def test_delivery_waits_for_a_year_and_all_pending_contracts():
    game = AgendaScript()
    game.announce("reconnect_rural_america")
    game.vars["USA_agenda_review_day"] = game.globals["num_days"] + 1
    assert not game.condition(game.triggers["USA_agenda_delivery_available"])
    game.globals["num_days"] += 1
    assert game.condition(game.triggers["USA_agenda_delivery_available"])
    game.take("USA_agenda_broadband_774")
    assert not game.condition(game.triggers["USA_agenda_delivery_available"])


@pytest.mark.parametrize("year", (2020, 2024))
def test_delivery_cannot_close_the_agenda_before_the_2028_endpoints(year):
    game = AgendaScript(year=year)
    game.announce("reconnect_rural_america")
    assert not game.condition(game.triggers["USA_agenda_delivery_available"])


@pytest.mark.parametrize("party", POLICIES)
def test_delivery_never_credits_an_opposing_administrations_projects(party):
    game = AgendaScript(party)
    for slugs in POLICIES.values():
        for slug in slugs:
            game.announce(slug)
    statuses = (
        ("reserve", "trade", "supply")
        if party == "democrat"
        else ("rural_774", "privacy", "compute")
    )
    for status in statuses:
        game.vars["USA_agenda_" + status] = 2
    game.run("USA_agenda_deliver", 1)
    assert not game.popularity
    assert game.timed == {"USA_agenda_unfulfilled_promises": 180}


def test_agenda_has_no_free_buildings_technologies_or_repeatable_rewards():
    files = [
        ROOT / "common/decisions/USA_presidential_agenda.txt",
        ROOT / "common/scripted_effects/USA_presidential_agenda_effects.txt",
    ]
    script = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert not re.search(
        r"\b(add_building_construction|set_technology|add_research_slot|add_ideas)\s*=",
        script,
    )
    assert all(decision["fire_only_once"] == "yes" for decision in DECISIONS.values())
    assert (
        "repeatable = yes"
        not in FOCUSES[FOCUSES.index("id = USA_focus_working_majority") :]
    )
