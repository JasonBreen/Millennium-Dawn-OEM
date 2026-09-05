"""Round-trip and source-preservation checks for the localisation splitters."""

import shutil
import sys

import pytest
import split_equipment_localisation as equipment
import split_localisation as general


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as stream:
        stream.write(text)
    return path


@pytest.fixture
def local_files(tmp_path, monkeypatch):
    monkeypatch.setattr(general, "LOCALISATION_DIR", tmp_path)
    monkeypatch.setattr(equipment, "LOCALISATION_DIR", tmp_path)
    monkeypatch.setattr(
        equipment, "EQUIPMENT_FILE", tmp_path / "equipment_l_english.yml"
    )
    return tmp_path


@pytest.mark.parametrize(
    "parse", [general.parse_yaml_file, equipment.parse_equipment_file]
)
def test_parser_preserves_indented_keys_versions_escapes_and_continuations(
    tmp_path, parse
):
    source = _write(
        tmp_path / "source.yml",
        'l_english:\n # comment\n plain: "A: value"\n'
        '\tversioned:0 "A \\"quote\\" and \\n line"\n'
        ' multiline: "first\n  second"\n\n final: "last"\n',
    )
    assert parse(source) == {
        "plain": '"A: value"',
        "versioned": '0 "A \\"quote\\" and \\n line"',
        "multiline": '"first second"',
        "final": '"last"',
    }


@pytest.mark.parametrize(
    "parse", [general.parse_yaml_file, equipment.parse_equipment_file]
)
def test_parser_reports_unreadable_input_without_entries(tmp_path, capsys, parse):
    assert parse(tmp_path / "missing.yml") == {}
    assert "Error reading" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('"already quoted"', '"already quoted"'),
        ('0 "versioned"', '0 "versioned"'),
        ('12 "a \\"quote\\"" # note', '12 "a \\"quote\\"" # note'),
        ('""', '""'),
        ('raw "quote"', '"raw \\"quote\\""'),
        ("", '""'),
    ],
)
def test_value_serialization_only_quotes_bare_values(value, expected):
    assert general.format_localisation_value(value) == expected


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_writer_round_trip_sorts_keys_and_retains_bom_and_lf(tmp_path, kind):
    entries = {"z": '0 "Version: preserved"', "a": '"Already quoted"'}
    if kind == "general":
        output = tmp_path / "nested" / "test_l_english.yml"
        assert general.write_yaml_file(output, list(entries.items()), "Fixture")
    else:
        output = tmp_path / "equipment_infantry_l_english.yml"
        assert equipment.write_category_file("infantry", entries, tmp_path)
    data = output.read_bytes()
    assert data.startswith(b"\xef\xbb\xbfl_english:\n")
    assert b"\r" not in data
    assert data.index(b" a:") < data.index(b" z:")
    assert general.parse_yaml_file(output) == entries


def test_general_writer_without_optional_header(tmp_path):
    output = tmp_path / "test_l_english.yml"
    assert general.write_yaml_file(output, [("bare", "Text")])
    assert output.read_text(encoding="utf-8-sig") == 'l_english:\n bare: "Text"\n'


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_writer_reports_directory_failure(tmp_path, capsys, kind):
    parent = _write(tmp_path / "not_a_directory", "occupied")
    if kind == "general":
        result = general.write_yaml_file(parent / "test.yml", [("key", '"Value"')])
    else:
        result = equipment.write_category_file("other", {"key": '"Value"'}, parent)
    assert result is False
    assert "Error writing" in capsys.readouterr().err
    assert parent.read_text(encoding="utf-8-sig") == "occupied"


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("H_INFANTRY_WEAPONS_1_desc", "infantry"),
        ("IFV_1_type", "armor"),
        ("anti_air_1", "artillery"),
        ("fighter_1", "air"),
        ("nuclear_submarine_1", "naval"),
        ("construction_1", "industry"),
        ("radar_1", "electronics"),
        ("ICBM_1", "nuclear"),
        ("railway_1", "train"),
        ("unknown_desc_type", "other"),
    ],
)
def test_equipment_category_precedence_and_case(key, expected):
    assert equipment.categorize_entry(key) == expected


def test_general_strategy_uses_first_matching_prefix_and_fallback():
    result = general.categorize_entries(
        {"USA_event": "A", "USA_other": "B", "unmapped": "C"},
        {"prefixes": [("USA_", "specific"), ("USA", "broad")]},
    )
    assert result == {
        "specific": [("USA_event", "A"), ("USA_other", "B")],
        "other": [("unmapped", "C")],
    }


def _prepare_split(directory, kind):
    name = "equipment_l_english.yml" if kind == "equipment" else "events_l_english.yml"
    return _write(
        directory / name,
        'l_english:\n infantry_weapons_1:0 "Rifle"\n unknown: "Other"\n',
    )


def _split(source, kind, dry_run=False):
    if kind == "equipment":
        return equipment.split_equipment_file(dry_run)
    return general.split_file(
        source,
        {
            "prefixes": [("infantry", "parts/infantry_l_english")],
            "default": "parts/other_l_english",
        },
        dry_run,
    )


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_split_preserves_all_entries_and_original_backup(local_files, kind):
    source = _prepare_split(local_files, kind)
    original = source.read_bytes()
    count, result = _split(source, kind)
    assert count == 2
    assert result
    assert source.with_suffix(".yml.backup").read_bytes() == original
    assert source.read_bytes().startswith(b"\xef\xbb\xbfl_english:\n")
    assert "backed up" in source.read_text(encoding="utf-8-sig")
    restored = {}
    for output in local_files.rglob("*.yml"):
        if output != source:
            restored.update(general.parse_yaml_file(output))
    assert restored == {"infantry_weapons_1": '0 "Rifle"', "unknown": '"Other"'}
    assert _split(source, kind)[0] == 0
    assert source.with_suffix(".yml.backup").read_bytes() == original


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_dry_run_reports_outputs_without_changing_any_file(local_files, capsys, kind):
    source = _prepare_split(local_files, kind)
    original = source.read_bytes()
    count, result = _split(source, kind, dry_run=True)
    assert count == 2
    assert result
    assert list(local_files.rglob("*")) == [source]
    assert source.read_bytes() == original
    assert "[DRY RUN] Would create" in capsys.readouterr().out


@pytest.mark.parametrize("kind", ["general", "equipment"])
@pytest.mark.parametrize("failure", ["backup", "child"])
def test_split_failure_never_replaces_original(local_files, monkeypatch, kind, failure):
    source = _prepare_split(local_files, kind)
    original = source.read_bytes()
    if failure == "backup":

        def fail_backup(*args):
            raise OSError("backup unavailable")

        monkeypatch.setattr(shutil, "copy2", fail_backup)
    elif kind == "equipment":
        monkeypatch.setattr(equipment, "write_category_file", lambda *args: False)
    else:
        monkeypatch.setattr(general, "write_yaml_file", lambda *args: False)
    assert _split(source, kind)[0] == 0
    assert source.read_bytes() == original
    if failure == "backup":
        assert list(local_files.iterdir()) == [source]
    else:
        assert source.with_suffix(".yml.backup").read_bytes() == original


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_empty_source_is_not_replaced_or_backed_up(local_files, kind):
    source = _prepare_split(local_files, kind)
    _write(source, "l_english:\n # No localisation entries\n")
    original = source.read_bytes()
    assert _split(source, kind)[0] == 0
    assert source.read_bytes() == original
    assert list(local_files.iterdir()) == [source]


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_split_never_overwrites_existing_category(local_files, capsys, kind):
    source = _prepare_split(local_files, kind)
    output = local_files / (
        "equipment_infantry_l_english.yml"
        if kind == "equipment"
        else "parts/infantry_l_english.yml"
    )
    _write(output, 'l_english:\n independent: "Preserve this"\n')
    snapshots = {path: path.read_bytes() for path in (source, output)}
    assert _split(source, kind)[0] == 0
    assert {path: path.read_bytes() for path in snapshots} == snapshots
    assert not source.with_suffix(".yml.backup").exists()
    assert "Refusing to overwrite" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["general", "equipment"])
def test_split_rolls_back_partial_and_completed_children(
    local_files, monkeypatch, kind
):
    source = _prepare_split(local_files, kind)
    original = source.read_bytes()
    module = equipment if kind == "equipment" else general
    function = "write_category_file" if kind == "equipment" else "write_yaml_file"
    real_write = getattr(module, function)
    calls = 0

    def fail_second(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            return real_write(*args)
        output = (
            local_files / f"equipment_{args[0]}_l_english.yml"
            if kind == "equipment"
            else args[0]
        )
        _write(output, "partial output")
        return False

    monkeypatch.setattr(module, function, fail_second)
    assert _split(source, kind)[0] == 0
    assert calls == 2
    assert source.read_bytes() == original
    assert list(local_files.rglob("*.yml")) == [source]
    assert source.with_suffix(".yml.backup").read_bytes() == original


def test_equipment_missing_source_reports_failure(local_files, capsys):
    assert equipment.split_equipment_file() == (0, {})
    assert "does not exist" in capsys.readouterr().err


def test_file_discovery_and_scan_thresholds(local_files, monkeypatch, capsys):
    small = _write(local_files / "small.yml", "l_english:\n")
    lines = _write(local_files / "events_l_english.yml", "l_english:\n\n\n")
    large = _write(local_files / "large.yml", "l_english:\n" + "x" * 100)
    _write(local_files / "nested" / "ignored.yml", "x" * 100)
    (local_files / "directory.yml").mkdir()
    monkeypatch.setattr(general, "MAX_FILE_SIZE", 50)
    monkeypatch.setattr(general, "MAX_LINES", 2)
    assert set(general.get_yaml_files(local_files)) == {small, lines, large}
    assert general.get_yaml_files(local_files / "missing") == []
    found = general.scan_large_files()
    assert {entry["path"] for entry in found} == {large, lines}
    general.print_scan_results(found)
    output = capsys.readouterr().out
    assert output.index("  large.yml") < output.index("  events_l_english.yml")
    assert "Split strategy: Available" in output
    assert "Split strategy: None" in output


def test_file_info_keeps_size_when_text_cannot_be_decoded(tmp_path):
    source = tmp_path / "broken.yml"
    source.write_bytes(b"\xff\xfe\xff")
    assert general.get_file_info(source) == {"path": source, "size": 3, "lines": 0}


@pytest.mark.parametrize(
    ("size", "expected"),
    [(0, "0.0 B")]
    + [
        (1024**power, f"1.0 {unit}")
        for power, unit in enumerate(("KB", "MB", "GB", "TB"), 1)
    ],
)
def test_size_units(size, expected):
    assert general.format_size(size) == expected


@pytest.mark.parametrize(
    "args", [[], ["--dry-run"], ["--stats"], ["--apply", "--dry-run"]]
)
def test_equipment_cli_previews_unless_apply_is_explicit(
    local_files, monkeypatch, capsys, args
):
    source = _prepare_split(local_files, "equipment")
    original = source.read_bytes()
    monkeypatch.setattr(sys, "argv", ["split-equipment", *args])
    equipment.main()
    assert source.read_bytes() == original
    assert list(local_files.iterdir()) == [source]
    output = capsys.readouterr().out
    assert "Total: 2" in output if "--stats" in args else "DRY RUN" in output


def test_equipment_cli_apply_commits_split(local_files, monkeypatch, capsys):
    source = _prepare_split(local_files, "equipment")
    monkeypatch.setattr(sys, "argv", ["split-equipment", "--apply"])
    equipment.main()
    assert source.with_suffix(".yml.backup").exists()
    assert "Split 2 entries" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ([], "usage:"),
        (["--list-strategies"], "Available split strategies"),
        (["--scan"], "No large localisation files found"),
    ],
)
def test_general_cli_information_modes(
    local_files, monkeypatch, capsys, args, expected
):
    monkeypatch.setattr(sys, "argv", ["split-localisation", *args])
    general.main()
    assert expected in capsys.readouterr().out
    assert list(local_files.iterdir()) == []


@pytest.mark.parametrize("filename", ["missing", "unsupported_l_english.yml"])
def test_general_cli_rejects_missing_or_unconfigured_files(
    local_files, monkeypatch, capsys, filename
):
    if filename.startswith("unsupported"):
        _write(local_files / filename, "l_english:\n")
    monkeypatch.setattr(sys, "argv", ["split-localisation", "--split", filename])
    with pytest.raises(SystemExit, match="1"):
        general.main()
    assert "Error:" in capsys.readouterr().err


@pytest.mark.parametrize("dry_run", [True, False])
@pytest.mark.parametrize("split_all", [True, False])
def test_general_cli_split_and_split_all(
    local_files, monkeypatch, capsys, dry_run, split_all
):
    source = _write(
        local_files / "events_l_english.yml", 'l_english:\n USA_event: "Event"\n'
    )
    original = source.read_bytes()
    args = ["--split-all"] if split_all else ["--split", "events"]
    if dry_run:
        args.append("--dry-run")
    monkeypatch.setattr(sys, "argv", ["split-localisation", *args])
    general.main()
    output = capsys.readouterr().out
    assert (
        "Would split 1 entries into 1 files"
        if dry_run
        else "Split 1 entries into 1 files"
    ) in output
    if split_all:
        assert "Skipping equipment_l_english.yml" in output
    assert (source.read_bytes() == original) is dry_run
    assert source.with_suffix(".yml.backup").exists() is not dry_run
    assert (local_files / "events" / "usa_l_english.yml").exists() is not dry_run
