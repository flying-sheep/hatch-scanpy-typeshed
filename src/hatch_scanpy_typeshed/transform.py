"""Implement the signature transformations."""

from __future__ import annotations

from inspect import Parameter
from itertools import chain
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator
    from inspect import Signature


def transform_signature(sig: Signature) -> list[Signature]:
    """Transform a scanpy signature into a list of overloaded signatures."""
    if not isinstance(sig.return_annotation, str) or any(
        not isinstance(param.annotation, str) for param in sig.parameters.values()
    ):
        msg = "Need to use `from __future__ import annotations` and eval_str=False"
        raise TypeError(msg)
    return list(_transform_signatures([sig]))


def _transform_signatures(sigs: Iterable[Signature]) -> Iterator[Signature]:
    """Apply transformations recursively."""
    sigs = chain.from_iterable(map(transform_copy_sig, sigs))
    return sigs  # noqa: RET504


def transform_copy_sig(sig: Signature) -> Generator[Signature, None, None]:
    """Transform a scanpy copy signature into a list of overloaded signatures.

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
    if (
        (copy_param := sig.parameters.get("copy")) is None
        or copy_param.default is not False
        or copy_param.annotation != "bool"
        or sig.return_annotation != "AnnData | None"
    ):
        yield sig
        return

    yield sig.replace(
        parameters=_with_param(sig, "copy", annotation=Literal[True], default=Parameter.empty),
        return_annotation="AnnData",
    )

    yield sig.replace(
        parameters=_with_param(sig, "copy", annotation=Literal[False], default=False),
        return_annotation="None",
    )


def _with_param(sig: Signature, name: str, *, annotation: Any, default: Any) -> list[Parameter]:  # noqa: ANN401
    return [
        param.replace(annotation=annotation, default=default) if param.name == name else param
        for param in sig.parameters.values()
    ]
