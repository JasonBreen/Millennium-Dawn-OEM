from copy import deepcopy
from datetime import date, timedelta

import pytest
from shared.ai_race_test_support import _named_block, _parse_race_script
from stalker_lifecycle_test import ROOT, StalkerScript, _option


class ProliferationScript(StalkerScript):
    def __init__(self):
        super().__init__()
        for name in ("scripted", "operations", "proliferation", "incidents"):
            path = f"common/scripted_effects/99_METALGEAR_{name}_effects.txt"
            self.effects.update(
                _parse_race_script((ROOT / path).read_text(encoding="utf-8"))
            )
        self.triggers["METALGEAR_scenario_enabled"] = [("always", "=", "yes")]
        self.opinion_modifiers = set()
        if self.tag("JAP") is None:
            self.country(920, tag="JAP")
        self.country(769, tag="NEW_YORK")
        self.countries[769]["controller"] = 1
        self.globals.update(
            METALGEAR_capacity=2,
            METALGEAR_coherence=70,
            METALGEAR_reach=50,
            METALGEAR_exposure=10,
        )
        for tag in ("USA", "JAP", "SOV"):
            self.countries[self.tag(tag)]["vars"].update(
                political_power=200, METALGEAR_review_phase=4
            )
        self.goto(2001, 1, 1)

    def execute_statement(self, statement, identifier):
        if statement[0] == "add_opinion_modifier":
            fields = {key: value for key, _, value in statement[2]}
            self.opinion_modifiers.add(
                (identifier, self.tag(fields["target"]), fields["modifier"])
            )
        if statement[0] != "custom_effect_tooltip":
            super().execute_statement(statement, identifier)

    def condition_statement(self, statement, identifier):
        if statement[0] == "has_stability":
            return self.comparisons[statement[1]](
                self.countries[identifier]["vars"].get("stability", 0),
                float(statement[2]),
            )
        return super().condition_statement(statement, identifier)

    def run_hook(self, name, identifier):
        text = (
            ROOT / "common/on_actions/99_METALGEAR_proliferation_on_actions.txt"
        ).read_text(encoding="utf-8")
        body = _parse_race_script(_named_block(_named_block(text, name), "effect"))[
            "effect"
        ]
        self.execute(body, identifier)

    def run_control_change_hook(self):
        self.run_hook("on_state_control_changed", 698)


def choose(script, number, letter, tag="USA"):
    script.actor = script.tag(tag)
    filename = (
        "events/METALGEAR_" + ("proliferation" if number < 60 else "incidents") + ".txt"
    )
    script.hidden_option(
        f"METALGEAR.{number}", f"METALGEAR.{number}.{letter}", filename
    )


def available(script, number, letter):
    filename = (
        "events/METALGEAR_" + ("proliferation" if number < 60 else "incidents") + ".txt"
    )
    return script.condition(
        next(
            body
            for key, _, body in _option(
                f"METALGEAR.{number}", f"METALGEAR.{number}.{letter}", filename
            )
            if key == "trigger"
        ),
        script.actor,
    )


def start_trail(script, tag):
    text = (ROOT / "common/decisions/METALGEAR_proliferation_decisions.txt").read_text(
        encoding="utf-8"
    )
    body = _parse_race_script(
        _named_block(
            _named_block(text, f"METALGEAR_pf_{tag.lower()}_trail"), "complete_effect"
        )
    )["complete_effect"]
    script.actor = script.tag(tag)
    script.execute(body, script.actor)


def prepare_partner_record(script, tag):
    script.countries[script.tag(tag)]["vars"].update(
        METALGEAR_pf_phase=4, METALGEAR_pf_policy=1
    )


def begin_timed_work(script, tag, case, route="a"):
    if case == "trail":
        start_trail(script, tag)
        return "METALGEAR_pf_phase", {"USA": 50, "JAP": 51, "SOV": 52}[tag]
    if case == "inquiry":
        script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
        choose(script, 53, route)
        return "METALGEAR_pf_inquiry", 56
    phase = f"METALGEAR_pf_{case}_phase"
    script.countries[1]["vars"][phase] = 1
    choose(script, 59 if case == "tanker" else 61, route)
    return phase, 60 if case == "tanker" else 62


@pytest.mark.parametrize(
    "tag,case,route",
    [(tag, "trail", "a") for tag in ("USA", "JAP", "SOV")]
    + [("USA", "inquiry", route) for route in ("a", "b")]
    + [
        ("USA", case, route)
        for case in ("tanker", "shell")
        for route in ("a", "b", "c")
    ],
)
def test_daily_completion_delivers_at_expiration_without_a_monthly_wait(
    tag, case, route
):
    script = ProliferationScript()
    script.goto(2001, 1, 15)
    phase, report = begin_timed_work(script, tag, case, route)
    actor = script.tag(tag)
    script.goto(2001, 3, 1)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    deadline = date(2001, 1, 15) + timedelta(days=60)
    before_deadline = deadline - timedelta(days=1)
    script.goto(before_deadline.year, before_deadline.month, before_deadline.day)
    script.run_hook("on_daily", actor)
    assert script.countries[actor]["vars"][phase] == 2
    assert script.events.count((actor, f"METALGEAR.{report}")) == 0
    script = deepcopy(script)
    script.goto(deadline.year, deadline.month, deadline.day)
    script.run_hook("on_daily", actor)
    assert script.countries[actor]["vars"][phase] == 3
    assert script.events.count((actor, f"METALGEAR.{report}")) == 1
    for _ in range(2):
        script.run_hook("on_daily", actor)
        script.run("METALGEAR_monthly_proliferation_pulse", 1)
        script.run("METALGEAR_monthly_incidents_pulse", 1)
    assert script.events.count((actor, f"METALGEAR.{report}")) == 1
    choose(script, report, "a", tag)
    before = deepcopy(script.countries), script.globals.copy()
    script.run_hook("on_daily", actor)
    choose(script, report, "a", tag)
    assert (script.countries, script.globals) == before


@pytest.mark.parametrize("case", ["trail", "inquiry", "tanker", "shell"])
@pytest.mark.parametrize("interruption", ["site", "host", "disabled", "abandoned"])
def test_daily_completion_rechecks_interruption_before_delivering(case, interruption):
    script = ProliferationScript()
    phase, report = begin_timed_work(script, "USA", case)
    script.goto(2001, 3, 2)
    if interruption == "site":
        script.countries[769]["controller"] = 2
    elif interruption == "host":
        script.countries[1]["exists"] = False
    elif interruption == "disabled":
        script.triggers["METALGEAR_scenario_enabled"] = [("always", "=", "no")]
    else:
        if case == "trail":
            script.run("METALGEAR_pf_interrupt", 1)
        elif case == "inquiry":
            script.countries[1]["vars"][phase] = 5
            script.run("METALGEAR_pf_close_inquiry", 1)
        else:
            script.countries[1]["vars"][phase] = 5
            script.run(f"METALGEAR_pf_{case}_release", 1)
    script.run_hook("on_daily", 1)
    emergency_report = interruption == "site" and case in ("tanker", "shell")
    assert script.events.count((1, f"METALGEAR.{report}")) == int(emergency_report)
    if emergency_report:
        assert script.countries[1]["vars"][f"METALGEAR_pf_{case}_route"] == 3
    if interruption in ("site", "abandoned"):
        assert script.globals["METALGEAR_capacity"] == 2


@pytest.mark.parametrize("tag", ["USA", "JAP", "SOV"])
def test_daily_completion_honors_the_2005_preparation_cutoff(tag):
    script = ProliferationScript()
    script.goto(2004, 12, 1)
    phase, report = begin_timed_work(script, tag, "trail")
    script.goto(2005, 2, 1)
    script.run_hook("on_daily", script.tag(tag))
    assert script.countries[script.tag(tag)]["vars"][phase] == 5
    assert script.events.count((script.tag(tag), f"METALGEAR.{report}")) == 0
    assert script.globals["METALGEAR_capacity"] == 2


def test_simultaneous_daily_completions_keep_independent_commitments():
    script = ProliferationScript()
    begin_timed_work(script, "USA", "inquiry")
    begin_timed_work(script, "USA", "tanker")
    assert script.globals["METALGEAR_capacity"] == 0
    script.goto(2001, 3, 2)
    script.run_hook("on_daily", 1)
    assert script.events.count((1, "METALGEAR.56")) == 1
    assert script.events.count((1, "METALGEAR.60")) == 1
    choose(script, 56, "a")
    assert script.globals["METALGEAR_capacity"] == 1
    choose(script, 60, "a")
    assert script.globals["METALGEAR_capacity"] == 2


@pytest.mark.parametrize("brief", [59, 61])
def test_emergency_ai_weight_falls_at_low_stability_but_stays_nonzero(brief):
    script = ProliferationScript()
    filename = (
        "events/METALGEAR_" + ("proliferation" if brief == 59 else "incidents") + ".txt"
    )
    option = _option(f"METALGEAR.{brief}", f"METALGEAR.{brief}.c", filename)
    ai = next(body for key, _, body in option if key == "ai_chance")
    weights = []
    for stability in (0.5, 0.2):
        script.countries[1]["vars"]["stability"] = stability
        weight = float(next(value for key, _, value in ai if key == "base"))
        for key, _, modifier in ai:
            if key == "modifier" and script.condition(
                [entry for entry in modifier if entry[0] != "factor"], 1
            ):
                weight *= float(
                    next(value for name, _, value in modifier if name == "factor")
                )
        weights.append(weight)
    assert 0 < weights[1] < weights[0]


@pytest.mark.parametrize("tag,number", [("USA", 50), ("JAP", 51), ("SOV", 52)])
@pytest.mark.parametrize("letter,policy", [("a", 1), ("b", 2), ("c", 3)])
def test_national_trail_has_a_real_delay_and_one_terminal_policy(
    tag, number, letter, policy
):
    script = ProliferationScript()
    start_trail(script, tag)
    assert script.globals["METALGEAR_capacity"] == (1 if tag == "USA" else 2)
    script.goto(2001, 2, 28)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_phase"] == 2
    script = deepcopy(script)
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, number, letter, tag)
    variables = script.countries[script.tag(tag)]["vars"]
    assert variables["METALGEAR_pf_policy"] == policy
    assert script.globals["METALGEAR_capacity"] == 2
    before = variables.copy(), script.globals.copy()
    choose(script, number, letter, tag)
    assert (variables, script.globals) == before
    script.goto(2005, 1, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert variables["METALGEAR_pf_phase"] == 4
    assert variables["METALGEAR_pf_policy"] == policy


@pytest.mark.parametrize("tag", ["USA", "JAP", "SOV"])
@pytest.mark.parametrize("phase", [2, 3])
def test_2005_cancels_unfinished_trail_and_abandonment_is_idempotent(tag, phase):
    script = ProliferationScript()
    start_trail(script, tag)
    script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_phase"] = phase
    script.goto(2005, 1, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    script.run("METALGEAR_pf_interrupt", script.tag(tag))
    assert script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_phase"] == 5
    assert script.globals["METALGEAR_capacity"] == 2


@pytest.mark.parametrize("tag", ["USA", "JAP", "SOV"])
@pytest.mark.parametrize("capacity", [0, 2])
def test_2005_closes_an_unstarted_trail_without_releasing_unreserved_capacity(
    tag, capacity
):
    script = ProliferationScript()
    script.globals["METALGEAR_capacity"] = capacity
    script.goto(2005, 1, 1)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert script.countries[script.tag(tag)]["vars"].get("METALGEAR_pf_phase", 0) == 0
    script = deepcopy(script)
    script.goto(2005, 1, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    variables = script.countries[script.tag(tag)]["vars"]
    assert variables["METALGEAR_pf_phase"] == 5
    before = variables.copy(), script.globals.copy()
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    start_trail(script, tag)
    assert (variables, script.globals) == before
    assert script.globals["METALGEAR_capacity"] == capacity


@pytest.mark.parametrize(
    "japan,russia", [("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")]
)
def test_cooperation_requires_both_national_consents_and_returns_once(japan, russia):
    script = ProliferationScript()
    for tag in ("JAP", "SOV"):
        prepare_partner_record(script, tag)
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    choose(script, 54, japan, "JAP")
    choose(script, 55, russia, "SOV")
    assert script.globals["METALGEAR_capacity"] == 1
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, 56, "a")
    assert script.globals["METALGEAR_capacity"] == 2
    assert script.globals["METALGEAR_reach"] == 50 + 5 * (japan == "a") + 5 * (
        russia == "a"
    )
    before = script.globals.copy()
    choose(script, 56, "a")
    assert script.globals == before


@pytest.mark.parametrize("tag,number", [("JAP", 54), ("SOV", 55)])
@pytest.mark.parametrize("interruption", ["war", "annexation"])
def test_interrupted_partner_closes_without_canceling_other_country(
    tag, number, interruption
):
    script = ProliferationScript()
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    country = script.countries[script.tag(tag)]
    if interruption == "annexation":
        country["exists"] = False
    else:
        country["has_war_with"] = {1}
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, number, "a", tag)
    assert country["vars"]["METALGEAR_pf_exchange"] == 4
    other = script.tag("SOV" if tag == "JAP" else "JAP")
    assert script.countries[other]["vars"]["METALGEAR_pf_exchange"] == 1
    assert script.countries[1]["vars"]["METALGEAR_pf_inquiry"] == 2


@pytest.mark.parametrize("tag,number", [("JAP", 54), ("SOV", 55)])
@pytest.mark.parametrize("reply", [None, "a", "b"])
def test_initial_partner_notice_prevents_early_duplicates_and_allows_later_recovery(
    tag, number, reply
):
    script = ProliferationScript()
    prepare_partner_record(script, tag)
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    choose(script, 53, "a")
    requests = [
        (script.tag("JAP"), "METALGEAR.54"),
        (script.tag("SOV"), "METALGEAR.55"),
    ]
    assert [script.events.count(request) for request in requests] == [1, 1]
    script = deepcopy(script)
    script.goto(2001, 2, 1)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert [script.events.count(request) for request in requests] == [1, 1]
    if reply is not None:
        choose(script, number, reply, tag)
    script.goto(2001, 2, 5)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    for request in requests:
        answered = request[0] == script.tag(tag) and reply is not None
        assert script.events.count(request) == (1 if answered else 2)
    assert script.globals["METALGEAR_capacity"] == 1


def test_missing_shadow_records_still_dispatches_inquiry_and_both_incidents():
    script = ProliferationScript()
    script.goto(2006, 1, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    assert script.countries[1]["vars"]["METALGEAR_pf_inquiry"] == 1
    for year, case in [(2007, "tanker"), (2009, "shell")]:
        script.goto(year, 5, 1)
        script.run("METALGEAR_monthly_incidents_pulse", 1)
        assert script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] == 1


@pytest.mark.parametrize("case,brief,report", [("tanker", 59, 60), ("shell", 61, 62)])
@pytest.mark.parametrize("route,result", [("a", 1), ("b", 2), ("c", 3)])
def test_incident_routes_keep_separate_results_and_release_once(
    case, brief, report, route, result
):
    script = ProliferationScript()
    variables = script.countries[1]["vars"]
    variables[f"METALGEAR_pf_{case}_phase"] = 1
    choose(script, brief, route)
    assert script.globals["METALGEAR_capacity"] == (2 if route == "c" else 1)
    script = deepcopy(script)
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    choose(script, report, "a")
    variables = script.countries[1]["vars"]
    assert variables[f"METALGEAR_pf_{case}_result"] == result
    assert script.globals["METALGEAR_capacity"] == 2
    before = variables.copy(), script.globals.copy()
    choose(script, report, "b")
    assert (variables, script.globals) == before
    other = "tanker" if case == "shell" else "shell"
    assert f"METALGEAR_pf_{other}_result" not in variables


@pytest.mark.parametrize("brief,case,report", [(59, "tanker", 60), (61, "shell", 62)])
@pytest.mark.parametrize("controlled", [False, True])
def test_emergency_authority_keeps_its_delay_with_exhausted_capacity_or_lost_site(
    brief, case, report, controlled
):
    script = ProliferationScript()
    script.actor = 1
    script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] = 1
    script.globals["METALGEAR_capacity"] = 0
    assert not available(script, brief, "a")
    assert not available(script, brief, "b")
    assert available(script, brief, "c")
    script.countries[769]["controller"] = 1 if controlled else 2
    choose(script, brief, "c")
    for month, day in [(1, 1), (2, 1), (3, 1)]:
        script.goto(2001, month, day)
        script.run_control_change_hook()
        script.run_control_change_hook()
        script.run("METALGEAR_monthly_incidents_pulse", 1)
        assert script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] == 2
        assert script.events.count((1, f"METALGEAR.{report}")) == 0
        assert script.condition(
            [("has_country_flag", "=", f"METALGEAR_pf_{case}_wait")], 1
        )
        assert script.globals["METALGEAR_capacity"] == 0
    script = deepcopy(script)
    script.goto(2001, 3, 2)
    script.run_control_change_hook()
    script.run("METALGEAR_monthly_incidents_pulse", 1)
    variables = script.countries[1]["vars"]
    assert variables[f"METALGEAR_pf_{case}_phase"] == 3
    assert script.events.count((1, f"METALGEAR.{report}")) == 1
    choose(script, report, "a")
    assert variables[f"METALGEAR_pf_{case}_result"] == 3
    assert script.globals["METALGEAR_capacity"] == 0


@pytest.mark.parametrize("case,brief", [("tanker", 59), ("shell", 61)])
@pytest.mark.parametrize("route", ["a", "b"])
@pytest.mark.parametrize("dispatch", ["monthly", "control_hook"])
def test_lost_site_downgrades_and_releases_only_the_affected_commitment(
    case, brief, route, dispatch
):
    script = ProliferationScript()
    script.run("METALGEAR_pf_commit", 1)
    script.countries[1]["vars"][f"METALGEAR_pf_{case}_phase"] = 1
    choose(script, brief, route)
    script.countries[769]["controller"] = 2
    for _ in range(2):
        if dispatch == "control_hook":
            script.run_control_change_hook()
        else:
            script.run("METALGEAR_monthly_incidents_pulse", 1)
    assert script.globals["METALGEAR_capacity"] == 1
    variables = script.countries[1]["vars"]
    assert variables[f"METALGEAR_pf_{case}_route"] == 3
    assert variables[f"METALGEAR_pf_{case}_phase"] == 3
    assert variables["METALGEAR_pf_committed"] == 1
    assert not script.condition(
        [("has_country_flag", "=", f"METALGEAR_pf_{case}_wait")], 1
    )


@pytest.mark.parametrize("prepared", [False, True])
@pytest.mark.parametrize("partners", [0, 1, 2])
@pytest.mark.parametrize("brief,case", [(59, "tanker"), (61, "shell")])
@pytest.mark.parametrize("political_power", [-25, 0, 100])
def test_independent_authorization_remains_available_and_charges_discounted_cost(
    prepared, partners, brief, case, political_power
):
    script = ProliferationScript()
    script.actor = 1
    variables = script.countries[1]["vars"]
    variables.update(
        {f"METALGEAR_pf_{case}_phase": 1, "METALGEAR_pf_inquiry_result": int(prepared)}
    )
    for tag in ("JAP", "SOV")[:partners]:
        script.countries[script.tag(tag)]["vars"]["METALGEAR_pf_exchange"] = 2
    price = (25 if prepared else 50) - 5 * partners
    variables["political_power"] = political_power
    assert available(script, brief, "a")
    choose(script, brief, "a")
    assert variables["political_power"] == political_power - price
    before = variables.copy(), script.globals.copy()
    choose(script, brief, "a")
    assert (variables, script.globals) == before


@pytest.mark.parametrize("brief,case", [(53, "inquiry"), (59, "tanker"), (61, "shell")])
@pytest.mark.parametrize("route", ["a", "b"])
def test_paid_responses_do_not_force_low_power_players_into_fallbacks(
    brief, case, route
):
    script = ProliferationScript()
    variables = script.countries[1]["vars"]
    phase = (
        "METALGEAR_pf_inquiry" if case == "inquiry" else f"METALGEAR_pf_{case}_phase"
    )
    variables.update({phase: 1, "political_power": -10})
    assert available(script, brief, route)

    choose(script, brief, route)

    assert variables[phase] == 2
    assert variables["political_power"] == (
        -60 if route == "a" and brief != 53 else -35
    )
    assert script.globals["METALGEAR_capacity"] == 1
    before = variables.copy(), script.globals.copy()
    choose(script, brief, route)
    assert (variables, script.globals) == before


@pytest.mark.parametrize("tag,number", [("JAP", 54), ("SOV", 55)])
@pytest.mark.parametrize(
    "phase,policy,usable",
    [
        (0, 0, False),
        (2, 0, False),
        (3, 0, False),
        (4, 0, False),
        (4, 1, True),
        (4, 2, True),
        (4, 3, False),
        (5, 0, False),
    ],
)
@pytest.mark.parametrize("political_power", [-10, 200])
def test_partner_can_transfer_only_completed_nonconcealed_records(
    tag, number, phase, policy, usable, political_power
):
    script = ProliferationScript()
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    script.actor = script.tag(tag)
    variables = script.countries[script.actor]["vars"]
    variables.update(
        METALGEAR_pf_phase=phase,
        METALGEAR_pf_policy=policy,
        political_power=political_power,
    )
    assert available(script, number, "a") == usable
    assert available(script, number, "b")
    choose(script, number, "a", tag)
    assert variables["METALGEAR_pf_exchange"] == (2 if usable else 1)
    assert variables["political_power"] == political_power - (25 if usable else 0)
    before = variables.copy(), script.globals.copy(), script.opinion_modifiers.copy()
    choose(script, number, "a", tag)
    assert (variables, script.globals, script.opinion_modifiers) == before
    if not usable:
        choose(script, number, "b", tag)
        assert variables["METALGEAR_pf_exchange"] == 3
    script.goto(2001, 3, 2)
    script.run("METALGEAR_monthly_proliferation_pulse", 1)
    choose(script, 56, "a")
    assert script.globals["METALGEAR_reach"] == 50 + (5 if usable else 0)


@pytest.mark.parametrize("japan", range(5))
@pytest.mark.parametrize("russia", range(5))
def test_usa_exchange_status_reads_each_partners_record(japan, russia):
    script = ProliferationScript()
    script.countries[1]["vars"]["METALGEAR_pf_exchange"] = 2
    script.countries[script.tag("JAP")]["vars"]["METALGEAR_pf_exchange"] = japan
    script.countries[script.tag("SOV")]["vars"]["METALGEAR_pf_exchange"] = russia
    blocks = _parse_race_script(
        "source = {"
        + (
            ROOT
            / "common/scripted_localisation/99_METALGEAR_proliferation_scripted_localisation.txt"
        ).read_text(encoding="utf-8")
        + "}"
    )["source"]
    for tag, state in (("jap", japan), ("sov", russia)):
        record = next(
            body
            for key, _, body in blocks
            if key == "defined_text"
            and ("name", "=", f"METALGEAR_pf_{tag}_exchange_record") in body
        )
        for key, _, branch in record:
            if key != "text":
                continue
            fields = {name: value for name, _, value in branch}
            if "trigger" not in fields or script.condition(fields["trigger"], 1):
                assert fields["localization_key"] == (
                    f"METALGEAR_pf_exchange_{state}"
                    if state
                    else "METALGEAR_pf_exchange_none"
                )
                break
        else:
            pytest.fail("Exchange status has no matching text")
    for filename in (
        "MD_METALGEAR_l_english.yml",
        "MD_METALGEAR_preparation_l_english.yml",
    ):
        text = (ROOT / "localisation/english" / filename).read_text(
            encoding="utf-8-sig"
        )
        assert "[METALGEAR_pf_jap_exchange_record]" in text
        assert "[METALGEAR_pf_sov_exchange_record]" in text
        assert "[METALGEAR_pf_exchange_record]" not in text


@pytest.mark.parametrize("japan,russia", [(True, True), (True, False), (False, True)])
def test_each_incident_disclosure_adds_distinct_relations_and_cannot_repeat(
    japan, russia
):
    script = ProliferationScript()
    script.countries[1]["vars"]["METALGEAR_pf_inquiry"] = 1
    choose(script, 53, "a")
    for tag, event, accepted in (("JAP", 54, japan), ("SOV", 55, russia)):
        prepare_partner_record(script, tag)
        choose(script, event, "a" if accepted else "b", tag)
    for case, event in (("tanker", 60), ("shell", 62)):
        script.countries[1]["vars"].update(
            {f"METALGEAR_pf_{case}_phase": 3, f"METALGEAR_pf_{case}_route": 1}
        )
        choose(script, event, "a")
        for tag, accepted in (("JAP", japan), ("SOV", russia)):
            partner = script.tag(tag)
            assert (
                (1, partner, f"METALGEAR_pf_{case}_disclosure")
                in script.opinion_modifiers
            ) == accepted
            assert (
                (partner, 1, f"METALGEAR_pf_{case}_disclosure")
                in script.opinion_modifiers
            ) == accepted
        before = script.opinion_modifiers.copy(), script.external.copy()
        choose(script, event, "a")
        assert (script.opinion_modifiers, script.external) == before
    for tag, accepted in (("JAP", japan), ("SOV", russia)):
        partner = script.tag(tag)
        ids = {
            modifier
            for source, target, modifier in script.opinion_modifiers
            if source == 1 and target == partner
        }
        assert len(ids) == (3 if accepted else 0)
        assert ("diplomatic_support" in ids) == accepted
