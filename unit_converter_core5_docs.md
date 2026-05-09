# Architecture Decision Record

## App 37 — Unit Converter
**Scientific Units Group | Document 1 of 5**

### Title
Use dimensional analysis as the core correctness model for unit conversion.

### Status
Accepted

### Date
2026-05-09

### Context
The project is a small scientific unit converter named **StrictUnits**. Its goal is not merely to map strings like `"miles"` to `"km"` but to prove that a requested conversion is physically meaningful before producing a result. The application supports simple units, metric prefixes, compound unit expressions such as `m/s^2`, parenthesized expressions such as `W/(m^2*K)`, and affine temperature units such as Celsius and Fahrenheit.

The main risk in a converter is silent incorrectness. A converter that only matches category labels can accidentally permit invalid conversions, reject valid compound conversions, or mishandle temperature offsets. The project therefore needed a representation that could answer the question: “Do these units represent the same physical dimension?”

### Decision Drivers
- **Correctness over catalog breadth.** It is better to convert fewer units safely than many units loosely.
- **Learning value.** Dimensional analysis exposes deeper architecture than a dictionary-based converter.
- **Standard-library implementation.** The project avoids runtime dependencies and uses `decimal.Decimal`, `dataclasses`, `argparse`, and `functools`.
- **Scientific clarity.** Every unit carries an explicit dimension and scale.
- **Composable units.** Compound units should be produced by multiplying, dividing, and exponentiating unit objects.
- **Strict error behavior.** Incompatible dimensions should fail loudly.
- **CLI simplicity.** The first version should keep a narrow command surface while validating the engine.

### Options Considered

#### Option 1 — String-to-string conversion tables
This would store conversion factors directly between pairs such as `mile -> kilometer`, `meter -> foot`, and `Celsius -> Fahrenheit`.

**Benefits**
- Simple to implement for a small number of conversions.
- Easy for a beginner to understand.
- Fast lookup for direct conversions.

**Costs**
- Conversion table grows rapidly.
- Compound units require many special cases.
- Incompatible conversions are hard to reason about consistently.
- Does not naturally support algebra such as `kg*m/s^2`.

#### Option 2 — Category-based unit registry
This would assign each unit to a category such as length, mass, time, speed, force, or temperature.

**Benefits**
- More structured than direct pair tables.
- Easy to reject obvious mismatches such as length to mass.
- Useful for common consumer converters.

**Costs**
- Categories become arbitrary for compound scientific units.
- Derived units require extra category definitions.
- `N`, `kg*m/s^2`, and `J/m` may be physically related but not obvious from labels.
- Still encourages special-case logic.

#### Option 3 — Dimensional analysis with scale and offset
Each unit stores a seven-exponent SI base-dimension vector, a scale to base units, and an optional offset for affine units.

**Benefits**
- Strict conformability checks fall out of dimension equality.
- Derived units can be modeled compositionally.
- Compound unit expressions can be parsed into actual unit objects.
- `N` and `kg*m/s^2` reduce to the same dimension and scale.
- Temperature offset behavior can be isolated.

**Costs**
- More code than a lookup table.
- Requires careful parser and registry design.
- Affine units need explicit restrictions in compound expressions.
- Not all possible units are present in the initial catalog.

### Decision
StrictUnits uses **dimensional analysis as the core model**. A `Dimension` is represented as a seven-integer exponent tuple. A `Unit` combines a name, symbol, dimension, scale, and optional offset. A `Quantity` combines a `Decimal` value with a `Unit`. Conversion parses source and target unit expressions, verifies matching dimensions, converts the source value to base units, and converts from base units into the target unit.

### Rationale
This design matches the project’s scientific purpose. It makes conversion validity a property of the data model rather than a long list of command-specific checks. The same rule can handle simple conversions such as miles to kilometers, speed conversions such as meters per second to kilometers per hour, acceleration conversions, force equivalence, energy equivalence, and temperature conversion.

The approach also demonstrates stronger architectural thinking than a flat mapping. The converter has separate responsibilities: dimensions describe physical meaning, units describe scale and offset, the registry knows available units, the parser builds compound units, quantities perform typed arithmetic, and the CLI only handles user input/output.

### Trade-offs Accepted
- The initial catalog is intentionally limited to common scientific units rather than broad consumer categories.
- Unit expressions are parsed with a small custom recursive parser rather than a full grammar library.
- Runtime precision depends on `Decimal` context behavior and registry scale values.
- The CLI exposes only conversion, not catalog browsing or interactive mode.
- Celsius and Fahrenheit are supported but blocked from compound unit algebra because affine units do not compose like linear scale units.

### Consequences
- Incompatible conversions raise `ConformabilityError` instead of producing nonsense.
- Compound expressions are first-class, not bolted-on cases.
- Derived units such as newton, joule, watt, and hertz can coexist with equivalent expanded expressions.
- The registry becomes an important long-term extension point.
- The parser and unit algebra are the main maintenance risks.
- Future expansion should preserve the dimension-first model rather than adding shortcut conversions that bypass it.

### Superseded By
Not superseded.

### Constitution Alignment
This decision supports the Constitution by showing appropriate architectural thinking for a scientific CLI project. The project remains scoped, standard-library based, and verifiable while demonstrating a clear separation between parsing, modeling, conversion, and presentation.

---

# Technical Design Document

## App 37 — Unit Converter
**Scientific Units Group | Document 2 of 5**

### Purpose & Scope
StrictUnits is a Python command-line unit converter and small library. It converts numeric quantities between compatible units using dimensional analysis. The system supports:

- SI base dimensions represented as a seven-vector.
- Immutable `Dimension`, `Unit`, `Quantity`, and `ConversionResult` objects.
- A default unit registry with length, mass, time, current, temperature, amount, luminosity, force, energy, power, and frequency units.
- Metric prefixes for prefixable units.
- Compound unit parsing with multiplication, division, exponentiation, and parentheses.
- Affine temperature conversion for Celsius and Fahrenheit.
- CLI invocation through `strictunits convert` or `python main.py convert`.

The project intentionally does not attempt to be a full scientific units ecosystem. There is no interactive shell, no configuration file, no persistence layer, no custom user unit file, and no runtime dependency on third-party packages.

### System Context
The system sits between a user-provided unit expression and a numeric conversion result.

```text
User / script
    |
    | strictunits convert 10 m/s km/h
    v
CLI argparse layer
    |
    | value, from expression, to expression
    v
Conversion service
    |
    | parse source unit, parse target unit
    v
Unit parser + registry
    |
    | Unit objects with dimensions and scales
    v
Quantity conversion
    |
    | Decimal result
    v
Formatter
    |
    | stdout
```

### Component Breakdown

#### `strictunits.__init__`
Exports the public library API: `convert`, `ConversionResult`, `Dimension`, `Quantity`, `Unit`, `UnitRegistry`, `default_registry`, and exception classes.

#### `strictunits.dimensions`
Defines the dimension algebra.

Key objects:
- `BASE_DIMENSION_COUNT = 7`
- `BASE_DIMENSION_LABELS = ("L", "M", "T", "I", "Theta", "N", "J")`
- `Dimension`

Responsibilities:
- Validate that dimensions contain exactly seven exponents.
- Multiply, divide, and exponentiate dimensions.
- Provide base dimensions such as `Dimension.LENGTH`, `Dimension.MASS`, `Dimension.TIME`, and `Dimension.TEMPERATURE`.
- Produce readable reduced forms such as `L M T^-2`.

Notable implementation detail:
- The file contains two `__init__` definitions inside `Dimension`; the second one is the effective constructor. This does not appear to break behavior, but it is a cleanup candidate.

#### `strictunits.units`
Defines the `Unit` object and unit algebra.

Responsibilities:
- Convert numeric input to `Decimal`.
- Convert values to and from base units.
- Check conformability before converting between units.
- Compose units through multiplication, division, and integer exponentiation.
- Reject affine units in compound operations.

Key fields:
- `name`
- `symbol`
- `dimension`
- `scale`
- `offset`

#### `strictunits.quantity`
Defines `Quantity`, pairing a `Decimal` value with a `Unit`.

Responsibilities:
- Convert a quantity to another compatible unit.
- Add and subtract conformable quantities.
- Multiply and divide quantities, producing compound units.
- Exponentiate quantities.

#### `strictunits.registry`
Defines `UnitRegistry` and `default_registry`.

Responsibilities:
- Register units by symbol, name, and aliases.
- Track which units accept metric prefixes.
- Generate prefixed units lazily.
- Provide the default catalog.

Default catalog includes:
- Length: meter, inch, foot, yard, mile.
- Mass: gram, pound.
- Time: second, minute, hour.
- SI base units: ampere, kelvin, mole, candela.
- Temperature: Celsius and Fahrenheit as affine units.
- Derived units: newton, joule, watt, hertz.
- Metric prefixes from yotta to yocto for prefixable units.

#### `strictunits.parser`
Defines a small recursive-descent parser for unit expressions.

Responsibilities:
- Tokenize unit expressions.
- Normalize spaces, `**` into `^`, and `.` into `*`.
- Parse multiplication, division, powers, and parenthesized groups.
- Resolve unit names through the registry.
- Raise `ParseError` for invalid expressions.

Supported examples:
- `m`
- `km`
- `m/s`
- `m/s^2`
- `kg*m/s^2`
- `W/(m^2*K)`
- `N.m`

#### `strictunits.conversion`
Defines the conversion use case.

Responsibilities:
- Parse source and target units.
- Build a `Quantity`.
- Convert to the target unit.
- Return a `ConversionResult` containing the original and target structures.

#### `strictunits.formatting`
Formats `Decimal` results for CLI display.

Responsibilities:
- Return `"0"` for zero.
- Use scientific notation for very small or very large values.
- Strip trailing zeros in normal decimal output.

#### `strictunits.cli`
Defines the `argparse` command-line interface.

Responsibilities:
- Parse `strictunits convert <value> <from_unit> <to_unit>`.
- Call `convert`.
- Print `<value> <target-symbol>` to stdout.
- Print `error: ...` to stderr and exit `2` for `UnitError`.

#### `strictunits.exceptions`
Defines custom exception classes:
- `UnitError`
- `ConformabilityError`
- `UnknownUnitError`
- `ParseError`

#### `main.py`
Provides a repository-local entry point. It prepends `src` to `sys.path` and calls `strictunits.cli.main()` so the app can run as `python main.py convert ...` without an editable install.

### Module Dependency Graph

```text
main.py
  -> strictunits.cli

strictunits.__init__
  -> strictunits.conversion
  -> strictunits.dimensions
  -> strictunits.exceptions
  -> strictunits.quantity
  -> strictunits.registry
  -> strictunits.units

strictunits.cli
  -> strictunits.conversion
  -> strictunits.exceptions
  -> strictunits.formatting

strictunits.conversion
  -> strictunits.parser
  -> strictunits.quantity
  -> strictunits.registry
  -> strictunits.units

strictunits.parser
  -> re
  -> dataclasses
  -> strictunits.exceptions
  -> strictunits.registry
  -> strictunits.units

strictunits.quantity
  -> dataclasses
  -> decimal.Decimal
  -> strictunits.units

strictunits.registry
  -> dataclasses.replace
  -> decimal.Decimal
  -> functools.lru_cache
  -> strictunits.dimensions
  -> strictunits.exceptions
  -> strictunits.units

strictunits.units
  -> dataclasses
  -> decimal.Decimal
  -> strictunits.dimensions
  -> strictunits.exceptions

strictunits.dimensions
  -> dataclasses
  -> typing

strictunits.formatting
  -> decimal.Decimal
```

### Core Algorithms & Logic

#### Dimension algebra
Every physical dimension is a tuple of seven integer exponents:

```text
(L, M, T, I, Theta, N, J)
```

Examples:
- Length: `(1, 0, 0, 0, 0, 0, 0)`
- Mass: `(0, 1, 0, 0, 0, 0, 0)`
- Time: `(0, 0, 1, 0, 0, 0, 0)`
- Force: `M * L / T^2`, represented as `(1, 1, -2, 0, 0, 0, 0)`

Operations:
- Multiplication adds exponents.
- Division subtracts exponents.
- Power multiplies each exponent by the integer exponent.

#### Unit conversion
Conversion proceeds as:

```text
from_unit = parse_unit(from_expression)
to_unit = parse_unit(to_expression)
source = Quantity(value, from_unit)
target = source.to(to_unit)
```

`Unit.convert_value_to` performs:

1. Compare `self.dimension` and `target.dimension`.
2. If dimensions differ, raise `ConformabilityError`.
3. Convert source value to base:
   ```text
   base_value = value * source.scale + source.offset
   ```
4. Convert base value to target:
   ```text
   target_value = (base_value - target.offset) / target.scale
   ```

This same structure supports both linear conversions and affine temperature conversions.

#### Compound unit parsing
The parser normalizes input then tokenizes names, integer exponents, operators, and parentheses.

Grammar, simplified:

```text
expression := term (("*" | "/") term)*
term       := factor ("^" integer)?
factor     := unit_name | "(" expression ")"
```

A unit name is resolved through `UnitRegistry.get`. Operators compose actual `Unit` objects:
- `m/s` divides meter by second.
- `m/s^2` divides meter by second squared.
- `kg*m/s^2` builds an expanded force unit.
- `W/(m^2*K)` parses a grouped denominator.

#### Prefixed unit resolution
When a name is not found directly, the registry tries metric prefixes. It sorts prefixes longest-first to avoid ambiguity such as `da` versus `d`.

Example:
```text
km -> prefix "k" + base "m" -> meter with scale 1000
millisecond -> prefix "milli" + base "second" -> second with scale 0.001
```

Prefixed units are generated with `dataclasses.replace` and are not permanently registered.

#### Affine unit handling
Temperature units such as Celsius and Fahrenheit have nonzero offsets. They can be converted directly to each other or to Kelvin-compatible temperature units, but cannot be multiplied, divided, or exponentiated in compound expressions.

This prevents nonsensical expressions like:

```text
C/s
F^2
N*C
```

#### Decimal formatting
The CLI uses a small formatter:
- Zero becomes `0`.
- Values with exponent `< -6` or `>= 12` become scientific notation.
- Other values are normalized and trailing zeros are removed.

### Data Structures

#### `Dimension`
```python
@dataclass(frozen=True)
class Dimension:
    exponents: tuple[int, ...]
```

Purpose:
- Physical dimensional meaning.

#### `Unit`
```python
@dataclass(frozen=True)
class Unit:
    name: str
    symbol: str
    dimension: Dimension
    scale: Decimal
    offset: Decimal = Decimal("0")
```

Purpose:
- A named unit with a dimension, base scale, and optional affine offset.

#### `Quantity`
```python
@dataclass(frozen=True)
class Quantity:
    value: Decimal
    unit: Unit
```

Purpose:
- A numeric value associated with a unit.

#### `ConversionResult`
```python
@dataclass(frozen=True)
class ConversionResult:
    value: Decimal
    from_unit: Unit
    to_unit: Unit
    source: Quantity
    target: Quantity
```

Purpose:
- Return structure for library users and tests.

#### `Token`
```python
@dataclass(frozen=True)
class Token:
    kind: str
    value: str
```

Purpose:
- Parser token representation.

#### `UnitRegistry`
```python
class UnitRegistry:
    _units: dict[str, Unit]
    _prefixable: dict[str, Unit]
```

Purpose:
- Unit lookup and prefix expansion.

### State Management
Runtime state is minimal.

- The default registry is cached with `@lru_cache(maxsize=1)`.
- The parser stores `tokens` and an `index` during parsing.
- All scientific domain objects are immutable.
- The CLI does not write files or maintain sessions.
- No environment, config, or persistent state is required.

### Error Handling Strategy
The project uses a custom exception hierarchy for unit failures.

| Error | Trigger |
| --- | --- |
| `UnitError` | Base class for all unit-specific errors. |
| `ConformabilityError` | Source and target dimensions differ. |
| `UnknownUnitError` | Registry cannot resolve a unit name or prefixed unit. |
| `ParseError` | Unit expression syntax is invalid. |
| `ValueError` | Invalid dimension length or invalid non-domain argument. |
| `TypeError` | Non-integer dimension exponent. |

The CLI catches `UnitError`, writes `error: <message>` to stderr, and exits with status `2`.

### External Dependencies
Runtime dependencies:
- None beyond the Python standard library.

Development dependencies:
- `pytest`
- `pytest-cov`

Packaging:
- `setuptools>=69`
- Python `>=3.11`

### Concurrency Model
StrictUnits is single-threaded. There is no concurrency, no background work, and no async behavior. The only cached shared object is the default registry, which is read-only after construction during normal use.

### Known Limitations
- Unit catalog is intentionally small.
- No user-defined unit catalog.
- No interactive mode.
- No list/search command for supported units.
- No config file.
- No JSON/CSV output mode.
- No uncertainty propagation.
- No dimensional simplification display beyond dimension reduced forms.
- Parser only accepts integer powers.
- CLI error handling catches `UnitError`, but malformed numeric values from `Decimal` may surface as non-`UnitError` exceptions depending on invocation context.
- The package does not include `src/strictunits/__main__.py`, so `python -m strictunits` is not documented as supported; users should use `strictunits` after installation or `python main.py` from the repo.

### Design Patterns Used
- **Value Object:** `Dimension`, `Unit`, `Quantity`, `ConversionResult`.
- **Registry:** `UnitRegistry`.
- **Recursive-Descent Parser:** `UnitParser`.
- **Facade Function:** `convert`.
- **Custom Exception Hierarchy:** `UnitError` and subclasses.
- **Cached Singleton Factory:** `default_registry`.
- **Command Pattern, minimal form:** `argparse` subcommand dispatch for `convert`.

### Constitution Alignment
The implementation shows a clear move from beginner CLI scripting toward real domain modeling. It remains scoped, readable, and testable while demonstrating algebraic reasoning, immutability, strict validation, and command-line packaging.

---

# Interface Design Specification

## App 37 — Unit Converter
**Scientific Units Group | Document 3 of 5**

### Invocation Syntax

Installed console script:

```bash
strictunits convert <value> <from_unit> <to_unit>
```

Repository-local script:

```bash
python main.py convert <value> <from_unit> <to_unit>
```

Examples:

```bash
strictunits convert 5 miles km
strictunits convert 10 m/s km/h
strictunits convert 9.8 m/s^2 ft/s^2
strictunits convert 100 C F
```

### Argument Reference Table

| Argument | Type | Required | Default | Valid Values | Description |
| --- | --- | --- | --- | --- | --- |
| `command` | string | yes | none | `convert` | Selects the operation. Current CLI exposes only conversion. |
| `value` | string parsed as `Decimal` | yes | none | Decimal-compatible numeric text such as `5`, `9.8`, `1e3` | Numeric value to convert. |
| `from_unit` | string | yes | none | Unit expression | Source unit expression. |
| `to_unit` | string | yes | none | Unit expression | Target unit expression. |

### Unit Expression Contract
A unit expression may contain:
- Registered unit symbols, names, or aliases.
- Metric-prefixed units when the base unit is prefixable.
- Multiplication with `*`.
- Multiplication with `.` as a normalized alias.
- Division with `/`.
- Exponentiation with `^`.
- Exponentiation with `**`, normalized to `^`.
- Parentheses.
- Integer exponents.

Examples of valid expressions:

```text
m
km
miles
kg
s
h
m/s
km/h
m/s^2
kg*m/s^2
N
N*m
J
W/(m^2*K)
```

Examples of invalid expressions:

```text
                 # empty
m//s             # invalid syntax
m^x              # exponent is not integer
unknownunit      # not registered and not prefixable
C/s              # affine unit in compound expression
m kg             # spaces are removed, likely becoming invalid or unintended
```

### Registered Unit Categories
The default registry includes:

| Category | Examples |
| --- | --- |
| Length | `m`, `meter`, `km`, `in`, `ft`, `yd`, `mi`, `miles` |
| Mass | `g`, `kg`, `lb`, `pound` |
| Time | `s`, `ms`, `min`, `h`, `hr` |
| Electric current | `A`, `ampere` |
| Temperature | `K`, `C`, `degC`, `F`, `degF` |
| Amount | `mol` |
| Luminosity | `cd` |
| Force | `N`, `newton` |
| Energy | `J`, `joule` |
| Power | `W`, `watt` |
| Frequency | `Hz`, `hz`, `hertz` |

### Input Contract
- Input is command-line text.
- `value` must be convertible to `Decimal`.
- Units are case-sensitive where symbols require it. For example, `M` as mega prefix differs from `m` as meter or milli prefix depending on context.
- Unit expressions are stripped of spaces.
- Dot multiplication is accepted by replacing `.` with `*`.
- `**` is accepted by replacing it with `^`.
- Exponents must be integers.
- Source and target dimensions must match exactly.

### Output Contract
Successful conversion prints exactly one line:

```text
<formatted-decimal> <target-unit-symbol>
```

Examples:

```text
8.04672 km
36 km/h
212 degF
```

The exact target symbol is the symbol of the parsed target unit object. For generated prefixed units, the symbol may be the user-facing prefixed token, such as `km`.

### Exit Code Reference

| Exit Code | Meaning |
| ---: | --- |
| `0` | Conversion succeeded. |
| `2` | CLI parse failure or unit-domain error. |

### Error Output Behavior
For unit-specific failures, stderr receives:

```text
error: <message>
```

Examples:

```text
error: cannot convert 'm' [L] to 'kg' [M]
error: unknown unit 'banana'
error: expected ')' to close unit group
error: affine units such as Celsius and Fahrenheit cannot be used in compound units
```

The error format is human-readable. It is not structured JSON.

### Environment Variables
No project-specific environment variables are read.

Relevant ambient behavior:
- Python’s `Decimal` behavior is used for numeric representation.
- Python’s module search path matters only when running from source without installation.

### Configuration Files
No configuration file is used.

### Side Effects
Normal conversion has no filesystem, network, or system side effects.

The only repository-local side effect is from `main.py`, which inserts the local `src` directory into `sys.path` so source-tree execution can import `strictunits`.

### Usage Examples

#### Basic length conversion
```bash
strictunits convert 5 miles km
```

Expected shape:
```text
8.04672 km
```

#### Speed conversion
```bash
strictunits convert 10 m/s km/h
```

Expected shape:
```text
36 km/h
```

#### Acceleration conversion
```bash
strictunits convert 9.8 m/s^2 ft/s^2
```

Expected shape:
```text
32.152230971128608923884514 ft/s^2
```

Exact precision may depend on `Decimal` arithmetic representation.

#### Temperature conversion
```bash
strictunits convert 100 C F
```

Expected shape:
```text
212 degF
```

#### Parenthesized compound expression
```bash
strictunits convert 1 W/(m^2*K) kg/(s^3*K)
```

Expected shape:
```text
1 kg/s^3*K
```

The exact printed symbol is based on parser composition.

#### Intentional failure: incompatible dimensions
```bash
strictunits convert 5 m kg
```

Expected stderr:
```text
error: cannot convert 'm' [L] to 'kg' [M]
```

Expected exit:
```text
2
```

#### Intentional failure: unknown unit
```bash
strictunits convert 5 smoot m
```

Expected stderr shape:
```text
error: unknown unit 'smoot'
```

#### Intentional failure: affine compound unit
```bash
strictunits convert 1 C/s K/s
```

Expected stderr shape:
```text
error: affine units such as Celsius and Fahrenheit cannot be used in compound units
```

### Interface Stability Notes
The core public library interface is more stable than the CLI surface. `convert(value, from_expression, to_expression)` and the domain objects are the natural extension points. Future CLI additions should preserve the existing `convert` command syntax.

---

# Runbook

## App 37 — Unit Converter
**Scientific Units Group | Document 4 of 5**

### Prerequisites
- Python 3.11 or newer.
- A terminal shell.
- No runtime third-party dependencies.
- `pytest` and `pytest-cov` only if running tests or coverage.

Supported operating systems should include any OS with Python 3.11+, because the application uses only the standard library.

### Installation Procedure

#### Option A — Install from the repository
```bash
cd Unit-Converter
python -m pip install -r requirements.txt
```

This installs the package in editable mode because `requirements.txt` contains:

```text
-e .
pytest
pytest-cov
```

Then verify the script:

```bash
strictunits convert 5 miles km
```

#### Option B — Install package only
```bash
cd Unit-Converter
python -m pip install -e .
```

Then run:

```bash
strictunits convert 10 m/s km/h
```

#### Option C — Run without installing
```bash
cd Unit-Converter
python main.py convert 5 miles km
```

`main.py` prepends the local `src` directory to `sys.path`.

### Configuration Steps
No configuration is required.

There is no config file, no registry file, and no environment variable setup.

### Standard Operating Procedures

#### Convert a simple length
```bash
strictunits convert 5 miles km
```

#### Convert speed
```bash
strictunits convert 10 m/s km/h
```

#### Convert acceleration
```bash
strictunits convert 9.8 m/s^2 ft/s^2
```

#### Convert temperature
```bash
strictunits convert 100 C F
```

#### Use derived units
```bash
strictunits convert 3 N*m J
```

#### Use grouped expressions
```bash
strictunits convert 1 W/(m^2*K) kg/(s^3*K)
```

### Health Checks

#### CLI help
```bash
strictunits --help
```

Expected:
- Usage output appears.
- Exit code is `0`.

#### Convert command help
```bash
strictunits convert --help
```

Expected:
- Help for `value`, `from_unit`, and `to_unit`.
- Exit code is `0`.

#### Known conversion
```bash
strictunits convert 5 miles km
```

Expected:
```text
8.04672 km
```

#### Incompatible conversion should fail
```bash
strictunits convert 5 m kg
```

Expected:
- Error to stderr.
- Exit code `2`.

#### Test suite
```bash
python -m pytest -q
```

Expected:
- Tests pass.

#### Coverage
```bash
python -m pytest --cov=src/strictunits --cov-report=term-missing -q
```

Expected:
- Coverage report generated in terminal.

### Expected Output Samples

#### Miles to kilometers
```text
8.04672 km
```

#### Meters per second to kilometers per hour
```text
36 km/h
```

#### Celsius to Fahrenheit
```text
212 degF
```

#### Unknown unit
```text
error: unknown unit 'smoot'
```

#### Incompatible dimensions
```text
error: cannot convert 'm' [L] to 'kg' [M]
```

### Known Failure Modes

| Symptom | Probable Cause | Diagnostic Step | Resolution |
| --- | --- | --- | --- |
| `strictunits: command not found` | Package not installed or venv not active. | Run `python -m pip show strictunits`. | Activate the venv and run `python -m pip install -e .`. |
| `ModuleNotFoundError: strictunits` | Running from source without install and not using `main.py`. | Check invocation. | Use `python main.py ...` or install editable package. |
| `error: unknown unit 'x'` | Unit not registered or prefix cannot be resolved. | Try base unit symbol or known alias. | Use a supported unit or extend registry in code. |
| `error: cannot convert ...` | Source and target dimensions differ. | Compare dimensions in the error. | Choose physically compatible units. |
| `error: expected ')' to close unit group` | Unit expression syntax error. | Inspect parentheses. | Fix grouping. |
| `error: affine units ... cannot be used in compound units` | Celsius or Fahrenheit used in multiplication/division/power. | Check unit expression. | Use Kelvin for compound temperature dimensions. |
| Unexpected many decimal places | Decimal conversion preserves exact rational-like scale behavior. | Re-run with known examples. | Add presentation rounding in future version if needed. |
| `python -m strictunits` fails | No package `__main__.py` is present. | Check `src/strictunits/__main__.py`. | Use `strictunits` or `python main.py`. |

### Troubleshooting Decision Tree

```text
Command does not start
    |
    +-- Is the package installed?
    |       |
    |       +-- No -> python -m pip install -e .
    |       |
    |       +-- Yes -> Is venv active?
    |               |
    |               +-- No -> activate venv
    |               +-- Yes -> check PATH / console script
    |
Conversion fails
    |
    +-- Error says unknown unit?
    |       |
    |       +-- Check spelling, symbol, case, and aliases
    |
    +-- Error says cannot convert?
    |       |
    |       +-- Source and target dimensions differ
    |       +-- Choose compatible units
    |
    +-- Error says parse problem?
    |       |
    |       +-- Check operators, exponents, and parentheses
    |
    +-- Error says affine units cannot be compound?
            |
            +-- Use K instead of C/F in compound expressions
```

### Dependency Failure Handling
There are no runtime dependencies. For test dependencies:

| Dependency | Failure | Resolution |
| --- | --- | --- |
| `pytest` | `No module named pytest` | Run `python -m pip install -r requirements.txt`. |
| `pytest-cov` | Coverage option not recognized | Install `pytest-cov`. |
| `setuptools` | Editable install fails | Upgrade pip/setuptools with `python -m pip install --upgrade pip setuptools`. |

### Recovery Procedures

#### Broken local install
```bash
python -m pip uninstall strictunits -y
python -m pip install -e .
```

#### Broken venv
```bash
deactivate
rm -rf .venv
python -m venv .venv
# activate venv
python -m pip install -r requirements.txt
```

#### Failing parser examples
Reduce the expression to smaller pieces:

```bash
strictunits convert 1 m m
strictunits convert 1 s s
strictunits convert 1 m/s m/s
strictunits convert 1 m/s^2 m/s^2
```

Then reintroduce the target expression.

### Logging Reference
The application does not implement logging. Errors are printed directly to stderr in CLI mode.

### Maintenance Notes
- Keep dimension algebra tests strong; a small change can affect every derived unit.
- Add unit catalog entries through `UnitRegistry.register`, not by special-casing `convert`.
- Be careful with affine units; they are deliberately restricted in compound unit operations.
- Consider adding `src/strictunits/__main__.py` if module execution becomes a user expectation.
- Consider adding a `list-units` command once the registry grows.
- Consider explicit rounding/precision options only after preserving exact default behavior.
- The duplicate constructor definition in `Dimension` should be cleaned up to reduce reader confusion.

### Constitution Alignment
The runbook demonstrates verifiability through known conversion checks, intentional failure checks, and the pytest workflow. The operational scope remains appropriately small for a CLI learning project.

---

# Lessons Learned

## App 37 — Unit Converter
**Scientific Units Group | Document 5 of 5**

### Project Summary
StrictUnits is a small but architecturally meaningful scientific unit converter. It accepts numeric values and unit expressions, parses those expressions into composable unit objects, verifies physical compatibility through dimensional analysis, and converts values using `Decimal` scale and offset arithmetic.

The strongest part of the project is that correctness is built into the model. A meter is not merely a string category called “length”; it is a unit with a dimension vector. A newton is not merely a named conversion factor; it is equivalent to `kg*m/s^2` because both share the same dimension and scale. That makes the project more rigorous than a typical beginner unit converter.

### Original Goals vs. Actual Outcome

#### Original Goals
- Build a scientific unit converter.
- Avoid unsafe string matching.
- Support common units.
- Support compound expressions.
- Reject incompatible conversions.
- Provide a working CLI.

#### Actual Outcome
The implementation meets the main goals. It supports strict dimensional checks, compound parsing, metric prefixes, derived units, and affine temperature conversion. The CLI is intentionally small but functional. The design is library-first: the public `convert` function and domain objects are more important than the shell wrapper.

### Technical Decisions That Paid Off

#### Using a seven-vector dimension model
This decision made compatibility exact and general. It avoids maintaining a separate rule for every pair of categories.

#### Making domain objects immutable
`Dimension`, `Unit`, `Quantity`, and `ConversionResult` are frozen dataclasses. This makes unit composition safer and easier to reason about.

#### Using `Decimal`
`Decimal` avoids casual binary floating-point surprises and is a sensible choice for a converter where users expect stable numeric output.

#### Recursive-descent parsing
A small parser was enough for the grammar. It supports names, multiplication, division, exponentiation, and parentheses without requiring a parser generator.

#### Registry-based unit lookup
The registry keeps unit definitions centralized. This makes the core converter independent of the initial catalog.

#### Blocking affine units in compound expressions
This avoids mathematically invalid operations involving Celsius and Fahrenheit while still allowing direct temperature conversion.

### Technical Decisions That Created Debt

#### No registry listing interface
Users cannot ask the CLI which units are supported. This is acceptable for a first version but becomes a usability issue as the registry grows.

#### No custom unit definitions
Users cannot add domain-specific units without editing code. That keeps scope small but limits extensibility.

#### Minimal CLI
The CLI only exposes `convert`. There are no `list`, `explain`, `parse`, `dimensions`, or `aliases` commands.

#### Duplicate `Dimension.__init__`
The class contains two constructor definitions, with the second one overriding the first. Behavior is still driven by the second constructor, but the duplicate should be removed.

#### Formatting is fixed
The formatter chooses normal or scientific output but does not expose precision or rounding options.

### What Was Harder Than Expected
- Supporting temperature correctly, because Celsius and Fahrenheit require offsets while most unit algebra assumes linear scaling.
- Handling compound units without accidentally permitting affine composition.
- Designing prefix expansion without permanently registering every possible prefixed unit.
- Writing parser errors that are clear enough for command-line users.
- Making unit algebra readable without turning the project into a large physics library.

### What Was Easier Than Expected
- Representing dimensions as exponent tuples once the seven SI base dimensions were chosen.
- Implementing multiplication/division/power for dimensions and units.
- Building a small `argparse` CLI around a clean library function.
- Testing known conversions such as miles to kilometers and Celsius to Fahrenheit.
- Modeling derived units by composing base dimensions.

### Python-Specific Learnings

#### Frozen dataclasses
Frozen dataclasses are a good fit for scientific value objects. They communicate that a dimension or unit should not change after creation.

#### `Decimal`
`Decimal(str(value))` is a better input path than `Decimal(float_value)` when accepting CLI strings.

#### `functools.lru_cache`
A cached `default_registry()` avoids rebuilding the unit catalog every time while keeping initialization simple.

#### `dataclasses.replace`
`replace` is useful for generating prefixed unit variants from base units without mutating the base registry object.

#### `argparse`
A small subcommand interface can still be clean and professional when the application has one main use case.

### Architecture Insights
The main insight is that **domain modeling can replace fragile conditionals**. Once units know their dimensions, the converter does not need to remember that velocity belongs with velocity, force belongs with force, or energy belongs with energy. The algebra answers that.

Another insight is that a small project can still justify separate modules. The project is not large, but each module has a clear reason to exist:
- `dimensions` for physical meaning.
- `units` for unit algebra.
- `registry` for unit definitions.
- `parser` for expression parsing.
- `quantity` for value/unit pairing.
- `conversion` for the use case.
- `cli` for user interface.

This is an example of Article 3’s small multi-file exception: the files are small, focused, and single-responsibility.

### Testing Gaps
The existing tests cover important behavior:
- Dimension validation and algebra.
- Miles to kilometers.
- Meters per second to kilometers per hour.
- Force equivalence.
- Energy equivalence.
- Incompatible conversion failure.
- Celsius/Fahrenheit conversion.
- Parenthesized compound expressions.

Possible additional tests:
- CLI success and CLI failure paths.
- Unknown unit errors.
- Parser malformed syntax cases.
- Affine unit compound rejection.
- Prefix ambiguity such as `dam` versus `dm`.
- Formatting edge cases for very small and very large numbers.
- Quantity arithmetic beyond conversion.
- Registry alias behavior.
- `main.py` source-tree execution path.

### Reusable Patterns Identified
- Use algebraic value objects when the domain has mathematical rules.
- Keep parsers separate from business logic.
- Use registries for domain catalogs.
- Convert user input into typed domain objects as early as possible.
- Make invalid states difficult to represent.
- Keep CLI code thin and let the library own behavior.
- Test both success cases and intentional failure cases.

### If I Built This Again
I would keep the dimension-first architecture. I would add:

1. `strictunits list-units`
2. `strictunits explain m/s^2`
3. `strictunits dimensions N`
4. `strictunits aliases meter`
5. Optional precision/rounding flags.
6. `src/strictunits/__main__.py` for `python -m strictunits`.
7. A custom registry file for user-defined units.
8. Better parser diagnostics with token positions.
9. Cleanup of the duplicate `Dimension.__init__`.
10. More CLI integration tests.

### Open Questions
- Should the project support rational scale factors rather than only `Decimal`?
- Should angles be dimensionless or a separate pseudo-dimension?
- Should temperature differences be modeled separately from absolute temperatures?
- Should the CLI expose the base dimension vector of parsed units?
- Should user-defined units be stored in TOML or JSON?
- Should output formatting default to exact values or rounded human-friendly values?
- How broad should the unit catalog become before maintainability suffers?

### Constitution Reflection
StrictUnits is valid under the Constitution. It is authentic in scope, appropriately sized, and intentionally designed around a real domain constraint. It demonstrates Python fundamentals, modular architecture, verification through tests, and honest trade-offs. Its imperfections are concrete and teachable rather than signs of architectural failure.
