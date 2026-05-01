from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from functools import lru_cache

from .dimensions import Dimension
from .exceptions import UnknownUnitError
from .units import Unit, to_decimal


METRIC_PREFIXES: tuple[tuple[str, str, Decimal], ...] = (
    ("Y", "yotta", Decimal("1e24")),
    ("Z", "zetta", Decimal("1e21")),
    ("E", "exa", Decimal("1e18")),
    ("P", "peta", Decimal("1e15")),
    ("T", "tera", Decimal("1e12")),
    ("G", "giga", Decimal("1e9")),
    ("M", "mega", Decimal("1e6")),
    ("k", "kilo", Decimal("1e3")),
    ("h", "hecto", Decimal("1e2")),
    ("da", "deca", Decimal("1e1")),
    ("d", "deci", Decimal("1e-1")),
    ("c", "centi", Decimal("1e-2")),
    ("m", "milli", Decimal("1e-3")),
    ("u", "micro", Decimal("1e-6")),
    ("n", "nano", Decimal("1e-9")),
    ("p", "pico", Decimal("1e-12")),
    ("f", "femto", Decimal("1e-15")),
    ("a", "atto", Decimal("1e-18")),
    ("z", "zepto", Decimal("1e-21")),
    ("y", "yocto", Decimal("1e-24")),
)

class UnitRegistry:
    def __init__(self) -> None:
        self._units: dict[str, Unit] = {}
        self._prefixable: dict[str, Unit] = {}

    def register(
        self,
        name: str,
        symbol: str,
        dimension: Dimension,
        scale: Decimal | int | str,
        *,
        offset: Decimal | int | str = Decimal("0"),
        aliases: tuple[str, ...] = (),
        prefixable: bool = False,
    ) -> Unit:
        unit = Unit(
            name=name,
            symbol=symbol,
            dimension=dimension,
            scale=to_decimal(scale),
            offset=to_decimal(offset),
        )
        self.add(unit, aliases=aliases, prefixable=prefixable)
        return unit

    def add(self, unit: Unit, *, aliases: tuple[str, ...] = (), prefixable: bool = False) -> None:
        names = (unit.symbol, unit.name, *aliases)
        for name in names:
            self._units[name] = unit
            if prefixable:
                self._prefixable[name] = unit

    def get(self, name: str) -> Unit:
        try:
            return self._units[name]
        except KeyError:
            pass

        prefixed = self._get_prefixed(name)
        if prefixed is not None:
            return prefixed

        raise UnknownUnitError(f"unknown unit {name!r}")

