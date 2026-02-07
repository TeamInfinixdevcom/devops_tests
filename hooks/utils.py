"""
Utils functions to reuse in different parts of the codebase
"""

import os
import pathlib
import argparse
from git import Git
import nbformat


class NotebookTestError(BaseException):
    """Raised when a notebook validation test fails."""


def find_files(path_to_folder_from_project_root=".", file_extension=None):
    """
    Returns all files in a current git repo.
    The list of returned files may be filtered with `file_extension` param.
    """
    all_files = [
        path
        for path in Git(
            Git(path_to_folder_from_project_root).rev_parse("--show-toplevel")
        )
        .ls_files()
        .split("\n")
        if os.path.isfile(path)
    ]
    if file_extension is not None:
        return list(filter(lambda path: path.endswith(file_extension), all_files))

    return all_files


def repo_path():
    """returns absolute path to the repo base (ignoring .git location if in a submodule)"""
    path = pathlib.Path(__file__)
    while not (path.is_dir() and Git(path).rev_parse("--git-dir") == ".git"):
        path = path.parent
    return path


def open_and_test_notebooks(argv, test_functions):
    """Create argparser and run notebook tests"""
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        with open(filename, encoding="utf8") as notebook_file:
            notebook = nbformat.read(notebook_file, nbformat.NO_CONVERT)
            for func in test_functions:
                try:
                    func(notebook)
                except NotebookTestError as e:
                    print(f"{filename} : {e}")
                    retval = 1
    return retval
