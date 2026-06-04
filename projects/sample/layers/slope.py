from pathlib import Path

from alidade.models import Layer, ShellAction
from projects.sample.layers.elevation_10n import elevation_10n

slope = Layer(
    id="slope",
    name="Slope",
    type="raster",
    inputs=[elevation_10n],
    datasource="output/slope.tif",
    provider="gdal",
    crs="EPSG:26910",
    visible=False,
    style_xml=Path("styles/slope.xml"),
    action=ShellAction(command="gdaldem slope {input} {output}"),
)
