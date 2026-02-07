#!/usr/bin/env python3
"""checks if notebook is executed and do not contain 'stderr"""

from __future__ import annotations

from collections.abc import Sequence
from .utils import open_and_test_notebooks


def test_cell_contains_output(notebook):
    """checks if all notebook cells have an output present"""
    for cell_idx, cell in enumerate(notebook.cells):
        if cell.cell_type == "code" and cell.source != "":
            if cell.execution_count is None:
                raise ValueError(f"Cell {cell_idx} does not contain output")


def test_no_errors_or_warnings_in_output(notebook):
    """checks if all example Jupyter notebooks have clear std-err output
    (i.e., no errors or warnings) visible; except acceptable
    diagnostics from the joblib package"""
    for cell_idx, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            for output in cell.outputs:
                ot = output.get("output_type")
                if ot == "error":
                    raise ValueError(
                        f"Cell [{cell_idx}] contain error or warning. \n\n"
                        f"Cell [{cell_idx}] output:\n{output}\n"
                    )
                if ot == "stream" and output.get("name") == "stderr":
                    out_text = output.get("text")
                    if out_text and not out_text.startswith("[Parallel(n_jobs="):
                        raise ValueError(f" Cell [{cell_idx}]: {out_text}")


def main(argv: Sequence[str] | None = None) -> int:
    """test all notebooks"""
    return open_and_test_notebooks(
        argv=argv,
        test_functions=[
            test_cell_contains_output,
            test_no_errors_or_warnings_in_output,
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
