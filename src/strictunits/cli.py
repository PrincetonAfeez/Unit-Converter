"""CLI for the strictunits unit converter."""

from __future__ import annotations

import argparse
import sys

from .conversion import convert
from .exceptions import UnitError
from .formatting import format_decimal


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="strictunits",
        description="Strict scientific unit conversion with dimensional analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="Convert a value between compatible units.")
    convert_parser.add_argument("value", help="Numeric value to convert, such as 5 or 9.81.")
    convert_parser.add_argument("from_unit", help="Source unit expression, such as miles or m/s^2.")
    convert_parser.add_argument("to_unit", help="Target unit expression, such as km or ft/s^2.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "convert":
        try:
            result = convert(args.value, args.from_unit, args.to_unit)
        except UnitError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        print(f"{format_decimal(result.value)} {result.to_unit.symbol}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2
