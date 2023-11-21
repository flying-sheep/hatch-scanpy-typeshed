"""Implement the signature transformations."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Any, Literal

from mypy.nodes import FuncDef, NameExpr, OverloadedFuncDef
from mypy.types import Instance, get_proper_type

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator
    from inspect import Signature


def transform_func_def(sig: FuncDef) -> OverloadedFuncDef | None:
    """Transform a scanpy function definition into a overloaded definition."""
    return OverloadedFuncDef(list(_transform_func_defs([sig])))


def _transform_func_defs(func_defs: Iterable[FuncDef]) -> Iterator[FuncDef]:
    """Apply transformations recursively."""
    sigs = chain.from_iterable(map(transform_copy_func_def, func_defs))
    return sigs  # noqa: RET504


def transform_copy_func_def(func_def: FuncDef) -> Generator[FuncDef, None, None]:
    """Transform a scanpy copy function definition into overloaded function definitions.

    E.g. the following definition

    .. code:: python

       def x(adata: AnnData, *, copy: bool = False) -> AnnData | None: ...

    becomes

    .. code:: python

       @overload
       def x(adata: AnnData, *, copy: Literal[True]) -> AnnData: ...
       @overload
       def x(adata: AnnData, *, copy: Literal[False] = False) -> None: ...
    """
    if not _check_copy_param(func_def) or func_def.return_annotation != "AnnData | None":
        yield func_def
        return

    yield sig.replace(
        parameters=_with_param(sig, "copy", annotation=Literal[True], default=Parameter.empty),
        return_annotation="AnnData",
    )

    yield sig.replace(
        parameters=_with_param(sig, "copy", annotation=Literal[False], default=False),
        return_annotation="None",
    )


def _check_copy_param(func_def: FuncDef) -> bool:
    copy_param = next((arg for arg in func_def.arguments if arg.variable.name == "copy"), None)
    if copy_param is None or not isinstance(copy_param.initializer, NameExpr) or copy_param.initializer.name != "None":
        return False
    type_annot = get_proper_type(copy_param.type_annotation)
    if type_annot is None or not isinstance(type_annot, Instance) or type_annot.type.fullname != "bool":
        return False
    return True


def _with_param(sig: Signature, name: str, *, annotation: Any, default: Any) -> list[Parameter]:  # noqa: ANN401
    return [
        param.replace(annotation=annotation, default=default) if param.name == name else param
        for param in sig.parameters.values()
    ]
