from __future__ import annotations

import io
import json
from datetime import datetime, timezone

from moovi.cli.formats.json import JsonFormatter
from moovi.domain.models import (
    Course,
    Group,
    Participant,
    Role,
    Section,
    SiteInfo,
)


def render_json(method: str, *args, **kwargs):
    output = io.StringIO()
    formatter = JsonFormatter(output)
    getattr(formatter, method)(*args, **kwargs)
    return json.loads(output.getvalue())


def test_participants_keep_raw_roles_groups_and_derive_full_name() -> None:
    data = render_json(
        "participants",
        [
            Participant(
                7,
                "Ana",
                "Alumna",
                groups=(Group(146, "met_part"),),
                roles=(Role(5, "student", ""),),
            )
        ],
        include_email=False,
    )

    assert data[0]["first_name"] == "Ana"
    assert data[0]["last_name"] == "Alumna"
    assert data[0]["full_name"] == "Ana Alumna"
    assert data[0]["groups"] == [{"id": 146, "name": "met_part"}]
    assert data[0]["roles"] == [{"id": 5, "short_name": "student", "name": ""}]


def test_courses_serialize_dates_as_iso() -> None:
    data = render_json(
        "courses",
        [Course(101, "M1", "Matemáticas I", True, datetime(2024, 1, 1, tzinfo=timezone.utc))],
    )

    assert data[0]["start_date"] == "2024-01-01T00:00:00+00:00"


def test_sections_and_site_info() -> None:
    sections = render_json("sections", [Section(1, "Tema 1", "", ())])
    info = render_json(
        "site_info", SiteInfo(42, "profesor", "Profesor", "Moovi", "4.5", ("f1",))
    )

    assert sections[0]["name"] == "Tema 1"
    assert info["user_id"] == 42
    assert info["functions"] == ["f1"]
