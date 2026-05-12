from models import Project

from layers.cartodb_positron import cartodb_positron
from layers.national_parks import national_parks
from layers.state_capitol_bldgs import state_capitol_bldgs

spec = Project(
    title="Buffer and Query Practice",
    crs="EPSG:3857",
    extent=(
        -13543601.317267451,
        2332818.518554697,
        -7926694.38256428,
        6604519.163899155,
    ),
    layers=[
        national_parks,
        state_capitol_bldgs,
        cartodb_positron,
    ],
)
