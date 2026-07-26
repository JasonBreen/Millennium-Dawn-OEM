#!/usr/bin/env python3
"""
Split equipment_l_english.yml into smaller files based on equipment categories.

This script specifically handles the equipment localisation file which is very large.
It splits by equipment type prefixes.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple

# Configuration
LOCALISATION_DIR = Path("localisation/english")
EQUIPMENT_FILE = LOCALISATION_DIR / "equipment_l_english.yml"

# Equipment categories and their prefixes
EQUIPMENT_CATEGORIES = {
    "infantry": [
        "infantry_weapons",
        "H_infantry_weapons",
        "combat_eng_equipment",
        "cnc_equipment",
        "L_Drone_equipment",
        "land_drone_equipment",
        "UAV_equipment",
        "UGV_equipment",
        "USV_equipment",
        "UUV_equipment",
    ],
    "armor": [
        "light_tank",
        "medium_tank",
        "heavy_tank",
        "super_heavy_tank",
        "modern_tank",
        "tank_destroyer",
        "armored_car",
        "IFV",
        "APC",
        "SPG",
        "SPAA",
        "AAV",
        "MRAV",
    ],
    "artillery": [
        "towed_artillery",
        "self_propelled_artillery",
        "rocket_artillery",
        "anti_tank",
        "anti_air",
        "infantry_AT",
        "infantry_AA",
    ],
    "air": [
        "fighter",
        "heavy_fighter",
        "jet_fighter",
        "bomber",
        "tactical_bomber",
        "strategic_bomber",
        "naval_bomber",
        "CAS",
        "transport_plane",
        "helicopter",
        "attack_helicopter",
        "transport_helicopter",
        "scout_helicopter",
        "UCAV",
    ],
    "naval": [
        "battleship",
        "battlecruiser",
        "carrier",
        "heavy_cruiser",
        "light_cruiser",
        "destroyer",
        "submarine",
        "nuclear_submarine",
        "missile_submarine",
        "torpedo_boat",
        "missile_boat",
        "patrol_boat",
        "amphibious",
    ],
    "industry": [
        "industrial_equipment",
        "construction",
        "infrastructure",
        "supply",
        "repair",
        "maintenance",
    ],
    "electronics": [
        "radar",
        "sonar",
        "computer",
        "sensor",
        "electronic_warfare",
        "jamming",
        "decryption",
    ],
    "nuclear": [
        "nuclear",
        "atomic",
        "thermonuclear",
        "missile",
        "rocket",
        "ballistic",
        "cruise_missile",
        "ICBM",
        "SLBM",
        "IRBM",
        "SRBM",
    ],
    "train": [
        "train_equipment",
        "railway",
        "locomotive",
    ],
    "other": [],  # Default category
}


def parse_equipment_file(filepath: Path) -> Dict[str, str]:
    """Parse the equipment localisation file."""
    entries = {}

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return entries

    # Remove BOM if present
    if content.startswith("\ufeff"):
        content = content[1:]

    # Split by lines
    lines = content.split("\n")

    current_key = None
    in_multiline = False
    multiline_value = ""

    for line in lines:
        line = line.rstrip()  # Remove trailing whitespace

        # Skip empty lines and comments
        if not line or line.startswith("#") or line.startswith("l_english:"):
            if in_multiline:
                # Save the multiline value
                if current_key:
                    entries[current_key] = multiline_value.strip()
                current_key = None
                in_multiline = False
                multiline_value = ""
            continue

        # Check for key: value pattern
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            # This is a new key
            if in_multiline:
                # Save the previous multiline value
                if current_key:
                    entries[current_key] = multiline_value.strip()

            parts = line.split(":", 1)
            current_key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""

            # Check if value continues on next line
            if value.endswith("\\") or (value and value[0] == '"' and value[-1] != '"'):
                in_multiline = True
                multiline_value = value
            else:
                entries[current_key] = value
                current_key = None
                in_multiline = False
        elif in_multiline and current_key:
            # Continuation of multiline value
            multiline_value += " " + line.strip()
        elif current_key and line.startswith(" ") and line.strip():
            # This might be a continuation
            if current_key in entries:
                entries[current_key] += " " + line.strip()

    # Save any remaining multiline value
    if in_multiline and current_key:
        entries[current_key] = multiline_value.strip()

    return entries


def categorize_entry(key: str) -> str:
    """Categorize an entry based on its key prefix."""
    key_lower = key.lower()

    for category, prefixes in EQUIPMENT_CATEGORIES.items():
        for prefix in prefixes:
            if key_lower.startswith(prefix.lower()):
                return category

    # Check for _desc suffix (belongs to same category as base key)
    if key.endswith("_desc"):
        base_key = key[:-5]  # Remove _desc
        return categorize_entry(base_key)

    # Check for _type suffix
    if key.endswith("_type"):
        base_key = key[:-5]  # Remove _type
        return categorize_entry(base_key)

    return "other"


def write_category_file(
    category: str, entries: Dict[str, str], output_dir: Path
) -> bool:
    """Write a category file."""
    output_path = output_dir / f"equipment_{category}_l_english.yml"

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            # Write UTF-8 BOM for HOI4 compatibility
            f.write("\ufeffl_english:\n\n")

            # Write header comment
            f.write(f"# Equipment Localisation - {category.capitalize()} Category\n")
            f.write("# Split from equipment_l_english.yml\n\n")

            # Write entries sorted by key
            for key in sorted(entries.keys()):
                value = entries[key]
                # Escape quotes in value
                value_escaped = value.replace('"', '\\"')
                # Ensure value is quoted
                if not (value.startswith('"') and value.endswith('"')):
                    value_escaped = f'"{value_escaped}"'
                f.write(f" {key}: {value_escaped}\n")

        return True
    except Exception as e:
        print(f"Error writing {output_path}: {e}", file=sys.stderr)
        return False


def split_equipment_file(dry_run: bool = False) -> Tuple[int, Dict[str, int]]:
    """Split the equipment localisation file."""
    if not EQUIPMENT_FILE.exists():
        print(f"Error: {EQUIPMENT_FILE} does not exist.", file=sys.stderr)
        return 0, {}

    print(f"Parsing {EQUIPMENT_FILE}...")
    entries = parse_equipment_file(EQUIPMENT_FILE)
    print(f"Found {len(entries)} entries")

    # Categorize entries
    categories = {cat: {} for cat in EQUIPMENT_CATEGORIES.keys()}

    for key, value in entries.items():
        category = categorize_entry(key)
        categories[category][key] = value

    # Print category statistics
    print("\nCategory Distribution:")
    for category, cat_entries in sorted(categories.items()):
        print(f"  {category}: {len(cat_entries)} entries")

    if dry_run:
        print("\n[DRY RUN] Would create the following files:")
        for category, cat_entries in sorted(categories.items()):
            if cat_entries:
                print(
                    f"  equipment_{category}_l_english.yml ({len(cat_entries)} entries)"
                )
        return len(entries), {cat: len(ents) for cat, ents in categories.items()}

    # Create output directory
    output_dir = LOCALISATION_DIR

    # Write each category file
    created_files = []
    for category, cat_entries in sorted(categories.items()):
        if cat_entries:
            if write_category_file(category, cat_entries, output_dir):
                created_files.append(f"equipment_{category}_l_english.yml")
                print(
                    f"Created: equipment_{category}_l_english.yml ({len(cat_entries)} entries)"
                )
            else:
                print(f"Failed to create: equipment_{category}_l_english.yml")

    # Create a master file that includes all the split files
    backup_path = EQUIPMENT_FILE.with_suffix(EQUIPMENT_FILE.suffix + ".backup")

    # Backup original
    try:
        import shutil

        shutil.copy2(EQUIPMENT_FILE, backup_path)
        print(f"Backup created: {backup_path.name}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}", file=sys.stderr)

    # Write new master file
    with open(EQUIPMENT_FILE, "w", encoding="utf-8") as f:
        f.write("\ufeff# Equipment Localisation\n")
        f.write(
            "# This file has been split into multiple category files for better maintainability.\n"
        )
        f.write("# Original file backed up as equipment_l_english.yml.backup\n")
        f.write("#\n")
        f.write(
            "# To use the split files, include them in your mod's localisation loading order:\n"
        )
        for created_file in created_files:
            f.write(f"#   - {created_file}\n")
        f.write("\n")
        f.write("# The following files were created:\n")
        for category in sorted(categories.keys()):
            if categories[category]:
                f.write(
                    f"#   - equipment_{category}_l_english.yml ({len(categories[category])} entries)\n"
                )

    print(f"Updated master file: {EQUIPMENT_FILE.name}")

    return len(entries), {cat: len(ents) for cat, ents in categories.items()}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Split equipment_l_english.yml into category files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the split",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show category statistics only",
    )

    args = parser.parse_args()

    if args.stats:
        entries = parse_equipment_file(EQUIPMENT_FILE)
        categories = {cat: {} for cat in EQUIPMENT_CATEGORIES.keys()}

        for key, value in entries.items():
            category = categorize_entry(key)
            categories[category][key] = value

        print("Category Statistics:")
        print("-" * 40)
        for category, cat_entries in sorted(categories.items()):
            print(f"{category}: {len(cat_entries)} entries")

        print(f"\nTotal: {len(entries)} entries")
        return

    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    total_entries, category_counts = split_equipment_file(args.dry_run)

    if args.dry_run:
        print(
            f"\n[DRY RUN] Would split {total_entries} entries into {len(category_counts)} category files"
        )
    else:
        print(
            f"\nSplit {total_entries} entries into {len(category_counts)} category files"
        )


if __name__ == "__main__":
    main()
