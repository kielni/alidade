"""Raw UC and CSU campus locations from UCandCSU_XY.txt.

Used only as a dependency source for uc_and_csu so the build system can
pass the text file path to the reproject function. Not displayed directly.

UCandCSU_XY.txt columns (comma-delimited, whitespace-padded):
    latitude  — WGS 84 latitude
    longitude — WGS 84 longitude
    school    — institution name (e.g. "UC Berkeley", "San Jose State")
"""

from alidade.models import Layer

uc_and_csu_raw = Layer(
    id="uc_and_csu_raw",
    name="UC and CSU (raw)",
    type="vector",
    datasource=(
        "data/UCandCSU_XY.txt"
        "?type=csv&xField=longitude&yField=latitude&crs=EPSG:4326"
    ),
    provider="delimitedtext",
    crs="EPSG:4326",
    geometry_type="Point",
    visible=False,
)
