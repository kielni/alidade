import geopandas as gpd

from alidade.models import (
    BoundLayer,
    Layer,
    PythonAction,
    SimpleFill,
    SingleSymbol,
    Symbol,
)
from projects.lab4.layers.census_tracts_raw import census_tracts_raw
from projects.lab4.layers.mall_buffers import mall_buffers

# output/mall_buffer_tracts.shp: census tracts (pct_m22_39 > 20%) that
# spatially intersect a mall 5-mile buffer. One row per (tract × mall) pair.
# Fields: GEOID, NAMELSAD, Total, M22_39, pct_m22_39, mall_id, mall_name.
_PCT_THRESHOLD = 20.0


def intersect_mall_buffer_tracts(layer: BoundLayer) -> None:
    buffers_layer, tracts_layer = layer.inputs
    buf = gpd.read_file(buffers_layer.path)[["id", "mall_name", "geometry"]].rename(
        columns={"id": "mall_id"}
    )

    tr = gpd.read_file(tracts_layer.path)
    tr = tr[tr["Total"] > 0].copy()
    tr["pct_m22_39"] = tr["M22_39"] / tr["Total"] * 100
    tr = tr[tr["pct_m22_39"] > _PCT_THRESHOLD][
        ["GEOID", "NAMELSAD", "Total", "M22_39", "pct_m22_39", "geometry"]
    ]

    joined = gpd.sjoin(tr, buf, how="inner", predicate="intersects")
    joined = joined.drop(columns=["index_right"])
    joined[
        [
            "GEOID",
            "NAMELSAD",
            "Total",
            "M22_39",
            "pct_m22_39",
            "mall_id",
            "mall_name",
            "geometry",
        ]
    ].to_file(layer.path)


mall_buffer_tracts = Layer(
    id="mall_buffer_tracts",
    name="Mall Buffer Census Tracts",
    type="vector",
    inputs=[mall_buffers, census_tracts_raw],
    datasource="output/mall_buffer_tracts.shp",
    provider="ogr",
    crs="EPSG:2227",
    visible=True,
    geometry_type="Polygon",
    renderer=SingleSymbol(
        symbol=Symbol(
            type="fill",
            layers=[
                SimpleFill(
                    color="255,200,50,180",
                    outline_color="180,120,0,255",
                    outline_width=0.5,
                )
            ],
        )
    ),
    action=PythonAction(fn=intersect_mall_buffer_tracts),
)
