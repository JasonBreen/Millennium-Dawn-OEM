import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPORATE_EFFECTS_PATH = (
    ROOT / "common" / "scripted_effects" / "00_corporate_history_effects.txt"
)
CORPORATE_ON_ACTIONS_PATH = (
    ROOT / "common" / "on_actions" / "01_oem_corporate_history_on_actions.txt"
)
LINUX_ON_ACTIONS_PATH = (
    ROOT / "common" / "on_actions" / "02_linux_system_on_actions.txt"
)
ISR_ON_ACTIONS_PATH = ROOT / "common" / "on_actions" / "99_ISR_on_actions.txt"
ISR_EVENTS_PATH = ROOT / "events" / "ISR_oem_events.txt"
USA_DECISIONS_PATH = (
    ROOT / "common" / "decisions" / "USA_corporate_systems_dashboard.txt"
)


def _blocks(text: str, name: str) -> list[str]:
    pattern = re.compile(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{")
    blocks = []
    for match in pattern.finditer(text):
        depth = 0
        for index in range(text.index("{", match.start()), len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[match.start() : index + 1])
                    break
    return blocks


def _named_block(text: str, name: str) -> str:
    blocks = _blocks(text, name)
    assert blocks, f"missing block {name}"
    return blocks[0]


def test_isr_dispatch_respects_corporate_history_modes():
    effects = CORPORATE_EFFECTS_PATH.read_text(encoding="utf-8")
    yearly = CORPORATE_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    isr_on_actions = ISR_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    events = ISR_EVENTS_PATH.read_text(encoding="utf-8")

    bootstrap = _named_block(effects, "OEM_corporate_history_startup_bootstrap")
    startup = _named_block(effects, "corporate_history_on_startup")
    isr_startup = min(
        (
            block
            for block in _blocks(bootstrap, "if")
            if "country_exists = ISR" in block and "ISR_oem_events.90" in block
        ),
        key=len,
    )
    full = next(
        block
        for block in _blocks(isr_startup, "if")
        if "limit = { corporate_history_full_enabled = yes }" in block
    )
    outcomes_only = next(
        block
        for block in _blocks(isr_startup, "else_if")
        if "limit = { corporate_history_outcomes_only_enabled = yes }" in block
    )

    assert full.count("country_event = ISR_oem_events.90") == 1
    assert "ISR_oem_events.90" not in outcomes_only
    assert "ISR_oem_reconstruct_history = yes" in outcomes_only
    assert "ISR_oem_events.90" not in startup
    assert "ISR_oem_reconstruct_history" not in startup

    event_90 = next(
        block
        for block in _blocks(events, "country_event")
        if "id = ISR_oem_events.90" in block
    )
    immediate = _named_block(event_90, "immediate")
    assert "ISR_oem_reconstruct_history = yes" in immediate
    assert "ISR_oem_schedule_current_year_events = yes" in immediate

    yearly_dispatch = _named_block(yearly, "on_daily_ABK")
    yearly_isr_gate = min(
        (
            block
            for block in _blocks(yearly_dispatch, "if")
            if "ISR_oem_schedule_2001_events = yes" in block
        ),
        key=len,
    )
    assert "corporate_history_full_enabled = yes" in yearly_isr_gate

    daily = _named_block(isr_on_actions, "on_daily_ISR")
    monthly = _named_block(isr_on_actions, "on_monthly_ISR")
    assert "corporate_history_full_enabled = yes" in daily
    assert "ISR_oem_schedule_due_events = yes" in daily
    assert "corporate_history_outcomes_only_enabled = yes" in monthly
    assert "ISR_oem_reconstruct_history = yes" in monthly


def test_abk_hooks_remain_intentional_singleton_dispatchers():
    corporate = CORPORATE_ON_ACTIONS_PATH.read_text(encoding="utf-8")
    linux = LINUX_ON_ACTIONS_PATH.read_text(encoding="utf-8")

    for on_actions in (corporate, linux):
        assert len(_blocks(on_actions, "on_daily_ABK")) == 1
        assert re.search(r"(?m)^\s*on_daily\s*=", on_actions) is None

    assert "limit = { tag = ABK }" in _named_block(corporate, "on_daily_ABK")
    assert "ABK is the date dispatcher only" in linux


def test_usa_policy_visibility_keeps_ibm_outside_recipient_or():
    decisions = USA_DECISIONS_PATH.read_text(encoding="utf-8")
    recipients = {
        "USA_corporate_policy_open_systems_procurement": {
            "USA_apple_state_initialized",
            "USA_nvidia_state_initialized",
        },
        "USA_corporate_policy_domestic_capacity_grants": {
            "USA_apple_state_initialized",
            "USA_nvidia_state_initialized",
            "USA_ti_state_initialized",
            "USA_micron_state_initialized",
            "USA_motorola_state_initialized",
        },
        "USA_corporate_policy_secure_federal_systems": {
            "USA_dell_state_initialized",
            "USA_motorola_state_initialized",
            "USA_google_state_initialized",
        },
        "USA_corporate_policy_advanced_computing_consortium": {
            "USA_nvidia_state_initialized",
            "USA_google_state_initialized",
            "USA_apple_state_initialized",
            "USA_ti_state_initialized",
            "USA_micron_state_initialized",
            "USA_motorola_state_initialized",
        },
    }

    for decision_id, expected_recipients in recipients.items():
        decision = _named_block(decisions, decision_id)
        visible = _named_block(decision, "visible")
        recipient_or = _named_block(visible, "OR")
        flags = set(re.findall(r"has_country_flag = ([A-Za-z0-9_]+)", recipient_or))

        assert visible.count("has_country_flag = USA_ibm_state_initialized") == 1
        assert "USA_ibm_state_initialized" not in flags
        assert flags == expected_recipients
