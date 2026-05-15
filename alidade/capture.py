"""Read the saved extent from output/project.qgs and write it back into project.py."""

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


def _read_extent(qgs_path: Path) -> tuple[float, float, float, float]:
    """Parse the MapCanvas extent from qgs_path and return (xmin, ymin, xmax, ymax)."""
    tree = ElementTree.parse(qgs_path)
    root = tree.getroot()
    canvas = root.find(".//mapcanvas[@name='theMapCanvas']")
    if canvas is None:
        raise ValueError("theMapCanvas not found in project.qgs")
    extent = canvas.find("extent")
    if extent is None:
        raise ValueError("extent not found in theMapCanvas")
    xmin = float(extent.findtext("xmin") or "")
    ymin = float(extent.findtext("ymin") or "")
    xmax = float(extent.findtext("xmax") or "")
    ymax = float(extent.findtext("ymax") or "")
    return xmin, ymin, xmax, ymax


def _write_extent(project_py: Path, extent: tuple[float, float, float, float]) -> None:
    """Rewrite the extent=(...) tuple in project_py with new coordinates."""
    xmin, ymin, xmax, ymax = extent
    new_extent = (
        f"    extent=(\n"
        f"        {xmin},\n"
        f"        {ymin},\n"
        f"        {xmax},\n"
        f"        {ymax},\n"
        f"    ),"
    )
    text = project_py.read_text()
    updated = re.sub(
        r"    extent=\(\n(?:        [^\n]+\n){4}    \),",
        new_extent,
        text,
    )
    if updated == text:
        raise ValueError("extent tuple not found in project.py — pattern did not match")
    project_py.write_text(updated)


def main() -> None:
    """Sync the extent from output/project.qgs into project.py."""
    parser = argparse.ArgumentParser(
        description="Capture extent from QGIS project into project.py."
    )
    parser.add_argument("project_dir", help="Path to project directory")
    args = parser.parse_args()

    project_dir = (Path.cwd() / args.project_dir).resolve()
    qgs_path = project_dir / "output" / "project.qgs"
    project_py = project_dir / "project.py"

    if not qgs_path.exists():
        print(f"output/project.qgs not found in {project_dir} — run 'make build' first")
        sys.exit(1)
    if not project_py.exists():
        print(f"project.py not found in {project_dir}")
        sys.exit(1)

    extent = _read_extent(qgs_path)
    _write_extent(project_py, extent)
    print(
        f"extent updated: xmin={extent[0]}, ymin={extent[1]}, xmax={extent[2]}, "
        f"ymax={extent[3]}"
    )


if __name__ == "__main__":
    main()
