#!/usr/bin/env python3
"""
Checks notebook execution status for Jupyter notebooks"""

from __future__ import annotations

from collections.abc import Sequence
from .utils import open_and_test_notebooks


def test_show_plot_used_instead_of_matplotlib(notebook):
    """checks if plotting is done with open_atmos_jupyter_utils show_plot()"""
    matplot_used = False
    show_plot_used = False
    for cell in notebook.cells:
        if cell.cell_type == "code":
            if "pyplot.show(" in cell.source or "plt.show(" in cell.source:
                matplot_used = True
            if "show_plot(" in cell.source:
                show_plot_used = True
    if matplot_used and not show_plot_used:
        raise ValueError(
            "if using matplotlib, please use open_atmos_jupyter_utils.show_plot()"
        )


def test_show_anim_used_instead_of_matplotlib(notebook):
    """checks if animation generation is done with open_atmos_jupyter_utils show_anim()"""
    matplot_used = False
    show_anim_used = False
    for cell in notebook.cells:
        if cell.cell_type == "code":
            if (
                "funcAnimation" in cell.source
                or "matplotlib.animation" in cell.source
                or "from matplotlib import animation" in cell.source
            ):
                matplot_used = True
            if "show_anim(" in cell.source:
                show_anim_used = True
    if matplot_used and not show_anim_used:
        raise AssertionError("""if using matplotlib for animations,
            please use open_atmos_jupyter_utils.show_anim()""")


def main(argv: Sequence[str] | None = None) -> int:
    """test all notebooks"""
    return open_and_test_notebooks(
        argv=argv,
        test_functions=[
            test_show_anim_used_instead_of_matplotlib,
            test_show_plot_used_instead_of_matplotlib,
        ],
    )


if __name__ == "__main__":
    raise SystemExit(main())
