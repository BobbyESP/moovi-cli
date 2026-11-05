from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from moovi.cli.tables.base import Column, Table


class FakeTable(Table):
    def __init__(
        self,
        columns: Sequence[Column],
        rows: Sequence[Sequence[object]],
        *,
        single_row: bool = False,
    ) -> None:
        self._columns = columns
        self._rows = rows
        self._single_row = single_row

    @property
    def columns(self) -> Sequence[Column]:
        return self._columns

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return self._rows

    @property
    def single_row(self) -> bool:
        return self._single_row


@pytest.fixture
def make_table():
    def _make(
        columns: Sequence[Column],
        rows: Sequence[Sequence[object]],
        *,
        single_row: bool = False,
    ) -> FakeTable:
        return FakeTable(columns, rows, single_row=single_row)

    return _make
