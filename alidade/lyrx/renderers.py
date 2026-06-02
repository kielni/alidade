"""CIM renderer factories."""

from typing import Any


def simple_renderer(symbol_ref: dict[str, Any], label: str = "") -> dict[str, Any]:
    """Return a CIMSimpleRenderer. Required fields per spec: type, patch, symbol."""
    return {
        "type": "CIMSimpleRenderer",
        "patch": "Default",
        "label": label,
        "symbol": symbol_ref,
    }


def class_break(
    symbol_ref: dict[str, Any], label: str, upper_bound: float
) -> dict[str, Any]:
    """Return a single CIMClassBreak dict."""
    return {
        "type": "CIMClassBreak",
        "label": label,
        "patch": "Default",
        "symbol": symbol_ref,
        "upperBound": upper_bound,
    }


def class_breaks_renderer(
    field: str, breaks: list[dict[str, Any]], minimum_break: float
) -> dict[str, Any]:
    """Return a CIMClassBreaksRenderer for GraduatedColor.

    CIMClassBreaksProperties fields (breaks, minimumBreak) merge directly
    onto the renderer object in CIM JSON — they are not nested under a key.
    """
    return {
        "type": "CIMClassBreaksRenderer",
        "classBreakType": "GraduatedColor",
        "field": field,
        "minimumBreak": minimum_break,
        "breaks": breaks,
    }
