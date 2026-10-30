from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from moovi.cli.formats.csv import CsvFormatter
from moovi.domain.models import (
    Assignment,
    Course,
    Group,
    Module,
    Participant,
    Role,
    Section,
    SiteInfo,
)


def render_csv(method: str, *args, **kwargs) -> list[list[str]]:
    output = io.StringIO()
    formatter = CsvFormatter(output)
    getattr(formatter, method)(*args, **kwargs)
    return list(csv.reader(io.StringIO(output.getvalue())))


def test_courses_csv_quotes_commas_and_uses_iso_dates() -> None:
    rows = render_csv(
        "courses",
        [
            Course(101, "M1", "Matemáticas, I", False, datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ],
    )

    assert rows[0] == ["id", "short_name", "full_name", "visible", "start_date"]
    assert rows[1] == [
        "101",
        "M1",
        "Matemáticas, I",
        "false",
        "2024-01-01T00:00:00+00:00",
    ]


def test_participants_csv_separates_names_and_joins_groups_and_roles() -> None:
    rows = render_csv(
        "participants",
        [
            Participant(
                7,
                "Ana",
                "Alumna, Jr.",
                groups=(
                    Group(146, "met_part"),
                    Group(147, "Grupo;Raro"),
                    Group(148, "Grupo, Coma"),
                ),
                roles=(Role(5, "student", ""), Role(3, "editingteacher", "")),
            )
        ],
        include_email=False,
    )

    assert rows[0] == [
        "id",
        "first_name",
        "last_name",
        "groups",
        "roles",
        "last_access",
        "email",
    ]
    assert rows[1] == [
        "7",
        "Ana",
        "Alumna, Jr.",
        "met_part;Grupo#Raro;Grupo, Coma",
        "student;editingteacher",
        "",
        "",
    ]


def test_sections_csv_flattens_modules_and_keeps_empty_sections() -> None:
    rows = render_csv(
        "sections",
        [
            Section(1, "Tema 1", "", (Module(11, "Foro", "forum", True, "https://x"),)),
            Section(2, "Tema 2", "", ()),
        ],
    )

    assert rows[0] == [
        "section_id",
        "section_name",
        "module_id",
        "module_name",
        "mod_name",
        "visible",
        "url",
    ]
    assert rows[1] == ["1", "Tema 1", "11", "Foro", "forum", "true", "https://x"]
    assert rows[2] == ["2", "Tema 2", "", "", "", "", ""]


def test_assignments_csv() -> None:
    rows = render_csv(
        "assignments",
        [
            Assignment(
                501,
                101,
                "Práctica 1",
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                None,
                100.0,
            )
        ],
    )

    assert rows[0] == [
        "id",
        "course_id",
        "name",
        "due_date",
        "cutoff_date",
        "max_grade",
    ]
    assert rows[1] == [
        "501",
        "101",
        "Práctica 1",
        "2024-01-01T00:00:00+00:00",
        "",
        "100",
    ]


def test_site_info_csv() -> None:
    rows = render_csv(
        "site_info", SiteInfo(42, "profesor", "Profesor", "Moovi", "4.5", ("a", "b"))
    )

    assert rows == [
        ["user_id", "username", "full_name", "site_name", "release", "functions_count"],
        ["42", "profesor", "Profesor", "Moovi", "4.5", "2"],
    ]
