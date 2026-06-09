"""Shared utilities for loading project specs and resolving layer source paths."""

import importlib
import types
from pathlib import Path

from alidade.models import BoundProject, Project

# helpers.py lives at alidade/util/helpers.py; repo root is three .parent() calls up
_REPO_ROOT = Path(__file__).parent.parent.parent


def _package_parts(project_path: Path) -> tuple[str, ...]:
    """Return the repo-relative path parts for project_path.

    Handles the case where project_path was resolved through a symlink
    (e.g. projects/joins -> /some/other/dir): searches projects/* for a
    symlink whose resolved target matches project_path.
    """
    try:
        return project_path.relative_to(_REPO_ROOT).parts
    except ValueError:
        pass
    for candidate in (_REPO_ROOT / "projects").glob("*"):
        if candidate.is_symlink() and candidate.resolve() == project_path:
            return candidate.relative_to(_REPO_ROOT).parts
    raise ValueError(
        f"{str(project_path)!r} is not under {str(_REPO_ROOT)!r} "
        "and no symlink in projects/ resolves to it"
    )


def load_project_module(project_path: Path) -> types.ModuleType:
    """Import <project_path>/project.py and return the module."""
    if not (project_path / "project.py").exists():
        raise SystemExit(
            f"project.py not found in {project_path} - run 'make dump' first"
        )
    package = ".".join(_package_parts(project_path))
    return importlib.import_module(f"{package}.project")


def bind_project(project_path: Path) -> BoundProject:
    """Load project.py from project_dir and return its spec bound to project_path."""
    spec: Project = load_project_module(project_path).spec
    return BoundProject(**spec.model_dump(mode="python"), project_path=project_path)
