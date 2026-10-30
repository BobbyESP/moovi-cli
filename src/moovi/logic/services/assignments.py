"""Casos de uso de tareas."""

from __future__ import annotations

from moovi.domain.models import Assignment
from moovi.logic.session import MoodleSession


class AssignmentService:
    def __init__(self, session: MoodleSession) -> None:
        self._session = session

    def list_assignments(self, course_id: int) -> list[Assignment]:
        return self._session.assignments([course_id])
