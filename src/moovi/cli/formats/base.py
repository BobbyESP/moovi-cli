"""Contrato de los formatters de salida."""

from __future__ import annotations

from typing import Protocol

from moovi.cli.tables.base import Table


class Formatter(Protocol):
    def render(self, table: Table) -> None: ...
