"""Selección del formato de presentación."""

from __future__ import annotations

import sys
from typing import TextIO

from moovi.cli.formats.base import Formatter
from moovi.cli.formats.csv import CsvFormatter
from moovi.cli.formats.json import JsonFormatter
from moovi.cli.formats.table import TableFormatter

FORMATS = ("table", "json", "raw")


def create_formatter(
    name: str, stream: TextIO | None = None
) -> Formatter:
    target = stream or sys.stdout
    if name == "json":
        return JsonFormatter(target)
    if name == "raw":
        return CsvFormatter(target)
    return TableFormatter(target)
