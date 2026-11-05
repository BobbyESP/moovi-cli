"""Formato JSON."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any, TextIO

from moovi.cli.formats.base import Formatter
from moovi.cli.formats.common import to_jsonable, write_json
from moovi.cli.tables.base import RichValue, Table, row_items


class JsonFormatter(Formatter):
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def render(self, table: Table) -> None:
        data = [_row_to_dict(table, row) for row in table.rows]
        payload: object = data[0] if table.single_row and data else data
        write_json(payload, self._stream)


def _row_to_dict(table: Table, row: Sequence[object]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column, value in row_items(table, row):
        if isinstance(value, RichValue):
            result[column.key] = to_jsonable(value.raw)
            if value.json_text:
                result[f"{column.key}_text"] = value.text
        else:
            result[column.key] = to_jsonable(value)
    return result
