from __future__ import annotations

import re
from dataclasses import dataclass

from .exceptions import ParseError
from .registry import UnitRegistry, default_registry
from .units import Unit


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|[-+]?\d+|\^|[*/()]")

@dataclass(frozen=True)
class Token:
    kind: str
    value: str


class UnitParser:
    def __init__(self, expression: str, registry: UnitRegistry) -> None:
        self.expression = expression
        self.registry = registry
        self.tokens = self._tokenize(expression)
        self.index = 0

    def parse(self) -> Unit:
        if not self.tokens:
            raise ParseError("empty unit expression")

        unit = self._parse_expression()
        if self._peek() is not None:
            token = self._peek()
            raise ParseError(f"unexpected token {token.value!r} in {self.expression!r}")
        return unit

