from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Iterable


BASE_DIMENSION_COUNT = 7
BASE_DIMENSION_LABELS = ("L", "M", "T", "I", "Theta", "N", "J")


@dataclass(frozen=True)
class Dimension:
    exponents: tuple[int, ...]
    
    def __init__(self, exponents: tuple[int, ...]) -> None:
        self.exponents = exponents

    NONE: ClassVar["Dimension"]
    LENGTH: ClassVar["Dimension"]
    MASS: ClassVar["Dimension"]
    TIME: ClassVar["Dimension"]
    CURRENT: ClassVar["Dimension"]
    TEMPERATURE: ClassVar["Dimension"]
    AMOUNT: ClassVar["Dimension"]
    LUMINOSITY: ClassVar["Dimension"]

    def __init__(self, exponents: Iterable[int]) -> None:
        values = tuple(int(value) for value in exponents)
        if len(values) != BASE_DIMENSION_COUNT:
            raise ValueError(f"expected {BASE_DIMENSION_COUNT} dimension exponents, got {len(values)}")
        object.__setattr__(self, "exponents", values)

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(left + right for left, right in zip(self.exponents, other.exponents))

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(left - right for left, right in zip(self.exponents, other.exponents))

    def __pow__(self, power: int) -> "Dimension":
        if not isinstance(power, int):
            raise TypeError("dimensions can only be raised to integer powers")
        return Dimension(value * power for value in self.exponents)

    @property
    def is_dimensionless(self) -> bool:
        return all(value == 0 for value in self.exponents)

    def reduced_form(self) -> str:
        if self.is_dimensionless:
            return "dimensionless"

        parts = []
        for label, exponent in zip(BASE_DIMENSION_LABELS, self.exponents):
            if exponent == 0:
                continue
            parts.append(label if exponent == 1 else f"{label}^{exponent}")
        return " ".join(parts)

    def __str__(self) -> str:
        return self.reduced_form()
