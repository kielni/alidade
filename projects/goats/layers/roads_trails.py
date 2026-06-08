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


def clip_roads_trails(layer: BoundLayer) -> None:
    """Reproject and clip roads and trails to park boundary."""
    (border,) = layer.inputs
    gdf = gpd.read_file(layer.raw_path)
    keep = {"@id", "name", gdf.geometry.name}
    gdf = gdf[[c for c in gdf.columns if c in keep]]
    gdf = gdf[gdf.geom_type.isin(["LineString", "MultiLineString"])].to_crs(CRS)
    clip_border(gdf, border.path).to_file(layer.path)


roads_trails = Layer(
    id="roads_trails",
    name="Roads & Trails",
    type="vector",
    inputs=[border],
    raw_file="data/roads_trails.geojson",
    source_description="Road and trail lines",
    source_origin="OpenStreetMap via Overpass Turbo",
    datasource="output/roads_trails.shp",
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
    action=PythonAction(fn=clip_roads_trails),
)
