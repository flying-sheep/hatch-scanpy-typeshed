"""Test the transform module."""

from __future__ import annotations

import pytest
from mypy.stubdoc import ArgSig, FunctionSig

from hatch_scanpy_typeshed.transform import _check_copy_param


@pytest.mark.parametrize(
    ("args", "expected", "warning"),
    [
        pytest.param(
            [ArgSig("adata", "AnnData"), ArgSig("*"), ArgSig("copy", "bool", default=True)],
            True,
            None,
            id="default",
        ),
        pytest.param(
            [ArgSig("adata", "AnnData"), ArgSig("copy", "bool", default=True)],
            False,
            r"Parameter 'copy' must be a keyword-only argument in function x",
            id="no_star",
        ),
    ],
)
def test_check_copy_param(*, args: list[ArgSig], expected: bool, warning: str | None) -> None:
    sig = FunctionSig("x", args, "AnnData | None")
    if warning is not None:
        with pytest.warns(UserWarning, match=warning):
            assert _check_copy_param(sig) == expected
    else:
        assert _check_copy_param(sig) == expected
