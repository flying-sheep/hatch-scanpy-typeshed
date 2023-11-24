"""Test the generate module."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from mypy.stubgen import StubSource, generate_asts_for_modules, mypy_options, parse_options

from hatch_scanpy_typeshed.generate import generate_stub_for_py_module

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        pytest.param(
            """\
            from anndata import AnnData

            def example(adata: AnnData, *, copy: bool = False) -> AnnData | None:
                print(copy)
            """,
            """\
            from anndata import AnnData
            from typing import Literal, overload

            @overload
            def example(adata: AnnData, *, copy: Literal[True]) -> AnnData: ...
            @overload
            def example(adata: AnnData, *, copy: Literal[False] = False) -> None: ...
            """,
            id="copy",
        ),
        pytest.param(
            """\
            from anndata import AnnData

            def example(adata: AnnData) -> AnnData | None:
                print(adata)
            """,
            """\
            from anndata import AnnData

            def example(adata: AnnData) -> AnnData | None: ...
            """,
            id="no_copy",
        ),
    ],
)
def test_copy(tmp_path: Path, code: str, expected: str) -> None:
    src = dedent(code)
    path = tmp_path / "example_mod.py"
    path.write_text(src)
    mod = StubSource(path.stem, path=str(path))

    mypy_opts = mypy_options(parse_options([]))
    mypy_opts.verbosity = 0  # Set to 1 for debugging

    generate_asts_for_modules([mod], parse_only=False, mypy_options=mypy_opts, verbose=True)
    assert mod.ast
    assert "example" in mod.ast.names, "Module was not analyzed"

    lines = generate_stub_for_py_module(mod).splitlines()
    assert lines, "Empty stub"
    assert lines == dedent(expected).splitlines()
