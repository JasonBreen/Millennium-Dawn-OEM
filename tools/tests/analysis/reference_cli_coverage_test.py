"""Exercise reference analysis and reports against isolated miniature mod trees."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import _reference_finder as reports
import audit_leader_portraits as portraits
import calculate_days
import find_idea_references as ideas
import find_scripted_loc_references as scripted_loc
import pytest
import review_branch
import search_add_ideas as additions


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return path


@pytest.fixture
def idea_tree(tmp_path, monkeypatch):
    monkeypatch.setattr(ideas, "REPO_ROOT", tmp_path)
    source = write(
        tmp_path,
        "common/ideas/sample.txt",
        "ideas = {\n country = {\n  TST_live = {\n  }\n"
        "  TST_unused = {\n  }\n  TST_live = {\n  }\n"
        "  OR = {\n  }\n  USA = {\n  }\n }\n}\n",
    )
    target = write(
        tmp_path,
        "events/use.txt",
        "add_ideas = {\n TST_live\n}\nadd_ideas = TST_live_extra\n"
        "has_idea = TST_live\nadd_ideas = TST_live }\n",
    )
    return source, target


def test_idea_search_collects_block_and_scalar_references_once(idea_tree, tmp_path):
    source, target = idea_tree
    assert ideas.extract_idea_names(source) == ["TST_live", "TST_unused"]
    search = ideas.make_idea_searcher([tmp_path / "events", tmp_path / "absent"])
    assert search([]) == {}
    refs = search(["TST_live", "TST_unused"])
    assert refs["TST_unused"] == []
    assert [row[1] for row in refs["TST_live"]] == [2, 5, 6]
    assert all(Path(row[0]).name == target.name for row in refs["TST_live"])


@pytest.mark.parametrize("show_all", [False, True])
def test_idea_cli_report_retains_unused_names_and_optional_references(
    idea_tree, tmp_path, monkeypatch, capsys, show_all
):
    source, _ = idea_tree
    monkeypatch.setattr("builtins.input", lambda _: " y ")
    saved = []

    def save_report(path, root, text):
        assert Path(path).name == path
        saved.append(write(tmp_path, path, text))

    monkeypatch.setattr(reports, "write_text_under", save_report)
    monkeypatch.setattr(
        sys,
        "argv",
        ["find_idea_references.py", str(source), *(["--show-all"] if show_all else [])],
    )
    ideas.main()
    assert len(saved) == 1
    text = saved[0].read_text(encoding="utf-8")
    assert "Unreferenced: 1" in text and "TST_unused" in text
    assert ("TST_live (3 refs)" in text) is show_all
    assert "Total references found: 3" in capsys.readouterr().out


@pytest.mark.parametrize("response", ["n", EOFError, KeyboardInterrupt])
def test_report_decline_and_interruption_do_not_write(idea_tree, monkeypatch, response):
    source, _ = idea_tree

    def answer(_):
        if isinstance(response, type):
            raise response
        return response

    monkeypatch.setattr("builtins.input", answer)
    monkeypatch.setattr(
        reports, "write_text_under", lambda *args: pytest.fail("unexpected report")
    )
    monkeypatch.setattr(sys, "argv", ["find_idea_references.py", str(source)])
    ideas.main()


def test_report_write_failure_is_nonzero(idea_tree, monkeypatch):
    source, _ = idea_tree
    monkeypatch.setattr("builtins.input", lambda _: "y")

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr(reports, "write_text_under", fail)
    monkeypatch.setattr(sys, "argv", ["find_idea_references.py", str(source)])
    with pytest.raises(SystemExit, match="Error writing report: disk full"):
        ideas.main()


@pytest.mark.parametrize("exists", [False, True])
def test_missing_or_empty_source_is_an_explicit_error(tmp_path, monkeypatch, exists):
    source = tmp_path / "source.txt"
    if exists:
        write(tmp_path, source.name, "ideas = {}\n")
    monkeypatch.setattr(
        sys, "argv", ["find_idea_references.py", str(source), "--no-report"]
    )
    with pytest.raises(SystemExit, match="No ideas found" if exists else "not found"):
        ideas.main()


def test_scripted_loc_search_distinguishes_invocations_from_plain_loc_text(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(scripted_loc, "REPO_ROOT", tmp_path)
    source = write(
        tmp_path,
        "common/scripted_localisation/source.txt",
        "defined_text = {\n name = TST_name\n}\ndefined_text = {\n name = TST_name\n}\n",
    )
    write(
        tmp_path,
        "localisation/english/sample.yml",
        'l_english:\n a: "[TST_name]"\n b: "TST_name"\n',
    )
    write(tmp_path, "interface/sample.gui", 'text = "[TST_name]"\n')
    assert scripted_loc.extract_scripted_loc_names(source) == ["TST_name"]
    search = scripted_loc.make_scripted_loc_searcher(
        [source.parent, tmp_path / "localisation", tmp_path / "interface"], source
    )
    assert search([]) == {}
    refs = search(["TST_name"])
    assert len(refs["TST_name"]) == 2
    monkeypatch.setattr(
        sys,
        "argv",
        ["find_scripted_loc_references.py", str(source), "--no-report", "--show-all"],
    )
    scripted_loc.main()
    output = capsys.readouterr().out
    assert "All scripted localisation names are referenced" in output
    assert "Total references found: 2" in output


def test_idea_addition_search_filters_exact_patterns_and_prefixes(tmp_path, capsys):
    target = write(
        tmp_path,
        "events/test.txt",
        "add_ideas = TST_one\nadd_timed_idea = {\n idea = TST_two\n days = 3\n}\n",
    )
    write(tmp_path, "events/ignored.dds", "add_ideas = TST_asset\n")
    matches = additions.search_file(str(target))
    assert [(row[0], row[1], row[3]) for row in matches] == [
        ("TST_one", 1, "add_ideas"),
        ("TST_two", 3, "add_timed_idea"),
    ]
    assert additions.search_directory(str(tmp_path)) == {str(target): matches}
    assert additions.filter_excluded_tags(matches, []) == matches
    assert additions.filter_excluded_tags(matches, ["XXX", "TST_one"]) == matches[1:]
    assert additions.search_file(str(tmp_path / "missing")) == []
    assert "Error reading file" in capsys.readouterr().out


@pytest.mark.parametrize(
    "directory,unique,pattern,exclude",
    [
        (False, False, "all", []),
        (True, True, "add_timed_idea", ["TST_one"]),
        (False, False, "add_ideas", ["TST"]),
    ],
)
def test_idea_addition_cli_selection(
    tmp_path, monkeypatch, capsys, directory, unique, pattern, exclude
):
    target = write(
        tmp_path,
        "test.txt",
        "add_ideas = TST_one\nadd_timed_idea = {\n idea = TST_two\n}\n",
    )
    write(tmp_path, "empty.txt", "no = yes\n")
    args = [
        "search_add_ideas.py",
        str(tmp_path if directory else target),
        str(tmp_path / "missing"),
        "--pattern-type",
        pattern,
    ]
    if directory:
        args.append("--directory")
    if unique:
        args.extend(["--unique-tags", "--no-line-numbers", "--no-full-line"])
    if exclude:
        args.extend(["--exclude", *exclude])
    monkeypatch.setattr(sys, "argv", args)
    additions.main()
    output = capsys.readouterr().out
    assert "Warning:" in output
    if unique:
        assert "Found 1 unique idea tags:" in output and "TST_two" in output
    elif exclude:
        assert "No idea patterns found." in output
    else:
        assert "Found 2 idea patterns in 1 files" in output
        assert "(line 1): add_ideas = TST_one" in output
    additions.print_results(
        {str(target): additions.search_file(str(target))}, False, False
    )
    assert "(line " not in capsys.readouterr().out


@pytest.mark.parametrize(
    "base,changed",
    [(None, ""), ("upstream/main", "README.md\nevents/one.txt\nevents/two.txt")],
)
def test_branch_report_uses_verified_base_and_counts_directories(
    monkeypatch, capsys, base, changed
):
    calls = []

    def git(command, **kwargs):
        calls.append(command)
        output = changed if "--name-only" in command else "review-output"
        return subprocess.CompletedProcess(command, 0, output, "")

    monkeypatch.setattr(review_branch.subprocess, "run", git)
    monkeypatch.setattr(sys, "argv", ["review_branch.py", *([base] if base else [])])
    review_branch.main()
    output = capsys.readouterr().out
    assert calls[0][-1] == f"{base or 'main'}^{{commit}}"
    assert "--- Full diff ---" in output
    if changed:
        assert "    2  events" in output and "    1  ." in output


def test_branch_report_rejects_unknown_base(monkeypatch, capsys):
    monkeypatch.setattr(
        review_branch.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 1, "", ""),
    )
    monkeypatch.setattr(sys, "argv", ["review_branch.py", "missing"])
    with pytest.raises(SystemExit) as error:
        review_branch.main()
    assert error.value.code == 1
    assert "unknown base ref 'missing'" in capsys.readouterr().err


def test_days_calculator_rejects_bad_ranges_and_counts_game_calendar(
    monkeypatch, capsys
):
    values = iter(["1999.1.1", "2000.13.1", "2000.2.30", "2000.1.1", "2001.3.2"])
    monkeypatch.setattr("builtins.input", lambda _: next(values))
    with pytest.raises(StopIteration):
        calculate_days.main()
    output = capsys.readouterr().out
    assert "Year is less than 2000" in output
    assert "Month out of range" in output and "Days out of range" in output
    assert "Days since 2000: 0" in output and "Days since 2000: 425" in output


def test_portrait_audit_separates_missing_and_case_broken_references(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(portraits, "REPO_ROOT", tmp_path)
    write(
        tmp_path,
        "interface/portraits.gfx",
        'texturefile = "gfx/leaders/TST/wrong.dds"\ntexturefile = "gfx/leaders/TST/wrong.dds"\n',
    )
    write(
        tmp_path,
        "common/characters/test.txt",
        'portrait = "bare.dds"\npicture = "Exact.dds"\n',
    )
    fake = SimpleNamespace(
        texture_files={
            "gfx/leaders/TST/Wrong.dds",
            "gfx/leaders/TST/Bare.dds",
            "gfx/leaders/TST/Dead.dds",
            "gfx/leaders/TST/Exact.dds",
            "gfx/interface/other.dds",
        },
        referenced_textures={"gfx/leaders/TST/Exact.dds"},
        game_file_textures=set(),
        texture_filename_lookup={
            "Wrong.dds": [],
            "Bare.dds": [],
            "Dead.dds": [],
            "Exact.dds": [],
        },
        validate_unused_textures=lambda: None,
    )
    monkeypatch.setattr(portraits, "Validator", lambda *a, **kw: fake)
    zero, broken, validator = portraits.run_audit()
    assert validator is fake and zero == ["gfx/leaders/TST/Dead.dds"]
    assert {row[0] for row in broken} == {
        "gfx/leaders/TST/Bare.dds",
        "gfx/leaders/TST/Wrong.dds",
    }
    assert portraits._normalize(r"\gfx\\leaders\TST\a.dds") == "gfx/leaders/TST/a.dds"
    assert (
        portraits._scan_raw_refs(
            str(tmp_path / "missing"), portraits._GFX_FILE_REF_PATTERNS
        )
        == []
    )
    for flags in ([], ["--json"]):
        monkeypatch.setattr(sys, "argv", ["audit_leader_portraits.py", *flags])
        portraits.main()
        output = capsys.readouterr().out
        if flags:
            assert json.loads(output)["zero_reference"] == zero
        else:
            assert "Broken-reference: 2" in output
