"""The CI sparse workspace includes validator inputs, not unrelated art or audio."""

import shlex
import subprocess
import sys

import pytest
import yaml
from shared.paths import REPO_ROOT
from shared.suite import (
    initialize_git_repository,
    run_bash_step,
    run_git,
    substitute_expressions,
    workflow_step,
    write_under_str,
)

PROFILE = "tools/validation/ci_workspace_profile.txt"


def test_workspace_profile_materializes_only_validator_inputs(tmp_path):
    included = [
        "common/probe.txt",
        "events/probe.txt",
        "history/probe.txt",
        "localisation/english/probe.yml",
        "interface/core.gfx",
        "gfx/flags/probe.tga",
        "gfx/interface/decisions/probe.dds",
        "map/adjacency_rules.txt",
        "music/playlists/probe.txt",
        "resources/documentation/probe.md",
        ".claude/docs/typo-watchlist.md",
        ".github/actions/setup-md-python/action.yml",
        "CLAUDE.md",
        "pyproject.toml",
        "validation_config.json",
        "descriptor.mod",
    ]
    excluded = [
        "gfx/interface/portraits/probe.dds",
        "resources/vanilla/interface/probe.gfx",
        "map/provinces.bmp",
        "music/probe.ogg",
        "music/albums/probe.mp3",
        "music/probe.wav",
    ]
    for relative in included + excluded:
        write_under_str(tmp_path, relative, "probe\n")
    profile = (REPO_ROOT / PROFILE).read_text(encoding="utf-8")
    write_under_str(tmp_path, PROFILE, profile)
    initialize_git_repository(tmp_path, ".")
    result = subprocess.run(
        ["git", "sparse-checkout", "set", "--no-cone", "--stdin"],
        cwd=tmp_path,
        input=profile,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stderr == ""
    assert all((tmp_path / relative).is_file() for relative in included + [PROFILE])
    assert not any((tmp_path / relative).exists() for relative in excluded)


ART = "gfx/interface/portraits/probe.dds"
# Shipped by the CI workspace profile but not the staged one.
OUTSIDE_STAGED = ("gfx/interface/decisions/probe.dds", "localisation/french/p.yml")


def _staged_fetch(tmp_path):
    """Run the workflow's staged fetch into a sparse clone of an older base.

    Returns (checkout, target sha)."""
    source = tmp_path / "source"
    for relative in ("common/probe.txt", "gfx/flags/probe.tga", ART, *OUTSIDE_STAGED):
        write_under_str(source, relative, f"initial {relative}\n")
    initialize_git_repository(source, ".")
    run_git(source, "branch", "base")
    write_under_str(source, "common/probe.txt", "updated content\n")
    write_under_str(source, ART, "updated unused art\n")
    run_git(source, "commit", "-am", "target revision")
    target = run_git(source, "rev-parse", "HEAD").stdout.strip()
    checkout = tmp_path / "checkout"
    run_git(
        tmp_path,
        "clone",
        "--no-checkout",
        "--branch",
        "base",
        source.as_uri(),
        str(checkout),
    )
    fetch = workflow_step("tools-tests", "Fetch merge revision for staged integration")
    command = shlex.split(
        substitute_expressions(
            fetch["run"],
            {"github.repository": "owner/repo", "github.sha": target},
        ).replace("https://github.com/owner/repo.git", source.as_uri())
    )
    assert command[:2] == ["git", "fetch"]
    run_git(checkout, *command[1:])
    return checkout, target


@pytest.mark.skipif(sys.platform == "win32", reason="the step runs in bash on Linux")
def test_staged_worktree_step_checks_out_only_the_staged_profile(tmp_path):
    checkout, target = _staged_fetch(tmp_path)
    for profile in ("staged_sparse_profile.txt", "ci_workspace_profile.txt"):
        body = (REPO_ROOT / "tools/validation" / profile).read_text(encoding="utf-8")
        write_under_str(checkout, f"tools/validation/{profile}", body)
    step = workflow_step("tools-tests", "Create staged integration worktree")
    script = substitute_expressions(
        step["run"],
        {"runner.temp": str(tmp_path / "runner"), "github.sha": target},
    )

    result = run_bash_step(script, checkout)

    assert result.returncode == 0, result.stdout + result.stderr
    worktree = tmp_path / "runner" / "md-staged-validator-test"
    assert (worktree / "common/probe.txt").read_text(
        encoding="utf-8"
    ) == "updated content\n"
    assert (worktree / "gfx/flags/probe.tga").is_file()
    assert not any((worktree / path).exists() for path in (ART, *OUTSIDE_STAGED))


def test_merge_driver_checkout_includes_its_ordering_dependency():
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/changelog-conflict-fixer.yml").read_text(
            encoding="utf-8"
        )
    )
    checkout = workflow["jobs"]["fix-changelog-conflicts"]["steps"][0]
    assert {
        "/tools/merge_changelog.py",
        "/tools/linting/check_changelog.py",
    } <= set(checkout["with"]["sparse-checkout"].split())
