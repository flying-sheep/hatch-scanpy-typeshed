"""Compatibility module to import class from Python instead of mypyc-compiled .so file.

See https://github.com/python/mypy/issues/14736
"""

from __future__ import annotations

import shutil
import sys
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from tempfile import mkdtemp
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

__all__ = ["_import_from_python"]


def _import_from_python(mod_name: str) -> ModuleType:
    assert mod_name not in sys.modules

    root_pkg = mod_name.split(".", 1)[0]

    tmp_dir = Path(mkdtemp())
    root_spec = find_spec(root_pkg)
    assert root_spec is not None
    assert root_spec.origin is not None
    pkg_dir = Path(root_spec.origin).parent
    shutil.copytree(
        pkg_dir,
        tmp_dir / pkg_dir.name,
        ignore=lambda _, names: [n for n in names if n.endswith(".so")],
    )

    sys.path.insert(0, str(tmp_dir))

    spec = find_spec(mod_name)
    assert spec
    assert type(spec.loader).__name__ != "ExtensionFileLoader"
    return import_module(mod_name)


def _import_from_python_alt(mod_name: str) -> ModuleType:
    assert mod_name not in sys.modules
    meta_path = sys.meta_path.copy()

    sys.meta_path[:] = [
        loader
        for loader in meta_path
        if getattr(loader, "__name__", None) not in {"ExtensionFileLoader", "AssertionRewritingHook"}
    ]

    try:
        spec = find_spec(mod_name)
        assert spec
        assert type(spec.loader).__name__ != "ExtensionFileLoader"
        return import_module(mod_name)
    finally:
        sys.meta_path[:] = meta_path
