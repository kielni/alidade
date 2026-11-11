"""Tests for loading a project from an arbitrary directory."""

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from alidade.util.helpers import bind_map, load_map_module

PROJECT_NAME = "alidade_test_external_project"

PROJECT_FILES = {
    "__init__.py": 'from .main import spec\n\n__all__ = ["spec"]\n',
    "util.py": 'CRS = "EPSG:4326"\n',
    "layers/__init__.py": "",
    "layers/boundary.py": (
        "from alidade.models import Layer\n"
        "from ..util import CRS\n\n"
        'boundary = Layer(id="park_boundary", name="Boundary", type="vector",'
        ' datasource="boundary.geojson", crs=CRS)\n'
    ),
    "layers/buffer.py": (
        "from alidade.models import Layer\n"
        "from ..util import CRS\n"
        "from .boundary import boundary\n\n"
        'buffer = Layer(id="park_boundary_buffer", name="Buffer", type="vector",'
        ' datasource="output/buffer.geojson", crs=CRS, inputs=[boundary])\n'
    ),
    "main.py": (
        "from alidade.models import Map\n"
        "from .layers.boundary import boundary\n"
        "from .layers.buffer import buffer\n"
        "from .util import CRS\n\n"
        'spec = Map(title="External", crs=CRS, layers=[boundary, buffer])\n'
    ),
}


def _unload(name: str) -> None:
    """Remove a project package and its submodules from sys.modules."""
    for module in [m for m in sys.modules if m == name or m.startswith(name + ".")]:
        del sys.modules[module]


@pytest.fixture
def external_project(tmp_path: Path) -> Iterator[Path]:
    """Write a minimal project with relative imports outside the repo."""
    project = tmp_path / PROJECT_NAME
    for rel, text in PROJECT_FILES.items():
        path = project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    yield project
    _unload(PROJECT_NAME)


def test_bind_map_outside_repo(external_project: Path) -> None:
    bound = bind_map(external_project)
    assert bound.map_path == external_project
    assert [layer.id for layer in bound.layers] == [
        "park_boundary",
        "park_boundary_buffer",
    ]


def test_project_parent_not_added_to_sys_path(external_project: Path) -> None:
    load_map_module(external_project)
    assert str(external_project.parent) not in sys.path


def test_load_is_idempotent(external_project: Path) -> None:
    assert load_map_module(external_project) is load_map_module(external_project)


def test_name_collision_is_reported(external_project: Path, tmp_path: Path) -> None:
    load_map_module(external_project)
    other = tmp_path / "elsewhere" / PROJECT_NAME
    other.mkdir(parents=True)
    (other / "__init__.py").write_text("")
    with pytest.raises(SystemExit, match="already taken"):
        load_map_module(other)


def test_missing_init_is_reported(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="__init__.py not found"):
        load_map_module(tmp_path)
