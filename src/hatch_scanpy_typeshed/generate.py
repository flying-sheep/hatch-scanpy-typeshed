"""Creates Python code from signatures."""

from __future__ import annotations

import sys
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, overload

from mypy.nodes import NOT_ABSTRACT
from mypy.stubgen import (
    ASTStubGenerator,
    Options,
    StubSource,
    collect_build_targets,
    find_defined_names,
    generate_asts_for_modules,
    mypy_options,
    parse_options,
)
from mypy.stubutil import FunctionContext, common_dir_prefix, generate_guarded
from mypy.util import check_python_version

from .transform import transform_func_def

if TYPE_CHECKING:
    from mypy.nodes import FuncDef

logger = getLogger(__name__)


class TransformingStubGenerator(ASTStubGenerator):
    """Stub generator that transforms signatures."""

    def visit_func_def(self, o: FuncDef) -> None:
        """Transform function definition into stub."""
        ctx = FunctionContext(
            module_name=self.module_name,
            name=o.name,
            docstring=self._get_func_docstring(o),
            is_abstract=o.abstract_status != NOT_ABSTRACT,
            class_info=None,  # We could maybe support classes here?
        )

        self.record_name(o.name)

        default_sig = self.get_default_function_sig(o, ctx)
        sigs_orig = self.get_signatures(default_sig, self.sig_generators, ctx)

        if (sigs := transform_func_def(sigs_orig)) is None:
            super().visit_func_def(o)
            return

        for output in self.format_func_def(
            sigs,
            is_coroutine=o.is_coroutine,
            decorators=[*self._decorators, *(["@overload"] if len(sigs) > 1 else [])],
            docstring=ctx.docstring,
        ):
            self.add(output + "\n")


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
) -> str:
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
) -> str | None:
    """Use AST to generate type stub for single file."""
    gen = TransformingStubGenerator(
        mod.runtime_all,
        include_private=include_private,
        analyzed=not parse_only,
        export_less=export_less,
        include_docstrings=include_docstrings,
    )
    assert mod.ast is not None, "This function must be used only with analyzed modules"
    find_defined_names(mod.ast)
    mod.ast.accept(gen)

    output = gen.output()
    if target is None:
        return output
    # Write output to file or return.
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
