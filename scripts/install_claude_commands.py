#!/usr/bin/env python3
"""Install or uninstall ai-writer Claude Code slash commands.

Symlinks all .md files from the project's commands/ directory into
~/.claude/commands/, making them available as slash commands in any
Claude Code session.

Usage:
    python scripts/install_claude_commands.py             # install
    python scripts/install_claude_commands.py --uninstall  # remove
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def get_project_commands_dir() -> Path:
    """Return the absolute path to the project's commands/ directory."""
    return Path(__file__).resolve().parent.parent / "commands"


def get_claude_commands_dir() -> Path:
    """Return the absolute path to ~/.claude/commands/."""
    return Path.home() / ".claude" / "commands"


def install(project_dir: Path, claude_dir: Path) -> None:
    """Symlink all .md files from project commands/ into ~/.claude/commands/."""
    claude_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(project_dir.glob("*.md"))
    if not md_files:
        print("No .md files found in commands/ — nothing to install.")
        print("Add command definitions to commands/ and re-run this script.")
        return

    installed = []
    skipped = []

    for src in md_files:
        dest = claude_dir / src.name
        if dest.is_symlink() or dest.exists():
            if dest.is_symlink() and dest.resolve() == src.resolve():
                skipped.append(src.name)
                continue
            else:
                print(f"  WARNING: {dest} already exists and points elsewhere — skipping")
                skipped.append(src.name)
                continue

        os.symlink(src, dest)
        installed.append(src.name)

    if installed:
        print(f"Installed {len(installed)} command(s) into {claude_dir}:")
        for name in installed:
            print(f"  + {name}")
    if skipped:
        print(f"Skipped {len(skipped)} (already present):")
        for name in skipped:
            print(f"  ~ {name}")
    if not installed and not skipped:
        print("Nothing to install.")


def uninstall(project_dir: Path, claude_dir: Path) -> None:
    """Remove symlinks in ~/.claude/commands/ that point back to this project."""
    if not claude_dir.exists():
        print("No ~/.claude/commands/ directory found — nothing to uninstall.")
        return

    md_files = sorted(project_dir.glob("*.md"))
    if not md_files:
        print("No .md files in commands/ — nothing to uninstall.")
        return

    removed = []
    not_found = []

    for src in md_files:
        dest = claude_dir / src.name
        if dest.is_symlink() and dest.resolve() == src.resolve():
            dest.unlink()
            removed.append(src.name)
        else:
            not_found.append(src.name)

    if removed:
        print(f"Removed {len(removed)} command(s) from {claude_dir}:")
        for name in removed:
            print(f"  - {name}")
    else:
        print("No matching symlinks found — nothing to remove.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Install or uninstall ai-writer Claude Code slash commands."
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove previously installed command symlinks.",
    )
    args = parser.parse_args()

    project_dir = get_project_commands_dir()
    claude_dir = get_claude_commands_dir()

    if not project_dir.is_dir():
        print(f"ERROR: commands/ directory not found at {project_dir}", file=sys.stderr)
        sys.exit(1)

    if args.uninstall:
        uninstall(project_dir, claude_dir)
    else:
        install(project_dir, claude_dir)


if __name__ == "__main__":
    main()
