"""Read the saved extent from output/project.qgs and print it as a Python tuple."""

import argparse
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


def main() -> None:
    """Print the current extent from output/project.qgs as a Python tuple."""
    parser = argparse.ArgumentParser(
        description="Print the extent from output/project.qgs."
    )
    parser.add_argument("project_dir", help="Path to project directory")
    args = parser.parse_args()

    project_dir = (Path.cwd() / args.project_dir).resolve()
    qgs_path = project_dir / "output" / "project.qgs"

    if not qgs_path.exists():
        print(f"output/project.qgs not found in {project_dir} — run 'make build' first")
        sys.exit(1)

    xmin, ymin, xmax, ymax = _read_extent(qgs_path)
    print(f"(\n    {xmin},\n    {ymin},\n    {xmax},\n    {ymax},\n)")


if __name__ == "__main__":
    main()
