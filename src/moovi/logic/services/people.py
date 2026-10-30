"""Casos de uso de personas matriculadas."""

from __future__ import annotations

from dataclasses import replace

from moovi.domain.models import Participant
from moovi.logic.session import MoodleSession


class PeopleService:
    def __init__(self, session: MoodleSession) -> None:
        self._session = session

    def list_participants(
        self, course_id: int, *, include_email: bool = False
    ) -> list[Participant]:
        participants = self._session.participants(course_id)
        if include_email:
            return participants
        return [replace(participant, email=None) for participant in participants]
