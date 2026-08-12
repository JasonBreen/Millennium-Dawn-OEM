from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

ACTIONABLE_DECISIONS = (
    (
        "common/decisions/USA_corporate_systems_dashboard.txt",
        365,
        {
            "USA_corporate_policy_open_systems_procurement",
            "USA_corporate_policy_domestic_capacity_grants",
            "USA_corporate_policy_secure_federal_systems",
            "USA_corporate_policy_advanced_computing_consortium",
        },
    ),
    (
        "common/decisions/POL_industrial_sovereignty.txt",
        365,
        {
            "POL_industrial_sovereignty_policy_industrial_credit",
            "POL_industrial_sovereignty_policy_strategic_procurement",
            "POL_industrial_sovereignty_policy_regional_export_finance",
            "POL_industrial_sovereignty_policy_applied_research_consortium",
        },
    ),
    (
        "common/decisions/SOV_computing_sovereignty.txt",
        30,
        {
            "SOV_computing_sovereignty_project_180nm",
            "SOV_computing_sovereignty_project_90nm",
            "SOV_computing_sovereignty_project_65nm_pilot",
            "SOV_computing_sovereignty_project_65nm_hvm",
            "SOV_computing_sovereignty_project_28nm_hvm",
            "SOV_computing_sovereignty_project_16nm_hvm",
            "SOV_computing_sovereignty_project_angstrem_t",
            "SOV_computing_sovereignty_project_foreign_8c_tapeout",
            "SOV_computing_sovereignty_project_foreign_16c_tapeout",
        },
    ),
)


def _block_at(text: str, opening_brace: int) -> str:
    depth = 0
    for index in range(opening_brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1 : index]
    raise AssertionError("Unbalanced scripted block")


def _top_level_decisions(text: str) -> dict[str, str]:
    decisions = {}
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.startswith("\t") and not line.startswith("\t\t") and " = {" in line:
            decision_id = line.strip().split(" = {", 1)[0]
            opening_brace = offset + line.index("{")
            decisions[decision_id] = _block_at(text, opening_brace)
        offset += len(line)
    return decisions


@pytest.mark.parametrize(
    ("relative_path", "cooldown_days", "expected"), ACTIONABLE_DECISIONS
)
def test_non_linux_corporate_actions_are_explicitly_reusable(
    relative_path: str, cooldown_days: int, expected: set[str]
):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    decisions = _top_level_decisions(text)
    actionable = {
        decision_id
        for decision_id, body in decisions.items()
        if "complete_effect = {" in body
    }

    assert actionable == expected
    for decision_id in actionable:
        body = decisions[decision_id]
        assert f"days_re_enable = {cooldown_days}" in body
        assert "fire_only_once = no" in body
