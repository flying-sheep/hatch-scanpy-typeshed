"""Compatibility module to import class from Python instead of mypyc-compiled .so file.

See https://github.com/python/mypy/issues/14736
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING


def _import_from_python() -> type[ASTStubGenerator]:
    #
    from importlib.util import module_from_spec, spec_from_file_location

    import mypy.stubgen

    mod_old = mypy.stubgen

    path = Path(mod_old.__file__)
    path = path.with_name(f"{path.name.split('.', 1)[0]}.py")
    spec = spec_from_file_location(mod_old.__name__, path)
    assert spec is not None
    assert spec.loader is not None
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "ASTStubGenerator" in dir(mod)
    return mod.ASTStubGenerator


if TYPE_CHECKING:
    from mypy.stubgen import ASTStubGenerator
else:
    ASTStubGenerator = _import_from_python()
