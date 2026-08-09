#!/usr/bin/env python3
"""
Millennium Dawn Resources Directory Cleanup Tool

Identifies and helps remove legacy, deprecated, or unintegrated content
from the resources/ directory.

Usage:
    python3 tools/resources_cleanup.py --scan          # Scan for cleanup candidates
    python3 tools/resources_cleanup.py --list         # List all files in resources/
    python3 tools/resources_cleanup.py --archive     # Archive old content to separate repo
    python3 tools/resources_cleanup.py --clean       # Interactive cleanup
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

RESOURCES_DIR = Path("resources")
ARCHIVE_DIR = Path("resources_archive")

# Patterns that indicate legacy/unintegrated content
LEGACY_PATTERNS = [
    "old",
    "deprecated",
    "archived",
    "discarded",
    "backup",
    "dump",
    "shit",  # e.g., "Bird's AI Shit", "Dread's Puppet Interaction Shit"
    "proof of concept",
    "test",
    "template",
    "rework",
    "unused",
    "legacy",
]

# File extensions that are typically not integrated
UNINTEGRATED_EXTENSIONS = [
    ".xlsx",
    ".docx",
    ".txt",  # Only if not referenced by the mod
    ".jpg",
    ".png",  # Only if not in gfx/
    ".csv",
    ".py",  # Python scripts in resources are likely tools, not mod content
    ".md",
    ".pdf",
]

# Known directories that should be kept
KEEP_DIRS = {
    "National Content",
    "documentation",
    "parliament_generator",
    "OOBs",
}


def get_all_files(directory: Path) -> List[Path]:
    """Get all files in a directory tree."""
    files = []
    if not directory.exists():
        return files

    for item in directory.rglob("*"):
        if item.is_file():
            files.append(item)

    return files


def is_legacy_content(path: Path) -> bool:
    """Check if a path appears to be legacy content."""
    path_str = str(path).lower()

    # Check directory name
    for pattern in LEGACY_PATTERNS:
        if pattern in path_str:
            return True

    # Check parent directory
    for parent in path.parents:
        if parent == path.parent:
            break
        parent_str = str(parent.name).lower()
        for pattern in LEGACY_PATTERNS:
            if pattern in parent_str:
                return True

    return False


def is_unintegrated_file(path: Path) -> bool:
    """Check if a file appears to be unintegrated."""
    if path.suffix.lower() in UNINTEGRATED_EXTENSIONS:
        # Some exceptions
        if path.suffix.lower() == ".txt" and "scripted" in str(path).lower():
            return False
        return True

    return False


def get_file_info(path: Path) -> Dict:
    """Get information about a file."""
    stat = path.stat()

    return {
        "path": path,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "is_legacy": is_legacy_content(path),
        "is_unintegrated": is_unintegrated_file(path),
        "is_keep_dir": any(keep_dir in str(path) for keep_dir in KEEP_DIRS),
    }


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def scan_resources() -> Tuple[List[Dict], Dict]:
    """Scan the resources directory and categorize files."""
    if not RESOURCES_DIR.exists():
        print(f"Directory {RESOURCES_DIR} does not exist.")
        return [], {}

    all_files = get_all_files(RESOURCES_DIR)
    file_infos = [get_file_info(f) for f in all_files]

    # Categorize
    categories = {
        "legacy": [],
        "unintegrated": [],
        "keep": [],
        "unknown": [],
    }

    total_size = 0
    for info in file_infos:
        total_size += info["size"]

        if info["is_keep_dir"]:
            categories["keep"].append(info)
        elif info["is_legacy"]:
            categories["legacy"].append(info)
        elif info["is_unintegrated"]:
            categories["unintegrated"].append(info)
        else:
            categories["unknown"].append(info)

    return file_infos, categories


def print_scan_results(categories: Dict, total_size: int):
    """Print the scan results."""
    print("\n" + "=" * 80)
    print("RESOURCES DIRECTORY SCAN RESULTS")
    print("=" * 80)
    print(f"Total files: {sum(len(v) for v in categories.values())}")
    print(f"Total size: {format_size(total_size)}")
    print()

    for category, files in categories.items():
        if files:
            category_size = sum(f["size"] for f in files)
            print(
                f"{category.upper()} ({len(files)} files, {format_size(category_size)}):"
            )

            # Sort by size (largest first)
            sorted_files = sorted(files, key=lambda x: x["size"], reverse=True)

            for file_info in sorted_files[:10]:  # Show top 10
                rel_path = file_info["path"].relative_to(RESOURCES_DIR)
                print(f"  {rel_path} ({format_size(file_info['size'])})")

            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
            print()


def interactive_cleanup(categories: Dict) -> List[Path]:
    """Interactive cleanup mode."""
    print("\n" + "=" * 80)
    print("INTERACTIVE CLEANUP MODE")
    print("=" * 80)
    print("You will be prompted to delete or archive each file.")
    print("Enter 'd' to delete, 'a' to archive, 'k' to keep, 'q' to quit")
    print()

    to_remove = []
    to_archive = []

    # Process legacy files first
    for file_info in sorted(
        categories["legacy"], key=lambda x: x["size"], reverse=True
    ):
        rel_path = file_info["path"].relative_to(RESOURCES_DIR)
        print(f"\n[LEGACY] {rel_path} ({format_size(file_info['size'])})")
        print(f"  Modified: {file_info['modified'].strftime('%Y-%m-%d')}")

        while True:
            choice = input("  Action [d/a/k/q]: ").strip().lower()
            if choice in ["d", "delete"]:
                to_remove.append(file_info["path"])
                break
            elif choice in ["a", "archive"]:
                to_archive.append(file_info["path"])
                break
            elif choice in ["k", "keep"]:
                break
            elif choice in ["q", "quit"]:
                return to_remove, to_archive
            else:
                print("  Invalid choice. Please enter d, a, k, or q.")

    # Process unintegrated files
    for file_info in sorted(
        categories["unintegrated"], key=lambda x: x["size"], reverse=True
    ):
        rel_path = file_info["path"].relative_to(RESOURCES_DIR)
        print(f"\n[UNINTEGRATED] {rel_path} ({format_size(file_info['size'])})")
        print(f"  Modified: {file_info['modified'].strftime('%Y-%m-%d')}")

        while True:
            choice = input("  Action [d/a/k/q]: ").strip().lower()
            if choice in ["d", "delete"]:
                to_remove.append(file_info["path"])
                break
            elif choice in ["a", "archive"]:
                to_archive.append(file_info["path"])
                break
            elif choice in ["k", "keep"]:
                break
            elif choice in ["q", "quit"]:
                return to_remove, to_archive
            else:
                print("  Invalid choice. Please enter d, a, k, or q.")

    return to_remove, to_archive


def archive_files(files: List[Path]) -> int:
    """Archive files to a separate directory."""
    if not files:
        return 0

    ARCHIVE_DIR.mkdir(exist_ok=True)
    archived = 0

    for filepath in files:
        rel_path = filepath.relative_to(RESOURCES_DIR)
        archive_path = ARCHIVE_DIR / rel_path
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(filepath), str(archive_path))
            archived += 1
            print(f"  Archived: {rel_path}")
        except Exception as e:
            print(f"  Error archiving {rel_path}: {e}", file=sys.stderr)

    return archived


def delete_files(files: List[Path]) -> int:
    """Delete files permanently."""
    if not files:
        return 0

    deleted = 0

    for filepath in files:
        try:
            filepath.unlink()
            deleted += 1
            print(f"  Deleted: {filepath.relative_to(RESOURCES_DIR)}")
        except Exception as e:
            print(
                f"  Error deleting {filepath.relative_to(RESOURCES_DIR)}: {e}",
                file=sys.stderr,
            )

    return deleted


def list_all_files() -> None:
    """List all files in resources directory."""
    if not RESOURCES_DIR.exists():
        print(f"Directory {RESOURCES_DIR} does not exist.")
        return

    all_files = get_all_files(RESOURCES_DIR)

    print("\n" + "=" * 80)
    print("ALL FILES IN RESOURCES DIRECTORY")
    print("=" * 80)
    print(f"Total: {len(all_files)} files")
    print()

    for filepath in sorted(all_files):
        rel_path = filepath.relative_to(RESOURCES_DIR)
        size = filepath.stat().st_size
        print(f"{rel_path} ({format_size(size)})")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up resources directory in Millennium Dawn mod"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan and categorize files in resources/",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all files in resources/",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Interactive cleanup mode",
    )
    parser.add_argument(
        "--archive-all-legacy",
        action="store_true",
        help="Archive all legacy files without prompting",
    )
    parser.add_argument(
        "--delete-all-legacy",
        action="store_true",
        help="Delete all legacy files without prompting (DANGEROUS)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without modifying files",
    )

    args = parser.parse_args()

    if args.list:
        list_all_files()
        return

    # Scan resources
    file_infos, categories = scan_resources()
    total_size = sum(f["size"] for f in file_infos)

    if args.scan:
        print_scan_results(categories, total_size)

        # Print recommendations
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        legacy_size = sum(f["size"] for f in categories["legacy"])
        unintegrated_size = sum(f["size"] for f in categories["unintegrated"])

        if legacy_size > 0:
            print(f"\n1. Archive or delete legacy content ({format_size(legacy_size)})")
            print("   These files appear to be old or deprecated.")

        if unintegrated_size > 0:
            print(f"\n2. Review unintegrated files ({format_size(unintegrated_size)})")
            print("   These files may not be used by the mod.")

        print(f"\n3. Consider moving {KEEP_DIRS} to a separate repository")
        print("   These directories contain useful reference material.")

        return

    if args.archive_all_legacy:
        legacy_files = [f["path"] for f in categories["legacy"]]
        print(f"\nArchiving {len(legacy_files)} legacy files...")

        if args.dry_run:
            print("DRY RUN - No files will be modified")
            for filepath in legacy_files:
                print(f"  Would archive: {filepath.relative_to(RESOURCES_DIR)}")
        else:
            archived = archive_files(legacy_files)
            print(f"\nArchived {archived} files to {ARCHIVE_DIR}")

        return

    if args.delete_all_legacy:
        legacy_files = [f["path"] for f in categories["legacy"]]
        print(
            f"\nWARNING: About to PERMANENTLY DELETE {len(legacy_files)} legacy files!"
        )
        print("This action cannot be undone.")

        if args.dry_run:
            print("DRY RUN - No files will be deleted")
            for filepath in legacy_files:
                print(f"  Would delete: {filepath.relative_to(RESOURCES_DIR)}")
        else:
            confirm = input("Type 'DELETE' to confirm: ").strip()
            if confirm == "DELETE":
                deleted = delete_files(legacy_files)
                print(f"\nDeleted {deleted} files.")
            else:
                print("Deletion cancelled.")

        return

    if args.clean:
        to_remove, to_archive = interactive_cleanup(categories)

        if to_remove:
            print(f"\n\nFiles to DELETE ({len(to_remove)}):")
            for filepath in to_remove:
                print(f"  {filepath.relative_to(RESOURCES_DIR)}")

            if not args.dry_run:
                confirm = (
                    input("\nConfirm deletion of these files? [y/N]: ").strip().lower()
                )
                if confirm == "y":
                    deleted = delete_files(to_remove)
                    print(f"\nDeleted {deleted} files.")

        if to_archive:
            print(f"\n\nFiles to ARCHIVE ({len(to_archive)}):")
            for filepath in to_archive:
                print(f"  {filepath.relative_to(RESOURCES_DIR)}")

            if not args.dry_run:
                confirm = (
                    input("\nConfirm archiving of these files? [y/N]: ").strip().lower()
                )
                if confirm == "y":
                    archived = archive_files(to_archive)
                    print(f"\nArchived {archived} files to {ARCHIVE_DIR}.")

        if args.dry_run:
            print("\nDRY RUN - No files were modified.")

    if not any(
        [
            args.scan,
            args.list,
            args.clean,
            args.archive_all_legacy,
            args.delete_all_legacy,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    main()
