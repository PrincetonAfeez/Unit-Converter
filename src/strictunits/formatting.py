"""Formatting functionality for the strictunits unit converter."""

from __future__ import annotations

from decimal import Decimal


def format_decimal(value: Decimal) -> str:
    if value.is_zero():
        return "0"

    normalized = value.normalize()
    if normalized.adjusted() < -6 or normalized.adjusted() >= 12:
        mantissa, exponent = f"{normalized:.12E}".split("E")
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa}E{exponent}"

    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text
