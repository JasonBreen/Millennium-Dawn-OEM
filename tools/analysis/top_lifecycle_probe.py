"""Check TOP lifecycle wiring and inspect its opt-in HOI4 game.log markers.

Run ``wiring`` before launching the mod. In a new campaign, open the HOI4
console and enter ``effect TOP_enable_diagnostics = yes``. Let two
weekly pulses pass, then run ``log <game.log> --expect-mode limited`` (or
``full`` / ``off``). Log evidence proves the hooks executed in that campaign;
the static wiring check alone does not.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from shared_utils import extract_block_from_text  # noqa: E402

PROBE_RE = re.compile(
    r"TOP_PROBE mode=(?P<mode>-?\d+(?:\.\d+)?) "
    r"clock=(?P<clock>-?\d+(?:\.\d+)?) "
    r"registry=(?P<registry>-?\d+(?:\.\d+)?) "
    r"country_ticks=(?P<country_ticks>-?\d+(?:\.\d+)?)"
)
MODES = {"off": 0, "limited": 1, "full": 2}


def named_block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    if match is None:
        raise ValueError(f"Missing block: {name}")
    body, end = extract_block_from_text(text, match.start())
    if end == -1:
        raise ValueError(f"Unbalanced block: {name}")
    return body


def check_wiring(root: Path) -> list[str]:
    """Return missing source links; this is not an engine execution test."""
    paths = {
        "startup": "common/on_actions/00_on_actions.txt",
        "weekly": "common/on_actions/MD_on_actions.txt",
        "ct": "common/scripted_effects/00_ct_effects.txt",
        "lifecycle": "common/scripted_effects/00_targeted_operations_lifecycle.txt",
        "registry": "common/scripted_effects/01_targeted_operations_registry.txt",
        "triggers": "common/scripted_triggers/01_targeted_operations_triggers.txt",
    }
    source = {
        name: (root / path).read_text(encoding="utf-8-sig")
        for name, path in paths.items()
    }
    failures = []

    def require(block: str, call: str, location: str) -> None:
        if re.search(rf"(?m)^\s*{re.escape(call)}\s*=\s*yes\s*$", block) is None:
            failures.append(f"{location} does not call {call}")

    require(
        named_block(source["startup"], "on_startup"),
        "counter_terror_global_setup",
        "on_startup",
    )
    ct_global = named_block(source["ct"], "counter_terror_global_setup")
    require(ct_global, "TOP_cache_game_rule", "counter_terror_global_setup")
    require(ct_global, "TOP_initialize_global", "counter_terror_global_setup")
    require(ct_global, "create_staggered_cycle", "counter_terror_global_setup")
    require(
        named_block(source["ct"], "create_staggered_cycle"),
        "add_on_creation",
        "create_staggered_cycle",
    )
    require(
        named_block(source["ct"], "add_on_creation"),
        "counter_terror_nation_startup",
        "add_on_creation",
    )
    require(
        named_block(source["ct"], "counter_terror_nation_startup"),
        "TOP_country_initialize",
        "counter_terror_nation_startup",
    )
    require(
        named_block(source["ct"], "ct_staggered_country_tick"),
        "TOP_country_tick",
        "ct_staggered_country_tick",
    )
    weekly = named_block(source["weekly"], "on_weekly")
    country_buckets = len(
        re.findall(r"(?m)^\s*ct_staggered_country_tick\s*=\s*yes\s*$", weekly)
    )
    if country_buckets != 4:
        failures.append(
            f"on_weekly dispatches {country_buckets} CT country buckets; expected four"
        )
    guard = weekly.find("has_global_flag = on_weekly_global_done")
    if guard < 0:
        failures.append("on_weekly lacks the existing global once-per-week guard")
    else:
        guard_block, end = extract_block_from_text(
            weekly, weekly.rfind("if = {", 0, guard)
        )
        if end == -1:
            failures.append("on_weekly global guard is unbalanced")
        else:
            require(guard_block, "TOP_global_weekly", "on_weekly global guard")

    require(
        named_block(source["lifecycle"], "TOP_initialize_global"),
        "TOP_setup_registry",
        "TOP_initialize_global",
    )
    require(
        named_block(source["lifecycle"], "TOP_country_initialize"),
        "TOP_resize_country_arrays",
        "TOP_country_initialize",
    )
    if "set_global_flag = TOP_diagnostics_enabled" not in named_block(
        source["lifecycle"], "TOP_enable_diagnostics"
    ):
        failures.append("TOP_enable_diagnostics does not set the diagnostic flag")
    global_weekly = named_block(source["lifecycle"], "TOP_global_weekly")
    require(global_weekly, "TOP_cache_game_rule", "TOP_global_weekly")
    require(global_weekly, "TOP_initialize_global", "TOP_global_weekly")
    if "add_to_variable = { global.TOP_clock = 7 }" not in global_weekly:
        failures.append("TOP_global_weekly does not advance the clock by seven")
    require(
        named_block(source["lifecycle"], "TOP_country_tick"),
        "TOP_country_initialize",
        "TOP_country_tick",
    )
    for name in ("TOP_setup_registry", "TOP_resize_country_arrays"):
        named_block(source["registry"], name)
    if "has_game_rule" in source["triggers"]:
        failures.append(
            "TOP scripted triggers evaluate has_game_rule before a game exists"
        )
    if "is_ai = no" not in named_block(source["triggers"], "TOP_human_offense"):
        failures.append("TOP_human_offense lacks the player-only gate")
    return failures


def parse_probes(log: str) -> list[dict[str, int]]:
    probes = []
    for match in PROBE_RE.finditer(log):
        probes.append(
            {name: int(float(value)) for name, value in match.groupdict().items()}
        )
    return probes


def check_probes(
    probes: list[dict[str, int]], mode: str, capacity: int, min_samples: int = 2
) -> list[str]:
    failures = []
    if len(probes) < min_samples:
        return [f"Found {len(probes)} TOP_PROBE samples; need {min_samples}"]
    expected_mode = MODES[mode]
    for number, probe in enumerate(probes, 1):
        if probe["mode"] != expected_mode:
            failures.append(f"Sample {number}: mode {probe['mode']} != {expected_mode}")
        expected_capacity = 0 if mode == "off" else capacity
        if probe["registry"] != expected_capacity:
            failures.append(
                f"Sample {number}: registry {probe['registry']} != {expected_capacity}"
            )
        if mode == "off" and (probe["clock"] != 0 or probe["country_ticks"] != 0):
            failures.append(f"Sample {number}: Off mode advanced TOP state")
    if mode != "off":
        for previous, current in zip(probes, probes[1:]):
            if current["clock"] - previous["clock"] != 7:
                failures.append("TOP clock did not advance by seven between samples")
        if not any(probe["country_ticks"] > 0 for probe in probes[1:]):
            failures.append("No staggered country tick appeared after the first sample")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="mod checkout to inspect"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("wiring", help="check static hook reachability")
    log_parser = subparsers.add_parser(
        "log", help="check opt-in native game.log markers"
    )
    log_parser.add_argument("game_log", type=Path)
    log_parser.add_argument("--expect-mode", choices=MODES, required=True)
    log_parser.add_argument("--min-samples", type=int, default=2)
    args = parser.parse_args(argv)

    if args.command == "wiring":
        failures = check_wiring(args.root)
        label = "static TOP lifecycle wiring"
    else:
        registry = (
            args.root / "common/scripted_effects/01_targeted_operations_registry.txt"
        ).read_text(encoding="utf-8")
        match = re.search(
            r"resize_array\s*=\s*\{\s*global\.TOP_status\s*=\s*(\d+)\s*\}",
            registry,
        )
        if match is None:
            parser.error("generated registry lacks TOP_status capacity")
        probes = parse_probes(args.game_log.read_text(encoding="utf-8-sig"))
        failures = check_probes(
            probes, args.expect_mode, int(match.group(1)), args.min_samples
        )
        label = f"{len(probes)} native TOP_PROBE samples in {args.expect_mode} mode"
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"PASS: {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
