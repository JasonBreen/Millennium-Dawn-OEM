"""Behavioral tests for tools/analysis/system_inspector.py on a synthetic mod tree."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
from shared.suite import write_under_str

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from tools.analysis import system_inspector  # noqa: E402

FILES = {
    "common/scripted_effects/ZZZ_effects.txt": """ZZZ_start = {
\tZZZ_missing_effect = yes
\tset_country_flag = ZZZ_started
\tset_variable = { global.ZZZ_counter = 1 }
\tif = { limit = { check_variable = { global.ZZZ_never_written > 0 } } country_event = zzz.1 }
\tcountry_event = zzz.9
\tshared_helper = yes
}

ZZZ_orphan = {
\tlog = "nobody calls this"
}
""",
    "common/scripted_triggers/ZZZ_triggers.txt": """ZZZ_ready = {
\thas_country_flag = ZZZ_started
\thas_country_flag = ZZZ_never_set
}
""",
    "events/ZZZ.txt": """add_namespace = zzz

country_event = {
\tid = zzz.1
\ttitle = zzz.1.t
\tdesc = zzz.1.d
\tis_triggered_only = yes

\toption = {
\t\tname = zzz.1.a
\t\tZZZ_start = yes
\t}
}

country_event = {
\tid = zzz.2
\ttitle = zzz.2.t
\tdesc = zzz.2.d
\tis_triggered_only = yes
}
""",
    "localisation/english/ZZZ_l_english.yml": """﻿l_english:
 zzz.1.t: "Title"
 zzz.1.a: "Option"
 zzz.2.t: "Title"
 zzz.2.d: "Desc"
""",
    "common/scripted_effects/shared_effects.txt": """shared_helper = {
\tlog = "shared"
}

uses_the_system = {
\tif = { limit = { ZZZ_ready = yes } }
}
""",
    "common/on_actions/00_on_actions.txt": """on_actions = {
\ton_startup = { effect = { ZZZ_start = yes } }
}
""",
}


@pytest.fixture
def mod_root(tmp_path: Path) -> Path:
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    return tmp_path


def inspect_mod(root: Path) -> dict:
    return system_inspector.inspect(system_inspector.read_tree(root), r"ZZZ", ("ZZZ_",))


@pytest.fixture
def report(mod_root: Path) -> dict:
    return inspect_mod(mod_root)


def test_files_and_definitions_belong_to_the_system(report):
    paths = {e["path"] for entries in report["files"].values() for e in entries}
    assert paths == {
        "common/scripted_effects/ZZZ_effects.txt",
        "common/scripted_triggers/ZZZ_triggers.txt",
        "events/ZZZ.txt",
        "localisation/english/ZZZ_l_english.yml",
    }
    assert report["definitions"]["scripted_effect"] == ["ZZZ_orphan", "ZZZ_start"]
    assert report["definitions"]["scripted_trigger"] == ["ZZZ_ready"]
    assert report["definitions"]["event"] == ["zzz.1", "zzz.2"]


def test_hooks_list_outside_files_that_reach_in(report):
    assert report["hooks"] == {
        "common/on_actions/00_on_actions.txt": ["ZZZ_start"],
        "common/scripted_effects/shared_effects.txt": ["ZZZ_ready"],
    }


def test_dependencies_name_the_outside_definition_and_its_file(report):
    assert report["dependencies"]["scripted_effect"] == [
        {
            "name": "shared_helper",
            "defined_in": "common/scripted_effects/shared_effects.txt",
        }
    ]


def test_unresolved_references_point_at_nothing(report):
    unresolved = report["unresolved"]
    assert unresolved["calls"] == ["ZZZ_missing_effect"]
    assert unresolved["events"] == ["zzz.9"]
    assert unresolved["localisation"] == ["zzz.1.d"]
    assert unresolved["flags_never_set"] == ["country:ZZZ_never_set"]
    assert unresolved["globals_never_written"] == ["ZZZ_never_written"]


def test_unused_definitions_are_never_referenced(report):
    assert report["unused"] == {
        "scripted_effects_and_triggers": ["ZZZ_orphan"],
        "triggered_only_events": ["zzz.2"],
    }


def test_script_language_words_are_not_hooks_or_dependencies(tmp_path):
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    write_under_str(
        tmp_path,
        "common/scripted_effects/00_scriptlanguage.txt",
        "yes = { custom_effect_tooltip = script.0.yes }\n",
    )
    report = system_inspector.inspect(
        system_inspector.read_tree(tmp_path), r"ZZZ", ("ZZZ_",)
    )
    names = [e["name"] for e in report["dependencies"]["scripted_effect"]]
    assert "yes" not in names


def test_cli_prints_json_and_rejects_a_pattern_with_no_files(tmp_path, capsys):
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    code = system_inspector.main(
        ["--path-pattern", "ZZZ", "--prefix", "ZZZ_", "--root", str(tmp_path), "--json"]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["unresolved"]["calls"] == ["ZZZ_missing_effect"]

    assert (
        system_inspector.main(["--path-pattern", "NOPE", "--root", str(tmp_path)]) == 1
    )
    assert "No files" in capsys.readouterr().err


def test_text_report_honours_sections(tmp_path, capsys):
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    system_inspector.main(
        [
            "--path-pattern",
            "ZZZ",
            "--prefix",
            "ZZZ_",
            "--root",
            str(tmp_path),
            "--section",
            "unused",
        ]
    )
    out = capsys.readouterr().out
    assert "== unused" in out
    assert "ZZZ_orphan" in out
    assert "== hooks" not in out


def test_presets_cover_the_documented_systems():
    assert {"stalker", "top", "ai_race", "econ_forum"} <= set(system_inspector.PRESETS)


@pytest.mark.parametrize(
    "rel",
    [
        "events/Targeted Operations.txt",
        "events/Targeted Operations Runtime.txt",
        "events/Targeted Operations Redesign.txt",
        "common/scripted_effects/01_targeted_operations_registry.txt",
    ],
)
def test_top_preset_matches_its_event_files(rel):
    assert re.search(system_inspector.PRESETS["top"].path_pattern, rel)


@pytest.mark.parametrize("id_first", [True, False])
def test_nested_dispatch_is_not_an_event_definition(mod_root, id_first):
    ident = "id = zzz.1"
    nested = "immediate = { country_event = { id = zzz.9 days = 1 } }"
    fields = [ident, nested] if id_first else [nested, ident]
    write_under_str(
        mod_root,
        "events/ZZZ.txt",
        "country_event = {\n"
        + "\n".join(fields)
        + '\nis_triggered_only = yes\nlog = "escaped \\"quote\\" and { braces }"\n}\n',
    )
    report = inspect_mod(mod_root)
    assert report["definitions"]["event"] == ["zzz.1"]
    assert report["unresolved"]["events"] == ["zzz.9"]
    assert system_inspector.event_blocks(
        system_inspector.read_tree(mod_root).code["events/ZZZ.txt"]
    ) == [("zzz.1", True)]


def test_missing_option_label_is_reported_without_treating_other_names_as_loc(mod_root):
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_l_english.yml",
        FILES["localisation/english/ZZZ_l_english.yml"].replace(
            ' zzz.1.a: "Option"\n', ""
        ),
    )
    write_under_str(
        mod_root,
        "common/characters/ZZZ_characters.txt",
        'characters = { ZZZ_character = { name = "ZZZ_person_name" } }\n',
    )
    assert inspect_mod(mod_root)["unresolved"]["localisation"] == ["zzz.1.a", "zzz.1.d"]


@pytest.mark.parametrize("message", ["ZZZ_orphan", "A report mentions ZZZ_orphan"])
def test_prose_cannot_create_hooks_dependencies_or_hide_unused_symbols(
    mod_root, message
):
    write_under_str(
        mod_root,
        "common/on_actions/00_on_actions.txt",
        f'on_actions = {{ on_startup = {{ effect = {{ log = "{message}" }} }} }}\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/outside.txt",
        'outside_helper = { log = "unused" }\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_prose.txt",
        'ZZZ_prose = { log = "outside_helper" }\n',
    )
    report = inspect_mod(mod_root)
    assert "common/on_actions/00_on_actions.txt" not in report["hooks"]
    assert "ZZZ_orphan" in report["unused"]["scripted_effects_and_triggers"]
    assert "outside_helper" not in [
        entry["name"] for entry in report["dependencies"]["scripted_effect"]
    ]


def test_quoted_identifiers_and_scripted_loc_remain_references(mod_root):
    write_under_str(
        mod_root,
        "common/ideas/outside.txt",
        "ideas = { country = { outside_idea = { } } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_quoted.txt",
        'ZZZ_quoted = { add_ideas = "outside_idea" }\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_localisation/ZZZ_text.txt",
        "defined_text = {\n name = ZZZ_display\n}\n",
    )
    write_under_str(
        mod_root,
        "interface/outside.gui",
        'instantTextBoxType = { text = "Report: [ZZZ_display]" }\n',
    )
    report = inspect_mod(mod_root)
    assert report["dependencies"]["idea"] == [
        {"name": "outside_idea", "defined_in": "common/ideas/outside.txt"}
    ]
    assert report["hooks"]["interface/outside.gui"] == ["ZZZ_display"]


@pytest.mark.parametrize(
    "read_kind,write_kind",
    [
        ("country", "global"),
        ("global", "country"),
        ("state", "character"),
        ("character", "state"),
        ("project", "country"),
        ("unit_leader", "country"),
        ("mio", "country"),
    ],
)
@pytest.mark.parametrize("block_value", [False, True])
def test_flag_resolution_requires_matching_scope(
    mod_root, read_kind, write_kind, block_value
):
    value = "{ flag = ZZZ_same_name }" if block_value else "ZZZ_same_name"
    write_under_str(
        mod_root,
        "common/scripted_effects/outside_flags.txt",
        f"outside_flags = {{ set_{write_kind}_flag = {value} }}\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_triggers/ZZZ_flags.txt",
        f"ZZZ_flags = {{ has_{read_kind}_flag = {value} }}\n",
    )
    assert (
        f"{read_kind}:ZZZ_same_name"
        in inspect_mod(mod_root)["unresolved"]["flags_never_set"]
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/outside_flags.txt",
        f"outside_flags = {{ set_{read_kind}_flag = {value} }}\n",
    )
    assert (
        f"{read_kind}:ZZZ_same_name"
        not in inspect_mod(mod_root)["unresolved"]["flags_never_set"]
    )


def test_modifier_definitions_have_hooks_and_dependencies(mod_root):
    write_under_str(
        mod_root,
        "common/modifier_definitions/ZZZ_modifiers.txt",
        "ZZZ_applied_power = { color_type = bad }\n",
    )
    write_under_str(
        mod_root,
        "common/modifier_definitions/outside.txt",
        "outside_power = { color_type = bad }\n",
    )
    write_under_str(
        mod_root,
        "common/synchronized_dynamic_tokens/MD_tokens.txt",
        "ZZZ_applied_power\n",
    )
    write_under_str(
        mod_root,
        "common/dynamic_modifiers/ZZZ_dynamic.txt",
        "ZZZ_dynamic = { enable = { always = yes } outside_power = ZZZ_power }\n",
    )
    report = inspect_mod(mod_root)
    assert report["hooks"]["common/synchronized_dynamic_tokens/MD_tokens.txt"] == [
        "ZZZ_applied_power"
    ]
    assert report["dependencies"]["modifier_definition"] == [
        {
            "name": "outside_power",
            "defined_in": "common/modifier_definitions/outside.txt",
        }
    ]


@pytest.mark.parametrize("indent", ["", " "])
@pytest.mark.parametrize("version", ["", "0"])
def test_english_keys_resolve_with_zero_or_one_space_indent(mod_root, indent, version):
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_label_l_english.yml",
        f'l_english:\n{indent}ZZZ_label:{version} "Known label"\n',
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_label.txt",
        "ZZZ_show_label = { custom_effect_tooltip = ZZZ_label }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["localisation"] == ["zzz.1.d"]


def test_gui_only_localisation_is_checked(mod_root):
    write_under_str(
        mod_root,
        "interface/ZZZ_dashboard.gui",
        'guiTypes = { instantTextBoxType = { text = "ZZZ_dashboard_title" } }\n',
    )
    assert "ZZZ_dashboard_title" in inspect_mod(mod_root)["unresolved"]["localisation"]
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_dashboard_l_english.yml",
        'l_english:\n ZZZ_dashboard_title: "Dashboard"\n',
    )
    assert (
        "ZZZ_dashboard_title" not in inspect_mod(mod_root)["unresolved"]["localisation"]
    )


def test_bare_definitions_remain_linkable_without_linking_language_helpers(mod_root):
    write_under_str(
        mod_root,
        "common/ideas/ZZZ_ideas.txt",
        "ideas = { country = { asio = { } ausfta = { } } }\n",
    )
    write_under_str(
        mod_root,
        "common/ideas/outside.txt",
        "ideas = { country = { thirdparty = { } } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_bare.txt",
        "ZZZ_use_bare = { add_ideas = thirdparty }\n"
        + "\n".join(f"{name} = {{ }}" for name in ("yes", "no", "from", "for")),
    )
    write_under_str(
        mod_root,
        "common/national_focus/outside.txt",
        "focus = { available = { always = yes } completion_reward = { "
        "add_ideas = asio remove_ideas = ausfta } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["hooks"]["common/national_focus/outside.txt"] == ["asio", "ausfta"]
    assert report["dependencies"]["idea"] == [
        {"name": "thirdparty", "defined_in": "common/ideas/outside.txt"}
    ]


@pytest.mark.parametrize("loc_file", ["ZZZ_labels", "outside_labels"])
def test_localisation_cannot_hide_unused_code(mod_root, loc_file):
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_bare_orphan.txt",
        "bare_orphan = { }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_triggers/ZZZ_lonely_trigger.txt",
        "ZZZ_lonely_trigger = { always = yes }\n",
    )
    write_under_str(
        mod_root,
        f"localisation/english/{loc_file}_l_english.yml",
        'l_english:\n ZZZ_orphan: "Label"\n bare_orphan: "Label"\n'
        ' ZZZ_lonely_trigger: "Label"\n zzz.2: "Label"\n',
    )
    assert inspect_mod(mod_root)["unused"] == {
        "scripted_effects_and_triggers": [
            "ZZZ_lonely_trigger",
            "ZZZ_orphan",
            "bare_orphan",
        ],
        "triggered_only_events": ["zzz.2"],
    }


@pytest.mark.parametrize(
    "text,line_count",
    [
        ("", 0),
        ("foo", 1),
        ("foo\n", 1),
        ("\n", 1),
        ("foo\nbar", 2),
        ("foo\nbar\n", 2),
        ("foo\r\n", 1),
    ],
)
def test_line_counts_do_not_include_an_empty_eof_line(tmp_path, text, line_count):
    write_under_str(tmp_path, "common/scripted_effects/ZZZ_lines.txt", text)
    report = inspect_mod(tmp_path)
    assert report["files"]["scripted_effect"] == [
        {"path": "common/scripted_effects/ZZZ_lines.txt", "lines": line_count}
    ]
    assert f"{line_count} lines" in system_inspector.render(report, ("files",), 10)


def test_weighted_event_pools_report_missing_dispatches(mod_root):
    write_under_str(
        mod_root,
        "common/on_actions/ZZZ_on_actions.txt",
        "on_actions = { on_weekly = { random_events = { "
        '100 = 0 100 = zzz.1 200 = "zzz.99" } '
        "other_block = { 100 = zzz.98 } } }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["events"] == ["zzz.9", "zzz.99"]


def test_localisation_global_substitutions_are_reads_but_prose_is_not_code(mod_root):
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_status_l_english.yml",
        'l_english:\n ZZZ_status: "[?global.ZZZ_loc_only|0] [?global.ZZZ_counter|0]"\n'
        ' ZZZ_prose: "global.ZZZ_plaintext set_variable = { global.ZZZ_loc_only = 1 }"\n'
        ' # ZZZ_comment: "[?global.ZZZ_comment|0]"\n',
    )
    assert inspect_mod(mod_root)["unresolved"]["globals_never_written"] == [
        "ZZZ_loc_only",
        "ZZZ_never_written",
    ]
    write_under_str(
        mod_root,
        "common/scripted_effects/outside_global.txt",
        "outside_global = { set_variable = { global.ZZZ_loc_only = 1 } }\n",
    )
    assert inspect_mod(mod_root)["unresolved"]["globals_never_written"] == [
        "ZZZ_never_written"
    ]


def test_focus_ids_are_direct_definitions_with_external_hooks(mod_root):
    write_under_str(
        mod_root,
        "common/national_focus/ZZZ_focus.txt",
        "focus_tree = { id = ZZZ_tree focus = { id = ZZZ_root } }\n"
        "shared_focus = { completion_reward = { country_event = { id = zzz.9 } } "
        'id = "ZZZ_shared" }\n'
        "joint_focus = { id = ZZZ_joint }\n",
    )
    write_under_str(
        mod_root,
        "events/outside_focus.txt",
        "country_event = { id = outside.1 trigger = { has_completed_focus = ZZZ_root } "
        "immediate = { complete_national_focus = ZZZ_shared } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["definitions"]["focus"] == ["ZZZ_joint", "ZZZ_root", "ZZZ_shared"]
    assert report["hooks"]["events/outside_focus.txt"] == ["ZZZ_root", "ZZZ_shared"]
    assert "ZZZ_tree" not in report["definitions"]["focus"]


def test_parameterized_calls_are_checked_without_counting_definitions(mod_root):
    write_under_str(
        mod_root,
        "common/scripted_effects/ZZZ_parameterized.txt",
        "ZZZ_parameterized = { ZZZ_missing_block = { TARGET = USA } "
        "shared_helper = { AMOUNT = 2 } ZZZ_start = { TARGET = USA } }\n",
    )
    write_under_str(
        mod_root,
        "common/scripted_guis/ZZZ_windows.txt",
        "scripted_gui = { ZZZ_window = { window_name = ZZZ_window } }\n",
    )
    write_under_str(
        mod_root,
        "common/ideas/ZZZ_ideas.txt",
        "ideas = { country = { ZZZ_idea = { } } }\n",
    )
    report = inspect_mod(mod_root)
    assert report["unresolved"]["calls"] == ["ZZZ_missing_block", "ZZZ_missing_effect"]
    assert report["dependencies"]["scripted_effect"] == [
        {
            "name": "shared_helper",
            "defined_in": "common/scripted_effects/shared_effects.txt",
        }
    ]


@pytest.mark.parametrize("field", ["pdx_tooltip", "pdx_tooltip_delayed", "buttonText"])
@pytest.mark.parametrize("quoted", [False, True])
def test_gui_tooltips_and_button_labels_resolve_localisation(mod_root, field, quoted):
    value = '"ZZZ_gui_label"' if quoted else "ZZZ_gui_label"
    write_under_str(
        mod_root,
        "interface/ZZZ_dashboard.gui",
        f"guiTypes = {{ buttonType = {{ {field} = {value} }} }}\n",
    )
    assert "ZZZ_gui_label" in inspect_mod(mod_root)["unresolved"]["localisation"]
    write_under_str(
        mod_root,
        "localisation/english/ZZZ_gui_l_english.yml",
        'l_english:\n ZZZ_gui_label:0 "Label"\n',
    )
    assert "ZZZ_gui_label" not in inspect_mod(mod_root)["unresolved"]["localisation"]


@pytest.mark.parametrize("scripted_kind", ["scripted_effects", "scripted_triggers"])
@pytest.mark.parametrize("call_value", ["yes", "no", "{ AMOUNT = 1 }"])
def test_shared_idea_name_is_not_a_scripted_dependency_until_called(
    mod_root, scripted_kind, call_value
):
    write_under_str(
        mod_root,
        f"common/{scripted_kind}/outside_economy.txt",
        "recession = { }\n",
    )
    idea_file = "common/ideas/ZZZ_economy.txt"
    idea = "ideas = { country = { recession = { available = { has_idea = recession }"
    write_under_str(mod_root, idea_file, idea + " } } }\n")
    kind = scripted_kind.removesuffix("s")
    assert not any(
        entry["name"] == "recession"
        for entry in inspect_mod(mod_root)["dependencies"].get(kind, ())
    )
    write_under_str(
        mod_root,
        idea_file,
        idea
        + f" {'on_remove' if scripted_kind == 'scripted_effects' else 'allowed'}"
        + f" = {{ recession = {call_value} }} }} }} }}\n",
    )
    assert {
        "name": "recession",
        "defined_in": f"common/{scripted_kind}/outside_economy.txt",
    } in inspect_mod(mod_root)["dependencies"][kind]
