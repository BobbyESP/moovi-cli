"""Utilidades genéricas de formato."""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from typing import Any, TextIO

from moovi.cli.tables.base import RichValue
from moovi.cli.text import flatten_text


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


def table_value(value: object) -> str:
    if isinstance(value, RichValue):
        return value.text
    if isinstance(value, datetime):
        return format_datetime(value)
    if isinstance(value, bool):
        return "sí" if value else "no"
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def csv_value(value: object) -> str:
    if isinstance(value, RichValue):
        text = value.csv_text if value.csv_text is not None else value.text
        return flatten_text(text)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)
