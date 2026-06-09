"""Shared utilities for loading project specs and resolving layer source paths."""

import importlib
from pathlib import Path

from alidade.models import BoundProject, Project

# alidade/ package root — the base for HERE-relative source path resolution.
_HERE = Path(__file__).parent.parent


def bind_project(project_path: Path) -> BoundProject:
    """Load project.py from project_dir and return its spec bound to project_path."""
    spec_path = project_path / "project.py"
    if not spec_path.exists():
        raise SystemExit(
            f"project.py not found in {project_path} — run 'make dump' first"
        )
    repo_root = _HERE.parent
    package = ".".join(project_path.relative_to(repo_root).parts)
    spec: Project = importlib.import_module(f"{package}.project").spec
    return BoundProject(**spec.model_dump(mode="python"), project_path=project_path)
