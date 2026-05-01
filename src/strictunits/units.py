from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .dimensions import Dimension
from .exceptions import ConformabilityError, UnitError

def to_decimal(value: Decimal | int | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

@dataclass(frozen=True)
class Unit:
    name: str
    symbol: str
    dimension: Dimension
    scale: Decimal
    offset: Decimal = Decimal("0")

    @property
    def is_affine(self) -> bool:
        return self.offset != 0
