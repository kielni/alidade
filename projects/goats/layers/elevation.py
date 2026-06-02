import subprocess
from pathlib import Path

from alidade.models import Layer, ProcessingStep, PythonAction
from projects.goats.util import CRS

_DEM_FILENAME = "USGS_13_n38w122_20250826.tif"
_SRC_CRS = "EPSG:4269"
_NODATA = "-999999"

"""
USGS 1/3 arc-second digital elevation model (DEM)

https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n38w122/USGS_13_n38w122_20250826.tif
"""


def crop_elevation(boundary: Path, output: Path) -> None:
    project_dir = boundary.parent.parent
    src = str(project_dir / "data" / _DEM_FILENAME)
    subprocess.run(
        [
            "gdalwarp",
            "-s_srs",
            _SRC_CRS,
            "-t_srs",
            CRS,
            "-cutline",
            str(boundary),
            "-crop_to_cutline",
            "-dstnodata",
            _NODATA,
            "-r",
            "bilinear",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=LZW",
            "-overwrite",
            src,
            str(output),
        ],
        check=True,
    )


elevation = Layer(
    id="usgs_elevation",
    name="Elevation",
    type="raster",
    source="./output/elevation.tif",
    provider="gdal",
    crs=CRS,
    visible=True,
    processing_step=ProcessingStep(
        description=(
            "Reproject DEM from EPSG:4269 to EPSG:26910 and crop to park boundary"
        ),
        action=PythonAction(fn=crop_elevation),
        depends_on=["park_boundary"],
        output=Path("output/elevation.tif"),
    ),
)
