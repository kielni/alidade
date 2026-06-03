from pathlib import Path

from alidade.render_map import render
from projects.goats.project import maps


def main() -> None:
    project_dir = Path(__file__).parent
    for spec in maps:
        render(project_dir, spec, f"map_{spec.id}")


if __name__ == "__main__":
    main()
