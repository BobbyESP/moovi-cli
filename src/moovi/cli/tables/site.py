"""Tabla de datos del sitio y el usuario autenticado."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, RichValue, Table
from moovi.domain.models import SiteInfo


class SiteInfoTable(Table):
    def __init__(self, info: SiteInfo) -> None:
        self._info = info

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("user_id", "ID"),
            Column("username", "USUARIO"),
            Column("full_name", "NOMBRE"),
            Column("site_name", "SITIO"),
            Column("release", "VERSIÓN"),
            Column("functions", "FUNCIONES", csv_key="functions_count"),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        info = self._info
        return [
            (
                info.user_id,
                info.username,
                info.full_name,
                info.site_name,
                info.release,
                RichValue(
                    raw=info.functions,
                    text=str(len(info.functions)),
                    csv_text=str(len(info.functions)),
                ),
            )
        ]

    @property
    def single_row(self) -> bool:
        return True
