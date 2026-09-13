"""Source contracts for the diplomacy influence windows, not a render test."""

import re
from pathlib import Path

import pytest
from shared_utils import direct_child_block, iter_direct_child_blocks, strip_comments

ROOT = Path(__file__).resolve().parents[2]
BUTTON_POSITIONS = {
    "opt_influence_action_button": (0, 0),
    "opt_aid_button": (0, 32),
    "opt_aid_military_button": (0, 64),
    "opt_military_supply_button": (0, 64),
    "opt_target_other_button": (0, 96),
    "opt_manipulate_politics_button": (28, 0),
    "opt_coup_button": (28, 32),
    "opt_economic_exploitation_button": (28, 64),
    "opt_make_puppet_button": (28, 96),
}


def _block(body, name):
    block = direct_child_block(body, name)
    assert block, f"Missing direct child block: {name}"
    return block[1:-1]


def _elements(body, kind):
    elements = {}
    opener = re.compile(r"\b" + re.escape(kind) + r"\s*=\s*\{")
    for _, start, end in iter_direct_child_blocks(body, opener):
        element = body[start + 1 : end]
        match = re.search(r'\bname\s*=\s*"([^"]+)"', element)
        assert match
        name = match.group(1)
        assert name not in elements
        elements[name] = element
    return elements


def _position(body):
    coordinates = dict(re.findall(r"\b([xy])\s*=\s*(-?\d+)", _block(body, "position")))
    return int(coordinates["x"]), int(coordinates["y"])


@pytest.fixture(scope="module")
def influence_sources():
    scripted = strip_comments(
        (ROOT / "common/scripted_guis/01_influence_scripted_guis.txt").read_text(
            encoding="utf-8"
        )
    )
    layout = strip_comments(
        (ROOT / "interface/MD_influence.gui").read_text(encoding="utf-8")
    )
    return _block(scripted, "scripted_gui"), _elements(
        _block(layout, "guiTypes"), "containerWindowType"
    )


@pytest.mark.parametrize(
    "name", ("countrydiplomacyview_influence", "countrydiplomacyview_influence_buttons")
)
def test_influence_windows_attach_directly_to_selected_country_diplomacy(
    influence_sources, name
):
    scripted, windows = influence_sources
    binding = _block(scripted, name)
    assert "context_type = selected_country_context" in binding
    assert "parent_window_token = selected_country_view_diplomacy" in binding
    assert "parent_scripted_gui" not in binding
    window = re.search(r'\bwindow_name\s*=\s*"([^"]+)"', binding)
    assert window and window.group(1) in windows


def test_button_window_keeps_its_original_position_inside_the_influence_panel(
    influence_sources,
):
    _, windows = influence_sources
    panel_x, panel_y = _position(windows["MD_countrydiplomacyview_influence"])
    assert _position(windows["influence_option_buttons"]) == (panel_x + 198, panel_y)


def test_influence_text_refresh_stays_separate_from_button_refresh(influence_sources):
    scripted, _ = influence_sources
    text = _block(scripted, "countrydiplomacyview_influence")
    buttons = _block(scripted, "countrydiplomacyview_influence_buttons")
    assert not re.search(r"\bdirty\s*=", text)
    assert "dirty = global.update_influence_ui" in buttons


@pytest.mark.parametrize("name", BUTTON_POSITIONS)
def test_influence_actions_keep_their_controls_and_bindings(influence_sources, name):
    scripted, windows = influence_sources
    controls = _elements(windows["influence_option_buttons"], "buttonType")
    assert controls.keys() == BUTTON_POSITIONS.keys()
    assert _position(controls[name]) == BUTTON_POSITIONS[name]
    assert "pdx_tooltip" in controls[name]
    binding = _block(scripted, "countrydiplomacyview_influence_buttons")
    assert _block(_block(binding, "triggers"), name + "_visible")
    assert _block(_block(binding, "triggers"), name + "_click_enabled")
    assert _block(_block(binding, "effects"), name + "_click")
