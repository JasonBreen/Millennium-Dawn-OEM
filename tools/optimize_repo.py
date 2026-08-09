#!/usr/bin/env python3
"""
Millennium Dawn Repository Optimization Tool

Main optimization script that coordinates various optimization tasks:
- Audio compression
- Localisation file splitting
- Resource directory cleanup
- File deduplication

Usage:
    python3 tools/optimize_repo.py --scan              # Scan for optimization opportunities
    python3 tools/optimize_repo.py --apply            # Apply all safe optimizations
    python3 tools/optimize_repo.py --audio            # Optimize audio files only
    python3 tools/optimize_repo.py --localisation     # Optimize localisation files only
    python3 tools/optimize_repo.py --resources        # Clean up resources directory
"""

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
REPO_ROOT = Path(".")
TOOLS_DIR = REPO_ROOT / "tools"


@dataclass
class OptimizationTask:
    name: str
    description: str
    command: List[str]
    estimated_savings: str
    risk_level: str  # "low", "medium", "high"
    requires_confirmation: bool = False


# Define optimization tasks
OPTIMIZATION_TASKS = {
    "audio-compress": OptimizationTask(
        name="Audio Compression",
        description="Compress audio files to reduce size",
        command=[
            sys.executable,
            str(TOOLS_DIR / "assets" / "compress_audio.py"),
            "--dry-run",
        ],
        estimated_savings="400-600MB",
        risk_level="low",
        requires_confirmation=True,
    ),
    "audio-apply": OptimizationTask(
        name="Audio Compression (Apply)",
        description="Apply audio compression",
        command=[
            sys.executable,
            str(TOOLS_DIR / "assets" / "compress_audio.py"),
            "--apply",
        ],
        estimated_savings="400-600MB",
        risk_level="low",
        requires_confirmation=True,
    ),
    "localisation-scan": OptimizationTask(
        name="Localisation Scan",
        description="Scan for large localisation files",
        command=[
            sys.executable,
            str(TOOLS_DIR / "linting" / "split_localisation.py"),
            "--scan",
        ],
        estimated_savings="0MB (organizational)",
        risk_level="low",
        requires_confirmation=False,
    ),
    "resources-scan": OptimizationTask(
        name="Resources Scan",
        description="Scan resources directory for cleanup candidates",
        command=[sys.executable, str(TOOLS_DIR / "resources_cleanup.py"), "--scan"],
        estimated_savings="100-500MB",
        risk_level="low",
        requires_confirmation=False,
    ),
    "resources-archive": OptimizationTask(
        name="Resources Archive Legacy",
        description="Archive legacy files from resources/",
        command=[
            sys.executable,
            str(TOOLS_DIR / "resources_cleanup.py"),
            "--archive-all-legacy",
            "--dry-run",
        ],
        estimated_savings="100-500MB",
        risk_level="medium",
        requires_confirmation=True,
    ),
}


def run_command(command: List[str], dry_run: bool = False) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    if dry_run:
        print(f"  [DRY RUN] Would run: {' '.join(command)}")
        return True, ""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=300,  # 5 minute timeout
        )

        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"

        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except FileNotFoundError as e:
        return False, f"Command not found: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies are installed."""
    missing = []

    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        missing.append("ffmpeg")

    return len(missing) == 0, missing


def scan_optimizations() -> Dict[str, OptimizationTask]:
    """Scan for available optimization opportunities."""
    print("\n" + "=" * 80)
    print("REPOSITORY OPTIMIZATION SCAN")
    print("=" * 80)

    # Check dependencies
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        print(f"\nMissing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install pyyaml")
        print("Install ffmpeg from your package manager")

    print("\nAvailable Optimization Tasks:")
    print("-" * 80)

    for task_id, task in OPTIMIZATION_TASKS.items():
        print(f"\n{task.name}:")
        print(f"  Description: {task.description}")
        print(f"  Estimated savings: {task.estimated_savings}")
        print(f"  Risk level: {task.risk_level}")
        print(f"  Command: {' '.join(task.command)}")

    return OPTIMIZATION_TASKS


def apply_optimization(task_id: str, dry_run: bool = False) -> bool:
    """Apply a specific optimization task."""
    if task_id not in OPTIMIZATION_TASKS:
        print(f"Error: Unknown task '{task_id}'", file=sys.stderr)
        return False

    task = OPTIMIZATION_TASKS[task_id]

    print(f"\nApplying: {task.name}")
    print(f"Description: {task.description}")
    print(f"Estimated savings: {task.estimated_savings}")
    print(f"Risk level: {task.risk_level}")

    if task.requires_confirmation and not dry_run:
        confirm = (
            input(f"\nConfirm {task.name}? This may modify files. [y/N]: ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Cancelled.")
            return False

    # Modify command for dry run
    if dry_run and "--dry-run" not in task.command:
        task_command = task.command + ["--dry-run"]
    else:
        task_command = task.command

    print(f"\nRunning: {' '.join(task_command)}")

    success, output = run_command(task_command, dry_run)

    if output:
        print(f"\nOutput:\n{output}")

    if success:
        print(f"\n{task.name} completed successfully!")
    else:
        print(f"\n{task.name} failed!", file=sys.stderr)

    return success


def apply_all_optimizations(dry_run: bool = False) -> Dict[str, bool]:
    """Apply all safe optimizations."""
    results = {}

    print("\n" + "=" * 80)
    print("APPLYING ALL SAFE OPTIMIZATIONS")
    print("=" * 80)

    # Apply in order of safety (low risk first)
    task_order = [
        "localisation-scan",
        "resources-scan",
        "audio-compress",
    ]

    for task_id in task_order:
        if task_id in OPTIMIZATION_TASKS:
            task = OPTIMIZATION_TASKS[task_id]
            if task.risk_level == "low":
                print(f"\n--- {task.name} ---")
                results[task_id] = apply_optimization(task_id, dry_run)

    return results


def main():
    parser = argparse.ArgumentParser(description="Optimize Millennium Dawn repository")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for optimization opportunities",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply all safe optimizations",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="Optimize audio files",
    )
    parser.add_argument(
        "--localisation",
        action="store_true",
        help="Optimize localisation files",
    )
    parser.add_argument(
        "--resources",
        action="store_true",
        help="Clean up resources directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--task",
        type=str,
        metavar="TASK",
        help="Run a specific optimization task",
    )

    args = parser.parse_args()

    if args.scan:
        scan_optimizations()
        return

    if args.task:
        apply_optimization(args.task, args.dry_run)
        return

    if args.audio:
        apply_optimization("audio-compress", args.dry_run)
        return

    if args.localisation:
        apply_optimization("localisation-scan", args.dry_run)
        return

    if args.resources:
        apply_optimization("resources-scan", args.dry_run)
        return

    if args.apply:
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified\n")
        apply_all_optimizations(args.dry_run)
        return

    if not any(
        [
            args.scan,
            args.apply,
            args.audio,
            args.localisation,
            args.resources,
            args.task,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    main()
