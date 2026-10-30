"""Renderizado de modelos de dominio: JSON, tablas y texto."""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from collections.abc import Sequence
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, TextIO

from moovi.domain.models import (
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)

_BLOCK_TAGS = frozenset(
    {
        "br",
        "p",
        "div",
        "li",
        "tr",
        "ul",
        "ol",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
    }
)


def to_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def print_json(value: Any, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    json.dump(to_jsonable(value), target, ensure_ascii=False, indent=2)
    target.write("\n")


def print_error(
    error: Exception, *, as_json: bool, stream: TextIO | None = None
) -> None:
    target = stream or sys.stderr
    if as_json:
        json.dump(
            {
                "error": {
                    "type": type(error).__name__,
                    "code": getattr(error, "code", None),
                    "message": str(error),
                }
            },
            target,
            ensure_ascii=False,
        )
        target.write("\n")
    else:
        target.write(f"Error: {error}\n")


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M UTC")


def strip_html(text: str) -> str:
    if not text:
        return ""
    parser = _TextExtractor()
    parser.feed(text)
    parser.close()
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in "".join(parser.parts).splitlines()
    ]
    return "\n".join(line for line in lines if line)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def render_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    stream: TextIO | None = None,
) -> None:
    target = stream or sys.stdout
    if not rows:
        target.write("(sin resultados)\n")
        return

    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    target.write("  ".join(h.ljust(w) for h, w in zip(headers, widths)).rstrip() + "\n")
    target.write("  ".join("-" * w for w in widths).rstrip() + "\n")
    for row in rows:
        target.write(
            "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip() + "\n"
        )


def render_site_info(info: SiteInfo, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    target.write(f"Usuario: {info.full_name} ({info.username}, id {info.user_id})\n")
    target.write(f"Sitio: {info.site_name} — {info.release}\n")
    target.write(f"Funciones disponibles: {len(info.functions)}\n")


def render_courses(courses: Sequence[Course], stream: TextIO | None = None) -> None:
    rows = [
        [
            str(course.id),
            course.short_name,
            course.full_name,
            "sí" if course.visible else "no",
        ]
        for course in courses
    ]
    render_table(["ID", "SHORTNAME", "NOMBRE", "VISIBLE"], rows, stream)


def render_sections(sections: Sequence[Section], stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    if not sections:
        target.write("(sin secciones)\n")
        return
    for section in sections:
        name = strip_html(section.name) or f"Sección {section.id}"
        target.write(f"## {name}\n")
        summary = strip_html(section.summary)
        if summary:
            target.write(f"   {_shorten(summary, 300)}\n")
        for module in section.modules:
            hidden = "" if module.visible else " (oculta)"
            target.write(
                f"  - [{module.mod_name}] {strip_html(module.name)}{hidden}\n"
            )
        target.write("\n")


def render_participants(
    participants: Sequence[Participant],
    *,
    include_email: bool = False,
    stream: TextIO | None = None,
) -> None:
    headers = ["ID", "NOMBRE", "ROLES", "ÚLTIMO ACCESO"]
    if include_email:
        headers.append("EMAIL")
    rows: list[list[str]] = []
    for participant in participants:
        row = [
            str(participant.id),
            participant.full_name,
            ", ".join(participant.roles) or "—",
            format_datetime(participant.last_access),
        ]
        if include_email:
            row.append(participant.email or "—")
        rows.append(row)
    render_table(headers, rows, stream)


def render_assignments(
    assignments: Sequence[Assignment], stream: TextIO | None = None
) -> None:
    rows = [
        [
            str(assignment.id),
            assignment.name,
            format_datetime(assignment.due_date),
            format_datetime(assignment.cutoff_date),
            _format_grade(assignment.max_grade),
        ]
        for assignment in assignments
    ]
    render_table(
        ["ID", "NOMBRE", "ENTREGA", "CIERRE", "NOTA MÁX."], rows, stream
    )


def _format_grade(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:g}"


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
