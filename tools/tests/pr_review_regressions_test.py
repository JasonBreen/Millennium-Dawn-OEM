import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MONETARY_DECISIONS = ROOT / "common" / "decisions" / "00_monetary_policy_decisions.txt"
CHI_DECISIONS = ROOT / "common" / "decisions" / "05_CHI_decisions.txt"
DECISION_SPRITES = ROOT / "interface" / "MD_decisions.gfx"


def _named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    assert match, f"missing block {name}"
    depth = 0
    for index in range(text.index("{", match.start()), len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise AssertionError(f"unterminated block {name}")


def test_expand_money_supply_ai_blocks_negative_treasury():
    decisions = MONETARY_DECISIONS.read_text(encoding="utf-8")
    decision = _named_block(decisions, "monetary_policy_expand_money_supply")
    ai_will_do = _named_block(decision, "ai_will_do")

    assert "check_variable = { treasury < 0 }" in ai_will_do
    assert "NOT = { check_variable = { treasury < 0 } }" not in ai_will_do


def test_reviewed_chi_decisions_use_a_defined_icon():
    decisions = CHI_DECISIONS.read_text(encoding="utf-8")
    sprites = DECISION_SPRITES.read_text(encoding="utf-8")
    assert 'name = "GFX_decision_generic_political_discourse"' in sprites

    for decision_id in ("CHI_jap_open_back_channel", "CHI_push_rcep_signing"):
        decision = _named_block(decisions, decision_id)
        assert "icon = generic_political_discourse" in decision
