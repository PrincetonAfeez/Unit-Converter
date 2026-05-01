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

    def _tokenize(self, expression: str) -> list[Token]:
        normalized = expression.strip().replace(" ", "").replace("**", "^").replace(".", "*")
        tokens: list[Token] = []
        position = 0
        while position < len(normalized):
            match = TOKEN_PATTERN.match(normalized, position)
            if match is None:
                raise ParseError(f"unexpected character {normalized[position]!r} in {expression!r}")
            value = match.group(0)
            kind = "operator" if value in {"*", "/", "^", "(", ")"} else "integer" if value.lstrip("+-").isdigit() else "name"
            tokens.append(Token(kind, value))
            position = match.end()
        return tokens

    def _parse_expression(self) -> Unit:
        unit = self._parse_term()
        while True:
            token = self._peek()
            if token is None or token.value == ")":
                return unit
            if token.value == "*":
                self._advance()
                unit = unit * self._parse_term()
                continue
            if token.value == "/":
                self._advance()
                unit = unit / self._parse_term()
                continue
            raise ParseError(f"expected '*', '/', or end of expression, got {token.value!r}")

    def _parse_term(self) -> Unit:
        unit = self._parse_factor()
        token = self._peek()
        if token is not None and token.value == "^":
            self._advance()
            exponent = self._advance()
            if exponent is None or exponent.kind != "integer":
                raise ParseError("expected integer exponent after '^'")
            unit = unit ** int(exponent.value)
        return unit
