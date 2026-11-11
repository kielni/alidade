"""Create a new alidade project directory from templates."""

import argparse
import importlib.util
import keyword
from pathlib import Path
from string import Template

TEMPLATE_DIR = Path(__file__).parent / "templates" / "project"


def _output_name(template: Path) -> Path:
    """Map a template path to the file it produces (drop .tmpl, restore dots)."""
    rel = template.relative_to(TEMPLATE_DIR).with_suffix("")
    if rel.name == "gitignore":
        return rel.with_name(".gitignore")
    return rel


def scaffold(project_dir: Path, title: str, crs: str) -> list[Path]:
    """Write the standard project layout to project_dir; return files written.

    The directory name becomes the project's import name, so it must be a
    valid Python identifier that does not shadow an installed module.
    """
    name = project_dir.name
    if not name.isidentifier() or keyword.iskeyword(name):
        raise SystemExit(f"{name!r} is not a valid Python package name")
    if importlib.util.find_spec(name) is not None:
        raise SystemExit(f"{name!r} would shadow an installed module; pick another")
    if project_dir.exists() and any(project_dir.iterdir()):
        raise SystemExit(f"{project_dir} already exists and is not empty")

    values = {"name": name, "title": title, "crs": crs}
    written: list[Path] = []
    for template in sorted(TEMPLATE_DIR.rglob("*.tmpl")):
        path = project_dir / _output_name(template)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(Template(template.read_text()).substitute(values))
        written.append(path)
    (project_dir / "data").mkdir()
    return written


def main() -> None:
    """CLI entry point for alidade-init."""
    parser = argparse.ArgumentParser(description="Create a new alidade project.")
    parser.add_argument("project_dir", help="Directory to create")
    parser.add_argument("--title", help="Map title (default: directory name)")
    parser.add_argument(
        "--crs", default="EPSG:4326", help="Project CRS (default: EPSG:4326)"
    )
    args = parser.parse_args()
    project_dir = Path(args.project_dir).resolve()
    title = args.title or project_dir.name.replace("_", " ").title()
    for path in scaffold(project_dir, title, args.crs):
        print(path)
    print(
        f"Next: add layers under layers/, then uv run alidade-build {args.project_dir}"
    )
