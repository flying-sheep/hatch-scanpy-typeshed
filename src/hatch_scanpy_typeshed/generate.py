"""Creates Python code from signatures."""

from __future__ import annotations

from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING

from mypy.stubgen import (
    Options,
    StubSource,
    collect_build_targets,
    generate_asts_for_modules,
    mypy_options,
)
from mypy.stubutil import common_dir_prefix, generate_guarded

from .compat import ASTStubGenerator
from .transform import transform_func_def

if TYPE_CHECKING:
    from mypy.nodes import FuncDef

logger = getLogger(__name__)


class TransformingStubGenerator(ASTStubGenerator):
    """Stub generator that transforms signatures."""

    def visit_func_def(self, o: FuncDef) -> None:
        """Transform function definition into stub."""
        if overloaded_def := transform_func_def(o):
            super().visit_overloaded_func_def(overloaded_def)
        else:
            super().visit_func_def(o)


def mod2path(mod: StubSource) -> Path:
    """Convert module name to path."""
    assert mod.path is not None, "Not found module was not skipped"
    target = Path(*mod.module.split("."))
    if Path(mod.path).name == "__init__.py":
        return target / "__init__.pyi"
    return target.with_suffix(".pyi")


def generate_stub_from_ast(
    mod: StubSource,
    target: Path,
    *,
    parse_only: bool = False,
    include_private: bool = False,
    export_less: bool = False,
) -> None:
    """Use AST to generate type stub for single file."""
    gen = TransformingStubGenerator(
        mod.runtime_all,
        include_private=include_private,
        analyzed=not parse_only,
        export_less=export_less,
    )
    assert mod.ast is not None, "This function must be used only with analyzed modules"
    mod.ast.accept(gen)

    # Write output to file.
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(gen.output()))


def generate_stubs(options: Options) -> None:
    """Generate stubs from collected modules and transform them."""
    mypy_opts = mypy_options(options)
    py_modules, _, _ = collect_build_targets(options, mypy_opts)
    generate_asts_for_modules(py_modules, options.parse_only, mypy_opts, options.verbose)
    files = {mod: Path(options.output_dir) / mod2path(mod) for mod in py_modules}
    for mod, target in files.items():
        with generate_guarded(mod.module, str(target), options.ignore_errors, options.verbose):
            generate_stub_from_ast(
                mod,
                target,
                parse_only=options.parse_only,
                include_private=options.include_private,
                export_less=options.export_less,
            )

    num_modules = len(py_modules)
    if not options.quiet and num_modules > 0:
        logger.info("Processed %d modules", num_modules)
        if len(files) == 1:
            logger.info("Generated %s", next(iter(files)))
        else:
            logger.info("Generated files under %s", common_dir_prefix([str(target) for target in files]))
