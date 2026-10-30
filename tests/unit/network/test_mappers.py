from datetime import timezone

from moovi.network.mappers import (
    map_assignments,
    map_courses,
    map_participants,
    map_sections,
    map_site_info,
    timestamp,
)


def test_timestamp_zero_and_invalid_are_none() -> None:
    assert timestamp(0) is None
    assert timestamp(-1) is None
    assert timestamp(None) is None
    assert timestamp("not-a-number") is None


def test_timestamp_is_utc() -> None:
    value = timestamp(1704067200)
    assert value is not None
    assert value.tzinfo == timezone.utc
    assert value.year == 2024


def test_maps_site_info_with_function_objects() -> None:
    info = map_site_info(
        {
            "userid": "42",
            "username": "profesor",
            "fullname": "Profesor",
            "sitename": "Moovi",
            "release": "4.5",
            "functions": [{"name": "core_webservice_get_site_info"}],
        }
    )

    assert info.user_id == 42
    assert info.functions == ("core_webservice_get_site_info",)


def test_maps_courses() -> None:
    [course] = map_courses(
        [
            {
                "id": "101",
                "shortname": "M1",
                "fullname": "Matemáticas I",
                "visible": 0,
                "startdate": 1704067200,
            }
        ]
    )

    assert course.id == 101
    assert course.visible is False
    assert course.start_date is not None


def test_maps_sections_and_modules() -> None:
    [section] = map_sections(
        [
            {
                "id": 1,
                "name": "Tema 1",
                "summary": "<p>Hola</p>",
                "modules": [
                    {
                        "id": 11,
                        "name": "Foro",
                        "modname": "forum",
                        "visible": 1,
                        "url": "https://example.test/forum",
                    }
                ],
            }
        ]
    )

    assert section.name == "Tema 1"
    assert section.modules[0].mod_name == "forum"
    assert section.modules[0].url == "https://example.test/forum"


def test_maps_participants_with_empty_role_name() -> None:
    [participant] = map_participants(
        [
            {
                "id": "7",
                "fullname": "Ana",
                "roles": [
                    {
                        "roleid": 5,
                        "name": "",
                        "shortname": "student",
                        "sortorder": 0,
                    }
                ],
                "lastcourseaccess": 1700000000,
                "email": "ana@uvigo.gal",
            }
        ]
    )

    [role] = participant.roles
    assert role.id == 5
    assert role.short_name == "student"
    assert role.name == ""
    assert participant.last_access is not None
    assert participant.email == "ana@uvigo.gal"


def test_maps_participants_with_role_name() -> None:
    [participant] = map_participants(
        [
            {
                "id": 8,
                "fullname": "Docente",
                "roles": [
                    {
                        "roleid": 10,
                        "name": "Profesor Invitado",
                        "shortname": "guestteacher",
                    }
                ],
            }
        ]
    )

    [role] = participant.roles
    assert role.id == 10
    assert role.short_name == "guestteacher"
    assert role.name == "Profesor Invitado"


def test_maps_assignments() -> None:
    [assignment] = map_assignments(
        {
            "courses": [
                {
                    "id": 101,
                    "assignments": [
                        {
                            "id": 501,
                            "name": "Práctica 1",
                            "duedate": 1704067200,
                            "cutoffdate": 0,
                            "grade": 100,
                        }
                    ],
                }
            ]
        }
    )

    assert assignment.course_id == 101
    assert assignment.due_date is not None
    assert assignment.cutoff_date is None
    assert assignment.max_grade == 100.0


def test_mappers_tolerate_bad_shapes() -> None:
    assert map_courses(None) == []
    assert map_sections({}) == []
    assert map_participants("nope") == []
    assert map_assignments([]) == []
