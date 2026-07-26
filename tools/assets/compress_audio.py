#!/usr/bin/env python3
"""
Millennium Dawn Audio Compression Tool

Compresses audio files to reduce repository size while maintaining acceptable quality.
- Music: Convert to 128kbps OGG (from typically 192-320kbps)
- Sound Effects: Convert to 96kbps OGG mono (from typically 192-320kbps stereo)

Usage:
    python3 tools/assets/compress_audio.py --dry-run    # Preview changes
    python3 tools/assets/compress_audio.py --apply     # Apply compression
    python3 tools/assets/compress_audio.py --restore   # Restore from backups
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Configuration
MUSIC_DIR = Path("music")
SOUND_DIR = Path("sound")
BACKUP_DIR = Path(".audio_backup")

# Target bitrates
MUSIC_BITRATE = "128k"  # 128kbps for music
SFX_BITRATE = "96k"  # 96kbps for sound effects

# File extensions to process
AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3", ".flac"}


def get_audio_files(directory: Path) -> List[Path]:
    """Find all audio files in a directory tree."""
    audio_files = []
    if not directory.exists():
        return audio_files

    for ext in AUDIO_EXTENSIONS:
        audio_files.extend(directory.rglob(f"*{ext}"))

    return [f for f in audio_files if f.is_file()]


def is_mono_audio(filepath: Path) -> bool:
    """Check if an audio file is mono using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=channels",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            channels = result.stdout.strip()
            return channels == "1"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return False


def get_audio_info(filepath: Path) -> Tuple[str, str, int]:
    """Get audio format, bitrate, and duration."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=format_name,bit_rate,duration",
                "-of",
                "json",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)
            format_info = data.get("format", {})
            return (
                format_info.get("format_name", "unknown"),
                format_info.get("bit_rate", "0"),
                float(format_info.get("duration", "0")),
            )
    except Exception:
        pass
    return ("unknown", "0", 0)


def compress_audio_file(
    input_path: Path,
    output_path: Path,
    bitrate: str,
    force_mono: bool = False,
) -> bool:
    """Compress an audio file using ffmpeg."""
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output
        "-i",
        str(input_path),
        "-c:a",
        "libvorbis",  # Use Vorbis codec for OGG
        "-b:a",
        bitrate,
    ]

    if force_mono:
        cmd.extend(["-ac", "1"])  # Force mono

    cmd.append(str(output_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return True
        else:
            print(f"  FFmpeg error: {result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"  Timeout compressing {input_path.name}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("  FFmpeg not found. Please install ffmpeg.", file=sys.stderr)
        return False


def create_backup(filepath: Path, backup_dir: Path) -> bool:
    """Create a backup of a file."""
    backup_path = backup_dir / filepath.relative_to(Path("."))
    backup_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copy2(filepath, backup_path)
        return True
    except Exception as e:
        print(f"  Failed to backup {filepath}: {e}", file=sys.stderr)
        return False


def restore_from_backup(filepath: Path, backup_dir: Path) -> bool:
    """Restore a file from backup."""
    backup_path = backup_dir / filepath.relative_to(Path("."))

    if not backup_path.exists():
        print(f"  No backup found for {filepath}", file=sys.stderr)
        return False

    try:
        shutil.copy2(backup_path, filepath)
        return True
    except Exception as e:
        print(f"  Failed to restore {filepath}: {e}", file=sys.stderr)
        return False


def get_file_size(filepath: Path) -> int:
    """Get file size in bytes."""
    return filepath.stat().st_size if filepath.exists() else 0


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def scan_audio_files() -> Tuple[List[Path], List[Path]]:
    """Scan for audio files in music and sound directories."""
    music_files = get_audio_files(MUSIC_DIR)
    sound_files = get_audio_files(SOUND_DIR)

    print(f"Found {len(music_files)} music files in {MUSIC_DIR}")
    print(f"Found {len(sound_files)} sound files in {SOUND_DIR}")

    return music_files, sound_files


def analyze_files(files: List[Path], label: str) -> Tuple[int, int]:
    """Analyze audio files and estimate savings."""
    total_original = 0
    total_compressed = 0

    print(f"\n{label} Analysis:")
    print("-" * 60)

    for filepath in sorted(files)[:10]:  # Show first 10 as sample
        size = get_file_size(filepath)
        total_original += size

        # Estimate compressed size (rough estimate: 50% reduction for music, 60% for SFX)
        if label == "Music":
            estimated_compressed = int(size * 0.5)
        else:
            estimated_compressed = int(size * 0.4)
        total_compressed += estimated_compressed

        fmt, bitrate, duration = get_audio_info(filepath)
        is_mono = is_mono_audio(filepath)

        print(f"  {filepath.relative_to(Path('.'))}")
        print(
            f"    Size: {format_size(size)}, Format: {fmt}, Bitrate: {bitrate}, Mono: {is_mono}"
        )

    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")

    print(f"\n  Total original size: {format_size(total_original)}")
    print(f"  Estimated compressed size: {format_size(total_compressed)}")
    print(f"  Estimated savings: {format_size(total_original - total_compressed)}")

    return total_original, total_compressed


def compress_files(
    files: List[Path],
    bitrate: str,
    force_mono: bool = False,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Compress a list of audio files."""
    total_original = 0
    total_compressed = 0
    processed = 0

    for filepath in files:
        original_size = get_file_size(filepath)
        total_original += original_size

        # Create temp output path
        temp_path = filepath.with_suffix(filepath.suffix + ".temp")

        if dry_run:
            fmt, bitrate_orig, duration = get_audio_info(filepath)
            estimated_compressed = (
                int(original_size * 0.4) if force_mono else int(original_size * 0.5)
            )
            total_compressed += estimated_compressed

            print(f"  [DRY RUN] {filepath.relative_to(Path('.'))}")
            print(
                f"    Original: {format_size(original_size)}, Estimated: {format_size(estimated_compressed)}"
            )
            processed += 1
            continue

        # Create backup
        if not create_backup(filepath, BACKUP_DIR):
            print(f"  Skipping {filepath} (backup failed)")
            continue

        # Compress
        print(f"  Compressing {filepath.relative_to(Path('.'))}...")
        if compress_audio_file(filepath, temp_path, bitrate, force_mono):
            # Replace original with compressed version
            try:
                os.replace(temp_path, filepath)
                compressed_size = get_file_size(filepath)
                total_compressed += compressed_size
                savings = original_size - compressed_size
                print(
                    f"    Done: {format_size(original_size)} -> {format_size(compressed_size)} (-{format_size(savings)})"
                )
                processed += 1
            except Exception as e:
                print(f"    Error replacing file: {e}", file=sys.stderr)
                # Restore from backup
                restore_from_backup(filepath, BACKUP_DIR)
        else:
            print(f"    Failed to compress {filepath}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()

    return total_original, total_compressed


def restore_all_backups() -> int:
    """Restore all files from backups."""
    if not BACKUP_DIR.exists():
        print("No backups found to restore.")
        return 0

    restored = 0
    for backup_file in BACKUP_DIR.rglob("*"):
        if backup_file.is_file():
            relative_path = backup_file.relative_to(BACKUP_DIR)
            original_path = Path(".") / relative_path

            if original_path.exists():
                if restore_from_backup(original_path, BACKUP_DIR):
                    restored += 1
                    print(f"  Restored: {relative_path}")

    return restored


def main():
    parser = argparse.ArgumentParser(
        description="Compress audio files in Millennium Dawn mod"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply compression to files",
    )
    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore files from backups",
    )
    parser.add_argument(
        "--music-only",
        action="store_true",
        help="Only process music files",
    )
    parser.add_argument(
        "--sound-only",
        action="store_true",
        help="Only process sound files",
    )
    parser.add_argument(
        "--force-mono",
        action="store_true",
        help="Force mono for all sound effects",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove backup directory after successful compression",
    )

    args = parser.parse_args()

    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        print("Error: ffmpeg is required but not found.", file=sys.stderr)
        print("Please install ffmpeg:", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg", file=sys.stderr)
        print("  macOS: brew install ffmpeg", file=sys.stderr)
        print("  Windows: Download from https://ffmpeg.org/", file=sys.stderr)
        sys.exit(1)

    # Scan for files
    music_files, sound_files = scan_audio_files()

    if args.restore:
        print("\nRestoring files from backups...")
        restored = restore_all_backups()
        print(f"\nRestored {restored} files.")

        # Clean up backup directory
        if BACKUP_DIR.exists():
            try:
                shutil.rmtree(BACKUP_DIR)
                print("Backup directory removed.")
            except Exception as e:
                print(
                    f"Warning: Could not remove backup directory: {e}", file=sys.stderr
                )

        return

    # Determine which files to process
    files_to_process = []
    label = ""

    if args.music_only:
        files_to_process = music_files
        label = "Music"
    elif args.sound_only:
        files_to_process = sound_files
        label = "Sound Effects"
    else:
        files_to_process = music_files + sound_files
        label = "All Audio"

    if not files_to_process:
        print("No audio files found to process.")
        return

    # Analyze if dry run or apply
    if args.dry_run or args.apply:
        print(f"\nProcessing {label} files...")
        print("=" * 60)

        if args.dry_run:
            print("DRY RUN MODE - No files will be modified\n")

        # Process music files
        if not args.sound_only:
            print("\nProcessing Music Files:")
            print("-" * 60)
            orig, comp = compress_files(
                music_files,
                MUSIC_BITRATE,
                force_mono=False,
                dry_run=args.dry_run,
            )
            music_savings = orig - comp
        else:
            orig, comp, music_savings = 0, 0, 0

        # Process sound files
        if not args.music_only:
            print("\nProcessing Sound Effect Files:")
            print("-" * 60)
            orig_sfx, comp_sfx = compress_files(
                sound_files,
                SFX_BITRATE,
                force_mono=args.force_mono,
                dry_run=args.dry_run,
            )
            sfx_savings = orig_sfx - comp_sfx
        else:
            orig_sfx, comp_sfx, sfx_savings = 0, 0, 0

        total_original = orig + orig_sfx
        total_compressed = comp + comp_sfx
        total_savings = music_savings + sfx_savings

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total original size: {format_size(total_original)}")
        print(f"Total compressed size: {format_size(total_compressed)}")
        print(f"Total savings: {format_size(total_savings)}")
        print(f"Compression ratio: {total_compressed / total_original * 100:.1f}%")

        if args.apply and not args.dry_run:
            print("\nCompression complete!")

            # Clean up backups if requested
            if args.cleanup and BACKUP_DIR.exists():
                try:
                    shutil.rmtree(BACKUP_DIR)
                    print("Backup directory removed (as requested).")
                except Exception as e:
                    print(
                        f"Warning: Could not remove backup directory: {e}",
                        file=sys.stderr,
                    )
            else:
                print(f"\nBackups saved to: {BACKUP_DIR}")
                print(
                    "To restore original files, run: python3 tools/assets/compress_audio.py --restore"
                )
    else:
        # Just analyze
        if not args.sound_only:
            analyze_files(music_files, "Music")
        if not args.music_only:
            analyze_files(sound_files, "Sound Effects")


if __name__ == "__main__":
    main()
