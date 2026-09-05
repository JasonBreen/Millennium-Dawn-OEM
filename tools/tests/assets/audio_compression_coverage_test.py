"""Exercise media conversion and recovery without running a media executable."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import compress_audio as audio
import pytest


def _media(root, name, payload=b"original media"):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(audio, "MUSIC_DIR", tmp_path / "music")
    monkeypatch.setattr(audio, "SOUND_DIR", tmp_path / "sound")
    monkeypatch.setattr(audio, "BACKUP_DIR", tmp_path / ".audio_backup")
    monkeypatch.setattr(
        audio, "Path", lambda name: tmp_path if name == "." else Path(name)
    )
    return tmp_path


@pytest.fixture(autouse=True)
def forbid_external_media(monkeypatch):
    monkeypatch.setattr(
        audio.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("Unexpected media subprocess"),
    )


def _probe(monkeypatch, stdout="", returncode=0, stderr=""):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)

    monkeypatch.setattr(audio.subprocess, "run", run)
    return calls


def _cli(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["compress_audio.py", *args])
    audio.main()


def test_audio_discovery_filters_nonfiles_and_other_formats(sandbox, capsys):
    expected = {
        _media(sandbox, "music/song.ogg"),
        _media(sandbox, "music/nested/song.mp3"),
        _media(sandbox, "music/theme.flac"),
        _media(sandbox, "music/sample.wav"),
    }
    _media(sandbox, "music/credits.txt")
    (sandbox / "music/not-a-file.ogg").mkdir()
    assert audio.get_audio_files(sandbox / "missing") == []
    music, sound = audio.scan_audio_files()
    assert set(music) == expected and sound == []
    assert "Found 4 music files" in capsys.readouterr().out


@pytest.mark.parametrize(
    "stdout,returncode,expected", [("1\n", 0, True), ("2", 0, False), ("1", 1, False)]
)
def test_mono_probe_stream_and_channel_parsing(
    monkeypatch, stdout, returncode, expected
):
    calls = _probe(monkeypatch, stdout, returncode)
    assert audio.is_mono_audio(Path("fixture.ogg")) is expected
    command, kwargs = calls[0]
    assert command[0] == "ffprobe"
    assert command[command.index("-select_streams") + 1] == "a:0"
    assert command[command.index("-show_entries") + 1] == "stream=channels"
    assert command[-1] == "fixture.ogg"
    assert kwargs == {"capture_output": True, "text": True, "timeout": 10}


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("ffprobe"),
        subprocess.TimeoutExpired("ffprobe", 10),
        PermissionError("denied"),
    ],
)
def test_probes_degrade_safely_on_execution_failure(monkeypatch, error):
    def run(*args, **kwargs):
        raise error

    monkeypatch.setattr(audio.subprocess, "run", run)
    assert not audio.is_mono_audio(Path("fixture.ogg"))
    assert audio.get_audio_info(Path("fixture.ogg")) == ("unknown", "0", 0)


@pytest.mark.parametrize(
    "payload,returncode,expected",
    [
        (
            json.dumps(
                {
                    "format": {
                        "format_name": "ogg",
                        "bit_rate": "128000",
                        "duration": "3.5",
                    }
                }
            ),
            0,
            ("ogg", "128000", 3.5),
        ),
        ("{}", 0, ("unknown", "0", 0)),
        ("not json", 0, ("unknown", "0", 0)),
        ('{"format": {"duration": "N/A"}}', 0, ("unknown", "0", 0)),
        ("", 1, ("unknown", "0", 0)),
    ],
)
def test_audio_metadata_probe_formats_and_malformed_output(
    monkeypatch, payload, returncode, expected
):
    calls = _probe(monkeypatch, payload, returncode)
    assert audio.get_audio_info(Path("fixture.ogg")) == expected
    command, kwargs = calls[0]
    assert (
        command[command.index("-show_entries") + 1]
        == "format=format_name,bit_rate,duration"
    )
    assert command[command.index("-of") + 1] == "json"
    assert kwargs["timeout"] == 10


@pytest.mark.parametrize("mono", [False, True])
@pytest.mark.parametrize("success", [False, True])
def test_converter_uses_explicit_ogg_container_for_temporary_suffix(
    monkeypatch, capsys, mono, success
):
    calls = _probe(
        monkeypatch, returncode=0 if success else 1, stderr="invalid fixture"
    )
    assert (
        audio.compress_audio_file(
            Path("input.ogg"), Path("input.ogg.temp"), "96k", mono
        )
        is success
    )
    command, kwargs = calls[0]
    expected = ["ffmpeg", "-y", "-i", "input.ogg", "-c:a", "libvorbis", "-b:a", "96k"]
    if mono:
        expected += ["-ac", "1"]
    assert command == expected + ["-f", "ogg", "input.ogg.temp"]
    assert kwargs == {"capture_output": True, "text": True, "timeout": 60}
    assert ("FFmpeg error: invalid fixture" in capsys.readouterr().err) is not success


@pytest.mark.parametrize(
    "error,message",
    [
        (FileNotFoundError("ffmpeg"), "FFmpeg not found"),
        (subprocess.TimeoutExpired("ffmpeg", 60), "Timeout compressing"),
    ],
)
def test_converter_execution_errors(monkeypatch, capsys, error, message):
    def run(*args, **kwargs):
        raise error

    monkeypatch.setattr(audio.subprocess, "run", run)
    assert not audio.compress_audio_file(Path("input.ogg"), Path("output.temp"), "128k")
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    "size,expected",
    [
        (0, "0.0 B"),
        (1024, "1.0 KB"),
        (1024**2, "1.0 MB"),
        (1024**3, "1.0 GB"),
        (1024**4, "1.0 TB"),
    ],
)
def test_human_readable_audio_sizes(size, expected):
    assert audio.format_size(size) == expected


def test_backup_keeps_original_across_repeated_compression(sandbox):
    path = _media(sandbox, "music/song.ogg")
    assert audio.create_backup(path, audio.BACKUP_DIR)
    path.write_bytes(b"compressed")
    assert audio.create_backup(path, audio.BACKUP_DIR)
    assert (audio.BACKUP_DIR / "music/song.ogg").read_bytes() == b"original media"
    assert audio.restore_from_backup(path, audio.BACKUP_DIR)
    assert path.read_bytes() == b"original media"
    assert audio.get_file_size(path) == len(b"original media")
    assert audio.get_file_size(sandbox / "missing") == 0


def test_backup_and_restore_failures_leave_sources_untouched(
    sandbox, monkeypatch, capsys
):
    path = _media(sandbox, "music/song.ogg")
    assert not audio.restore_from_backup(path, audio.BACKUP_DIR)

    def copy(*args):
        raise PermissionError("locked fixture")

    monkeypatch.setattr(audio.shutil, "copy2", copy)
    assert not audio.create_backup(path, audio.BACKUP_DIR)
    _media(audio.BACKUP_DIR, "music/song.ogg")
    assert not audio.restore_from_backup(path, audio.BACKUP_DIR)
    assert path.read_bytes() == b"original media"
    output = capsys.readouterr().err
    assert (
        "No backup found" in output
        and "Failed to backup" in output
        and "Failed to restore" in output
    )


@pytest.mark.parametrize("label,expected", [("Music", 600), ("Sound Effects", 480)])
def test_analysis_counts_every_file_but_only_probes_ten(
    sandbox, monkeypatch, capsys, label, expected
):
    paths = [_media(sandbox, f"music/{i:02}.ogg", b"x" * 100) for i in range(12)]
    calls = _probe(monkeypatch, "{}")
    assert audio.analyze_files(paths, label) == (1200, expected)
    assert len(calls) == 20
    assert "2 more files" in capsys.readouterr().out


@pytest.mark.parametrize("mono,expected", [(False, 50), (True, 40)])
def test_compression_dry_run_never_creates_backup_or_output(
    sandbox, monkeypatch, mono, expected
):
    path = _media(sandbox, "music/song.ogg", b"x" * 100)
    calls = _probe(monkeypatch, "{}")
    assert audio.compress_files([path], "96k", mono, True) == (100, expected)
    assert len(calls) == 1 and calls[0][0][0] == "ffprobe"
    assert path.read_bytes() == b"x" * 100
    assert not audio.BACKUP_DIR.exists()
    assert not path.with_suffix(".ogg.temp").exists()


def _conversion(monkeypatch, success=True, payload=b"small"):
    def convert(source, target, bitrate, mono):
        target.write_bytes(payload)
        return success

    monkeypatch.setattr(audio, "compress_audio_file", convert)


def test_successful_compression_replaces_original_with_backup(sandbox, monkeypatch):
    path = _media(sandbox, "sound/effect.wav")
    _conversion(monkeypatch)
    failures = []
    assert audio.compress_files([path], "96k", True, failed_files=failures) == (14, 5)
    assert failures == []
    assert path.read_bytes() == b"small"
    assert (audio.BACKUP_DIR / "sound/effect.wav").read_bytes() == b"original media"
    assert not path.with_suffix(".wav.temp").exists()


@pytest.mark.parametrize("partial_output", [False, True])
def test_failed_conversion_counts_unchanged_file_and_cleans_partial_output(
    sandbox, monkeypatch, partial_output
):
    path = _media(sandbox, "music/song.ogg")
    if partial_output:
        _conversion(monkeypatch, False)
    else:
        monkeypatch.setattr(audio, "compress_audio_file", lambda *args: False)
    failures = []
    assert audio.compress_files([path], "128k", failed_files=failures) == (14, 14)
    assert failures == [path]
    assert path.read_bytes() == b"original media"
    assert (audio.BACKUP_DIR / "music/song.ogg").read_bytes() == b"original media"
    assert not path.with_suffix(".ogg.temp").exists()


def test_failed_backup_prevents_conversion(sandbox, monkeypatch, capsys):
    path = _media(sandbox, "music/song.ogg")
    monkeypatch.setattr(audio, "create_backup", lambda *args: False)
    monkeypatch.setattr(
        audio,
        "compress_audio_file",
        lambda *args: pytest.fail("converted without backup"),
    )
    failures = []
    assert audio.compress_files([path], "128k", failed_files=failures) == (14, 14)
    assert failures == [path] and path.read_bytes() == b"original media"
    assert "backup failed" in capsys.readouterr().out


@pytest.mark.parametrize("existing_backup", [False, True])
def test_replace_failure_preserves_current_source_and_original_backup(
    sandbox, monkeypatch, capsys, existing_backup
):
    current = b"current source B"
    path = _media(sandbox, "music/song.ogg", current)
    backup_path = audio.BACKUP_DIR / "music/song.ogg"
    original = b"first original A" if existing_backup else current
    if existing_backup:
        _media(audio.BACKUP_DIR, "music/song.ogg", original)
    _conversion(monkeypatch)

    def replace(source, target):
        assert source == path.with_suffix(".ogg.temp")
        assert target == path
        raise PermissionError("replacement blocked")

    monkeypatch.setattr(audio.os, "replace", replace)
    failures = []
    assert audio.compress_files([path], "128k", failed_files=failures) == (
        len(current),
        len(current),
    )
    assert failures == [path] and path.read_bytes() == current
    assert backup_path.read_bytes() == original
    assert not path.with_suffix(".ogg.temp").exists()
    assert "Error replacing file" in capsys.readouterr().err


def test_restore_all_recreates_missing_originals(sandbox, capsys):
    assert audio.restore_all_backups() == 0
    assert "No backups found" in capsys.readouterr().out
    _media(audio.BACKUP_DIR, "music/deleted.ogg", b"original")
    assert audio.restore_all_backups() == 1
    assert (sandbox / "music/deleted.ogg").read_bytes() == b"original"


@pytest.mark.parametrize(
    "args", [[], ["--apply"], ["--dry-run"], ["--music-only"], ["--sound-only"]]
)
def test_cli_without_audio_reports_empty_scan(sandbox, monkeypatch, capsys, args):
    calls = _probe(monkeypatch)
    _cli(monkeypatch, args)
    assert calls[0][0] == ["ffmpeg", "-version"]
    assert "No audio files found" in capsys.readouterr().out


def test_cli_missing_ffmpeg_exits_before_modifying_files(sandbox, monkeypatch, capsys):
    path = _media(sandbox, "music/song.ogg")

    def run(*args, **kwargs):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(audio.subprocess, "run", run)
    with pytest.raises(SystemExit) as error:
        _cli(monkeypatch, ["--apply"])
    assert error.value.code == 1 and path.read_bytes() == b"original media"
    assert "ffmpeg is required" in capsys.readouterr().err


@pytest.mark.parametrize("mode", [[], ["--music-only"], ["--sound-only"]])
def test_cli_analysis_selects_media_class(sandbox, monkeypatch, capsys, mode):
    _media(sandbox, "music/song.ogg")
    _media(sandbox, "sound/effect.ogg")
    _probe(monkeypatch, "{}")
    _cli(monkeypatch, mode)
    output = capsys.readouterr().out
    assert ("Music Analysis" in output) is (mode != ["--sound-only"])
    assert ("Sound Effects Analysis" in output) is (mode != ["--music-only"])
    assert not audio.BACKUP_DIR.exists()


@pytest.mark.parametrize(
    "mode", [[], ["--music-only"], ["--sound-only", "--force-mono"]]
)
def test_cli_preview_selects_classes_and_preserves_media(
    sandbox, monkeypatch, capsys, mode
):
    music = _media(sandbox, "music/song.ogg", b"x" * 100)
    sound = _media(sandbox, "sound/effect.ogg", b"x" * 100)
    _probe(monkeypatch, "{}")
    _cli(monkeypatch, ["--dry-run", *mode])
    output = capsys.readouterr().out
    expected = "40.0%" if "--force-mono" in mode else "50.0%"
    assert f"Compression ratio: {expected}" in output
    assert "DRY RUN MODE" in output
    assert music.stat().st_size == sound.stat().st_size == 100
    assert not audio.BACKUP_DIR.exists()


def test_cli_empty_file_has_finite_compression_ratio(sandbox, monkeypatch, capsys):
    _media(sandbox, "music/empty.ogg", b"")
    _probe(monkeypatch, "{}")
    _cli(monkeypatch, ["--dry-run"])
    assert "Compression ratio: 0.0%" in capsys.readouterr().out


@pytest.mark.parametrize("cleanup", [False, True])
def test_cli_successful_apply_respects_backup_cleanup(
    sandbox, monkeypatch, capsys, cleanup
):
    target = _media(sandbox, "music/song.ogg")
    _probe(monkeypatch)
    _conversion(monkeypatch)
    _cli(monkeypatch, ["--apply"] + (["--cleanup"] if cleanup else []))
    assert target.read_bytes() == b"small"
    assert audio.BACKUP_DIR.exists() is not cleanup
    output = capsys.readouterr().out
    assert "Compression complete!" in output
    assert ("Backups saved to" in output) is not cleanup


def test_cli_failed_apply_never_discards_backup(sandbox, monkeypatch, capsys):
    path = _media(sandbox, "music/song.ogg")
    _probe(monkeypatch)
    _conversion(monkeypatch, False)
    _cli(monkeypatch, ["--apply", "--cleanup"])
    assert path.read_bytes() == b"original media"
    assert (audio.BACKUP_DIR / "music/song.ogg").read_bytes() == b"original media"
    output = capsys.readouterr().out
    assert "Compression incomplete: 1 files failed" in output
    assert "Total savings: 0.0 B" in output


@pytest.mark.parametrize("failed_restore", [False, True])
def test_cli_restore_removes_backup_only_after_every_file_restored(
    sandbox, monkeypatch, capsys, failed_restore
):
    path = _media(sandbox, "music/song.ogg", b"compressed")
    _media(audio.BACKUP_DIR, "music/song.ogg", b"original")
    _probe(monkeypatch)
    if failed_restore:
        monkeypatch.setattr(audio, "restore_from_backup", lambda *args: False)
    _cli(monkeypatch, ["--restore"])
    assert path.read_bytes() == (b"compressed" if failed_restore else b"original")
    assert audio.BACKUP_DIR.exists() is failed_restore
    assert f"Restored {0 if failed_restore else 1} files" in capsys.readouterr().out


@pytest.mark.parametrize("mode", ["restore", "apply"])
def test_cli_backup_cleanup_error_is_reported_without_data_loss(
    sandbox, monkeypatch, capsys, mode
):
    target = _media(sandbox, "music/song.ogg")
    _media(audio.BACKUP_DIR, "music/song.ogg")
    _probe(monkeypatch)
    _conversion(monkeypatch)

    def remove(path):
        assert path == audio.BACKUP_DIR
        raise PermissionError("backup directory locked")

    monkeypatch.setattr(audio.shutil, "rmtree", remove)
    _cli(monkeypatch, [f"--{mode}", "--cleanup"])
    assert target.exists() and (audio.BACKUP_DIR / "music/song.ogg").exists()
    assert "Could not remove backup directory" in capsys.readouterr().err
