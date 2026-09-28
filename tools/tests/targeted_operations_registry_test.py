"""Contract checks for the first upstream TOP registry slice."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "common/scripted_effects/01_targeted_operations_registry.txt"
MANIFEST_RELATIVE = Path("tools/data/targeted_operations.json")

spec = importlib.util.spec_from_file_location(
    "generate_targeted_operations",
    ROOT / "tools/generators/generate_targeted_operations.py",
)
assert spec is not None and spec.loader is not None
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def write_manifest(root: Path, data: dict) -> None:
    path = root / MANIFEST_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        json.dump(data, stream)


def test_checked_in_registry_matches_manifest() -> None:
    manifest = generator.load_manifest(ROOT)
    assert generator.registry(manifest) == REGISTRY_PATH.read_text(encoding="utf-8")


def test_authored_identity_keys_cannot_be_reassigned(tmp_path: Path) -> None:
    manifest = copy.deepcopy(generator.load_manifest(ROOT))
    manifest["targets"][0]["key"], manifest["targets"][1]["key"] = (
        manifest["targets"][1]["key"],
        manifest["targets"][0]["key"],
    )
    write_manifest(tmp_path, manifest)
    with pytest.raises(ValueError, match="retain their stable IDs"):
        generator.load_manifest(tmp_path)


def test_historical_outcome_cannot_force_a_campaign_removal(tmp_path: Path) -> None:
    manifest = copy.deepcopy(generator.load_manifest(ROOT))
    manifest["targets"][0]["historical_outcome"]["force_in_campaign"] = True
    write_manifest(tmp_path, manifest)
    with pytest.raises(ValueError, match="cannot force campaign removals"):
        generator.load_manifest(tmp_path)


def test_check_reports_drift_without_rewriting_output(tmp_path: Path) -> None:
    write_manifest(tmp_path, generator.load_manifest(ROOT))
    output = tmp_path / "common/scripted_effects/01_targeted_operations_registry.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        stream.write("stale\n")

    assert generator.generate(tmp_path, check=True) == [
        "common/scripted_effects/01_targeted_operations_registry.txt"
    ]
    assert output.read_text(encoding="utf-8") == "stale\n"
