"""Tests for the conversion functionality."""

from decimal import Decimal

import pytest

from strictunits import ConformabilityError, convert
from strictunits.parser import parse_unit


def test_length_conversion_from_miles_to_kilometers() -> None:
    result = convert("5", "miles", "km")

    assert result.value == Decimal("8.04672")


def test_speed_conversion_from_meters_per_second_to_kilometers_per_hour() -> None:
    result = convert("10", "m/s", "km/h")

    assert result.value == Decimal("36.000")


def test_force_units_reduce_to_same_dimension() -> None:
    newton = parse_unit("N")
    expanded = parse_unit("kg*m/s^2")

    assert newton.dimension == expanded.dimension
    assert newton.scale == expanded.scale


def test_energy_expression_can_convert_to_joules() -> None:
    result = convert("3", "N*m", "J")

    assert result.value == Decimal("3")


def test_incompatible_units_raise_conformability_error() -> None:
    with pytest.raises(ConformabilityError, match="L.*M"):
        convert("5", "m", "kg")


def test_celsius_to_fahrenheit() -> None:
    result = convert("100", "C", "F")

    assert result.value == Decimal("212.0000000000000000000000000")


def test_fahrenheit_to_celsius() -> None:
    result = convert("32", "F", "C")

    assert result.value == Decimal("0E-25")


def test_parenthesized_compound_unit() -> None:
    left = parse_unit("W/(m^2*K)")
    right = parse_unit("kg/(s^3*K)")

    assert left.dimension == right.dimension
