"""Formato JSON."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TextIO

from moovi.cli.formats.common import write_json
from moovi.domain.models import (
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
        write_json(list(participants), self._stream)

    def assignments(self, assignments: Sequence[Assignment]) -> None:
        write_json(list(assignments), self._stream)
