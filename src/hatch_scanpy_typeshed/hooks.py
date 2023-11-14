"""Hook module referenced by ``hatch``’s entry point."""

from __future__ import annotations

from hatchling.plugin import hookimpl

from .plugin import ScanpyBuildHook


@hookimpl
def hatch_register_build_hook() -> type[ScanpyBuildHook]:
    """Pluggy hook implementation returning a hatch build hook class."""
    return ScanpyBuildHook
