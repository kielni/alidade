"""Shared utilities for loading map specs and resolving layer source paths."""

import importlib
import types
from pathlib import Path

from alidade.models import BoundMap, Map

# helpers.py lives at alidade/util/helpers.py; repo root is three .parent() calls up
_REPO_ROOT = Path(__file__).parent.parent.parent


def _package_parts(map_path: Path) -> tuple[str, ...]:
    """Return the repo-relative path parts for map_path.

    Handles the case where map_path was resolved through a symlink
    (e.g. projects/joins -> /some/other/dir): searches projects/* for a
    symlink whose resolved target matches map_path.
    """
    try:
        return map_path.relative_to(_REPO_ROOT).parts
    except ValueError:
        pass
    for candidate in (_REPO_ROOT / "projects").glob("*"):
        if candidate.is_symlink() and candidate.resolve() == map_path:
            return candidate.relative_to(_REPO_ROOT).parts
    raise ValueError(
        f"{str(map_path)!r} is not under {str(_REPO_ROOT)!r} "
        "and no symlink in projects/ resolves to it"
    )


def load_map_module(map_path: Path) -> types.ModuleType:
    """Import the project package at map_path and return the module."""
    if not (map_path / "__init__.py").exists():
        raise SystemExit(f"__init__.py not found in {map_path}")
    package = ".".join(_package_parts(map_path))
    return importlib.import_module(package)


def bind_map(map_path: Path) -> BoundMap:
    """Load main.py from map_dir and return its spec bound to map_path."""
    spec: Map = load_map_module(map_path).spec
    return BoundMap(**spec.model_dump(mode="python"), map_path=map_path)
