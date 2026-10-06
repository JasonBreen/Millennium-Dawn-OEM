from ai_race_state_model_test import ROOT, _named_block


def test_the_private_room_invite_needs_the_hosted_forum_to_be_preparing():
    decisions = (ROOT / "common/decisions/econ_forum_decisions.txt").read_text(
        encoding="utf-8"
    )
    invite = _named_block(decisions, "econ_forum_invite_to_private_room")
    root = _named_block(invite, "target_root_trigger")
    assert "has_country_flag = econ_forum_preparing" in root
    assert "has_variable = econ_forum_hosted" in root
    assert (
        "check_variable = { global.econ_forum_preparing^econ_forum_hosted = 1 }" in root
    )
