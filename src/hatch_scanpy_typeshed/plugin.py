"""Implementation of the hook class."""

from __future__ import annotations

from typing import Any, Literal, Protocol

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.plugin.manager import PluginManager

ArtifactVersion = Literal["in-tree"]


class BuildCallback(Protocol):  # noqa: D101
    def __call__(self, build_dir: str, **build_data: Any) -> str:  # pragma: no cover  # noqa: ANN401, D102
        ...


class ScanpyBuilderConfig(BuilderConfig):
    """Config for scanpy builder."""


class ScanpyBuildHook(BuilderInterface[ScanpyBuilderConfig, PluginManager]):
    """Build hook that generates .pyi files for Scanpy."""

    PLUGIN_NAME = "scanpy-builder"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """See https://hatch.pypa.io/latest/plugins/build-hook/reference/."""

    def get_version_api(self) -> dict[str, BuildCallback]:
        """Return mapping of `str` versions to a callable that is used for building.

        The callable’s return value is the absolute path to the generated .pyi file.
        """
        return {"in-tree": self.build_in_tree}

    def build_in_tree(self, build_dir: str, **build_data: Any) -> str:  # noqa: ANN401
        """Build files in tree."""
        msg = f"Not implemented: {build_dir!r}, {build_data!r}"
        raise NotImplementedError(msg)
