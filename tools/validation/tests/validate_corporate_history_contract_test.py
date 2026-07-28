import json
from pathlib import Path

from validate_corporate_history_contract import Validator


def _write(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(
    callerless=None,
    allowed_reads=None,
    with_other_chain=False,
    variables=None,
    allow_multiple_completion_producers=False,
):
    chains = [
        {
            "name": "TestCo",
            "tag": "USA",
            "namespace": "USA_test_events",
            "root": "USA_test",
            "tier": 1,
            "owned_prefixes": ["USA_test"],
            "variables": (
                {"USA_test_state": {"min": 0, "max": 10}}
                if variables is None
                else variables
            ),
            "outcome_idea_prefixes": ["USA_test_outcome_"],
            "requires_current_year_scheduler": True,
            "allow_yearly_scheduler_duplicates": True,
            "callerless_anchors": callerless or [],
            "allowed_multiple_callers": [],
            "allowed_reads": allowed_reads or [],
            "allowed_writes": [],
            "allow_multiple_completion_producers": allow_multiple_completion_producers,
        }
    ]
    if with_other_chain:
        chains.append(
            {
                "name": "OtherCo",
                "tag": "USA",
                "namespace": "USA_other_events",
                "root": "USA_other",
                "tier": 2,
                "owned_prefixes": ["USA_other"],
                "variables": {},
                "outcome_idea_prefixes": [],
                "requires_current_year_scheduler": False,
                "allow_yearly_scheduler_duplicates": False,
                "callerless_anchors": [],
                "allowed_multiple_callers": [],
                "allowed_reads": [],
                "allowed_writes": [],
            }
        )
    return {"chains": chains}


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


def _base_core_effects(monthly_registration=True, startup_reconstructs=False):
    startup_body = (
        "USA_test_reconstruct_history = yes"
        if startup_reconstructs
        else "country_event = { id = USA_test_events.90 days = 1 }"
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
    reconstruct_body=None,
    startup_reconstructs=False,
    manifest_overrides=None,
    cross_chain_reads=(),
    cross_chain_trigger_reads=(),
    cross_chain_effect_calls=(),
    cleanup_in_option=False,
    drop_cleanup_effect=False,
    drop_state_effects=False,
    allow_multiple_completion_producers=False,
    extra_effects="",
):
    manifest = _manifest(
        callerless,
        allow_multiple_completion_producers=allow_multiple_completion_producers,
        **(manifest_overrides or {}),
    )
    _write(root, "tools/corporate_history_contract.json", json.dumps(manifest))
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
        _base_core_effects(
            monthly_registration=monthly_registration,
            startup_reconstructs=startup_reconstructs,
        ),
    )
    _write(
        root,
        "common/scripted_effects/00_corporate_history_dispatch_effects.txt",
        _base_dispatch(duplicate=duplicate_dispatch),
    )
    _write(root, "common/scripted_effects/00_yearly_effects.txt", _base_yearly())
    effects = _base_effects()
    if reconstruct_body is not None:
        head, _sep, _tail = effects.partition("USA_test_reconstruct_history = {")
        effects = f"{head}USA_test_reconstruct_history = {{\n{reconstruct_body}}}\n"
    if drop_state_effects:
        head, _sep, tail = effects.partition(
            "USA_test_schedule_current_year_events = {"
        )
        del head
        effects = "USA_test_schedule_current_year_events = {" + tail
        effects = effects.replace("\tUSA_test_clamp_state = yes\n", "")
    if cleanup_in_option or drop_cleanup_effect:
        effects = effects.replace(
            "USA_test_clear_capstone_outcome = {\n"
            "\tremove_ideas = {\n"
            "\t\tUSA_test_outcome_a\n"
            "\t\tUSA_test_outcome_b\n"
            "\t}\n"
            "}\n\n",
            "",
        ).replace("\tUSA_test_clear_capstone_outcome = yes\n", "")
    if treasury_in_reconstruct:
        effects = effects.replace(
            "\t\tset_country_flag = USA_test_branch_a\n",
            "\t\tset_country_flag = USA_test_branch_a\n\t\tmodify_treasury_effect = yes\n",
        )
    if duplicate_complete:
        effects += "\nUSA_test_extra_complete = {\n\tset_country_flag = USA_test_reconstruct_complete\n}\n"
    if extra_effects:
        effects += "\n" + extra_effects
    _write(root, "common/scripted_effects/USA_test_effects.txt", effects)
    _write(
        root,
        "common/on_actions/MD_event_on_actions.txt",
        "on_monthly_USA = { effect = { USA_corporate_history_monthly_outcomes = yes } }\n",
    )
    events = _base_events(
        include_hidden_ninety=include_hidden_ninety, include_anchor=include_anchor
    )
    if missing_clamp or drop_state_effects:
        events = events.replace("\n\t\t\tUSA_test_clamp_state = yes", "")
    if cleanup_in_option:
        events = events.replace(
            "\t\tname = USA_test_events.1.a\n",
            "\t\tname = USA_test_events.1.a\n"
            "\t\tremove_ideas = {\n"
            "\t\t\tUSA_test_outcome_a\n"
            "\t\t\tUSA_test_outcome_b\n"
            "\t\t}\n",
        )
    if cross_chain_reads or cross_chain_trigger_reads:
        flag_reads = [f"\t\t\thas_country_flag = {flag}" for flag in cross_chain_reads]
        trigger_reads = [
            f"\t\t\tmodifier = {{ add = 5 {trigger} = yes }}"
            for trigger in cross_chain_trigger_reads
        ]
        reads = "\n".join(flag_reads + trigger_reads)
        events = events.replace(
            "\t\tname = USA_test_events.1.a\n",
            f"\t\tname = USA_test_events.1.a\n\t\tai_chance = {{\n\t\t\tbase = 10\n{reads}\n\t\t}}\n",
        )
    if cross_chain_effect_calls:
        calls = "\n".join(f"\t\t{effect} = yes" for effect in cross_chain_effect_calls)
        events = events.replace(
            "\t\tname = USA_test_events.1.a\n",
            f"\t\tname = USA_test_events.1.a\n{calls}\n",
        )
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


def test_recovery_helper_routed_through_the_scheduler_keeps_the_caller_pair(tmp_path):
    """Lost-delivery recovery must re-enter the scheduler, not fire the event itself.

    Nintendo and AIG recover a missed delivery from their monthly driver. Routing that
    through the current-year scheduler keeps the permitted dispatcher + scheduler pair;
    a helper that queued the event directly would silently become a third caller.
    """
    _build_fixture(
        tmp_path,
        extra_effects=(
            "USA_test_recover_missing_events = {\n"
            "\tif = {\n"
            "\t\tlimit = { NOT = { has_country_flag = USA_test_branch_a } }\n"
            "\t\tUSA_test_schedule_current_year_events = yes\n"
            "\t}\n"
            "}\n"
        ),
    )
    messages = _messages(tmp_path)
    assert not any("multiple direct callers" in message for message in messages)


def test_recovery_helper_firing_the_event_directly_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        extra_effects=(
            "USA_test_recover_missing_events = {\n"
            "\tif = {\n"
            "\t\tlimit = { NOT = { has_country_flag = USA_test_branch_a } }\n"
            "\t\tcountry_event = { id = USA_test_events.1 days = 5 }\n"
            "\t}\n"
            "}\n"
        ),
    )
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.1 has multiple direct callers" in message
        for message in messages
    )


def test_tier_one_missing_hidden_ninety(tmp_path):
    _build_fixture(tmp_path, include_hidden_ninety=False)
    messages = _messages(tmp_path)
    assert any(
        "USA_test_events.90 is missing or not hidden and "
        "USA_test_reconstruct_history is not called directly from "
        "corporate_history_on_startup" in message
        for message in messages
    )


def test_tier_one_startup_reconstruct_replaces_hidden_ninety(tmp_path):
    _build_fixture(tmp_path, include_hidden_ninety=False, startup_reconstructs=True)
    assert _messages(tmp_path) == []


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


_COMPLETE_BRANCH = """\tif = {
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
"""


def _reconstruct(branch: str) -> str:
    return branch + _COMPLETE_BRANCH


_UNGUARDED_MESSAGE = (
    "USA_test_reconstruct_history has a state-changing block "
    "without sibling-marker guards"
)


def _guarded_branch(limit_body: str) -> str:
    return (
        "\tif = {\n"
        "\t\tlimit = {\n"
        "\t\t\tdate > 2001.2.1\n"
        f"{limit_body}"
        "\t\t}\n"
        "\t\tset_country_flag = USA_test_branch_a\n"
        "\t\tadd_to_variable = { USA_test_state = 1 }\n"
        "\t\tUSA_test_clamp_state = yes\n"
        "\t}\n"
    )


def test_direct_negative_flag_guard_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch("\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n")
        ),
    )
    assert _messages(tmp_path) == []


def test_direct_negative_idea_guard_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch("\t\t\tNOT = { has_idea = USA_test_outcome_a }\n")
        ),
    )
    assert _messages(tmp_path) == []


def test_negated_or_flag_set_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tOR = {\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == []


def test_negated_or_mixed_flag_and_idea_set_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tOR = {\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\t\thas_idea = USA_test_outcome_a\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == []


def test_positive_or_marker_set_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tOR = {\n"
                "\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_double_negated_marker_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_marker_guarding_another_country_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tCAN = { NOT = { has_country_flag = USA_test_branch_a } }\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_marker_only_in_the_effect_body_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            "\tif = {\n"
            "\t\tlimit = { date > 2001.2.1 }\n"
            "\t\tcustom_effect_tooltip = USA_test_branch_a_tt\n"
            "\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
            "\t\tset_country_flag = USA_test_branch_a\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_date_only_state_changing_branch_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(_guarded_branch("")),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_branch_without_a_limit_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            "\tif = {\n"
            "\t\tset_country_flag = USA_test_branch_a\n"
            "\t\tadd_to_variable = { USA_test_state = 1 }\n"
            "\t\tUSA_test_clamp_state = yes\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == [
        "USA_test_reconstruct_history has a state-changing block without a date guard",
        _UNGUARDED_MESSAGE,
    ]


def test_variable_only_mutation_still_needs_a_marker_guard(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            "\tif = {\n"
            "\t\tlimit = { date > 2001.2.1 }\n"
            "\t\tadd_to_variable = { USA_test_state = 1 }\n"
            "\t\tUSA_test_clamp_state = yes\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_declared_cross_chain_read_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_qnx_stack"],
        },
        cross_chain_reads=["USA_other_qnx_stack"],
    )
    assert _messages(tmp_path) == []


def test_cross_chain_exception_does_not_cover_prefix_neighbours(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_qnx_stack"],
        },
        cross_chain_reads=["USA_other_qnx_stack", "USA_other_qnx_stack_v2"],
    )
    assert _messages(tmp_path) == [
        "TestCo has undeclared cross-chain read-only AI/flavour use of "
        "USA_other_qnx_stack_v2, owned by OtherCo"
    ]


def test_declared_cross_chain_scripted_trigger_read_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_administration"],
        },
        cross_chain_trigger_reads=["USA_other_administration"],
    )
    assert _messages(tmp_path) == []


def test_undeclared_cross_chain_scripted_trigger_read_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"with_other_chain": True},
        cross_chain_trigger_reads=["USA_other_administration"],
    )
    assert _messages(tmp_path) == [
        "TestCo has undeclared cross-chain read-only AI/flavour use of "
        "USA_other_administration, owned by OtherCo"
    ]


def test_cross_chain_effect_call_remains_a_write(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={
            "with_other_chain": True,
            "allowed_reads": ["USA_other_administration"],
        },
        cross_chain_effect_calls=["USA_other_administration"],
    )
    assert _messages(tmp_path) == [
        "TestCo writes USA_other_administration, owned by OtherCo, "
        "outside declared exceptions"
    ]


def test_flag_state_chain_needs_no_initialize_or_clamp_effect(tmp_path):
    _build_fixture(
        tmp_path, manifest_overrides={"variables": {}}, drop_state_effects=True
    )
    assert _messages(tmp_path) == []


def test_bounded_state_chain_still_needs_initialize_and_clamp_effects(tmp_path):
    _build_fixture(tmp_path, drop_state_effects=True)
    messages = _messages(tmp_path)
    assert "TestCo is missing its initialization effect" in messages
    assert "TestCo is missing its clamp effect" in messages


def test_reconstruction_that_never_lands_an_outcome_has_no_terminal_resolver(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=(
            "\tif = {\n"
            "\t\tlimit = {\n"
            "\t\t\tdate > 2001.2.1\n"
            "\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
            "\t\t}\n"
            "\t\tset_country_flag = USA_test_branch_a\n"
            "\t}\n"
            "\tif = {\n"
            "\t\tlimit = { date > 2001.3.1 }\n"
            "\t\tset_country_flag = USA_test_reconstruct_complete\n"
            "\t}\n"
        ),
    )
    assert _messages(tmp_path) == ["TestCo is missing a terminal resolver effect"]


def test_capstone_cleanup_may_live_in_the_event_option(tmp_path):
    _build_fixture(tmp_path, cleanup_in_option=True)
    assert _messages(tmp_path) == []


def test_chain_without_any_capstone_cleanup_is_reported(tmp_path):
    _build_fixture(tmp_path, drop_cleanup_effect=True)
    assert _messages(tmp_path) == [
        "TestCo is missing a mutually exclusive cleanup effect"
    ]


def test_bare_multi_child_not_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]


def test_separate_negated_markers_are_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = { has_country_flag = USA_test_branch_a }\n"
                "\t\t\tNOT = { has_country_flag = USA_test_branch_b }\n"
            )
        ),
    )
    assert _messages(tmp_path) == []


def test_negated_and_marker_set_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        reconstruct_body=_reconstruct(
            _guarded_branch(
                "\t\t\tNOT = {\n"
                "\t\t\t\tAND = {\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_a\n"
                "\t\t\t\t\thas_country_flag = USA_test_branch_b\n"
                "\t\t\t\t}\n"
                "\t\t\t}\n"
            )
        ),
    )
    assert _messages(tmp_path) == [_UNGUARDED_MESSAGE]
