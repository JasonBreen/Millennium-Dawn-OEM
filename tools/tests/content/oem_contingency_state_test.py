"""Execute the contingency scripts with engine effects stubbed at their boundaries.

These tests cover script state transitions, not HOI4 scope dispatch or multiplayer.
"""

import json
import operator
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def parse(text):
    raw = re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}=<>]|[^\s{}=<>]+', text)
    tokens = iter(token for token in raw if not token.startswith("#"))
    result = []
    frames = [result]
    for key in tokens:
        if key == "}":
            assert len(frames) > 1
            frames.pop()
            continue
        comparison, value = next(tokens), next(tokens)
        assert comparison in ("=", "<", ">")
        if value == "{":
            child = []
            frames[-1].append((key, comparison, child))
            frames.append(child)
        else:
            frames[-1].append((key, comparison, value))
    assert len(frames) == 1
    return result


def fields(block):
    return {key: value for key, _, value in block}


class Script:
    """Small, fail-closed executor for the syntax used by this feature."""

    compare = {"=": operator.eq, ">": operator.gt, "<": operator.lt}

    def __init__(self, nuclear="balanced", dms="balanced"):
        self.rules = {
            "rule_oem_nuclear_collapse": nuclear,
            "rule_oem_dead_man_switch": dms,
        }
        self.effects = {}
        for name in (
            "04_oem_contingency_effects",
            "04_oem_nuclear_collapse_effects",
            "04_oem_successor_crisis_effects",
        ):
            self.effects.update(self.load(f"common/scripted_effects/{name}.txt"))
        self.triggers = self.load(
            "common/scripted_triggers/04_oem_contingency_triggers.txt"
        )
        self.triggers["is_able_to_use_nuclear_strikes"] = self.load(
            "common/scripted_triggers/01_raids_triggers.txt"
        )["is_able_to_use_nuclear_strikes"]
        self.decisions = fields(
            self.load("common/decisions/oem_contingency_decisions.txt")[
                "oem_contingencies"
            ]
        )
        self.globals, self.countries, self.temps = {}, {}, {}
        self.events, self.history, self.stack = [], [], []
        self.day = 0
        self.sender = None
        self.dlc = True

    @staticmethod
    def load(path):
        return fields(parse((ROOT / path).read_text(encoding="utf-8-sig")))

    def country(self, name, **values):
        data = {
            "vars": {},
            "flags": {},
            "ideas": [],
            "techs": [],
            "equipment": {"nuclear_missile_equipment": 5},
            "exists": True,
            "is_faction_leader": False,
            "is_subject": False,
            "has_capitulated": False,
            "num_of_factories": 50,
            "num_of_controlled_states": 5,
            "political_power": 500,
            "stability": 0.6,
            "continent": "europe",
            "wars": [],
            "wargoals": [],
            "pacts": [],
            "faction": None,
            "overlord": None,
            "bonuses": [],
        }
        data.update(values)
        self.countries[name] = data
        return data

    @property
    def current(self):
        return self.stack[-1]

    def target(self, name):
        if name == "THIS":
            return self.current
        if name == "PREV":
            assert len(self.stack) > 1
            return self.stack[-2]
        if name == "ROOT":
            return self.stack[0]
        if name == "FROM":
            return self.sender
        return name

    def variable(self, name):
        scope = self.current
        if name.startswith("global."):
            return self.globals, name[7:], "global"
        for prefix in ("PREV", "ROOT", "FROM", "THIS"):
            if name.startswith(prefix + "."):
                scope = self.target(prefix)
                name = name[len(prefix) + 1 :]
                break
        return self.countries[scope]["vars"], name, scope

    def value(self, token):
        if isinstance(token, list):
            data = fields(token)
            return self.value(data["value"]) + self.value(data.get("add", "0"))
        if token in ("THIS", "PREV", "ROOT", "FROM"):
            return self.target(token)
        if token in self.countries:
            return token
        try:
            return float(token)
        except ValueError:
            pass
        if "^" in token:
            array, index = token.split("^", 1)
            data = self.value(array) or []
            if index == "num":
                return len(data)
            position = int(self.value(index))
            return data[position] if position < len(data) else 0
        data, key, scope = self.variable(token)
        return self.temps.get((scope, key), data.get(key, 0))

    def write(self, name, value, temporary=False):
        if "^" in name:
            array, index = name.split("^", 1)
            data, key, _ = self.variable(array)
            data[key][int(self.value(index))] = value
        else:
            data, key, scope = self.variable(name)
            if temporary:
                self.temps[scope, key] = value
            else:
                data[key] = value

    def scoped(self, scope, block, condition=False):
        assert scope in self.countries, f"Invalid country reference: {scope}"
        self.stack.append(scope)
        try:
            return self.condition(block) if condition else self.execute(block)
        finally:
            self.stack.pop()

    def condition(self, block):
        matched = False
        for key, op, value in block:
            if key in ("if", "else_if", "else"):
                if key == "if":
                    matched = False
                data = fields(value)
                if not matched and (key == "else" or self.condition(data["limit"])):
                    matched = True
                    if not self.condition(
                        [entry for entry in value if entry[0] != "limit"]
                    ):
                        return False
            elif not self.check(key, op, value):
                return False
        return True

    def check(self, key, op, value):
        country = self.countries[self.current]
        assert key not in ("political_power", "stability"), "Use native has_* triggers"
        if key in self.triggers:
            return self.condition(self.triggers[key]) == (value == "yes")
        if key in ("custom_override_tooltip", "custom_trigger_tooltip"):
            return self.condition([entry for entry in value if entry[0] != "tooltip"])
        if key in ("OR", "AND", "NOT"):
            checks = (self.check(*entry) for entry in value)
            return any(checks) if key == "OR" else all(checks) != (key == "NOT")
        if key == "check_variable":
            data = fields(value)
            if "var" in data:
                left, comparison, right = data["var"], data["compare"], data["value"]
            else:
                left, comparison, right = value[0]
            left, right = self.value(left), self.value(right)
            if isinstance(left, str) and isinstance(right, (int, float)):
                left = int(left in self.countries)
            compare = (
                operator.ge
                if comparison == "greater_than_or_equals"
                else self.compare[comparison]
            )
            return compare(left, right)
        if key == "has_game_rule":
            data = fields(value)
            return self.rules[data["rule"]] == data["option"]
        if key == "has_dlc":
            return self.dlc
        if key == "is_in_array":
            name, _, member = value[0]
            return self.value(member) in (self.value(name) or [])
        if key == "any_of_scopes":
            data = fields(value)
            inner = [entry for entry in value if entry[0] != "array"]
            return any(
                self.scoped(member, inner, True) for member in self.value(data["array"])
            )
        if key.startswith("var:"):
            return self.scoped(self.value(key[4:]), value, True)
        if key in ("PREV", "ROOT", "FROM"):
            return self.scoped(self.target(key), value, True)
        if key == "tag":
            return self.current == self.target(value)
        if key == "has_tech":
            return value in country["techs"]
        if key == "has_idea":
            return value in country["ideas"]
        if key in ("has_country_flag", "has_global_flag"):
            flags = country["flags"] if key == "has_country_flag" else self.globals
            expiry = flags.get(value, -1)
            return expiry is None or expiry > self.day
        if key.startswith("is_in_") and key != "is_in_faction_with":
            continent = key.removeprefix("is_in_")
            continent = {"the_middle_east": "middle_east", "oceania": "australia"}.get(
                continent, continent
            )
            return (country["continent"] == continent) == (value == "yes")
        if key in ("has_equipment",):
            item, comparison, amount = value[0]
            return self.compare[comparison](
                country["equipment"].get(item, 0), float(amount)
            )
        if key == "has_war_with":
            return self.target(value) in country["wars"]
        if key == "has_wargoal_against":
            return self.target(value) in country["wargoals"]
        if key == "has_non_aggression_pact_with":
            return self.target(value) in country["pacts"]
        if key == "is_subject_of":
            return country["overlord"] == self.target(value)
        if key == "is_in_faction_with":
            return (
                country["faction"] is not None
                and country["faction"] == self.countries[self.target(value)]["faction"]
            )
        if key == "has_war":
            return bool(country["wars"]) == (value == "yes")
        if key in ("has_political_power", "has_stability"):
            return self.compare[op](country[key.removeprefix("has_")], float(value))
        if key == "any_owned_state":
            return country["num_of_controlled_states"] > 0
        if key == "always":
            return value == "yes"
        if key in country:
            if value in ("yes", "no"):
                return country[key] == (value == "yes")
            return self.compare[op](country[key], float(value))
        raise AssertionError(f"Unmodeled trigger: {key}")

    def execute(self, block):
        matched = False
        for key, _, value in block:
            country = self.countries[self.current]
            if key in ("if", "else_if", "else"):
                if key == "if":
                    matched = False
                data = fields(value)
                if not matched and (key == "else" or self.condition(data["limit"])):
                    matched = True
                    self.execute([entry for entry in value if entry[0] != "limit"])
            elif key == "oem_nuclear_devastate_country":
                self.history.append((self.current, "devastation"))
            elif key in self.effects:
                self.execute(self.effects[key])
            elif key in ("hidden_effect",):
                self.execute(value)
            elif key in (
                "set_variable",
                "set_temp_variable",
                "add_to_temp_variable",
                "add_to_variable",
                "subtract_from_variable",
            ):
                name, _, operand = value[0]
                amount = self.value(operand)
                if key in ("add_to_temp_variable", "add_to_variable"):
                    amount += self.value(name)
                elif key == "subtract_from_variable":
                    amount = self.value(name) - amount
                self.write(name, amount, temporary="temp" in key)
            elif key == "add_to_array":
                name, _, item = value[0]
                data, field, _ = self.variable(name)
                data.setdefault(field, []).append(self.value(item))
            elif key == "clear_variable":
                data, field, _ = self.variable(value)
                data.pop(field, None)
            elif key in ("for_each_loop", "for_each_scope_loop"):
                data = fields(value)
                inner = [
                    entry
                    for entry in value
                    if entry[0] not in ("array", "index", "value")
                ]
                for index, item in enumerate(list(self.value(data["array"]) or [])):
                    if key == "for_each_loop":
                        self.write(data["index"], index, True)
                        self.write(data["value"], item, True)
                        self.execute(inner)
                    else:
                        self.scoped(item, inner)
            elif key.startswith("var:"):
                self.scoped(self.value(key[4:]), value)
            elif key in ("PREV", "ROOT", "FROM"):
                self.scoped(self.target(key), value)
            elif key in ("add_ideas", "remove_ideas"):
                if key == "add_ideas" and value not in country["ideas"]:
                    country["ideas"].append(value)
                    self.history.append((self.current, value))
                elif key == "remove_ideas" and value in country["ideas"]:
                    country["ideas"].remove(value)
            elif key == "add_timed_idea":
                idea = fields(value)["idea"]
                country["ideas"].append(idea)
                self.history.append((self.current, idea))
            elif key == "add_equipment_to_stockpile":
                data = fields(value)
                country["equipment"][data["type"]] += self.value(data["amount"])
            elif key in ("set_country_flag", "set_global_flag"):
                data = fields(value) if isinstance(value, list) else {"flag": value}
                flag = (
                    data["flag"].replace("@PREV", "@" + str(self.target("PREV")))
                    if "@PREV" in data["flag"]
                    else data["flag"]
                )
                flags = country["flags"] if key == "set_country_flag" else self.globals
                flags[flag] = self.day + int(data["days"]) if "days" in data else None
            elif key == "clr_country_flag":
                country["flags"].pop(value, None)
            elif key == "country_event":
                data = fields(value) if isinstance(value, list) else {"id": value}
                self.events.append(
                    (self.day + int(data.get("days", 0)), self.current, data["id"])
                )
            elif key in ("add_political_power", "add_stability"):
                field = key.removeprefix("add_")
                country[field] += self.value(value)
            elif key in ("every_country", "every_other_country"):
                data = fields(value)
                for name in self.countries:
                    if key == "every_other_country" and name == self.current:
                        continue
                    if "limit" not in data or self.scoped(name, data["limit"], True):
                        self.scoped(
                            name, [entry for entry in value if entry[0] != "limit"]
                        )
            elif key == "add_tech_bonus":
                data = fields(value)
                country["bonuses"].append(
                    (data["technology"], self.value(data["bonus"]), int(data["uses"]))
                )
            elif key == "create_wargoal":
                data = fields(value)
                assert data["type"] == "puppet_wargoal_focus"
                country["wargoals"].append(self.target(data["target"]))
            elif key in ("log", "custom_effect_tooltip", "add_opinion_modifier"):
                continue
            else:
                raise AssertionError(f"Unmodeled effect: {key}")

    def run(self, name, country):
        self.temps.clear()
        self.scoped(country, self.effects[name])

    def decision(self, name, phase, country):
        self.temps.clear()
        self.scoped(country, fields(self.decisions[name])[phase])

    def take_decision(self, name, country):
        definition = fields(self.decisions[name])
        if "available" in definition:
            assert self.scoped(country, definition["available"], True)
        price = float(definition.get("cost", "0"))
        assert self.countries[country]["political_power"] >= price
        self.countries[country]["political_power"] -= price
        self.decision(name, "complete_effect", country)

    def strike(self, attacker, victim):
        raid = self.countries.setdefault("raid", {"vars": {}, "exists": False})
        raid["vars"].update(actor_country=attacker, victim_country=victim)
        self.run("oem_nuclear_stage_strike", "raid")
        self.countries.pop("raid")

    def reload(self):
        state = json.loads(
            json.dumps(
                {
                    name: getattr(self, name)
                    for name in (
                        "rules",
                        "globals",
                        "countries",
                        "events",
                        "history",
                        "day",
                    )
                }
            )
        )
        restored = Script()
        for name, value in state.items():
            setattr(restored, name, value)
        return restored


def world(nuclear="balanced", dms="balanced"):
    script = Script(nuclear, dms)
    for name in ("leader", "attacker", "ally1", "ally2", "ally3", "ally4"):
        script.country(name)
    script.countries["leader"].update(
        is_faction_leader=True,
        techs=["construction4", "construction5", "construction6"],
        wars=["attacker"],
    )
    script.countries["leader"]["ideas"] = [
        "nuclear_power_def",
        "strategic_retaliation_only",
    ]
    script.countries["attacker"]["ideas"] = ["nuclear_power_off", "full_first_use"]
    script.countries["attacker"]["wars"] = ["leader"]
    script.countries["ally1"]["continent"] = "north_america"
    script.countries["leader"]["vars"]["faction_members"] = [
        "leader",
        "ally1",
        "ally2",
        "ally3",
        "ally4",
    ]
    script.countries["leader"]["vars"]["oem_dms_enemy"] = "attacker"
    return script


def arm(script):
    script.countries["leader"]["vars"]["oem_dms_prepared_country"] = "leader"
    script.run("oem_dms_arm", "leader")


def test_off_has_no_records_equipment_charge_or_events():
    script = world("off", "off")
    script.strike("attacker", "leader")
    arm(script)
    script.run("oem_dms_activate", "leader")
    script.run("oem_nuclear_finish_collapse", "leader")
    assert script.globals == {}
    assert script.events == []
    assert script.countries["leader"]["equipment"]["nuclear_missile_equipment"] == 5


def test_first_attacker_preparation_and_reserve_are_snapshotted_before_damage():
    script = world()
    arm(script)
    script.strike("attacker", "leader")
    script.strike("ally4", "leader")
    assert script.globals["oem_nuclear_attackers"] == ["attacker"]
    assert script.globals["oem_nuclear_prepared"] == [1]
    assert script.globals["oem_nuclear_reserves"] == [1]
    assert script.countries["leader"]["equipment"]["nuclear_missile_equipment"] == 4
    assert len(script.events) == 2
    assert not any(action == "devastation" for _, action in script.history)


def test_each_attacker_is_condemned_once_without_overwriting_the_response_target():
    script = world()
    for attacker in ("attacker", "ally4", "attacker"):
        script.strike(attacker, "leader")
    assert script.globals["oem_nuclear_attackers"] == ["attacker"]
    assert script.globals["oem_nuclear_condemned"] == ["attacker", "ally4"]
    assert script.countries["attacker"]["ideas"].count("oem_nuclear_pariah") == 1


@pytest.mark.parametrize("disabled", ["doctrine", "dlc"])
def test_retaliation_respects_existing_doctrine_and_dlc(disabled):
    script = world()
    if disabled == "doctrine":
        script.countries["leader"]["ideas"] = ["nuclear_power_def", "no_use_case"]
    else:
        script.dlc = False
    script.strike("attacker", "leader")
    assert script.countries["leader"]["equipment"]["nuclear_missile_equipment"] == 5
    if disabled == "doctrine":
        assert script.globals["oem_nuclear_reserves"] == [0]
    else:
        assert script.globals == {}


@pytest.mark.parametrize(
    "mode,collapse",
    [("balanced", "oem_nuclear_collapse"), ("chaos", "oem_nuclear_collapse_chaos")],
)
def test_reciprocal_responses_are_bounded_and_collapse_once(mode, collapse):
    script = world(mode)
    script.strike("attacker", "leader")
    script = script.reload()
    script.run("oem_nuclear_retaliate", "leader")
    script.run("oem_nuclear_retaliate", "attacker")
    script.run("oem_nuclear_retaliate", "leader")
    script.run("oem_nuclear_finish_collapse", "attacker")
    assert script.globals["oem_nuclear_status"] == [2, 2]
    assert script.globals["oem_nuclear_reserves"] == [0, 0]
    assert len(script.events) == 4
    assert script.countries["leader"]["ideas"].count(collapse) == 1
    assert script.countries["attacker"]["ideas"].count(collapse) == 1
    assert script.countries["leader"]["equipment"]["nuclear_missile_equipment"] == 4
    assert script.countries["attacker"]["equipment"]["nuclear_missile_equipment"] == 4


def test_no_reserve_or_absent_attacker_cannot_retaliate():
    script = world()
    script.countries["leader"]["equipment"]["nuclear_missile_equipment"] = 0
    script.strike("attacker", "leader")
    script.countries["attacker"]["exists"] = False
    script.run("oem_nuclear_retaliate", "leader")
    assert script.globals["oem_nuclear_status"] == [2]
    assert script.globals["oem_nuclear_victims"] == ["leader"]


def test_timeout_then_stale_choice_never_repeats_collapse_or_trade_shock():
    script = world()
    script.strike("attacker", "leader")
    script.day = 7
    script.run("oem_nuclear_finish_collapse", "leader")
    script = script.reload()
    script.run("oem_nuclear_retaliate", "leader")
    script.run("oem_nuclear_finish_collapse", "leader")
    assert script.globals["oem_nuclear_status"] == [2]
    assert script.countries["leader"]["stability"] == pytest.approx(0.4)
    assert script.countries["ally1"]["ideas"].count("oem_nuclear_trade_shock") == 1


def test_nonnuclear_activation_survives_annexation_and_repeated_callbacks():
    script = world("off")
    arm(script)
    script.countries["leader"]["is_faction_leader"] = False
    assert script.globals["oem_dms_status"] == [1]
    script.run("oem_dms_activate", "leader")
    script.countries["leader"]["exists"] = False
    script = script.reload()
    script.run("oem_dms_activate", "leader")
    assert script.globals["oem_dms_status"] == [2]
    assert script.globals["oem_dms_recipient_status"] == [1, 1, 1]
    assert len(script.events) == 6
    script.countries["leader"].update(exists=True, is_faction_leader=True)
    arm(script)
    assert script.globals["oem_dms_sources"] == ["leader"]


def test_missing_recipient_is_closed_without_event_and_offered_archive_is_unique():
    script = world()
    arm(script)
    script.countries["ally2"]["exists"] = False
    script.run("oem_dms_activate", "leader")
    assert script.globals["oem_dms_recipient_status"] == [1, 3, 1]
    assert all(event[1] != "ally2" for event in script.events)
    assert len(set(script.globals["oem_dms_recipients"])) == 3


@pytest.mark.parametrize("mode,bonus", [("balanced", 0.25), ("chaos", 0.5)])
@pytest.mark.parametrize(
    "known,expected",
    [
        ("construction3", "construction4"),
        ("construction4", "construction5"),
        ("construction5", "construction6"),
    ],
)
def test_archive_grants_one_recorded_next_technology_after_source_disappears(
    mode, bonus, known, expected
):
    script = world(dms=mode)
    arm(script)
    script.run("oem_dms_activate", "leader")
    script.countries["leader"]["exists"] = False
    script.countries["ally1"]["techs"] = [known]
    script.run("oem_dms_accept", "ally1")
    script = script.reload()
    script.run("oem_dms_absorb_research", "ally1")
    script.run("oem_dms_absorb_research", "ally1")
    assert script.countries["ally1"]["bonuses"] == [(expected, bonus, 1)]
    assert script.globals["oem_dms_recipient_research"][0] == 0
    assert script.countries["ally1"]["wars"] == []


@pytest.mark.parametrize(
    "level,techs,factories",
    [
        (0, ["construction3"], 50),
        (1, ["construction4"], 50),
        (3, [], 50),
        (3, ["construction3"], 9),
    ],
)
def test_archive_never_grants_unrecorded_technology_or_bypasses_requirements(
    level, techs, factories
):
    script = world()
    arm(script)
    script.globals["oem_dms_recipient_research"][0] = level
    script.run("oem_dms_activate", "leader")
    script.run("oem_dms_accept", "ally1")
    script.countries["ally1"].update(techs=techs, num_of_factories=factories)
    script.run("oem_dms_absorb_research", "ally1")
    assert script.countries["ally1"]["bonuses"] == []


@pytest.mark.parametrize(
    "source_tech,recipient_tech,expected",
    [
        ("construction5", "construction3", []),
        ("construction6", "construction4", []),
        ("construction5", "construction4", [("construction5", 0.25, 1)]),
        ("construction6", "construction5", [("construction6", 0.25, 1)]),
    ],
)
def test_snapshot_does_not_infer_missing_source_prerequisites(
    source_tech, recipient_tech, expected
):
    script = world()
    script.countries["leader"]["techs"] = [source_tech]
    successor(script)
    script.countries["ally1"]["techs"] = [recipient_tech]
    script.run("oem_dms_absorb_research", "ally1")
    assert script.countries["ally1"]["bonuses"] == expected


def test_later_source_research_does_not_enlarge_the_armed_archive():
    script = world()
    script.countries["leader"]["techs"] = ["construction4"]
    arm(script)
    script.countries["leader"]["techs"].extend(["construction5", "construction6"])
    script.run("oem_dms_activate", "leader")
    script.run("oem_dms_accept", "ally1")
    script.countries["ally1"]["techs"] = ["construction4"]
    script.run("oem_dms_absorb_research", "ally1")
    assert script.countries["ally1"]["bonuses"] == []


def test_containment_cancels_pending_absorption_and_stale_acceptance():
    script = world()
    arm(script)
    script.run("oem_dms_activate", "leader")
    script.run("oem_dms_accept", "ally1")
    script.decision("oem_dms_contain_successors", "remove_effect", "ally1")
    script.run("oem_dms_accept", "ally1")
    script.run("oem_dms_absorb_research", "ally1")
    assert script.globals["oem_dms_recipient_status"][0] == 4
    assert "oem_dms_radicalized" not in script.countries["ally1"]["ideas"]
    assert script.countries["ally1"]["political_power"] == 450
    assert script.countries["ally1"]["bonuses"] == []


def test_preparation_requires_uninterrupted_reach_and_nuclear_snapshot_blocks_late_arming():
    script = world()
    preparation = fields(script.decisions["oem_dms_prepare"])
    assert preparation["days_remove"] == "180"
    script.decision("oem_dms_prepare", "complete_effect", "leader")
    script.countries["leader"]["is_faction_leader"] = False
    script.decision("oem_dms_prepare", "remove_effect", "leader")
    assert "oem_dms_prepared_country" not in script.countries["leader"]["vars"]
    script.countries["leader"]["is_faction_leader"] = True
    script.strike("attacker", "leader")
    arm(script)
    assert "oem_dms_sources" not in script.globals
    assert script.globals["oem_nuclear_prepared"] == [0]


def test_global_caps_are_shared_and_recipients_cannot_stack_sources():
    script = Script()
    for index in range(9):
        source = f"source{index}"
        members = [source] + [f"ally{index}_{number}" for number in range(4)]
        for name in members:
            script.country(
                name, continent="north_america" if name.endswith("_0") else "europe"
            )
        script.countries[source]["is_faction_leader"] = True
        script.countries[source]["vars"]["oem_dms_prepared_country"] = source
        script.countries[source]["vars"]["faction_members"] = members
        script.run("oem_dms_arm", source)
    assert len(script.globals["oem_dms_sources"]) == 8
    assert len(script.globals["oem_dms_recipients"]) == 24
    assert len(set(script.globals["oem_dms_recipients"])) == 24


def test_raid_disabled_branch_retains_original_devastation_and_uses_all_four_results():
    text = (ROOT / "common/raids/nuclear_raids.txt").read_text(encoding="utf-8")
    strategic = text.split("\tstrategic_nuclear_strike = {", 1)[1]
    assert strategic.count("oem_nuclear_stage_strike = yes") == 4
    assert strategic.count("record_strategic_nuclear_strike = yes") == 4
    assert strategic.count("every_owned_state = {") == 4
    assert strategic.count("limit = { oem_nuclear_collapse_enabled = yes }") == 4
    assert (
        "oem_nuclear_stage_strike"
        not in text.split("\tstrategic_nuclear_strike = {", 1)[0]
    )


def test_hooks_and_timed_events_have_terminal_guards():
    script = Script()
    hooks = fields(
        script.load("common/on_actions/oem_contingency_on_actions.txt")["on_actions"]
    )
    assert set(hooks) == {"on_capitulation_immediate", "on_annex"}
    events = parse((ROOT / "events/oem_contingencies.txt").read_text(encoding="utf-8"))
    events = {
        fields(value)["id"]: fields(value)
        for key, _, value in events
        if key == "country_event"
    }
    assert fields(events["oem_contingency.2"]["trigger"]) == {
        "oem_nuclear_response_pending": "yes"
    }
    assert fields(events["oem_contingency.11"]["trigger"]) == {
        "oem_dms_offer_pending": "yes"
    }
    assert fields(hooks["on_annex"])["effect"][0][0] == "FROM"


def successor(script, name="ally1"):
    arm(script)
    script.run("oem_dms_activate", "leader")
    script.run("oem_dms_accept", name)


def pulse(script, name, day):
    script.day = day
    script.globals["num_days"] = day
    script.run("oem_dms_process_pulse", name)


@pytest.mark.parametrize("mode,budget", [("balanced", 3), ("chaos", 6)])
def test_crises_exhaust_finite_capacity_and_stop_scheduling_without_paid_support(
    mode, budget
):
    script = world(dms=mode)
    successor(script)
    for number in range(1, budget + 1):
        pulse(script, "ally1", number * 90)
        assert script.globals["oem_dms_active_crises"] == 1
        script.run("oem_dms_close_crisis", "ally1")
        script = script.reload()
    events = len(script.events)
    pulse(script, "ally1", 9999)
    assert script.globals["oem_dms_active_crises"] == 0
    assert script.globals["oem_dms_recipient_capacity"][0] == 0
    assert script.globals["oem_dms_pulse_scheduled"][0] == 0
    assert len(script.events) == events
    assert script.countries["ally1"]["wars"] == []


def test_crisis_choice_creates_one_wargoal_and_never_declares_war():
    script = world()
    successor(script)
    pulse(script, "ally1", 90)
    script.take_decision("oem_dms_escalate_crisis", "ally1")
    script = script.reload()
    script.run("oem_dms_issue_wargoal", "ally1")
    assert script.countries["ally1"]["wargoals"] == ["attacker"]
    assert script.countries["ally1"]["wars"] == []
    assert script.countries["ally1"]["political_power"] == 400
    assert script.globals["oem_dms_active_crises"] == 0
    pulse(script, "ally1", 180)
    assert script.globals["oem_dms_recipient_capacity"][0] == 2


@pytest.mark.parametrize(
    "change", ["war", "pact", "same faction", "annexed", "subject"]
)
def test_crises_revalidate_diplomacy_before_spending_capacity_or_creating_wargoals(
    change,
):
    script = world()
    successor(script)
    if change == "war":
        script.countries["attacker"]["wars"].append("ally1")
    elif change == "pact":
        script.countries["attacker"]["pacts"].append("ally1")
    elif change == "same faction":
        script.countries["attacker"]["faction"] = "new alliance"
        script.countries["ally1"]["faction"] = "new alliance"
    elif change == "annexed":
        script.countries["attacker"]["exists"] = False
    else:
        script.countries["ally1"]["overlord"] = "attacker"
    pulse(script, "ally1", 90)
    script.run("oem_dms_issue_wargoal", "ally1")
    assert script.globals["oem_dms_recipient_capacity"][0] == 3
    assert script.countries["ally1"]["wargoals"] == []


def test_duplicate_pulses_and_closures_cannot_bypass_cooldowns_or_release_another_slot():
    script = world()
    successor(script)
    pulse(script, "ally1", 89)
    assert script.globals["oem_dms_recipient_capacity"][0] == 3
    pulse(script, "ally1", 90)
    script.run("oem_dms_close_crisis", "ally1")
    script = script.reload()
    pulse(script, "ally1", 90)
    script.run("oem_dms_close_crisis", "ally1")
    assert script.globals["oem_dms_active_crises"] == 0
    assert script.globals["oem_dms_recipient_capacity"][0] == 2
    assert script.globals["oem_dms_next_pulse_day"][0] == 180


def test_multiple_contingencies_share_four_pending_crisis_slots():
    script = world()
    successor(script)
    for name in ("ally2", "ally3"):
        script.run("oem_dms_accept", name)
    script.country("other_leader", is_faction_leader=True)
    members = ["other_leader", "other1", "other2", "other3", "other4"]
    for name in members[1:]:
        script.country(name, continent="north_america")
    script.countries["other_leader"]["vars"].update(
        faction_members=members, oem_dms_enemy="attacker"
    )
    script.countries["other_leader"]["vars"][
        "oem_dms_prepared_country"
    ] = "other_leader"
    script.run("oem_dms_arm", "other_leader")
    script.run("oem_dms_activate", "other_leader")
    for name in members[1:4]:
        script.run("oem_dms_accept", name)
    for name in script.globals["oem_dms_recipients"]:
        pulse(script, name, 90)
    assert script.globals["oem_dms_active_crises"] == 4
    assert sum(script.globals["oem_dms_crisis_active"]) == 4
    assert script.globals["oem_dms_recipient_capacity"] == [2, 2, 2, 2, 3, 3]


@pytest.mark.parametrize("mode,limit", [("balanced", 3), ("chaos", 6)])
def test_paid_support_is_capped_and_containment_stops_existing_and_future_crises(
    mode, limit
):
    script = world(dms=mode)
    successor(script)
    pulse(script, "ally1", 90)
    script.run("oem_dms_support_capacity", "ally1")
    script.run("oem_dms_support_capacity", "ally1")
    assert script.globals["oem_dms_recipient_capacity"][0] == limit
    script.decision("oem_dms_contain_successors", "remove_effect", "ally1")
    pulse(script, "ally1", 180)
    script.run("oem_dms_issue_wargoal", "ally1")
    script.run("oem_dms_support_capacity", "ally1")
    assert script.globals["oem_dms_active_crises"] == 0
    assert script.globals["oem_dms_pulse_scheduled"][0] == 0
    assert script.globals["oem_dms_recipient_capacity"][0] == 0
    assert script.countries["ally1"]["wargoals"] == []


def test_annexed_recipient_releases_crisis_slot_and_restoration_cannot_restart_it():
    script = world()
    successor(script)
    pulse(script, "ally1", 90)
    script.run("oem_dms_close_annexed_recipient", "ally1")
    script.countries["ally1"]["exists"] = False
    script = script.reload()
    script.countries["ally1"]["exists"] = True
    pulse(script, "ally1", 999)
    script.run("oem_dms_close_annexed_recipient", "ally1")
    assert script.globals["oem_dms_active_crises"] == 0
    assert script.globals["oem_dms_recipient_status"][0] == 4
    assert script.globals["oem_dms_pulse_scheduled"][0] == 0


def test_copied_preparation_cannot_arm_a_different_country():
    script = world()
    script.countries["leader"]["vars"]["oem_dms_prepared_country"] = "leader"
    clone = script.country("clone", is_faction_leader=True)
    clone["vars"] = dict(script.countries["leader"]["vars"])
    script.run("oem_dms_arm", "clone")
    assert script.globals == {}


def test_copied_source_slot_cannot_stand_down_the_original_contingency():
    script = world()
    arm(script)
    clone = script.country("clone", is_faction_leader=True)
    clone["vars"] = dict(script.countries["leader"]["vars"])
    clone["ideas"] = ["oem_dms_armed"]
    script.decision("oem_dms_stand_down", "complete_effect", "clone")
    assert script.globals["oem_dms_status"] == [1]


def test_copied_recipient_slot_cannot_contain_or_release_the_original_crisis():
    script = world()
    successor(script)
    pulse(script, "ally1", 90)
    clone = script.country("clone")
    clone["vars"] = dict(script.countries["ally1"]["vars"])
    clone["ideas"] = ["oem_dms_radicalized"]
    script.decision("oem_dms_contain_successors", "remove_effect", "clone")
    script.run("oem_dms_close_crisis", "clone")
    script.run("oem_dms_close_annexed_recipient", "clone")
    assert script.globals["oem_dms_recipient_status"][0] == 2
    assert script.globals["oem_dms_active_crises"] == 1


def test_recurring_notifications_have_no_actions_that_can_spend_a_later_crisis():
    events = parse((ROOT / "events/oem_contingencies.txt").read_text(encoding="utf-8"))
    notification = next(
        fields(value)
        for key, _, value in events
        if key == "country_event" and fields(value)["id"] == "oem_contingency.21"
    )
    assert fields(notification["option"]) == {"name": "oem_contingency.21.a"}
    assert notification["minor_flavor"] == "yes"
