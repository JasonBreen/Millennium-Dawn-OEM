import json
import re
from pathlib import Path

from validate_corporate_history_contract import (
    _BLOCK_IDENTIFIER,
    _TOP_LEVEL_BLOCK_RE,
    Validator,
)


def _write(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(callerless=None, allow_multiple_completion_producers=False):
    return {
        "chains": [
            {
                "name": "TestCo",
                "tag": "USA",
                "namespace": "USA_test_events",
                "root": "USA_test",
                "tier": 1,
                "owned_prefixes": ["USA_test"],
                "variables": {"USA_test_state": {"min": 0, "max": 10}},
                "outcome_idea_prefixes": ["USA_test_outcome_"],
                "requires_current_year_scheduler": True,
                "allow_yearly_scheduler_duplicates": True,
                "callerless_anchors": callerless or [],
                "allowed_multiple_callers": [],
                "allowed_reads": [],
                "allowed_writes": [],
                "allow_multiple_completion_producers": allow_multiple_completion_producers,
            }
        ]
    }


def _base_events(include_hidden_ninety=True, include_anchor=False):
    blocks = [
        """add_namespace = USA_test_events

country_event = {
\tid = USA_test_events.1
\ttitle = USA_test_events.1.t
\tdesc = USA_test_events.1.d
\tpicture = GFX_test
\tis_triggered_only = yes
\toption = {
\t\tname = USA_test_events.1.a
\t\thidden_effect = {
\t\t\tadd_to_variable = { USA_test_state = 1 }
\t\t\tUSA_test_clamp_state = yes
\t\t}
\t}
}
""".strip()
    ]
    if include_anchor:
        blocks.append(
            """
country_event = {
\tid = USA_test_events.2
\ttitle = USA_test_events.2.t
\tdesc = USA_test_events.2.d
\tpicture = GFX_test
\tis_triggered_only = yes
\toption = { name = USA_test_events.2.a }
}
""".strip()
        )
    if include_hidden_ninety:
        blocks.append(
            """
country_event = {
\tid = USA_test_events.90
\thidden = yes
\tis_triggered_only = yes
\tfire_only_once = yes
\timmediate = { USA_test_reconstruct_history = yes }
}
""".strip()
        )
    return "\n\n".join(blocks) + "\n"


def _base_effects():
    return """USA_test_initialize_state = {
\tif = {
\t\tlimit = { NOT = { has_country_flag = USA_test_state_initialized } }
\t\tset_variable = { USA_test_state = 0 }
\t\tset_country_flag = USA_test_state_initialized
\t}
\tUSA_test_clamp_state = yes
}

USA_test_clamp_state = {
\tclamp_variable = { var = USA_test_state min = 0 max = 10 }
}

USA_test_schedule_current_year_events = {
\tif = {
\t\tlimit = {
\t\t\tNOT = { has_start_date < 2001.1.1 }
\t\t\thas_start_date < 2001.1.2
\t\t}
\t\tcountry_event = { id = USA_test_events.1 days = 10 }
\t}
}

USA_test_clear_capstone_outcome = {
\tremove_ideas = {
\t\tUSA_test_outcome_a
\t\tUSA_test_outcome_b
\t}
}

USA_test_resolve_capstone = {
\tUSA_test_clear_capstone_outcome = yes
\tadd_ideas = USA_test_outcome_a
\tset_country_flag = USA_test_outcome_a_resolved
}

USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tNOT = { has_country_flag = USA_test_branch_a }
\t\t\tNOT = { has_country_flag = USA_test_branch_b }
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.3.1
\t\t\tNOT = { has_idea = USA_test_outcome_a }
\t\t\tNOT = { has_idea = USA_test_outcome_b }
\t\t}
\t\tUSA_test_resolve_capstone = yes
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _base_core_effects(monthly_registration=True, startup_uses_hidden=True):
    startup_body = (
        "country_event = { id = USA_test_events.90 days = 1 }"
        if startup_uses_hidden
        else "country_event = { id = USA_test_events.1 days = 1 }"
    )
    monthly_call = (
        "\t\tUSA_test_reconstruct_history = yes\n" if monthly_registration else ""
    )
    return f"""corporate_history_on_startup = {{
\tif = {{
\t\tlimit = {{ corporate_history_full_enabled = yes }}
\t\tif = {{
\t\t\tlimit = {{ country_exists = USA }}
\t\t\tUSA = {{
\t\t\t\tUSA_test_schedule_current_year_events = yes
\t\t\t\t{startup_body}
\t\t\t}}
\t\t}}
\t}}
\telse_if = {{
\t\tlimit = {{ corporate_history_outcomes_only_enabled = yes }}
\t\tif = {{
\t\t\tlimit = {{ country_exists = USA }}
\t\t\tUSA = {{ USA_test_reconstruct_history = yes }}
\t\t}}
\t}}
}}

USA_corporate_history_monthly_outcomes = {{
\tif = {{
\t\tlimit = {{
\t\t\tcorporate_history_outcomes_only_enabled = yes
\t\t\toriginal_tag = USA
\t\t\tNOT = {{ has_country_flag = collapsed_nation }}
\t\t\tNOT = {{ has_country_flag = USA_test_reconstruct_complete }}
\t\t}}
{monthly_call}\t}}
}}
"""


def _base_dispatch(duplicate=False):
    extra = (
        "\n\t\t\tcountry_event = { id = USA_test_events.1 days = 20 }"
        if duplicate
        else ""
    )
    return f"""USA_corporate_trigger_year_2001 = {{
\tif = {{
\t\tlimit = {{
\t\t\tcountry_exists = USA
\t\t\tcorporate_history_full_enabled = yes
\t\t}}
\t\tUSA = {{
\t\t\tcountry_event = {{ id = USA_test_events.1 days = 10 }}{extra}
\t\t}}
\t}}
}}
"""


def _base_yearly():
    return """startup_events = {
\tcorporate_history_on_startup = yes
}

trigger_year_2001_events = {
\tUSA_corporate_trigger_year_2001 = yes
}
"""


def _base_ideas(missing_civil_war=False):
    civ = "" if missing_civil_war else "\t\t\tallowed_civil_war = { always = yes }\n"
    return f"""ideas = {{
\tcountry = {{
\t\tUSA_test_outcome_a = {{
\t\t\tpicture = GFX_test
\t\t\tallowed = {{ original_tag = USA }}
{civ}\t\t}}

\t\tUSA_test_outcome_b = {{
\t\t\tpicture = GFX_test
\t\t\tallowed = {{ original_tag = USA }}
\t\t\tallowed_civil_war = {{ always = yes }}
\t\t}}
\t}}
}}
"""


def _build_fixture(
    root: Path,
    *,
    callerless=None,
    include_hidden_ninety=True,
    include_anchor=False,
    monthly_registration=True,
    duplicate_dispatch=False,
    missing_clamp=False,
    treasury_in_reconstruct=False,
    duplicate_complete=False,
    missing_civil_war=False,
    reconstruct_effect_override=None,
    allow_multiple_completion_producers=False,
):
    _write(
        root,
        "tools/corporate_history_contract.json",
        json.dumps(
            _manifest(
                callerless,
                allow_multiple_completion_producers=allow_multiple_completion_producers,
            )
        ),
    )
    _write(
        root,
        "common/scripted_triggers/MD_corporate_history_triggers.txt",
        """corporate_history_full_enabled = { always = yes }
corporate_history_outcomes_only_enabled = { always = no }
""",
    )
    _write(
        root,
        "common/game_rules/00_game_rules.txt",
        "rule_corporate_history = { default = { name = full } }\n",
    )
    _write(
        root,
        "common/scripted_effects/00_corporate_history_effects.txt",
        _base_core_effects(monthly_registration=monthly_registration),
    )
    _write(
        root,
        "common/scripted_effects/00_corporate_history_dispatch_effects.txt",
        _base_dispatch(duplicate=duplicate_dispatch),
    )
    _write(root, "common/scripted_effects/00_yearly_effects.txt", _base_yearly())
    effects = _base_effects()
    if reconstruct_effect_override is not None:
        effects = reconstruct_effect_override
    if treasury_in_reconstruct:
        effects = effects.replace(
            "\t\tset_country_flag = USA_test_branch_a\n",
            "\t\tset_country_flag = USA_test_branch_a\n\t\tmodify_treasury_effect = yes\n",
        )
    if duplicate_complete:
        effects += "\nUSA_test_extra_complete = {\n\tset_country_flag = USA_test_reconstruct_complete\n}\n"
    _write(root, "common/scripted_effects/USA_test_effects.txt", effects)
    _write(
        root,
        "common/on_actions/MD_event_on_actions.txt",
        "on_monthly_USA = { effect = { USA_corporate_history_monthly_outcomes = yes } }\n",
    )
    events = _base_events(
        include_hidden_ninety=include_hidden_ninety, include_anchor=include_anchor
    )
    if missing_clamp:
        events = events.replace("\n\t\t\tUSA_test_clamp_state = yes", "")
    _write(root, "events/USA_test_events.txt", events)
    _write(root, "common/ideas/USA_test_ideas.txt", _base_ideas(missing_civil_war))


def _messages(root: Path):
    validator = Validator(
        mod_path=str(root), use_colors=False, workers=1, no_cache=True
    )
    validator.run_all_validations()
    return [issue.message for issue in validator._issues]


def test_visible_event_with_no_caller(tmp_path):
    _build_fixture(tmp_path, include_anchor=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.2 has no direct callers" in message for message in messages
    )


def test_duplicate_dispatch_caller(tmp_path):
    _build_fixture(tmp_path, duplicate_dispatch=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_corporate_trigger_year_2001 schedules USA_test_events.1 2 times" in message
        for message in messages
    )


def test_tier_one_missing_hidden_ninety(tmp_path):
    _build_fixture(tmp_path, include_hidden_ninety=False)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.90 is missing or not hidden" in message for message in messages
    )


def test_tier_one_missing_monthly_outcomes_registration(tmp_path):
    _build_fixture(tmp_path, monthly_registration=False)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_reconstruct_history is not called from USA_corporate_history_monthly_outcomes"
        in message
        for message in messages
    )


def test_option_mutating_bounded_variable_without_clamp(tmp_path):
    _build_fixture(tmp_path, missing_clamp=True)
    messages = _messages(tmp_path)
    assert any(
        "mutates bounded variables without a later USA_test_clamp_state call" in message
        for message in messages
    )


def test_reconstruction_replaying_treasury(tmp_path):
    _build_fixture(tmp_path, treasury_in_reconstruct=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_reconstruct_history replays treasury changes" in message
        for message in messages
    )


def test_duplicate_reconstruct_complete_producers(tmp_path):
    _build_fixture(tmp_path, duplicate_complete=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_reconstruct_complete has 2 producers" in message
        for message in messages
    )


def test_allowed_duplicate_reconstruct_complete_producers(tmp_path):
    _build_fixture(
        tmp_path,
        duplicate_complete=True,
        allow_multiple_completion_producers=True,
    )
    messages = _messages(tmp_path)
    assert not any(
        "USA_test_reconstruct_complete has 2 producers" in message
        for message in messages
    )


def test_outcome_idea_missing_allowed_civil_war(tmp_path):
    _build_fixture(tmp_path, missing_civil_war=True)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_outcome_a is missing allowed_civil_war = { always = yes }" in message
        for message in messages
    )


def test_valid_minimal_tier_one_fixture(tmp_path):
    _build_fixture(tmp_path)
    assert _messages(tmp_path) == []


def test_explicitly_allowed_custom_anchor(tmp_path):
    _build_fixture(tmp_path, include_anchor=True, callerless=["USA_test_events.2"])
    messages = _messages(tmp_path)
    assert not any(
        "USA_test_events.2 has no direct callers" in message for message in messages
    )


# ============================================================================
# Reconstruction safety marker-guard tests
# ============================================================================


def _reconstruct_with_direct_negative_flag_guard():
    """Valid: direct negative country-flag guard."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tNOT = { has_country_flag = USA_test_branch_a }
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_direct_negative_idea_guard():
    """Valid: direct negative idea guard."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tNOT = { has_idea = USA_test_outcome_a }
\t\t}
\t\tUSA_test_resolve_capstone = yes
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_not_or_flag_set():
    """Valid: NOT -> OR flag set."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tNOT = {
\t\t\t\tOR = {
\t\t\t\t\thas_country_flag = USA_test_branch_a
\t\t\t\t\thas_country_flag = USA_test_branch_b
\t\t\t\t}
\t\t\t}
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_not_or_mixed_flag_idea_set():
    """Valid: mixed flag/idea NOT -> OR set."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tNOT = {
\t\t\t\tOR = {
\t\t\t\t\thas_country_flag = USA_test_branch_a
\t\t\t\t\thas_idea = USA_test_outcome_a
\t\t\t\t}
\t\t\t}
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_positive_or():
    """Invalid: positive OR (not negated)."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t\tOR = {
\t\t\t\thas_country_flag = USA_test_branch_a
\t\t\t\thas_country_flag = USA_test_branch_b
\t\t\t}
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_marker_only_after_limit():
    """Invalid: marker present only after the limit (in effect body)."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t}
\t\tNOT = { has_country_flag = USA_test_branch_a }
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_nested_marker_guard_only():
    """Invalid: nested limit guard does not cover the outer state change."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t}
\t\tif = {
\t\t\tlimit = { NOT = { has_country_flag = USA_test_branch_a } }
\t\t\tset_country_flag = USA_test_branch_b
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_top_level_date_and_nested_marker_only():
    """Invalid: nested marker guards do not count without a top-level limit."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tdate > 2001.2.1
\t\tif = {
\t\t\tlimit = { NOT = { has_country_flag = USA_test_branch_a } }
\t\t\tset_country_flag = USA_test_branch_b
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_date_only():
    """Invalid: date-only state-changing branch."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def _reconstruct_with_unguarded_state_change():
    """Invalid: genuinely unguarded reconstruction fixture."""
    return """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = {
\t\t\tdate > 2001.2.1
\t\t}
\t\tset_country_flag = USA_test_branch_a
\t\tadd_to_variable = { USA_test_state = 1 }
\t}
\tif = {
\t\tlimit = { date > 2001.3.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}
"""


def test_valid_direct_negative_flag_guard(tmp_path):
    """Test that direct negative flag guards are accepted."""
    _build_fixture(
        tmp_path,
        reconstruct_effect_override=_reconstruct_with_direct_negative_flag_guard(),
    )
    messages = _messages(tmp_path)
    assert not any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_block_header_regex_accepts_closing_brackets():
    assert _TOP_LEVEL_BLOCK_RE.search("header] = {")
    assert re.findall(r"(" + _BLOCK_IDENTIFIER + r")\s*=\s*\{", "header] = {") == [
        "header]"
    ]


def test_reconstruct_override_accepts_empty_string(tmp_path):
    _build_fixture(tmp_path, reconstruct_effect_override="")
    assert (tmp_path / "common/scripted_effects/USA_test_effects.txt").read_text(
        encoding="utf-8"
    ) == ""


def test_valid_direct_negative_idea_guard(tmp_path):
    """Test that direct negative idea guards are accepted."""
    _build_fixture(
        tmp_path,
        reconstruct_effect_override=_reconstruct_with_direct_negative_idea_guard(),
    )
    messages = _messages(tmp_path)
    assert not any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_valid_not_or_flag_set(tmp_path):
    """Test that NOT -> OR flag sets are accepted."""
    _build_fixture(
        tmp_path, reconstruct_effect_override=_reconstruct_with_not_or_flag_set()
    )
    messages = _messages(tmp_path)
    assert not any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_valid_not_or_mixed_flag_idea_set(tmp_path):
    """Test that mixed flag/idea NOT -> OR sets are accepted."""
    _build_fixture(
        tmp_path,
        reconstruct_effect_override=_reconstruct_with_not_or_mixed_flag_idea_set(),
    )
    messages = _messages(tmp_path)
    assert not any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_invalid_positive_or(tmp_path):
    """Test that positive-only OR blocks are rejected."""
    _build_fixture(
        tmp_path, reconstruct_effect_override=_reconstruct_with_positive_or()
    )
    messages = _messages(tmp_path)
    assert any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_invalid_marker_only_after_limit(tmp_path):
    """Test that markers appearing only after the limit are rejected."""
    _build_fixture(
        tmp_path,
        reconstruct_effect_override=_reconstruct_with_marker_only_after_limit(),
    )
    messages = _messages(tmp_path)
    assert any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_invalid_nested_marker_guard_only(tmp_path):
    """Test that nested marker guards do not validate the outer state change."""
    _build_fixture(
        tmp_path,
        reconstruct_effect_override=_reconstruct_with_nested_marker_guard_only(),
    )
    messages = _messages(tmp_path)
    assert any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_invalid_nested_marker_guard_without_top_level_limit(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_effect_override=_reconstruct_with_top_level_date_and_nested_marker_only(),
    )
    messages = _messages(tmp_path)
    assert any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_invalid_date_only(tmp_path):
    """Test that date-only state-changing branches are rejected."""
    _build_fixture(tmp_path, reconstruct_effect_override=_reconstruct_with_date_only())
    messages = _messages(tmp_path)
    assert any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )


def test_invalid_unguarded_reconstruction(tmp_path):
    """Test that genuinely unguarded reconstruction fixtures are rejected."""
    _build_fixture(
        tmp_path, reconstruct_effect_override=_reconstruct_with_unguarded_state_change()
    )
    messages = _messages(tmp_path)
    assert any(
        "state-changing block without sibling-marker guards" in message
        for message in messages
    )
