"""
Calculate slope from DEM, and categorize into four buckets: flat to gentle, moderate,
steep, too steep.
"""

import os
import subprocess
import tempfile

from alidade.models import (
    BoundLayer,
    Layer,
    PaletteEntry,
    PalettedRenderer,
    PythonAction,
)
from projects.goats.layers.elevation import elevation
from projects.goats.palette import (
    SLOPE_GENTLE,
    SLOPE_MODERATE,
    SLOPE_STEEP,
    SLOPE_TOO_STEEP,
)
from projects.goats.util import CRS

# Slope categories: (value, lo_pct, hi_pct_exclusive, color, label)
CLASSES = [
    (1, 0, 15, SLOPE_GENTLE, "Flat to gentle (0-15%)"),
    (2, 15, 27, SLOPE_MODERATE, "Moderate (15-27%)"),
    (3, 27, 58, SLOPE_STEEP, "Steep (27-58%)"),
    (4, 58, None, SLOPE_TOO_STEEP, "Too steep (58%+)"),
]

CALC_EXPR = " + ".join(
    f"(A>={lo})*(A<{hi})*{val}" if hi is not None else f"(A>={lo})*{val}"
    for val, lo, hi, _color, _label in CLASSES
)


def build_slope(layer: BoundLayer) -> None:
    """Compute percentage slope from elevation DEM and classify into 4 categories."""
    (elevation,) = layer.inputs
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        slope_pct = tmp.name
    try:
        subprocess.run(
            [
                "gdaldem",
                "slope",
                "-p",
                str(elevation.path),
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
                str(layer.path),
                "--calc",
                CALC_EXPR,
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
    inputs=[elevation],
    datasource="output/slope.tif",
    provider="gdal",
    crs=CRS,
    renderer=PalettedRenderer(
        entries=[
            PaletteEntry(value=val, color=color, label=label)
            for val, _lo, _hi, color, label in CLASSES
        ]
    ),
    action=PythonAction(fn=build_slope),
)
