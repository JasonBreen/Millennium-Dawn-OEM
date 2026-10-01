import importlib.util


def _module():
    from shared.paths import TOOLS_DIR

    path = TOOLS_DIR / "analysis" / "scenario_ai_audit.py"
    spec = importlib.util.spec_from_file_location("scenario_ai_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


DECISIONS = """
XX_category = {
	XX_no_weight = {
		available = { always = yes }
		complete_effect = { add_political_power = 1 }
	}
	XX_zero = {
		complete_effect = { add_political_power = 1 }
		ai_will_do = { base = 0 }
	}
	XX_player_only_zero = {
		visible = { is_ai = no }
		complete_effect = { add_political_power = 1 }
		ai_will_do = { base = 0 }
	}
	XX_remove_only = {
		cost = 10
		remove_effect = { add_political_power = 1 }
	}
	XX_ai_only_zero = {
		available = { NOT = { is_ai = no } }
		complete_effect = { add_political_power = 1 }
		ai_will_do = { base = 0 }
	}
	XX_or_zero = {
		visible = { OR = { is_ai = no has_war = yes } }
		complete_effect = { add_political_power = 1 }
		ai_will_do = { base = 0 }
	}
	XX_scoped_player = {
		visible = { FROM = { controller = { is_ai = no } } }
		complete_effect = { add_political_power = 1 }
	}
	XX_root_player = {
		visible = { ROOT = { is_ai = no } }
		complete_effect = { add_political_power = 1 }
	}
	XX_fine = {
		complete_effect = { add_political_power = 1 }
		ai_will_do = { base = 5 }
	}
	# a comment = { not a decision }
	XX_flavor = { icon = x }
}
"""


def _event(eid, options, trigger="", extra="", kind="country_event"):
    opts = "".join(
        f"\toption = {{\n\t\tname = {eid}.{i}\n{o}\t}}\n" for i, o in enumerate(options)
    )
    return f"{kind} = {{\n\tid = {eid}\n\ttitle = {eid}.t\n\tis_triggered_only = yes\n{extra}\ttrigger = {{ {trigger} }}\n{opts}}}\n\n"


WEIGHTED = ["\t\tai_chance = { base = 60 }\n", "\t\tai_chance = { base = 40 }\n"]

EVENTS = (
    "add_namespace = XX\n"
    + _event("XX.1", ["", "\t\tai_chance = { base = 1 }\n"])
    + _event("XX.2", WEIGHTED)
    + _event("XX.3", WEIGHTED)
    + _event("XX.4", WEIGHTED, trigger="is_ai = no")
    + _event("XX.5", ["\t\tai_chance = { base = 1 }\n"])
    + _event("XX.6", ["", ""], extra="\thidden = yes\n")
    + _event(
        "XX.7",
        WEIGHTED,
        extra="\tdesc = { text = x trigger = { check_variable = { global.XX_event_zone_id = 1 } } }\n",
    )
    + _event("XX.8", WEIGHTED, kind="news_event")
    + _event(
        "XX.10",
        [
            '\t\tlog = "fired # 1 } {" ai_chance = { base = 60 }\n',
            "\t\tai_chance = { base = 40 }\n",
        ],
        trigger="OR = { is_ai = no has_war = yes }",
        extra="\tdesc = { text = x trigger = { check_variable = { global.XX_event_zone_id = 1 } } }\n",
    )
    + _event(
        "XX.9",
        WEIGHTED,
        kind="state_event",
        extra="\tdesc = { text = x trigger = { check_variable = { global.XX_event_zone_id = 1 } } }\n",
    )
)

EFFECTS = """
XX_pulse = {
	if = {
		limit = { controller = { is_ai = no } }
		controller = { country_event = XX.2 }
	}
	every_country = { country_event = XX.3 }
	if = {
		limit = { is_ai = no }
		country_event = XX.3
		country_event = XX.4
	}
	country_event = { id = XX.7 days = 30 }
	country_event = { id = XX.5 }
	if = {
		limit = { is_ai = no }
		news_event = XX.8
	}
	random_state = { state_event = { id = XX.9 days = 5 } }
	country_event = { id = XX.10 hours = 6 }
}
"""


def _repo(tmp_path):
    repo = tmp_path / "repo"
    _write(repo / "common/decisions/XX_decisions.txt", DECISIONS)
    _write(repo / "common/decisions/OTHER.txt", DECISIONS.replace("XX_", "YY_"))
    _write(repo / "events/XX_core.txt", EVENTS)
    _write(repo / "common/scripted_effects/99_XX_effects.txt", EFFECTS)
    _write(repo / "common/scripted_effects/unrelated.txt", "x = { y = yes }\n")
    _write(
        repo / "history/countries/XXX - Test.txt",
        "capital = 1\ncountry_event = { id = XX.8 days = 1 }\n",
    )
    return repo


def test_audit_findings(tmp_path):
    mod = _module()
    results, count = mod.audit(_repo(tmp_path), "XX")
    assert count == 10
    decisions = {name: msg for _, name, msg in results["decisions"]}
    zero = "decision ai_will_do is 0; the AI never takes it"
    assert decisions == {
        "XX_no_weight": "decision has no ai_will_do",
        "XX_zero": zero,
        "XX_remove_only": "decision has no ai_will_do",
        "XX_ai_only_zero": zero,
        "XX_or_zero": zero,
        "XX_scoped_player": "decision has no ai_will_do",
    }
    options = {eid: msg for _, eid, msg in results["event options"]}
    assert options == {"XX.1": "1 of 2 options have no ai_chance"}
    dispatch = {(eid, msg) for _, eid, msg in results["dispatch"]}
    assert (
        "XX.2",
        "has AI weights but every dispatch is player-only (is_ai = no)",
    ) in dispatch
    assert (
        "XX.7",
        "delayed dispatch in 99_XX_effects.txt and the event reads a shared global",
    ) in dispatch
    # XX.8 is also sent, ungated, from a history file.
    assert (
        "XX.8",
        "has AI weights but every dispatch is player-only (is_ai = no)",
    ) not in dispatch
    assert (
        "XX.9",
        "delayed dispatch in 99_XX_effects.txt and the event reads a shared global",
    ) in dispatch
    assert dispatch >= {
        (
            "XX.10",
            "delayed dispatch in 99_XX_effects.txt and the event reads a shared global",
        )
    }
    assert (
        "XX.10",
        "has AI weights but every dispatch is player-only (is_ai = no)",
    ) not in dispatch
    assert not any(eid in ("XX.3", "XX.4", "XX.5") for eid, _ in dispatch)


def test_main_prints_report(tmp_path, capsys):
    mod = _module()
    assert mod.main(["XX", "--repo", str(_repo(tmp_path))]) == 0
    out = capsys.readouterr().out
    assert out.startswith("XX: 10 events checked, 11 finding(s)")
    assert "## dispatch (4)" in out
    assert "- XX_decisions.txt: XX_zero: decision ai_will_do is 0" in out
