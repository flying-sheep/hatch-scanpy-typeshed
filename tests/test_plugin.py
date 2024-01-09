"""Basic tests: Hook is found, works, and throws expected errors."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from hatchling.plugin.manager import PluginManager

if TYPE_CHECKING:
    from hatch_scanpy_typeshed.plugin import ScanpyBuildHook


@pytest.fixture(
    params=[
        pytest.param("mypkg/__init__.py", id="flat"),
        pytest.param("src/mypkg/__init__.py", id="src"),
    ],
)
def basic_project(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    project_path = tmp_path / "mypkg"
    project_path.mkdir()  # error if it exists
    (project_path / "pyproject.toml").write_text("[project]\nname = 'mypkg'\n")
    pkg_file_path = project_path / Path(request.param)
    pkg_file_path.parent.mkdir(parents=True, exist_ok=True)
    pkg_file_path.write_text("TODO\n")
    return project_path


@pytest.fixture()
def pkg_dir(basic_project: Path) -> Path:
    pkgs_dir = (basic_project / "src") if (basic_project / "src").is_dir() else basic_project
    return pkgs_dir / "mypkg"


def get_hook_cls() -> type[ScanpyBuildHook]:
    pm = PluginManager()
    pm.metadata_hook.collect(include_third_party=True)
    plugin = pm.manager.get_plugin("scanpy-builder")
    assert plugin is not None
    return plugin.hatch_register_build_hook()  # type: ignore[no-any-return]


def mk_hook(project_path: Path) -> ScanpyBuildHook:
    hook_cls = get_hook_cls()
    return hook_cls(str(project_path))


def test_load_plugin() -> None:
    from hatch_scanpy_typeshed.plugin import ScanpyBuildHook

    assert get_hook_cls() is ScanpyBuildHook


def test_basic(basic_project: Path, pkg_dir: Path) -> None:
    code = dedent(
        """\
        from anndata import AnnData

        def example(adata: AnnData, *, copy: bool = False) -> AnnData | None:
            ...
        """,
    )
    (pkg_dir / "trans.py").write_text(code)
    (pkg_dir / "ignored.py").write_text("")

    hook = mk_hook(basic_project)
    version_api = hook.get_version_api()
    [(version, build)] = version_api.items()
    assert version == "in-tree"
    build(str(basic_project))
    assert (pkg_dir / "trans.pyi").is_file()
    assert "@overload" in (pkg_dir / "trans.pyi").read_text()
    assert not (pkg_dir / "ignored.pyi").exists()
