"""Formato raw: CSV plano para componer con grep, sort, cut o awk."""

from __future__ import annotations

import csv
import sys
from collections.abc import Sequence
from typing import TextIO

from moovi.cli.formats.base import Formatter
from moovi.cli.formats.common import csv_value
from moovi.cli.tables.base import Column, Table, row_items


class CsvFormatter(Formatter):
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout
        self._writer = csv.writer(self._stream, lineterminator="\n")

    def render(self, table: Table) -> None:
        columns = [column for column in table.columns if column.csv]
        self._writer.writerow(
            [column.csv_key or column.key for column in columns]
        )
        for row in table.rows:
            values = _visible_values(table, columns, row)
            self._writer.writerow([csv_value(value) for value in values])


def _visible_values(
    table: Table, columns: Sequence[Column], row: Sequence[object]
) -> list[object]:
    return [
        value
        for column, value in row_items(table, row)
        if column.csv
    ]
