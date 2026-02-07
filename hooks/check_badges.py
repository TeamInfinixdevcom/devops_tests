#!/usr/bin/env python3
# pylint: disable=missing-function-docstring
"""
Checks/repairs notebook badge headers.

This version optionally uses Git to discover the repository root (to build
repo-relative notebook URLs) and uses Python's logging module instead of print()
for structured messages.

Behavior:
- By default it will attempt to detect the git repo root (if GitPython is
  installed and the file is in a git working tree) and fall back to Path.cwd().
- Use --no-git to force using Path.cwd().
- Use --repo-root PATH to explicitly set repository root.
- Use --verbose to enable debug logging.

Usage:
    check_badges --repo-name=devops_tests [--repo-owner=open-atmos] [--fix-header]
        [--no-git] [--repo-root PATH] [--verbose] FILES...
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

import nbformat
from nbformat import NotebookNode

from .utils import NotebookTestError

REPO_OWNER_DEFAULT = "open-atmos"


logger = logging.getLogger(__name__)


def relative_path(absolute_path, repo_root):
    """returns a path relative to the repo base (converting backslashes to slashes on Windows)"""
    absolute_path = Path(absolute_path).resolve()
    repo_root = Path(repo_root).resolve()

    try:
        relpath = absolute_path.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(
            f"{absolute_path} is not inside repo root {repo_root}"
        ) from exc

    return relpath.as_posix()


def preview_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    svg_badge_url = (
        "https://img.shields.io/static/v1?"
        + "label=render%20on&logo=github&color=87ce3e&message=GitHub"
    )
    link = f"https://github.com/{repo_owner}/{repo_name}/blob/main/{relpath}"
    return f"[![preview notebook]({svg_badge_url})]({link})"


def mybinder_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    svg_badge_url = "https://mybinder.org/badge_logo.svg"
    link = (
        f"https://mybinder.org/v2/gh/{repo_owner}/{repo_name}.git/main?urlpath=lab/tree/"
        + f"{relpath}"
    )
    return f"[![launch on mybinder.org]({svg_badge_url})]({link})"


def colab_badge_markdown(relpath: str, repo_name: str, repo_owner: str) -> str:
    svg_badge_url = "https://colab.research.google.com/assets/colab-badge.svg"
    link = (
        f"https://colab.research.google.com/github/{repo_owner}/{repo_name}/blob/main/"
        + f"{relpath}"
    )
    return f"[![launch on Colab]({svg_badge_url})]({link})"


def find_repo_root(start_path: Path, prefer_git: bool = True) -> Path:
    """
    Find repository root for the given start_path.

    If prefer_git is True, attempt to use GitPython to locate the repository root
    (searching parent directories). If that fails, fall back to cwd().
    """
    if prefer_git:
        try:
            # Import locally so the module doesn't hard-depend on GitPython at import time
            from git import Repo  # pylint: disable=import-outside-toplevel

            try:
                repo = Repo(start_path, search_parent_directories=True)
                if repo.working_tree_dir:
                    root = Path(repo.working_tree_dir)
                    logger.debug("Discovered git repository root: %s", root)
                    return root
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.debug("Git repo detection failed for %s: %s", start_path, exc)
        except ImportError as exc:
            logger.debug("GitPython not available or import failed: %s", exc)

    cwd = Path.cwd()
    logger.debug("Using current working directory as repo root: %s", cwd)
    return cwd


def expected_badges_for(
    notebook_path: Path,
    repo_name: str,
    repo_owner: str,
    repo_root: Optional[Path] = None,
) -> List[str]:
    """
    Return the canonical badge lines expected for notebook_path.
    If repo_root is provided, attempt to build a relative path from it; otherwise
    find repository root automatically (using find_repo_root).
    """
    if repo_root is None:
        repo_root = find_repo_root(notebook_path)

    if repo_root is None:
        raise ValueError("Could not determine repo root")

    relpath = relative_path(notebook_path, repo_root)
    return [
        preview_badge_markdown(relpath, repo_name, repo_owner),
        mybinder_badge_markdown(relpath, repo_name, repo_owner),
        colab_badge_markdown(relpath, repo_name, repo_owner),
    ]


def read_notebook(path: Path) -> NotebookNode:
    with path.open(encoding="utf8") as fp:
        return nbformat.read(fp, nbformat.NO_CONVERT)


def write_notebook(path: Path, nb: NotebookNode) -> None:
    with path.open("w", encoding="utf8") as fp:
        nbformat.write(nb, fp)


def first_cell_lines(nb: NotebookNode) -> List[str]:
    """Return list of stripped lines from the first cell if it's markdown, else []"""
    if not nb.cells:
        return []
    first = nb.cells[0]
    if first.cell_type != "markdown":
        return []
    return [ln.strip() for ln in str(first.source).splitlines() if ln.strip() != ""]


def badges_match(
    actual_lines: Iterable[str], expected_lines: Iterable[str]
) -> Tuple[bool, str]:
    """
    Check whether the expected badge lines are present in actual_lines.
    Tolerant: ignores order, strips whitespace.
    Returns (matches, message). Message empty on match else explains which badges missing.
    """
    actual_set = {ln.strip() for ln in actual_lines}
    expected_list = list(expected_lines)
    missing = [exp for exp in expected_list if exp.strip() not in actual_set]
    if not missing:
        return True, ""
    return False, f"Missing badges: {missing}"


def test_notebook_has_at_least_three_cells(notebook_filename: str) -> None:
    """checks if all notebooks have at least three cells"""
    nb = read_notebook(Path(notebook_filename))
    if len(nb.cells) < 3:
        raise ValueError("Notebook should have at least 3 cells")


def test_first_cell_contains_three_badges(
    notebook_filename: str,
    repo_name: str,
    repo_owner: str = REPO_OWNER_DEFAULT,
    repo_root: Optional[Path] = None,
) -> None:
    """
    checks if the notebook's first cell contains the three badges.
    Raises ValueError on failure.

    The optional repo_root can be provided to control how the notebook path is
    converted into the remote URL. If None, the module will attempt to detect
    a git repo root and fall back to cwd().
    """
    nb = read_notebook(Path(notebook_filename))
    lines = first_cell_lines(nb)
    expected = expected_badges_for(
        Path(notebook_filename), repo_name, repo_owner, repo_root
    )
    ok, msg = badges_match(lines, expected)
    if not ok:
        raise ValueError(msg)


def test_second_cell_is_a_markdown_cell(notebook_filename: str) -> None:
    """checks if all notebooks have their second cell as markdown"""
    nb = read_notebook(Path(notebook_filename))
    if len(nb.cells) < 2:
        raise ValueError("Notebook has no second cell")
    if nb.cells[1].cell_type != "markdown":
        raise ValueError("Second cell is not a markdown cell")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-name", required=True)
    parser.add_argument("--repo-owner", default=REPO_OWNER_DEFAULT)
    parser.add_argument(
        "--fix-header",
        action="store_true",
        help="If set, attempt to fix notebooks missing the header.",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Do not attempt to detect git repo root; use cwd()",
    )
    parser.add_argument(
        "--repo-root", help="Explicit repository root to use when building URLs"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    # configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    prefer_git = not args.no_git
    repo_root_path: Optional[Path] = Path(args.repo_root) if args.repo_root else None
    retval = 0
    for filename in args.filenames:
        path = Path(filename)
        try:
            effective_repo_root = repo_root_path or (
                find_repo_root(path, prefer_git) if prefer_git else Path.cwd()
            )

            test_notebook_has_at_least_three_cells(filename)
            test_first_cell_contains_three_badges(
                filename, args.repo_name, args.repo_owner, effective_repo_root
            )
            test_second_cell_is_a_markdown_cell(filename)

            logger.info("%s: OK", filename)
            retval = retval or 0
        except NotebookTestError as exc:
            logger.error("%s: %s", filename, exc)
            retval = 1
    return retval


if __name__ == "__main__":
    raise SystemExit(main())
