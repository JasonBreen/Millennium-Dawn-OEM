"""Regression cases for corporate-history contract failures and valid boundaries."""

import copy
import json
from pathlib import Path

import pytest
from validate_corporate_history_contract import (
    BlockDef,
    Validator,
    _program_lifecycle_findings,
)
from validate_corporate_history_contract_test import (
    _build_fixture,
    _enable_economic_layer_fixture,
    _manifest,
)


def _write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(text)


@pytest.fixture(scope="module")
def shared_inputs():
    root = Path(__file__).resolve().parents[2]
    payload = json.loads((root / "corporate_history_contract.json").read_text("utf-8"))
    system = payload["shared_systems"][0]
    paths = {
        relative
        for value in system["files"].values()
        for relative in (value if isinstance(value, list) else [value])
    }
    return (
        payload["schema_version"],
        system,
        {relative: (root.parent / relative).read_bytes() for relative in paths},
    )


@pytest.fixture
def shared(tmp_path, shared_inputs):
    version, system, inputs = shared_inputs
    for relative, content in inputs.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    validator = Validator(str(tmp_path), no_color=True)
    validator._manifest_payload = {
        "schema_version": version,
        "shared_systems": [copy.deepcopy(system)],
    }
    return validator


def _system(validator):
    return validator._manifest_payload["shared_systems"][0]


def _shared_findings(validator):
    effects = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    return validator._validate_shared_systems(effects, validator._load_events())


def _assert_finding(findings, expected):
    assert any(expected in message for message, _, _ in findings), findings
    assert all(file and line >= 1 for _, file, line in findings)


def _replace_role(validator, role, before, after):
    relative = _system(validator)["files"][role]
    text = (validator._root / relative).read_text("utf-8-sig")
    assert before in text, (role, before)
    _write(validator._root, relative, text.replace(before, after))


def _set_effect(validator, name, body):
    effects = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    effects[name] = [BlockDef(name, "common/scripted_effects/fixture.txt", 2, body)]
    return validator._validate_shared_systems(effects, validator._load_events())


def test_shared_system_shipping_contract_is_valid(shared):
    assert _shared_findings(shared) == []


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("files", [], "files must be an object"),
        ("files", {}, "files is missing:"),
        ("game_rule", None, "game_rule must be an object"),
        ("game_rule", {"id": "absent"}, "requires exactly one absent"),
        ("variables", [], "exact bounded base"),
        ("variables", {"bad": {}}, "exact bounded base"),
        ("initial_state", {}, "approved 2/3/3 Mixed initial state"),
        ("support_model_codes", {}, "support codes 0..3"),
        ("support_model_precedence", "adapter_first", "base-first precedence"),
        ("reconstruction_baseline", [], "neutral reconstruction baseline"),
        ("historical_routes", {}, "national historical routes"),
        ("scripted_effects", [], "scripted_effects must be a non-empty list"),
        ("scripted_effects", ["missing_effect"], "requires exactly one missing_effect"),
        ("event_ids", [], "must reserve exactly"),
        (
            "lifecycle_markers",
            {"linux_system_events.1": []},
            "expected, pending, and resolved",
        ),
        (
            "lifecycle_markers",
            {"linux_system_events.1": ["lost", "pending", "resolved"]},
            "never uses lifecycle marker lost",
        ),
        (
            "participant_array",
            "global.linux_system_participants",
            "without a global registry",
        ),
        ("dispatcher_host", "ABK", "country-local on_monthly driver"),
        ("owned_timed_ideas", None, "owned_timed_ideas must be a list"),
        ("adoption_ideas", ["missing_idea"], "missing idea missing_idea"),
        ("persistent_idea_modifiers", [], "persistent economic modifier matrix"),
        (
            "persistent_idea_modifiers",
            {"bad": None},
            "persistent economic modifier matrix",
        ),
        ("timed_idea_modifiers", {}, "timed economic modifier matrix"),
        ("programs", {}, "approved program costs, durations, and state changes"),
        (
            "excluded_generic_idea_tags",
            [],
            "exclude USA from both generic idea families",
        ),
        ("allowed_native_reads", [], "undeclared native reads"),
        (
            "storage_lifecycle_markers",
            {"USA_oem_events.16": []},
            "storage lifecycle declaration",
        ),
        (
            "storage_lifecycle_markers",
            {"USA_oem_events.16": ["lost", "pending", "resolved"]},
            "never uses lifecycle marker lost",
        ),
        ("usa_bridge_effect", "absent_bridge", "requires exactly one absent_bridge"),
    ],
)
def test_shared_system_rejects_incompatible_manifest_values(
    shared, field, value, expected
):
    _system(shared)[field] = value
    _assert_finding(_shared_findings(shared), expected)


@pytest.mark.parametrize("value", [None, "invalid", 1])
def test_shared_system_rejects_non_object_entry(shared, value):
    shared._manifest_payload["shared_systems"] = [value]
    _assert_finding(_shared_findings(shared), "shared_systems[0] must be an object")


@pytest.mark.parametrize(
    ("role", "before", "after", "expected"),
    [
        (
            "rule",
            "name = outcomes_only",
            "name = other",
            "does not contain all declared options",
        ),
        (
            "trigger",
            "linux_system_full_enabled = {",
            "lost_full_enabled = {",
            "requires exactly one linux_system_full_enabled",
        ),
        (
            "effect",
            "max = 10",
            "max = 11",
            "must clamp linux_system_base_deployment to 0..10",
        ),
        (
            "event",
            "is_triggered_only = yes",
            "is_triggered_only = no",
            "must be triggered-only",
        ),
        (
            "event",
            "country_event = {",
            "news_event = {",
            "must not define global news events",
        ),
        (
            "category",
            "linux_system_full_enabled = yes",
            "always = yes",
            "category must be visible only in Full mode",
        ),
        (
            "decision",
            "cost = 25",
            "cost = 26",
            "must use its declared PP cost and active duration",
        ),
        (
            "decision",
            "fire_only_once = no",
            "fire_only_once = yes",
            "must remain reusable",
        ),
        (
            "decision",
            "complete_effect = {",
            "unused_effect = {",
            "is missing complete_effect",
        ),
        (
            "decision",
            "remove_effect = {",
            "unused_remove = {",
            "is missing remove_effect",
        ),
        ("decision", "log =", "ignored_log =", "must log first"),
        (
            "decision",
            "linux_system_full_enabled = yes",
            "always = yes",
            "must be exposed only in Full mode",
        ),
        (
            "decision",
            "has_active_mission = bankruptcy_incoming_collapse",
            "always = no",
            "must block AI during bankruptcy collapse",
        ),
        (
            "decision",
            "NOT = { original_tag = USA }",
            "NOT = { original_tag = GER }",
            "public_procurement must be hidden for USA",
        ),
        (
            "trigger",
            "linux_system_upstream_maintenance_program",
            "absent_program",
            "active-program trigger must cover all four program ideas",
        ),
        (
            "idea",
            "research_speed_factor = 0.005",
            "research_speed_factor = 0.006",
            "modifiers do not match the shared-system contract",
        ),
    ],
)
def test_shared_system_rejects_script_contract_drift(
    shared, role, before, after, expected
):
    _replace_role(shared, role, before, after)
    _assert_finding(_shared_findings(shared), expected)


@pytest.mark.parametrize(
    ("name", "body", "expected"),
    [
        (
            "linux_system_reconstruct_country",
            "linux_system_bad_helper = yes",
            "forbidden side effect modify_treasury_effect through linux_system_bad_helper",
        ),
        (
            "linux_system_refresh_ideas",
            "always = yes",
            "does not own every declared idea",
        ),
        (
            "linux_system_clear_owned_artifacts",
            "always = yes",
            "must remove every owned idea",
        ),
        (
            "linux_system_apply_upstream_maintenance_program",
            "always = yes",
            "does not charge its declared GDP fraction",
        ),
        (
            "linux_system_apply_enterprise_support_program",
            "always = yes",
            "must set support model 2",
        ),
        (
            "linux_system_apply_public_procurement_program",
            "set_variable = { linux_system_base_support_model = 1 }",
            "may not change the support model",
        ),
        (
            "USA_corporate_systems_linux_contribution",
            "always = yes",
            "must read all four generic base-state inputs",
        ),
        (
            "USA_corporate_systems_linux_contribution",
            "set_temp_variable = { value = linux_system_effective_deployment }",
            "may not read adapter or effective Linux state",
        ),
        (
            "USA_corporate_systems_linux_contribution",
            "add_to_temp_variable = { USA_oem_contribution_deployment = 2 }",
            "contributions must be limited to one point per axis",
        ),
    ],
)
def test_shared_system_effect_contracts_follow_reachable_helpers(
    shared, name, body, expected
):
    _write(
        shared._root,
        "common/scripted_effects/fixture.txt",
        "linux_system_bad_helper = { modify_treasury_effect = yes }",
    )
    _assert_finding(_set_effect(shared, name, body), expected)


def test_shared_system_reconstruction_cycle_is_safe_without_replayed_rewards(shared):
    _write(
        shared._root,
        "common/scripted_effects/fixture.txt",
        "linux_system_helper = { linux_system_reconstruct_country = yes }",
    )
    assert (
        _set_effect(
            shared, "linux_system_reconstruct_country", "linux_system_helper = yes"
        )
        == []
    )


@pytest.mark.parametrize("role", ["rule", "effect", "event", "decision"])
def test_shared_system_reports_missing_declared_inputs(shared, role):
    relative = _system(shared)["files"][role]
    (shared._root / relative).unlink()
    _assert_finding(_shared_findings(shared), f"missing {role} file {relative}")


def test_shared_system_reports_unreadable_declared_input(shared, monkeypatch):
    path = shared._root / _system(shared)["files"]["effect"]
    original = Path.read_text

    def read_text(current, *args, **kwargs):
        if current == path:
            raise PermissionError("fixture access denied")
        return original(current, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    _assert_finding(_shared_findings(shared), "cannot read effect file")


def test_shared_system_checks_unused_reads_and_foreign_writes(shared):
    _system(shared)["allowed_native_reads"].append("USA_unused_read")
    _replace_role(
        shared,
        "effect",
        "linux_system_monthly_driver = {",
        "linux_system_monthly_driver = {\n set_country_flag = USA_foreign_write\n every_country = { always = yes }",
    )
    findings = _shared_findings(shared)
    for message in (
        "declares unused native reads: USA_unused_read",
        "writes native-system state: USA_foreign_write",
        "may not use every_country",
    ):
        _assert_finding(findings, message)


def test_shared_system_requires_event_options_and_declared_location(shared):
    effects = shared._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    events = shared._load_events()
    event = events["linux_system_events.1"]
    event.options = []
    event.file = "events/foreign.txt"
    events["linux_system_events.6"] = copy.copy(event)
    findings = shared._validate_shared_systems(effects, events)
    for message in (
        "outside its declared event file",
        "requires at least one option",
        "has undeclared events: linux_system_events.6",
    ):
        _assert_finding(findings, message)


@pytest.mark.parametrize("version", [4, 5])
def test_shared_system_legacy_registry_requires_cleanup_and_dispatcher(shared, version):
    shared._manifest_payload["schema_version"] = version
    system = _system(shared)
    system["participant_array"] = "global.legacy_participants"
    system["dispatcher_host"] = "ABK"
    _replace_role(
        shared,
        "effect",
        "linux_system_monthly_driver = {",
        "linux_system_monthly_driver = {\n if = { limit = { original_tag = ABK } always = yes }",
    )
    findings = _shared_findings(shared)
    for message in (
        "registry must deduplicate",
        "must use ABK as its monthly dispatcher host",
        "may not own gameplay state",
        "and the participant entry",
    ):
        _assert_finding(findings, message)


@pytest.mark.parametrize(
    "problem", ["undeclared", "missing_file", "no_bom", "missing_key"]
)
def test_shared_system_requires_readable_complete_english_localisation(shared, problem):
    files = _system(shared)["files"]
    if problem == "undeclared":
        files["localisation"] = []
        expected = "requires declared English localisation files"
    elif problem == "missing_file":
        files["localisation"] = ["localisation/english/missing_l_english.yml"]
        expected = "missing localisation file"
    else:
        relative = files["localisation"][0]
        path = shared._root / relative
        if problem == "no_bom":
            path.write_bytes(path.read_bytes()[3:])
            expected = "must retain a UTF-8 BOM"
        else:
            _system(shared)["localisation_keys"].append("absent_key")
            expected = "missing localisation key absent_key"
    _assert_finding(_shared_findings(shared), expected)


def test_shared_system_limits_ibm_story_extension_but_keeps_save_anchor(shared):
    relative = _system(shared)["files"]["ibm_event"]
    _write(shared._root, relative, "country_event = { id = USA_ibm_events.90 }\n")
    assert not any(
        "beyond .50" in message for message, _, _ in _shared_findings(shared)
    )
    _write(shared._root, relative, "country_event = { id = USA_ibm_events.51 }\n")
    _assert_finding(
        _shared_findings(shared), "IBM story events may not extend beyond .50: [51]"
    )


@pytest.fixture
def reusable(tmp_path):
    _write(
        tmp_path,
        "common/decisions/program.txt",
        """program = {
	fire_only_once = no
	days_remove = 180
	complete_effect = { add_timed_idea = { idea = program_idea days = 180 } }
}
""",
    )
    _write(
        tmp_path,
        "localisation/english/program_l_english.yml",
        'l_english:\n program_desc: "Runs for 180 days."\n',
    )
    validator = Validator(str(tmp_path), no_color=True)
    validator._manifest_payload = {
        "schema_version": 5,
        "reusable_decision_lifecycles": [
            {
                "name": "Programs",
                "decision_file": "common/decisions/program.txt",
                "localisation_file": "localisation/english/program_l_english.yml",
                "forbidden_cooldown_markers": ["program_cooldown"],
                "programs": [
                    {
                        "decision": "program",
                        "kind": "timed_idea",
                        "active_days": 180,
                        "cooldown_mode": "active_duration",
                        "cooldown_days": 0,
                        "idea": "program_idea",
                        "cleanup_effect": "cleanup",
                        "cleanup_decision": True,
                        "localisation_keys": ["program_desc"],
                    }
                ],
            }
        ],
    }
    return validator


def _reusable_findings(validator, effects=None):
    if effects is None:
        effects = {
            "cleanup": [
                BlockDef(
                    "cleanup",
                    "effects.txt",
                    1,
                    "remove_ideas = { program_idea }\nremove_decision = program",
                )
            ]
        }
    return validator._validate_reusable_decision_lifecycles(effects)


def test_reusable_timed_program_releases_slot_at_expiration(reusable):
    assert _reusable_findings(reusable) == []


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("decision", "missing", "Missing reusable decision missing"),
        ("kind", "unknown", "unsupported lifecycle kind unknown"),
        ("active_days", None, "lifecycle durations must be integers"),
        ("active_days", 0, "temporary program must last 1 to 365 days"),
        ("cooldown_mode", "unknown", "unsupported cooldown mode unknown"),
        ("cooldown_days", 1, "zero post-program cooldown"),
        (
            "duration_source",
            "missing_source",
            "requires exactly one duration source missing_source",
        ),
        (
            "cleanup_effect",
            "missing_cleanup",
            "requires exactly one cleanup effect missing_cleanup",
        ),
        (
            "localisation_keys",
            ["missing_key"],
            "Missing lifecycle localisation key missing_key",
        ),
    ],
)
def test_reusable_lifecycle_rejects_invalid_program_contract(
    reusable, field, value, expected
):
    reusable._manifest_payload["reusable_decision_lifecycles"][0]["programs"][0][
        field
    ] = value
    _assert_finding(_reusable_findings(reusable), expected)


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        (None, "must be an object"),
        ({}, "is missing:"),
        (
            {"name": "Programs", "decision_file": "absent.txt", "programs": []},
            "is missing absent.txt",
        ),
    ],
)
def test_reusable_lifecycle_reports_invalid_system_entries(reusable, entry, expected):
    reusable._manifest_payload["reusable_decision_lifecycles"] = [entry]
    _assert_finding(_reusable_findings(reusable), expected)


@pytest.mark.parametrize("entries", [[], None, "bad"])
def test_reusable_lifecycle_requires_programs(reusable, entries):
    reusable._manifest_payload["reusable_decision_lifecycles"][0]["programs"] = entries
    _assert_finding(_reusable_findings(reusable), "programs must be a non-empty list")


@pytest.mark.parametrize(
    ("entry", "expected"),
    [(None, "programs[0] must be an object"), ({}, "programs[0] is missing:")],
)
def test_reusable_lifecycle_reports_incomplete_program_entries(
    reusable, entry, expected
):
    reusable._manifest_payload["reusable_decision_lifecycles"][0]["programs"] = [entry]
    _assert_finding(_reusable_findings(reusable), expected)


def test_reusable_lifecycle_detects_duplicate_declarations_and_undeclared_decisions(
    reusable,
):
    system = reusable._manifest_payload["reusable_decision_lifecycles"][0]
    system["programs"].append(copy.deepcopy(system["programs"][0]))
    path = reusable._root / system["decision_file"]
    _write(
        reusable._root,
        system["decision_file"],
        path.read_text("utf-8") + "\nextra = { complete_effect = { always = yes } }",
    )
    findings = _reusable_findings(reusable)
    _assert_finding(findings, "declared more than once")
    _assert_finding(findings, "undeclared: extra")


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (
            "fire_only_once = no",
            "fire_only_once = yes",
            "must declare fire_only_once = no",
        ),
        ("days_remove = 180", "days_remove = 30", "must remain active for 180 days"),
        (
            "days_remove = 180",
            "days_remove = 180\n\tremove_effect = { set_country_flag = program_cooldown }",
            "may not start post-program cooldown",
        ),
    ],
)
def test_reusable_lifecycle_checks_executable_cadence(
    reusable, before, after, expected
):
    path = reusable._root / "common/decisions/program.txt"
    _write(
        reusable._root,
        "common/decisions/program.txt",
        path.read_text("utf-8").replace(before, after),
    )
    _assert_finding(_reusable_findings(reusable), expected)


@pytest.mark.parametrize(
    "body", ["remove_decision = program", "remove_ideas = program_idea"]
)
def test_reusable_cleanup_must_release_both_idea_and_active_decision(reusable, body):
    effects = {"cleanup": [BlockDef("cleanup", "effects.txt", 1, body)]}
    expected = (
        "must remove program_idea"
        if "remove_ideas" not in body
        else "must remove active decision program"
    )
    _assert_finding(_reusable_findings(reusable, effects), expected)


@pytest.mark.parametrize("days", [0, 30, 180, 366])
def test_reusable_parallel_cooldown_matches_active_duration(reusable, days):
    program = reusable._manifest_payload["reusable_decision_lifecycles"][0]["programs"][
        0
    ]
    program.update(cooldown_mode="days_re_enable", cooldown_days=days)
    relative = "common/decisions/program.txt"
    _write(
        reusable._root,
        relative,
        (reusable._root / relative)
        .read_text("utf-8")
        .replace("days_remove = 180", f"days_re_enable = {days}"),
    )
    findings = _reusable_findings(reusable)
    if days == 180:
        assert findings == []
    else:
        _assert_finding(findings, "re-enable period must equal its active duration")
        if days in (0, 366):
            _assert_finding(findings, "re-enable period must last 1 to 365 days")


@pytest.mark.parametrize("days", [90, 730, "bad"])
def test_reusable_construction_project_distinguishes_timer_and_policy_cadence(
    reusable, days
):
    system = reusable._manifest_payload["reusable_decision_lifecycles"][0]
    system["programs"] = [
        {
            "decision": "program",
            "kind": "construction_project",
            "active_days": 0,
            "cooldown_mode": "days_re_enable",
            "cooldown_days": 90,
            "mission": "build",
            "project_days": days,
        }
    ]
    _write(
        reusable._root,
        system["decision_file"],
        "program = {\n fire_only_once = no\n days_re_enable = 90\n complete_effect = { activate_mission = build }\n}\nbuild = { days_mission_timeout = 90 }\n",
    )
    findings = _reusable_findings(reusable)
    if days == 90:
        assert findings == []
    else:
        _assert_finding(findings, "construction mission build must last")
        if days == 730:
            _assert_finding(findings, "construction timer over 365 days needs a reason")


@pytest.mark.parametrize(
    ("kind", "active", "expected"),
    [
        ("cadence_only", 1, "must use active_days = 0"),
        ("cadence_only", 0, "requires a timed idea"),
    ],
)
def test_reusable_non_timed_programs_cannot_claim_an_active_idea_slot(
    reusable, kind, active, expected
):
    reusable._manifest_payload["reusable_decision_lifecycles"][0]["programs"][0].update(
        kind=kind, active_days=active
    )
    _assert_finding(_reusable_findings(reusable), expected)


@pytest.mark.parametrize(
    "text",
    [
        None,
        'l_english:\n program_desc: "Runs for 90 days."',
        'l_english:\n program_desc: "Runs for 180 days then 730 days."',
    ],
)
def test_reusable_lifecycle_localisation_matches_duration(reusable, text):
    relative = "localisation/english/program_l_english.yml"
    if text is None:
        (reusable._root / relative).unlink()
        expected = "is missing localisation/english/program_l_english.yml"
    else:
        _write(reusable._root, relative, text)
        expected = (
            "still claims a 730-day lifecycle"
            if "730" in text
            else "must state 180 days"
        )
    _assert_finding(_reusable_findings(reusable), expected)


@pytest.mark.parametrize(
    ("changes", "lockout", "expected"),
    [
        ({"program_class": "unknown"}, "concurrent", "must declare program_class"),
        ({"days": 730}, "concurrent", "must not impose a 730-day active program"),
        ({"cooldown_days": 200}, "sequential", "must not outlast its 180-day program"),
        (
            {"days": 365, "program_class": "major_commitment", "cooldown_days": 1},
            "sequential",
            "locks the player out for 366 days",
        ),
        (
            {"cleanup_owner": ""},
            "concurrent",
            "must declare the effect that owns its cleanup",
        ),
    ],
)
def test_program_duration_class_limits(changes, lockout, expected):
    program = {
        "program_class": "operational",
        "days": 180,
        "cooldown_days": 0,
        "cleanup_owner": "cleanup",
    }
    program.update(changes)
    _assert_finding(
        _program_lifecycle_findings(
            "program", program, "days", lockout, "contract.json"
        ),
        expected,
    )


@pytest.fixture
def economic(tmp_path):
    _build_fixture(tmp_path)
    _enable_economic_layer_fixture(tmp_path)
    validator = Validator(str(tmp_path), no_color=True)
    validator._load_manifest()
    return validator


def _economic_findings(validator):
    effects = validator._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    return validator._validate_economic_layers(effects, validator._load_manifest())


def _save_economic(validator):
    _write(
        validator._root,
        "tools/corporate_history_contract.json",
        json.dumps(validator._manifest_payload),
    )


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("variables", {}, "requires declared bounded variables"),
        (
            "variables",
            {"USA_oem_option_value": {}},
            "invalid bounds for USA_oem_option_value",
        ),
        ("cdf", None, "CDF contract must be an object"),
        (
            "cdf",
            {"knots": [1, 0], "values": [0.5, 0.84134]},
            "paired, monotonic, and bounded",
        ),
        ("cdf", {"knots": [], "values": []}, "paired, monotonic, and bounded"),
        ("cdf", {"knots": "invalid", "values": []}, "paired, monotonic, and bounded"),
        (
            "cdf",
            {"knots": [0, 1], "values": [0.123456, 0.84134]},
            "missing contracted value 0.123456",
        ),
        ("modifier_families", [], "requires modifier families"),
        (
            "modifier_families",
            [{"name": "broken", "members": ["a"], "thresholds": [1]}],
            "invalid members or thresholds",
        ),
        (
            "modifier_families",
            [
                {
                    "name": "broken",
                    "members": ["a"],
                    "thresholds": [],
                    "score": "undeclared",
                }
            ],
            "reads undeclared score undeclared",
        ),
        ("policy_programs", [], "requires exactly four policy programs"),
        ("updater", "absent", "authoritative updater absent"),
        ("bridge", "absent", "bridge absent must have exactly one definition"),
    ],
)
def test_economic_layer_rejects_inconsistent_declarations(
    economic, field, value, expected
):
    economic._manifest_payload["economic_layers"][0][field] = value
    _save_economic(economic)
    _assert_finding(_economic_findings(economic), expected)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ([None], "must be an object"),
        ([{}], "missing required fields"),
        ([], "non-empty economic_layers list"),
    ],
)
def test_economic_layer_requires_complete_objects(economic, payload, expected):
    economic._manifest_payload["economic_layers"] = payload
    _save_economic(economic)
    _assert_finding(_economic_findings(economic), expected)


@pytest.mark.parametrize(
    "field",
    [
        "effect_file",
        "dynamic_modifier_file",
        "decision_file",
        "idea_file",
        "scripted_localisation_file",
        "localisation_file",
    ],
)
def test_economic_layer_missing_input_has_a_diagnostic(economic, field):
    relative = economic._manifest_payload["economic_layers"][0][field]
    (economic._root / relative).unlink()
    _assert_finding(_economic_findings(economic), f"is missing {field} {relative}")


@pytest.mark.parametrize(
    ("field", "before", "after", "expected"),
    [
        (
            "effect_file",
            "corporate_history_enabled = yes",
            "always = yes",
            "missing required gate or cleanup symbol corporate_history_enabled",
        ),
        (
            "effect_file",
            "clear_variable = USA_oem_option_value",
            "clear_variable = other",
            "Off cleanup must clear USA_oem_option_value",
        ),
        (
            "effect_file",
            "remove_dynamic_modifier =",
            "ignored_modifier =",
            "never clears dynamic modifier",
        ),
        (
            "decision_file",
            "USA_oem_policy_1 = {",
            "missing_policy = {",
            "Missing policy decision USA_oem_policy_1",
        ),
        (
            "decision_file",
            "fire_only_once = no",
            "fire_only_once = yes",
            "must remain reusable",
        ),
        (
            "decision_file",
            "available = {",
            "allowed = {",
            "must block while USA_oem_program_1 is active",
        ),
    ],
)
def test_economic_layer_script_drift_has_a_diagnostic(
    economic, field, before, after, expected
):
    relative = economic._manifest_payload["economic_layers"][0][field]
    text = (economic._root / relative).read_text("utf-8")
    assert before in text
    _write(economic._root, relative, text.replace(before, after))
    _assert_finding(_economic_findings(economic), expected)


def test_economic_layer_requires_parseable_policy_body(economic):
    relative = economic._manifest_payload["economic_layers"][0]["decision_file"]
    _write(economic._root, relative, "USA_oem_policy_1 = {\n")
    _assert_finding(
        _economic_findings(economic), "Could not parse policy decision USA_oem_policy_1"
    )


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("cleanup_owner", "other", "as its cleanup owner"),
        ("refresh_policy", "stack", "block_while_active refresh policy"),
    ],
)
def test_economic_policy_requires_cleanup_owner_and_no_stacking(
    economic, field, value, expected
):
    economic._manifest_payload["economic_layers"][0]["policy_programs"][0][
        field
    ] = value
    _save_economic(economic)
    _assert_finding(_economic_findings(economic), expected)


def test_economic_updater_cannot_move_to_an_undeclared_file(economic):
    effects = economic._load_top_level_blocks(["common/scripted_effects/**/*.txt"])
    updater = effects["USA_oem_update_real_options_economy"][0]
    effects[updater.name] = [
        BlockDef(updater.name, "foreign.txt", updater.line, updater.body)
    ]
    _assert_finding(
        economic._validate_economic_layers(effects, economic._load_manifest()),
        "must be defined in common/scripted_effects/USA_oem_real_options_effects.txt",
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("{", "Failed to load"),
        ("{}", "non-empty chains list"),
        ('{"chains":[null]}', "chains[0] must be an object"),
        ('{"schema_version":2,"chains":[{}]}', "missing required fields"),
    ],
)
def test_manifest_rejects_unparseable_or_incomplete_chains(tmp_path, text, expected):
    _write(tmp_path, "tools/corporate_history_contract.json", text)
    validator = Validator(str(tmp_path), no_color=True)
    assert validator._load_manifest() == []
    assert any(expected in issue.message for issue in validator._issues)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("tier", "bad", "chains[0] is invalid"),
        ("outcomes_only_strategy", "events", "invalid outcomes_only_strategy"),
        (
            "requires_current_year_scheduler",
            False,
            "disagrees with full_start_strategies",
        ),
    ],
)
def test_manifest_reports_inconsistent_chain_strategy(tmp_path, field, value, expected):
    payload = _manifest()
    payload["chains"][0][field] = value
    _write(tmp_path, "tools/corporate_history_contract.json", json.dumps(payload))
    validator = Validator(str(tmp_path), no_color=True)
    validator._load_manifest()
    assert any(expected in issue.message for issue in validator._issues)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("namespaces", "bad", "list fields must contain only non-empty strings"),
        ("namespaces", [""], "list fields must contain only non-empty strings"),
        ("id", "", "must be non-empty strings"),
        ("owner_tags", ["USA", "USA"], "contains duplicate values"),
    ],
)
def test_independent_subsystem_rejects_ambiguous_identity(
    tmp_path, field, value, expected
):
    subsystem = {
        "id": "test",
        "kind": "independent_chronology",
        "mode_policy": "full_only",
        "namespaces": [],
        "event_ids": [],
        "owner_tags": ["USA"],
        "reconstruction_effects": [],
        "scheduler_entrypoints": [],
        "effect_roots": ["USA_test"],
    }
    subsystem[field] = value
    validator = Validator(str(tmp_path), no_color=True)
    assert (
        validator._load_independent_subsystems(
            {"independent_subsystems": [subsystem]}, 6
        )
        == ()
    )
    assert any(expected in issue.message for issue in validator._issues)


@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        ([], "requires a non-empty"),
        ([None], "must be an object"),
        ([{}], "missing required fields"),
    ],
)
def test_independent_subsystems_require_structured_entries(tmp_path, entries, expected):
    validator = Validator(str(tmp_path), no_color=True)
    assert (
        validator._load_independent_subsystems({"independent_subsystems": entries}, 6)
        == ()
    )
    assert any(expected in issue.message for issue in validator._issues)
