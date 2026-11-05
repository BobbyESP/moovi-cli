"""Formato de tabla para humanos."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from moovi.cli.formats.base import Formatter
from moovi.cli.formats.common import table_value
from moovi.cli.tables.base import Column, Table, row_items


class TableFormatter(Formatter):
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def render(self, table: Table) -> None:
        columns = [column for column in table.columns if column.table]
        if not table.rows:
            self._stream.write("(sin resultados)\n")
            return
        if table.single_row:
            self._render_single(table, columns)
            return
        self._render_grid(table, columns)

    def _render_single(self, table: Table, columns: Sequence[Column]) -> None:
        values = _visible_values(table, columns, table.rows[0])
        for column, value in zip(columns, values):
            lines = table_value(value).splitlines() or [""]
            self._stream.write(f"{column.header}: {lines[0]}\n")
            for line in lines[1:]:
                self._stream.write(f"  {line}\n")

    def _render_grid(self, table: Table, columns: Sequence[Column]) -> None:
        rendered_rows: list[list[list[str]]] = []
        for row in table.rows:
            values = _visible_values(table, columns, row)
            rendered_rows.append(
                [table_value(value).splitlines() or [""] for value in values]
            )

        headers = [column.header for column in columns]
        widths = [len(header) for header in headers]
        for row in rendered_rows:
            for index, lines in enumerate(row):
                widths[index] = max(widths[index], *(len(line) for line in lines))

        self._write_line(headers, widths)
        self._write_line(["-" * width for width in widths], widths)
        for row in rendered_rows:
            height = max((len(lines) for lines in row), default=1)
            for line_index in range(height):
                cells = [
                    lines[line_index] if line_index < len(lines) else ""
                    for lines in row
                ]
                self._write_line(cells, widths)

    def _write_line(self, cells: Sequence[str], widths: Sequence[int]) -> None:
        self._stream.write(
            "  ".join(cell.ljust(width) for cell, width in zip(cells, widths)).rstrip()
            + "\n"
        )


def _visible_values(
    table: Table, columns: Sequence[Column], row: Sequence[object]
) -> list[object]:
    return [
        value
        for column, value in row_items(table, row)
        if column.table
    ]
