import json
from decimal import Decimal
from pathlib import Path

import pytest
from validate_corporate_history_contract import (
    _NATIVE_ARRAY_BLOCK_EFFECTS,
    _NATIVE_CONTRACT_ROLES,
    _NATIVE_VARIABLE_BLOCK_EFFECTS,
    _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS,
    Validator,
    _collect_native_write_tokens,
    _is_repeatable_decision,
    _removes_active_decision,
)


def _write(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_loc(root: Path, relative: str, text: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("fire_only_once = no", True),
        ("fire_only_once=no", True),
        ("fire_only_once = no # reusable decision", True),
        ("fire_only_once = yes", False),
        ("# fire_only_once = no", False),
        ('log = "fire_only_once = no"', False),
        ('log = "start\nfire_only_once = no\nend"', False),
        ('log = "fire_only_once = no"\nfire_only_once = no', True),
        ("", False),
    ),
)
def test_repeatable_decision_requires_an_active_no_declaration(text, expected):
    assert _is_repeatable_decision(text) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        ("remove_decision = linux_system_program", True),
        ("remove_decision=linux_system_program", True),
        ("remove_decision = linux_system_other_program", False),
        ("# remove_decision = linux_system_program", False),
        ('log = "remove_decision = linux_system_program"', False),
        ('log = "start\nremove_decision = linux_system_program\nend"', False),
        (
            'log = "remove_decision = linux_system_program"\n'
            "remove_decision = linux_system_program",
            True,
        ),
        ("", False),
    ),
)
def test_active_decision_cleanup_requires_an_executable_removal(text, expected):
    assert _removes_active_decision(text, "linux_system_program") is expected


def _manifest(
    callerless=None,
    other_callerless=None,
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
            "full_start_strategies": [
                "yearly_dispatcher",
                "current_year_scheduler",
                "reconstruction",
            ],
            "outcomes_only_strategy": "reconstruction",
            "monthly_driver": "USA_corporate_history_monthly_outcomes",
            "terminal_marker": "USA_test_reconstruct_complete",
            "terminal_date": "2001-03-01",
            "outcome_ideas": ["USA_test_outcome_a", "USA_test_outcome_b"],
            "expected_callers": {},
            "dependency_order": [],
            "localisation_prefixes": ["USA_test"],
            "effect_preview_policy": "engine_or_explicit",
            "bridge_refresh_policy": "none",
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
                "full_start_strategies": ["yearly_dispatcher"],
                "outcomes_only_strategy": "suppressed",
                "monthly_driver": "USA_corporate_history_monthly_outcomes",
                "terminal_marker": "USA_other_reconstruct_complete",
                "terminal_date": "2001-03-01",
                "outcome_ideas": [],
                "expected_callers": {},
                "dependency_order": [],
                "localisation_prefixes": ["USA_other"],
                "effect_preview_policy": "engine_or_explicit",
                "bridge_refresh_policy": "none",
                "owned_prefixes": ["USA_other"],
                "variables": {},
                "outcome_idea_prefixes": [],
                "requires_current_year_scheduler": False,
                "allow_yearly_scheduler_duplicates": False,
                "callerless_anchors": other_callerless or [],
                "allowed_multiple_callers": [],
                "allowed_reads": [],
                "allowed_writes": [],
            }
        )
    return {"schema_version": 2, "chains": chains}


def _base_events(include_hidden_ninety=True, include_anchor=False):
    blocks = ["""add_namespace = USA_test_events

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
""".strip()]
    if include_anchor:
        blocks.append("""
country_event = {
\tid = USA_test_events.2
\ttitle = USA_test_events.2.t
\tdesc = USA_test_events.2.d
\tpicture = GFX_test
\tis_triggered_only = yes
\toption = { name = USA_test_events.2.a }
}
""".strip())
    if include_hidden_ninety:
        blocks.append("""
country_event = {
\tid = USA_test_events.90
\thidden = yes
\tis_triggered_only = yes
\tfire_only_once = yes
\timmediate = { USA_test_reconstruct_history = yes }
}
""".strip())
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
        """corporate_history_full_enabled = {
	NOT = { has_game_rule = { rule = rule_corporate_history option = outcomes_only } }
	NOT = { has_game_rule = { rule = rule_corporate_history option = disabled } }
}
corporate_history_outcomes_only_enabled = {
	has_game_rule = { rule = rule_corporate_history option = outcomes_only }
}
corporate_history_enabled = {
	OR = {
		corporate_history_full_enabled = yes
		corporate_history_outcomes_only_enabled = yes
	}
}
""",
    )
    _write(
        root,
        "common/game_rules/00_game_rules.txt",
        """rule_corporate_history = {
	default = { name = full }
	option = { name = outcomes_only }
	option = { name = disabled }
}
""",
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
        """on_startup = { effect = { corporate_history_on_startup = yes } }
on_monthly_USA = { effect = { USA_corporate_history_monthly_outcomes = yes } }
""",
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
    _write_loc(
        root,
        "localisation/english/MD_focus_USA_l_english.yml",
        """l_english:
 USA_test_events.1.t: "Test event"
 USA_test_events.1.d: "Test description."
 USA_test_events.1.a: "Choose the test"
 USA_test_events.2.t: "Test anchor"
 USA_test_events.2.d: "Test anchor description."
 USA_test_events.2.a: "Choose the anchor"
 USA_test_outcome_a: "Outcome A"
 USA_test_outcome_a_desc: "The first outcome."
 USA_test_outcome_b: "Outcome B"
 USA_test_outcome_b_desc: "The second outcome."
""",
    )


def _messages(root: Path):
    validator = Validator(
        mod_path=str(root), use_colors=False, workers=1, no_cache=True
    )
    validator.run_all_validations()
    return [issue.message for issue in validator._issues]


def _enable_bridge_fixture(root: Path, *, refresh: str):
    manifest_path = root / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["bridge_refresh_policy"] = "immediate"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    events_path = root / "events/USA_test_events.txt"
    events = events_path.read_text(encoding="utf-8")
    if refresh == "transitive":
        mutation = "\t\tUSA_test_finish_bridge = yes\n"
    else:
        mutation = "\t\tset_country_flag = USA_test_bridge_outcome\n"
        if refresh == "direct":
            mutation += "\t\tUSA_corporate_systems_update_economic_bridge = yes\n"
    events_path.write_text(
        events.replace(
            "\t\tname = USA_test_events.1.a\n",
            "\t\tname = USA_test_events.1.a\n" + mutation,
        ),
        encoding="utf-8",
    )

    axes = (
        "open_standards",
        "vertical_integration",
        "supply_resilience",
        "security_control",
        "national_compute_stack",
    )
    reset = "\n".join(
        f"\tset_temp_variable = {{ USA_oem_contribution_{axis} = 0 }}" for axis in axes
    )
    contribution_clamps = "\n".join(
        f"\tclamp_temp_variable = {{ var = USA_oem_contribution_{axis} min = -3 max = 3 }}"
        for axis in axes
    )
    effective = "\n".join(
        f"\tset_variable = {{ USA_oem_effective_{axis} = 0 }}\n"
        f"\tadd_to_variable = {{ USA_oem_effective_{axis} = USA_oem_contribution_{axis} }}\n"
        f"\tclamp_variable = {{ var = USA_oem_effective_{axis} min = 0 max = 10 }}"
        for axis in axes
    )
    score = "\n".join(
        (
            f"\t\tset_temp_variable = {{ USA_corporate_systems_economic_integration_score = USA_oem_effective_{axes[0]} }}",
            *(
                f"\t\tadd_to_temp_variable = {{ USA_corporate_systems_economic_integration_score = USA_oem_effective_{axis} }}"
                for axis in axes[1:]
            ),
        )
    )
    helper = (
        "USA_test_finish_bridge = {\n"
        "\tset_country_flag = USA_test_bridge_outcome\n"
        "\tUSA_corporate_systems_update_economic_bridge = yes\n"
        "}\n\n"
        if refresh == "transitive"
        else ""
    )
    _write(
        root,
        "common/scripted_effects/USA_corporate_systems_effects.txt",
        f"""{helper}USA_corporate_systems_clear_economic_bridge_ideas = {{
\tremove_ideas = {{
\t\tUSA_corporate_systems_economic_integration_1
\t\tUSA_corporate_systems_economic_integration_2
\t\tUSA_corporate_systems_economic_integration_3
\t\tUSA_corporate_systems_economic_integration_4
\t\tUSA_corporate_systems_economic_integration_5
\t}}
}}

USA_corporate_systems_clear_derived_axes = {{
\tset_variable = {{ USA_oem_effective_open_standards = 0 }}
}}

USA_corporate_systems_test_contribution = {{
\tif = {{
\t\tlimit = {{ has_country_flag = USA_test_bridge_outcome }}
\t\tadd_to_temp_variable = {{ USA_oem_contribution_open_standards = 1 }}
\t}}
}}

USA_corporate_systems_rebuild_company_contributions = {{
{reset}
\tUSA_corporate_systems_test_contribution = yes
{contribution_clamps}
}}

USA_corporate_systems_rebuild_effective_axes = {{
{effective}
}}

USA_corporate_systems_update_economic_bridge = {{
\tif = {{
\t\tlimit = {{ corporate_history_enabled = yes }}
\t\tUSA_corporate_systems_rebuild_company_contributions = yes
\t\tUSA_corporate_systems_rebuild_effective_axes = yes
{score}
\t\tif = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 15 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_1
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 22 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_2
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 29 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_3
\t\t}}
\t\telse_if = {{
\t\t\tlimit = {{ check_variable = {{ USA_corporate_systems_economic_integration_score < 38 }} }}
\t\t\tadd_ideas = USA_corporate_systems_economic_integration_4
\t\t}}
\t\telse = {{ add_ideas = USA_corporate_systems_economic_integration_5 }}
\t}}
\telse = {{
\t\tUSA_corporate_systems_clear_derived_axes = yes
\t\tUSA_corporate_systems_clear_economic_bridge_ideas = yes
\t}}
}}
""",
    )


def _enable_economic_layer_fixture(root: Path):
    manifest_path = root / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 3
    manifest["economic_layers"] = [
        {
            "name": "Test Real Options",
            "tag": "USA",
            "updater": "USA_oem_update_real_options_economy",
            "bridge": "USA_corporate_systems_update_economic_bridge",
            "effect_file": "common/scripted_effects/USA_oem_real_options_effects.txt",
            "dynamic_modifier_file": "common/dynamic_modifiers/05_USA_oem_test.txt",
            "decision_file": "common/decisions/USA_oem_test.txt",
            "idea_file": "common/ideas/USA_oem_test_ideas.txt",
            "scripted_localisation_file": "common/scripted_localisation/USA_oem_test.txt",
            "localisation_file": "localisation/english/MD_focus_USA_l_english.yml",
            "initialized_flag": "USA_oem_real_options_initialized",
            "variables": {"USA_oem_option_value": {"min": 0, "max": 100}},
            "source_variables": ["USA_oem_effective_open_standards"],
            "cdf": {
                "input_min": -3,
                "input_max": 3,
                "output_min": 0,
                "output_max": 1,
                "knots": [0, 1],
                "values": [0.5, 0.84134],
            },
            "modifier_families": [
                {
                    "name": "investment_climate",
                    "score": "USA_oem_option_value",
                    "thresholds": [50],
                    "members": [
                        "USA_oem_investment_climate_1",
                        "USA_oem_investment_climate_2",
                    ],
                }
            ],
            "policy_programs": [
                {
                    "decision": f"USA_oem_policy_{number}",
                    "idea": f"USA_oem_program_{number}",
                    "program_class": (
                        "major_commitment" if number in {2, 4} else "operational"
                    ),
                    "days": 365 if number in {2, 4} else 180,
                    "cooldown_days": 365 if number in {2, 4} else 180,
                    "refresh_policy": "block_while_active",
                    "cleanup_owner": "USA_oem_update_real_options_economy",
                }
                for number in range(1, 5)
            ],
            "dashboard_variables": ["USA_oem_option_value_display"],
            "scripted_localisation": ["USA_oem_investment_climate_label"],
            "localisation_keys": [
                "USA_corporate_systems_real_options",
                "USA_corporate_systems_real_options_desc",
            ],
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    _write(
        root,
        "common/scripted_effects/USA_oem_real_options_effects.txt",
        """USA_corporate_systems_update_economic_bridge = {
	USA_oem_update_real_options_economy = yes
}

USA_oem_update_real_options_economy = {
	if = {
		limit = {
			corporate_history_enabled = yes
			original_tag = USA
			NOT = { has_country_flag = collapsed_nation }
		}
		set_country_flag = USA_oem_real_options_initialized
		set_temp_variable = { USA_oem_test_source = USA_oem_effective_open_standards }
		set_variable = { USA_oem_option_value = { value = 50 clamp = { min = 0 max = 100 } } }
		clamp_variable = { var = USA_oem_option_value min = 0 max = 100 }
		set_variable = { USA_oem_option_value_display = { value = USA_oem_option_value round = yes } }
		set_temp_variable = { USA_oem_cdf_output = 0.5 }
		if = {
			limit = { check_variable = { USA_oem_cdf_input > 0 } }
			set_temp_variable = { USA_oem_cdf_output = 0.84134 }
		}
		clamp_temp_variable = { var = USA_oem_cdf_output min = 0 max = 1 }
		if = {
			limit = { check_variable = { USA_oem_option_value < 50 } }
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
			add_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
		}
		else = {
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
			remove_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
			add_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
		}
	}
	else = {
		clr_country_flag = USA_oem_real_options_initialized
		remove_ideas = {
			USA_oem_program_1
			USA_oem_program_2
			USA_oem_program_3
			USA_oem_program_4
		}
		clear_variable = USA_oem_option_value
		clear_variable = USA_oem_option_value_display
		remove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }
		remove_dynamic_modifier = { modifier = USA_oem_investment_climate_2 }
	}
}
""",
    )
    _write(
        root,
        "common/dynamic_modifiers/05_USA_oem_test.txt",
        """USA_oem_investment_climate_1 = {
	enable = { always = yes }
	productivity_growth_modifier = -0.01
}

USA_oem_investment_climate_2 = {
	enable = { always = yes }
	productivity_growth_modifier = 0.01
}
""",
    )

    decisions = []
    idea_blocks = []
    loc_lines = [
        ' USA_corporate_systems_real_options: "Real Options"',
        ' USA_corporate_systems_real_options_desc: "[?USA_oem_option_value_display|0]"',
        ' USA_oem_investment_climate_1: "Frozen"',
        ' USA_oem_investment_climate_1_desc: "Frozen investment."',
        ' USA_oem_investment_climate_2: "Investable"',
        ' USA_oem_investment_climate_2_desc: "Investable conditions."',
    ]
    for number in range(1, 5):
        program_days = 365 if number in {2, 4} else 180
        decisions.append(f"""USA_oem_policy_{number} = {{
	days_re_enable = {program_days}

	fire_only_once = no

	available = {{
		NOT = {{ has_country_flag = collapsed_nation }}
		NOT = {{ has_idea = USA_oem_program_{number} }}
	}}
	complete_effect = {{
		add_timed_idea = {{ idea = USA_oem_program_{number} days = {program_days} }}
	}}
}}""")
        idea_blocks.append(f"""USA_oem_program_{number} = {{
	picture = generic_economic_increase
	allowed = {{ original_tag = USA }}
	allowed_civil_war = {{ always = yes }}
}}""")
        loc_lines.extend(
            [
                f' USA_oem_policy_{number}_desc: "Runs for {program_days} days."',
                f' USA_oem_policy_{number}_tt: "Temporary program for {program_days} days."',
                f' USA_oem_program_{number}: "Program {number}"',
                f' USA_oem_program_{number}_desc: "Program {number} description."',
            ]
        )
    _write(root, "common/decisions/USA_oem_test.txt", "\n\n".join(decisions))
    indented_ideas = "\n\n".join(
        "\t\t" + block.replace("\n", "\n\t\t") for block in idea_blocks
    )
    _write(
        root,
        "common/ideas/USA_oem_test_ideas.txt",
        f"ideas = {{\n\tcountry = {{\n{indented_ideas}\n\t}}\n}}\n",
    )
    _write(
        root,
        "common/scripted_localisation/USA_oem_test.txt",
        """defined_text = {
	name = USA_oem_investment_climate_label
	text = { localization_key = USA_oem_investment_climate_1 }
}
""",
    )
    loc_path = root / "localisation/english/MD_focus_USA_l_english.yml"
    existing_loc = loc_path.read_text(encoding="utf-8-sig")
    _write_loc(
        root,
        "localisation/english/MD_focus_USA_l_english.yml",
        existing_loc + "\n" + "\n".join(loc_lines) + "\n",
    )


def _enable_reusable_lifecycle_fixture(root: Path):
    _enable_economic_layer_fixture(root)
    manifest_path = root / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    layer = manifest["economic_layers"][0]
    manifest["reusable_decision_lifecycles"] = [
        {
            "name": "Test Real Options",
            "decision_file": layer["decision_file"],
            "effect_file": layer["effect_file"],
            "localisation_file": layer["localisation_file"],
            "programs": [
                {
                    "decision": program["decision"],
                    "kind": "timed_idea",
                    "idea": program["idea"],
                    "active_days": program["days"],
                    "cooldown_mode": "days_re_enable",
                    "cooldown_days": program["cooldown_days"],
                    "duration_source": "decision",
                    "localisation_keys": [
                        f"{program['decision']}_desc",
                        f"{program['decision']}_tt",
                    ],
                    "cleanup_effect": "USA_oem_update_real_options_economy",
                }
                for program in layer["policy_programs"]
            ],
        }
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


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
        "USA_test_reconstruct_history transitively replays treasury changes" in message
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
        callerless=["USA_test_events.91"],
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


def test_cross_chain_read_in_split_namespace_file_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        callerless=["USA_test_events.91"],
        manifest_overrides={
            "with_other_chain": True,
            "other_callerless": ["USA_other_events.91"],
        },
    )
    _write(
        tmp_path,
        "events/USA_test_events_extension.txt",
        """country_event = {
\tid = USA_test_events.91
\thidden = yes
\tis_triggered_only = yes
\ttrigger = { has_country_flag = USA_other_platform }
}
""",
    )
    assert _messages(tmp_path) == [
        "TestCo has undeclared cross-chain read-only AI/flavour use of "
        "USA_other_platform, owned by OtherCo"
    ]


def test_events_sharing_a_file_are_checked_under_their_own_namespaces(tmp_path):
    _build_fixture(
        tmp_path,
        callerless=["USA_test_events.91"],
        manifest_overrides={
            "with_other_chain": True,
            "other_callerless": ["USA_other_events.91"],
        },
    )
    _write(
        tmp_path,
        "events/shared_events.txt",
        """country_event = {
\tid = USA_test_events.91
\thidden = yes
\tis_triggered_only = yes
\timmediate = { set_country_flag = USA_test_platform }
}

country_event = {
\tid = USA_other_events.91
\thidden = yes
\tis_triggered_only = yes
\timmediate = { set_country_flag = USA_other_platform }
}
""",
    )
    assert _messages(tmp_path) == []


def test_duplicate_manifest_identity_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"].append(dict(manifest["chains"][0]))
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    messages = _messages(tmp_path)
    assert "Manifest name TestCo is declared 2 times" in messages
    assert "Manifest namespace USA_test_events is declared 2 times" in messages
    assert "Manifest root USA_test is declared 2 times" in messages


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


def test_game_rule_requires_all_three_modes(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/game_rules/00_game_rules.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\toption = { name = disabled }\n", ""
        ),
        encoding="utf-8",
    )
    assert any(
        "must define Full, Outcomes Only, and Disabled" in message
        for message in _messages(tmp_path)
    )


def test_full_trigger_must_exclude_disabled(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_triggers/MD_corporate_history_triggers.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\tNOT = { has_game_rule = { rule = rule_corporate_history option = disabled } }\n",
            "",
        ),
        encoding="utf-8",
    )
    assert any(
        "corporate_history_full_enabled does not exclude disabled" in message
        for message in _messages(tmp_path)
    )


def test_startup_driver_requires_exactly_one_on_action_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "on_new_term = { effect = { corporate_history_on_startup = yes } }\n",
        encoding="utf-8",
    )
    assert any(
        "corporate_history_on_startup requires exactly one on-action caller; found 2"
        in message
        for message in _messages(tmp_path)
    )


def test_monthly_driver_requires_matching_on_action_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "on_monthly_USA = { effect = { USA_corporate_history_monthly_outcomes = yes } }\n",
            "",
        ),
        encoding="utf-8",
    )
    assert any(
        "USA_corporate_history_monthly_outcomes requires exactly one matching on-monthly caller; found 0"
        in message
        for message in _messages(tmp_path)
    )


def test_hidden_event_without_a_caller_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    _write(
        tmp_path,
        "events/USA_test_events_extension.txt",
        """country_event = {
\tid = USA_test_events.91
\thidden = yes
\tis_triggered_only = yes
\timmediate = { set_country_flag = USA_test_hidden_resolved }
}
""",
    )
    assert any(
        "USA_test_events.91 has no direct callers" in message
        for message in _messages(tmp_path)
    )


def test_manifest_expected_callers_are_exact(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["expected_callers"] = {
        "USA_test_events.1": ["effect:wrong_owner"]
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(
        "USA_test_events.1 callers differ from the manifest" in message
        for message in _messages(tmp_path)
    )


def test_dispatcher_requires_the_matching_trigger_year_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/00_yearly_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "trigger_year_2001_events", "trigger_year_2002_events"
        ),
        encoding="utf-8",
    )
    assert any(
        "USA_corporate_trigger_year_2001 must be called by trigger_year_2001_events"
        in message
        for message in _messages(tmp_path)
    )


def test_dispatcher_event_calls_must_be_inside_the_full_gate(tmp_path):
    _build_fixture(tmp_path)
    path = (
        tmp_path / "common/scripted_effects/00_corporate_history_dispatch_effects.txt"
    )
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\t\tcorporate_history_full_enabled = yes\n", ""
        ),
        encoding="utf-8",
    )
    assert any(
        "schedules events outside its corporate_history_full_enabled branch" in message
        for message in _messages(tmp_path)
    )


def test_cross_chain_event_call_is_a_declared_write(tmp_path):
    _build_fixture(tmp_path, manifest_overrides={"with_other_chain": True})
    path = tmp_path / "events/USA_test_events.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\tname = USA_test_events.1.a\n",
            "\t\tname = USA_test_events.1.a\n"
            "\t\tcountry_event = { id = USA_other_events.1 days = 1 }\n",
        ),
        encoding="utf-8",
    )
    assert any(
        "TestCo writes USA_other_events, owned by OtherCo" in message
        for message in _messages(tmp_path)
    )


def test_multiply_variable_without_clamp_is_rejected(tmp_path):
    _build_fixture(tmp_path, missing_clamp=True)
    path = tmp_path / "events/USA_test_events.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "add_to_variable = { USA_test_state = 1 }",
            "multiply_variable = { USA_test_state = 2 }",
        ),
        encoding="utf-8",
    )
    assert any(
        "mutates bounded variables without a later USA_test_clamp_state call" in message
        for message in _messages(tmp_path)
    )


def test_transitive_reconstruction_reward_is_rejected(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    text = path.read_text(encoding="utf-8").replace(
        "USA_test_reconstruct_history = {\n",
        "USA_test_reconstruct_history = {\n\tUSA_test_reward_helper = yes\n",
    )
    text += "\nUSA_test_reward_helper = {\n\tmodify_treasury_effect = yes\n}\n"
    path.write_text(text, encoding="utf-8")
    assert any(
        "transitively replays treasury changes through USA_test_reward_helper"
        in message
        for message in _messages(tmp_path)
    )


def test_cleanup_must_remove_every_declared_outcome(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\t\tUSA_test_outcome_b\n", ""),
        encoding="utf-8",
    )
    assert any(
        "TestCo is missing a mutually exclusive cleanup effect" in message
        for message in _messages(tmp_path)
    )


def test_explicit_preview_policy_requires_option_tooltip(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["effect_preview_policy"] = "explicit"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(
        "USA_test_events.1.a requires exact custom_effect_tooltip = USA_test_events.1.a_tt"
        in message
        for message in _messages(tmp_path)
    )


def test_oem_localisation_requires_utf8_bom(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig")
    path.write_text(text, encoding="utf-8")
    assert any(
        "English OEM localisation file is missing a UTF-8 BOM" in message
        for message in _messages(tmp_path)
    )


def test_manifest_v2_requires_lifecycle_fields(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["chains"][0]["terminal_date"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert any(
        "is missing required fields: terminal_date" in message
        for message in _messages(tmp_path)
    )


def test_startup_driver_accepts_one_hop_on_action_caller(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "corporate_history_on_startup = yes", "startup_events = yes"
        ),
        encoding="utf-8",
    )
    assert not any(
        "corporate_history_on_startup requires exactly one on-action caller" in message
        for message in _messages(tmp_path)
    )


def test_standard_indirect_clamp_matches_manifest_bounds(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "clamp_variable = { var = USA_test_state min = 0 max = 10 }",
            "set_temp_variable = { corp_value = USA_test_state }\n"
            "\tcorporate_history_clamp_value = yes\n"
            "\tset_variable = { USA_test_state = corp_value }",
        ),
        encoding="utf-8",
    )
    assert not any(
        "must clamp USA_test_state to manifest bounds" in message
        for message in _messages(tmp_path)
    )


def test_nonstandard_indirect_temp_clamp_matches_manifest_bounds(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0, "max": 7}}},
    )
    path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    text = path.read_text(encoding="utf-8").replace(
        "clamp_variable = { var = USA_test_state min = 0 max = 10 }",
        "USA_test_validate_registers = yes",
    )
    text += (
        "\nUSA_test_validate_registers = {\n"
        "\tset_temp_variable = { corp_value = USA_test_state }\n"
        "\tclamp_temp_variable = { var = corp_value min = 0 max = 7 }\n"
        "\tset_variable = { USA_test_state = corp_value }\n"
        "}\n"
    )
    path.write_text(text, encoding="utf-8")
    assert not any(
        "must clamp USA_test_state to manifest bounds" in message
        for message in _messages(tmp_path)
    )


def test_reconstruction_may_call_hidden_integration_event(tmp_path):
    _build_fixture(tmp_path)
    events_path = tmp_path / "events/USA_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8") + "\ncountry_event = {\n"
        "\tid = USA_test_events.91\n"
        "\thidden = yes\n"
        "\tis_triggered_only = yes\n"
        "\timmediate = { set_country_flag = USA_test_hidden_integrated }\n"
        "}\n",
        encoding="utf-8",
    )
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8").replace(
            "USA_test_reconstruct_history = {\n",
            "USA_test_reconstruct_history = {\n\tcountry_event = USA_test_events.91\n",
        ),
        encoding="utf-8",
    )
    assert not any(
        "transitively fires an event" in message for message in _messages(tmp_path)
    )


def test_reconstruction_rejects_visible_event_replay(tmp_path):
    _build_fixture(tmp_path)
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8").replace(
            "USA_test_reconstruct_history = {\n",
            "USA_test_reconstruct_history = {\n\tcountry_event = USA_test_events.1\n",
        ),
        encoding="utf-8",
    )
    assert any(
        "transitively fires an event" in message for message in _messages(tmp_path)
    )


def test_shared_english_localisation_key_resolves_outside_owned_prefix(tmp_path):
    _build_fixture(tmp_path)
    events_path = tmp_path / "events/USA_test_events.txt"
    events_path.write_text(
        events_path.read_text(encoding="utf-8").replace(
            "title = USA_test_events.1.t", "title = SHARED_CORPORATE_TITLE"
        ),
        encoding="utf-8",
    )
    loc_path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    loc_path.write_bytes(
        loc_path.read_bytes() + b' SHARED_CORPORATE_TITLE: "Shared title"\n'
    )
    assert not any(
        "Missing English corporate-history localisation key SHARED_CORPORATE_TITLE"
        in message
        for message in _messages(tmp_path)
    )


def test_tooltip_exemption_requires_a_reason(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["effect_preview_policy"] = "explicit"
    manifest["chains"][0]["tooltip_exemptions"] = {"USA_test_events.1.a": ""}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    messages = _messages(tmp_path)
    assert "Tooltip exemption USA_test_events.1.a requires a reason" in messages
    assert not any(
        "requires exact custom_effect_tooltip" in message for message in messages
    )


def test_auxiliary_completion_marker_has_declared_ownership(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["auxiliary_completion_markers"] = [
        "USA_test_aux_reconstruct_complete"
    ]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8") + "\nUSA_test_aux_complete = {\n"
        "\tset_country_flag = USA_test_aux_reconstruct_complete\n"
        "}\n",
        encoding="utf-8",
    )
    core_path = tmp_path / "common/scripted_effects/00_corporate_history_effects.txt"
    core_path.write_text(
        core_path.read_text(encoding="utf-8").replace(
            "NOT = { has_country_flag = USA_test_reconstruct_complete }",
            "NOT = { has_country_flag = USA_test_reconstruct_complete }\n"
            "\t\t\tNOT = { has_country_flag = USA_test_aux_reconstruct_complete }",
        ),
        encoding="utf-8",
    )
    assert not any(
        "USA_test_aux_reconstruct_complete has 0 owning chains" in message
        for message in _messages(tmp_path)
    )


def test_bridge_contribution_requires_immediate_refresh(tmp_path):
    _build_fixture(tmp_path)
    _enable_bridge_fixture(tmp_path, refresh="missing")
    assert any(
        "changes a USA bridge contribution without an immediate refresh" in message
        for message in _messages(tmp_path)
    )


def test_bridge_accepts_transitive_immediate_refresh(tmp_path):
    _build_fixture(tmp_path)
    _enable_bridge_fixture(tmp_path, refresh="transitive")
    assert not any(
        "changes a USA bridge contribution without an immediate refresh" in message
        for message in _messages(tmp_path)
    )


def test_scoped_english_localisation_rejects_malformed_quotes(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        'USA_test_events.1.d: "Test description."',
        'USA_test_events.1.d: "A "broken" description"',
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert any(
        "Malformed English corporate-history localisation value USA_test_events.1.d"
        in message
        for message in _messages(tmp_path)
    )


def test_scoped_english_localisation_rejects_physical_newline(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        'USA_test_events.1.d: "Test description."',
        'USA_test_events.1.d: "First line\n second line"',
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert any(
        "Malformed English corporate-history localisation value USA_test_events.1.d"
        in message
        for message in _messages(tmp_path)
    )


def test_scoped_english_localisation_accepts_escapes_and_literal_newline(tmp_path):
    _build_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        'USA_test_events.1.d: "Test description."',
        r'USA_test_events.1.d: "A \"quoted\" description\nSecond line #4"',
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert not any(
        "Malformed English corporate-history localisation value USA_test_events.1.d"
        in message
        for message in _messages(tmp_path)
    )


def test_duplicate_scoped_english_key_is_rejected_but_non_english_is_ignored(tmp_path):
    _build_fixture(tmp_path)
    _write_loc(
        tmp_path,
        "localisation/english/duplicate_l_english.yml",
        'l_english:\n USA_test_events.1.t: "Duplicate"\n',
    )
    _write_loc(
        tmp_path,
        "localisation/french/duplicate_l_french.yml",
        'l_french:\n USA_test_events.1.t: "French duplicate"\n',
    )
    assert any(
        "English OEM localisation key USA_test_events.1.t is defined 2 times" in message
        for message in _messages(tmp_path)
    )


def test_manifest_terminal_date_matches_scripted_completion_guard(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["terminal_date"] = "2001-03-02"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "terminal marker USA_test_reconstruct_complete must use date > 2001.3.2"
        in message
        for message in _messages(tmp_path)
    )


def test_manifest_scheduler_requirement_matches_full_start_strategy(tmp_path):
    _build_fixture(tmp_path)
    manifest_path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["chains"][0]["full_start_strategies"].remove("current_year_scheduler")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "requires_current_year_scheduler disagrees with full_start_strategies"
        in message
        for message in _messages(tmp_path)
    )


def test_decimal_manifest_bounds_are_preserved(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0.05, "max": 1.0}}},
    )
    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, no_cache=True
    )

    chains = validator._load_manifest()

    assert chains[0].variables["USA_test_state"].minimum == Decimal("0.05")
    assert chains[0].variables["USA_test_state"].maximum == Decimal("1.0")


def test_decimal_clamp_mismatch_is_rejected(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0.05, "max": 1.0}}},
    )

    assert any(
        "must clamp USA_test_state to manifest bounds 0.05..1.0" in message
        for message in _messages(tmp_path)
    )


def test_decimal_clamp_matching_manifest_is_accepted(tmp_path):
    _build_fixture(
        tmp_path,
        manifest_overrides={"variables": {"USA_test_state": {"min": 0.05, "max": 1.0}}},
    )
    effects_path = tmp_path / "common/scripted_effects/USA_test_effects.txt"
    effects_path.write_text(
        effects_path.read_text(encoding="utf-8").replace(
            "var = USA_test_state min = 0 max = 10",
            "var = USA_test_state min = 0.05 max = 1.00",
        ),
        encoding="utf-8",
    )

    assert not any(
        "must clamp USA_test_state to manifest bounds" in message
        for message in _messages(tmp_path)
    )


def test_valid_real_options_contract_fixture(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)

    assert not any("real-options" in message.lower() for message in _messages(tmp_path))


def test_real_options_requires_one_authoritative_updater(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\nUSA_oem_update_real_options_economy = { always = yes }\n",
        encoding="utf-8",
    )

    assert any(
        "requires exactly one authoritative updater" in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_unsupported_script_math_operator(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "set_temp_variable = { USA_oem_cdf_output = 0.5 }",
            "set_temp_variable = { USA_oem_cdf_output = 0.5 exp = 2 }",
        ),
        encoding="utf-8",
    )

    assert any(
        "uses unsupported scripted math operator exp" in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_direct_on_action_hook(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/on_actions/MD_event_on_actions.txt"
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\non_daily_USA = { effect = { USA_oem_update_real_options_economy = yes } }\n",
        encoding="utf-8",
    )

    assert any(
        "must be reached through the economic bridge, not an on-action" in message
        for message in _messages(tmp_path)
    )


def test_real_options_tier_family_requires_cleanup(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    text = path.read_text(encoding="utf-8").replace(
        "\t\t\tremove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }\n",
        "",
    )
    text = text.replace(
        "\t\tremove_dynamic_modifier = { modifier = USA_oem_investment_climate_1 }\n",
        "",
    )
    path.write_text(text, encoding="utf-8")

    assert any(
        "never clears dynamic modifier USA_oem_investment_climate_1" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_duration_must_match_contract(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("days = 180", "days = 730", 1),
        encoding="utf-8",
    )

    assert any(
        "must add USA_oem_program_1 once for 180 days" in message
        for message in _messages(tmp_path)
    )


def test_reusable_temporary_program_cannot_exceed_365_days(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["reusable_decision_lifecycles"][0]["programs"][0]["active_days"] = 730
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "USA_oem_policy_1 temporary program must last 1 to 365 days" in message
        for message in _messages(tmp_path)
    )


def test_reusable_program_localisation_must_match_duration(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    path.write_text(
        path.read_text(encoding="utf-8-sig").replace(
            "Runs for 180 days.", "Runs for 730 days.", 1
        ),
        encoding="utf-8-sig",
    )

    messages = _messages(tmp_path)
    assert any(
        "USA_oem_policy_1_desc must state 180 days" in message for message in messages
    )
    assert any(
        "USA_oem_policy_1_desc still claims a 730-day lifecycle" in message
        for message in messages
    )


def test_reusable_program_reenable_period_must_equal_active_duration(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["reusable_decision_lifecycles"][0]["programs"][0]["cooldown_days"] = 365
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "USA_oem_policy_1 re-enable period must equal its active duration" in message
        for message in _messages(tmp_path)
    )


def test_long_construction_timer_requires_a_manifest_reason(tmp_path):
    _build_fixture(tmp_path)
    _enable_reusable_lifecycle_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    program = manifest["reusable_decision_lifecycles"][0]["programs"][0]
    program.update(
        {
            "kind": "construction_project",
            "active_days": 0,
            "cooldown_days": 180,
            "mission": "USA_oem_policy_2",
            "project_days": 730,
        }
    )
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "USA_oem_policy_1 construction timer over 365 days needs a reason" in message
        for message in _messages(tmp_path)
    )


def test_major_policy_program_duration_must_match_contract(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("days = 365", "days = 180", 1),
        encoding="utf-8",
    )

    assert any(
        "must add USA_oem_program_2 once for 365 days" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_cooldown_must_match_contract(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "days_re_enable = 180", "days_re_enable = 365", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must declare a 180-day cooldown" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_must_remain_reusable(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\n\tfire_only_once = no\n", "", 1),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must remain reusable after its declared cooldown" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_must_block_while_active(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "NOT = { has_idea = USA_oem_program_1 }", "always = yes", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must block while USA_oem_program_1 is active" in message
        for message in _messages(tmp_path)
    )


def test_policy_program_is_unavailable_after_collapse(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/decisions/USA_oem_test.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\tNOT = { has_country_flag = collapsed_nation }\n", "", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "USA_oem_policy_1 must be unavailable after national collapse" in message
        for message in _messages(tmp_path)
    )


def test_real_options_cleanup_removes_policy_programs(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("\t\t\tUSA_oem_program_1\n", "", 1),
        encoding="utf-8",
    )

    assert any(
        "Off/collapse cleanup must remove USA_oem_program_1" in message
        for message in _messages(tmp_path)
    )


def test_real_options_dashboard_reads_authoritative_outputs(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        "USA_oem_option_value_display", "USA_oem_stale_value_display"
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

    assert any(
        "dashboard does not read authoritative output USA_oem_option_value_display"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_requires_program_localisation(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "localisation/english/MD_focus_USA_l_english.yml"
    text = path.read_text(encoding="utf-8-sig").replace(
        ' USA_oem_program_1_desc: "Program 1 description."\n', ""
    )
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))

    assert any(
        "Missing English real-options localisation key USA_oem_program_1_desc"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_helpers_are_mode_neutral(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "corporate_history_enabled = yes",
            "corporate_history_enabled = yes\n\t\t\tcorporate_history_full_enabled = yes",
            1,
        ),
        encoding="utf-8",
    )

    assert any("must be mode-neutral" in message for message in _messages(tmp_path))


def test_real_options_rejects_company_owned_writes(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "set_country_flag = USA_oem_real_options_initialized",
            "set_country_flag = USA_oem_real_options_initialized\n"
            "\t\tset_variable = { USA_test_state = 5 }",
            1,
        ),
        encoding="utf-8",
    )

    assert any(
        "writes company-owned variable USA_test_state" in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_undeclared_persistent_writes(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "set_country_flag = USA_oem_real_options_initialized",
            "set_country_flag = USA_oem_real_options_initialized\n"
            "\t\tset_variable = { USA_oem_untracked_state = 5 }",
            1,
        ),
        encoding="utf-8",
    )

    assert any(
        "writes undeclared persistent variable USA_oem_untracked_state" in message
        for message in _messages(tmp_path)
    )


def test_real_options_requires_bounded_cdf_output(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\t\tclamp_temp_variable = { var = USA_oem_cdf_output min = 0 max = 1 }\n",
            "",
        ),
        encoding="utf-8",
    )

    assert any(
        "CDF output must clamp to 0..1" in message for message in _messages(tmp_path)
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    (("knots", "0.5"), ("values", None), ("values", True)),
)
def test_real_options_rejects_nonnumeric_cdf_elements(tmp_path, field, replacement):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["economic_layers"][0]["cdf"][field][1] = replacement
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "CDF knots and values must contain only finite numbers" in message
        for message in _messages(tmp_path)
    )


@pytest.mark.parametrize("replacement", ("40", None, True, float("nan")))
def test_real_options_rejects_invalid_modifier_thresholds(tmp_path, replacement):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    family = manifest["economic_layers"][0]["modifier_families"][0]
    family["thresholds"] = [20, replacement]
    family["members"].append("USA_oem_investment_climate_3")
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "modifier family investment_climate thresholds must contain only finite numbers"
        in message
        for message in _messages(tmp_path)
    )


def test_real_options_rejects_non_object_policy_programs(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["economic_layers"][0]["policy_programs"] = [None, "invalid", 1, True]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    messages = _messages(tmp_path)
    assert {message for message in messages if "policy_programs[" in message} == {
        f"Test Real Options policy_programs[{index}] must be an object"
        for index in range(4)
    }


def test_real_options_requires_monthly_bridge_reachability(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "common/scripted_effects/USA_oem_real_options_effects.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "\tUSA_oem_update_real_options_economy = yes\n", "", 1
        ),
        encoding="utf-8",
    )

    assert any(
        "must call USA_oem_update_real_options_economy exactly once" in message
        for message in _messages(tmp_path)
    )


def test_schema_v4_requires_shared_systems(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 4
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "Schema v4 requires a non-empty shared_systems list" in message
        for message in _messages(tmp_path)
    )


def test_schema_v5_requires_reusable_decision_lifecycles(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 5
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "Schema v5 requires reusable_decision_lifecycles" in message
        for message in _messages(tmp_path)
    )


def test_schema_v4_rejects_incomplete_shared_system_declarations(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    path = tmp_path / "tools/corporate_history_contract.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["schema_version"] = 4
    manifest["shared_systems"] = [{}]
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(
        "shared_systems[0] is missing required fields" in message
        for message in _messages(tmp_path)
    )


def test_shared_system_native_write_scanner_covers_structured_mutations():
    text = """
set_country_flag = { flag = POL_native_flag days = 30 }
set_global_flag = { flag = USA_native_global_flag }
modify_country_flag = { value = 2 flag = FRA_native_numeric_flag }
set_mio_flag = ENG_native_mio_flag
set_variable = { var = THIS.SOV_native_meter value = 1 }
modulo_variable = { var = FRA_native_modulo value = 2 }
set_variable_to_random = { max = 5 var = ENG_native_random min = -5 integer = yes }
clear_variable = ROOT.CHI_native_meter
round_variable = THIS.SOV_native_rounded
randomize_variable = { distribution = uniform var = ROOT.CHI_native_random min = 0 max = 1 }
add_to_array = { array = ROOT.POL_native_array value = 1 }
clear_array = THIS.RAJ_native_array
find_highest_in_array = { array = values value = CHI_native_max index = SOV_native_index }
add_ideas = FRA_native_idea
add_timed_idea = { days = 365 idea = RAJ_native_timed_idea }
remove_ideas = { ENG_native_idea CHI_native_idea }
complete_national_focus = { focus = GER_native_focus }
country_event = { days = 1 id = VEN_native_events.1 }
news_event = GER_native_news.1
"""

    assert _collect_native_write_tokens(
        text,
        ("CHI_", "ENG_", "FRA_", "GER_", "POL_", "RAJ_", "SOV_", "USA_", "VEN_"),
    ) == {
        "CHI_native_meter",
        "CHI_native_max",
        "CHI_native_random",
        "CHI_native_idea",
        "ENG_native_idea",
        "ENG_native_mio_flag",
        "ENG_native_random",
        "FRA_native_idea",
        "FRA_native_modulo",
        "FRA_native_numeric_flag",
        "GER_native_news",
        "GER_native_focus",
        "POL_native_array",
        "POL_native_flag",
        "RAJ_native_array",
        "RAJ_native_timed_idea",
        "SOV_native_index",
        "SOV_native_meter",
        "SOV_native_rounded",
        "USA_native_global_flag",
        "VEN_native_events",
    }


@pytest.mark.parametrize(
    ("event_dispatch", "expected_token"),
    (
        ("state_event = USA_native_state_events.1", "USA_native_state_events"),
        (
            "unit_leader_event = { id = USA_native_unit_events.1 days = 1 }",
            "USA_native_unit_events",
        ),
        (
            "operative_leader_event = { days = 1 id = USA_native_operative_events.1 }",
            "USA_native_operative_events",
        ),
    ),
)
def test_shared_system_native_write_scanner_covers_all_event_dispatch_effects(
    event_dispatch, expected_token
):
    assert _collect_native_write_tokens(event_dispatch, ("USA_",)) == {expected_token}


def test_shared_system_native_write_scanner_covers_canonical_persistent_operators():
    assert _NATIVE_VARIABLE_BLOCK_EFFECTS == (
        "set_variable",
        "add_to_variable",
        "subtract_from_variable",
        "multiply_variable",
        "divide_variable",
        "modulo_variable",
        "clamp_variable",
        "randomize_variable",
        "set_variable_to_random",
    )
    assert _NATIVE_VARIABLE_SCALAR_OR_BLOCK_EFFECTS == (
        "clear_variable",
        "round_variable",
    )
    assert _NATIVE_ARRAY_BLOCK_EFFECTS == (
        "add_to_array",
        "remove_from_array",
        "resize_array",
    )


def test_shared_system_native_write_scanner_covers_every_executable_owned_role():
    assert _NATIVE_CONTRACT_ROLES == (
        "effect",
        "trigger",
        "on_action",
        "event",
        "idea",
        "decision",
        "category",
    )
