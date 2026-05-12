from models import Project

from layers.national_parks import national_parks
from layers.openstreetmap import openstreetmap
from layers.state_capitol_bldgs import state_capitol_bldgs

from layers.usaparks import usaparks

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
        usaparks,
        openstreetmap,
    ],
)
