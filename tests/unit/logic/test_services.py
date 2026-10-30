from __future__ import annotations

from moovi.domain.models import (
    Assignment,
    Course,
    Participant,
    Role,
    Section,
    SiteInfo,
)
from moovi.logic.services.assignments import AssignmentService
from moovi.logic.services.auth import AuthService
from moovi.logic.services.catalog import CatalogService
from moovi.logic.services.people import PeopleService

SITE = SiteInfo(42, "profesor", "Profesor", "Moovi", "4.5")


class FakeSession:
    def __init__(self) -> None:
        self.relogins = 0

    def relogin(self) -> None:
        self.relogins += 1

    def site_info(self) -> SiteInfo:
        return SITE

    def courses(self) -> list[Course]:
        return [Course(101, "M1", "Matemáticas I", True)]

    def contents(self, course_id: int) -> list[Section]:
        assert course_id == 101
        return [Section(1, "Tema 1", "", ())]

    def participants(self, course_id: int) -> list[Participant]:
        assert course_id == 101
        return [
            Participant(
                7,
                "Ana",
                "Alumna",
                roles=(Role(5, "student", ""),),
                email="ana@uvigo.gal",
            )
        ]

    def assignments(self, course_ids: list[int]) -> list[Assignment]:
        assert course_ids == [101]
        return [Assignment(501, 101, "Práctica 1")]


def test_auth_login_force_relogins() -> None:
    session = FakeSession()
    service = AuthService(session)

    service.login(force=True)

    assert session.relogins == 1


def test_catalog_delegates() -> None:
    service = CatalogService(FakeSession())

    assert service.list_courses()[0].short_name == "M1"
    assert service.get_contents(101)[0].name == "Tema 1"


def test_people_hides_email_by_default() -> None:
    service = PeopleService(FakeSession())

    [participant] = service.list_participants(101)

    assert participant.email is None
    assert participant.full_name == "Ana Alumna"


def test_people_can_include_email() -> None:
    service = PeopleService(FakeSession())

    [participant] = service.list_participants(101, include_email=True)

    assert participant.email == "ana@uvigo.gal"


def test_assignments_delegates() -> None:
    service = AssignmentService(FakeSession())

    assert service.list_assignments(101)[0].name == "Práctica 1"
