"""Tests for the dimensions functionality."""

from __future__ import annotations

import pytest

from strictunits.dimensions import BASE_DIMENSION_COUNT, Dimension


def test_dimension_init_requires_seven_exponents() -> None:
    with pytest.raises(ValueError, match=str(BASE_DIMENSION_COUNT)):
        Dimension((1, 0))


def test_dimension_mul_div_and_pow() -> None:
    force = Dimension.MASS * Dimension.LENGTH / (Dimension.TIME**2)
    assert force.reduced_form() == "L M T^-2"

    squared_length = Dimension.LENGTH**2
    assert squared_length.reduced_form() == "L^2"


def test_dimension_pow_requires_integer() -> None:
    with pytest.raises(TypeError, match="integer powers"):
        Dimension.LENGTH**1.5  # type: ignore[operator]


def test_dimension_dimensionless_and_string() -> None:
    assert Dimension.NONE.is_dimensionless is True
    assert str(Dimension.NONE) == "dimensionless"
    assert str(Dimension.TIME) == "T"
