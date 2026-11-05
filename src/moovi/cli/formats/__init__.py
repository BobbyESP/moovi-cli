"""Selección del formato de presentación."""

from __future__ import annotations

import sys
from typing import TextIO

from moovi.cli.formats.base import Formatter
from moovi.cli.formats.csv import CsvFormatter
from moovi.cli.formats.json import JsonFormatter
from moovi.cli.formats.table import TableFormatter

FORMATTERS = {
    "table": TableFormatter,
    "json": JsonFormatter,
    "raw": CsvFormatter,
}
FORMATS = tuple(FORMATTERS)


def create_formatter(
    name: str, stream: TextIO | None = None
) -> Formatter:
    target = stream or sys.stdout
    return FORMATTERS[name](target)
