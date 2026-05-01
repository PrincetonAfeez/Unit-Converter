from __future__ import annotations

import re
from dataclasses import dataclass

from .exceptions import ParseError
from .registry import UnitRegistry, default_registry
from .units import Unit


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|[-+]?\d+|\^|[*/()]")

