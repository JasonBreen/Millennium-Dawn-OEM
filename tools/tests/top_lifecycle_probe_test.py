"""Focused checks for TOP source wiring and native log probe evaluation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import top_lifecycle_probe

ROOT = Path(__file__).resolve().parents[2]


def copy_wiring_files(root: Path) -> None:
    paths = (
        "common/on_actions/00_on_actions.txt",
        "common/on_actions/MD_on_actions.txt",
        "common/scripted_effects/00_ct_effects.txt",
        "common/scripted_effects/00_targeted_operations_lifecycle.txt",
        "common/scripted_effects/01_targeted_operations_registry.txt",
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "common/game_rules/01_targeted_operations.txt",
    )
    for relative in paths:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())


def test_current_lifecycle_wiring_is_reachable():
    assert top_lifecycle_probe.check_wiring(ROOT) == []


def test_wiring_detects_removed_country_tick(tmp_path):
    copy_wiring_files(tmp_path)
    ct_effects = tmp_path / "common/scripted_effects/00_ct_effects.txt"
    ct_effects.write_bytes(
        ct_effects.read_bytes()
        .replace(b"TOP_country_tick = yes", b"always = yes")
        .replace(b"counter_terror_nation_startup = yes", b"always = yes")
    )
    weekly = tmp_path / "common/on_actions/MD_on_actions.txt"
    weekly.write_bytes(
        weekly.read_bytes().replace(b"ct_staggered_country_tick = yes", b"always = yes")
    )
    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "ct_staggered_country_tick does not call TOP_country_tick" in failures
    assert "add_on_creation does not call counter_terror_nation_startup" in failures
    assert "on_weekly dispatches 0 CT country buckets; expected four" in failures


def test_wiring_requires_a_console_diagnostics_setter(tmp_path):
    copy_wiring_files(tmp_path)
    lifecycle = (
        tmp_path / "common/scripted_effects/00_targeted_operations_lifecycle.txt"
    )
    lifecycle.write_text(
        lifecycle.read_text(encoding="utf-8").replace(
            "set_global_flag = TOP_diagnostics_enabled", "always = yes"
        ),
        encoding="utf-8",
    )
    assert (
        "TOP_enable_diagnostics does not set the diagnostic flag"
        in top_lifecycle_probe.check_wiring(tmp_path)
    )


def test_limited_mode_requires_weekly_country_ticks():
    probes = top_lifecycle_probe.parse_probes(
        "[2000.1.8] TOP_PROBE mode=1 clock=7 registry=161 country_ticks=0\n"
        "[2000.1.15] TOP_PROBE mode=1 clock=14 registry=161 country_ticks=32\n"
    )
    assert top_lifecycle_probe.check_probes(probes, "limited", 161) == []


def test_off_mode_stays_inert():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=0 clock=0 registry=0 country_ticks=0\n" * 2
    )
    assert top_lifecycle_probe.check_probes(probes, "off", 161) == []
    probes[1]["clock"] = 7
    assert "Sample 2: Off mode advanced TOP state" in top_lifecycle_probe.check_probes(
        probes, "off", 161
    )


def test_probe_rejects_duplicate_weekly_dispatch_and_missing_country_tick():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=2 clock=7 registry=161 country_ticks=0\n"
        "TOP_PROBE mode=2 clock=7 registry=161 country_ticks=0\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "full", 161)
    assert "TOP clock did not advance by seven between samples" in failures
    assert "Sample 2: no staggered country tick" in failures


def test_probe_rejects_any_missed_weekly_country_tick():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=1 clock=7 registry=161 country_ticks=0\n"
        "TOP_PROBE mode=1 clock=14 registry=161 country_ticks=32\n"
        "TOP_PROBE mode=1 clock=21 registry=161 country_ticks=0\n"
    )
    assert top_lifecycle_probe.check_probes(probes, "limited", 161) == [
        "Sample 3: no staggered country tick"
    ]


def test_probe_rejects_fractional_values():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=1 clock=7.5 registry=161 country_ticks=1\n"
        "TOP_PROBE mode=1.5 clock=14.5 registry=161.5 country_ticks=1\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "limited", 161)
    assert "Sample 1: non-integer clock" in failures
    assert "Sample 2: non-integer mode, clock, registry" in failures


def test_probe_rejects_clocks_outside_the_weekly_phase():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=1 clock=1 registry=161 country_ticks=1\n"
        "TOP_PROBE mode=1 clock=8 registry=161 country_ticks=1\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "limited", 161)
    assert "Sample 1: clock 1 is not a positive multiple of seven" in failures
    assert "Sample 2: clock 8 is not a positive multiple of seven" in failures


def test_wiring_ignores_commented_out_statements(tmp_path):
    copy_wiring_files(tmp_path)
    lifecycle = (
        tmp_path / "common/scripted_effects/00_targeted_operations_lifecycle.txt"
    )
    lifecycle.write_text(
        lifecycle.read_text(encoding="utf-8")
        .replace(
            "set_global_flag = TOP_diagnostics_enabled",
            "# set_global_flag = TOP_diagnostics_enabled",
        )
        .replace(
            "add_to_variable = { global.TOP_clock = 7 }",
            "# add_to_variable = { global.TOP_clock = 7 }",
        ),
        encoding="utf-8",
    )
    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "TOP_enable_diagnostics does not set the diagnostic flag" in failures
    assert "TOP_global_weekly does not advance the clock by seven" in failures


def test_wiring_validates_the_game_rule_options(tmp_path):
    copy_wiring_files(tmp_path)
    rules = tmp_path / "common/game_rules/01_targeted_operations.txt"
    rules.write_text(
        rules.read_text(encoding="utf-8").replace(
            "name = TOP_full_sandbox_option", "name = TOP_renamed_option"
        ),
        encoding="utf-8",
    )
    assert "TOP_game_rule lacks option TOP_full_sandbox_option" in (
        top_lifecycle_probe.check_wiring(tmp_path)
    )


def test_wiring_requires_country_storage_resize(tmp_path):
    copy_wiring_files(tmp_path)
    registry = tmp_path / "common/scripted_effects/01_targeted_operations_registry.txt"
    text = registry.read_text(encoding="utf-8")
    registry.write_text(
        text.replace("resize_array = { TOP_known = 161 }", "always = yes"),
        encoding="utf-8",
    )
    assert (
        "TOP_resize_country_arrays does not size TOP_known to the registry capacity"
        in top_lifecycle_probe.check_wiring(tmp_path)
    )


def test_cli_rejects_sample_threshold_below_two(tmp_path):
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="2"):
        top_lifecycle_probe.main(
            [
                "--root",
                str(ROOT),
                "log",
                str(log),
                "--expect-mode",
                "off",
                "--min-samples",
                "0",
            ]
        )


def test_off_rule_keeps_achievements():
    rules = (ROOT / "common/game_rules/01_targeted_operations.txt").read_text(
        encoding="utf-8"
    )
    off = rules[rules.index("name = TOP_disabled_option") :]
    assert "allow_achievements = yes" in off[: off.index("}")]


def test_probe_requires_enough_native_samples():
    assert top_lifecycle_probe.check_probes([], "limited", 161) == [
        "Found 0 TOP_PROBE samples; need 2"
    ]


def test_probe_rejects_wrong_mode_and_registry_capacity():
    probes = top_lifecycle_probe.parse_probes(
        "TOP_PROBE mode=2 clock=7 registry=160 country_ticks=0\n"
        "TOP_PROBE mode=2 clock=14 registry=160 country_ticks=1\n"
    )
    failures = top_lifecycle_probe.check_probes(probes, "limited", 161)
    assert "Sample 1: mode 2 != 1" in failures
    assert "Sample 1: registry 160 != 161" in failures


def test_cli_reads_capacity_from_generated_array(tmp_path, capsys):
    log = tmp_path / "game.log"
    log.write_text(
        "TOP_PROBE mode=0 clock=0 registry=0 country_ticks=0\n" * 2,
        encoding="utf-8",
    )
    assert (
        top_lifecycle_probe.main(
            ["--root", str(ROOT), "log", str(log), "--expect-mode", "off"]
        )
        == 0
    )
    assert "PASS: 2 native TOP_PROBE samples in off mode" in capsys.readouterr().out


def test_cli_rejects_registry_without_capacity(tmp_path):
    registry = tmp_path / "common/scripted_effects/01_targeted_operations_registry.txt"
    registry.parent.mkdir(parents=True)
    registry.write_text("TOP_setup_registry = {}\n", encoding="utf-8")
    log = tmp_path / "game.log"
    log.write_text("", encoding="utf-8")
    with pytest.raises(SystemExit, match="2"):
        top_lifecycle_probe.main(
            ["--root", str(tmp_path), "log", str(log), "--expect-mode", "off"]
        )
