"""Registry functionality for the strictunits unit converter."""

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
    """A registry of units and their relationships."""
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
        """Add a unit to the registry."""
        names = (unit.symbol, unit.name, *aliases)
        for name in names:
            self._units[name] = unit
            if prefixable:
                self._prefixable[name] = unit

    def get(self, name: str) -> Unit:
        """Get a unit from the registry."""
        try:
            return self._units[name]
        except KeyError:
            pass

        prefixed = self._get_prefixed(name)
        if prefixed is not None:
            return prefixed

        raise UnknownUnitError(f"unknown unit {name!r}")

    def _get_prefixed(self, name: str) -> Unit | None:
        """Get a prefixed unit from the registry."""
        prefix_tokens: list[tuple[str, Decimal]] = []
        for symbol, prefix_name, scale in METRIC_PREFIXES:
            prefix_tokens.append((symbol, scale))
            prefix_tokens.append((prefix_name, scale))

        for prefix, prefix_scale in sorted(prefix_tokens, key=lambda item: len(item[0]), reverse=True):
            """Get a prefixed unit from the registry."""
            if not name.startswith(prefix) or len(name) == len(prefix):
                continue

            suffix = name[len(prefix) :]
            base = self._prefixable.get(suffix)
            if base is None or base.is_affine:
                continue

            return replace(
                base,
                name=name,
                symbol=name,
                scale=base.scale * prefix_scale,
            )
        return None


@lru_cache(maxsize=1)
def default_registry() -> UnitRegistry:
    """Get the default registry."""
    registry = UnitRegistry()

    registry.register(
        "meter",
        "m",
        Dimension.LENGTH,
        "1",
        aliases=("meters", "metre", "metres"),
        prefixable=True,
    )
    registry.register("inch", "in", Dimension.LENGTH, "0.0254", aliases=("inches",))
    registry.register("foot", "ft", Dimension.LENGTH, "0.3048", aliases=("feet",))
    registry.register("yard", "yd", Dimension.LENGTH, "0.9144", aliases=("yards",))
    registry.register("mile", "mi", Dimension.LENGTH, "1609.344", aliases=("miles",))

    registry.register("gram", "g", Dimension.MASS, "0.001", aliases=("grams",), prefixable=True)
    registry.register("pound", "lb", Dimension.MASS, "0.45359237", aliases=("pounds",))

    registry.register("second", "s", Dimension.TIME, "1", aliases=("seconds", "sec"), prefixable=True)
    registry.register("minute", "min", Dimension.TIME, "60", aliases=("minutes",))
    registry.register("hour", "h", Dimension.TIME, "3600", aliases=("hours", "hr", "hrs"))

    registry.register("ampere", "A", Dimension.CURRENT, "1", aliases=("amp", "amps"), prefixable=True)
    registry.register("kelvin", "K", Dimension.TEMPERATURE, "1", aliases=("kelvins",), prefixable=True)
    registry.register("mole", "mol", Dimension.AMOUNT, "1", aliases=("moles",), prefixable=True)
    registry.register("candela", "cd", Dimension.LUMINOSITY, "1", aliases=("candelas",), prefixable=True)

    registry.register("celsius", "degC", Dimension.TEMPERATURE, "1", offset="273.15", aliases=("C",))
    registry.register(
        "fahrenheit",
        "degF",
        Dimension.TEMPERATURE,
        Decimal(5) / Decimal(9),
        offset=Decimal("273.15") - (Decimal(32) * Decimal(5) / Decimal(9)),
        aliases=("F",),
    )

    force = Dimension.MASS * Dimension.LENGTH / (Dimension.TIME**2)
    energy = force * Dimension.LENGTH
    power = energy / Dimension.TIME
    frequency = Dimension.NONE / Dimension.TIME

    registry.register("newton", "N", force, "1", aliases=("newtons",), prefixable=True)
    registry.register("joule", "J", energy, "1", aliases=("joules",), prefixable=True)
    registry.register("watt", "W", power, "1", aliases=("watts",), prefixable=True)
    registry.register("hertz", "Hz", frequency, "1", aliases=("hz",), prefixable=True)

    return registry
