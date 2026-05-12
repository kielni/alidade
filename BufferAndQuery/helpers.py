"""Processing helpers for the BufferAndQuery project."""

from __future__ import annotations

import subprocess
from pathlib import Path


def filter_national_parks(inputs: list[Path], output: Path) -> None:
    """Filter USAParks.shp to FCC='D83' (National Park Service units) with ogr2ogr.

    ogr2ogr is GDAL's vector data conversion and filtering tool.
    """
    subprocess.run(
        [
            "ogr2ogr",
            "-where",
            "FCC='D83'",
            str(output),
            str(inputs[0]),
        ],
        check=True,
    )
