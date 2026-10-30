"""Formato raw: CSV plano para componer con grep, sort, cut o awk."""

from __future__ import annotations

import csv
import sys
from collections.abc import Sequence
from typing import TextIO

from moovi.cli.formats.common import (
    format_bool,
    format_grade,
    iso_datetime,
    role_key,
)
from moovi.domain.models import (
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)


class CsvFormatter:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout
        self._writer = csv.writer(self._stream, lineterminator="\n")

    def site_info(self, info: SiteInfo) -> None:
        self._write(
            [
                "user_id",
                "username",
                "full_name",
                "site_name",
                "release",
                "functions_count",
            ],
            [
                [
                    str(info.user_id),
                    info.username,
                    info.full_name,
                    info.site_name,
                    info.release,
                    str(len(info.functions)),
                ]
            ],
        )

    def courses(self, courses: Sequence[Course]) -> None:
        self._write(
            ["id", "short_name", "full_name", "visible", "start_date"],
            [
                [
                    str(course.id),
                    course.short_name,
                    course.full_name,
                    format_bool(course.visible),
                    iso_datetime(course.start_date),
                ]
                for course in courses
            ],
        )

    def sections(self, sections: Sequence[Section]) -> None:
        rows: list[list[str]] = []
        for section in sections:
            if not section.modules:
                rows.append(
                    [
                        str(section.id),
                        section.name,
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                continue
            for module in section.modules:
                rows.append(
                    [
                        str(section.id),
                        section.name,
                        str(module.id),
                        module.name,
                        module.mod_name,
                        format_bool(module.visible),
                        module.url or "",
                    ]
                )
        self._write(
            [
                "section_id",
                "section_name",
                "module_id",
                "module_name",
                "mod_name",
                "visible",
                "url",
            ],
            rows,
        )

    def participants(
        self,
        participants: Sequence[Participant],
        *,
        include_email: bool,
    ) -> None:
        del include_email  # la columna existe siempre; queda vacía sin --emails
        self._write(
            ["id", "full_name", "roles", "last_access", "email"],
            [
                [
                    str(participant.id),
                    participant.full_name,
                    ";".join(role_key(role) for role in participant.roles),
                    iso_datetime(participant.last_access),
                    participant.email or "",
                ]
                for participant in participants
            ],
        )

    def assignments(self, assignments: Sequence[Assignment]) -> None:
        self._write(
            [
                "id",
                "course_id",
                "name",
                "due_date",
                "cutoff_date",
                "max_grade",
            ],
            [
                [
                    str(assignment.id),
                    str(assignment.course_id),
                    assignment.name,
                    iso_datetime(assignment.due_date),
                    iso_datetime(assignment.cutoff_date),
                    format_grade(assignment.max_grade, missing=""),
                ]
                for assignment in assignments
            ],
        )

    def _write(
        self, headers: Sequence[str], rows: Sequence[Sequence[str]]
    ) -> None:
        self._writer.writerow(headers)
        self._writer.writerows(rows)
