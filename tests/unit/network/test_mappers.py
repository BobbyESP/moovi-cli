from datetime import timezone

from moovi.network.mappers import (
    map_announcements,
    map_assignments,
    map_courses,
    map_forums,
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
                "firstname": "Ana",
                "lastname": "Alumna",
                "fullname": "Ana Alumna",
                "groups": [
                    {"id": 146, "name": "met_part"},
                    {"id": 147, "name": "apr2_part"},
                ],
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
    assert participant.first_name == "Ana"
    assert participant.last_name == "Alumna"
    assert participant.full_name == "Ana Alumna"
    assert [(group.id, group.name) for group in participant.groups] == [
        (146, "met_part"),
        (147, "apr2_part"),
    ]
    assert participant.last_access is not None
    assert participant.email == "ana@uvigo.gal"


def test_maps_participants_with_role_name() -> None:
    [participant] = map_participants(
        [
            {
                "id": 8,
                "firstname": "Docente",
                "lastname": "Invitado",
                "fullname": "Docente Invitado",
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
    assert participant.full_name == "Docente Invitado"


def test_falls_back_to_fullname_when_parts_are_missing() -> None:
    [participant] = map_participants(
        [{"id": 9, "fullname": "Nombre Completo"}]
    )

    assert participant.first_name == "Nombre Completo"
    assert participant.last_name == ""
    assert participant.full_name == "Nombre Completo"
    assert participant.groups == ()


def test_maps_participant_without_groups() -> None:
    [participant] = map_participants(
        [{"id": 9, "firstname": "Sin", "lastname": "Grupos"}]
    )

    assert participant.groups == ()


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


def test_maps_forums() -> None:
    forums = map_forums(
        [
            {
                "id": "2217",
                "course": "101",
                "name": "Foro de novas",
                "type": "news",
                "forcesubscribe": 1,
            },
            {
                "id": 2218,
                "course": 101,
                "name": "Foro xeral",
                "type": "general",
                "forcesubscribe": "0",
            },
        ]
    )

    assert forums[0].id == 2217
    assert forums[0].course_id == 101
    assert forums[0].force_subscribe is True
    assert forums[1].force_subscribe is False


def test_maps_announcements() -> None:
    [announcement] = map_announcements(
        {
            "discussions": [
                {
                    "id": 9001,
                    "name": "Aviso importante",
                    "userfullname": "Profesor Uno",
                    "created": 1704067200,
                    "numreplies": 2,
                    "pinned": True,
                    "locked": False,
                }
            ]
        }
    )

    assert announcement.id == 9001
    assert announcement.subject == "Aviso importante"
    assert announcement.author == "Profesor Uno"
    assert announcement.created is not None
    assert announcement.num_replies == 2
    assert announcement.pinned is True
    assert announcement.locked is False


def test_mappers_tolerate_bad_shapes() -> None:
    assert map_courses(None) == []
    assert map_sections({}) == []
    assert map_participants("nope") == []
    assert map_assignments([]) == []
    assert map_forums({}) == []
    assert map_announcements([]) == []
