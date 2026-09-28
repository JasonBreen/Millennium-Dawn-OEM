"""Focused checks for TOP source wiring and native log probe evaluation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import top_lifecycle_probe

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (
    "common/on_actions/00_on_actions.txt",
    "common/on_actions/MD_on_actions.txt",
    "common/scripted_effects/00_ct_effects.txt",
    "common/scripted_effects/00_targeted_operations_effects.txt",
    "common/scripted_effects/01_targeted_operations_registry.txt",
    "common/scripted_triggers/01_targeted_operations_triggers.txt",
    "common/scripted_triggers/04_targeted_operations_cases.txt",
    "common/scripted_triggers/07_targeted_operations_redesign.txt",
    "common/scripted_effects/04_targeted_operations_cases.txt",
    "common/scripted_effects/07_targeted_operations_organization_cases.txt",
)


def copy_sources(root):
    for relative in SOURCE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())


def test_current_system_wiring_is_reachable():
    assert top_lifecycle_probe.check_wiring(ROOT) == []


def test_wiring_detects_removed_country_tick(tmp_path):
    copy_sources(tmp_path)
    ct_effects = tmp_path / "common/scripted_effects/00_ct_effects.txt"
    ct_effects.write_bytes(
        ct_effects.read_bytes().replace(b"TOP_country_tick = yes", b"always = yes")
    )
    weekly = tmp_path / "common/on_actions/MD_on_actions.txt"
    weekly.write_bytes(
        weekly.read_bytes().replace(b"ct_staggered_country_tick = yes", b"always = yes")
    )
    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "ct_staggered_country_tick does not call TOP_country_tick" in failures
    assert "on_weekly dispatches 0 CT country buckets; expected four" in failures


def test_wiring_requires_human_only_offense_and_shared_single_slot(tmp_path):
    copy_sources(tmp_path)
    triggers = tmp_path / "common/scripted_triggers/01_targeted_operations_triggers.txt"
    triggers.write_bytes(triggers.read_bytes().replace(b"\tis_ai = no", b"", 1))
    cases = tmp_path / "common/scripted_triggers/04_targeted_operations_cases.txt"
    cases.write_bytes(
        cases.read_bytes().replace(
            b"TOP_operation_subject_kind = 0", b"TOP_operation_subject_kind = 1"
        )
    )
    redesign = tmp_path / "common/scripted_triggers/07_targeted_operations_redesign.txt"
    redesign.write_bytes(
        redesign.read_bytes().replace(
            b"TOP_operation_slot_available = yes", b"always = yes"
        )
    )

    failures = top_lifecycle_probe.check_wiring(tmp_path)
    assert "TOP_human_offense lacks the player-only gate" in failures
    assert "TOP_operation_slot_available does not require an empty slot" in failures
    assert (
        "Person and organization operations do not share the single slot gate"
        in failures
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
    assert "No staggered country tick appeared after the first sample" in failures


def test_probe_requires_enough_native_samples():
    assert top_lifecycle_probe.check_probes([], "limited", 161) == [
        "Found 0 TOP_PROBE samples; need 2"
    ]


def test_slot_trace_accepts_completed_person_and_organization_operations():
    events = top_lifecycle_probe.parse_slot_events(
        "TOP_SLOT event=begin actor=USA kind=1 id=12 seq=3 clock=14\n"
        "TOP_SLOT event=begin actor=FRA kind=2 id=7 seq=1 clock=14\n"
        "TOP_SLOT event=end actor=USA kind=1 id=12 seq=3 clock=42\n"
        "TOP_SLOT event=end actor=FRA kind=2 id=7 seq=1 clock=42\n"
    )
    assert top_lifecycle_probe.check_slot_events(events) == []


def test_slot_trace_rejects_overlap_and_mismatched_release():
    events = top_lifecycle_probe.parse_slot_events(
        "TOP_SLOT event=begin actor=USA kind=1 id=12 seq=3 clock=14\n"
        "TOP_SLOT event=begin actor=USA kind=2 id=7 seq=1 clock=14\n"
        "TOP_SLOT event=end actor=USA kind=1 id=12 seq=4 clock=42\n"
    )
    failures = top_lifecycle_probe.check_slot_events(events)
    assert "Trace 2: USA began (2, 7, 1) while (1, 12, 3) was active" in failures
    assert "Trace 3: USA ended (1, 12, 4) instead of (1, 12, 3)" in failures
    assert "USA still holds slot (1, 12, 3)" in failures


def test_wiring_detects_missing_organization_slot_trace(tmp_path):
    copy_sources(tmp_path)
    cases = (
        tmp_path
        / "common/scripted_effects/07_targeted_operations_organization_cases.txt"
    )
    cases.write_bytes(cases.read_bytes().replace(b"TOP_trace_slot_begin = yes", b""))
    assert (
        "organization operation begin lacks one slot trace"
        in top_lifecycle_probe.check_wiring(tmp_path)
    )
