#!/usr/bin/env python3
"""Delete files ignored by Git according to the repository .gitignore."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List


def run_git(args: List[str], cwd: Path) -> str:
    """Run a git command and return stdout, raising on failure."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        cmd = " ".join(["git", *args])
        raise RuntimeError(f"Failed to run '{cmd}': {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def detect_repo_root(start: Path) -> Path:
    """Return the Git repository root for the given path."""
    stdout = run_git(["rev-parse", "--show-toplevel"], start)
    return Path(stdout.strip())


def list_ignored_files(repo_root: Path) -> List[Path]:
    """Return ignored file paths relative to the repo root."""
    stdout = run_git(["ls-files", "--others", "-i", "--exclude-standard"], repo_root)
    files = []
    for line in stdout.splitlines():
        rel_path = line.strip()
        if not rel_path:
            continue
        candidate = repo_root / rel_path
        if candidate.is_file():
            files.append(candidate)
    return files


def format_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def prompt_confirmation(count: int) -> bool:
    prompt = f"Delete {count} ignored file{'s' if count != 1 else ''}? [y/N]: "
    reply = input(prompt).strip().lower()
    return reply in {"y", "yes"}


def delete_files(paths: Iterable[Path]) -> int:
    deleted = 0
    for path in paths:
        try:
            path.unlink()
            deleted += 1
        except FileNotFoundError:
            continue
        except PermissionError as exc:
            raise RuntimeError(f"Permission denied removing {path!s}") from exc
    return deleted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Delete files ignored by Git in the current working tree."
            " Uses 'git ls-files --others -i --exclude-standard' under the hood."
        )
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path inside the target Git repository (defaults to current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list the files that would be deleted",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        repo_root = detect_repo_root(args.repo.resolve())
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    ignored_files = list_ignored_files(repo_root)

    if not ignored_files:
        print("No ignored files to delete.")
        return 0

    print("Ignored files:")
    for path in ignored_files:
        print(f"  {format_rel(path, repo_root)}")

    if args.dry_run:
        print("Dry run: no files deleted.")
        return 0

    if not args.yes and not prompt_confirmation(len(ignored_files)):
        print("Aborted.")
        return 0

    try:
        deleted = delete_files(ignored_files)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"Deleted {deleted} file{'s' if deleted != 1 else ''}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
