"""`_collect_files` path scoping: relative for should_skip_file, full for extra_skip."""

from validator_common import BaseValidator


class _Probe(BaseValidator):
    TITLE = "probe"

    def run_all_validations(self):  # pragma: no cover - not exercised
        return 0


def _mod_with_org(tmp_path):
    """A mod root under an ignored ancestor, holding one MIO org file."""
    root = tmp_path / ".claude" / "worktrees" / "test-worktree"
    org = root / "common" / "military_industrial_organization" / "organizations"
    org.mkdir(parents=True)
    (org / "USA_org.txt").write_text("org = {}\n", encoding="utf-8")
    other = root / "common" / "national_focus"
    other.mkdir(parents=True)
    (other / "05_usa.txt").write_text("focus = {}\n", encoding="utf-8")
    return root


def test_extra_skip_receives_the_full_path(tmp_path):
    """Callbacks match anchored fragments like `/<ORG_DIR>/`, absent when relative."""
    root = _mod_with_org(tmp_path)
    seen = []

    def extra_skip(path):
        seen.append(path)
        return (
            "/common/military_industrial_organization/organizations/"
            in path.replace("\\", "/")
        )

    files = _Probe(str(root), workers=1)._collect_files(
        ["common/**/*.txt"], extra_skip=extra_skip
    )

    assert seen, "extra_skip was never consulted"
    assert all(
        p.replace("\\", "/").startswith(str(root).replace("\\", "/")) for p in seen
    )
    names = [f.replace("\\", "/").rsplit("/", 1)[-1] for f in files]
    assert "USA_org.txt" not in names, "org file leaked past extra_skip"
    assert "05_usa.txt" in names


def test_mod_content_survives_an_ignored_ancestor(tmp_path):
    """The mod root sits under `.claude/`; its own files must still be collected."""
    root = _mod_with_org(tmp_path)
    files = _Probe(str(root), workers=1)._collect_files(["common/**/*.txt"])
    names = sorted(f.replace("\\", "/").rsplit("/", 1)[-1] for f in files)
    assert names == ["05_usa.txt", "USA_org.txt"]
