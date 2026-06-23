"""Tests for the focus standardizer's handling of will_lead_to_war_with.

A focus may declare war on several targets, so will_lead_to_war_with can appear
multiple times. The standardizer must preserve every occurrence, in order.
"""

from standardize_focus_tree import (
    extract_focus_properties,
    format_focus_block,
    standardize_focus_tree,
)


def _focus_with_war_targets(targets):
    lines = ["\tfocus = {\n", "\t\tid = TST_invade\n", "\n"]
    for tag in targets:
        lines.append(f"\t\twill_lead_to_war_with = {tag}\n")
    lines.append("\t}\n")
    return lines


def test_single_war_target_preserved():
    props = extract_focus_properties(_focus_with_war_targets(["MOR"]))
    assert props["will_lead_to_war_with"] == ["will_lead_to_war_with = MOR"]


def test_multiple_war_targets_all_preserved_in_order():
    props = extract_focus_properties(_focus_with_war_targets(["MOR", "TUN", "LBA"]))
    assert props["will_lead_to_war_with"] == [
        "will_lead_to_war_with = MOR",
        "will_lead_to_war_with = TUN",
        "will_lead_to_war_with = LBA",
    ]


def test_no_war_target():
    props = extract_focus_properties(["\tfocus = {\n", "\t\tid = TST_peace\n", "\t}\n"])
    assert props["will_lead_to_war_with"] == []


def test_round_trip_emits_one_line_per_target():
    props = extract_focus_properties(_focus_with_war_targets(["MOR", "TUN"]))
    out = format_focus_block(props)
    war_lines = [l.strip() for l in out if "will_lead_to_war_with" in l]
    assert war_lines == [
        "will_lead_to_war_with = MOR",
        "will_lead_to_war_with = TUN",
    ]
    # Re-parsing the emitted block yields the same two targets (idempotent).
    reparsed = extract_focus_properties([l + "\n" for l in out])
    assert reparsed["will_lead_to_war_with"] == [
        "will_lead_to_war_with = MOR",
        "will_lead_to_war_with = TUN",
    ]


def test_text_icon_and_overlay_emitted_directly_under_icon():
    lines = [
        "\tfocus = {\n",
        "\t\tid = TST_branding\n",
        "\t\ticon = TST_icon\n",
        "\t\toverlay = GFX_overlay\n",
        "\t\ttext_icon = TST_style\n",
        "\t\tcost = 5\n",
        "\t}\n",
    ]
    props = extract_focus_properties(lines)
    out = format_focus_block(props)

    icon_idx = out.index("\t\ticon = TST_icon")
    text_icon_idx = out.index("\t\ttext_icon = TST_style")
    overlay_idx = out.index("\t\toverlay = GFX_overlay")
    first_blank_idx = out.index("")
    cost_idx = out.index("\t\tcost = 5")

    # text_icon and overlay sit right after icon, before the first blank line.
    assert icon_idx < text_icon_idx < first_blank_idx
    assert icon_idx < overlay_idx < first_blank_idx
    # cost is no longer grouped with text_icon/overlay.
    assert cost_idx > first_blank_idx


def _joint_focus_file_lines():
    return [
        "joint_focus = {\n",
        "\tid = TST_joint\n",
        "\ticon = TST_icon\n",
        "\tx = 10\n",
        "\ty = 0\n",
        "\tcost = 5\n",
        "\tsearch_filters = { FOCUS_FILTER_POLITICAL }\n",
        "\tcompletion_reward = {\n",
        '\t\tlog = "[GetDateText]: [Root.GetName]: Focus TST_joint"\n',
        "\t\tadd_political_power = 50\n",
        "\t}\n",
        "\tai_will_do = { base = 5 }\n",
        "}\n",
    ]


def test_joint_focus_dedented_to_top_level(tmp_path):
    src = tmp_path / "shared.txt"
    src.write_text("".join(_joint_focus_file_lines()), encoding="utf-8")

    assert standardize_focus_tree(str(src), str(src)) is True
    out = src.read_text(encoding="utf-8").splitlines()

    assert "joint_focus = {" in out  # block opens at column 0
    assert "\tid = TST_joint" in out  # properties at 1 tab
    assert "\tsearch_filters = { FOCUS_FILTER_POLITICAL }" in out
    # closing brace of the block at column 0
    assert out[-1] == "}" or "}" in [l for l in out if l == "}"]
    assert "}" in out
    # no over-indented property survives
    assert not any(l.startswith("\t\t\tid =") for l in out)


def test_joint_focus_standardization_idempotent(tmp_path):
    src = tmp_path / "shared.txt"
    src.write_text("".join(_joint_focus_file_lines()), encoding="utf-8")

    assert standardize_focus_tree(str(src), str(src)) is True
    first = src.read_text(encoding="utf-8")
    assert standardize_focus_tree(str(src), str(src)) is True
    second = src.read_text(encoding="utf-8")
    assert first == second
