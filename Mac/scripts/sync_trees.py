#!/usr/bin/env python3
"""sync_trees.py - Synchronize root source files to Linux/ and Mac/ trees.

Copies every shared source file from the root directory to both Linux/ and Mac/
subdirectories.  Files that only exist in the root (e.g. figure_cache.py) are
copied too so the platform trees stay complete.

Usage:
    python scripts/sync_trees.py              # preview (dry run)
    python scripts/sync_trees.py --apply      # actually copy
    python scripts/sync_trees.py --check      # exit 1 if any file differs
"""
import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files and non-Python assets that must be byte-identical across all three trees.
SYNC_EXTENSIONS = {".py", ".md", ".txt", ".json", ".toml", ".cfg", ".ini", ".yml", ".yaml"}

# Directories inside root that are NOT platform mirrors (skip them).
SKIP_DIRS = {
    "Linux", "Mac", ".venv", "__pycache__", ".git", "dist", "build",
    "wheels", "release_assets", "tests", "scripts", "docs", ".github",
    "assets", "manuals", "linuxzip", "winzip", "node_modules",
}

TARGETS = [ROOT / "Linux", ROOT / "Mac"]


def _collect_syncable_files() -> list[Path]:
    """Return root-level files that should be mirrored."""
    files: list[Path] = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir():
            continue
        if child.suffix in SYNC_EXTENSIONS:
            files.append(child)
    return files


def sync(apply: bool = False, check: bool = False) -> int:
    files = _collect_syncable_files()
    diffs = 0
    copied = 0
    skipped = 0

    for src in files:
        for target_dir in TARGETS:
            if not target_dir.is_dir():
                continue
            dst = target_dir / src.name
            if dst.exists() and filecmp.cmp(src, dst, shallow=False):
                skipped += 1
                continue
            diffs += 1
            label = "COPY" if apply else "DIFF"
            status = "new" if not dst.exists() else "changed"
            print(f"  [{label}] {src.name} -> {target_dir.name}/ ({status})")
            if apply:
                shutil.copy2(src, dst)
                copied += 1

    print(f"\nSummary: {len(files)} source files, {diffs} differ, {skipped} identical")
    if apply:
        print(f"Copied: {copied} files")
    elif not check:
        if diffs:
            print("Run with --apply to sync.")
    if check and diffs:
        print("ERROR: trees are out of sync", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync root source files to Linux/ and Mac/")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--apply", action="store_true", help="Actually copy files")
    group.add_argument("--check", action="store_true", help="Exit 1 if any file differs")
    args = parser.parse_args()
    return sync(apply=args.apply, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
