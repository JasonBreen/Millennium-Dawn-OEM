#!/usr/bin/env python3
"""
Clean up legacy and deprecated files from the resources directory.

This script identifies and removes files that are:
1. In directories marked as legacy/deprecated/old/etc.
2. Not referenced by the main mod

Usage:
    python3 tools/cleanup_legacy_resources.py --scan          # Scan for cleanup candidates
    python3 tools/cleanup_legacy_resources.py --list         # List files to be removed
    python3 tools/cleanup_legacy_resources.py --clean       # Remove files (with confirmation)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List

RESOURCES_DIR = Path("resources")

# Directories that should be completely removed (legacy/unused)
REMOVE_DIRS = [
    "AA_graphics_dump",
    "archived-branches",
    "Bird's AI Shit",
    "consolidated-graphics-branch",
    "deprecated-missile-graphics",
    "deprecated-tech-graphics",
    "discarded events and desicions",
    "Dread's Puppet Interaction Shit",
    "Dread's Religion Shit",
    "Dread UAR",
    "GFX Counter Icons",
    "GFX templates",
    "Heastels NATO stuff",
    "Internal Factions",
    "Land combat",
    "misc-graphics",
    "Old Desired Laws",
    "old doctrines",
    "Old MD Tech Icons - Bird Save",
    "Old Tank Builder Icons",
    "Operations",
    "Opinion_modifiers.xlsx",
    "parliament_generator",  # Keep this - it has active content
    "Politics",
    "population_estimator.py",
    "portrait_dump",
    "Power projection",
    "Railroad stuff",
    "Ship_builder.xlsx",
    "sphere of influence stuff",
    "Space Rework",
    "Space System",
    "start up gui",
    "subideologies guide.docx",
    "Subideologies modding.txt",
    "Tech",
    "Trade Rework",
    "unused JAP submod content",
    "User Interface",
    "wagner",
    "Warsaw",
]

# Files that should be kept (whitelist)
KEEP_FILES = {
    "National Content",
    "documentation",
    "OOBs",
    "parliament_generator",
    "2000px-world.png",
    "How_to_get_git_log.txt",
    "List of batallion types.txt",
    "List of triggers and effects 1_9_1.txt",
    "md4_00_graphics.lua",
    "state_category_cheat_sheet.jpg",
    "hoi_mapfont4.dds",
    "hoi_mapfont4.fnt",
    "BRA_gui_scripted_localisation.txt",
    "corporate_history_contract.json",
}

# Patterns that indicate legacy content
LEGACY_PATTERNS = [
    r"\bold\b",
    r"\bdeprecated\b",
    r"\barchived\b",
    r"\bdiscarded\b",
    r"\bbackup\b",
    r"\bdump\b",
    r"\bshit\b",
    r"\brework\b",
    r"\bunused\b",
    r"\blegacy\b",
    r"\btest\b",
    r"\btemplate\b",
]


def should_remove_dir(dir_path: Path) -> bool:
    """Check if a directory should be removed."""
    dir_name = dir_path.name

    # Check if in remove list
    if dir_name in REMOVE_DIRS:
        return True

    # Check if parent is in remove list
    for parent in dir_path.parents:
        if parent == dir_path.parent:
            break
        if parent.name in REMOVE_DIRS:
            return True

    # Check for legacy patterns in name
    for pattern in LEGACY_PATTERNS:
        if re.search(pattern, dir_name, re.IGNORECASE):
            return True

    return False


def should_remove_file(file_path: Path) -> bool:
    """Check if a file should be removed."""
    # Check if in keep list
    if file_path.name in KEEP_FILES or any(
        keep in str(file_path) for keep in KEEP_FILES
    ):
        return False

    # Check if parent should be removed
    for parent in file_path.parents:
        if parent == file_path.parent:
            break
        if should_remove_dir(parent):
            return True

    # Check for legacy patterns in name
    for pattern in LEGACY_PATTERNS:
        if re.search(pattern, file_path.name, re.IGNORECASE):
            return True

    return False


def get_files_to_remove() -> List[Path]:
    """Get list of files to remove."""
    files_to_remove = []

    if not RESOURCES_DIR.exists():
        return files_to_remove

    # First, check directories
    for item in RESOURCES_DIR.iterdir():
        if item.is_dir() and should_remove_dir(item):
            # Add all files in this directory
            for file_path in item.rglob("*"):
                if file_path.is_file():
                    files_to_remove.append(file_path)
        elif item.is_file() and should_remove_file(item):
            files_to_remove.append(item)

    return files_to_remove


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="Clean up legacy files from resources directory"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for files to remove",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all files to be removed",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove files (with confirmation)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without removing",
    )

    args = parser.parse_args()

    files_to_remove = get_files_to_remove()

    if args.scan:
        print("\n" + "=" * 80)
        print("RESOURCES CLEANUP SCAN")
        print("=" * 80)
        print(f"Found {len(files_to_remove)} files to remove")

        total_size = sum(f.stat().st_size for f in files_to_remove)
        print(f"Total size: {format_size(total_size)}")

        # Show by directory
        dir_counts = {}
        for f in files_to_remove:
            dir_name = f.parent.name if f.parent != RESOURCES_DIR else "(root)"
            dir_counts[dir_name] = dir_counts.get(dir_name, 0) + 1

        print("\nFiles by directory:")
        for dir_name, count in sorted(
            dir_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  {dir_name}: {count} files")

        if len(dir_counts) > 10:
            print(f"  ... and {len(dir_counts) - 10} more directories")

        return

    if args.list:
        print("\nFiles to be removed:")
        for f in sorted(files_to_remove):
            rel_path = f.relative_to(RESOURCES_DIR)
            print(f"  {rel_path}")
        print(f"\nTotal: {len(files_to_remove)} files")
        return

    if args.clean:
        if not files_to_remove:
            print("No files to remove.")
            return

        total_size = sum(f.stat().st_size for f in files_to_remove)

        print("\n" + "=" * 80)
        print("RESOURCES CLEANUP")
        print("=" * 80)
        print(
            f"About to remove {len(files_to_remove)} files ({format_size(total_size)})"
        )

        if args.dry_run:
            print("\nDRY RUN - No files will be removed")
            print("\nFiles that would be removed:")
            for f in sorted(files_to_remove)[:20]:
                rel_path = f.relative_to(RESOURCES_DIR)
                print(f"  {rel_path}")
            if len(files_to_remove) > 20:
                print(f"  ... and {len(files_to_remove) - 20} more")
            return

        confirm = (
            input(f"\nRemove these {len(files_to_remove)} files? [y/N]: ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Cancelled.")
            return

        removed_count = 0
        removed_size = 0

        for f in files_to_remove:
            try:
                size = f.stat().st_size
                f.unlink()
                removed_count += 1
                removed_size += size
            except Exception as e:
                print(
                    f"Error removing {f.relative_to(RESOURCES_DIR)}: {e}",
                    file=sys.stderr,
                )

        print(f"\nRemoved {removed_count} files ({format_size(removed_size)})")

        # Also remove empty directories
        removed_dirs = 0
        for dir_path in sorted(RESOURCES_DIR.rglob("*"), reverse=True):
            if dir_path.is_dir():
                try:
                    dir_path.rmdir()
                    removed_dirs += 1
                except OSError:
                    pass  # Directory not empty

        if removed_dirs > 0:
            print(f"Removed {removed_dirs} empty directories")

        return

    if not any([args.scan, args.list, args.clean]):
        parser.print_help()


if __name__ == "__main__":
    main()
