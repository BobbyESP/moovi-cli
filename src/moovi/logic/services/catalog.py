"""Casos de uso de catálogo: cursos y contenido."""

from __future__ import annotations

from moovi.domain.models import Course, Section
from moovi.logic.session import MoodleSession


class CatalogService:
    def __init__(self, session: MoodleSession) -> None:
        self._session = session

    def list_courses(self) -> list[Course]:
        return self._session.courses()

    def get_contents(self, course_id: int) -> list[Section]:
        return self._session.contents(course_id)
