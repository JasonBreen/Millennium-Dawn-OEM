#!/usr/bin/env python3
"""
Split equipment_l_english.yml into smaller files based on equipment categories.

This script specifically handles the equipment localisation file which is very large.
It splits by equipment type prefixes.
"""

import shutil
import sys
from pathlib import Path
from typing import Dict, Tuple

from split_localisation import (
    format_localisation_value,
    parse_yaml_file,
    remove_incomplete_outputs,
)

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
    return parse_yaml_file(filepath)


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
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            # Write UTF-8 BOM for HOI4 compatibility
            f.write("\ufeffl_english:\n\n")

            # Write header comment
            f.write(f"# Equipment Localisation - {category.capitalize()} Category\n")
            f.write("# Split from equipment_l_english.yml\n\n")

            # Write entries sorted by key
            for key in sorted(entries.keys()):
                value = entries[key]
                f.write(f" {key}: {format_localisation_value(value)}\n")

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
    if not entries:
        print("No entries to split; original file retained.")
        return 0, {}

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
    outputs = [
        output_dir / f"equipment_{category}_l_english.yml"
        for category, cat_entries in categories.items()
        if cat_entries
    ]
    for output_path in outputs:
        if output_path.exists():
            print(
                f"Refusing to overwrite existing output: {output_path}", file=sys.stderr
            )
            return 0, {}

    backup_path = EQUIPMENT_FILE.with_suffix(EQUIPMENT_FILE.suffix + ".backup")
    try:
        shutil.copy2(EQUIPMENT_FILE, backup_path)
        print(f"Backup created: {backup_path.name}")
    except Exception as e:
        print(f"Error: Could not create backup: {e}", file=sys.stderr)
        return 0, {}

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
                remove_incomplete_outputs(outputs)
                return 0, {}

    # Write new master file
    with open(EQUIPMENT_FILE, "w", encoding="utf-8", newline="") as f:
        f.write("\ufeffl_english:\n# Equipment Localisation\n")
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

    dry_run = args.dry_run or not args.apply
    if dry_run:
        print("DRY RUN MODE - No files will be modified\n")

    total_entries, category_counts = split_equipment_file(dry_run)

    if dry_run:
        print(
            f"\n[DRY RUN] Would split {total_entries} entries into {len(category_counts)} category files"
        )
    else:
        print(
            f"\nSplit {total_entries} entries into {len(category_counts)} category files"
        )


if __name__ == "__main__":
    main()
