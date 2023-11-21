"""Test the generate module."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from mypy.stubgen import StubSource, generate_asts_for_modules, mypy_options, parse_options

from hatch_scanpy_typeshed.generate import generate_stub_from_ast

if TYPE_CHECKING:
    from pathlib import Path


def test_copy(tmp_path: Path) -> None:
    src = dedent(
        """\
        def example(adata: AnnData, *, copy: bool = False) -> AnnData | None:
            print(copy)
        """,
    )
    path = tmp_path / "example_mod.py"
    path.write_text(src)
    mod = StubSource(path.stem, path=str(path))

    mypy_opts = mypy_options(parse_options([]))
    mypy_opts.verbosity = 0  # Set to 1 for debugging

    generate_asts_for_modules([mod], parse_only=False, mypy_options=mypy_opts, verbose=True)
    assert mod.ast
    assert "example" in mod.ast.names, "Module was not analyzed"

    generate_stub_from_ast(mod, pyi_path := path.with_suffix(".pyi"))
    lines = pyi_path.read_text().splitlines()[1:]
    assert lines, "Empty stub"
    expected = dedent(
        """\
        from __future__ import annotations

        import typing
        from anndata import AnnData

        @overload
        def example(
            adata: AnnData,
            *,
            copy: typing.Literal[True],
        ) -> AnnData: ...

        @overload
        def example(
            adata: AnnData,
            *,
            copy: typing.Literal[False] = False,
        ) -> None: ...
        """,
    ).splitlines()
    assert lines == expected
