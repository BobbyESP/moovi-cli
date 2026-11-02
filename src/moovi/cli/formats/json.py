"""Formato JSON."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from moovi.cli.formats.common import write_json
from moovi.domain.models import (
    Announcement,
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)


class JsonFormatter:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout

    def site_info(self, info: SiteInfo) -> None:
        write_json(info, self._stream)

    def courses(self, courses: Sequence[Course]) -> None:
        write_json(list(courses), self._stream)

    def sections(self, sections: Sequence[Section]) -> None:
        write_json(list(sections), self._stream)

    def participants(
        self,
        participants: Sequence[Participant],
        *,
        include_email: bool,
    ) -> None:
        del include_email  # el servicio ya decide si incluye el email
        write_json(
            [
                {
                    "id": participant.id,
                    "first_name": participant.first_name,
                    "last_name": participant.last_name,
                    "full_name": participant.full_name,
                    "groups": participant.groups,
                    "roles": participant.roles,
                    "last_access": participant.last_access,
                    "email": participant.email,
                }
                for participant in participants
            ],
            self._stream,
        )

    def assignments(self, assignments: Sequence[Assignment]) -> None:
        write_json(list(assignments), self._stream)

    def announcements(self, announcements: Sequence[Announcement]) -> None:
        write_json(list(announcements), self._stream)
