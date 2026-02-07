# pylint: disable=missing-function-docstring

"""
Unit tests for hooks/check_badges.py: good and bad notebook examples.

These tests write small notebooks to temporary files and call the
badge-check functions that expect filenames.
"""

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import pytest

from hooks import check_badges as cb


def _write_nb_and_return_path(tmp_path, nb, name="nb.ipynb"):
    p = tmp_path / name
    nbformat.write(nb, str(p))
    return str(p)


def test_good_notebook_header_and_second_cell(tmp_path):
    # arrange
    nb_path = tmp_path / "good.ipynb"
    repo_name = "devops_tests"
    repo_owner = "open-atmos"

    relpath = cb.relative_path(nb_path, tmp_path)
    first_cell = "\n".join(
        [
            cb.preview_badge_markdown(relpath, repo_name, repo_owner),
            cb.mybinder_badge_markdown(relpath, repo_name, repo_owner),
            cb.colab_badge_markdown(relpath, repo_name, repo_owner),
        ]
    )

    # act
    nb = new_notebook(
        cells=[
            new_markdown_cell(first_cell),
            new_markdown_cell("Some description"),
            new_code_cell(source="print('ok')", execution_count=1, outputs=[]),
        ]
    )
    path = _write_nb_and_return_path(tmp_path, nb, name="good.ipynb")

    # assert
    cb.test_notebook_has_at_least_three_cells(path)
    cb.test_first_cell_contains_three_badges(
        path, repo_name, repo_owner, repo_root=tmp_path
    )
    cb.test_second_cell_is_a_markdown_cell(path)


def test_too_few_cells_raises(tmp_path):
    nb = new_notebook(cells=[new_markdown_cell("only one cell")])
    path = _write_nb_and_return_path(tmp_path, nb, name="few.ipynb")
    with pytest.raises(ValueError):
        cb.test_notebook_has_at_least_three_cells(path)


def test_first_cell_bad_badges_raises(tmp_path):
    nb = new_notebook(
        cells=[
            new_markdown_cell("not the right badges\nline2\nline3"),
            new_markdown_cell("desc"),
            new_code_cell(source="print(1)", execution_count=1, outputs=[]),
        ]
    )
    path = _write_nb_and_return_path(tmp_path, nb, name="badbadges.ipynb")
    with pytest.raises(ValueError):
        cb.test_first_cell_contains_three_badges(path, "devops_tests")


def test_second_cell_not_markdown_raises(tmp_path):
    nb = new_notebook(
        cells=[
            new_markdown_cell("badge1\nbadge2\nbadge3"),
            new_code_cell(source="print('I am code')", execution_count=1, outputs=[]),
            new_code_cell(source="print('more')", execution_count=2, outputs=[]),
        ]
    )
    path = _write_nb_and_return_path(tmp_path, nb, name="second_not_md.ipynb")
    with pytest.raises(ValueError):
        cb.test_second_cell_is_a_markdown_cell(path)
