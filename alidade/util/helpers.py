"""Shared utilities for loading map specs and resolving layer source paths."""

import importlib.util
import sys
import types
from pathlib import Path

from alidade.models import BoundMap, Map


def load_map_module(map_path: Path) -> types.ModuleType:
    """Import the project package at map_path and return the module.

    The project is imported under its own directory name, so it can live
    anywhere on disk. Only the project package is registered in
    sys.modules; its parent directory is not added to sys.path, so sibling
    directories cannot shadow installed packages. Modules inside the project
    must import each other with relative imports (``from ..util import CRS``).
    """
    init = map_path / "__init__.py"
    if not init.exists():
        raise SystemExit(f"__init__.py not found in {map_path}")
    name = map_path.name
    existing = sys.modules.get(name)
    if existing is not None:
        if Path(existing.__file__ or "").resolve() == init.resolve():
            return existing
        raise SystemExit(
            f"cannot load project {str(map_path)!r}: module name {name!r} is "
            f"already taken by {existing.__file__!r}; rename the project directory"
        )
    spec = importlib.util.spec_from_file_location(
        name, init, submodule_search_locations=[str(map_path)]
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[name]
        raise
    return module


def bind_map(map_path: Path) -> BoundMap:
    """Load main.py from map_dir and return its spec bound to map_path."""
    spec: Map = load_map_module(map_path).spec
    return BoundMap(**spec.model_dump(mode="python"), map_path=map_path)
