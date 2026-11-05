from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from moovi.cli.formats.csv import CsvFormatter
from moovi.cli.tables.base import Column, RichValue


def render(table) -> list[list[str]]:
    output = io.StringIO()
    CsvFormatter(output).render(table)
    return list(csv.reader(io.StringIO(output.getvalue())))


def test_uses_keys_and_csv_key(make_table) -> None:
    table = make_table(
        [
            Column("id", "ID", csv_key="section_id"),
            Column("name", "NOMBRE"),
            Column("internal", "INTERNO", csv=False),
        ],
        [(1, "Tema", "oculto")],
    )

    rows = render(table)

    assert rows[0] == ["section_id", "name"]
    assert rows[1] == ["1", "Tema"]


def test_rich_value_uses_csv_text_and_flattens(make_table) -> None:
    table = make_table(
        [Column("message", "MENSAJE")],
        [
            (
                RichValue(
                    raw="<p>Hola</p><p>Mundo</p>",
                    text="Hola\nMundo",
                    csv_text="Hola, Mundo",
                ),
            )
        ],
    )

    rows = render(table)

    assert rows[1] == ["Hola, Mundo"]


def test_csv_quotes_commas_and_quotes(make_table) -> None:
    table = make_table(
        [Column("subject", "ASUNTO")],
        [('Aviso, con "comillas"',)],
    )

    output = io.StringIO()
    CsvFormatter(output).render(table)
    raw = output.getvalue()

    assert '"Aviso, con ""comillas"""' in raw
    assert list(csv.reader(io.StringIO(raw)))[1] == ['Aviso, con "comillas"']


def test_dates_and_booleans_use_raw_representation(make_table) -> None:
    table = make_table(
        [Column("created", "FECHA"), Column("visible", "VISIBLE")],
        [(datetime(2024, 1, 1, tzinfo=timezone.utc), False)],
    )

    rows = render(table)

    assert rows[1] == ["2024-01-01T00:00:00+00:00", "false"]
