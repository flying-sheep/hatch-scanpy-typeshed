"""Test the generate module."""

from __future__ import annotations

from types import ModuleType

from hatch_scanpy_typeshed.generate import generate_overloads


def test_copy() -> None:
    class AnnData:
        pass

    def example(adata: AnnData, *, copy: bool = False) -> AnnData | None:
        ...

    mod = ModuleType("example_mod")
    mod.__all__ = ["example"]
    mod.example = example

    assert generate_overloads(mod).splitlines()[1:] == [
        "from __future__ import annotations",
        "",
        "from anndata import AnnData",
        "",
        "@overload",
        "def example(",
        "    adata: AnnData,",
        "    *,",
        "    copy: typing.Literal[True],",
        ") -> AnnData: ...",
        "",
        "@overload",
        "def example(",
        "    adata: AnnData,",
        "    *,",
        "    copy: typing.Literal[False] = False,",
        ") -> None: ...",
        "",
    ]
