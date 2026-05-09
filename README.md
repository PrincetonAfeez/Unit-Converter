# StrictUnits

StrictUnits is a small scientific unit converter that uses dimensional
analysis instead of string matching. It can convert compatible units, parse
compound unit expressions, and reject incompatible conversions with clear
errors.

## Installation

```powershell
python -m pip install -r requirements.txt
```

## Examples

```powershell
python main.py convert 5 miles km
python main.py convert 10 m/s km/h
python main.py convert 9.8 m/s^2 ft/s^2
strictunits convert 100 C F
```

## Scope

This first version focuses on the core engine:

- immutable dimensions, units, and quantities
- 7-vector SI base dimensions
- strict conformability checks
- common length, mass, time, force, energy, power, and temperature units
- compound unit parsing with `*`, `/`, `^`, and parentheses
- affine temperature conversion for Celsius and Fahrenheit

## Testing

Run tests:

```powershell
python -m pytest -q
```

Run tests with coverage:

```powershell
python -m pytest --cov=src/strictunits --cov-report=term-missing -q
```

