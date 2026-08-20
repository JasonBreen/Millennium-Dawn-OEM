#!/usr/bin/env python3
"""
Millennium Dawn Localisation File Splitter

Splits large localisation YAML files into smaller, more manageable files
based on prefixes or categories.

Usage:
    python3 tools/linting/split_localisation.py --scan              # Scan for large files
    python3 tools/linting/split_localisation.py --split events     # Split events_l_english.yml
    python3 tools/linting/split_localisation.py --split equipment  # Split equipment_l_english.yml
    python3 tools/linting/split_localisation.py --split-all        # Split all large files
"""

import argparse
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
LOCALISATION_DIR = Path("localisation/english")
MAX_FILE_SIZE = 500 * 1024  # 500KB - files larger than this should be split
MAX_LINES = 10000  # Files with more than this many lines should be split

# Known large files and their split strategies
SPLIT_STRATEGIES = {
    "events_l_english.yml": {
        "prefixes": [
            ("md4", "events/md4_"),
            ("generic", "events/generic_"),
            ("israel", "events/israel_"),
            ("USA", "events/usa_"),
            ("RUS", "events/rus_"),
            ("CHI", "events/chi_"),
            ("FRA", "events/fra_"),
            ("ENG", "events/eng_"),
            ("GER", "events/ger_"),
        ],
        "default": "events/other_",
    },
    "equipment_l_english.yml": {
        "prefixes": [
            ("equip_infantry", "equipment/infantry_"),
            ("equip_armor", "equipment/armor_"),
            ("equip_artillery", "equipment/artillery_"),
            ("equip_air", "equipment/air_"),
            ("equip_naval", "equipment/naval_"),
            ("equip_vehicle", "equipment/vehicle_"),
            ("equip_electronics", "equipment/electronics_"),
            ("equip_industry", "equipment/industry_"),
        ],
        "default": "equipment/other_",
    },
    "countries_l_english.yml": {
        "prefixes": [
            ("USA", "countries/north_america_"),
            ("CAN", "countries/north_america_"),
            ("MEX", "countries/north_america_"),
            ("RUS", "countries/europe_"),
            ("ENG", "countries/europe_"),
            ("FRA", "countries/europe_"),
            ("GER", "countries/europe_"),
            ("CHI", "countries/asia_"),
            ("JAP", "countries/asia_"),
            ("IND", "countries/asia_"),
        ],
        "default": "countries/other_",
    },
}


def get_yaml_files(directory: Path) -> List[Path]:
    """Get all YAML localisation files."""
    yaml_files = []
    if not directory.exists():
        return yaml_files

    for filepath in directory.glob("*.yml"):
        if filepath.is_file():
            yaml_files.append(filepath)

    return yaml_files


def get_file_info(filepath: Path) -> Dict:
    """Get information about a YAML file."""
    stat = filepath.stat()

    # Count lines
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
            line_count = len(lines)
    except Exception:
        line_count = 0

    return {
        "path": filepath,
        "size": stat.st_size,
        "lines": line_count,
    }


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def scan_large_files() -> List[Dict]:
    """Scan for large localisation files that should be split."""
    yaml_files = get_yaml_files(LOCALISATION_DIR)
    large_files = []

    for file_info in [get_file_info(f) for f in yaml_files]:
        if file_info["size"] > MAX_FILE_SIZE or file_info["lines"] > MAX_LINES:
            large_files.append(file_info)

    return large_files


def parse_yaml_file(filepath: Path) -> Dict[str, str]:
    """Parse a YAML localisation file into key-value pairs."""
    entries = {}

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return entries

    # Simple YAML parser for localisation files
    # Format: key: "value"
    lines = content.split("\n")
    current_key = None

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#") or line.startswith("l_english:"):
            continue

        # Check for key: value pattern
        if ":" in line:
            # Handle multi-line values
            if line.endswith("\\") or (current_key and not line.startswith(" ")):
                # This is a continuation or a new key
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_key = parts[0].strip()
                    value = parts[1].strip()
                    entries[current_key] = value
            else:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    current_key = parts[0].strip()
                    value = parts[1].strip()
                    entries[current_key] = value
        elif current_key and line.startswith(" ") and line.strip():
            # Continuation of previous value
            if current_key in entries:
                entries[current_key] += " " + line.strip()

    return entries


def categorize_entries(
    entries: Dict[str, str], strategy: Dict
) -> Dict[str, List[Tuple[str, str]]]:
    """Categorize localisation entries based on a split strategy."""
    categories = defaultdict(list)

    for key, value in entries.items():
        categorized = False

        # Check each prefix pattern
        for prefix, category in strategy.get("prefixes", []):
            if key.startswith(prefix):
                categories[category].append((key, value))
                categorized = True
                break

        if not categorized:
            # Use default category
            default_category = strategy.get("default", "other")
            categories[default_category].append((key, value))

    return categories


def write_yaml_file(
    filepath: Path, entries: List[Tuple[str, str]], header: str = None
) -> bool:
    """Write entries to a YAML file."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8", newline="") as f:
            # Write UTF-8 BOM for HOI4 compatibility
            f.write("\ufeff")

            if header:
                f.write(f"# {header}\n")

            f.write("l_english:\n")

            for key, value in sorted(entries):
                # Escape special characters in value
                value_escaped = value.replace('"', '\\"')
                f.write(f' {key}: "{value_escaped}"\n')

        return True
    except Exception as e:
        print(f"Error writing {filepath}: {e}", file=sys.stderr)
        return False


def split_file(
    filepath: Path, strategy: Dict, dry_run: bool = False
) -> Tuple[int, List[Path]]:
    """Split a localisation file based on a strategy."""
    print(f"\nSplitting {filepath.name}...")

    # Parse the file
    entries = parse_yaml_file(filepath)
    print(f"  Found {len(entries)} entries")

    # Categorize entries
    categories = categorize_entries(entries, strategy)
    print(f"  Categorized into {len(categories)} categories")

    created_files = []

    # Write each category to a separate file
    for category, category_entries in categories.items():
        output_path = LOCALISATION_DIR / f"{category}.yml"

        if dry_run:
            print(
                f"  [DRY RUN] Would create: {output_path.name} ({len(category_entries)} entries)"
            )
        else:
            if write_yaml_file(
                output_path, category_entries, f"Split from {filepath.name}"
            ):
                created_files.append(output_path)
                print(
                    f"  Created: {output_path.name} ({len(category_entries)} entries)"
                )
            else:
                print(f"  Failed to create: {output_path.name}")

    # Create a master file that includes all the split files
    if not dry_run:
        master_path = filepath
        backup_path = filepath.with_suffix(filepath.suffix + ".backup")

        # Backup original
        try:
            shutil.copy2(filepath, backup_path)
            print(f"  Backup created: {backup_path.name}")
        except Exception as e:
            print(f"  Warning: Could not create backup: {e}", file=sys.stderr)

        # Write new master file that includes the split files
        with open(master_path, "w", encoding="utf-8", newline="") as f:
            f.write(
                "\ufeff# This file has been split into multiple files for better maintainability\n"
            )
            f.write("# Original file backed up as .backup\n")
            f.write("# Include the following files instead:\n")
            for created_file in created_files:
                f.write(f"#   - {created_file.name}\n")

        print(f"  Updated master file: {master_path.name}")

    return len(entries), created_files


def print_scan_results(large_files: List[Dict]):
    """Print the scan results."""
    print("\n" + "=" * 80)
    print("LARGE LOCALISATION FILES SCAN RESULTS")
    print("=" * 80)
    print(f"Files larger than {format_size(MAX_FILE_SIZE)} or {MAX_LINES} lines:\n")

    for file_info in sorted(large_files, key=lambda x: x["size"], reverse=True):
        rel_path = file_info["path"].relative_to(LOCALISATION_DIR)
        print(f"  {rel_path}")
        print(f"    Size: {format_size(file_info['size'])}")
        print(f"    Lines: {file_info['lines']}")

        # Check if we have a split strategy
        filename = file_info["path"].name
        if filename in SPLIT_STRATEGIES:
            print(
                f"    Split strategy: Available ({len(SPLIT_STRATEGIES[filename]['prefixes'])} prefixes)"
            )
        else:
            print("    Split strategy: None (would need manual configuration)")
        print()


def main():

    parser = argparse.ArgumentParser(
        description="Split large localisation files in Millennium Dawn mod"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for large localisation files",
    )
    parser.add_argument(
        "--split",
        type=str,
        metavar="FILE",
        help="Split a specific file (e.g., 'events' for events_l_english.yml)",
    )
    parser.add_argument(
        "--split-all",
        action="store_true",
        help="Split all files with defined strategies",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List available split strategies",
    )

    args = parser.parse_args()

    if args.list_strategies:
        print("\nAvailable split strategies:")
        print("-" * 40)
        for filename, strategy in SPLIT_STRATEGIES.items():
            print(f"\n{filename}:")
            print(f"  Prefixes: {len(strategy['prefixes'])}")
            for prefix, category in strategy["prefixes"][:5]:
                print(f"    {prefix} -> {category}")
            if len(strategy["prefixes"]) > 5:
                print(f"    ... and {len(strategy['prefixes']) - 5} more")
            print(f"  Default: {strategy['default']}")
        return

    if args.scan:
        large_files = scan_large_files()
        print_scan_results(large_files)

        if not large_files:
            print("No large localisation files found.")

        return

    if args.split:
        filename = args.split
        if not filename.endswith("_l_english.yml"):
            filename += "_l_english.yml"

        filepath = LOCALISATION_DIR / filename

        if not filepath.exists():
            print(f"Error: File {filepath} does not exist.", file=sys.stderr)
            sys.exit(1)

        if filename not in SPLIT_STRATEGIES:
            print(f"Error: No split strategy defined for {filename}.", file=sys.stderr)
            print("Available strategies:", file=sys.stderr)
            for strategy_name in SPLIT_STRATEGIES.keys():
                print(f"  - {strategy_name}", file=sys.stderr)
            sys.exit(1)

        strategy = SPLIT_STRATEGIES[filename]

        if args.dry_run:
            print("DRY RUN MODE - No files will be modified\n")

        entry_count, created_files = split_file(filepath, strategy, args.dry_run)

        if args.dry_run:
            print(
                f"\n[DRY RUN] Would split {entry_count} entries into {len(created_files)} files"
            )
        else:
            print(f"\nSplit {entry_count} entries into {len(created_files)} files")

        return

    if args.split_all:
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified\n")

        total_entries = 0
        total_files = 0

        for filename, strategy in SPLIT_STRATEGIES.items():
            filepath = LOCALISATION_DIR / filename

            if filepath.exists():
                entry_count, created_files = split_file(
                    filepath, strategy, args.dry_run
                )
                total_entries += entry_count
                total_files += len(created_files)
            else:
                print(f"Skipping {filename} (file does not exist)")

        if args.dry_run:
            print(
                f"\n[DRY RUN] Would split {total_entries} entries into {total_files} files"
            )
        else:
            print(f"\nSplit {total_entries} entries into {total_files} files")

        return

    if not any([args.scan, args.split, args.split_all, args.list_strategies]):
        parser.print_help()


if __name__ == "__main__":
    main()
