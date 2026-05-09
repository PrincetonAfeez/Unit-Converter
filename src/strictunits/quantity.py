"""Quantity functionality for the strictunits unit converter."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .units import Unit, to_decimal


@dataclass(frozen=True)
class Quantity:
    value: Decimal
    unit: Unit

    def __init__(self, value: Decimal | int | str, unit: Unit) -> None:
        object.__setattr__(self, "value", to_decimal(value))
        object.__setattr__(self, "unit", unit)

    def to(self, target_unit: Unit) -> "Quantity":
        return Quantity(self.unit.convert_value_to(self.value, target_unit), target_unit)

    def __add__(self, other: "Quantity") -> "Quantity":
        converted = other.to(self.unit)
        return Quantity(self.value + converted.value, self.unit)

    def __sub__(self, other: "Quantity") -> "Quantity":
        converted = other.to(self.unit)
        return Quantity(self.value - converted.value, self.unit)

    def __mul__(self, other: Decimal | int | str | "Quantity") -> "Quantity":
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value, self.unit * other.unit)
        return Quantity(self.value * to_decimal(other), self.unit)

    def __truediv__(self, other: Decimal | int | str | "Quantity") -> "Quantity":
        if isinstance(other, Quantity):
            return Quantity(self.value / other.value, self.unit / other.unit)
        return Quantity(self.value / to_decimal(other), self.unit)

    def __pow__(self, power: int) -> "Quantity":
        return Quantity(self.value**power, self.unit**power)
