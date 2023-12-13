"""Implementation of the hook class."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Protocol

from hatchling.builders.config import BuilderConfig
from hatchling.builders.plugin.interface import BuilderInterface
from hatchling.plugin.manager import PluginManager
from mypy import stubgen

from .generate import generate_stubs

if TYPE_CHECKING:
    from hatchling.metadata.core import ProjectMetadata

ArtifactVersion = Literal["in-tree"]


class BuildCallback(Protocol):  # noqa: D101
    def __call__(self, build_dir: str, **build_data: Any) -> str:  # pragma: no cover  # noqa: ANN401, D102
        ...


class ScanpyBuilderConfig(BuilderConfig):
    """Config for scanpy builder."""

    builder: ScanpyBuildHook  # type: ignore[misc,unused-ignore]

    def get_min_python_version(self) -> tuple[int, int]:
        """Return the minimum supported Python version."""
        constraint = self.builder.metadata.core.python_constraint
        for minor in range(8, 100):
            if constraint.contains(f"3.{minor}"):
                return 3, minor
        msg = f"Unsupported Python version constraint: {constraint}"
        raise RuntimeError(msg)

    def mypy_stubgen_options(self, build_dir: Path, output_dir: Path | None = None) -> stubgen.Options:
        """Return mypy stubgen options."""
        if output_dir is None:
            output_dir = build_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        return stubgen.Options(
            pyversion=self.get_min_python_version(),
            no_import=True,
            inspect=True,
            doc_dir="",  # the default
            search_path=[],
            interpreter=sys.executable,
            parse_only=False,
            ignore_errors=False,
            include_private=False,
            output_dir=str(output_dir),
            modules=[],
            packages=[],
            files=[str(build_dir)],
            verbose=False,
            quiet=False,
            export_less=False,
            include_docstrings=True,
        )


class ScanpyBuildHook(BuilderInterface[ScanpyBuilderConfig, PluginManager]):
    """Build hook that generates .pyi files for Scanpy."""

    PLUGIN_NAME = "scanpy-builder"

    metadata: ProjectMetadata[PluginManager]  # type: ignore[misc,unused-ignore]

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """See https://hatch.pypa.io/latest/plugins/build-hook/reference/."""

    # TODO: def clean(self, directory: str, versions: list[str]) -> None:  # noqa: TD003

    @classmethod
    def get_config_class(cls) -> type[ScanpyBuilderConfig]:
        """Return the config class."""
        return ScanpyBuilderConfig

    def get_version_api(self) -> dict[str, BuildCallback]:
        """Return mapping of `str` versions to a callable that is used for building."""
        return {"in-tree": self.build_in_tree}

    def build_in_tree(self, build_dir: str, **_build_data: Any) -> str:  # noqa: ANN401
        """Build files in tree."""
        options = self.config.mypy_stubgen_options(Path(build_dir))
        generate_stubs(options)
        return options.output_dir
