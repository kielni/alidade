"""
USGS 1/3 arc-second digital elevation model (DEM)

https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n38w122/USGS_13_n38w122_20250826.tif

Checked in version is cropped to project area via
`uv run projects/goats/layers/elevation.py`
"""

import os
import subprocess

from alidade.models import BoundLayer, Layer, PythonAction
from projects.goats.layers.border import border
from projects.goats.util import BBOX_GENERAL, CRS

SRC_CRS = "EPSG:4269"
NODATA = "-999999"


def crop_elevation_to_bbox() -> None:
    """Crop full USGS DEM to project bounding box; output as USGS_bbox.tif.

    Run once before the pipeline to reduce the 477 MB source file to a small
    park-only raster.  Prints size before and after.
    """
    src = "projects/goats/data/USGS_13_n38w122_20250826.tif"
    dst = "projects/goats/data/USGS_bbox.tif"
    xmin, ymin, xmax, ymax = BBOX_GENERAL
    subprocess.run(
        [
            "gdalwarp",
            "-te",
            str(xmin),
            str(ymin),
            str(xmax),
            str(ymax),
            "-te_srs",
            "EPSG:4326",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=LZW",
            "-overwrite",
            src,
            dst,
        ],
        check=True,
    )
    src_size = os.path.getsize(src) / 1e6
    dst_size = os.path.getsize(dst) / 1e6
    print(f"  USGS DEM: {src_size:.0f} MB → {dst_size:.1f} MB")


def crop_elevation(layer: BoundLayer) -> None:
    """Reproject DEM from EPSG:4269 to EPSG:26910 and crop to park boundary."""
    (border,) = layer.inputs
    subprocess.run(
        [
            "gdalwarp",
            "-s_srs",
            SRC_CRS,
            "-t_srs",
            CRS,
            "-cutline",
            str(border.path),
            "-crop_to_cutline",
            "-dstnodata",
            NODATA,
            "-r",
            "bilinear",
            "-of",
            "GTiff",
            "-co",
            "COMPRESS=LZW",
            "-overwrite",
            str(layer.raw_path),
            str(layer.path),
        ],
        check=True,
    )


elevation = Layer(
    id="usgs_elevation",
    name="Elevation",
    type="raster",
    inputs=[border],
    raw_file="data/USGS_bbox.tif",
    source_description="1/3 arc-second elevation DEM",
    source_origin="USGS National Elevation Dataset, EPSG:4269",
    datasource="output/elevation.tif",
    provider="gdal",
    crs=CRS,
    action=PythonAction(fn=crop_elevation),
)


if __name__ == "__main__":
    # run via `uv run projects/goats/layers/elevation.py`
    crop_elevation_to_bbox()
