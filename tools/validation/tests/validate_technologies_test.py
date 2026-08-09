"""Tests for `validate_technologies.py` (tech category consistency)."""

import validate_technologies as V

FIXTURE = """technologies = {
\tfoo_1 = {
\t\tcategories = {
\t\t\tCAT_a
\t\t\tCAT_b
\t\t}
\t\tpath = {
\t\t\tleads_to_tech = foo_2
\t\t\tresearch_cost_coeff = 1
\t\t}
\t}
\tfoo_2 = {
\t\tcategories = {
\t\t\tCAT_a
\t\t}
\t}
\tbar_1 = {
\t\tcategories = {
\t\t\tCAT_x
\t\t}
\t\tpath = {
\t\t\tleads_to_tech = baz_1
\t\t\tresearch_cost_coeff = 1
\t\t}
\t}
\tbaz_1 = {
\t\tcategories = {
\t\t\tCAT_y
\t\t}
\t}
}
"""


def _write_fixture(tmp_path):
    tech_dir = tmp_path / "common" / "technologies"
    tech_dir.mkdir(parents=True)
    (tech_dir / "test.txt").write_text(FIXTURE, encoding="utf-8")


def test_same_family_missing_category_flagged(tmp_path):
    _write_fixture(tmp_path)
    v = V.Validator(str(tmp_path))
    v.run_validations()
    assert len(v._issues) == 1
    issue = v._issues[0]
    assert issue.category == "category-missing"
    assert "foo_2" in issue.message
    assert "CAT_b" in issue.message
    assert issue.file.endswith("test.txt")


def test_different_family_branch_not_flagged(tmp_path):
    _write_fixture(tmp_path)
    v = V.Validator(str(tmp_path))
    v.run_validations()
    assert not any("baz_1" in i.message for i in v._issues)


def test_staged_only_limits_findings_to_staged_file(tmp_path):
    _write_fixture(tmp_path)
    other = tmp_path / "common" / "technologies" / "other.txt"
    other.write_text(
        """technologies = {
\tqux_1 = {
\t\tcategories = {
\t\t\tCAT_q
\t\t\tCAT_r
\t\t}
\t\tpath = {
\t\t\tleads_to_tech = qux_2
\t\t\tresearch_cost_coeff = 1
\t\t}
\t}
\tqux_2 = {
\t\tcategories = {
\t\t\tCAT_q
\t\t}
\t}
}
""",
        encoding="utf-8",
    )
    v = V.Validator(str(tmp_path), staged_only=True)
    v.staged_files = [str(other)]
    v.run_validations()
    assert len(v._issues) == 1
    assert "qux_2" in v._issues[0].message
    assert "foo_2" not in v._issues[0].message


def test_stem():
    assert V.stem("gen_4_large") == V.stem("gen_3_large")
    assert V.stem("nsb_engine_tech_6") == V.stem("nsb_engine_tech_5")
    assert V.stem("AA_upgrade_1") != V.stem("Anti_Air_0")
    assert V.stem("countermeasures_1") != V.stem("air_weapons_1")
