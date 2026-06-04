from pathlib import Path

from alidade.models import Layer, ShellAction
from projects.sample.layers.elevation import elevation

elevation_10n = Layer(
    id="elevation_10n",
    name="elevation-10N",
    type="raster",
    inputs=[elevation],
    datasource="output/elevation_10n.tif",
    provider="gdal",
    crs="EPSG:26910",
    visible=False,
    style_xml=Path("styles/elevation_10n.xml"),
    action=ShellAction(
        command="gdalwarp -t_srs EPSG:26910 -r bilinear {input} {output}"
    ),
)
