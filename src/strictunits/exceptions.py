"""Exceptions for the strictunits unit converter."""

from __future__ import annotations


class UnitError(Exception):
    """Base class for all unit conversion errors."""


class ConformabilityError(UnitError):
    """Raised when two units do not have the same physical dimension."""


class UnknownUnitError(UnitError):
    """Raised when a unit name is not registered."""


class ParseError(UnitError):
    """Raised when a unit expression cannot be parsed."""
