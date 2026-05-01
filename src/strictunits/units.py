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


    def __mul__(self, other: "Unit") -> "Unit":
        self._ensure_composable(other)
        return Unit(
            name=f"{self.name}*{other.name}",
            symbol=f"{self.symbol}*{other.symbol}",
            dimension=self.dimension * other.dimension,
            scale=self.scale * other.scale,
        )


    def __truediv__(self, other: "Unit") -> "Unit":
        self._ensure_composable(other)
        return Unit(
            name=f"{self.name}/{other.name}",
            symbol=f"{self.symbol}/{other.symbol}",
            dimension=self.dimension / other.dimension,
            scale=self.scale / other.scale,
        )

    def __pow__(self, power: int) -> "Unit":
        if self.is_affine and power != 1:
            raise UnitError(f"affine unit {self.symbol!r} cannot be raised to a power")
        return Unit(
            name=f"{self.name}^{power}",
            symbol=f"{self.symbol}^{power}",
            dimension=self.dimension**power,
            scale=self.scale**power,
        )

    def _ensure_composable(self, other: "Unit") -> None:
        if self.is_affine or other.is_affine:
            raise UnitError("affine units such as Celsius and Fahrenheit cannot be used in compound units")
