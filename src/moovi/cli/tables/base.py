"""Contrato de las tablas de datos que consumen los formatters."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Column:
    key: str
    header: str
    table: bool = True
    csv: bool = True
    csv_key: str | None = None


@dataclass(frozen=True, slots=True)
class RichValue:
    """Valor con representaciones distintas para JSON y para tabla/CSV."""

    raw: object
    text: str
    csv_text: str | None = None
    json_text: bool = False


class Table(Protocol):
    @property
    def columns(self) -> Sequence[Column]: ...

    @property
    def rows(self) -> Sequence[Sequence[object]]: ...

    @property
    def single_row(self) -> bool: ...


def row_items(table: Table, row: Sequence[object]) -> Iterator[tuple[Column, object]]:
    if len(row) != len(table.columns):
        raise ValueError(
            f"La fila tiene {len(row)} valores y la tabla "
            f"{len(table.columns)} columnas"
        )
    yield from zip(table.columns, row)
