"""Tablas del foro de noticias de Moovi."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, RichValue, Table
from moovi.cli.text import flatten_text, html_to_text
from moovi.domain.models import Announcement, AnnouncementContent


class AnnouncementsTable(Table):
    def __init__(self, announcements: Sequence[Announcement]) -> None:
        self._announcements = announcements

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("id", "ID"),
            Column("created", "FECHA"),
            Column("author", "AUTOR"),
            Column("subject", "ASUNTO"),
            Column("num_replies", "RESPUESTAS"),
            Column("pinned", "FIJADO", table=False),
            Column("locked", "BLOQUEADO", table=False),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return [
            (
                announcement.id,
                announcement.created,
                announcement.author,
                announcement.subject,
                announcement.num_replies,
                announcement.pinned,
                announcement.locked,
            )
            for announcement in self._announcements
        ]

    @property
    def single_row(self) -> bool:
        return False


class AnnouncementContentTable(Table):
    def __init__(self, content: AnnouncementContent) -> None:
        self._content = content

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("id", "ID"),
            Column("discussion_id", "DISCUSIÓN"),
            Column("subject", "ASUNTO"),
            Column("author", "AUTOR"),
            Column("created", "FECHA"),
            Column("modified", "MODIFICADO"),
            Column("message_format", "FORMATO", table=False, csv=False),
            Column("message", "MENSAJE", csv_key="message_text"),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        content = self._content
        text = (
            html_to_text(content.message)
            if content.message_format == 1
            else content.message
        )
        return [
            (
                content.id,
                content.discussion_id,
                content.subject,
                content.author,
                content.created,
                content.modified,
                content.message_format,
                RichValue(
                    raw=content.message,
                    text=text,
                    csv_text=flatten_text(text),
                    json_text=True,
                ),
            )
        ]

    @property
    def single_row(self) -> bool:
        return True
