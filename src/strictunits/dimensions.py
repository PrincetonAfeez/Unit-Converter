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
