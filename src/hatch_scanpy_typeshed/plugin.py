"""Implementation of the hook class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hatchling.builders.plugin.interface import BuilderInterface

if TYPE_CHECKING:
    from collections.abc import Callable


class ScanpyBuildHook(BuilderInterface):
    """Build hook that generates .pyi files for Scanpy."""

    PLUGIN_NAME = "scanpy-builder"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """See https://hatch.pypa.io/latest/plugins/build-hook/reference/."""

    def get_version_api(self) -> dict[str, Callable[[str, dict], str]]:
        """Return mapping of `str` versions to a callable that is used for building.

        The callable’s return value is the absolute path to the generated .pyi file.
        """

        def version_api(build_dir: str, build_data: dict) -> str:
            msg = f"Not implemented: {build_dir!r}, {build_data!r}"
            raise NotImplementedError(msg)

        return {"1.0": version_api}
