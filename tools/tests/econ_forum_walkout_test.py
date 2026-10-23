"""Execute forum invitation source; native HOI4 acceptance is separate."""

from collections import Counter
from pathlib import Path

import pytest
from ai_race_state_model_test import _named_block, _parse_race_script
from targeted_operations_core_test import ScriptArray, TargetScript

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = ROOT / "common/scripted_effects/01_econ_forum_effects.txt"


class ForumScript(TargetScript):
    """Reuse the scope interpreter, forcing the successful 50% follower roll."""

    def __init__(self, preparing=1, hosted=2):
        source = EFFECTS.read_text(encoding="utf-8")
        self.effects = _parse_race_script(source)
        self.triggers = _parse_race_script(
            (ROOT / "common/scripted_triggers/01_econ_forum_triggers.txt").read_text(
                encoding="utf-8"
            )
        )
        self.standing_pass = _parse_race_script(
            _named_block(
                _named_block(source, "econ_forum_open_preparation"), "every_country"
            )
        )["every_country"]
        self.countries, self.globals, self.temps = {}, {}, {}
        self.scope_stack, self.events, self.targets = [], [], {}
        self.global_flags, self.external, self.stubs = {}, Counter(), set()
        self.random_draws = 0
        self.goto(2005, 1)
        for identifier in range(1, 5):
            country = self.country(identifier, ai=True, tag=f"C{identifier}")
            country["vars"].update(id=identifier, political_power=100)
            country["faction"] = 1 if identifier == 2 else 2
            self.run("econ_forum_ensure_country_arrays", identifier)
        # The caller has already boycotted before it leads a walkout.
        self.countries[1]["vars"]["econ_forum_boycott"][0] = 1
        if hosted is not None:
            self.countries[1]["vars"]["econ_forum_hosted"] = hosted
        for field in ("host", "preparing", "prestige", "cycle"):
            self.globals[f"econ_forum_{field}"] = ScriptArray([0] * 9)
        self.globals["econ_forum_host"][0] = 2
        self.globals["econ_forum_host"][2] = 1
        self.globals["econ_forum_preparing"][2] = preparing
        self.globals["econ_forum_prestige"][:] = [20] * 9
        self.temps.update(v=0, ef_i=6, ef_host=2)

    def value(self, name, identifier):
        if isinstance(name, str) and name.startswith("event_target:"):
            return self.targets[name.split(":", 1)[1]]
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        key, _, operand = statement
        country = self.countries[identifier]
        if key == "is_in_faction":
            return bool(country["faction"]) == (operand == "yes")
        if key == "is_in_faction_with":
            return (
                country["faction"]
                == self.countries[self.value(operand, identifier)]["faction"]
            )
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "every_country":
            for member in self.countries:
                self.scoped(operand, identifier, member)
        elif key == "limit":
            raise AssertionError("A country limit must be evaluated before its effects")
        elif key == "save_event_target_as":
            self.targets[operand] = identifier
        elif key == "resize_array":
            fields = dict((name, value) for name, _, value in operand)
            scope, name = self._scope(fields["array"], identifier)
            size = int(self.value(fields["size"], identifier))
            old = scope.get(name, [])
            scope[name] = ScriptArray((old + [0] * size)[:size])
        else:
            super().execute_statement(statement, identifier)

    def scoped(self, operand, identifier, target, condition=False):
        if not condition:
            limits = [body for key, _, body in operand if key == "limit"]
            if limits and not super().scoped(
                limits[0], identifier, target, condition=True
            ):
                return None
            operand = [entry for entry in operand if entry[0] != "limit"]
        return super().scoped(operand, identifier, target, condition=condition)


@pytest.mark.parametrize("preparing", [0, 1])
def test_walkout_invites_followers_in_the_current_or_next_preparation(preparing):
    forum = ForumScript(preparing)
    forum.run("econ_forum_lead_walkout", 1)
    for follower in (3, 4):
        variables = forum.countries[follower]["vars"]
        assert variables["econ_forum_walkout_host"] == 1
        assert variables["econ_forum_walkout_forum"] == 0
        assert variables["econ_forum_boycott"][0] == 1
        assert variables["econ_forum_status"][2] == preparing
        assert variables["political_power"] == 75
    assert forum.temps["ef_i"] == 6
    assert forum.temps["v"] == 0
    assert forum.globals["econ_forum_prestige"][2] == 22
    assert forum.events == [(2, "econ_forum_news.9")]
    if not preparing:
        forum.temps.update(ef_i=2, ef_host=1)
        forum.execute_statement(("every_country", "=", forum.standing_pass), 1)
        assert [forum.countries[i]["vars"]["econ_forum_status"][2] for i in (3, 4)] == [
            1,
            1,
        ]


@pytest.mark.parametrize(
    "status,boycott", [(1, 0), (2, 0), (3, 0), (4, 0), (-1, 0), (0, 1)]
)
def test_walkout_respects_existing_rival_invitation_reply_and_boycott(status, boycott):
    forum = ForumScript()
    variables = forum.countries[3]["vars"]
    variables["econ_forum_status"][2] = status
    variables["econ_forum_boycott"][2] = boycott
    forum.run("econ_forum_lead_walkout", 1)
    assert variables["econ_forum_status"][2] == status
    assert variables["econ_forum_boycott"][2] == boycott
    forum.run("econ_forum_lead_walkout", 1)
    assert variables["political_power"] == 75
    assert forum.globals["econ_forum_prestige"][2] == 22


def test_walkout_without_a_hosted_forum_does_not_invite():
    forum = ForumScript(hosted=None)
    forum.run("econ_forum_lead_walkout", 1)
    variables = forum.countries[3]["vars"]
    assert "econ_forum_walkout_host" not in variables
    assert variables["econ_forum_status"][2] == 0
    assert forum.temps["ef_i"] == 6


@pytest.mark.parametrize("ai", [False, True])
def test_normal_standing_invitation_is_idempotent_and_queues_only_for_humans(ai):
    forum = ForumScript()
    forum.countries[3]["ai"] = ai
    forum.temps["ef_i"] = 2
    for _ in range(2):
        forum.run("econ_forum_send_invitation", 3)
    variables = forum.countries[3]["vars"]
    assert variables["econ_forum_status"][2] == 1
    assert variables.get("econ_forum_invite_queue", []) == ([] if ai else [2])
    assert forum.events == ([] if ai else [(3, "econ_forum.2")])
