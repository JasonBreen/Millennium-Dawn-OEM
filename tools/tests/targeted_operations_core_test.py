import json
from collections import Counter
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
from great_ai_race_state_model_test import (
    _named_block,
    _parse_race_script,
)
from targeted_operations_helpers_test import TargetedScript

ROOT = Path(__file__).resolve().parents[2]


class ScriptArray(list):
    def get(self, index, default=0):
        return self[index] if 0 <= index < len(self) else default


class TargetScript(TargetedScript):
    """Execute TOP source while recording separately owned engine and legacy effects."""

    def __init__(self):
        self.effects = {}
        for filename in (
            "00_targeted_operations_effects.txt",
            "01_targeted_operations_world.txt",
            "01_targeted_operations_registry.txt",
            "04_targeted_operations_cases.txt",
            "06_targeted_operations_redesign.txt",
            "07_targeted_operations_organization_cases.txt",
            "08_targeted_operations_resolution.txt",
            "09_targeted_operations_depth.txt",
        ):
            self.effects.update(
                _parse_race_script(
                    (ROOT / "common/scripted_effects" / filename).read_text(
                        encoding="utf-8"
                    )
                )
            )
        succession = (
            ROOT / "common/scripted_effects/01_targeted_operations_successors.txt"
        ).read_text(encoding="utf-8")
        self.effects.update(
            _parse_race_script(
                _named_block(succession, "TOP_select_authored_successor")
            )
        )
        self.triggers = _parse_race_script(
            (
                ROOT / "common/scripted_triggers/01_targeted_operations_triggers.txt"
            ).read_text(encoding="utf-8")
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/04_targeted_operations_cases.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/03_targeted_operations_political_roster.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/07_targeted_operations_redesign.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT / "common/scripted_triggers/05_targeted_operations_runtime.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.triggers.update(
            _parse_race_script(
                (
                    ROOT
                    / "common/scripted_triggers/05_targeted_operations_arg_wrappers.txt"
                ).read_text(encoding="utf-8")
            )
        )
        self.countries, self.globals, self.temps = {}, {}, {}
        self.scope_stack, self.events = [], []
        self.global_flags, self.external = {}, Counter()
        self.ineligible_roles = set()
        self.legacy_first_removals = []
        self.random_draws = 0
        self.today = date(2005, 1, 1)
        self.mode = "TOP_limited_sandbox_option"
        self.stubs = {
            "TOP_initialize_global",
            "TOP_refresh_view",
            "TOP_update_iraq_progress",
            "TOP_apply_legacy_outcome",
            "TOP_apply_legacy_release",
            "TOP_retire_registered_character",
            "TOP_apply_legacy_assessment",
            "TOP_apply_office_successor",
            "TOP_exploit_capture",
            "TOP_apply_exposure",
            "TOP_start_exposed_kill_crisis",
            "TOP_review_tick",
            "TOP_cancel_review",
            "TOP_begin_review",
            "TOP_get_defensive_modifiers",
            "TOP_security_country_tick",
            "TOP_build_view",
            "TOP_prepare_authored_service",
            "TOP_refresh_visit_dossiers",
            "TOP_process_visits",
            "TOP_process_crisis",
            "TOP_initialize_doctrine",
            "TOP_seed_public_subjects",
            "international_systems_force_update",
        }
        manifest = json.loads(
            (ROOT / "tools/data/targeted_operations.json").read_text(encoding="utf-8")
        )
        tags = ["---", "USA", "YEM", "PER", "TAL", "AFG", "IRQ", "ISI", "PAK"]
        for group in manifest["groups"]:
            for tag in (
                [group["host"]]
                + group.get("movement_hosts", [])
                + group.get("regional_hosts", [])
            ):
                if tag not in tags:
                    tags.append(tag)
        for ident, tag in enumerate(tags):
            self.country(ident, tag=tag)
            self.countries[ident].update(states=[], exists=ident != 0)
        self.countries[1]["techs"].update(
            {"special_forces_tech_1", "decryption1", "decryption2"}
        )
        self.countries[1]["vars"]["political_power"] = 500
        self.state(100, 1)
        self.state(101, 2)
        self.state(102, 3)
        self.run("TOP_setup_registry", 1)
        self.run("TOP_initialize_redesign_global", 1)
        self.globals.update(
            TOP_rule_enabled=1,
            TOP_rule_mode=1,
            TOP_active_targets=ScriptArray(),
            active_terror_orgs=ScriptArray([0, 10]),
            active_terror_org_threat_lvl=ScriptArray([50, 40]),
        )
        for ident in range(1, len(tags)):
            self.run("TOP_country_initialize", ident)

    def state(self, ident, controller):
        self.country(ident, tag=f"state_{ident}")
        self.countries[ident].update(controller=controller, states=[])
        self.countries[ident]["vars"]["infrastructure"] = 3
        self.countries[ident]["vars"]["arms_factory"] = 2
        self.countries[ident]["vars"]["industrial_complex"] = 2
        self.countries[ident]["resources"] = ["oil"]
        self.countries[controller]["states"].append(ident)

    def tag(self, token):
        return next(
            (ident for ident, data in self.countries.items() if data["tag"] == token),
            None,
        )

    def _scope(self, name, identifier):
        if name.startswith("PREV."):
            return self._scope(name[5:], self.scope_stack[-1])
        if "^" in name:
            array, index = name.split("^", 1)
            scope, key = super()._scope(array, identifier)
            return scope.setdefault(key, ScriptArray()), int(
                self.value(index, identifier)
            )
        return super()._scope(name, identifier)

    def value(self, name, identifier):
        if isinstance(name, str):
            if name in {"THIS", "THIS.id", "ROOT"}:
                return identifier
            if name == "PREV":
                return self.scope_stack[-1]
            if name == "controller":
                return self.countries[identifier].get("controller", 0)
            if name.startswith("var:"):
                return self.value(name[4:], identifier)
            if name.endswith("^num"):
                return len(self.value(name[:-4], identifier) or [])
            country = self.tag(name)
            if country is not None:
                return country
        return super().value(name, identifier)

    def scoped(self, operand, identifier, target, condition=False):
        self.scope_stack.append(identifier)
        try:
            if condition:
                return self.condition(operand, target)
            self.execute(operand, target)
        finally:
            self.scope_stack.pop()

    def condition_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key.startswith("var:") or key == "controller" or self.tag(key) is not None:
            result = self.scoped(
                operand, identifier, self.value(key, identifier), condition=True
            )
        elif key == "raid_show_target_intervention_check":
            result = operand == "yes"
        elif key == "TOP_authored_role_eligible":
            # No longer parameterised: the caller sets TOP_role_target,
            # because the engine cannot substitute $PARAM$ for a trigger.
            result = (
                self.value("TOP_role_target", identifier) not in self.ineligible_roles
            )
        elif key == "TOP_authored_civilian_mandate_valid":
            result = operand == "no"
        elif key == "TOP_review_pending":
            result = operand == "no"
        elif key == "TOP_target_protection_at_war":
            result = operand == "no"
        elif key in {
            "TOP_case_visit_review_valid",
            "TOP_case_visit_execution_valid",
            "TOP_case_visit_approval_fits",
        }:
            result = operand != "no"
        elif key == "is_in_array":
            name, _, member = operand[0]
            result = self.value(member, identifier) in (
                self.value(name, identifier) or []
            )
        elif key == "is_controlled_by":
            result = self.value("controller", identifier) == self.value(
                operand, identifier
            )
        elif key in {
            "num_of_controlled_states",
            "has_political_power",
            "arms_factory",
            "industrial_complex",
            "infrastructure",
        }:
            value = (
                len(self.countries[identifier]["states"])
                if key == "num_of_controlled_states"
                else self.countries[identifier]["vars"].get(
                    "political_power" if key == "has_political_power" else key, 0
                )
            )
            result = self.comparisons[comparison](
                value, self.value(operand, identifier)
            )
        elif key in {"has_war_with", "is_in_faction_with"}:
            result = self.value(operand, identifier) in self.countries[identifier].get(
                key, set()
            )
        elif key == "has_opinion":
            result = False
        elif key == "has_civil_war":
            result = self.countries[identifier].get("civil_war", False) == (
                operand == "yes"
            )
        elif key == "state_has_any_resource":
            result = bool(self.countries[identifier].get("resources", [])) == (
                operand == "yes"
            )
        else:
            result = super().condition_statement(statement, identifier)
        return result

    def run(self, name, identifier):
        if name in self.stubs:
            self.external[name, identifier] += 1
            if name == "TOP_apply_legacy_outcome":
                self.legacy_first_removals.append(
                    self.value("TOP_first_removal", identifier)
                )
        else:
            self.execute(self.effects[name], identifier)

    def call(self, name, identifier=1, **arguments):
        # Scripted effects no longer take parameters: the engine does not
        # substitute $PARAM$ for an effect any more than for a trigger, so each
        # reads a TOP_arg_* temp variable the caller sets first.
        for key, value in arguments.items():
            self.temps[f"TOP_arg_{key.lower()}"] = value
        self.execute(self.effects[name], identifier)

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key in self.stubs:
            self.run(key, identifier)
        elif key == "controller" or self.tag(key) is not None:
            self.scoped(operand, identifier, self.value(key, identifier))
        elif key in {"random_controlled_state", "capital_scope"}:
            states = self.countries[identifier]["states"]
            if states:
                self.scoped(operand, identifier, states[0])
        elif key == "resize_array":
            name, _, size = operand[0]
            scope, name = self._scope(name, identifier)
            array = scope.setdefault(name, ScriptArray())
            size = int(self.value(size, identifier))
            array[:] = (array + [0] * size)[:size]
        elif key in {"for_each_loop", "for_loop_effect"}:
            data = {name: value for name, _, value in operand}
            if key == "for_each_loop":
                entries = enumerate(list(self.value(data["array"], identifier) or []))
                metadata = {"array", "index", "value"}
            else:
                start = int(self.value(data.get("start", 0), identifier))
                end = int(self.value(data["end"], identifier))
                if data.get("compare") == "less_than_or_equals":
                    end += 1
                entries = enumerate(range(start, end, int(data.get("add", 1))))
                metadata = {"start", "end", "compare", "add", "value"}
            for index, value in entries:
                self.temps[data.get("value", "v")] = value
                if "index" in data:
                    self.temps[data["index"]] = index
                self.execute(
                    [entry for entry in operand if entry[0] not in metadata], identifier
                )
        elif key == "remove_from_array":
            data = {name: value for name, _, value in operand}
            if "array" in data:
                array = self.value(data["array"], identifier)
                array.pop(int(self.value(data["index"], identifier)))
            else:
                name, _, value = operand[0]
                array = self.value(name, identifier) or []
                member = self.value(value, identifier)
                if member in array:
                    array.remove(member)
        elif key == "modulo_variable":
            name, _, value = operand[0]
            scope, name = self._scope(name, identifier)
            scope[name] %= self.value(value, identifier)
        elif key == "random":
            data = {name: value for name, _, value in operand}
            self.random_draws += 1
            if self.value(data["chance"], identifier) > 0:
                self.execute(
                    [entry for entry in operand if entry[0] != "chance"], identifier
                )
        elif key == "randomize_temp_variable":
            data = {name: value for name, _, value in operand}
            self.random_draws += 1
            self.temps[data["var"]] = self.value(data["min"], identifier)
        elif key == "add_political_power":
            variables = self.countries[identifier]["vars"]
            variables["political_power"] = variables.get(
                "political_power", 0
            ) + self.value(operand, identifier)
        elif key == "add_stability":
            variables = self.countries[identifier]["vars"]
            variables["stability"] = variables.get("stability", 0) + self.value(
                operand, identifier
            )
        elif key == "add_opinion_modifier":
            self.external[key, identifier] += 1
        elif key == "damage_building":
            self.external[key, identifier] += 1
        elif key == "add_dynamic_modifier":
            self.external[key, identifier] += 1
        else:
            super().execute_statement(statement, identifier)

    def target(self, ident=11, status=1, *, host=2, state=101, actor=1):
        for field, value in (("status", status), ("host", host), ("state", state)):
            self.globals[f"TOP_{field}"][ident] = value
        if status == 1 and ident not in self.globals["TOP_active_targets"]:
            self.globals["TOP_active_targets"].append(ident)
        variables = self.countries[actor]["vars"]
        variables["TOP_selected"] = ident
        variables["TOP_selected_kind"] = 1
        dossiers = variables.setdefault("TOP_dossiers", ScriptArray())
        if ident not in dossiers:
            dossiers.append(ident)
        for field, value in (
            ("known", 1),
            ("confidence", 85),
            ("identity_confidence", 85),
            ("location_confidence", 85),
            ("pattern_confidence", 85),
            ("package_state", 1),
            ("lead_state", state),
            ("lead_host", host),
            ("assessment", status),
        ):
            variables[f"TOP_{field}"][ident] = value
        return variables

    def authorize(self, target=11, method=1, *, host=2, state=101, actor=1, begin=True):
        variables = self.target(target, host=host, state=state, actor=actor)
        for field, value in (
            ("host", host),
            ("state", state),
            ("method", method),
            ("until", 91),
            ("phase", 2),
            ("due", 0),
            ("sequence", target),
            ("facility", 2),
            ("assurance", 85),
            ("rigor", 1),
            ("identity", 85),
            ("location", 85),
            ("pattern", 85),
            ("lead_age", 0),
            ("access", method),
            ("host_posture", 4 if method == 5 else 1),
            ("doctrine", 2),
            ("capability", 85),
            ("protection", host),
        ):
            variables[f"TOP_case_{field}"][target] = value
        active = variables.setdefault("TOP_active_cases", ScriptArray())
        if target not in active:
            active.append(target)
        self.call("TOP_load_case", actor, TARGET=target)
        self.temps.update(
            TOP_target=target,
            TOP_method=method,
            TOP_operation_state=state,
            target_state=state,
            TOP_facility_kind=2,
        )
        if begin:
            self.call("TOP_begin_person_operation", actor, TARGET=target)
        return variables

    def authorize_organization(
        self, group=2, objective=1, *, host=3, state=102, actor=1, begin=True
    ):
        variables = self.countries[actor]["vars"]
        self.globals["TOP_group_created"][group] = 1
        self.globals["TOP_group_window"][group] = 1
        self.globals["TOP_group_destroyed"][group] = 0
        self.globals["TOP_group_class"][group] = 1
        self.globals["TOP_group_host"][group] = host
        self.globals["TOP_group_state"][group] = state
        variables["TOP_selected_kind"] = 2
        variables["TOP_selected_organization"] = group
        if group not in variables["TOP_organization_dossiers"]:
            variables["TOP_organization_dossiers"].append(group)
        for field, value in (
            ("known", 1),
            ("verification", 85),
            ("location", 85),
            ("activity", 85),
            ("lead_age", 0),
            ("lead_state", state),
            ("lead_host", host),
            ("package_state", 1),
        ):
            variables[f"TOP_org_{field}"][group] = value
        for field, value in (
            ("host", host),
            ("state", state),
            ("until", 91),
            ("phase", 2),
            ("due", 0),
            ("sequence", group),
            ("objective", objective),
            ("verification", 85),
            ("location", 85),
            ("activity", 85),
            ("lead_age", 0),
            ("access", 3),
            ("host_posture", 1),
            ("doctrine", 2),
            ("capability", 85),
        ):
            variables[f"TOP_org_case_{field}"][group] = value
        if group not in variables["TOP_active_organization_cases"]:
            variables["TOP_active_organization_cases"].append(group)
        if begin:
            self.call("TOP_begin_organization_operation", actor, GROUP=group)
        self.temps["TOP_group_target"] = group
        return variables

    def persisted_clone(self):
        restored = TargetScript()
        restored.countries = deepcopy(self.countries)
        restored.globals = deepcopy(self.globals)
        restored.global_flags = deepcopy(self.global_flags)
        restored.ineligible_roles = set(self.ineligible_roles)
        restored.today, restored.mode = self.today, self.mode
        return restored


def case_snapshot(script, target, actor=1):
    variables = script.countries[actor]["vars"]
    return {
        name: value[target]
        for name, value in variables.items()
        if name.startswith("TOP_case_") and isinstance(value, list)
    }


@pytest.mark.parametrize("initial", [0, 1, 2, 3, 4])
def test_import_enrolls_only_active_people_once_and_consumes_location(initial):
    script = TargetScript()
    script.globals["TOP_status"][11] = initial
    script.temps["TOP_import_state"] = 101
    script.call("TOP_import_target_location", 2, TARGET=11)
    script.call("TOP_import_target_location", 2, TARGET=11)
    assert script.globals["TOP_active_targets"].count(11) == int(initial < 2)
    assert script.globals["TOP_status"][11] == (1 if initial < 2 else initial)
    assert script.temps["TOP_import_state"] == 0


def test_capture_release_recapture_does_not_repeat_lifetime_rewards():
    script = TargetScript()
    variables = script.target()
    script.call("TOP_capture_target", TARGET=11)
    rewarded_pp = variables["political_power"]
    threat = list(script.globals["active_terror_org_threat_lvl"])
    script.run("TOP_release_selected", 1)
    script.call("TOP_capture_target", TARGET=11)
    assert script.globals["TOP_status"][11] == 2
    assert script.globals["TOP_removals"][11] == 1
    assert variables["political_power"] == rewarded_pp
    assert script.globals["active_terror_org_threat_lvl"] == threat
    assert script.globals["TOP_exploited"][11] == 0
    assert script.globals["TOP_exploitation_until"][11] == 14
    assert script.external["TOP_exploit_capture", 1] == 0
    assert script.legacy_first_removals == [1, 0]


def test_transferred_prisoner_is_known_and_manageable_by_recipient():
    script = TargetScript()
    script.target(status=2)
    script.globals["TOP_custodian"][11] = 1
    script.run("TOP_transfer_selected", 1)
    recipient = script.countries[2]["vars"]
    assert script.globals["TOP_custodian"][11] == 2
    assert recipient["TOP_known"][11] == 1
    assert recipient["TOP_assessment"][11] == 2
    assert 11 in recipient["TOP_dossiers"]
    recipient["TOP_selected"] = 11
    assert script.condition(script.triggers["TOP_custody_owned"], 2)


def test_delayed_assessment_retains_original_method_state_and_uncertainty():
    script = TargetScript()
    variables = script.authorize()
    script.temps["TOP_tier"] = 2
    script.run("TOP_complete_operation", 1)
    assert variables["TOP_archive_result"][0] == 5
    assert variables["TOP_assessment"][11] == 5
    script.authorize(12, method=4, host=3, state=102)
    variables["TOP_case_due"][12] = 100
    script.globals["TOP_state"][11] = 102
    script.globals["TOP_clock"] = 15
    script.run("TOP_process_timers", 1)
    assert variables["TOP_assessment"][11] == 3
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_result"][0] == 3
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_archive_method"][0] == 1
    assert variables["TOP_archive_state"][0] == 101


def test_legacy_capture_cannot_borrow_an_unrelated_mandate():
    script = TargetScript()
    variables = script.authorize(target=12, method=4)
    script.target(11)
    script.call("TOP_capture_target", TARGET=11)
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_archive_method"][0] == 0
    assert variables["TOP_archive_state"][0] == 101


@pytest.mark.parametrize("objective", (1, 2, 3))
def test_facility_sabotage_damages_the_map_without_removing_a_person(objective):
    script = TargetScript()
    variables = script.authorize_organization(objective=objective, host=2, state=101)
    original_person_status = list(script.globals["TOP_status"])
    script.run("TOP_resolve_organization_operation", 1)
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_subject_kind"][0] == 2
    assert variables["TOP_archive_subject_id"][0] == 2
    assert variables["TOP_archive_objective"][0] == objective
    assert variables["TOP_archive_result"][0] == 11
    assert script.external["damage_building", 101] == 1
    assert script.globals["TOP_group_disruption_type"][2] == objective
    assert script.globals["TOP_group_disruption_until"][2] == 90
    assert script.globals["TOP_status"] == original_person_status


def test_partner_operation_revalidates_cooperative_posture_before_execution():
    script = TargetScript()
    variables = script.authorize(method=5, begin=False)
    variables["TOP_case_host_posture"][11] = 5
    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 2
    assert script.globals["TOP_attempts"][11] == 0
    assert variables["TOP_archive_cursor"] == 0
    assert variables["TOP_operation_subject_kind"] == 0

    variables["TOP_case_host_posture"][11] = 4
    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_operation_subject_kind"] == 1


@pytest.mark.parametrize(
    "trigger", ["TOP_native_authorized", "TOP_mission_binding_valid"]
)
def test_changed_state_controller_invalidates_authorization(trigger):
    script = TargetScript()
    script.authorize()
    # These triggers no longer take parameters; they read temp variables.
    script.temps.update({"TOP_arg_target": 11, "TOP_arg_method": 1})
    statements = script.triggers[trigger]
    assert script.condition(statements, 1)
    script.countries[101]["controller"] = 3
    assert not script.condition(statements, 1)


def test_organization_execution_revalidates_the_recorded_state_controller():
    script = TargetScript()
    variables = script.authorize_organization(
        objective=1, host=2, state=101, begin=False
    )
    script.temps["TOP_arg_group"] = 2
    statements = script.triggers["TOP_can_begin_organization_operation"]
    assert script.condition(statements, 1)
    script.countries[101]["controller"] = 3
    assert not script.condition(statements, 1)
    script.call("TOP_begin_organization_operation", GROUP=2)
    assert variables["TOP_org_case_phase"][2] == 2


def test_ai_cannot_designate_collect_or_begin_a_person_operation():
    script = TargetScript()
    variables = script.target()
    script.countries[1]["ai"] = True
    variables["TOP_package_state"][11] = 0
    power = variables["political_power"]
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][11] == 0
    assert variables["political_power"] == power

    variables["TOP_package_state"][11] = 1
    script.run("TOP_collect_selected", 1)
    assert variables["TOP_collecting_subjects"] == []

    script.authorize(begin=False)
    script.call("TOP_begin_person_operation", TARGET=11)
    assert variables["TOP_case_phase"][11] == 2
    assert variables["TOP_operation_subject_kind"] == 0


def test_ai_cannot_begin_an_organization_operation():
    script = TargetScript()
    variables = script.authorize_organization(begin=False)
    script.countries[1]["ai"] = True
    script.call("TOP_begin_organization_operation", GROUP=2)
    assert variables["TOP_org_case_phase"][2] == 2
    assert variables["TOP_operation_subject_kind"] == 0


def test_generated_native_raids_have_no_offensive_ai_weight():
    raids = (ROOT / "common/raids/targeted_operations_raids.txt").read_text(
        encoding="utf-8"
    )
    assert raids.count("ai_will_do = {") > 0
    assert raids.count("ai_will_do = { base = 0 }") == raids.count("ai_will_do = {")
    assert "TOP_ai_choose_operation" not in "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in (ROOT / "common/scripted_effects").glob("*targeted_operations*.txt")
    )


@pytest.mark.parametrize("group,target,host", [(1, 7, 5), (3, 36, 7)])
def test_later_targets_can_activate_after_original_host_loses_territory(
    group, target, host
):
    script = TargetScript()
    script.state(110, host)
    script.globals["TOP_window"][target] = 1
    script.globals["TOP_group_window"][group] = 1
    script.run(f"TOP_activate_group_{group}", 1)
    assert script.globals["TOP_status"][target] == 1
    assert script.globals["TOP_host"][target] == host
    assert script.globals["TOP_state"][target] == 110
    assert script.globals["TOP_active_targets"].count(target) == 1


def test_exhausted_succession_preserves_group_and_cannot_redirect_backlash():
    script = TargetScript()
    script.target(12, status=3)
    script.globals["TOP_office"][12] = 1
    for index in range(65, 129):
        script.globals["TOP_generated_used"][index] = 1
        script.globals["TOP_status"][index] = 3
    script.temps["TOP_target"] = 12
    script.run("TOP_choose_successor", 1)
    assert script.globals["TOP_group_leader"][2] == 0
    assert script.globals["TOP_active_targets"] == []
    assert script.globals["active_terror_orgs"] == [0, 10]
    script.globals["TOP_backlash"][2] = 3
    script.run("TOP_global_monthly", 1)
    assert script.globals["active_terror_org_threat_lvl"] == [50, 41]
    assert script.globals["TOP_backlash"][2] == 2
    assert script.globals["TOP_backlash"][0] == 0


@pytest.mark.parametrize("first_outcome", ["TOP_capture_target", "TOP_kill_target"])
def test_competing_countries_cannot_resolve_or_reward_the_same_person_twice(
    first_outcome,
):
    script = TargetScript()
    script.target()
    script.countries[2]["vars"]["political_power"] = 200
    script.call(first_outcome, TARGET=11)
    first_status = script.globals["TOP_status"][11]
    script.call("TOP_capture_target", 2, TARGET=11)
    script.call("TOP_kill_target", 2, TARGET=11)
    assert script.globals["TOP_status"][11] == first_status
    assert script.globals["TOP_removals"][11] == 1
    assert script.countries[2]["vars"]["political_power"] == 200
    assert script.countries[2]["vars"]["TOP_archive_cursor"] == 0
    assert script.external["TOP_exploit_capture", 2] == 0


@pytest.mark.parametrize("writes", [128, 129, 257])
def test_archive_rollover_retains_exactly_the_most_recent_128_results(writes):
    script = TargetScript()
    variables = script.authorize()
    script.temps["TOP_result"] = 9
    for day in range(writes):
        script.globals["TOP_clock"] = day
        script.run("TOP_archive_result", 1)
    assert variables["TOP_archive_cursor"] == writes % 128
    assert len(variables["TOP_archive_rows"]) == 128
    assert len(set(variables["TOP_archive_rows"])) == 128
    assert set(variables["TOP_archive_day"]) == set(range(writes - 128, writes))
    for field in ("target", "result", "method", "day", "state"):
        assert len(variables[f"TOP_archive_{field}"]) == 128


def test_last_registry_slot_has_all_arrays_and_can_be_resolved():
    script = TargetScript()
    capacity = len(script.globals["TOP_status"])
    target = capacity - 1
    variables = script.target(target)
    script.call("TOP_capture_target", TARGET=target)
    script.call("TOP_kill_target", TARGET=target)
    assert script.globals["TOP_status"][target] == 3
    assert script.globals["TOP_removals"][target] == 1
    assert variables["TOP_capture_exploited"][target] == 0
    assert script.globals["TOP_exploited"][target] == 0
    for name, array in script.globals.items():
        if (
            name.startswith("TOP_")
            and isinstance(array, list)
            and name
            not in {
                "TOP_active_targets",
                "TOP_pending_actors",
                "TOP_backlash",
                "TOP_detained_targets",
                "TOP_detained_next",
            }
            and not name.startswith("TOP_group_")
        ):
            assert len(array) == capacity, name
    for name, array in variables.items():
        if (
            name.startswith("TOP_")
            and isinstance(array, list)
            and name
            not in {
                "TOP_dossiers",
                "TOP_pending_assessments",
                "TOP_active_cases",
                "TOP_cases_to_close",
                "TOP_retired_native_bindings",
                "TOP_vip_assignments",
                "TOP_collecting_subjects",
                "TOP_organization_dossiers",
                "TOP_active_organization_cases",
                "TOP_attribution_pending_people",
                "TOP_attribution_pending_organizations",
            }
            and not name.startswith("TOP_archive_")
            and not name.startswith("TOP_org_")
        ):
            assert len(array) == capacity, name


@pytest.mark.parametrize("boundary", ["reserved", "one_past_end"])
def test_reserved_and_out_of_bounds_ids_cannot_resolve(boundary):
    script = TargetScript()
    target = 0 if boundary == "reserved" else len(script.globals["TOP_status"])
    before = deepcopy(script.globals)
    script.call("TOP_capture_target", TARGET=target)
    assert script.globals == before
    assert script.countries[1]["vars"]["TOP_archive_cursor"] == 0


@pytest.mark.parametrize(
    "mode,expected_mode,enabled",
    [
        ("TOP_limited_sandbox_option", 1, 1),
        ("TOP_full_sandbox_option", 2, 1),
        ("TOP_disabled_option", 0, 0),
    ],
)
def test_game_rule_cache_initializes_fresh_campaign(mode, expected_mode, enabled):
    script = TargetScript()
    script.mode = mode
    script.globals.pop("TOP_rule_enabled")
    script.globals.pop("TOP_rule_mode")
    script.run("TOP_cache_game_rule", 1)
    assert script.globals.get("TOP_rule_mode", 0) == expected_mode
    assert script.globals.get("TOP_rule_enabled", 0) == enabled


def test_disabled_rule_keeps_global_and_country_state_inert():
    script = TargetScript()
    script.target()
    script.mode = "TOP_disabled_option"
    script.globals["TOP_rule_enabled"] = 0
    script.globals["TOP_rule_mode"] = 0
    before = deepcopy((script.globals, script.countries))
    script.call("TOP_capture_target", TARGET=11)
    script.call("TOP_import_target_location", 2, TARGET=12)
    script.run("TOP_global_weekly", 1)
    script.run("TOP_global_monthly", 1)
    assert (script.globals, script.countries) == before


@pytest.mark.parametrize(
    "target,method,state", [(12, 1, 101), (11, 2, 101), (11, 1, 102)]
)
def test_native_callback_for_a_superseded_binding_cannot_touch_current_case(
    target, method, state
):
    script = TargetScript()
    variables = script.authorize()
    original_case = case_snapshot(script, 11)
    script.globals["TOP_status"][12] = 1
    script.temps.update(
        actor_country=1,
        target_state=state,
        TOP_target=target,
        TOP_method=method,
        TOP_tier=2,
    )
    script.call("TOP_native_result_args")
    assert script.globals["TOP_status"][11] == 1
    assert script.globals["TOP_status"][12] == 1
    assert script.globals["TOP_attempts"][11] == 0
    assert case_snapshot(script, 11) == original_case
    assert variables["TOP_archive_cursor"] == 0


def test_lethal_bda_updates_the_original_archive_without_rerolling_physical_truth():
    script = TargetScript()
    variables = script.authorize(method=3)
    script.run("TOP_complete_operation", 1)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_removals"][11] == 1
    assert variables["TOP_attempts"][11] == 1
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_physical"][0] == 3
    assert variables["TOP_assessment"][11] == 5

    script.globals["TOP_clock"] = 15
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_removals"][11] == 1
    assert script.globals["TOP_attempts"][11] == 1
    assert variables["TOP_assessment"][11] == 3
    assert variables["TOP_archive_cursor"] == 1
    assert variables["TOP_archive_result"][0] == 3
    assert variables["TOP_archive_physical"][0] == 3
    assert variables["TOP_archive_method"][0] == 3
    assert variables["TOP_archive_state"][0] == 101


def test_annexed_custodian_hands_prisoner_to_prison_controller_without_losing_credit():
    script = TargetScript()
    script.target()
    script.call("TOP_capture_target", TARGET=11)
    assert script.globals["TOP_custody_state"][11] == 100
    assert script.globals["TOP_detained_targets"] == [11]
    script.countries[1]["exists"] = False
    script.countries[100]["controller"] = 3
    script.run("TOP_update_detained_targets", 2)
    script.run("TOP_update_detained_targets", 2)
    recipient = script.countries[3]["vars"]
    assert script.globals["TOP_status"][11] == 2
    assert script.globals["TOP_custodian"][11] == 3
    assert script.globals["TOP_custody_state"][11] == 102
    assert script.globals["TOP_detained_targets"] == [11]
    assert script.globals["TOP_removals"][11] == 1
    assert 11 not in script.globals["TOP_active_targets"]
    assert recipient["TOP_known"][11] == 1
    assert recipient["TOP_assessment"][11] == 2
    assert recipient["TOP_dossiers"] == [11]
    assert script.external["TOP_exploit_capture", 3] == 0
    assert script.external["TOP_update_iraq_progress", 2] == 2


@pytest.mark.parametrize("end_custody", ["TOP_release_selected", "TOP_kill_target"])
def test_released_or_dead_people_leave_bounded_detention_processing(end_custody):
    script = TargetScript()
    script.target()
    script.call("TOP_capture_target", TARGET=11)
    if end_custody == "TOP_kill_target":
        script.call(end_custody, TARGET=11)
    else:
        script.run(end_custody, 1)
    script.run("TOP_update_detained_targets", 2)
    assert script.globals["TOP_detained_targets"] == []


def test_returning_org_identity_reopens_activation_without_resurrecting_removed_people():
    script = TargetScript()
    script.globals["TOP_group_window"][2] = 1
    script.globals["TOP_status"][12] = 3
    script.globals["TOP_window"][12] = 1
    script.globals["TOP_window"][13] = 1
    script.run("TOP_reconcile_organizations", 1)
    script.globals["active_terror_orgs"] = ScriptArray([0, 14])
    script.run("TOP_reconcile_organizations", 1)
    assert script.globals["TOP_group_destroyed"][2] == 1
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_status"][13] == 0
    script.globals["active_terror_orgs"].append(10)
    script.run("TOP_reconcile_organizations", 1)
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_group_destroyed"][2] == 0
    assert script.globals["TOP_status"][12] == 3
    assert script.globals["TOP_status"][13] == 1
    assert script.globals["TOP_active_targets"] == [13]
    script.temps["TOP_target"] = 13
    script.run("TOP_find_org", 1)
    assert script.temps["TOP_org_slot"] == 2


def test_designation_allows_multiple_persistent_packages_in_one_host():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_package_state"][11] = 0
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][11] == 1
    script.target(12)
    variables["TOP_package_state"][12] = 0
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][12] == 1
    script.target(13, host=3, state=102)
    variables["TOP_package_state"][13] = 0
    script.run("TOP_designate_selected", 1)
    assert variables["TOP_package_state"][13] == 1
    assert variables.get("TOP_active_cases", []) == []
    assert variables["political_power"] == 425

    script.countries[3]["vars"]["political_power"] = 100
    script.target(11, actor=3)
    script.countries[3]["vars"]["TOP_package_state"][11] = 0
    script.run("TOP_designate_selected", 3)
    assert script.countries[3]["vars"]["TOP_package_state"][11] == 1
    assert script.countries[3]["vars"]["political_power"] == 75


def fire_native_callback(script, target=11, method=1, tier=2, state=101):
    """Run a raid callback from its own instance scope.

    TOP_native_result_args reads TOP_target, TOP_method and TOP_tier: raids set
    them inline because common/raids/ is parsed before the scripted effects
    register, so a parameterised call there cannot resolve.
    """
    script.country(1000, tag="raid_instance")
    script.countries[1000]["vars"].update(actor_country=1, target_state=state)
    script.temps.pop("target_state", None)
    script.temps.update(TOP_target=target, TOP_method=method, TOP_tier=tier)
    script.call("TOP_native_result_args", 1000)


def test_native_callback_loads_its_person_case_while_another_host_is_selected():
    script = TargetScript()
    variables = script.authorize()
    script.authorize(12, host=3, state=102, begin=False)
    other = case_snapshot(script, 12)
    fire_native_callback(script)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_case_phase"][11] == 4
    assert case_snapshot(script, 12) == other
    assert variables["TOP_archive_target"][0] == 11
    assert variables["TOP_archive_state"][0] == 101


@pytest.mark.parametrize("restore", [False, True], ids=["live", "persisted_state"])
def test_waiting_timed_mandates_execute_sequentially_through_one_slot(restore):
    script = TargetScript()
    script.authorize(method=3)
    script.authorize(12, method=4, host=3, state=102)
    if restore:
        script = script.persisted_clone()
    variables = script.countries[1]["vars"]
    assert variables["TOP_case_phase"][11] == 3
    assert variables["TOP_case_phase"][12] == 2
    variables["TOP_selected"] = 0
    script.temps.clear()
    script.globals["TOP_clock"] = 29
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][11] == 3
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_case_phase"][11] == 4
    assert variables["TOP_case_phase"][12] == 2
    assert variables["TOP_attempts"][11] == 1
    assert variables["TOP_attempts"][12] == 0

    script.call("TOP_begin_person_operation", TARGET=12)
    assert variables["TOP_case_phase"][12] == 3
    script.globals["TOP_clock"] = 58
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][12] == 2
    assert variables["TOP_archive_cursor"] == 2
    assert variables["TOP_attempts"][11] == variables["TOP_attempts"][12] == 1
    assert set(variables["TOP_archive_target"][:2]) == {11, 12}


def test_assessment_holds_host_after_expiry_and_revoke_until_recorded_confirmation():
    script = TargetScript()
    variables = script.authorize()
    script.temps["TOP_tier"] = 2
    script.run("TOP_complete_operation", 1)
    assert variables["TOP_case_phase"][11] == 4
    script.authorize(12, host=3, state=102, begin=False)
    variables["TOP_case_until"][12] = 300
    other = case_snapshot(script, 12)
    variables["TOP_selected"] = 11
    script.run("TOP_revoke_authorization", 1)
    script.run("TOP_confirm_assessment", 1)
    assert variables["TOP_case_phase"][11] == 4
    script.globals["TOP_clock"] = 100
    script.run("TOP_process_timers", 1)
    assert variables["TOP_case_phase"][11] == 5
    script.call("TOP_find_host_case", HOST=2)
    assert script.temps["TOP_host_case"] == 11
    script.run("TOP_revoke_authorization", 1)
    assert variables["TOP_case_phase"][11] == 5
    script.run("TOP_confirm_assessment", 1)
    assert variables["TOP_case_phase"][11] == 0
    assert variables["TOP_active_cases"] == [12]
    assert case_snapshot(script, 12) == other
    assert script.globals["TOP_status"][11] == 3


def test_another_countrys_kill_changes_global_truth_before_local_reporting():
    script = TargetScript()
    variables = script.authorize()
    script.call("TOP_kill_target", 3, TARGET=11)
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_confirmed_dead"][11] == 1
    assert variables["TOP_case_phase"][11] == 5
    assert variables["TOP_assessment"][11] == 3
    script.run("TOP_confirm_assessment", 1)
    assert variables["TOP_case_phase"][11] == 0


@pytest.mark.parametrize("action", ["close", "revoke", "expire"])
def test_closing_one_case_preserves_other_hosts_and_rejects_its_late_callback(action):
    script = TargetScript()
    variables = script.authorize()
    script.authorize(12, host=3, state=102)
    variables["TOP_case_until"][12] = 300
    other = case_snapshot(script, 12)
    variables["TOP_selected"] = 11
    if action == "close":
        script.call("TOP_close_case", TARGET=11, SEQUENCE=999)
        assert variables["TOP_case_phase"][11] == 3
        script.call("TOP_close_case", TARGET=11, SEQUENCE=11)
    elif action == "revoke":
        script.run("TOP_revoke_authorization", 1)
    else:
        script.globals["TOP_clock"] = 100
        script.run("TOP_process_timers", 1)
    assert variables["TOP_case_phase"][11] == 0
    assert case_snapshot(script, 12) == other
    assert variables["TOP_active_cases"] == [12]
    fire_native_callback(script)
    assert script.globals["TOP_status"][11] == 1
    assert script.globals["TOP_status"][12] == 1
    assert variables["TOP_archive_cursor"] == 0
    assert case_snapshot(script, 12) == other


def test_cancelled_timed_case_cannot_complete_after_other_host_is_authorized():
    script = TargetScript()
    variables = script.authorize(method=3)
    script.authorize(12, method=4, host=3, state=102)
    assert variables["TOP_case_phase"][12] == 2
    variables["TOP_selected"] = 11
    script.run("TOP_revoke_authorization", 1)
    script.call("TOP_begin_person_operation", TARGET=12)
    script.globals["TOP_clock"] = 29
    script.run("TOP_process_timers", 1)
    assert script.globals["TOP_status"][11] == 1
    assert script.globals["TOP_status"][12] == 2
    assert variables["TOP_attempts"][11] == 0
    assert variables["TOP_attempts"][12] == 1
    assert variables["TOP_archive_target"][0] == 12


def test_person_window_cannot_force_a_network_into_existence_before_its_window():
    script = TargetScript()
    script.run("TOP_open_windows_2006", 1)
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_status"][11] == 0
    script.run("TOP_open_windows_2009", 1)
    script.run("TOP_activate_group_2", 1)
    assert script.globals["TOP_status"][11] == 1
