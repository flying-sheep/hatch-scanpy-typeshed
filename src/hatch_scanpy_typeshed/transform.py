"""Implement the signature transformations."""

from __future__ import annotations

from itertools import chain
from typing import TYPE_CHECKING, Any

from mypy.stubdoc import ArgSig, FunctionSig

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator


def transform_func_def(sigs: Iterable[FunctionSig]) -> list[FunctionSig] | None:
    """Transform a scanpy function definition into a overloaded definition."""
    return list(_transform_func_defs(sigs))


def _transform_func_defs(sigs: Iterable[FunctionSig]) -> Iterator[FunctionSig]:
    """Apply transformations recursively."""
    sigs = chain.from_iterable(map(transform_copy_func_def, sigs))
    return sigs  # noqa: RET504


def transform_copy_func_def(sig: FunctionSig) -> Generator[FunctionSig, None, None]:
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
    if not _check_copy_param(sig) or sig.ret_type != "AnnData | None":
        yield sig
        return

    yield FunctionSig(
        sig.name,
        _with_arg(sig, "copy", type="Literal[True]", default=False),  # default=empty
        "AnnData",
    )
    yield FunctionSig(
        sig.name,
        _with_arg(sig, "copy", type="Literal[False]", default=True),  # default="False"
        "None",
    )


def _check_copy_param(sig: FunctionSig) -> bool:
    copy_param = next((arg for arg in sig.args if arg.name == "copy"), None)
    # TODO: check that default is False
    if copy_param is None or not copy_param.default:
        return False
    return copy_param.type == "bool"


def _with_arg(sig: FunctionSig, name: str, *, type: Any, default: bool) -> list[ArgSig]:  # noqa: ANN401, A002
    return [ArgSig(name, type, default) if arg.name == name else arg for arg in sig.args]
