"""Shared file-input contracts for the guard validators, plus guard_scan sanitize and Context."""

import disk_cache
import guard_scan
import pytest
import validate_ai_weight_order
import validate_building_guards
import validate_dynamic_modifier_guards
import validate_influence_calls

_CASES = [
    (
        validate_dynamic_modifier_guards,
        "remove_dynamic_modifier = { modifier = PER_pan_iranist_attack }",
        "remove_dynamic_modifier = { modifier = PER_pan_iranist_attack } is not "
        "guarded by a check that PER_pan_iranist_attack is applied",
        None,
    ),
    (
        validate_influence_calls,
        "every_country = { change_influence_percentage = yes }",
        "change_influence_percentage = yes runs inside every_country without a "
        "per-iteration influence_target; temp variables persist across "
        "iterations, so every pass after the first re-targets the first "
        "iterated country",
        None,
    ),
    (
        validate_ai_weight_order,
        "ai_chance = { modifier = { factor = 0 } modifier = { add = 5 } }",
        "ai_chance adds after a factor = 0 modifier, which brings the zeroed "
        "weight back; move the factor = 0 modifiers last",
        None,
    ),
    (
        validate_building_guards,
        "damage_building = { type = fuel_silo damage = 1 }",
        "damage_building = { type = fuel_silo ... } is not guarded by a check "
        "that fuel_silo exists",
        "unguarded-damage-building",
    ),
]


@pytest.fixture(params=_CASES, ids=[case[0].__name__ for case in _CASES])
def scanner_case(request):
    return request.param


def test_scan_file_reads_and_relativizes_path(tmp_path, monkeypatch, scanner_case):
    scanner, script, message, category = scanner_case
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    target = tmp_path / "events"
    target.mkdir()
    path = target / "Test.txt"
    path.write_text("wrapper = {\n\t" + script + "\n}\n", encoding="utf-8-sig")
    args = (str(path), str(tmp_path) + "/")
    expected = ("events/Test.txt", 2, message)
    if category:
        expected = (category, *expected)
    assert scanner.scan_file(args) == [expected]
    assert scanner.scan_file(args) == [expected]


def test_scan_file_skips_files_without_the_effect(tmp_path, monkeypatch, scanner_case):
    def scanned(*_args):
        raise AssertionError("a file without the effect reached the scan")

    monkeypatch.setattr(disk_cache, "per_file_cached_by_content", scanned)
    path = tmp_path / "quiet.txt"
    path.write_text("focus = { id = TST_focus }\n", encoding="utf-8")
    assert scanner_case[0].scan_file((str(path), str(tmp_path) + "/")) == []


@pytest.mark.parametrize("bad_input", ["missing", "directory", "invalid-utf8"])
def test_read_file_reports_unreadable_input(tmp_path, bad_input):
    path = tmp_path / "broken.txt"
    if bad_input == "directory":
        path.mkdir()
    elif bad_input == "invalid-utf8":
        path.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="Cannot scan"):
        guard_scan.read_file(str(path))


def test_scan_file_reports_unreadable_input(tmp_path, scanner_case):
    with pytest.raises(ValueError, match="Cannot scan"):
        scanner_case[0].scan_file((str(tmp_path / "missing.txt"), str(tmp_path)))


def test_sanitize_empty_string():
    assert guard_scan.sanitize("") == ""


def test_sanitize_plain_script():
    script = (
        "if = {\n"
        "\tlimit = { fuel_silo > 0 }\n"
        "\tdamage_building = { type = fuel_silo damage = 1 }\n"
        "}\n"
    )
    assert guard_scan.sanitize(script) == script


def test_sanitize_full_line_comment_preserves_line_count():
    script = "# This is a comment line\n652 = {\n\tfuel_silo > 0\n}\n"
    sanitized = guard_scan.sanitize(script)
    lines = sanitized.split("\n")
    assert lines[0] == ""
    assert lines[1] == "652 = {"
    assert len(lines) == len(script.split("\n"))


def test_sanitize_inline_comment_stripped():
    script = "fuel_silo > 0 # check if silo present\n"
    sanitized = guard_scan.sanitize(script)
    assert sanitized == "fuel_silo > 0 \n"


def test_sanitize_comment_containing_braces_neutralized():
    script = "# if = { limit = { fuel_silo > 0 } }\n652 = { type = fuel_silo }\n"
    sanitized = guard_scan.sanitize(script)
    assert "if =" not in sanitized
    assert "{" not in sanitized.split("\n")[0]
    assert "652 = { type = fuel_silo }" in sanitized


def test_sanitize_blank_quoted_strings():
    inner = "building_damage = { type = fuel_silo }"
    script = f'log = "{inner}"\n'
    sanitized = guard_scan.sanitize(script)
    expected = f'log = "{" " * len(inner)}"\n'
    assert sanitized == expected
    assert len(sanitized) == len(script)


def test_sanitize_meta_effect_macro_template():
    inner = "[?building_damage_by_missile]"
    script = f'DAM = "{inner}"\n'
    sanitized = guard_scan.sanitize(script)
    expected = f'DAM = "{" " * len(inner)}"\n'
    assert sanitized == expected
    assert len(sanitized) == len(script)


def test_sanitize_quoted_string_with_comment_char():
    inner = "building #1 damage"
    script = f'log = "{inner}"\n'
    sanitized = guard_scan.sanitize(script)
    expected = f'log = "{" " * len(inner)}"\n'
    assert sanitized == expected


def test_sanitize_comment_with_quoted_string():
    script = '# log = "test string"\n652 = { fuel_silo > 0 }\n'
    sanitized = guard_scan.sanitize(script)
    assert sanitized == "\n652 = { fuel_silo > 0 }\n"


def test_sanitize_multiline_quoted_string():
    script = 'text = "line one\nline two"\n'
    sanitized = guard_scan.sanitize(script)
    assert sanitized == 'text = "        \n        "\n'
    assert len(sanitized.split("\n")) == 3


def test_sanitize_escaped_quote_in_string():
    script = 'log = "escaped \\"quote\\" inside"\n'
    sanitized = guard_scan.sanitize(script)
    expected = 'log = "                        "\n'
    assert sanitized == expected
    assert len(sanitized) == len(script)


def test_context_apply():
    ctx0 = guard_scan.Context()
    assert ctx0.present == frozenset()

    # Empty proven set returns same context instance
    ctx1 = ctx0.apply(set())
    assert ctx1 is ctx0

    # Non-empty set returns new Context with union
    ctx2 = ctx0.apply({"fuel_silo"})
    assert ctx2.present == frozenset({"fuel_silo"})

    ctx3 = ctx2.apply({"arms_factory"})
    assert ctx3.present == frozenset({"fuel_silo", "arms_factory"})
