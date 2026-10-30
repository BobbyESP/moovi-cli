from __future__ import annotations

import io
from datetime import datetime, timezone

from moovi.cli.formats.table import TableFormatter
from moovi.domain.models import (
    Assignment,
    Course,
    Module,
    Participant,
    Role,
    Section,
    SiteInfo,
)

STUDENT = Role(5, "student", "")
TEACHER = Role(3, "editingteacher", "")


def render(method: str, *args, **kwargs) -> str:
    output = io.StringIO()
    formatter = TableFormatter(output)
    getattr(formatter, method)(*args, **kwargs)
    return output.getvalue()


def test_role_labels() -> None:
    text = render(
        "participants",
        [Participant(7, "Ana", "Alumna", (STUDENT,))],
        include_email=False,
    )

    assert "Alumno/a" in text
    assert "NOMBRE" in text
    assert "APELLIDOS" in text
    assert "Ana" in text
    assert "Alumna" in text

    assert "Profesor/a" in render(
        "participants",
        [Participant(8, "Docente", "Uno", (TEACHER,))],
        include_email=False,
    )


def test_prefers_role_name() -> None:
    role = Role(10, "guestteacher", "Profesor Invitado")
    text = render(
        "participants",
        [Participant(9, "Invitado", "Docente", (role,))],
        include_email=False,
    )
    assert "Profesor Invitado" in text


def test_participants_email_column_only_when_requested() -> None:
    participant = Participant(
        7, "Ana", "Alumna", (STUDENT,), None, "ana@uvigo.gal"
    )

    without_email = render("participants", [participant], include_email=False)
    with_email = render("participants", [participant], include_email=True)

    assert "EMAIL" not in without_email
    assert "EMAIL" in with_email
    assert "ana@uvigo.gal" in with_email


def test_courses_table_and_empty_state() -> None:
    courses = [
        Course(101, "M1", "Matemáticas I", True),
        Course(102, "M2", "Matemáticas II", False),
    ]
    text = render("courses", courses)

    assert "SHORTNAME" in text
    assert "M1" in text
    assert "no" in text
    assert render("courses", []) == "(sin resultados)\n"


def test_sections_strip_html_and_mark_hidden_modules() -> None:
    sections = [
        Section(
            1,
            "Tema 1",
            "<p>Introducción</p>",
            (Module(11, "Foro de avisos", "forum", True), Module(12, "Apuntes", "resource", False)),
        )
    ]
    text = render("sections", sections)

    assert "Tema 1" in text
    assert "Introducción" in text
    assert "<p>" not in text
    assert "(oculta)" in text


def test_assignments_table() -> None:
    date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    text = render(
        "assignments", [Assignment(501, 101, "Práctica 1", date, None, 100.0)]
    )

    assert "Práctica 1" in text
    assert "2024-01-01 00:00 UTC" in text
    assert "100" in text


def test_site_info() -> None:
    text = render(
        "site_info",
        SiteInfo(42, "profesor", "Profesor", "Moovi", "4.5", ("f1", "f2")),
    )

    assert "Profesor" in text
    assert "Moovi" in text
    assert "Funciones disponibles: 2" in text
