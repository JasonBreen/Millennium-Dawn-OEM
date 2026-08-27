import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))

from check_chain_extraction import check  # noqa: E402


def _write(root, rel, text, bom=False):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    with io.open(str(path), "wb") as handle:
        handle.write((b"\xef\xbb\xbf" + data) if bom else data)
    return str(path)


EVENT = """country_event = {
\tid = demo.1
\ttitle = demo.1.t
\tdesc = demo.1.d
\tis_triggered_only = yes

\ttrigger = {
\t\tNOT = { has_country_flag = DEMO_took_the_deal }
\t}

\toption = {
\t\tname = demo.1.a
\t\tset_country_flag = DEMO_took_the_deal
\t\tai_chance = { base = 50 }
\t}
}
"""

LOC = """l_english:
 demo.1.t: "Demo"
 demo.1.d: "Demo description"
 demo.1.a: "Take the deal"
"""

SET_LINE = "\t\tset_country_flag = DEMO_took_the_deal\n"
GUARD_LINE = "\t\tNOT = { has_country_flag = DEMO_took_the_deal }\n"


def _fixture(tmp_path, event=EVENT, loc=LOC):
    target = _write(tmp_path, "events/demo.txt", event)
    _write(tmp_path, "localisation/english/demo_l_english.yml", loc, bom=True)
    (tmp_path / "common").mkdir(exist_ok=True)
    return target


def _messages(tmp_path, target, **kwargs):
    return [m for _, _, m in check(str(tmp_path), [target], "", **kwargs)]


def test_a_complete_chain_passes(tmp_path):
    target = _fixture(tmp_path)

    assert check(str(tmp_path), [target], "") == []


def test_flags_written_but_never_read_are_reported(tmp_path):
    target = _fixture(tmp_path, event=EVENT.replace(GUARD_LINE, ""))

    assert any("DEMO_took_the_deal is written but never read" in m
               for m in _messages(tmp_path, target))


def test_flags_read_but_never_written_are_reported(tmp_path):
    event = EVENT.replace(
        "\t\tai_chance = { base = 50 }",
        "\t\tai_chance = {\n\t\t\tbase = 50\n"
        "\t\t\tmodifier = { factor = 2 has_country_flag = DEMO_sibling_chain }\n\t\t}",
    )
    target = _fixture(tmp_path, event=event)

    assert any("DEMO_sibling_chain is read but never written" in m
               for m in _messages(tmp_path, target))


def test_an_option_with_no_outcome_is_reported(tmp_path):
    target = _fixture(tmp_path, event=EVENT.replace(SET_LINE, ""))

    assert any("demo.1.a records no outcome" in m for m in _messages(tmp_path, target))


def test_missing_localisation_is_reported(tmp_path):
    target = _fixture(tmp_path, loc=LOC.replace(' demo.1.a: "Take the deal"\n', ""))

    assert any("no localisation for demo.1.a" in m for m in _messages(tmp_path, target))


def test_effect_outcomes_exempts_a_chain_that_records_through_effects(tmp_path):
    event = EVENT.replace(SET_LINE, "\t\tDEMO_apply_route = yes\n").replace(GUARD_LINE, "")
    target = _fixture(tmp_path, event=event)

    strict = _messages(tmp_path, target)
    lenient = _messages(tmp_path, target, effect_outcomes=True)

    assert any("demo.1.a records no outcome" in m for m in strict)
    assert not any("records no outcome" in m for m in lenient)
