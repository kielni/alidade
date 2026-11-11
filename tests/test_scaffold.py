"""Tests for alidade-init, alidade-mkinclude, and GEN.mk recipes."""

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from alidade import makefile_gen, mkinclude
from alidade.models import BoundMap, Layer, ShellAction
from alidade.scaffold import scaffold
from alidade.util.helpers import bind_map

PROJECT_NAME = "alidade_test_scaffold"


@pytest.fixture
def project_dir(tmp_path: Path) -> Iterator[Path]:
    """Yield a project path and unload its modules afterwards."""
    yield tmp_path / PROJECT_NAME
    for module in [m for m in sys.modules if m.split(".")[0] == PROJECT_NAME]:
        del sys.modules[module]


def test_scaffold_loads_as_project(project_dir: Path) -> None:
    scaffold(project_dir, "Scaffold Test", "EPSG:26910")
    for rel in ["main.py", "palette.py", "util.py", "layers/__init__.py"]:
        assert (project_dir / rel).exists()
    assert (project_dir / ".gitignore").read_text().startswith("output/")
    assert (project_dir / "data").is_dir()
    bound = bind_map(project_dir)
    assert bound.title == "Scaffold Test"
    assert bound.crs == "EPSG:26910"


def test_scaffold_rejects_invalid_name(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="not a valid"):
        scaffold(tmp_path / "my-project", "x", "EPSG:4326")


def test_scaffold_rejects_shadowing_name(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="shadow"):
        scaffold(tmp_path / "json", "x", "EPSG:4326")


def test_scaffold_rejects_non_empty_dir(project_dir: Path) -> None:
    project_dir.mkdir()
    (project_dir / "notes.md").write_text("")
    with pytest.raises(SystemExit, match="not empty"):
        scaffold(project_dir, "x", "EPSG:4326")


def test_gen_mk_uses_running_environment(tmp_path: Path) -> None:
    layer = Layer(
        id="derived_layer",
        name="Derived",
        type="vector",
        datasource="output/derived.geojson",
        crs="EPSG:4326",
        action=ShellAction(command="touch {output}"),
    )
    spec = BoundMap(title="T", crs="EPSG:4326", layers=[layer], map_path=tmp_path)
    build_layer = Path(sys.executable).parent / "alidade-build-layer"
    assert f"\t{build_layer} {tmp_path} derived_layer" in makefile_gen.generate(spec)


def test_mkinclude_path_exists(capsys: pytest.CaptureFixture[str]) -> None:
    mkinclude.main()
    assert Path(capsys.readouterr().out.strip()).is_file()
