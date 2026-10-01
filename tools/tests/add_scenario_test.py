import importlib.util

import pytest


def _module():
    from shared.paths import GENERATORS_DIR

    spec = importlib.util.spec_from_file_location(
        "add_scenario", GENERATORS_DIR / "add_scenario.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path, text, bom=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)


def _repo(tmp_path):
    repo = tmp_path / "repo"
    _write(
        repo / "common/game_rules/00_game_rules.txt",
        "rule_other = {\r\n\tname = OTHER\r\n}\r\n",
    )
    _write(
        repo / "localisation/english/MD_game_rules_l_english.yml",
        'l_english:\n RULE_OTHER: "Other"\n',
        bom=True,
    )
    _write(repo / "events/Other.txt", "add_namespace = OTHER\n")
    _write(
        repo / ".claude/docs/documentation-references.md",
        "| File | What |\n| `scripted-gui.md` | GUI |\n| `stalker-scenario.md` | STALKER |\n",
    )
    return repo


def _read(path):
    return path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")


def test_new_scaffolds_the_scenario(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    written = mod.add_scenario(
        repo, "SILENTHILL", "Silent Hill", "The town has always been wrong."
    )

    rules = _read(repo / "common/game_rules/00_game_rules.txt")
    assert "rule_silenthill_scenario = {" in rules and "rule_other = {" in rules
    assert (repo / "common/game_rules/00_game_rules.txt").read_bytes().count(
        b"\r\n"
    ) == rules.count("\n")
    loc = repo / "localisation/english/MD_game_rules_l_english.yml"
    assert loc.read_bytes().startswith(b"\xef\xbb\xbf")
    assert (
        ' RULE_SILENTHILL_SCENARIO_ENABLED_DESC: "The town has always been wrong."'
        in _read(loc)
    )

    trigger = _read(
        repo / "common/scripted_triggers/99_SILENTHILL_scripted_triggers.txt"
    )
    assert "has_global_flag = GLOBAL_SILENTHILL_scenario_enabled" in trigger
    assert "has_game_rule" not in trigger
    on_actions = _read(repo / "common/on_actions/99_SILENTHILL_on_actions.txt")
    assert "random_country = { SILENTHILL_initialize_scenario = yes }" in on_actions
    assert "SILENTHILL_monthly_pulse = yes" in on_actions
    assert (
        "set_global_flag = { flag = SILENTHILL_monthly_pulse_done value = 1 days = 27 }"
        in on_actions
    )
    assert "NOT = { has_global_flag = SILENTHILL_monthly_pulse_done }" in on_actions
    assert _read(repo / "events/SILENTHILL.txt") == "add_namespace = SILENTHILL\n"
    assert (
        (repo / "localisation/english/MD_SILENTHILL_l_english.yml")
        .read_bytes()
        .startswith(b"\xef\xbb\xbf")
    )
    doc = _read(repo / ".claude/docs/silenthill-scenario.md")
    assert "The next free block is 10–19." in doc and "# Silent Hill Scenario" in doc
    index = _read(repo / ".claude/docs/documentation-references.md")
    assert index.index("silenthill-scenario.md") < index.index("stalker-scenario.md")
    assert len(written) == 10
    assert written[-1] == ".claude/docs/documentation-references.md"


def test_new_skips_index_when_absent_or_present(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    (repo / ".claude/docs/documentation-references.md").unlink()
    written = mod.add_scenario(
        repo, "DEUSEX", "Deus Ex", "Someone is pulling the strings."
    )
    assert (repo / ".claude/docs/deusex-scenario.md").exists()
    assert ".claude/docs/documentation-references.md" not in written


def test_new_refuses_any_existing_rule_loc_key(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    loc = repo / "localisation/english/MD_game_rules_l_english.yml"
    _write(loc, _read(loc) + ' RULE_OVERLOOK_SCENARIO_ENABLED_DESC: "x"\n', bom=True)
    with pytest.raises(mod.ToolError, match="RULE_OVERLOOK_SCENARIO_ENABLED_DESC"):
        mod.add_scenario(repo, "OVERLOOK", "Overlook", "x")
    assert "rule_overlook_scenario" not in _read(
        repo / "common/game_rules/00_game_rules.txt"
    )


@pytest.mark.parametrize(
    "key, name, description, message",
    [
        ("silenthill", "Silent Hill", "x", "uppercase"),
        ("S", "Silent Hill", "x", "uppercase"),
        ("SILENTHILL", "Two\nlines", "x", "one line"),
        ("SILENTHILL", "Silent Hill", 'a "quote"', "one line"),
        ("SILENTHILL", " ", "x", "one line"),
        ("OTHER", "Other", "x", "namespace OTHER"),
    ],
)
def test_new_rejects_bad_input(tmp_path, key, name, description, message):
    mod = _module()
    with pytest.raises(mod.ToolError, match=message):
        mod.add_scenario(_repo(tmp_path), key, name, description)


def test_new_refuses_collisions(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    mod.add_scenario(repo, "SILENTHILL", "Silent Hill", "x")
    with pytest.raises(mod.ToolError, match="already exists in common/game_rules"):
        mod.add_scenario(repo, "SILENTHILL", "Silent Hill", "x")

    repo2 = _repo(tmp_path / "b")
    loc = repo2 / "localisation/english/MD_game_rules_l_english.yml"
    _write(loc, _read(loc) + ' RULE_OVERLOOK_SCENARIO: "x"\n', bom=True)
    with pytest.raises(mod.ToolError, match="RULE_OVERLOOK_SCENARIO already exists"):
        mod.add_scenario(repo2, "OVERLOOK", "Overlook", "x")

    repo3 = _repo(tmp_path / "c")
    _write(repo3 / "common/on_actions/99_MGS_on_actions.txt", "x")
    with pytest.raises(mod.ToolError, match="refusing to overwrite"):
        mod.add_scenario(repo3, "MGS", "Metal Gear", "x")
    assert "rule_mgs_scenario" not in _read(
        repo3 / "common/game_rules/00_game_rules.txt"
    )


def test_subsystems_take_consecutive_blocks(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    mod.add_scenario(repo, "SILENTHILL", "Silent Hill", "x")
    block, written = mod.add_subsystem(repo, "SILENTHILL", "order", "The Order")
    assert block == (10, 19)
    assert "events/SILENTHILL_order.txt" in written
    block, _ = mod.add_subsystem(repo, "SILENTHILL", "visitors", "Visitors")
    assert block == (20, 29)

    pulse = _read(repo / "common/scripted_effects/99_SILENTHILL_pulse_effects.txt")
    assert (
        "SILENTHILL_monthly_pulse = {\n\tSILENTHILL_monthly_order_pulse = yes\n\tSILENTHILL_monthly_visitors_pulse = yes\n}"
        in pulse
    )
    doc = _read(repo / ".claude/docs/silenthill-scenario.md")
    assert "- **The Order (10–19):** `SILENTHILL_order.txt`" in doc
    assert doc.index("Visitors (20–29)") < doc.index("Localisation file names are")
    assert "The next free block is 30–39." in doc
    assert "`99_SILENTHILL_visitors_effects.txt`.\n\nLocalisation file names are" in doc
    assert (
        _read(repo / "common/scripted_effects/99_SILENTHILL_order_effects.txt")
        == "SILENTHILL_monthly_order_pulse = {\n}\n"
    )
    assert (
        (repo / "localisation/english/MD_SILENTHILL_order_l_english.yml")
        .read_bytes()
        .startswith(b"\xef\xbb\xbf")
    )


def test_subsystem_refuses_an_occupied_block(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    mod.add_scenario(repo, "SILENTHILL", "Silent Hill", "x")
    _write(
        repo / "events/SILENTHILL_early.txt",
        "country_event = {\n\tid = SILENTHILL.12\n}\n",
    )
    with pytest.raises(mod.ToolError, match=r"SILENTHILL\.12"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "The Order")
    assert not (repo / "events/SILENTHILL_order.txt").exists()


def test_subsystem_refuses_a_pulse_defined_elsewhere(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    mod.add_scenario(repo, "SILENTHILL", "Silent Hill", "x")
    _write(
        repo / "common/scripted_effects/99_SILENTHILL_misc_effects.txt",
        "SILENTHILL_monthly_order_pulse = {\n\tlog = x\n}\n",
    )
    with pytest.raises(mod.ToolError, match="already defined in 99_SILENTHILL_misc"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "The Order")


def test_subsystem_on_a_stalker_style_doc(tmp_path):
    mod = _module()
    repo = tmp_path / "repo"
    _write(
        repo / ".claude/docs/stalker-scenario.md",
        "# STALKER\r\n\r\n## Subsystems\r\n\r\n- **Core (1–9):** `STALKER.txt`.\r\n\r\n"
        "Localisation file names are `x`.\r\n\r\nThe next free block is 160–169. Decision categories.\r\n",
    )
    _write(
        repo / "common/scripted_effects/99_STALKER_pulse_effects.txt",
        "# entry\r\nSTALKER_monthly_pulse = {\r\n\tSTALKER_monthly_meme_pulse = yes\r\n}\r\n",
    )
    block, _ = mod.add_subsystem(repo, "STALKER", "silent", "Silent")
    assert block == (160, 169)
    pulse_path = repo / "common/scripted_effects/99_STALKER_pulse_effects.txt"
    assert (
        b"\tSTALKER_monthly_meme_pulse = yes\r\n\tSTALKER_monthly_silent_pulse = yes\r\n}"
        in pulse_path.read_bytes()
    )
    doc = _read(repo / ".claude/docs/stalker-scenario.md")
    assert "The next free block is 170–179. Decision categories." in doc


def _scenario(tmp_path):
    mod = _module()
    repo = _repo(tmp_path)
    mod.add_scenario(repo, "SILENTHILL", "Silent Hill", "x")
    return mod, repo


def test_subsystem_rejects_bad_input(tmp_path):
    mod, repo = _scenario(tmp_path)
    with pytest.raises(mod.ToolError, match="uppercase key"):
        mod.add_subsystem(repo, "silenthill", "order", "x")
    with pytest.raises(mod.ToolError, match="lowercase"):
        mod.add_subsystem(repo, "SILENTHILL", "Order", "x")
    with pytest.raises(mod.ToolError, match="one line"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "a\nb")
    with pytest.raises(mod.ToolError, match="no OVERLOOK scenario"):
        mod.add_subsystem(repo, "OVERLOOK", "order", "x")


def test_subsystem_refuses_broken_or_duplicate_state(tmp_path):
    mod, repo = _scenario(tmp_path)
    doc = repo / ".claude/docs/silenthill-scenario.md"
    pulse = repo / "common/scripted_effects/99_SILENTHILL_pulse_effects.txt"
    original_doc, original_pulse = _read(doc), _read(pulse)

    _write(doc, original_doc.replace("The next free block is 10–19.", ""))
    with pytest.raises(mod.ToolError, match="no 'The next free block"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "x")

    _write(doc, original_doc.replace("## Subsystems", "## Parts"))
    with pytest.raises(mod.ToolError, match="needs a '## Subsystems'"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "x")

    _write(doc, original_doc)
    _write(pulse, "# nothing here\n")
    with pytest.raises(mod.ToolError, match="does not define SILENTHILL_monthly_pulse"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "x")
    _write(pulse, "SILENTHILL_monthly_pulse = {\n\tx = yes")
    with pytest.raises(mod.ToolError, match="is not closed"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "x")
    _write(
        pulse,
        original_pulse.replace("{\n}", "{\n\tSILENTHILL_monthly_order_pulse = yes\n}"),
    )
    with pytest.raises(mod.ToolError, match="already in"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "x")

    _write(pulse, original_pulse)
    _write(repo / "events/SILENTHILL_order.txt", "x")
    with pytest.raises(mod.ToolError, match="refusing to overwrite"):
        mod.add_subsystem(repo, "SILENTHILL", "order", "x")


def test_main(tmp_path, capsys):
    mod = _module()
    repo = _repo(tmp_path)
    assert (
        mod.main(
            [
                "--repo",
                str(repo),
                "new",
                "SILENTHILL",
                "Silent Hill",
                "--description",
                "x",
            ]
        )
        == 0
    )
    assert "Scaffolded the SILENTHILL scenario" in capsys.readouterr().out
    assert (
        mod.main(["--repo", str(repo), "subsystem", "SILENTHILL", "order", "The Order"])
        == 0
    )
    assert "event IDs 10-19" in capsys.readouterr().out
    assert mod.main(["--repo", str(repo), "subsystem", "NOPE", "order", "x"]) == 1
    assert "error: no NOPE scenario" in capsys.readouterr().err
