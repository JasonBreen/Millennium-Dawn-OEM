from pathlib import Path

from great_ai_race_state_model_test import _parse_race_script
from targeted_operations_core_test import TargetScript

ROOT = Path(__file__).resolve().parents[2]
CT_SETUP = _parse_race_script(
    (ROOT / "common/scripted_effects/00_ct_effects.txt").read_text(encoding="utf-8")
)["counter_terror_global_setup"]


def test_registry_initialization_precedes_country_startup():
    calls = [name for name, _, _ in CT_SETUP]
    assert calls.index("TOP_initialize_global") < calls.index("create_staggered_cycle")


def test_country_case_arrays_use_registry_capacity_at_startup():
    script = TargetScript()
    script.globals.clear()
    script.globals["TOP_rule_enabled"] = 1
    country_vars = script.countries[1]["vars"]
    country_vars.clear()

    initialized = []
    for name, _, operand in CT_SETUP:
        if name == "TOP_initialize_global":
            assert operand == "yes"
            script.run("TOP_setup_registry", 1)
            initialized.append(name)
        elif name == "create_staggered_cycle":
            assert operand == "yes"
            script.run("TOP_country_initialize", 1)
            initialized.append(name)

    assert sorted(initialized) == ["TOP_initialize_global", "create_staggered_cycle"]
    capacity = script.globals["TOP_registry_capacity"]
    assert capacity == 161
    assert len(country_vars["TOP_known"]) == capacity

    case_arrays = [
        operand[0][0]
        for name, _, operand in script.effects["TOP_initialize_cases"]
        if name == "resize_array"
    ]
    assert len(case_arrays) == len(set(case_arrays)) == 15
    assert all(name.startswith("TOP_case_") for name in case_arrays)
    assert {name: len(country_vars[name]) for name in case_arrays} == {
        name: capacity for name in case_arrays
    }
