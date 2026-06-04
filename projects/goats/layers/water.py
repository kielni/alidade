from pathlib import Path

import geopandas as gpd

from alidade.models import (
    Layer,
    ProcessingStep,
    PythonAction,
    SimpleLine,
    SingleSymbol,
    Symbol,
)
from projects.goats.util import CRS, clip_border

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


def clip_water(border: Path, output: Path) -> None:
    """Reproject and clip OSM stream data to the park clip border."""
    project_dir = border.parent.parent
    gdf = gpd.read_file(project_dir / "data" / "water.geojson").to_crs(CRS)
    clip_border(gdf, output).to_file(output)


water = Layer(
    id="riparian_zone",
    name="Riparian Areas",
    type="vector",
    source="./output/water.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="68,119,170,255",
                    line_width=0.6,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Reproject and clip streams to park boundary",
        action=PythonAction(fn=clip_water),
        depends_on=["clip_border"],
        output=Path("output/water.shp"),
    ),
)
