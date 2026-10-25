"""Tests for project root discovery and settings lookup."""

from pathlib import Path

import pytest

from alidade.config import find_project_root, get_setting
from alidade.publish_arcgis import ItemRegistry

KEY = "ALIDADE_TEST_SETTING"


@pytest.fixture(autouse=True)
def clear_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make sure the test key is not set in the environment."""
    monkeypatch.delenv(KEY, raising=False)


def test_project_root_is_nearest_marker(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("")
    inner = tmp_path / "carto"
    (inner / "nested").mkdir(parents=True)
    (inner / "alidade.toml").write_text("")
    assert find_project_root(inner / "nested") == inner
    assert find_project_root(tmp_path / "other") == tmp_path


def test_reads_project_local_env(tmp_path: Path) -> None:
    (tmp_path / "local.env").write_text(f"# comment\n{KEY} = project\n")
    assert get_setting(KEY, tmp_path) == "project"


def test_environment_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "local.env").write_text(f"{KEY} := project\n")
    monkeypatch.setenv(KEY, "env")
    assert get_setting(KEY, tmp_path) == "env"


def test_empty_environment_does_not_hide_file_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "local.env").write_text(f"{KEY} := project\n")
    monkeypatch.setenv(KEY, "")
    assert get_setting(KEY, tmp_path) == "project"


def test_missing_setting_is_none(tmp_path: Path) -> None:
    assert get_setting(KEY, tmp_path) is None


def test_item_registry_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "local.arcgis.json"
    registry = ItemRegistry(path)
    assert registry == {}
    registry["park_boundary"] = {"feature_item_id": "abc"}
    registry.save()
    assert ItemRegistry(path) == {"park_boundary": {"feature_item_id": "abc"}}
