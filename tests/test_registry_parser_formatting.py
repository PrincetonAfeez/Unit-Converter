"""Tests for the registry, parser, and formatting functionality."""

from __future__ import annotations

from decimal import Decimal

import pytest

from strictunits import ParseError, UnknownUnitError, default_registry
from strictunits.formatting import format_decimal
from strictunits.parser import UnitParser, parse_unit
from strictunits.registry import UnitRegistry


def test_registry_register_add_get_and_unknown() -> None:
    reg = UnitRegistry()
    unit = reg.register("widget", "wd", parse_unit("m").dimension, "2", aliases=("widgets",), prefixable=True)

    assert reg.get("wd") is unit
    assert reg.get("widget") is unit
    assert reg.get("widgets") is unit

    with pytest.raises(UnknownUnitError, match="unknown unit"):
        reg.get("does-not-exist")


def test_registry_prefix_resolution_symbol_and_name_variants() -> None:
    reg = default_registry()
    assert reg.get("km").scale == Decimal("1000")
    assert reg.get("kilometer").scale == Decimal("1000")
    assert reg.get("microsecond").scale == Decimal("0.000001")


def test_registry_does_not_prefix_affine_units() -> None:
    reg = default_registry()
    with pytest.raises(UnknownUnitError, match="unknown unit"):
        reg.get("kC")


def test_parser_parses_compound_parentheses_and_alias_styles() -> None:
    reg = default_registry()
    left = parse_unit("W/(m^2*K)", reg)
    right = parse_unit("kg/(s**3.K)", reg)
    assert left.dimension == right.dimension


@pytest.mark.parametrize(
    ("expression", "error"),
    [
        ("", "empty unit expression"),
        ("m$", "unexpected character"),
        ("m^", "expected integer exponent"),
        ("(m/s", r"expected '\)'"),
        ("m(", r"expected '\*', '/', or end of expression"),
        ("m)", "unexpected token"),
        ("m/", "unexpected end of unit expression"),
        ("^2", "expected unit name or group"),
    ],
)
def test_parser_reports_invalid_expression_errors(expression: str, error: str) -> None:
    with pytest.raises(ParseError, match=error):
        parse_unit(expression)


def test_unit_parser_peek_and_advance_at_end() -> None:
    parser = UnitParser("m", default_registry())
    assert parser._peek() is not None
    assert parser._advance() is not None
    assert parser._peek() is None
    assert parser._advance() is None


def test_format_decimal_for_zero_plain_and_scientific_cases() -> None:
    assert format_decimal(Decimal("0E-25")) == "0"
    assert format_decimal(Decimal("36.000")) == "36"
    assert format_decimal(Decimal("1.2300")) == "1.23"
    assert format_decimal(Decimal("1E+2")) == "100"
    assert format_decimal(Decimal("0.000000123")) == "1.23E-7"
