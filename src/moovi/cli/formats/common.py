"""Helpers compartidos por los formatters."""

from __future__ import annotations

import dataclasses
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any, TextIO

from moovi.domain.models import Role

_ROLE_LABELS = {
    "student": "Alumno/a",
    "editingteacher": "Profesor/a",
    "teacher": "Profesor/a",
    "guestteacher": "Profesor/a invitado/a",
    "manager": "Gestor/a",
    "coursecreator": "Creador/a de cursos",
    "guest": "Invitado/a",
}

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


def write_json(value: Any, stream: TextIO) -> None:
    json.dump(to_jsonable(value), stream, ensure_ascii=False, indent=2)
    stream.write("\n")


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M UTC")


def iso_datetime(value: datetime | None) -> str:
    return value.isoformat() if value is not None else ""


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def format_grade(value: float | None, *, missing: str = "—") -> str:
    if value is None:
        return missing
    return f"{value:g}"


def role_label(role: Role) -> str:
    if role.name:
        return role.name
    if role.short_name:
        return _ROLE_LABELS.get(role.short_name, role.short_name)
    return f"Rol {role.id}" if role.id else "—"


def role_key(role: Role) -> str:
    if role.short_name:
        return role.short_name
    if role.name:
        return role.name
    return f"role_{role.id}" if role.id else ""


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


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"
