"""Implement the signature transformations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING
from warnings import warn

from mypy.stubdoc import ArgSig, FunctionSig

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator
    from typing import Any


@dataclass
class PosArgWarning(UserWarning):
    """Warning raised if `copy` parameter is positional."""

    sig: FunctionSig

    def __str__(self) -> str:  # noqa: D105
        return f"Parameter 'copy' must be a keyword-only argument in function {self.sig.name}: {self.sig}"


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
        _with_arg(sig, "copy", type="Literal[True]", default_value=None),
        "AnnData",
    )
    yield FunctionSig(
        sig.name,
        _with_arg(sig, "copy", type="Literal[False]", default_value="False"),
        "None",
    )


def _check_copy_param(sig: FunctionSig) -> bool:
    i, copy_param = next(enumerate(arg for arg in sig.args if arg.name == "copy"), (-1, None))
    # TODO: check that default is False
    # https://github.com/flying-sheep/hatch-scanpy-typeshed/issues/2
    if copy_param is None or not copy_param.default:
        return False
    if copy_param.type != "bool":
        return False
    star_i = next((i for i, arg in enumerate(sig.args) if arg.is_star_arg() or arg.is_star_kwarg()), -1)
    if i > star_i:
        warn(PosArgWarning(sig), stacklevel=2)
        return False
    return True


def _with_arg(sig: FunctionSig, name: str, *, type: Any, default_value: str | None) -> list[ArgSig]:  # noqa: ANN401, A002
    return [
        ArgSig(
            name,
            type,
            default=default_value is not None,
            default_value="..." if default_value is None else default_value,
        )
        if arg.name == name
        else arg
        for arg in sig.args
    ]
