"""
Use layers in project.py to generate print layouts for three maps.

In QGIS, open the Python console and export each map to a named PDF:

```python
_pdf = "/path/to/alidade/alidade/util/export_pdf.py")

print_prefix = "print_overview"
exec(open(_pdf).read())

print_prefix = "print_young_men"
exec(open(_pdf).read())

print_prefix = "print_young_men_near_malls"
exec(open(_pdf).read())
```
"""

from alidade import project_dir
from alidade.models import PrintLayout, PrintMapFrame, PrintScaleBar
from alidade.render import _load_spec, render_print_layout

PROJECT_DIR = project_dir(__file__)

CREDITS = "US Census Bureau, 2010 data · Big Bucks INC · CartoDB Positron"


def print_overview():
    """Generate print_overview.qpt: 1:600,000 overview of M22_39 by census tract.

    Template: print_overview.qpt
    1:600,000 scale map
    distribution of 22-39 year old males (census_tracts), M22_39 graduated color scheme
    mall locations (malls)
    major roads (major_roads)
    """
    layers = {"census_tracts", "malls", "major_roads", "cartodb_positron"}
    base = _load_spec(PROJECT_DIR)
    layers = [
        layer.model_copy(update={"visible": layer.id in layers})
        for layer in base.layers
    ]
    layout = PrintLayout(
        name="print_overview",
        title_text="Distribution of Males Aged 22–39",
        credits_text=CREDITS,
        map_frame=PrintMapFrame(scale=600000),
        scale_bar=PrintScaleBar(unit_type="mi", num_units_per_segment=50.0),
    )
    spec = base.model_copy(update={"layers": layers, "print_layout": layout})
    render_print_layout(spec, PROJECT_DIR)


def print_young_men():
    """Generate print layout for map of tracts with high % of young men.

    Template: print_young_men.qpt
    1:350,000 scale map
    Census tracts with greater than 20% 22-39 year old males (target_tracts)
    mall locations (malls)
    """
    pass


def print_young_men_near_malls():
    """Generate print layout for tracts with high % of young men near malls.

    Template: print_young_men_near_malls.qpt
    1:350,000 scale map
    Census tracts with >20% 22-39 year old males near malls (mall_target_intersect)
    mall locations (malls)
    5 mile buffers of malls (mall_buffers) ; unfilled or transparent polygons
    """
    pass


if __name__ == "__main__":
    print_overview()
    # print_young_men()
    # print_young_men_near_malls()
