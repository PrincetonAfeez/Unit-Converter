"""Tests for the units and quantity functionality."""

from __future__ import annotations

from decimal import Decimal

import pytest

from strictunits import ConformabilityError, Quantity, UnitError, default_registry
from strictunits.units import to_decimal


def test_to_decimal_accepts_int_str_and_decimal() -> None:
    assert to_decimal(3) == Decimal("3")
    assert to_decimal("2.5") == Decimal("2.5")
    assert to_decimal(Decimal("7.1")) == Decimal("7.1")


def test_unit_convert_value_to_and_affine_property() -> None:
    reg = default_registry()
    meter = reg.get("m")
    kilometer = reg.get("km")
    celsius = reg.get("C")
    kelvin = reg.get("K")

    assert meter.convert_value_to(Decimal("1000"), kilometer) == Decimal("1")
    assert celsius.is_affine is True
    assert celsius.convert_value_to(Decimal("0"), kelvin) == Decimal("273.15")


def test_unit_convert_raises_for_incompatible_dimensions() -> None:
    reg = default_registry()
    with pytest.raises(ConformabilityError, match="cannot convert"):
        reg.get("m").convert_value_to(Decimal("1"), reg.get("s"))


def test_unit_mul_div_pow_and_affine_composition_rules() -> None:
    reg = default_registry()
    meter = reg.get("m")
    second = reg.get("s")
    celsius = reg.get("C")

    speed = meter / second
    area = meter**2
    product = meter * second

    assert speed.symbol == "m/s"
    assert area.symbol == "m^2"
    assert product.symbol == "m*s"

    with pytest.raises(UnitError, match="compound units"):
        _ = celsius * second
    with pytest.raises(UnitError, match="cannot be raised"):
        _ = celsius**2


def test_quantity_math_methods_and_unit_propagation() -> None:
    reg = default_registry()
    meter = reg.get("m")
    cm = reg.get("cm")
    second = reg.get("s")

    left = Quantity("3", meter)
    right = Quantity("50", cm)

    added = left + right
    subtracted = left - right
    multiplied_scalar = left * 2
    multiplied_quantity = left * Quantity("2", second)
    divided_scalar = left / 2
    divided_quantity = left / Quantity("2", second)
    powered = left**2
    converted = right.to(meter)

    assert added.value == Decimal("3.5")
    assert subtracted.value == Decimal("2.5")
    assert multiplied_scalar.value == Decimal("6")
    assert multiplied_quantity.value == Decimal("6")
    assert multiplied_quantity.unit.symbol == "m*s"
    assert divided_scalar.value == Decimal("1.5")
    assert divided_quantity.unit.symbol == "m/s"
    assert powered.unit.symbol == "m^2"
    assert converted.value == Decimal("0.5")
