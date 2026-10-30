"""Formato de tabla para humanos."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from moovi.cli.formats.common import (
    format_datetime,
    format_grade,
    role_label,
    shorten,
    strip_html,
)
from moovi.domain.models import (
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)


class TableFormatter:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def site_info(self, info: SiteInfo) -> None:
        self._stream.write(
            f"Usuario: {info.full_name} ({info.username}, id {info.user_id})\n"
        )
        self._stream.write(f"Sitio: {info.site_name} — {info.release}\n")
        self._stream.write(f"Funciones disponibles: {len(info.functions)}\n")

    def courses(self, courses: Sequence[Course]) -> None:
        rows = [
            [
                str(course.id),
                course.short_name,
                course.full_name,
                "sí" if course.visible else "no",
            ]
            for course in courses
        ]
        self._table(["ID", "SHORTNAME", "NOMBRE", "VISIBLE"], rows)

    def sections(self, sections: Sequence[Section]) -> None:
        if not sections:
            self._stream.write("(sin secciones)\n")
            return
        for section in sections:
            name = strip_html(section.name) or f"Sección {section.id}"
            self._stream.write(f"## {name}\n")
            summary = strip_html(section.summary)
            if summary:
                self._stream.write(f"   {shorten(summary, 300)}\n")
            for module in section.modules:
                hidden = "" if module.visible else " (oculta)"
                self._stream.write(
                    f"  - [{module.mod_name}] {strip_html(module.name)}{hidden}\n"
                )
            self._stream.write("\n")

    def participants(
        self,
        participants: Sequence[Participant],
        *,
        include_email: bool,
    ) -> None:
        headers = ["ID", "NOMBRE", "ROLES", "ÚLTIMO ACCESO"]
        if include_email:
            headers.append("EMAIL")
        rows: list[list[str]] = []
        for participant in participants:
            row = [
                str(participant.id),
                participant.full_name,
                ", ".join(role_label(role) for role in participant.roles) or "—",
                format_datetime(participant.last_access),
            ]
            if include_email:
                row.append(participant.email or "—")
            rows.append(row)
        self._table(headers, rows)

    def assignments(self, assignments: Sequence[Assignment]) -> None:
        rows = [
            [
                str(assignment.id),
                assignment.name,
                format_datetime(assignment.due_date),
                format_datetime(assignment.cutoff_date),
                format_grade(assignment.max_grade),
            ]
            for assignment in assignments
        ]
        self._table(
            ["ID", "NOMBRE", "ENTREGA", "CIERRE", "NOTA MÁX."], rows
        )

    def _table(self, headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
        if not rows:
            self._stream.write("(sin resultados)\n")
            return

        widths = [len(header) for header in headers]
        for row in rows:
            for index, cell in enumerate(row):
                widths[index] = max(widths[index], len(cell))

        self._stream.write(
            "  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip() + "\n"
        )
        self._stream.write(
            "  ".join("-" * w for w in widths).rstrip() + "\n"
        )
        for row in rows:
            self._stream.write(
                "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip()
                + "\n"
            )
