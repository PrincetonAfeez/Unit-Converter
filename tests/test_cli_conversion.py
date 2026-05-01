"""Tests for the CLI conversion functionality."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

import strictunits.cli as cli
from strictunits.cli import build_parser, main
from strictunits.conversion import convert


def test_convert_returns_full_conversion_result() -> None:
    result = convert("5", "miles", "km")
    assert result.value == Decimal("8.04672")
    assert result.from_unit.symbol == "mi"
    assert result.to_unit.symbol == "km"
    assert result.source.unit.symbol == "mi"
    assert result.target.unit.symbol == "km"


def test_build_parser_and_cli_success(capsys) -> None:
    parser = build_parser()
    parsed = parser.parse_args(["convert", "10", "m/s", "km/h"])
    assert parsed.command == "convert"
    assert parsed.from_unit == "m/s"

    exit_code = main(["convert", "10", "m/s", "km/h"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "36 km/h"


def test_cli_returns_error_for_incompatible_units(capsys) -> None:
    exit_code = main(["convert", "5", "m", "kg"])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "cannot convert" in captured.err


def test_cli_unknown_command_branch_raises_system_exit() -> None:
    with pytest.raises(SystemExit):
        main(["unknown"])


def test_cli_unknown_command_returns_2_when_parser_error_does_not_exit(monkeypatch) -> None:
    class DummyParser:
        def parse_args(self, argv):  # noqa: ANN001
            return SimpleNamespace(command="noop")

        def error(self, _message: str) -> None:
            return None

    monkeypatch.setattr(cli, "build_parser", lambda: DummyParser())
    assert main(["noop"]) == 2
