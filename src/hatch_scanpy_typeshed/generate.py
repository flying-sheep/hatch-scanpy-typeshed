"""Creates Python code from signatures."""

from __future__ import annotations

import re
import sys
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, overload
from warnings import catch_warnings, simplefilter, warn

from mypy.nodes import NOT_ABSTRACT
from mypy.stubgen import (
    EMPTY,
    FUNC,
    ASTStubGenerator,
    Options,
    StubSource,
    collect_build_targets,
    find_defined_names,
    generate_asts_for_modules,
    mypy_options,
    parse_options,
)
from mypy.stubutil import FunctionContext, ImportTracker, common_dir_prefix, generate_guarded
from mypy.util import check_python_version

from .transform import PosArgWarning, transform_func_def

if TYPE_CHECKING:
    from mypy.nodes import FuncDef

logger = getLogger(__name__)


class TransformingStubGenerator(ASTStubGenerator):
    """Stub generator that transforms signatures."""

    did_transform: bool

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]  # noqa: D107, ANN002, ANN003
        super().__init__(*args, **kwargs)
        self.import_tracker = PrettyImportTracker()
        self.did_transform = False

    def visit_func_def(self, o: FuncDef) -> None:
        """Transform function definition into stub."""
        ctx = FunctionContext(
            module_name=self.module_name,
            name=o.name,
            docstring=self._get_func_docstring(o),
            is_abstract=o.abstract_status != NOT_ABSTRACT,
            class_info=None,  # We could maybe support classes here?
        )

        default_sig = self.get_default_function_sig(o, ctx)
        sigs_orig = self.get_signatures(default_sig, self.sig_generators, ctx)

        if (sigs := transform_func_def(sigs_orig)) is None:
            super().visit_func_def(o)
            return

        # This part is copied from visit_func_def
        if (
            self.is_private_name(o.name, o.fullname)
            or self.is_not_in_all(o.name)
            or (self.is_recorded_name(o.name) and not o.is_overload)
        ):
            self.clear_decorators()
            return
        if self.is_top_level() and self._state not in (EMPTY, FUNC):
            self.add("\n")
        self.record_name(o.name)
        # end of copied code

        if len(sigs) > 1:
            self.did_transform = True
            self.import_tracker.add_import_from(
                "typing",
                [("Literal", "Literal"), ("overload", "overload")],
                require=True,
            )
            self.add_decorator("overload")
        # Set o.func.is_overload = True?

        for line in self.format_func_def(
            sigs,
            is_coroutine=o.is_coroutine,
            decorators=self._decorators,
            docstring=ctx.docstring,
        ):
            self.add(f"{line}\n")

        # This part is copied again
        self.clear_decorators()
        self._state = FUNC


class PrettyImportTracker(ImportTracker):
    """Import tracker that collapses identical names and aliases."""

    def import_lines(self) -> list[str]:  # noqa: D102
        return [re.sub(r"\b([\w]+) as \1\b", r"\1", line) for line in super().import_lines()]


def mod2path(mod: StubSource) -> Path:
    """Convert module name to path."""
    assert mod.path is not None, "Not found module was not skipped"
    target = Path(*mod.module.split("."))
    if Path(mod.path).name == "__init__.py":
        return target / "__init__.pyi"
    return target.with_suffix(".pyi")


@overload
def generate_stub_for_py_module(
    mod: StubSource,
    target: None = None,
    *,
    parse_only: bool = False,
    include_private: bool = False,
    export_less: bool = False,
    include_docstrings: bool = False,
) -> tuple[str, bool]:
    ...


@overload
def generate_stub_for_py_module(
    mod: StubSource,
    target: Path,
    *,
    parse_only: bool = False,
    include_private: bool = False,
    export_less: bool = False,
    include_docstrings: bool = False,
) -> None:
    ...


def generate_stub_for_py_module(
    mod: StubSource,
    target: Path | None = None,
    *,
    parse_only: bool = False,
    include_private: bool = False,
    export_less: bool = False,
    include_docstrings: bool = False,
) -> tuple[str, bool] | None:
    """Use AST to generate type stub for single file.

    If target is None, return output as string and a flag indicating whether transformations were made.
    Otherwise, if transformations were made, write output to file.
    """
    gen = TransformingStubGenerator(
        mod.runtime_all,
        include_private=include_private,
        analyzed=not parse_only,
        export_less=export_less,
        include_docstrings=include_docstrings,
    )
    assert mod.ast is not None, "This function must be used only with analyzed modules"
    find_defined_names(mod.ast)
    with catch_warnings(record=True) as warnings:
        simplefilter(action="always", category=PosArgWarning)
        mod.ast.accept(gen)
        msg = None
        if func_names := [
            w.message.func_name if isinstance(w.message, PosArgWarning) else str(w.message)
            for w in warnings
            if issubclass(w.category, PosArgWarning)
        ]:
            s = "" if len(func_names) == 1 else "s"
            qualnames = ", ".join(func_names)
            msg = f"Parameter 'copy' must be a keyword-only argument in {mod.module} function{s} {qualnames}"
    if msg is not None:
        warn(msg, UserWarning, stacklevel=2)

    output = gen.output()
    if target is None:
        return output, gen.did_transform
    if gen.did_transform:
        # Write output to file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output)
    return None


def generate_stubs(options: Options) -> None:
    """Generate stubs from collected modules and transform them."""
    mypy_opts = mypy_options(options)
    py_modules, _, _ = collect_build_targets(options, mypy_opts)
    generate_asts_for_modules(py_modules, options.parse_only, mypy_opts, options.verbose)
    files = {mod: Path(options.output_dir) / mod2path(mod) for mod in py_modules}
    for mod, target in files.items():
        with generate_guarded(mod.module, str(target), ignore_errors=options.ignore_errors, verbose=options.verbose):
            generate_stub_for_py_module(
                mod,
                target,
                parse_only=options.parse_only,
                include_private=options.include_private,
                export_less=options.export_less,
                include_docstrings=options.include_docstrings,
            )

    num_modules = len(py_modules)
    if not options.quiet and num_modules > 0:
        logger.info("Processed %d modules", num_modules)
        if len(files) == 1:
            logger.info("Generated %s", next(iter(files)))
        else:
            logger.info("Generated files under %s", common_dir_prefix([str(target) for target in files]))


def main(args: list[str] | None = None) -> None:
    """Command line interface."""
    check_python_version("stubgen")

    options = parse_options(sys.argv[1:] if args is None else args)
    generate_stubs(options)
