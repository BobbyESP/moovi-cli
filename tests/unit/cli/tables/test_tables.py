from __future__ import annotations

from datetime import datetime, timezone

from moovi.cli.tables import (
    AssignmentsTable,
    ContentsTable,
    CoursesTable,
    SiteInfoTable,
)
from moovi.cli.tables.base import RichValue
from moovi.domain.models import (
    Assignment,
    Course,
    Module,
    Section,
    SiteInfo,
)


def test_site_info_table() -> None:
    table = SiteInfoTable(
        SiteInfo(42, "profesor", "Profesor", "Moovi", "4.5", ("f1", "f2"))
    )

    assert table.single_row is True
    assert [column.key for column in table.columns] == [
        "user_id",
        "username",
        "full_name",
        "site_name",
        "release",
        "functions",
    ]
    functions = table.rows[0][5]
    assert isinstance(functions, RichValue)
    assert functions.raw == ("f1", "f2")
    assert functions.text == "2"


def test_courses_table_hides_start_date_in_table() -> None:
    date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    table = CoursesTable([Course(101, "M1", "Matemáticas", True, date)])

    assert table.single_row is False
    start_date = table.columns[4]
    assert start_date.key == "start_date"
    assert start_date.table is False
    assert table.rows == [(101, "M1", "Matemáticas", True, date)]


def test_contents_table_keeps_summary_and_modules() -> None:
    section = Section(
        1,
        "Tema 1",
        "<p>Introducción</p>",
        (
            Module(11, "Foro", "forum", True),
            Module(12, "Apuntes", "resource", False),
        ),
    )
    table = ContentsTable([section])

    summary, modules = table.rows[0][2], table.rows[0][3]
    assert isinstance(summary, RichValue)
    assert summary.raw == "<p>Introducción</p>"
    assert summary.text == "Introducción"
    assert summary.json_text is True

    assert isinstance(modules, RichValue)
    assert modules.raw == section.modules
    assert "[forum] Foro" in modules.text
    assert "[resource] Apuntes (oculta)" in modules.text
    assert "forum:Foro:1" in (modules.csv_text or "")
    assert "resource:Apuntes:0" in (modules.csv_text or "")


def test_assignments_table_hides_course_id_in_table() -> None:
    date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    table = AssignmentsTable([Assignment(501, 101, "Práctica", date, None, 100)])

    course_id = table.columns[1]
    assert course_id.key == "course_id"
    assert course_id.table is False
    assert table.rows == [(501, 101, "Práctica", date, None, 100)]
