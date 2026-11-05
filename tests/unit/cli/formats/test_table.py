from __future__ import annotations

import io
from datetime import datetime, timezone

from moovi.cli.formats.table import TableFormatter
from moovi.cli.tables.base import Column, RichValue


def render(table) -> str:
    output = io.StringIO()
    TableFormatter(output).render(table)
    return output.getvalue()


def test_horizontal_table(make_table) -> None:
    table = make_table(
        [Column("id", "ID"), Column("name", "NOMBRE")],
        [(1, "Ana"), (2, "Luis")],
    )

    text = render(table)

    assert "ID" in text
    assert "NOMBRE" in text
    assert "Ana" in text
    assert "Luis" in text


def test_hidden_columns_are_not_rendered(make_table) -> None:
    table = make_table(
        [Column("id", "ID"), Column("internal", "INTERNO", table=False)],
        [(1, "secreto")],
    )

    text = render(table)

    assert "INTERNO" not in text
    assert "secreto" not in text


def test_rich_value_uses_text_and_keeps_multiline(make_table) -> None:
    table = make_table(
        [Column("message", "MENSAJE")],
        [
            (
                RichValue(
                    raw="<p>Hola</p><p>Mundo</p>",
                    text="Hola\nMundo",
                    json_text=True,
                ),
            )
        ],
    )

    text = render(table)

    assert "Hola" in text
    assert "Mundo" in text
    assert "<p>" not in text


def test_single_row_is_rendered_as_a_detail_view(make_table) -> None:
    table = make_table(
        [
            Column("subject", "ASUNTO"),
            Column("created", "FECHA"),
            Column("message", "MENSAJE"),
        ],
        [
            (
                "Aviso",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                RichValue(raw="<p>Hola</p>", text="Hola\nMundo"),
            )
        ],
        single_row=True,
    )

    text = render(table)

    assert "ASUNTO: Aviso" in text
    assert "FECHA: 2024-01-01 00:00 UTC" in text
    assert "MENSAJE: Hola" in text
    assert "  Mundo" in text


def test_empty_table(make_table) -> None:
    table = make_table([Column("id", "ID")], [])

    assert render(table) == "(sin resultados)\n"


def test_mismatched_row_length_fails(make_table) -> None:
    table = make_table([Column("id", "ID")], [(1, 2)])

    try:
        render(table)
    except ValueError as exc:
        assert "columnas" in str(exc)
    else:
        raise AssertionError("La fila inválida no ha fallado")
