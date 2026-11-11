"""Print the path of alidade.mk for use in a project Makefile's include."""

from pathlib import Path


def main() -> None:
    """CLI entry point for alidade-mkinclude."""
    print(Path(__file__).parent / "alidade.mk")
