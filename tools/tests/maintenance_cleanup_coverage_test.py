"""Exercise cleanup commands against isolated resources and mocked subprocesses."""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import cleanup_legacy_resources as legacy
import optimize_repo as optimize
import pytest
import resources_cleanup as resources


def _file(root, name, content="fixture"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(content)
    return path


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    root = tmp_path / "backup checkout" / "resources"
    root.mkdir(parents=True)
    monkeypatch.setattr(legacy, "RESOURCES_DIR", root)
    monkeypatch.setattr(resources, "RESOURCES_DIR", root)
    monkeypatch.setattr(resources, "ARCHIVE_DIR", tmp_path / "archive")
    monkeypatch.setattr(optimize, "REPO_ROOT", tmp_path)
    return root


def _cli(monkeypatch, module, args, answers=()):
    responses = iter(answers)
    monkeypatch.setattr(sys, "argv", [module.__name__, *args])
    monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
    module.main()


@pytest.mark.parametrize("module", [legacy, resources])
@pytest.mark.parametrize(
    ("size", "expected"),
    [
        (0, "0.0 B"),
        (1024, "1.0 KB"),
        (1024**2, "1.0 MB"),
        (1024**3, "1.0 GB"),
        (1024**4, "1.0 TB"),
    ],
)
def test_size_units(module, size, expected):
    assert module.format_size(size) == expected


def test_legacy_selection_honors_nested_and_protected_paths(sandbox):
    selected = {
        _file(sandbox, "old art/plain.dds"),
        _file(sandbox, "current/deprecated/sample.dds"),
        _file(sandbox, "archived-branches/branch/script.txt"),
        _file(sandbox, "old root.txt"),
        _file(sandbox, "documentation-backup/old.txt"),
    }
    protected = {
        _file(sandbox, "parliament_generator/old example.py"),
        _file(sandbox, "old art/corporate_history_contract.json"),
        _file(sandbox, "old art/documentation/old source.txt"),
        _file(sandbox, "current/live.dds"),
    }
    assert set(legacy.get_files_to_remove()) == selected
    assert all(not legacy.should_remove_file(path) for path in protected)
    assert not legacy.should_remove_dir(sandbox)
    assert not legacy.should_remove_file(sandbox.parent / "old unrelated.txt")


@pytest.mark.parametrize("args", [["--scan"], ["--list"], [], ["--clean"]])
def test_legacy_empty_or_missing_directory(sandbox, monkeypatch, capsys, args):
    sandbox.rmdir()
    _cli(monkeypatch, legacy, args)
    output = capsys.readouterr().out
    assert legacy.get_files_to_remove() == []
    assert any(text in output for text in ("0", "No files", "usage:"))


@pytest.mark.parametrize("args", [["--scan"], ["--list"], ["--clean", "--dry-run"]])
def test_legacy_preview_retains_all_files(sandbox, monkeypatch, capsys, args):
    paths = [_file(sandbox, f"old dir {i}/sample.txt") for i in range(22)]
    _cli(monkeypatch, legacy, args)
    output = capsys.readouterr().out
    assert all(path.read_text(encoding="utf-8") == "fixture" for path in paths)
    assert "22 files" in output or "Total: 22" in output
    if "--scan" in args:
        assert "12 more directories" in output
    if "--dry-run" in args:
        assert "2 more" in output


@pytest.mark.parametrize("answer", ["", "no", "Y"])
def test_legacy_confirmation_and_empty_directory_protection(
    sandbox, monkeypatch, capsys, answer
):
    target = _file(sandbox, "old art/obsolete.dds")
    keep = _file(sandbox, "old art/documentation/guide.txt")
    empty_keep = sandbox / "parliament_generator"
    empty_keep.mkdir()
    removable = _file(sandbox, "deprecated art/obsolete.dds")
    _cli(monkeypatch, legacy, ["--clean"], [answer])
    assert target.exists() is (answer != "Y")
    assert removable.exists() is (answer != "Y")
    assert keep.exists() and empty_keep.is_dir()
    output = capsys.readouterr().out
    assert ("Removed 2 files" if answer == "Y" else "Cancelled.") in output
    if answer == "Y":
        assert not removable.parent.exists()
        assert "Removed 1 empty directories" in output


def test_legacy_cleanup_continues_after_permission_error(sandbox, monkeypatch, capsys):
    blocked = _file(sandbox, "old art/blocked.dds")
    removable = _file(sandbox, "old art/removable.dds")
    original = Path.unlink

    def unlink(path, *args, **kwargs):
        if path == blocked:
            raise PermissionError("locked fixture")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink)
    _cli(monkeypatch, legacy, ["--clean"], ["y"])
    output = capsys.readouterr()
    assert blocked.exists() and not removable.exists()
    assert "locked fixture" in output.err
    assert "Removed 1 files" in output.out


def test_resource_scan_uses_resource_relative_names(sandbox):
    expected = {
        "legacy": _file(sandbox, "old art/obsolete.dds"),
        "unintegrated": _file(sandbox, "candidate.PNG"),
        "keep": _file(sandbox, "documentation/old example.txt"),
        "unknown": _file(sandbox, "active/unit.dds"),
    }
    infos, categories = resources.scan_resources()
    assert len(infos) == 4
    for category, path in expected.items():
        assert [info["path"] for info in categories[category]] == [path]
        assert categories[category][0]["size"] == len("fixture")
    assert not resources.is_legacy_content(sandbox.parent / "old unrelated.txt")
    assert not resources.get_file_info(
        _file(sandbox, "documentation-backup/obsolete.dds")
    )["is_keep_dir"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("sheet.XLSX", True),
        ("notes.txt", True),
        ("scripted_effects.txt", False),
        ("art.dds", False),
    ],
)
def test_resource_unintegrated_extensions(sandbox, name, expected):
    assert resources.is_unintegrated_file(sandbox / name) is expected


@pytest.mark.parametrize("args", [["--scan"], ["--list"], [], ["--clean"]])
def test_resources_missing_directory_is_valid_empty_scan(
    sandbox, monkeypatch, capsys, args
):
    sandbox.rmdir()
    _cli(monkeypatch, resources, args)
    assert resources.get_all_files(sandbox) == []
    assert "does not exist" in capsys.readouterr().out


def test_resources_scan_report_truncates_large_category(sandbox, monkeypatch, capsys):
    paths = [_file(sandbox, f"old art/{i}.dds") for i in range(12)]
    _file(sandbox, "notes.csv")
    _cli(monkeypatch, resources, ["--scan"])
    output = capsys.readouterr().out
    assert "Total files: 13" in output
    assert "2 more files" in output
    assert "Review unintegrated files" in output
    assert "Archive or delete legacy content" in output
    _cli(monkeypatch, resources, ["--list"])
    assert "Total: 13 files" in capsys.readouterr().out
    assert all(path.exists() for path in paths)


@pytest.mark.parametrize("category", ["legacy", "unintegrated"])
def test_resource_interactive_choices_select_without_mutation(
    sandbox, monkeypatch, capsys, category
):
    paths = [_file(sandbox, f"old art/{i}.dds", "x" * (10 - i)) for i in range(5)]
    categories = {"legacy": [], "unintegrated": []}
    categories[category] = [resources.get_file_info(path) for path in paths]
    answers = iter(["invalid", "delete", "archive", "keep", "quit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert resources.interactive_cleanup(categories) == ([paths[0]], [paths[1]])
    assert all(path.exists() for path in paths)
    assert "Invalid choice" in capsys.readouterr().out


@pytest.mark.parametrize("action", ["archive", "delete"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_resources_bulk_actions_are_scoped_to_legacy(
    sandbox, monkeypatch, capsys, action, dry_run
):
    target = _file(sandbox, "old art/remove.dds")
    keep = _file(sandbox, "documentation/old guide.txt")
    other = _file(sandbox, "pending.png")
    args = [f"--{action}-all-legacy"] + (["--dry-run"] if dry_run else [])
    _cli(monkeypatch, resources, args, ["DELETE"])
    assert target.exists() is dry_run
    assert keep.exists() and other.exists()
    archived = resources.ARCHIVE_DIR / "old art/remove.dds"
    assert archived.exists() is (action == "archive" and not dry_run)
    if archived.exists():
        assert archived.read_text(encoding="utf-8") == "fixture"
    assert ("DRY RUN" in capsys.readouterr().out) is dry_run


def test_resources_bulk_delete_requires_exact_confirmation(
    sandbox, monkeypatch, capsys
):
    target = _file(sandbox, "old art/remove.dds")
    _cli(monkeypatch, resources, ["--delete-all-legacy"], ["delete"])
    assert target.exists()
    assert "Deletion cancelled" in capsys.readouterr().out


@pytest.mark.parametrize("dry_run,confirm", [(False, "y"), (False, "n"), (True, "y")])
def test_resources_interactive_commit_requires_confirmation(
    sandbox, monkeypatch, capsys, dry_run, confirm
):
    target = _file(sandbox, "old art/remove.dds")
    archived = _file(sandbox, "drawing.png")
    args = ["--clean"] + (["--dry-run"] if dry_run else [])
    _cli(monkeypatch, resources, args, ["d", "a", confirm, confirm])
    expected_exists = dry_run or confirm != "y"
    assert target.exists() is expected_exists
    assert archived.exists() is expected_exists
    output = capsys.readouterr().out
    assert "Files to DELETE (1)" in output and "Files to ARCHIVE (1)" in output
    if dry_run:
        assert "DRY RUN - No files were modified" in output


def test_resources_empty_and_failed_operations(sandbox, monkeypatch, capsys):
    assert resources.archive_files([]) == resources.delete_files([]) == 0
    missing = sandbox / "old missing.dds"
    assert resources.delete_files([missing]) == 0

    def failed_move(*args):
        raise PermissionError("locked fixture")

    monkeypatch.setattr(resources.shutil, "move", failed_move)
    target = _file(sandbox, "old art/blocked.dds")
    assert resources.archive_files([target]) == 0
    assert target.exists()
    output = capsys.readouterr().err
    assert "Error deleting" in output and "Error archiving" in output


@pytest.mark.parametrize("returncode", [0, 1])
@pytest.mark.parametrize("stderr", ["", "diagnostic"])
def test_optimization_command_result_and_subprocess_contract(
    sandbox, monkeypatch, returncode, stderr
):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=returncode, stdout="result", stderr=stderr)

    monkeypatch.setattr(optimize.subprocess, "run", run)
    result = optimize.run_command(["fixture", "--scan"])
    assert result == (
        returncode == 0,
        "result" + (f"\nSTDERR:\n{stderr}" if stderr else ""),
    )
    assert calls == [
        (
            ["fixture", "--scan"],
            {
                "capture_output": True,
                "text": True,
                "cwd": optimize.REPO_ROOT,
                "timeout": 300,
            },
        )
    ]


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (subprocess.TimeoutExpired("fixture", 300), "Command timed out"),
        (FileNotFoundError("fixture"), "Command not found"),
        (PermissionError("fixture"), "Error:"),
    ],
)
def test_optimization_command_errors(monkeypatch, error, message):
    def run(*args, **kwargs):
        raise error

    monkeypatch.setattr(optimize.subprocess, "run", run)
    success, output = optimize.run_command(["fixture"])
    assert not success and message in output


def test_optimization_command_dry_run_never_starts_process(monkeypatch, capsys):
    monkeypatch.setattr(
        optimize.subprocess, "run", lambda *a, **kw: pytest.fail("spawned")
    )
    assert optimize.run_command(["fixture", "--apply"], True) == (True, "")
    assert "Would run: fixture --apply" in capsys.readouterr().out


@pytest.mark.parametrize("missing", [False, True])
def test_optimization_scan_reports_dependency_status(monkeypatch, capsys, missing):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if missing:
            raise FileNotFoundError("ffmpeg")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(optimize.subprocess, "run", run)
    assert optimize.scan_optimizations() is optimize.OPTIMIZATION_TASKS
    assert calls == [["ffmpeg", "-version"]]
    output = capsys.readouterr().out
    assert ("Missing dependencies: ffmpeg" in output) is missing
    assert all(task.name in output for task in optimize.OPTIMIZATION_TASKS.values())


@pytest.mark.parametrize("success", [False, True])
@pytest.mark.parametrize("dry_run", [False, True])
def test_optimization_apply_preserves_commands_and_confirmation(
    monkeypatch, capsys, success, dry_run
):
    task = optimize.OptimizationTask(
        "Fixture", "Fixture action", ["fixture"], "1MB", "low", True
    )
    monkeypatch.setattr(optimize, "OPTIMIZATION_TASKS", {"fixture": task})
    calls = []
    monkeypatch.setattr(
        optimize,
        "run_command",
        lambda command, preview: calls.append((command, preview))
        or (success, "status"),
    )
    answers = iter(["y"] if not dry_run else [])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    assert optimize.apply_optimization("fixture", dry_run) is success
    assert task.command == ["fixture"]
    assert calls == [(["fixture", "--dry-run"] if dry_run else ["fixture"], dry_run)]
    output = capsys.readouterr()
    assert "status" in output.out
    assert ("completed successfully" in output.out) is success
    assert ("failed!" in output.err) is not success


def test_optimization_rejects_unknown_or_cancelled_tasks(monkeypatch, capsys):
    monkeypatch.setattr(optimize, "run_command", lambda *args: pytest.fail("executed"))
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert not optimize.apply_optimization("missing")
    assert not optimize.apply_optimization("audio-compress")
    output = capsys.readouterr()
    assert "Unknown task" in output.err and "Cancelled" in output.out


def test_optimization_existing_dry_run_flag_is_not_duplicated(monkeypatch):
    calls = []
    monkeypatch.setattr(
        optimize,
        "run_command",
        lambda command, preview: calls.append(command) or (True, ""),
    )
    assert optimize.apply_optimization("audio-compress", True)
    assert calls[0].count("--dry-run") == 1


def test_apply_all_excludes_missing_or_risky_tasks(monkeypatch):
    tasks = dict(optimize.OPTIMIZATION_TASKS)
    tasks.pop("resources-scan")
    tasks["audio-compress"] = optimize.OptimizationTask(
        "Risky", "", ["fixture"], "", "high"
    )
    monkeypatch.setattr(optimize, "OPTIMIZATION_TASKS", tasks)
    calls = []
    monkeypatch.setattr(
        optimize,
        "apply_optimization",
        lambda task, preview: calls.append((task, preview)) or True,
    )
    assert optimize.apply_all_optimizations(True) == {"localisation-scan": True}
    assert calls == [("localisation-scan", True)]


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], "help"),
        (["--scan"], "scan"),
        (["--task", "fixture"], "fixture"),
        (["--audio"], "audio-compress"),
        (["--localisation"], "localisation-scan"),
        (["--resources"], "resources-scan"),
        (["--apply"], "all"),
        (["--apply", "--dry-run"], "all"),
    ],
)
def test_optimization_cli_dispatch(monkeypatch, capsys, args, expected):
    calls = []
    monkeypatch.setattr(
        optimize, "scan_optimizations", lambda: calls.append(("scan", False))
    )
    monkeypatch.setattr(
        optimize,
        "apply_all_optimizations",
        lambda preview: calls.append(("all", preview)),
    )
    monkeypatch.setattr(
        optimize,
        "apply_optimization",
        lambda task, preview: calls.append((task, preview)),
    )
    _cli(monkeypatch, optimize, args)
    assert calls == ([] if expected == "help" else [(expected, "--dry-run" in args)])
    if expected == "help":
        assert "usage:" in capsys.readouterr().out
