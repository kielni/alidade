import os
import subprocess
import tempfile
from pathlib import Path

from alidade.models import (
    Layer,
    PaletteEntry,
    PalettedRenderer,
    ProcessingStep,
    PythonAction,
)
from projects.goats.util import CRS

# Slope categories: (value, lo_pct, hi_pct_exclusive, hex_color, label)
_CLASSES = [
    (1, 0, 15, "#1a9641", "Flat to gentle (0–15%)"),
    (2, 15, 27, "#ffffbf", "Moderate (15–27%)"),
    (3, 27, 58, "#fdae61", "Steep (27–58%)"),
    (4, 58, None, "#efefef", "Too steep (58%+)"),
]

_CALC_EXPR = " + ".join(
    f"(A>={lo})*(A<{hi})*{val}" if hi is not None else f"(A>={lo})*{val}"
    for val, lo, hi, _color, _label in _CLASSES
)


def build_slope(elevation_tif: Path, output: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        slope_pct = tmp.name
    try:
        subprocess.run(
            [
                "gdaldem",
                "slope",
                "-p",
                str(elevation_tif),
                slope_pct,
                "-of",
                "GTiff",
                "-co",
                "COMPRESS=LZW",
            ],
            check=True,
        )
        subprocess.run(
            [
                "gdal_calc.py",
                "-A",
                slope_pct,
                "--outfile",
                str(output),
                "--calc",
                _CALC_EXPR,
                "--type",
                "Byte",
                "--NoDataValue",
                "0",
                "--hideNoData",
                "--co",
                "COMPRESS=LZW",
                "--overwrite",
            ],
            check=True,
        )
    finally:
        if os.path.exists(slope_pct):
            os.unlink(slope_pct)


slope = Layer(
    id="slope_percent",
    name="Slope",
    type="raster",
    source="./output/slope.tif",
    provider="gdal",
    crs=CRS,
    visible=True,
    renderer=PalettedRenderer(
        entries=[
            PaletteEntry(value=val, color=color, label=label)
            for val, _lo, _hi, color, label in _CLASSES
        ]
    ),
    processing_step=ProcessingStep(
        description=(
            "Compute percentage slope from elevation DEM and classify"
            " into 4 categories"
        ),
        action=PythonAction(fn=build_slope),
        depends_on=["usgs_elevation"],
        output=Path("output/slope.tif"),
    ),
)
