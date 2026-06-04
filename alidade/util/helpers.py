"""Shared utilities for loading project specs and resolving layer source paths."""

import importlib
from pathlib import Path

from alidade.models import Project, ProjectSpec

# alidade/ package root — the base for HERE-relative source path resolution.
_HERE = Path(__file__).parent.parent


def load_spec(project_path: Path) -> Project:
    """Load project.py from project_dir and return its spec attribute."""
    spec_path = project_path / "project.py"
    if not spec_path.exists():
        raise SystemExit(
            f"project.py not found in {project_path} — run 'make dump' first"
        )
    repo_root = _HERE.parent
    package = ".".join(project_path.relative_to(repo_root).parts)
    spec: ProjectSpec = importlib.import_module(f"{package}.project").spec
    return Project(**spec.model_dump(), project_path=project_path)


def resolve_source_path(source: str, project_dir: Path) -> Path:
    """Return the absolute filesystem Path for a layer source string.

    Strips OGR (|layername=...) and delimited-text (?...) suffixes before
    resolving. Absolute paths and URIs are returned as-is.
    """
    path_part = source.split("|")[0].split("?")[0]
    if path_part.startswith("/") or ":" in path_part.split("/")[0]:
        return Path(path_part)
    return (project_dir / path_part).resolve()


def abs_source(source: str, project_dir: Path) -> str:
    """Resolve a source path to an absolute string, preserving OGR/CSV suffixes.

    Paths starting with './' or 'data/' are project-dir-relative. All other
    relative paths resolve against the alidade package root (the convention for
    source data shipped alongside the repo). URIs and absolute paths pass through
    unchanged.
    """
    if source.startswith("/") or source.startswith("?") or ":" in source.split("/")[0]:
        return source
    if "|" in source:
        path_part, tail = source.split("|", 1)
        suffix = "|" + tail
    elif "?" in source:
        path_part, tail = source.split("?", 1)
        suffix = "?" + tail
    else:
        path_part, suffix = source, ""
    if path_part.startswith("./") or path_part.startswith("data/"):
        return str((project_dir / path_part).resolve()) + suffix
    return str((_HERE / path_part).resolve()) + suffix
