"""Puertos que la lógica necesita y que implementan los adaptadores."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from moovi.domain.models import (
    Announcement,
    Assignment,
    Course,
    Forum,
    Participant,
    Section,
    SiteInfo,
)
from moovi.domain.values import Token


class MoodleGateway(Protocol):
    """Acceso tipado a las funciones de Moodle que usa la aplicación."""

    def login(self, username: str, password: str) -> Token: ...

    def site_info(self, token: Token) -> SiteInfo: ...

    def users_courses(self, token: Token, user_id: int) -> list[Course]: ...

    def course_contents(self, token: Token, course_id: int) -> list[Section]: ...

    def enrolled_users(self, token: Token, course_id: int) -> list[Participant]: ...

    def assignments(
        self, token: Token, course_ids: Sequence[int]
    ) -> list[Assignment]: ...

    def course_forums(self, token: Token, course_id: int) -> list[Forum]: ...

    def forum_discussions(
        self, token: Token, forum_id: int, limit: int
    ) -> list[Announcement]: ...


class TokenStore(Protocol):
    """Persistencia del token entre ejecuciones."""

    def load(self, site: str, username: str | None = None) -> Token | None: ...

    def load_username(self, site: str) -> str | None: ...

    def save(self, site: str, username: str, token: Token) -> None: ...

    def clear(self, site: str, username: str | None = None) -> None: ...
