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

    def convert_value_to(self, value: Decimal, target: "Unit") -> Decimal:        """."""
        if self.dimension != target.dimension:
            raise ConformabilityError(
                "cannot convert "
                f"{self.symbol!r} [{self.dimension.reduced_form()}] "
                f"to {target.symbol!r} [{target.dimension.reduced_form()}]"
            )

        base_value = self.to_base(value)
        return target.from_base(base_value)

    def to_base(self, value: Decimal) -> Decimal:
        return (value * self.scale) + self.offset

    def from_base(self, value: Decimal) -> Decimal:
        return (value - self.offset) / self.scale

