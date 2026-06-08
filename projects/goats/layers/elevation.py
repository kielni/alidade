import subprocess

from alidade.models import BoundLayer, Layer, PythonAction
from projects.goats.layers.border import border
from projects.goats.util import CRS

# TODO: read from file instead of hardcoding
_SRC_CRS = "EPSG:4269"
_NODATA = "-999999"

"""
USGS 1/3 arc-second digital elevation model (DEM)

https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n38w122/USGS_13_n38w122_20250826.tif
"""


def crop_elevation(layer: BoundLayer) -> None:
    """Reproject DEM from EPSG:4269 to EPSG:26910 and crop to park boundary."""
    (border,) = layer.inputs
    subprocess.run(
        [
            "gdalwarp",
            "-s_srs",
            _SRC_CRS,
            "-t_srs",
            CRS,
            "-cutline",
            str(border.path),
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
    raw_file="data/USGS_13_n38w122_20250826.tif",
    source_description="1/3 arc-second elevation DEM",
    source_origin="USGS National Elevation Dataset, EPSG:4269",
    datasource="output/elevation.tif",
    provider="gdal",
    crs=CRS,
    visible=True,
    action=PythonAction(fn=crop_elevation),
)
