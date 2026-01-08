#!/usr/bin/env python3
"""
PR Validation Script
Checks for:
1. PR Size constraints (files changed, lines changed)
2. Potential breaking changes (regex match on public API)
"""

import argparse
import re
import subprocess
import sys


def get_git_diff_stats(base_ref: str) -> tuple[int, int, list[str]]:
    """Get files and lines changed stats."""
    try:
        # Get number of files changed
        cmd_files = ["git", "diff", "--name-only", f"origin/{base_ref}..."]
        result_files = subprocess.run(
            cmd_files, capture_output=True, text=True, check=True
        )
        files = result_files.stdout.strip().splitlines()
        num_files_changed = len(files)

        # Get lines changed (additions + deletions)
        cmd_lines = ["git", "diff", "--stat", f"origin/{base_ref}..."]
        result_lines = subprocess.run(
            cmd_lines, capture_output=True, text=True, check=True
        )
        # Parse last line like " 5 files changed, 10 insertions(+), 5 deletions(-)"
        output_lines = result_lines.stdout.strip().splitlines()
        if not output_lines:
            return 0, 0, []

        last_line = output_lines[-1]
        insertions = 0
        deletions = 0

        # Simple extraction
        ins_match = re.search(r"(\d+) insertion", last_line)
        if ins_match:
            insertions = int(ins_match.group(1))

        del_match = re.search(r"(\d+) deletion", last_line)
        if del_match:
            deletions = int(del_match.group(1))

        total_lines_changed = insertions + deletions

        return num_files_changed, total_lines_changed, files

    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}")
        sys.exit(1)


def check_breaking_changes(base_ref: str, files: list[str]) -> list[str]:
    """Check for potential breaking changes in src/monitoring/metrics files."""
    metrics_files = [f for f in files if f.startswith("src/monitoring/metrics/")]

    if not metrics_files:
        return []

    warnings: list[str] = []

    # Check diff content for specific files
    try:
        cmd_diff = ["git", "diff", f"origin/{base_ref}...", "--"] + metrics_files
        result_diff = subprocess.run(cmd_diff, capture_output=True, text=True)

        # This is very basic signature check - if we see a removed definition
        # It's safer to flag it.
        # Looking for lines starting with "-def " or "-    def "
        for line in result_diff.stdout.splitlines():
            if re.match(r"^\-\s*def\s+", line):
                warnings.append(f"Potential removal of function/method: {line.strip()}")

    except Exception as e:
        print(f"Error checking breaking changes: {e}")

    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate PR constraints")
    parser.add_argument(
        "--base-ref", default="main", help="Base branch ref (e.g., main)"
    )
    parser.add_argument("--max-files", type=int, default=50, help="Max files changed")
    parser.add_argument("--max-lines", type=int, default=1000, help="Max lines changed")
    args = parser.parse_args()

    print(f"🔍 Validating PR against {args.base_ref}...")

    files_count, lines_count, files_list = get_git_diff_stats(args.base_ref)

    print(f"📊 Stats: {files_count} files changed, {lines_count} lines changed")

    # Size Checks
    failed = False
    if files_count > args.max_files:
        print(f"⚠️  Large PR: {files_count} files changed (Limit: {args.max_files})")
        print("   Consider breaking into smaller PRs")
        # We don't fail, just warn usually, unless strict blocking is desired
        # For now, let's just warn to match previous behavior

    if lines_count > args.max_lines:
        print(f"⚠️  Large PR: {lines_count} lines changed (Limit: {args.max_lines})")
        print("   Consider breaking into smaller PRs")

    # Breaking Changes
    breaking_warnings = check_breaking_changes(args.base_ref, files_list)
    if breaking_warnings:
        print("⚠️  Potential breaking changes detected in metrics API:")
        for w in breaking_warnings:
            print(f"   {w}")
        print("   Please document in PR description")

    # Tests check
    code_changed = any(f.startswith("src/") for f in files_list)
    tests_changed = any(f.startswith("tests/") for f in files_list)

    if code_changed and not tests_changed:
        print("❌ Code changes detected in src/ without accompanying tests in tests/")
        failed = True
    elif code_changed:
        print("✅ Tests included")

    # TODO check
    # Check for TODOs in changed python files
    todo_count = 0
    python_files = [f for f in files_list if f.endswith(".py")]
    if python_files:
        try:
            # grep in the changed files
            # Note: This checks the *entire* file content of changed files, not just the diff
            # This matches the previous bash script behavior roughly, but git grep checks checked out files
            cmd = ["git", "grep", "-i", "-E", "TODO|FIXME", "--"] + python_files
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                todos = result.stdout.strip().splitlines()
                todo_count = len(todos)
                if todo_count > 0:
                    print(
                        f"⚠️  Found {todo_count} TODO/FIXME comments in changed files:"
                    )
                    for todo in todos[:5]:  # Show first 5
                        print(f"   {todo}")
                    if todo_count > 5:
                        print(f"   ... and {todo_count - 5} more")
                    print("   Please create issues for TODOs before merging")
        except Exception:
            pass

    if failed:
        sys.exit(1)

    print("✅ PR Validation passed")


if __name__ == "__main__":
    main()
