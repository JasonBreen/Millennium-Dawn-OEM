"""Trust and replay boundaries for the metadata-only conflict gate publisher."""

import copy
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml
from shared.paths import REPO_ROOT

SPEC = importlib.util.spec_from_file_location(
    "publish_conflict_validation",
    REPO_ROOT / ".github/scripts/publish_conflict_validation.py",
)
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)
REPOSITORY = "owner/repo"
HEAD, BASE = "a" * 40, "b" * 40


class API:
    """Model GitHub-owned metadata independently of PR-authored test artifacts."""

    def __init__(self):
        self.run = {
            "id": 100,
            "workflow_id": 20,
            "run_attempt": 2,
            "repository": {"id": 10, "full_name": REPOSITORY},
            "head_repository": {"id": 10},
            "path": publisher.WORKFLOW,
            "event": "workflow_dispatch",
            "head_branch": "main",
            "head_sha": BASE,
            "display_title": f"Conflict validation PR #7 head {HEAD} base {BASE}",
            "status": "completed",
            "conclusion": "success",
        }
        self.event = {"repository": {"id": 10}, "workflow_run": copy.deepcopy(self.run)}
        self.workflow = {"id": 20, "path": publisher.WORKFLOW}
        self.pr = {
            "number": 7,
            "state": "open",
            "head": {"repo": {"id": 10}, "sha": HEAD},
            "base": {"repo": {"id": 10}, "sha": BASE, "ref": "main"},
        }
        self.main, self.default_branch = BASE, "main"
        self.jobs = [
            {
                "name": name,
                "run_id": 100,
                "run_attempt": 2,
                "head_sha": BASE,
                "status": "completed",
                "conclusion": "success",
            }
            for name in publisher.JOBS
        ]
        self.runs = [self.run]
        self.sources = {100: self.run}
        self.checks, self.writes = [], []
        self.reads = 0
        self.race_at = None

    def call(self, path, method="GET", data=None):
        if method != "GET":
            self.writes.append((path, method, copy.deepcopy(data)))
            if method == "POST":
                check = {"id": 1, "app": {"slug": "github-actions"}, **data}
                self.checks.append(check)
            else:
                check = next(
                    item for item in self.checks if path == f"check-runs/{item['id']}"
                )
                check.update(data)
            return copy.deepcopy(check)
        if path == "":
            self.reads += 1
            if self.reads == self.race_at:
                self.pr["head"]["sha"] = "c" * 40
            return {"default_branch": self.default_branch}
        if path.startswith("actions/runs/"):
            return copy.deepcopy(self.sources[int(path.rsplit("/", 1)[1])])
        if path == "actions/workflows/test-suite.yml":
            return self.workflow
        if path == "git/ref/heads/main":
            return {"object": {"sha": self.main}}
        if path == "pulls/7":
            return self.pr
        raise AssertionError(f"Unexpected metadata read: {path}")

    def pages(self, path, key):
        if key == "jobs":
            assert path == (
                f"actions/runs/{self.run['id']}/attempts/{self.run['run_attempt']}/jobs"
            )
            return self.jobs
        if key == "check_runs":
            assert path == f"commits/{HEAD}/check-runs?filter=all"
            return self.checks
        assert path.endswith(f"event=workflow_dispatch&branch=main&head_sha={BASE}")
        return self.runs

    def publish(self):
        publisher.publish(self, self.event, REPOSITORY, 10)


def _set(value, path, replacement):
    parts = path.split(".")
    for part in parts[:-1]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    value[parts[-1]] = replacement


def _assert_failed_check(api):
    with pytest.raises(ValueError):
        api.publish()
    assert api.checks[0]["conclusion"] == "failure"
    assert not any(data.get("conclusion") == "success" for _, _, data in api.writes)


def test_success_attaches_only_to_the_validated_pr_sha_and_replays_update_one_check():
    api = API()
    api.publish()
    api.publish()
    assert len(api.checks) == 1
    assert api.checks[0]["head_sha"] == HEAD != BASE
    assert api.checks[0]["name"] == "Test suite gate"
    assert api.checks[0]["conclusion"] == "success"
    assert api.checks[0]["details_url"].endswith("/100/attempts/2")
    assert sum(method == "POST" for _, method, _ in api.writes) == 1


@pytest.mark.parametrize("event_suffix", ["", "@main"])
@pytest.mark.parametrize("run_suffix", ["", "@main"])
def test_registered_workflow_accepts_plain_and_trusted_ref_qualified_paths(
    event_suffix, run_suffix
):
    api = API()
    api.event["workflow_run"]["path"] += event_suffix
    api.run["path"] += run_suffix
    api.publish()
    assert api.checks[0]["conclusion"] == "success"


@pytest.mark.parametrize("target", ["event", "run"])
@pytest.mark.parametrize(
    "path",
    [
        f"{publisher.WORKFLOW}@attacker",
        f"{publisher.WORKFLOW}@refs/tags/main",
        f"{publisher.WORKFLOW}@refs/heads/main",
        f"{publisher.WORKFLOW}@main@attacker",
        f"{publisher.WORKFLOW}@",
        f"{publisher.WORKFLOW}@main\n",
        f"{publisher.WORKFLOW}@main/../attacker",
        f"{publisher.WORKFLOW}@{BASE}",
        f"owner/repo/{publisher.WORKFLOW}@main",
        ".github/workflows/other.yml@main",
        ".github/workflows/../workflows/test-suite.yml@main",
        None,
    ],
)
def test_ref_suffix_cannot_replace_registered_workflow_branch_or_revision(target, path):
    api = API()
    record = api.event["workflow_run"] if target == "event" else api.run
    record["path"] = path
    with pytest.raises(ValueError, match="Workflow path mismatch"):
        api.publish()
    assert not api.writes


@pytest.mark.parametrize("suffix", ["@main", "@attacker"])
def test_live_path_rechecks_accept_only_the_same_registered_workflow(suffix):
    api = API()
    original_call = api.call

    def path_changes(path, method="GET", data=None):
        if path == "":
            api.run["path"] = publisher.WORKFLOW + suffix
        return original_call(path, method, data)

    api.call = path_changes
    if suffix == "@attacker":
        _assert_failed_check(api)
    else:
        api.publish()
        assert api.checks[0]["conclusion"] == "success"


@pytest.mark.parametrize("new_id,new_attempt", [(100, 3), (101, 1)])
@pytest.mark.parametrize("newest_first", [True, False])
def test_queued_callbacks_for_distinct_runs_and_attempts_converge_to_latest_result(
    new_id, new_attempt, newest_first
):
    api = API()
    api.run.update(status="in_progress", conclusion=None)
    api.event["workflow_run"] = copy.deepcopy(api.run)
    api.publish()
    assert api.checks[0]["status"] == "in_progress"
    old_callback = copy.deepcopy(api.event["workflow_run"])
    api.run = {
        **api.run,
        "id": new_id,
        "run_attempt": new_attempt,
        "status": "completed",
        "conclusion": "success",
    }
    api.sources[new_id] = api.run
    api.runs.append(api.run)
    for job in api.jobs:
        job.update(run_id=new_id, run_attempt=new_attempt)
    callbacks = [old_callback, copy.deepcopy(api.run)]
    if newest_first:
        callbacks.reverse()
    for callback in callbacks:
        api.event["workflow_run"] = callback
        if callback == api.run:
            api.publish()
        else:
            with pytest.raises(ValueError):
                api.publish()
    assert len(api.checks) == 1
    assert api.checks[0]["conclusion"] == "success"
    assert api.checks[0]["details_url"].endswith(f"/{new_id}/attempts/{new_attempt}")


@pytest.mark.parametrize("suffix", ["", "@main"])
@pytest.mark.parametrize(
    "target,path,value",
    [
        ("event", "repository.id", 99),
        ("event", "workflow_run.id", "100"),
        ("event", "workflow_run.repository.id", 99),
        ("event", "workflow_run.repository.full_name", "fork/repo"),
        ("event", "workflow_run.head_repository.id", 99),
        ("event", "workflow_run.workflow_id", 99),
        ("event", "workflow_run.path", ".github/workflows/other.yml"),
        ("event", "workflow_run.event", "pull_request"),
        ("event", "workflow_run.head_branch", "attacker"),
        ("event", "workflow_run.display_title", "forged title"),
        ("event", "workflow_run.head_sha", HEAD),
        ("run", "id", 99),
        ("run", "repository.id", 99),
        ("run", "head_repository.id", 99),
        ("run", "workflow_id", 99),
        ("run", "path", "other.yml"),
        ("run", "event", "pull_request"),
        ("run", "head_branch", "attacker"),
        ("workflow", "path", "other.yml"),
    ],
)
def test_identity_rejection_never_writes_a_check(suffix, target, path, value):
    api = API()
    api.run["path"] += suffix
    api.event["workflow_run"]["path"] += suffix
    _set(getattr(api, target), path, value)
    with pytest.raises(ValueError):
        api.publish()
    assert api.writes == []


@pytest.mark.parametrize(
    "title,source_sha",
    [
        ("forged title", BASE),
        (f"Conflict validation PR #0 head {HEAD} base {BASE}", BASE),
        (f"Conflict validation PR #7 head {HEAD} base {BASE}\n", BASE),
        (f"Conflict validation PR #7 head {HEAD} base {BASE}", HEAD),
    ],
)
def test_protected_title_is_a_strict_pin_record(title, source_sha):
    api = API()
    for run in (api.run, api.event["workflow_run"]):
        run.update(display_title=title, head_sha=source_sha)
    with pytest.raises(ValueError):
        api.publish()
    assert not api.writes


@pytest.mark.parametrize(
    "target,path,value",
    [
        ("pr", "number", 8),
        ("pr", "state", "closed"),
        ("pr", "head.repo.id", 99),
        ("pr", "base.repo.id", 99),
        ("pr", "head.sha", "c" * 40),
        ("pr", "base.sha", "c" * 40),
        ("pr", "base.ref", "other"),
        ("event", "workflow_run.run_attempt", 1),
        ("run", "conclusion", "failure"),
        ("run", "conclusion", "cancelled"),
        ("run", "conclusion", "skipped"),
        ("run", "conclusion", None),
    ],
)
def test_unacceptable_live_evidence_blocks_the_gate(target, path, value):
    api = API()
    _set(getattr(api, target), path, value)
    _assert_failed_check(api)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "extra",
        "main",
        "default",
        "superseded",
        "not listed",
        "failure",
        "cancelled",
        "skipped",
        "in_progress",
        "wrong run",
        "wrong attempt",
        "wrong sha",
    ],
)
def test_missing_failed_or_mismatched_attempt_evidence_fails_closed(change):
    api = API()
    if change == "missing":
        api.jobs.pop()
    elif change == "duplicate":
        api.jobs.append(api.jobs[0])
    elif change == "extra":
        api.jobs.append({**api.jobs[0], "name": "Unexpected job"})
    elif change == "main":
        api.main = HEAD
    elif change == "default":
        api.default_branch = "other"
    elif change == "superseded":
        api.runs.append({**api.run, "id": 101})
    elif change == "not listed":
        api.runs = []
    else:
        key, value = {
            "wrong run": ("run_id", 99),
            "wrong attempt": ("run_attempt", 1),
            "wrong sha": ("head_sha", HEAD),
            "in_progress": ("status", "in_progress"),
        }.get(change, ("conclusion", change))
        api.jobs[0][key] = value
    _assert_failed_check(api)


@pytest.mark.parametrize("race_at", [2, 3])
def test_head_races_before_and_after_completion_revoke_success(race_at):
    api = API()
    api.race_at = race_at
    with pytest.raises(ValueError, match="Stale PR head"):
        api.publish()
    assert api.checks[0]["conclusion"] == "failure"
    assert api.writes[-1][2]["conclusion"] == "failure"


def test_active_rerun_revokes_previous_success_and_old_callbacks_cannot_clobber_it():
    api = API()
    api.publish()
    api.run.update(run_attempt=3, status="in_progress", conclusion=None)
    api.event["workflow_run"] = copy.deepcopy(api.run)
    api.publish()
    assert api.checks[0]["status"] == "in_progress"
    api.event["workflow_run"]["run_attempt"] = 2
    writes = len(api.writes)
    with pytest.raises(ValueError, match="newer publisher"):
        api.publish()
    assert len(api.writes) == writes


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "other"),
        ("head_sha", BASE),
        ("app", {"slug": "other"}),
        ("details_url", "https://attacker.invalid/"),
    ],
)
def test_owned_check_cannot_be_replaced_by_a_different_app_or_identity(field, value):
    api = API()
    api.publish()
    api.checks[0][field] = value
    writes = len(api.writes)
    with pytest.raises(ValueError):
        api.publish()
    assert len(api.writes) == writes


@pytest.mark.parametrize("pages", [1, 2, 10, 11])
def test_api_pagination_rejects_truncation_and_exhaustion(pages):
    api = publisher.GitHub(REPOSITORY, "test-token")
    api.call = lambda path: {
        "total_count": pages * 100,
        "jobs": list(range(100)) if int(path.rsplit("=", 1)[1]) < pages else [],
    }
    if pages > 10:
        with pytest.raises(ValueError):
            api.pages("actions/runs/100/jobs", "jobs")
    else:
        assert len(api.pages("actions/runs/100/jobs", "jobs")) == (pages - 1) * 100


def test_main_reads_only_runner_context(monkeypatch, tmp_path):
    api = API()
    event_path = tmp_path / "event.json"
    with event_path.open("w", encoding="utf-8", newline="") as handle:
        json.dump(api.event, handle)
    for key, value in {
        "GITHUB_EVENT_PATH": str(event_path),
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_REPOSITORY_ID": "10",
        "GH_TOKEN": "test-token",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(publisher, "GitHub", lambda *args: api)
    publisher.main()
    assert api.checks[0]["conclusion"] == "success"


@pytest.mark.parametrize("native", [True, False])
def test_native_or_duplicate_checks_are_never_overwritten(native):
    api = API()
    api.publish()
    if native:
        api.checks[0]["external_id"] = "native-actions-check"
    else:
        api.checks.append(copy.deepcopy(api.checks[0]))
    writes = len(api.writes)
    with pytest.raises(ValueError):
        api.publish()
    assert len(api.writes) == writes


@pytest.mark.parametrize("failure_at", [1, 2, 3])
def test_metadata_transport_errors_revoke_the_check(failure_at):
    api = API()
    original = api.call

    def failing_call(path, method="GET", data=None):
        if path == "" and api.reads + 1 == failure_at:
            raise OSError("API unavailable")
        return original(path, method, data)

    api.call = failing_call
    with pytest.raises(OSError):
        api.publish()
    assert api.writes[-1][2]["conclusion"] == "failure"


@pytest.mark.parametrize(
    "change", ["none", "main", "attempt", "workflow", "source result"]
)
def test_base_updates_reuse_one_check_and_live_source_races_fail_closed(change):
    api = API()
    api.publish()
    if change == "none":
        new_base = "d" * 40
        api.main = api.pr["base"]["sha"] = new_base
        api.run = {
            **api.run,
            "id": 101,
            "run_attempt": 1,
            "head_sha": new_base,
            "display_title": api.run["display_title"].replace(BASE, new_base),
        }
        api.sources[101] = api.run
        api.runs.append(api.run)
        api.event["workflow_run"] = copy.deepcopy(api.run)
        api.jobs = [
            {**job, "run_id": 101, "run_attempt": 1, "head_sha": new_base}
            for job in api.jobs
        ]
        # The real API route is pinned to the current base, not the fixture's BASE.
        original_pages = api.pages
        api.pages = lambda path, key: (
            api.runs if key == "workflow_runs" else original_pages(path, key)
        )
        api.publish()
        assert len(api.checks) == 1
        assert api.checks[0]["conclusion"] == "success"
        assert api.checks[0]["details_url"].endswith("/101/attempts/1")
        assert api.sources[100]["head_sha"] == BASE
        assert api.sources[100]["display_title"].endswith(f"base {BASE}")
        return
    original = api.call

    def changing_call(path, method="GET", data=None):
        if path == "" and api.reads == 3:
            key, value = {
                "main": (None, HEAD),
                "attempt": ("run_attempt", 3),
                "workflow": ("workflow_id", 99),
                "source result": ("conclusion", "failure"),
            }[change]
            if key is None:
                api.main = value
            else:
                api.run[key] = value
        return original(path, method, data)

    api.call = changing_call
    with pytest.raises(ValueError):
        api.publish()
    assert api.checks[0]["conclusion"] == "failure"


@pytest.mark.parametrize(
    "changed,value",
    [
        (None, None),
        ("GITHUB_REF", "refs/heads/attacker"),
        ("GITHUB_SHA", HEAD),
        ("DEFAULT_BRANCH", "other"),
        ("HEAD_REPOSITORY", "fork/repo"),
        ("REQUESTED_HEAD", BASE),
        ("REQUESTED_BASE", HEAD),
        ("BASE_SHA", HEAD),
        ("BASE_REF", "other"),
        ("PR_STATE", "closed"),
        ("EVENT_PR_NUMBER", "7/../../actions"),
        ("HEAD_SHA", "not-a-sha"),
    ],
)
def test_dispatch_resolver_checks_live_pins_before_any_pr_checkout(
    tmp_path, changed, value
):
    bash = (
        Path(r"C:\Program Files\Git\bin\bash.exe")
        if os.name == "nt"
        else shutil.which("bash")
    )
    if not bash or not Path(bash).is_file():
        pytest.skip("Bash is unavailable")
    config = yaml.safe_load(
        (REPO_ROOT / ".github/workflows/test-suite.yml").read_text(encoding="utf-8")
    )
    step = config["jobs"]["detect-changes"]["steps"][0]
    assert step["name"] == "Resolve validation ref"
    shim = r"""
    gh() {
      case "$*" in
        *--jq\ .default_branch) printf '%s' "$DEFAULT_BRANCH" ;;
        *--jq\ .sha) printf '%s' "$PROTECTED_SHA" ;;
        *) printf '{}' ;;
      esac
    }
    jq() {
      case "$*" in
        '-r .head.repo.full_name') printf '%s' "$HEAD_REPOSITORY" ;;
        '-r .head.sha') printf '%s' "$HEAD_SHA" ;;
        '-r .base.repo.full_name') printf '%s' "$GITHUB_REPOSITORY" ;;
        '-r .base.sha') printf '%s' "$BASE_SHA" ;;
        '-r .base.ref') printf '%s' "$BASE_REF" ;;
        '-r .state') printf '%s' "$PR_STATE" ;;
        *) return 1 ;;
      esac
    }
    """
    env = {
        **os.environ,
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_SHA": BASE,
        "PROTECTED_SHA": BASE,
        "DEFAULT_BRANCH": "main",
        "EVENT_PR_NUMBER": "7",
        "HEAD_SHA": HEAD,
        "BASE_SHA": BASE,
        "REQUESTED_HEAD": HEAD,
        "REQUESTED_BASE": BASE,
        "HEAD_REPOSITORY": REPOSITORY,
        "BASE_REF": "main",
        "PR_STATE": "open",
        "GITHUB_OUTPUT": "output",
    }
    if changed:
        env[changed] = value
    result = subprocess.run(
        [str(bash), "-e", "-c", shim + step["run"]],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == (1 if changed else 0), result.stdout + result.stderr
    output = tmp_path / "output"
    if changed:
        assert not output.exists()
    else:
        assert f"head-sha={HEAD}" in output.read_text(encoding="utf-8")
