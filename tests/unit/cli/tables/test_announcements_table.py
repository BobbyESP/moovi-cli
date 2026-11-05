from __future__ import annotations

from datetime import datetime, timezone

from moovi.cli.tables import AnnouncementContentTable, AnnouncementsTable
from moovi.cli.tables.base import RichValue
from moovi.domain.models import Announcement, AnnouncementContent


def test_announcements_table_hides_flags_from_human_table() -> None:
    table = AnnouncementsTable(
        [
            Announcement(
                9001,
                "Aviso",
                "Profesor",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                2,
                True,
                False,
            )
        ]
    )

    columns = {column.key: column for column in table.columns}
    assert columns["pinned"].table is False
    assert columns["locked"].table is False
    assert columns["pinned"].csv is True
    assert table.rows[0][0] == 9001
    assert table.rows[0][5] is True


def test_announcement_content_table() -> None:
    content = AnnouncementContent(
        9001,
        8001,
        "Aviso",
        "Profesor",
        datetime(2024, 1, 1, tzinfo=timezone.utc),
        datetime(2024, 1, 2, tzinfo=timezone.utc),
        1,
        "<p>Hola, mundo</p><p>Segundo párrafo</p>",
    )
    table = AnnouncementContentTable(content)

    assert table.single_row is True
    assert table.rows[0][6] == 1
    message = table.rows[0][7]
    assert isinstance(message, RichValue)
    assert message.raw == content.message
    assert message.text == "Hola, mundo\nSegundo párrafo"
    assert message.csv_text == "Hola, mundo Segundo párrafo"
    assert message.json_text is True
