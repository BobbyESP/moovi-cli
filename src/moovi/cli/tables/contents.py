"""Tabla de datos del contenido de un curso."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, RichValue, Table
from moovi.cli.text import html_to_text
from moovi.domain.models import Section


class ContentsTable(Table):
    def __init__(self, sections: Sequence[Section]) -> None:
        self._sections = sections

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("id", "ID", csv_key="section_id"),
            Column("name", "SECCIÓN", csv_key="section_name"),
            Column("summary", "RESUMEN", csv_key="summary_text"),
            Column("modules", "MÓDULOS"),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        rows: list[Sequence[object]] = []
        for section in self._sections:
            modules_text = "\n".join(
                f"[{module.mod_name}] {module.name}"
                + ("" if module.visible else " (oculta)")
                for module in section.modules
            )
            modules_csv = ";".join(
                f"{module.mod_name}:{module.name}:{'1' if module.visible else '0'}"
                for module in section.modules
            )
            rows.append(
                (
                    section.id,
                    section.name,
                    RichValue(
                        raw=section.summary,
                        text=html_to_text(section.summary),
                        json_text=True,
                    ),
                    RichValue(
                        raw=section.modules,
                        text=modules_text,
                        csv_text=modules_csv,
                    ),
                )
            )
        return rows

    @property
    def single_row(self) -> bool:
        return False
