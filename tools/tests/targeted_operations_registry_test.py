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


def test_existing_representations_resolve_to_shipped_files() -> None:
    manifest = generator.load_manifest(ROOT)
    for target in manifest["targets"]:
        for representation in target["existing_representations"]:
            assert (ROOT / representation["path"]).is_file(), (
                target["id"],
                representation["path"],
            )


def test_authored_successor_requires_group_pool_even_without_successors(
    tmp_path: Path,
) -> None:
    manifest = copy.deepcopy(generator.load_manifest(ROOT))
    group = next(group for group in manifest["groups"] if group["id"] == 22)
    group["succession"] = []
    write_manifest(tmp_path, manifest)
    with pytest.raises(
        ValueError, match="Authored successor missing from group pool: 145"
    ):
        generator.load_manifest(tmp_path)


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


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate_id",
        "duplicate_key",
        "duplicate_group",
        "duplicate_ct_slot",
        "foreign_successor",
        "missing_successor",
        "foreign_group_successor",
        "generated_overlap",
        "generated_end",
        "capacity",
        "target_class",
        "group_class",
        "location_policy",
        "unknown_source",
        "stable_group_key",
        "negative_ct_slot",
        "group_public_identity",
        "target_public_identity",
        "facility_default",
        "empty_facility_override",
        "unknown_facility_override",
        "leader_role",
        "leader_office",
        "consequence_profile",
        "duplicate_successor",
        "incomplete_successor",
        "activation_year",
        "missing_sources",
    ],
)
def test_manifest_rejects_invalid_identity_and_provenance(
    tmp_path: Path, defect: str
) -> None:
    data = copy.deepcopy(generator.load_manifest(ROOT))
    if defect == "duplicate_id":
        data["targets"][1]["id"] = data["targets"][0]["id"]
    elif defect == "duplicate_key":
        data["targets"][1]["key"] = data["targets"][0]["key"]
    elif defect == "duplicate_group":
        data["groups"][1]["id"] = data["groups"][0]["id"]
    elif defect == "duplicate_ct_slot":
        data["groups"][1]["ct_id"] = data["groups"][0]["ct_id"]
    elif defect == "foreign_successor":
        data["targets"][0]["successors"].append(64)
    elif defect == "missing_successor":
        data["targets"][0]["successors"].append(999)
    elif defect == "foreign_group_successor":
        data["groups"][0]["succession"].append(64)
    elif defect == "generated_overlap":
        data["targets"][-1]["id"] = 65
    elif defect == "generated_end":
        data["generated_end"] = 130
    elif defect == "capacity":
        data["capacity"] += 1
    elif defect == "target_class":
        data["targets"][0]["target_class"] = "person"
    elif defect == "group_class":
        data["groups"][0]["group_class"] = "organization"
    elif defect == "location_policy":
        data["groups"][0]["location_policy"] = "random_state"
    elif defect == "unknown_source":
        data["targets"][0]["sources"].append("missing_source")
    elif defect == "stable_group_key":
        data["groups"][0]["key"], data["groups"][1]["key"] = (
            data["groups"][1]["key"],
            data["groups"][0]["key"],
        )
    elif defect == "negative_ct_slot":
        data["groups"][0]["ct_id"] = -1
    elif defect == "group_public_identity":
        data["groups"][0]["public_identity"] = True
    elif defect == "target_public_identity":
        data["targets"][0]["public_identity"] = True
    elif defect == "facility_default":
        data["facility_objective_defaults"]["state_security"] = [
            "command",
            "funding",
        ]
    elif defect == "empty_facility_override":
        data["groups"][0]["facility_objectives"] = []
    elif defect == "unknown_facility_override":
        data["groups"][0]["facility_objectives"] = ["safehouse"]
    elif defect == "leader_role":
        data["targets"][0]["leader_role"] = "president"
    elif defect == "leader_office":
        leader = next(
            target for target in data["targets"] if target["leader_role"] != "none"
        )
        leader["role_eligibility"]["office_keys"] = []
    elif defect == "consequence_profile":
        data["targets"][0]["consequence_profile"] = "political_leader"
    elif defect == "duplicate_successor":
        data["targets"][0]["successors"].append(data["targets"][0]["successors"][0])
    elif defect == "incomplete_successor":
        data["targets"][0]["successors"].pop()
    elif defect == "activation_year":
        data["targets"][0]["activation_year"] = 1999
    else:
        data["targets"][0]["sources"] = []

    write_manifest(tmp_path, data)
    with pytest.raises(ValueError):
        generator.load_manifest(tmp_path)


def test_facility_objectives_can_override_known_defaults() -> None:
    data = copy.deepcopy(generator.load_manifest(ROOT))
    group = next(
        group
        for group in data["groups"]
        if group["group_class"] == "political_executive"
    )
    group["facility_objectives"] = ["training"]
    assert generator.group_objective_mask(data, group) == 2


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
