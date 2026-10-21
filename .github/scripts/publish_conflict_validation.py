"""Publish an exact-head gate using trusted Actions metadata, never PR artifacts."""

import json
import os
import re
import urllib.request
from collections import Counter

WORKFLOW = ".github/workflows/test-suite.yml"
TITLE = re.compile(
    r"Conflict validation PR #([1-9][0-9]*) head ([0-9a-f]{40}) base ([0-9a-f]{40})"
)
JOBS = {
    "Detect changes",
    "File path validation",
    "Prepare workspace",
    "Tools tests (Linux)",
    "Tools tests (macOS)",
    "Tools tests (Windows)",
    "Content tests",
    "Tools quality",
    "Mod tests (core)",
    "Mod tests (targeted-a)",
    "Mod tests (targeted-b)",
    "Docs quality / Docs checks",
    "Test suite report",
    "Test suite gate",
}


def require(condition, message):
    """Stop before issuing a successful check on incomplete or mismatched evidence."""
    if not condition:
        raise ValueError(message)


class GitHub:
    """Use only repository-relative API paths; never follow artifact or log URLs."""

    def __init__(self, repository, token):
        require(
            re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository),
            "Invalid repository",
        )
        self.root = f"https://api.github.com/repos/{repository}/"
        self.token = token

    def call(self, path, method="GET", data=None):
        request = urllib.request.Request(
            self.root + path,
            data=None if data is None else json.dumps(data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Content-Type": "application/json",
            },
            method=method,
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def pages(self, path, key):
        result = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 11):
            data = self.call(f"{path}{separator}per_page=100&page={page}")
            require(data.get("total_count", 0) <= 1000, "API search is truncated")
            items = data[key]
            result.extend(items)
            if len(items) < 100:
                return result
        raise ValueError("API pagination exhausted")


def identity(api, event, repository, repository_id):
    """Authenticate the source before trusting its protected-workflow run name."""
    source = event["workflow_run"]
    require(event["repository"]["id"] == repository_id, "Event repository mismatch")
    require(type(source["id"]) is int, "Invalid source run ID")
    run = api.call(f"actions/runs/{source['id']}")
    workflow = api.call("actions/workflows/test-suite.yml")
    for item in (source, run):
        require(item["id"] == source["id"], "Source run mismatch")
        require(item["repository"]["id"] == repository_id, "Run repository mismatch")
        require(item["repository"]["full_name"] == repository, "Run owner mismatch")
        require(item["head_repository"]["id"] == repository_id, "Fork run rejected")
        require(item["workflow_id"] == workflow["id"], "Workflow ID mismatch")
        require(item["path"] == WORKFLOW, "Workflow path mismatch")
        require(item["event"] == "workflow_dispatch", "Historical PR run rejected")
        require(item["head_branch"] == "main", "Untrusted source branch")
        require(item["display_title"] == run["display_title"], "Run title mismatch")
        require(item["head_sha"] == run["head_sha"], "Source revision mismatch")
    match = TITLE.fullmatch(run["display_title"])
    require(match is not None, "Missing exact validation pins")
    number, head, base = match.groups()
    require(run["head_sha"] == base, "Source workflow is not at the pinned base")
    require(workflow["path"] == WORKFLOW, "Unexpected workflow registration")
    return run, int(number), head, base


def current(api, run, number, head, base, repository_id):
    """Recheck live pins, the latest attempt, and newer dispatches before writing."""
    repository = api.call("")
    require(repository["default_branch"] == "main", "Default branch changed")
    require(api.call("git/ref/heads/main")["object"]["sha"] == base, "Main advanced")
    pr = api.call(f"pulls/{number}")
    require(pr["number"] == number and pr["state"] == "open", "PR is not open")
    for side, sha in (("head", head), ("base", base)):
        require(pr[side]["repo"]["id"] == repository_id, "PR repository mismatch")
        require(pr[side]["sha"] == sha, f"Stale PR {side}")
    require(pr["base"]["ref"] == "main", "PR base changed")
    latest = api.call(f"actions/runs/{run['id']}")
    require(
        all(
            latest[key] == run[key]
            for key in (
                "id",
                "workflow_id",
                "run_attempt",
                "head_sha",
                "display_title",
                "event",
                "path",
            )
        ),
        "Run identity or attempt changed",
    )
    runs = api.pages(
        "actions/workflows/test-suite.yml/runs"
        f"?event=workflow_dispatch&branch=main&head_sha={base}",
        "workflow_runs",
    )
    matching = [item for item in runs if item["display_title"] == run["display_title"]]
    require(
        matching and max(item["id"] for item in matching) == run["id"],
        "Source dispatch was superseded or is missing",
    )
    return latest


def successful_jobs(api, run):
    """Every full-suite leg must succeed in this exact attempt, including the gate."""
    jobs = api.pages(
        f"actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs"
    )
    require(
        Counter(job["name"] for job in jobs) == Counter(JOBS),
        "Missing, duplicate, or unexpected validation jobs",
    )
    for job in jobs:
        require(job["run_id"] == run["id"], "Job run mismatch")
        require(job["run_attempt"] == run["run_attempt"], "Job attempt mismatch")
        require(job["head_sha"] == run["head_sha"], "Job workflow revision mismatch")
        require(
            job["status"] == "completed" and job["conclusion"] == "success",
            f"Validation job did not succeed: {job['name']}",
        )


def publish(api, event, repository, repository_id):
    """Keep one owned check per PR head; replays cannot create extra gates."""
    run, number, head, base = identity(api, event, repository, repository_id)
    marker = f"conflict-validation-v1:{number}:{head}"
    checks = api.pages(f"commits/{head}/check-runs?filter=all", "check_runs")
    require(
        not any(
            check["name"] == "Test suite gate" and check.get("external_id") != marker
            for check in checks
        ),
        "A different gate already exists on this head; use its original PR workflow",
    )
    owned = [check for check in checks if check.get("external_id") == marker]
    require(len(owned) <= 1, "Duplicate publication checks")
    for check in owned:
        require(
            check["name"] == "Test suite gate"
            and check["head_sha"] == head
            and check["app"]["slug"] == "github-actions",
            "Check ownership mismatch",
        )
        prior = re.fullmatch(
            rf"https://github.com/{re.escape(repository)}/actions/runs/([0-9]+)/attempts/([0-9]+)",
            check["details_url"],
        )
        require(prior is not None, "Unrecognized owned check provenance")
        require(
            tuple(map(int, prior.groups()))
            <= (run["id"], event["workflow_run"]["run_attempt"]),
            "A newer publisher already owns this check",
        )
    data = {
        "name": "Test suite gate",
        "external_id": marker,
        "details_url": f"https://github.com/{repository}/actions/runs/{run['id']}"
        f"/attempts/{run['run_attempt']}",
        "status": "in_progress",
    }
    if owned:
        check = api.call(f"check-runs/{owned[0]['id']}", "PATCH", data)
    else:
        check = api.call("check-runs", "POST", {**data, "head_sha": head})
    require(check["head_sha"] == head, "Published check SHA mismatch")
    endpoint = f"check-runs/{check['id']}"
    try:
        require(
            event["workflow_run"]["run_attempt"] == run["run_attempt"],
            "Event attempt is stale",
        )
        latest = current(api, run, number, head, base, repository_id)
        if latest["status"] != "completed":
            return
        require(latest["conclusion"] == "success", "Source run did not succeed")
        successful_jobs(api, run)
        latest = current(api, run, number, head, base, repository_id)
        require(
            latest["status"] == "completed" and latest["conclusion"] == "success",
            "Source result changed",
        )
        api.call(endpoint, "PATCH", {"status": "completed", "conclusion": "success"})
        latest = current(api, run, number, head, base, repository_id)
        require(
            latest["status"] == "completed" and latest["conclusion"] == "success",
            "Source result changed after publication",
        )
    except Exception:
        api.call(endpoint, "PATCH", {"status": "completed", "conclusion": "failure"})
        raise


def main():
    """Read only runner-provided context; no PR-supplied inputs are executed."""
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        event = json.load(handle)
    repository = os.environ["GITHUB_REPOSITORY"]
    api = GitHub(repository, os.environ["GH_TOKEN"])
    publish(api, event, repository, int(os.environ["GITHUB_REPOSITORY_ID"]))


if __name__ == "__main__":
    main()
