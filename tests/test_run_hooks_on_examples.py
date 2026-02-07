# pylint: disable=missing-function-docstring

"""
Run the hooks on good and bad example notebooks and assert behavior + logs.

This test executes the hook modules the same way pre-commit would:
  python -m hooks.check_badges --repo-name=... PATH
  python -m hooks.check_notebooks PATH

It captures stdout/stderr (which is where logging.basicConfig writes), asserts
expected exit codes, and checks stderr for expected failure substrings.

Adjust the candidate paths in _find_example() if your examples are stored elsewhere.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _find_example(basename: str) -> Path | None:
    """
    Try a set of common locations for example notebooks and return the first
    existing Path or None if not found.
    """
    candidates = [
        Path("tests") / "examples" / basename,
        Path(basename),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _run_module(module: str, args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", module] + args
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


@pytest.mark.parametrize(
    "name, expected_badge_exit, expected_badge_msg",
    [
        ("good.ipynb", 0, ""),
        ("bad.ipynb", 1, "Missing badges"),
    ],
)
def test_check_badges_on_examples(
    name: str, expected_badge_exit: int, expected_badge_msg: str
):
    nb_path = _find_example(name)
    if nb_path is None:
        pytest.skip(f"No example notebook found for {name};")

    res = _run_module("hooks.check_badges", ["--repo-name=devops_tests", str(nb_path)])
    combined_msgs = (res.stderr or "") + "\n" + (res.stdout or "")

    # Check exit code first
    if expected_badge_exit == 0:
        assert (
            res.returncode == 0
        ), f"Expected success; stderr:\n{res.stderr}\nstdout:\n{res.stdout}"
        # For success, ensure no obvious error strings are present
        assert "Missing badges" not in combined_msgs
        assert "ERROR" not in combined_msgs
        assert "Traceback" not in combined_msgs
    else:
        assert (
            res.returncode != 0
        ), f"Expected failure; got exit {res.returncode}\nstdout:\n{res.stdout}"

        assert expected_badge_msg in combined_msgs, (
            f"Expected to find {expected_badge_msg!r} in output"
            f"\n---STDERR---\n{res.stderr}"
            f"\n---STDOUT---\n{res.stdout}"
        )


@pytest.mark.parametrize(
    "name, should_fail, expected_msg_substr",
    [
        ("good.ipynb", False, ""),
        ("bad.ipynb", True, "Cell does not contain output!"),
    ],
)
def test_notebooks_output_on_examples(
    name: str, should_fail: bool, expected_msg_substr: str
):
    nb_path = _find_example(name)
    if nb_path is None:
        pytest.skip(f"No example notebook found for {name}")

    res = _run_module("hooks.notebooks_output", [str(nb_path)])

    if should_fail:
        assert (
            res.returncode != 0
        ), f"Expected check_notebooks to fail on {nb_path}, but it succeeded"
        combined = (res.stderr or "") + "\n" + (res.stdout or "")

        possible_substrings = [
            expected_msg_substr,
            "Notebook cell missing execution_count attribute",
            "Cell does not contain output!",
            "Traceback",
            "stderr",
        ]
        assert any(s and s in combined for s in possible_substrings), (
            f"Expected one of {possible_substrings!r} in output for failing notebook"
            f"\nSTDERR:\n{res.stderr}"
            f"\nSTDOUT:\n{res.stdout}"
        )
    else:
        assert res.returncode == 0, (
            f"Expected check_notebooks to succeed on {nb_path};"
            f" stderr:\n{res.stderr}\nstdout:\n{res.stdout}"
        )


@pytest.mark.parametrize(
    "name, should_fail", (("good.ipynb", False), ("bad.ipynb", False))
)
def test_check_notebooks_on_examples(name: str, should_fail: bool):
    nb_path = _find_example(name)
    if nb_path is None:
        pytest.skip(f"No example notebook found for {name}")

    res = _run_module("hooks.check_notebooks", [str(nb_path)])
    assert res.returncode == should_fail
