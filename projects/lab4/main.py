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
from alidade.render import render_print_layout

from .project import spec_near_malls, spec_overview, spec_young_men

PROJECT_DIR = project_dir(__file__)


def print_overview():
    render_print_layout(spec_overview, PROJECT_DIR)


def print_young_men():
    render_print_layout(spec_young_men, PROJECT_DIR)


def print_young_men_near_malls():
    render_print_layout(spec_near_malls, PROJECT_DIR)


if __name__ == "__main__":
    print_overview()
    # print_young_men()
    # print_young_men_near_malls()
