"""Implement the signature transformations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING
from warnings import warn

from mypy.stubdoc import ArgSig, FunctionSig

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator
    from typing import Any, Never


@dataclass
class PosArgWarning(UserWarning):
    """Warning raised if `copy` parameter is positional."""

    func_name: str

    def __str__(self) -> str:  # noqa: D105
        return f"Parameter 'copy' must be a keyword-only argument in function {self.func_name}"


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

    yield _DefaultFunctionSig(
        sig.name,
        _with_arg(sig, "copy", type="Literal[True]", default_value=None),
        "AnnData",
    )
    yield _DefaultFunctionSig(
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
        warn(sig.name, PosArgWarning, stacklevel=2)
        return False
    return True


def _with_arg(sig: FunctionSig, name: str, *, type: Any, default_value: str | None) -> list[ArgSig]:  # noqa: ANN401, A002
    return [_DefaultArgSig(name, type, default_value) if arg.name == name else arg for arg in sig.args]


class _DefaultArgSig(ArgSig):
    default_value: str | None

    def __init__(self, name: str, type: str | None = None, default_value: str | None = None) -> None:  # noqa: A002
        self.name = name
        self.type = type
        self.default_value = default_value

    @property
    def default(self) -> bool:
        return self.default_value is not None

    @default.setter
    def default(self, value: bool) -> Never:  # pragma: no cover
        msg = f"cannot set default to {value}"
        raise RuntimeError(msg)


class _DefaultFunctionSig(FunctionSig):
    args: list[_DefaultArgSig | ArgSig]

    def format_sig(
        self,
        indent: str = "",
        is_async: bool = False,  # noqa: FBT001, FBT002
        any_val: str | None = None,
        docstring: str | None = None,
    ) -> str:
        """Copy of the super method, but able to format defaults."""
        import keyword

        from mypy.util import quote_docstring

        args: list[str] = []
        for arg in self.args:
            arg_def = arg.name

            if arg_def in keyword.kwlist:
                arg_def = f"_{arg_def}"

            if (
                arg.type is None
                and any_val is not None
                and arg.name not in ("self", "cls")
                and not arg.name.startswith("*")
            ):
                arg_type: str | None = any_val
            else:
                arg_type = arg.type
            if arg_type:
                arg_def += f": {arg_type}"
                if arg.default:
                    arg_def += " = "
            elif arg.default:
                arg_def += "="
            if isinstance(arg, _DefaultArgSig) and arg.default_value is not None:
                arg_def += arg.default_value
            elif arg.default:
                arg_def += "..."

            args.append(arg_def)

        retfield = ""
        ret_type = self.ret_type if self.ret_type else any_val
        if ret_type is not None:
            retfield = f" -> {ret_type}"

        prefix = "async " if is_async else ""
        sig = "{indent}{prefix}def {name}({args}){ret}:".format(
            indent=indent,
            prefix=prefix,
            name=self.name,
            args=", ".join(args),
            ret=retfield,
        )
        suffix = f"\n{indent}    {quote_docstring(docstring)}" if docstring else " ..."
        return f"{sig}{suffix}"
