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
Roads and trails from OpenStreetMap data,
downloaded via Overpass Turbo: https://overpass-turbo.eu
Use this to identify priority areas "along roads, wide trails"

[out:json][timeout:25];
(
  // Hiking trails
  way["highway"="path"]({{bbox}});
  way["highway"="footway"]({{bbox}});
  way["highway"="track"]({{bbox}});
  way["route"="hiking"]({{bbox}});
  way["sac_scale"]({{bbox}});
  relation["route"="hiking"]({{bbox}});

  // Roads
  way["highway"~"motorway|trunk|primary|secondary|tertiary|unclassified|residential|service"]({{bbox}});
);
out geom;
"""


def clip_roads_trails(border: Path, output: Path) -> None:
    project_dir = border.parent.parent
    gdf = gpd.read_file(project_dir / "data" / "roads_trails.geojson")
    gdf = gdf[gdf.geom_type.isin(["LineString", "MultiLineString"])].to_crs(CRS)
    clip_border(gdf, output).to_file(output)


roads_trails = Layer(
    id="roads_trails",
    name="Roads & Trails",
    type="vector",
    source="./output/roads_trails.shp",
    provider="ogr",
    crs=CRS,
    visible=True,
    geometry_type="LineString",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="line",
            layers=[
                SimpleLine(
                    line_color="120,80,40,255",
                    line_width=0.5,
                )
            ],
        )
    ),
    processing_step=ProcessingStep(
        description="Reproject and clip roads and trails to park boundary",
        action=PythonAction(fn=clip_roads_trails),
        depends_on=["clip_border"],
        output=Path("output/roads_trails.shp"),
    ),
)
