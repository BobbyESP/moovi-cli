"""Tabla de datos de tareas."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, Table
from moovi.domain.models import Assignment


class AssignmentsTable(Table):
    def __init__(self, assignments: Sequence[Assignment]) -> None:
        self._assignments = assignments

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("id", "ID"),
            Column("course_id", "CURSO", table=False),
            Column("name", "NOMBRE"),
            Column("due_date", "ENTREGA"),
            Column("cutoff_date", "CIERRE"),
            Column("max_grade", "NOTA MÁX."),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return [
            (
                assignment.id,
                assignment.course_id,
                assignment.name,
                assignment.due_date,
                assignment.cutoff_date,
                assignment.max_grade,
            )
            for assignment in self._assignments
        ]

    @property
    def single_row(self) -> bool:
        return False
