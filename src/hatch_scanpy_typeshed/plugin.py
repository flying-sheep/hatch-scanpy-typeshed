"""Implementation of the hook class."""

from __future__ import annotations

from typing import Any

from hatchling.builders.plugin.interface import BuilderInterface


class ScanpyBuildHook(BuilderInterface):
    """Build hook that generates .pyi files for Scanpy."""

    PLUGIN_NAME = "scanpy-builder"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """See https://hatch.pypa.io/latest/plugins/build-hook/reference/."""
