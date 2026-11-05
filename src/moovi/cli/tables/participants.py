"""Tabla de datos de personas matriculadas."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, RichValue, Table
from moovi.cli.tables.roles import role_key, role_label
from moovi.domain.models import Group, Participant, Role


class ParticipantsTable(Table):
    def __init__(
        self, participants: Sequence[Participant], *, include_email: bool
    ) -> None:
        self._participants = participants
        self._include_email = include_email

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("id", "ID"),
            Column("first_name", "NOMBRE"),
            Column("last_name", "APELLIDOS"),
            Column("full_name", "NOMBRE COMPLETO", table=False, csv=False),
            Column("groups", "GRUPOS"),
            Column("roles", "ROLES"),
            Column("last_access", "ÚLTIMO ACCESO"),
            Column("email", "EMAIL", table=self._include_email),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return [
            (
                participant.id,
                participant.first_name,
                participant.last_name,
                participant.full_name,
                _groups_value(participant.groups),
                _roles_value(participant.roles),
                participant.last_access,
                participant.email,
            )
            for participant in self._participants
        ]

    @property
    def single_row(self) -> bool:
        return False


def _groups_value(groups: Sequence[Group]) -> RichValue:
    return RichValue(
        raw=groups,
        text="; ".join(group.name for group in groups if group.name),
        csv_text=";".join(
            group.name.replace(";", "#") for group in groups if group.name
        ),
    )


def _roles_value(roles: Sequence[Role]) -> RichValue:
    return RichValue(
        raw=roles,
        text=", ".join(role_label(role) for role in roles),
        csv_text=";".join(role_key(role) for role in roles),
    )
