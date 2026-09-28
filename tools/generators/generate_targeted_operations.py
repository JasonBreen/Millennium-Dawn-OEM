"""Generate stable Targeted Operations identity and dossier storage definitions."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GLOBAL_FIELDS = (
    "status",
    "confirmed_dead",
    "state",
    "host",
    "custodian",
    "custody_state",
    "custody_actor",
    "custody_sequence",
    "affiliation",
    "political",
    "civilian",
    "security",
    "attempts",
    "removals",
    "first_outcome",
    "window",
    "office",
    "generated_used",
    "pressure",
    "public_identity",
    "leader_role",
    "consequence_profile",
)
COUNTRY_FIELDS = (
    "legacy_report_pending",
    "known",
    "confidence",
    "lead_state",
    "lead_host",
    "lead_age",
    "lead_report_clock",
    "assessment",
    "mandates",
    "attempts",
    "bda_due",
    "bda_result",
    "bda_method",
    "bda_state",
    "bda_token",
    "bda_archive_row",
    "bda_archive_token",
    "bda_identity",
    "capture_exploited",
    "exchange_country",
    "exchange_until",
    "identity_confidence",
    "location_confidence",
    "pattern_confidence",
    "identity_source",
    "location_source",
    "pattern_source",
    "lead_source",
    "history_cycle",
    "package_state",
    "collection_focus",
    "liaison_age",
    "liaison_reliability",
)
GROUP_FIELDS = (
    "ct",
    "leader",
    "created",
    "destroyed",
    "window",
    "class",
    "public_identity",
    "host",
    "state",
    "pressure",
    "disruption_type",
    "disruption_until",
    "facility_objectives",
)
ORG_COUNTRY_FIELDS = (
    "known",
    "verification",
    "location",
    "activity",
    "verification_source",
    "location_source",
    "activity_source",
    "lead_source",
    "history_cycle",
    "lead_state",
    "lead_host",
    "lead_age",
    "lead_report_clock",
    "package_state",
    "collection_focus",
    "mandates",
    "liaison_age",
    "liaison_reliability",
)
ROOT = Path(__file__).resolve().parents[2]
TARGET_CLASSES = {"militant", "official", "civilian"}
GROUP_CLASS_IDS = {
    "militant_network": 1,
    "state_security": 2,
    "political_executive": 3,
    "civilian_organization": 4,
}
GROUP_CLASSES = set(GROUP_CLASS_IDS)
LOCATION_POLICIES = {"group_hq", "country_capital", "target_state"}
CLASS_LOCATION_POLICIES = {
    "militant_network": {"group_hq"},
    "state_security": {"country_capital", "target_state"},
    "political_executive": {"country_capital", "target_state"},
    "civilian_organization": {"country_capital", "target_state"},
}
FACILITY_OBJECTIVE_BITS = {"command": 1, "training": 2, "funding": 4}
FACILITY_OBJECTIVE_DEFAULTS = {
    "militant_network": 7,
    "state_security": 7,
    "political_executive": 5,
    "civilian_organization": 5,
}
LEADER_ROLE_IDS = {
    "none": 0,
    "head_of_state": 1,
    "head_of_government": 2,
    "senior_political": 3,
    "state_security_official": 4,
    "civilian_public_figure": 5,
}
CONSEQUENCE_PROFILE_IDS = {
    "militant": 1,
    "state_security": 2,
    "political_leader": 3,
    "civilian_public": 4,
}
STABLE_GROUP_KEYS = (
    "aq",
    "aqap",
    "isi",
    "ttp",
    "boko",
    "shabaab",
    "aqim",
    "lra",
    "ji",
    "asg",
    "iraq",
    "irgc",
    "russian_executive",
    "belarus_presidency",
    "ukraine_presidency",
    "iran_supreme_office",
    "irgc_command",
    "irgc_ground",
    "irgc_aerospace",
    "irgc_navy",
    "tpusa",
    "isis_k",
    "jnim",
    "isis_somalia",
    "china_presidency",
    "north_korea_supreme_office",
    "myanmar_executive",
    "turkiye_presidency",
    "brazil_presidency",
    "egypt_presidency",
    "indonesia_presidency",
    "saudi_executive",
    "israel_premiership",
    "venezuela_presidency",
)
STABLE_TARGET_KEYS = (
    "osama_bin_laden",
    "ayman_al_zawahiri",
    "khalid_sheikh_mohammed",
    "ramzi_bin_al_shibh",
    "mohammed_atef",
    "abu_faraj_al_libbi",
    "abu_yahya_al_libi",
    "atiyah_abd_al_rahman",
    "saif_al_adel",
    "abu_muhammad_al_masri",
    "anwar_al_awlaki",
    "nasir_al_wuhayshi",
    "qasim_al_raymi",
    "khalid_al_batarfi",
    "ibrahim_al_asiri",
    "abu_fatima_al_jaheishi",
    "turki_al_binali",
    "lavdrim_muhaxheri",
    "gulmurod_khalimov",
    "abdullah_ahmed_al_mashadani",
    "ahmed_khalal_al_juhayshi",
    "fares_reif_al_naima",
    "abu_ahmad_al_alwani",
    "abu_muhammad_al_shimali",
    "ayad_al_jumaili",
    "khairy_abed_mahmoud_al_taey",
    "abdul_wahid_khutnayer_ahmad",
    "abu_jihad_shishani",
    "abu_musab_al_zarqawi",
    "abu_ayyub_al_masri",
    "abu_omar_al_baghdadi",
    "abu_bakr_al_baghdadi",
    "abu_muhammad_al_adnani",
    "abu_omar_al_shishani",
    "abu_ibrahim_al_hashimi_al_qurashi",
    "abu_hafs_al_hashimi_al_qurashi",
    "nek_muhammad_wazir",
    "baitullah_mehsud",
    "hakimullah_mehsud",
    "maulana_fazlullah",
    "noor_wali_mehsud",
    "omar_khalid_khorasani",
    "abubakar_shekau",
    "abu_musab_al_barnawi",
    "ahmed_abdi_godane",
    "ahmed_diriye",
    "abdelmalek_droukdel",
    "mokhtar_belmokhtar",
    "abdelhamid_abu_zeid",
    "joseph_kony",
    "hambali",
    "noordin_mohammad_top",
    "dulmatin",
    "khadaffy_janjalani",
    "isnilon_hapilon",
    "saddam_hussein",
    "qusay_hussein",
    "uday_hussein",
    "abid_hamid_mahmud",
    "ali_hassan_al_majid",
    "izzat_ibrahim_al_douri",
    "hani_abd_al_latif_tilfah",
    "aziz_salih_al_numan",
    "qasem_soleimani",
    "vladimir_putin",
    "dmitry_medvedev",
    "alexander_lukashenko",
    "volodymyr_zelenskyy",
    "ali_khamenei",
    "mojtaba_khamenei",
    "mohammad_ali_jafari",
    "hossein_salami",
    "mohammad_pakpour",
    "esmail_qaani",
    "amir_ali_hajizadeh",
    "ali_fadavi",
    "charlie_kirk",
    "saad_bin_atef_al_awlaki",
    "abu_ubaydah_yusuf_al_anabi",
    "xi_jinping",
    "sanaullah_ghafari",
    "kim_jong_un",
    "min_aung_hlaing",
    "iyad_ag_ghali",
    "jehad_serwan_mostafa",
    "recep_tayyip_erdogan",
    "ibrahim_ahmed_mahmoud_al_qosi",
    "luiz_inacio_lula_da_silva",
    "abdel_fattah_el_sisi",
    "hamza_salih_bin_said_al_ghamdi",
    "abd_al_rahman_al_maghrebi",
    "prabowo_subianto",
    "abdiqadir_mumin",
    "mohammed_bin_salman",
    "benjamin_netanyahu",
    "nicolas_maduro",
)


def block(name: str, lines: list[str]) -> str:
    return name + " = {\n" + "\n".join("\t" + line for line in lines) + "\n}\n"


def objective_mask(objectives: object) -> int:
    if (
        not isinstance(objectives, list)
        or not objectives
        or len(objectives) != len(set(objectives))
        or any(objective not in FACILITY_OBJECTIVE_BITS for objective in objectives)
    ):
        raise ValueError(
            "Facility objectives must be a nonempty set of known objectives"
        )
    return sum(FACILITY_OBJECTIVE_BITS[objective] for objective in objectives)


def group_objective_mask(data: dict, group: dict) -> int:
    objectives = group.get(
        "facility_objectives",
        data["facility_objective_defaults"][group["group_class"]],
    )
    return objective_mask(objectives)


def load_manifest(root: Path) -> dict:
    with (root / "tools/data/targeted_operations.json").open(
        encoding="utf-8"
    ) as stream:
        data = json.load(stream)
    if data.get("version") != 4:
        raise ValueError("Targeted Operations manifest must use schema version 4")
    defaults = data.get("facility_objective_defaults")
    if not isinstance(defaults, dict) or set(defaults) != GROUP_CLASSES:
        raise ValueError("Facility objective defaults must cover every group class")
    for group_class, expected in FACILITY_OBJECTIVE_DEFAULTS.items():
        if objective_mask(defaults[group_class]) != expected:
            raise ValueError(f"Invalid facility objective default for {group_class}")

    ids = [target["id"] for target in data["targets"]]
    expected_ids = list(range(1, data["generated_start"])) + list(
        range(data["generated_end"], data["capacity"])
    )
    if ids != expected_ids:
        raise ValueError(
            "Authored IDs must preserve slots 1-64 and follow the reserved generated interval"
        )
    if not (
        data["generated_start"] == 65
        and data["generated_end"] == 129
        and data["generated_end"] <= data["capacity"] <= 838
    ):
        raise ValueError("Invalid registry capacity")
    if tuple(target["key"] for target in data["targets"]) != STABLE_TARGET_KEYS:
        raise ValueError("Authored person keys must retain their stable IDs")
    group_id_list = [group["id"] for group in data["groups"]]
    group_ids = set(group_id_list)
    if group_id_list != list(range(1, len(data["groups"]) + 1)):
        raise ValueError(
            "Organization identities must preserve slots 1-12 and append consecutive groups"
        )
    if tuple(group["key"] for group in data["groups"]) != STABLE_GROUP_KEYS:
        raise ValueError("Organization keys must retain their stable IDs")
    ct_ids = [group["ct_id"] for group in data["groups"] if "ct_id" in group]
    if any(type(ident) is not int or not 0 <= ident <= 14 for ident in ct_ids) or len(
        set(ct_ids)
    ) != len(ct_ids):
        raise ValueError("Duplicate or out-of-range CT identity")
    if len({target["key"] for target in data["targets"]}) != len(ids):
        raise ValueError("Duplicate target key")
    groups = {group["id"]: group for group in data["groups"]}
    for target in data["targets"]:
        if target["group"] not in group_ids or any(
            i not in ids for i in target["successors"]
        ):
            raise ValueError(f"Invalid affiliation or successor for {target['id']}")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", target["key"]):
            raise ValueError(f"Invalid target key for {target['id']}")
        if target.get("target_class") not in TARGET_CLASSES:
            raise ValueError(f"Invalid target class for {target['id']}")
        group = groups[target["group"]]
        group_class = group.get("group_class")
        allowed_group_classes = {
            "militant": {"militant_network"},
            "official": {"state_security", "political_executive"},
            "civilian": {"civilian_organization"},
        }[target["target_class"]]
        if group_class not in allowed_group_classes:
            raise ValueError(f"Target class does not match group for {target['id']}")
        if type(target.get("public_identity")) is not bool:
            raise ValueError(f"Invalid public identity for target {target['id']}")
        expected_public = target["target_class"] != "militant"
        if target["public_identity"] != expected_public:
            raise ValueError(
                f"Public identity does not match target class for {target['id']}"
            )
        leader_role = target.get("leader_role")
        if leader_role not in LEADER_ROLE_IDS:
            raise ValueError(f"Invalid leader role for target {target['id']}")
        consequence_profile = target.get("consequence_profile")
        if consequence_profile not in CONSEQUENCE_PROFILE_IDS:
            raise ValueError(f"Invalid consequence profile for target {target['id']}")
        expected_profile = {
            "militant_network": "militant",
            "state_security": "state_security",
            "political_executive": "political_leader",
            "civilian_organization": "civilian_public",
        }[group_class]
        if consequence_profile != expected_profile:
            raise ValueError(
                f"Consequence profile does not match group for {target['id']}"
            )
        role_eligibility = target.get("role_eligibility", {})
        eligibility_kind = role_eligibility.get("kind")
        political_roles = {"head_of_state", "head_of_government", "senior_political"}
        serving_roles = political_roles | {"state_security_official"}
        if leader_role in serving_roles:
            if (
                eligibility_kind != "serving_state_role"
                or not role_eligibility.get("office_keys")
                or role_eligibility.get("trigger")
                != f"TOP_authored_role_eligible = {{ TARGET = {target['id']} }}"
            ):
                raise ValueError(
                    f"Incomplete serving leader binding for {target['id']}"
                )
        if (
            leader_role == "civilian_public_figure"
            and eligibility_kind != "civilian_exception_only"
        ):
            raise ValueError(f"Incomplete civilian leader binding for {target['id']}")
        if eligibility_kind == "serving_state_role" and leader_role == "none":
            raise ValueError(f"Serving official lacks a leader role for {target['id']}")
        if (
            eligibility_kind == "civilian_exception_only"
            and leader_role != "civilian_public_figure"
        ):
            raise ValueError(
                f"Civilian exception lacks a leader role for {target['id']}"
            )
        if target["historical_outcome"].get("force_in_campaign") is not False:
            raise ValueError("Historical outcomes cannot force campaign removals")
        if not 2000 <= target["activation_year"] <= 2032:
            raise ValueError(f"Invalid authored opportunity year for {target['id']}")
        if not target["sources"]:
            raise ValueError(f"Missing authoring provenance for {target['id']}")
        if any(source not in data["sources"] for source in target["sources"]):
            raise ValueError(f"Unknown source for {target['id']}")
    for group in data["groups"]:
        if group.get("group_class") not in GROUP_CLASSES:
            raise ValueError(f"Invalid group class for {group['id']}")
        if group.get("location_policy") not in LOCATION_POLICIES:
            raise ValueError(f"Invalid location policy for {group['id']}")
        if (
            group["location_policy"]
            not in CLASS_LOCATION_POLICIES[group["group_class"]]
        ):
            raise ValueError(
                f"Location policy does not match class for group {group['id']}"
            )
        if "ct_id" in group and group["group_class"] != "militant_network":
            raise ValueError(
                f"Only militant networks can use a CT identity: {group['id']}"
            )
        if type(group.get("public_identity")) is not bool:
            raise ValueError(f"Invalid public identity for group {group['id']}")
        expected_public = group["group_class"] != "militant_network"
        if group["public_identity"] != expected_public:
            raise ValueError(
                f"Public identity does not match class for group {group['id']}"
            )
        group_objective_mask(data, group)
        succession = group.get("succession", [])
        if len(succession) != len(set(succession)):
            raise ValueError(f"Duplicate successor for organization {group['id']}")
    affiliations = {t["id"]: t["group"] for t in data["targets"]}
    targets = {target["id"]: target for target in data["targets"]}
    for group in data["groups"]:
        for successor in group.get("succession", []):
            if affiliations.get(successor) != group["id"]:
                raise ValueError(
                    "Organization successor belongs to another organization"
                )
            if (
                targets[successor]["role_eligibility"].get("kind")
                != "authored_successor_pool"
            ):
                raise ValueError(
                    "Organization successor is not in an authored successor pool"
                )
            expected = [ident for ident in group["succession"] if ident != successor]
            if targets[successor]["successors"] != expected:
                raise ValueError(f"Incomplete successor binding for {successor}")
    for target in data["targets"]:
        if target["id"] in target["successors"] or len(target["successors"]) != len(
            set(target["successors"])
        ):
            raise ValueError(f"Duplicate or self successor for {target['id']}")
        if any(affiliations[i] != target["group"] for i in target["successors"]):
            raise ValueError("Person successor belongs to another organization")
        if target["successors"]:
            expected = [
                ident
                for ident in groups[target["group"]].get("succession", [])
                if ident != target["id"]
            ]
            if target["successors"] != expected:
                raise ValueError(f"Incomplete successor binding for {target['id']}")

    return data


def registry(data: dict) -> str:
    capacity = data["capacity"]
    group_capacity = max(group["id"] for group in data["groups"]) + 1
    lines = [
        f"set_variable = {{ global.TOP_registry_capacity = {capacity} }}",
    ]
    lines += [
        f"resize_array = {{ global.TOP_{field} = {capacity} }}"
        for field in GLOBAL_FIELDS
    ]
    for field in GROUP_FIELDS:
        lines.append(
            f"resize_array = {{ global.TOP_group_{field} = {group_capacity} }}"
        )
    lines += [
        f"resize_array = {{ global.TOP_backlash = {group_capacity} }}",
        "set_variable = { global.TOP_clock = 0 }",
    ]
    for group in data["groups"]:
        gid = group["id"]
        lines += [
            f"set_variable = {{ global.TOP_group_ct^{gid} = {group.get('ct_id', -1)} }}",
            f"set_variable = {{ global.TOP_group_class^{gid} = {GROUP_CLASS_IDS[group['group_class']]} }}",
            f"set_variable = {{ global.TOP_group_public_identity^{gid} = {int(group['public_identity'])} }}",
            f"set_variable = {{ global.TOP_group_facility_objectives^{gid} = {group_objective_mask(data, group)} }}",
        ]
    for target in data["targets"]:
        ident = target["id"]
        lines += [
            f"set_variable = {{ global.TOP_affiliation^{ident} = {target['group']} }}",
            f"set_variable = {{ global.TOP_political^{ident} = {int(target['target_class'] in {'official', 'civilian'})} }}",
            f"set_variable = {{ global.TOP_public_identity^{ident} = {int(target['public_identity'])} }}",
            f"set_variable = {{ global.TOP_leader_role^{ident} = {LEADER_ROLE_IDS[target['leader_role']]} }}",
            f"set_variable = {{ global.TOP_consequence_profile^{ident} = {CONSEQUENCE_PROFILE_IDS[target['consequence_profile']]} }}",
        ]
        if target["target_class"] == "civilian":
            lines.append(f"set_variable = {{ global.TOP_civilian^{ident} = 1 }}")
    for ident in range(data["generated_start"], data["generated_end"]):
        group = (ident - data["generated_start"]) % 10 + 1
        lines += [
            f"set_variable = {{ global.TOP_affiliation^{ident} = {group} }}",
            f"set_variable = {{ global.TOP_consequence_profile^{ident} = {CONSEQUENCE_PROFILE_IDS['militant']} }}",
        ]
    output = block("TOP_setup_registry", lines)
    output += "\n" + block(
        "TOP_resize_country_arrays",
        [f"resize_array = {{ TOP_{field} = {capacity} }}" for field in COUNTRY_FIELDS]
        + [
            f"resize_array = {{ TOP_org_{field} = {group_capacity} }}"
            for field in ORG_COUNTRY_FIELDS
        ]
        + [
            f"resize_array = {{ TOP_archive_{field} = 128 }}"
            for field in (
                "target",
                "result",
                "method",
                "day",
                "state",
                "disposition",
                "custody_token",
            )
        ],
    )
    return output


def generate(root: Path, check: bool = False) -> list[str]:
    relative = "common/scripted_effects/01_targeted_operations_registry.txt"
    path = root / relative
    content = registry(load_manifest(root))
    current = None
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as stream:
            current = stream.read()
    if current == content:
        return []
    if not check:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as stream:
            stream.write(content)
    return [relative]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = generate(args.root, args.check)
    if args.check and changed:
        print("Generated target definitions are stale: " + ", ".join(changed))
        return 1
    print(
        f"Target registry: {len(changed)} generated files {'differ' if args.check else 'updated'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
