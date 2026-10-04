import re
from datetime import date
from pathlib import Path

import pytest
from ai_race_state_model_test import (
    EFFECTS_PATH,
    PROGRESSION_PATH,
    UPSTREAM_PREFIXES,
    _extract_block,
    _named_block,
    _variable_write_targets,
)

ROOT = Path(__file__).resolve().parents[2]
LAB_EFFECTS_PATH = ROOT / "common" / "scripted_effects" / "USA_ai_race_lab_effects.txt"
LAB_EVENTS_PATH = ROOT / "events" / "USA_ai_race_lab_events.txt"
USA_LOC_PATH = ROOT / "localisation" / "english" / "MD_focus_USA_l_english.yml"
OPINION_PATH = (
    ROOT / "common" / "opinion_modifiers" / "00_ai_race_opinion_modifiers.txt"
)
OPINION_LOC_PATH = (
    ROOT / "localisation" / "english" / "MD_opinion_modifiers_l_english.yml"
)

OPENAI_MAPPING = (
    ("ai_race_capability_external", "USA_openai_frontier_capability"),
    ("ai_race_compute_external", "USA_openai_compute_independence"),
    ("ai_race_deployment_external", "USA_openai_deployment_reach"),
    ("ai_race_control_capacity_external", "USA_openai_mission_control"),
    ("ai_race_public_confidence_external", "USA_openai_safety_governance"),
)
PALANTIR_MAPPING = (
    ("ai_race_deployment_external", "USA_palantir_corporate_government_reach"),
    ("ai_race_deployment_external", "USA_palantir_corporate_commercial_reach"),
    (
        "ai_race_control_capacity_external",
        "USA_palantir_corporate_deployment_governance",
    ),
)
LAB_STATE_FLAGS = {
    "palantir": "USA_palantir_corporate_state_initialized",
    "openai": "USA_openai_state_initialized",
    "anthropic": "USA_anthropic_state_initialized",
}
# Each lab variable prefix and the clamp that bounds it to 0-10.
LAB_CLAMPS = {
    "USA_palantir_corporate_": "USA_palantir_corporate_clamp_state",
    "USA_openai_": "USA_openai_clamp_state",
    "USA_anthropic_": "USA_anthropic_clamp_state",
    "USA_xai_": "USA_xai_clamp_state",
}
EVENT_IDS = tuple(range(1, 10))


def _effects() -> str:
    return EFFECTS_PATH.read_text(encoding="utf-8")


def _lab_effects() -> str:
    return LAB_EFFECTS_PATH.read_text(encoding="utf-8")


def _events() -> dict[int, str]:
    text = LAB_EVENTS_PATH.read_text(encoding="utf-8")
    events = {}
    for match in re.finditer(r"(?m)^country_event = \{", text):
        block = _extract_block(text, match.start())
        event_id = int(re.search(r"id = USA_ai_race_lab\.(\d+)", block).group(1))
        assert event_id not in events, event_id
        events[event_id] = block
    return events


def _options(event: str) -> list[str]:
    return [
        _extract_block(event, match.start())
        for match in re.finditer(r"(?m)^\toption = \{", event)
    ]


def _branches(try_block: str) -> list[dict]:
    """Each dated branch of a try effect, in source order."""
    branches = []
    for match in re.finditer(r"(?m)^\t\t(?:if|else_if) = \{", try_block):
        branch = _extract_block(try_block, match.start())
        limit = _named_block(branch, "limit")
        year, month, day = map(
            int, re.search(r"date > (\d+)\.(\d+)\.(\d+)", limit).groups()
        )
        event_id = int(
            re.search(r"country_event = USA_ai_race_lab\.(\d+)", branch).group(1)
        )
        extra = re.findall(r"(?<!NOT = \{ )has_country_flag = (\w+)", limit)
        branches.append(
            {
                "after": date(year, month, day),
                "id": event_id,
                "extra_flags": tuple(extra),
                "fired_flag": f"USA_ai_race_lab_{event_id}_fired",
                "text": branch,
            }
        )
    return branches


def _try_blocks() -> dict[str, list[dict]]:
    text = _lab_effects()
    return {
        lab: _branches(_named_block(text, f"USA_ai_race_lab_try_{lab}"))
        for lab in LAB_STATE_FLAGS
    }


def _run_pulse(months, initialized):
    """Monthly model of USA_ai_race_lab_pulse: returns (month, event_id) firings."""
    fired, history = set(), []
    tries = _try_blocks()
    for month in months:
        sent = False
        for lab in ("palantir", "openai", "anthropic"):
            if sent or LAB_STATE_FLAGS[lab] not in initialized:
                continue
            for branch in tries[lab]:
                if month <= branch["after"] or branch["fired_flag"] in fired:
                    continue
                if not all(flag in initialized for flag in branch["extra_flags"]):
                    continue
                fired.add(branch["fired_flag"])
                history.append((month, branch["id"]))
                sent = True
                break
    return history


def _months(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current = date(current.year + current.month // 12, current.month % 12 + 1, 1)


ALL_LABS = set(LAB_STATE_FLAGS.values()) | {"USA_xai_state_initialized"}


@pytest.mark.parametrize(
    "name,mapping,weight",
    [
        ("ai_race_usa_openai_contribution", OPENAI_MAPPING, "2"),
        ("ai_race_usa_palantir_contribution", PALANTIR_MAPPING, None),
    ],
)
def test_lab_contribution_maps_exact_axes_and_only_adds_externals(
    name, mapping, weight
):
    block = _named_block(_effects(), name)
    for external, axis in mapping:
        expected = (
            f"add_to_variable = {{ {external} = {{ value = {axis} multiply = {weight} }} }}"
            if weight
            else f"add_to_variable = {{ {external} = {axis} }}"
        )
        assert block.count(expected) == 1, expected
    assert "corporate_history_enabled = yes" in block
    writes = _variable_write_targets(block)
    assert writes == {external for external, _ in mapping}, writes
    assert not any(target.startswith(UPSTREAM_PREFIXES) for target in writes)
    assert "set_variable" not in block


@pytest.mark.parametrize(
    "name", ["ai_race_usa_openai_contribution", "ai_race_usa_palantir_contribution"]
)
def test_lab_contribution_runs_on_both_usa_paths_inside_the_overlay(name):
    metrics = _named_block(_effects(), "ai_race_rebuild_country_metrics")
    assert metrics.count(f"{name} = yes") == 2
    # Each call sits between the national sample and the lab overlay, so the
    # dashboard attributes the lab's capability to the overlay.
    for call in re.finditer(rf"{name} = yes", metrics):
        before = metrics[: call.start()]
        after = metrics[call.end() :]
        assert before.rindex(
            "set_variable = { ai_race_capability_national_input"
        ) > before.rfind("ai_race_repair_country_state = yes")
        assert after.index(
            "set_variable = { ai_race_capability_lab_overlay"
        ) < after.index("ai_race_repair_country_state = yes")


def test_pulse_runs_once_for_the_usa_from_monthly_participant_work():
    progression = PROGRESSION_PATH.read_text(encoding="utf-8")
    monthly = _named_block(progression, "ai_race_run_monthly_work")
    hook = "if = { limit = { original_tag = USA } USA_ai_race_lab_pulse = yes }"
    assert monthly.count(hook) == 1
    loop = _named_block(monthly, "var:ai_race_participant")
    assert hook in loop
    assert progression.count("USA_ai_race_lab_pulse") == 1


def test_pulse_needs_full_corporate_history_and_a_live_country():
    pulse = _named_block(_lab_effects(), "USA_ai_race_lab_pulse")
    limit = _named_block(pulse, "limit")
    assert "corporate_history_full_enabled = yes" in limit
    assert "NOT = { has_country_flag = collapsed_nation }" in limit
    assert pulse.index("set_temp_variable = { usa_lab_fired = 0 }") < pulse.index(
        "USA_ai_race_lab_try_palantir = yes"
    )


def test_every_event_has_one_dated_branch_with_its_own_flag_in_date_order():
    tries = _try_blocks()
    seen = []
    for lab, branches in tries.items():
        assert branches, lab
        dates = [branch["after"] for branch in branches]
        assert dates == sorted(dates) and len(set(dates)) == len(dates), (lab, dates)
        try_block = _named_block(_lab_effects(), f"USA_ai_race_lab_try_{lab}")
        assert f"has_country_flag = {LAB_STATE_FLAGS[lab]}" in _named_block(
            try_block, "limit"
        )
        assert "check_variable = { usa_lab_fired = 0 }" in _named_block(
            try_block, "limit"
        )
        for branch in branches:
            text = branch["text"]
            assert f"NOT = {{ has_country_flag = {branch['fired_flag']} }}" in text
            assert text.count(f"set_country_flag = {branch['fired_flag']}") == 1
            assert "set_temp_variable = { usa_lab_fired = 1 }" in text
            seen.append(branch["id"])
    assert sorted(seen) == list(EVENT_IDS)
    assert set(_events()) == set(EVENT_IDS)


def test_event_triggers_match_their_dispatch_requirements():
    events = _events()
    for lab, branches in _try_blocks().items():
        for branch in branches:
            trigger = _named_block(events[branch["id"]], "trigger")
            assert "original_tag = USA" in trigger
            assert f"has_country_flag = {LAB_STATE_FLAGS[lab]}" in trigger
            for flag in branch["extra_flags"]:
                assert f"has_country_flag = {flag}" in trigger, (branch["id"], flag)


def test_a_full_run_fires_each_event_once_and_never_two_in_a_month():
    history = _run_pulse(_months(date(2024, 1, 1), date(2027, 12, 1)), ALL_LABS)
    assert sorted(event_id for _, event_id in history) == list(EVENT_IDS)
    months = [month for month, _ in history]
    assert len(months) == len(set(months))
    after = {
        branch["id"]: branch["after"]
        for branches in _try_blocks().values()
        for branch in branches
    }
    for month, event_id in history:
        assert month > after[event_id], (event_id, month)


def test_restructuring_waits_for_xai_without_blocking_the_talent_war():
    without_xai = ALL_LABS - {"USA_xai_state_initialized"}
    history = _run_pulse(_months(date(2025, 1, 1), date(2027, 12, 1)), without_xai)
    fired = [event_id for _, event_id in history]
    assert 5 not in fired
    assert 6 in fired


def test_an_uninitialized_lab_fires_nothing():
    history = _run_pulse(
        _months(date(2024, 1, 1), date(2027, 12, 1)),
        ALL_LABS - {"USA_palantir_corporate_state_initialized"},
    )
    assert not {1, 2, 3} & {event_id for _, event_id in history}


def test_every_option_has_ai_weight_and_every_key_has_english_text():
    loc = USA_LOC_PATH.read_text(encoding="utf-8-sig")
    keys = set(re.findall(r"(?m)^ (USA_ai_race_lab\.[\w.]+):", loc))
    for event_id, event in _events().items():
        for suffix in ("t", "d"):
            assert f"USA_ai_race_lab.{event_id}.{suffix}" in keys
        options = _options(event)
        assert len(options) >= 2, event_id
        for option in options:
            assert "ai_chance = {" in option
            name = re.search(r"name = (USA_ai_race_lab\.[\w.]+)", option).group(1)
            assert name in keys, name
            for tooltip in re.findall(r"custom_effect_tooltip = (\S+)", option):
                assert tooltip in keys, tooltip


def test_paid_options_weigh_bankruptcy_not_the_balance():
    paid = 0
    for event in _events().values():
        options = _options(event)
        for option in options:
            if not re.search(
                r"add_political_power = -|treasury_change = -|modify_treasury_effect",
                option,
            ):
                continue
            paid += 1
            weights = _named_block(option, "ai_chance")
            assert "has_active_mission = bankruptcy_incoming_collapse" in weights
            assert "has_political_power" not in weights
            assert "check_variable = { treasury" not in weights
        # Every event keeps an option the AI still takes when broke.
        free = [
            option
            for option in options
            if "bankruptcy_incoming_collapse" not in option
            and "trigger = {" not in option
        ]
        assert free
    assert paid == 2


def test_event_options_write_only_lab_state_and_clamp_every_write():
    for event_id, event in _events().items():
        for option in _options(event):
            writes = _variable_write_targets(option)
            assert not any(target.startswith("ai_race_") for target in writes), writes
            for prefix, clamp in LAB_CLAMPS.items():
                if any(target.startswith(prefix) for target in writes):
                    # The clamp follows the last write to that lab.
                    last_write = max(
                        option.rindex(target)
                        for target in writes
                        if target.startswith(prefix)
                    )
                    assert option.find(f"{clamp} = yes", last_write) != -1, (
                        event_id,
                        clamp,
                    )


def test_opinion_modifiers_used_by_the_events_are_defined_and_named():
    defined = set(
        re.findall(r"(?m)^\t(\w+) = \{", OPINION_PATH.read_text(encoding="utf-8"))
    )
    used = set()
    for event in _events().values():
        used.update(re.findall(r"modifier = (USA_ai_race_\w+)", event))
    assert used
    assert used <= defined, used - defined
    loc = OPINION_LOC_PATH.read_text(encoding="utf-8-sig")
    for modifier in defined:
        assert re.search(rf'(?m)^ {modifier}: "[^"]+"$', loc), modifier
