from __future__ import annotations

import io
import json
from datetime import datetime, timezone

from moovi.cli.formats.json import JsonFormatter
from moovi.cli.tables.base import Column, RichValue


def render(table):
    output = io.StringIO()
    JsonFormatter(output).render(table)
    return json.loads(output.getvalue())


def test_numbers_and_dates_keep_their_type(make_table) -> None:
    table = make_table(
        [Column("id", "ID"), Column("created", "FECHA")],
        [(7, datetime(2024, 1, 1, tzinfo=timezone.utc))],
    )

    data = render(table)

    assert data == [{"id": 7, "created": "2024-01-01T00:00:00+00:00"}]


def test_rich_value_uses_raw_and_adds_text_when_requested(make_table) -> None:
    table = make_table(
        [Column("message", "MENSAJE")],
        [
            (
                RichValue(
                    raw="<p>Hola</p>",
                    text="Hola",
                    json_text=True,
                ),
            )
        ],
    )

    [row] = render(table)

    assert row["message"] == "<p>Hola</p>"
    assert row["message_text"] == "Hola"


def test_rich_value_without_json_text_does_not_add_companion(make_table) -> None:
    table = make_table(
        [Column("roles", "ROLES")],
        [(RichValue(raw=("student",), text="Alumno/a"),)],
    )

    [row] = render(table)

    assert row["roles"] == ["student"]
    assert "roles_text" not in row


def test_single_row_outputs_an_object(make_table) -> None:
    table = make_table(
        [Column("subject", "ASUNTO")],
        [("Aviso",)],
        single_row=True,
    )

    assert render(table) == {"subject": "Aviso"}
