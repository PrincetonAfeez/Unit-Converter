# Schema

Simple JSON Schema definitions for the StrictUnits unit-converter project.

These files are designed to be dropped into the repository root as `Schema/`.
They document common payloads used by the project and can be used by API layers,
CLI wrappers, tests, or future UI work.

## Files

- `dimension.schema.json` - the 7-exponent SI base-dimension vector.
- `unit.schema.json` - a unit definition with name, symbol, dimension, scale, offset, aliases, and prefix support.
- `quantity.schema.json` - a value paired with a unit expression or unit object.
- `conversion-request.schema.json` - request payload for `convert(value, from_unit, to_unit)`.
- `conversion-result.schema.json` - response payload for conversion results.
- `registry.schema.json` - portable data shape for a unit registry.

## Example conversion request

```json
{
  "value": "5",
  "from_unit": "miles",
  "to_unit": "km"
}
```

## Dimension order

StrictUnits uses the following SI base-dimension order:

```text
[L, M, T, I, Theta, N, J]
```

That means velocity is represented as:

```json
{"exponents": [1, 0, -1, 0, 0, 0, 0]}
```

## Notes

Decimal values are represented as strings in most schemas to preserve precision
and match the project's use of Python `Decimal` values.
