"""Conversion functionality for the strictunits unit converter."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .parser import parse_unit
from .quantity import Quantity
from .registry import UnitRegistry, default_registry
from .units import Unit


@dataclass(frozen=True)
class ConversionResult:
    """A conversion result is the result of a conversion."""
    value: Decimal
    from_unit: Unit
    to_unit: Unit
    source: Quantity
    target: Quantity


def convert(
    value: Decimal | int | str,
    from_expression: str,
    to_expression: str,
    registry: UnitRegistry | None = None,
) -> ConversionResult:
    """Convert a value from one unit to another."""
    unit_registry = registry or default_registry()
    from_unit = parse_unit(from_expression, unit_registry)
    to_unit = parse_unit(to_expression, unit_registry)
    source = Quantity(value, from_unit)
    target = source.to(to_unit)
    return ConversionResult(
        value=target.value,
        from_unit=from_unit,
        to_unit=to_unit,
        source=source,
        target=target,
    )
