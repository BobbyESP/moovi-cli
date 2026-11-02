"""Contrato de presentación: cada formato implementa estos métodos."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from moovi.domain.models import (
    Announcement,
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)


class Formatter(Protocol):
    def site_info(self, info: SiteInfo) -> None: ...

    def courses(self, courses: Sequence[Course]) -> None: ...

    def sections(self, sections: Sequence[Section]) -> None: ...

    def participants(
        self,
        participants: Sequence[Participant],
        *,
        include_email: bool,
    ) -> None: ...

    def assignments(self, assignments: Sequence[Assignment]) -> None: ...

    def announcements(self, announcements: Sequence[Announcement]) -> None: ...
