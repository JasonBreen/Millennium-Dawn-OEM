"""Behavioral tests for tools/analysis/system_inspector.py on a synthetic mod tree."""

from __future__ import annotations

import json
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
def report(tmp_path: Path) -> dict:
    for relative, text in FILES.items():
        write_under_str(tmp_path, relative, text)
    tree = system_inspector.read_tree(tmp_path)
    return system_inspector.inspect(tree, r"ZZZ", ("ZZZ_",))


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
    assert unresolved["flags_never_set"] == ["ZZZ_never_set"]
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
