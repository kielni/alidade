from pathlib import Path

from alidade.models import BoundProject
from alidade.render_map import render
from projects.goats.project import maps


def main() -> None:
    project_dir = Path(__file__).parent
    for spec in maps:
        bound = BoundProject(**spec.model_dump(mode="python"), project_path=project_dir)
        render(bound, f"map_{spec.id}")


if __name__ == "__main__":
    main()
