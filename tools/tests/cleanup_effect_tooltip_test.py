"""cleanup_effect_tooltip.py collapses only pure custom_effect_tooltip wrappers.

Covers the core transform (single- and multi-line), the must-NOT-touch cases
(real effects, empty blocks, comments), and the reference-dir guards: resources/
(AGENTS.md) and .claude/ (holds sibling worktree checkouts) must never be
rewritten, via both a file path and a directory entry point.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import cleanup_effect_tooltip as cet  # noqa: E402

_WRAP_SINGLE = "foo = {\n\teffect_tooltip = { custom_effect_tooltip = bar_tt }\n}\n"
_WRAP_MULTI = (
    "foo = {\n\teffect_tooltip = {\n\t\tcustom_effect_tooltip = bar_tt\n\t}\n}\n"
)
_COLLAPSED = "foo = {\n\tcustom_effect_tooltip = bar_tt\n}\n"


def test_single_line_wrapper_collapses(tmp_path):
    f = tmp_path / "ctrl.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    cet.main([str(f)])
    assert f.read_text(encoding="utf-8") == _COLLAPSED


def test_multi_line_wrapper_collapses(tmp_path):
    f = tmp_path / "ctrl.txt"
    f.write_text(_WRAP_MULTI, encoding="utf-8")
    cet.main([str(f)])
    assert f.read_text(encoding="utf-8") == _COLLAPSED


def test_real_effect_block_untouched():
    src = "\teffect_tooltip = {\n\t\tadd_stability = 0.1\n\t}\n".splitlines(
        keepends=True
    )
    out, n = cet.simplify_effect_tooltip_block(src)
    assert n == 0
    assert out == src


def test_mixed_and_empty_and_comment_untouched():
    for src in (
        "\teffect_tooltip = {\n\t\tcustom_effect_tooltip = X\n\t\tadd_stability = 0.1\n\t}\n",
        "\teffect_tooltip = { }\n",
        "\teffect_tooltip = {\n\t\t# note\n\t\tcustom_effect_tooltip = X\n\t}\n",
    ):
        lines = src.splitlines(keepends=True)
        out, n = cet.simplify_effect_tooltip_block(lines)
        assert n == 0
        assert out == lines


def test_resources_file_path_not_modified(tmp_path):
    res = tmp_path / "resources"
    res.mkdir()
    f = res / "keep.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    cet.main([str(f)])
    assert f.read_text(encoding="utf-8") == _WRAP_SINGLE


def test_claude_directory_not_walked(tmp_path):
    # .claude/worktrees holds full sibling checkouts of other branches.
    wt = tmp_path / ".claude" / "worktrees" / "x" / "common"
    wt.mkdir(parents=True)
    f = wt / "keep.txt"
    f.write_text(_WRAP_SINGLE, encoding="utf-8")
    cet.main([str(tmp_path / ".claude")])
    assert f.read_text(encoding="utf-8") == _WRAP_SINGLE


def test_repo_own_resources_and_claude_excluded(tmp_path):
    repo_root = tmp_path / "MillenniumDawn"
    for sub in ("resources", ".claude"):
        target = repo_root / sub / "ref.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_WRAP_SINGLE, encoding="utf-8")
        assert cet._is_excluded_path(str(target), repo_root=str(repo_root))


def test_ancestor_excluded_name_outside_repo_not_excluded(tmp_path):
    # A checkout nested under an ancestor literally named "resources" must not
    # exclude the whole repo: relative to its own root nothing is excluded.
    repo_root = tmp_path / "resources" / "MillenniumDawn"
    target = repo_root / "common" / "foo.txt"
    target.parent.mkdir(parents=True)
    target.write_text(_WRAP_SINGLE, encoding="utf-8")
    assert not cet._is_excluded_path(str(target), repo_root=str(repo_root))


def test_find_redundant_effect_tooltip_wrappers_block():
    src = "foo = {\n\teffect_tooltip = {\n\t\tcustom_effect_tooltip = bar_tt\n\t}\n}\n"
    lines = src.splitlines(keepends=True)
    issues = cet.find_redundant_effect_tooltip_wrappers(lines)
    assert len(issues) == 1
    assert issues[0][0] == 2
    assert "redundant effect_tooltip = { } wrapper" in issues[0][1]


def test_find_redundant_effect_tooltip_wrappers_inline():
    src = (
        "foo = {\n\teffect_tooltip = { custom_effect_tooltip = bar_tt } # comment\n}\n"
    )
    lines = src.splitlines(keepends=True)
    issues = cet.find_redundant_effect_tooltip_wrappers(lines)
    assert len(issues) == 1
    assert issues[0][0] == 2
    assert "redundant effect_tooltip = { } wrapper" in issues[0][1]


def test_find_redundant_effect_tooltip_wrappers_no_issues():
    valid_cases = [
        "foo = {\n\teffect_tooltip = {\n\t\tadd_stability = 0.1\n\t}\n}\n",
        "foo = {\n\teffect_tooltip = { }\n}\n",
        "foo = {\n\teffect_tooltip = {\n\t\t# note\n\t\tcustom_effect_tooltip = X\n\t}\n}\n",
        "foo = {\n\teffect_tooltip = { custom_effect_tooltip = X add_stability = 0.1 }\n}\n",
    ]
    for src in valid_cases:
        lines = src.splitlines(keepends=True)
        issues = cet.find_redundant_effect_tooltip_wrappers(lines)
        assert len(issues) == 0
