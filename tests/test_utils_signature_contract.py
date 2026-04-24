# pylint: disable=missing-function-docstring

import inspect

from hooks import check_notebooks as cn
from hooks import utils


def test_open_and_test_notebooks_signature_is_stable():
    sig = inspect.signature(utils.open_and_test_notebooks)
    params = list(sig.parameters.keys())
    assert params == ["argv", "test_functions"]


def test_check_notebooks_main_calls_utils_with_matching_keywords(monkeypatch):
    # Keep this contract explicit: imported utility in the hook exposes the same signature.
    assert inspect.signature(utils.open_and_test_notebooks) == inspect.signature(
        cn.open_and_test_notebooks
    )

    observed = {}

    def fake_open_and_test_notebooks(*, argv, test_functions):
        observed["argv"] = argv
        observed["test_functions"] = test_functions
        return 0

    monkeypatch.setattr(cn, "open_and_test_notebooks", fake_open_and_test_notebooks)

    result = cn.main(argv=["tests/examples/good.ipynb"])

    assert result == 0
    assert observed["argv"] == ["tests/examples/good.ipynb"]
    assert observed["test_functions"] == [cn.test_jetbrains_bug_py_66491]