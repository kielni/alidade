"""
Creeks from OpenStreetMap data,
downloaded via Overpass Turbo: https://overpass-turbo.eu
Use this to exclude areas within 100ft of creek to protect sensitive
riparian vegetation.

https://overpass-turbo.eu

```
[out:json][timeout:25];
(
  way["waterway"~"stream|river|canal|creek"]({{bbox}});
  relation["waterway"~"stream|river|canal|creek"]({{bbox}});
  way["natural"="water"]({{bbox}});
  relation["natural"="water"]({{bbox}});
  way["water"~"river|stream|lake|pond|reservoir"]({{bbox}});
);
out geom;
```
"""

import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleLine,
    SingleSymbol,
    Symbol,
)
from projects.goats.layers.border import border
from projects.goats.palette import WATER_FILL
from projects.goats.util import CRS, clip_border


def clip_water(layer: BoundLayer) -> None:
    """Reproject and clip streams to park boundary."""
    (border,) = layer.inputs
    gdf = gpd.read_file(layer.raw_path).to_crs(CRS)
    keep = {"@id", "name", gdf.geometry.name}
    gdf = gdf[[c for c in gdf.columns if c in keep]]
    clip_border(gdf, border.path).to_file(layer.path, driver="GPKG")


water = Layer(
    id="riparian_zone",
    name="Riparian Areas",
    type="vector",
    inputs=[border],
    raw_file="data/water.geojson",
    source_description="Waterway stream lines",
    source_origin="OpenStreetMap via Overpass Turbo",
    datasource="output/water.gpkg",
    crs=CRS,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color=WATER_FILL,
                    line_width=0.6,
                )
            ],
        )
    ),
    action=PythonAction(fn=clip_water),
)
