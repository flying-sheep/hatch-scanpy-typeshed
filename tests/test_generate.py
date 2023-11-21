"""Test the generate module."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

from mypy.options import Options as MypyOptions
from mypy.stubgen import StubSource, generate_asts_for_modules

from hatch_scanpy_typeshed.generate import generate_stub_from_ast

if TYPE_CHECKING:
    from pathlib import Path


def test_copy(tmp_path: Path) -> None:
    src = dedent(
        """\
        def example(adata: AnnData, *, copy: bool = False) -> AnnData | None:
            ...
        """,
    )
    path = tmp_path / "test.py"
    path.write_text(src)
    mod = StubSource("example_mod", path=str(path))

    mypy_opts = MypyOptions()

    generate_asts_for_modules([mod], parse_only=False, mypy_options=mypy_opts, verbose=True)
    generate_stub_from_ast(mod, pyi_path := path.with_suffix(".pyi"))
    assert (
        pyi_path.read_text().splitlines()[1:]
        == dedent(
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
    )
