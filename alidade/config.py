"""Locate a project's root directory and read alidade settings.

Settings come only from ``local.env`` in the project root. Environment
variables are deliberately ignored so a build depends on files in the
project, not on the shell it runs in. ``local.env`` uses Makefile syntax
(``KEY := VALUE`` or ``KEY = VALUE``).
"""

import re
from pathlib import Path

LOCAL_ENV = "local.env"


def find_project_root(map_path: Path) -> Path:
    """Return the nearest directory at or above map_path that marks a project.

    A directory containing ``alidade.toml`` or ``pyproject.toml`` is a project
    root. Falls back to map_path when no marker is found.
    """
    for directory in [map_path, *map_path.parents]:
        if (directory / "alidade.toml").exists():
            return directory
        if (directory / "pyproject.toml").exists():
            return directory
    return map_path


def read_env_file(path: Path) -> dict[str, str]:
    """Parse a Makefile-style env file (KEY := VALUE or KEY = VALUE)."""
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:?=\s*(.*)", line)
        if m:
            result[m.group(1)] = m.group(2).strip()
    return result


def load_settings(project_root: Path) -> dict[str, str]:
    """Return settings from the project root local.env; empty values are unset."""
    settings = read_env_file(project_root / LOCAL_ENV)
    return {key: value for key, value in settings.items() if value}


def get_setting(key: str, project_root: Path) -> str | None:
    """Return one setting for project_root, or None when it is not set."""
    return load_settings(project_root).get(key)
