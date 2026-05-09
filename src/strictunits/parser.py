"""Parser functionality for the strictunits unit converter."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .exceptions import ParseError
from .registry import UnitRegistry, default_registry
from .units import Unit


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|[-+]?\d+|\^|[*/()]")


@dataclass(frozen=True)
class Token:
    """A token is a lexical unit of a unit expression."""
    kind: str
    value: str


class UnitParser:
    """A unit parser is a parser for unit expressions."""
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
        """Tokenize a unit expression."""
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
        """Parse a unit expression."""
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
        """Parse a unit term."""
        unit = self._parse_factor()
        token = self._peek()
        if token is not None and token.value == "^":
            self._advance()
            exponent = self._advance()
            if exponent is None or exponent.kind != "integer":
                raise ParseError("expected integer exponent after '^'")
            unit = unit ** int(exponent.value)
        return unit

    def _parse_factor(self) -> Unit:
        """Parse a unit factor."""
        token = self._advance()
        if token is None:
            raise ParseError("unexpected end of unit expression")
        if token.kind == "name":
            return self.registry.get(token.value)
        if token.value == "(":
            unit = self._parse_expression()
            closing = self._advance()
            if closing is None or closing.value != ")":
                raise ParseError("expected ')' to close unit group")
            return unit
        raise ParseError(f"expected unit name or group, got {token.value!r}")

    def _peek(self) -> Token | None:
        """Peek at the next token."""
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _advance(self) -> Token | None:
        """Advance to the next token."""
        token = self._peek()
        if token is not None:
            self.index += 1
        return token


def parse_unit(expression: str, registry: UnitRegistry | None = None) -> Unit:
    """Parse a unit expression."""
    return UnitParser(expression, registry or default_registry()).parse()
