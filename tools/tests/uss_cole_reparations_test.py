from decimal import Decimal
from pathlib import Path

import pytest
from shared_utils import iter_statements, read_script

ROOT = Path(__file__).resolve().parents[2]


def _scalar(body, name):
    return next(value for key, value, _ in iter_statements(body) if key == name)


@pytest.fixture(scope="module")
def cole_events():
    source = read_script(ROOT / "events/United States.txt", keep_quotes=True)
    return {
        _scalar(body, "id"): body
        for key, _, body in iter_statements(source)
        if key == "country_event"
    }


def _option(events, event_id, option_id):
    return next(
        body
        for key, _, body in iter_statements(events[event_id])
        if key == "option" and _scalar(body, "name") == option_id
    )


def _payments(body, country):
    """Read executable literal treasury transfers, excluding tooltip previews."""
    change = Decimal(0)
    for key, _, block in iter_statements(body):
        if key == "set_temp_variable":
            change = Decimal(_scalar(block, "treasury_change"))
        elif key == "modify_treasury_effect":
            yield country, change
        elif block is not None and len(key) == 3 and key.isupper():
            yield from _payments(block, key)


@pytest.mark.parametrize(
    ("payer", "sudan_exists"),
    [("SUD", True), ("SSU", False), ("AFG", False), ("AFG", True)],
)
def test_acceptance_charges_the_responder_not_a_hardcoded_country(
    cole_events, payer, sudan_exists
):
    balances = {"USA": Decimal(100), "SSU": Decimal(3), "AFG": Decimal(5)}
    if sudan_exists:
        balances["SUD"] = Decimal(7)
    expected = balances.copy()
    expected[payer] -= Decimal("0.25")
    expected["USA"] += Decimal("0.25")

    accept = _option(cole_events, "usa.2000", "usa.2000.o1")
    for country, amount in _payments(accept, payer):
        balances[country] += amount

    assert balances == expected


@pytest.mark.parametrize(
    ("event_id", "option_id"),
    [
        ("usa.2000", "usa.2000.o2"),
        ("usa.2001", "usa.2001.o1"),
        ("usa.2002", "usa.2002.o1"),
    ],
)
def test_refusal_and_notifications_do_not_transfer_money(
    cole_events, event_id, option_id
):
    option = _option(cole_events, event_id, option_id)
    assert list(_payments(option, "USA")) == []


@pytest.mark.parametrize("response", [1, 2])
def test_response_keeps_the_accepting_or_refusing_country_as_sender(
    cole_events, response
):
    option = _option(cole_events, "usa.2000", f"usa.2000.o{response}")
    dispatches = [
        event
        for key, _, block in iter_statements(option)
        if key == "USA"
        for effect, _, event in iter_statements(block)
        if effect == "country_event"
    ]
    assert len(dispatches) == 1
    assert _scalar(dispatches[0], "id") == f"usa.200{response}"
    assert _scalar(dispatches[0], "days") == "1"


def test_compensation_text_names_the_responder_and_not_a_fixed_payer():
    source = (ROOT / "localisation/english/MD_focus_USA_l_english.yml").read_text(
        encoding="utf-8-sig"
    )
    values = dict(
        line.strip().split(": ", 1) for line in source.splitlines() if ": " in line
    )

    assert "Sudan" not in values["usa.2.o2"]
    for key in ("usa.2001.t", "usa.2001.d", "usa.2002.t", "usa.2002.d"):
        assert "[FROM.GetName]" in values[key]
        assert "[From.GetName]" not in values[key]
    assert "has paid" in values["usa.2001.d"]
