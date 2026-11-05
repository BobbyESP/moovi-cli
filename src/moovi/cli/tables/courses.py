"""Tabla de datos de cursos."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, Table
from moovi.domain.models import Course


class CoursesTable(Table):
    def __init__(self, courses: Sequence[Course]) -> None:
        self._courses = courses

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("id", "ID"),
            Column("short_name", "SHORTNAME"),
            Column("full_name", "NOMBRE"),
            Column("visible", "VISIBLE"),
            Column("start_date", "INICIO", table=False),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return [
            (
                course.id,
                course.short_name,
                course.full_name,
                course.visible,
                course.start_date,
            )
            for course in self._courses
        ]

    @property
    def single_row(self) -> bool:
        return False
