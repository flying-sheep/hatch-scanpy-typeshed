"""Basic tests: Hook is found, works, and throws expected errors."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from hatchling.plugin.manager import PluginManager

if TYPE_CHECKING:
    from hatch_scanpy_typeshed.plugin import ScanpyBuildHook


@pytest.fixture(params=["mypkg/__init__.py", "src/mypkg/__init__.py"])
def basic_project(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    project_path = tmp_path / "mypkg"
    project_path.mkdir()  # error if it exists
    (project_path / "pyproject.toml").write_text("[project]\nname = 'mypkg'\n")
    pkg_file_path = project_path / Path(request.param)
    pkg_file_path.parent.mkdir(parents=True, exist_ok=True)
    pkg_file_path.write_text("TODO\n")
    return project_path


@pytest.fixture()
def pkgs_dir(basic_project: Path) -> Path:
    return (basic_project / "src") if (basic_project / "src").is_dir() else basic_project


def get_hook_cls() -> type[ScanpyBuildHook]:
    pm = PluginManager()
    pm.metadata_hook.collect(include_third_party=True)
    plugin = pm.manager.get_plugin("scanpy-builder")
    return plugin.hatch_register_build_hook()


def mk_hook(project_path: Path) -> ScanpyBuildHook:
    hook_cls = get_hook_cls()
    return hook_cls(project_path, {})


def test_load_plugin() -> None:
    from hatch_scanpy_typeshed.plugin import ScanpyBuildHook

    assert get_hook_cls() is ScanpyBuildHook


def test_basic(basic_project: Path) -> None:
    hook, metadata = mk_hook(basic_project)
    hook.update(metadata)
    pytest.fail("TODO")
