import pytest
from ai_race_state_model_test import _parse_race_script
from stalker_lifecycle_test import ROOT, StalkerScript, _event

ROUTES = {
    "STALKER_apply_clear_sky_spared": "STALKER_strelok_turned_back",
    "STALKER_apply_clear_sky_canon": "STALKER_strelok_marked",
    "STALKER_apply_clear_sky_helped": "STALKER_strelok_remembers",
}


def _script():
    script = StalkerScript()
    script.effects.update(
        _parse_race_script(
            (ROOT / "common/scripted_effects/99_STALKER_legend_effects.txt").read_text(
                encoding="utf-8"
            )
        )
    )
    script.actor = 2
    script.run("STALKER_initialize_zone_society", 698)
    script.countries[698]["vars"].update(
        STALKER_zone_activity=50,
        STALKER_zone_containment=50,
        STALKER_zone_exploitation=50,
    )
    script.globals["STALKER_2012_route"] = 1
    return script


@pytest.mark.parametrize("usa_exists", [False, True])
def test_fairway_recovers_a_lost_carrier_after_120_days(usa_exists):
    script = _script()
    script.countries[1]["exists"] = usa_exists
    script.run("STALKER_schedule_fairway", 2)
    script.countries[1]["exists"] = False
    script.countries[2]["exists"] = False
    script.countries[698]["controller"] = 3
    script.goto(2012, 4, 29)
    script.run("STALKER_monthly_legend_pulse", 3)
    assert not any(event == "STALKER.174" for _, event in script.events)
    script.goto(2012, 4, 30)
    script.run("STALKER_monthly_legend_pulse", 3)
    assert (3, "STALKER.174") in script.events
    script.run("STALKER_monthly_legend_pulse", 3)
    assert script.events.count((3, "STALKER.174")) == 1
    script.countries[698]["controller"] = 4
    script.run("STALKER_monthly_legend_pulse", 4)
    assert (4, "STALKER.174") in script.events
    script.globals["STALKER_fairway_result"] = 1
    script.countries[698]["controller"] = 5
    script.run("STALKER_monthly_legend_pulse", 5)
    assert (5, "STALKER.174") not in script.events


def test_surviving_relay_and_monthly_recovery_share_one_pending_choice():
    script = _script()
    script.run("STALKER_schedule_fairway", 2)
    script.goto(2012, 4, 30)
    relay = next(
        body
        for key, _, body in _event("STALKER.178", "events/STALKER_legend.txt")
        if key == "immediate"
    )
    script.execute(relay, 1)
    assert script.events.count((2, "STALKER.174")) == 1
    script.run("STALKER_monthly_legend_pulse", 2)
    script.execute(relay, 1)
    assert script.events.count((2, "STALKER.174")) == 1


@pytest.mark.parametrize("effect,flag", ROUTES.items())
def test_clear_sky_routes_are_exclusive_and_resolve_only_once(effect, flag):
    script = _script()
    assert script.condition(script.triggers["STALKER_2011_unresolved"], 2)
    script.run(effect, 2)
    for other in ROUTES:
        script.run(other, 2)
    assert {route for route in ROUTES.values() if route in script.global_flags} == {
        flag
    }
    assert not script.condition(script.triggers["STALKER_2011_unresolved"], 2)
    assert "STALKER_2011_resolved" not in script.global_flags
    assert script.events.count((2, "STALKER.173")) == 1


@pytest.mark.parametrize("flag", ROUTES.values())
@pytest.mark.parametrize("effect", ROUTES)
def test_existing_route_state_blocks_every_later_resolution(flag, effect):
    script = _script()
    script.global_flags[flag] = None
    before = script.countries[698]["vars"].copy()
    script.run(effect, 2)
    assert script.countries[698]["vars"] == before
    assert not script.events


@pytest.mark.parametrize("entry", ["relay", "monthly"])
def test_turned_back_route_skips_the_raid_after_a_lost_carrier(entry):
    script = _script()
    script.global_flags["STALKER_strelok_turned_back"] = None
    script.global_flags["STALKER_2012_dispatched"] = None
    script.countries[2]["exists"] = False
    script.countries[698]["controller"] = 3
    script.actor = 3
    script.goto(2012, 4)
    if entry == "relay":
        relay = next(
            body
            for key, _, body in _event("STALKER.160", "events/STALKER_strelok.txt")
            if key == "immediate"
        )
        script.execute(relay, 3)
    else:
        script.run("STALKER_monthly_strelok_pulse", 3)
    assert "STALKER_2012_resolved" in script.global_flags
    assert "STALKER_fairway_scheduled" in script.global_flags
    assert script.events.count((3, "STALKER.162")) == 1
    assert not any(event == "STALKER.161" for _, event in script.events)
    before = script.events.copy()
    script.run("STALKER_begin_strelok_raid", 3)
    script.run("STALKER_monthly_strelok_pulse", 3)
    assert script.events == before
    script.goto(2012, 7, 29)
    script.run("STALKER_monthly_legend_pulse", 3)
    assert (3, "STALKER.174") not in script.events
    script.goto(2012, 7, 30)
    script.run("STALKER_monthly_legend_pulse", 3)
    assert script.events.count((3, "STALKER.174")) == 1


@pytest.mark.parametrize(
    "event_id,index",
    [
        (event, index)
        for event, count in [(172, 3), (174, 6), (176, 4)]
        for index in range(count)
    ],
)
@pytest.mark.parametrize("invalid", ["controller", "zone_id", "inactive", None])
def test_legend_choices_revalidate_the_current_original_zone(event_id, index, invalid):
    script = _script()
    option = [
        body
        for key, _, body in _event(f"STALKER.{event_id}", "events/STALKER_legend.txt")
        if key == "option"
    ][index]
    if invalid == "controller":
        script.countries[698]["controller"] = 3
    elif invalid == "zone_id":
        script.countries[698]["vars"]["STALKER_zone_id"] = 2
    elif invalid == "inactive":
        script.triggers["STALKER_is_active_zone_anchor"] = [("always", "=", "no")]
    before = script.countries[698]["vars"].copy()
    flags = script.global_flags.copy()
    globals_before = script.globals.copy()
    trigger = next(body for key, _, body in option if key == "trigger")
    hidden = next(body for key, _, body in option if key == "hidden_effect")
    if invalid:
        assert not script.condition(trigger, script.actor)
    script.execute(hidden, script.actor)
    if invalid:
        assert script.countries[698]["vars"] == before
        assert script.global_flags == flags
        assert script.globals == globals_before
        assert not script.events
    else:
        assert script.events
        resolved = (
            script.global_flags.copy(),
            script.globals.copy(),
            script.events.copy(),
        )
        script.execute(hidden, script.actor)
        assert (script.global_flags, script.globals, script.events) == resolved


def test_monthly_entry_point_wires_both_durable_story_recoveries_once():
    pulse = _parse_race_script(
        (ROOT / "common/scripted_effects/99_STALKER_pulse_effects.txt").read_text(
            encoding="utf-8"
        )
    )["STALKER_monthly_pulse"]
    assert pulse.count(("STALKER_monthly_strelok_pulse", "=", "yes")) == 1
    assert pulse.count(("STALKER_monthly_legend_pulse", "=", "yes")) == 1
