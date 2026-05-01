from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .dimensions import Dimension
from .exceptions import ConformabilityError, UnitError

def to_decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

