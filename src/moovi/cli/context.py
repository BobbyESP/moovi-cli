"""Composition root: el único lugar que conoce implementaciones concretas."""

from __future__ import annotations

from dataclasses import dataclass

from moovi.infra.settings import Settings
from moovi.infra.token_store import FileTokenStore
from moovi.logic.services import (
    AssignmentService,
    AuthService,
    CatalogService,
    PeopleService,
)
from moovi.logic.session import MoodleSession
from moovi.network.rest import MoodleRestClient


@dataclass(frozen=True, slots=True)
class Services:
    auth: AuthService
    catalog: CatalogService
    people: PeopleService
    assignments: AssignmentService


def build_services(settings: Settings) -> Services:
    gateway = MoodleRestClient(settings.site)
    store = FileTokenStore(settings.cache_path)
    session = MoodleSession(
        gateway,
        store,
        site=settings.site,
        username=settings.username,
        password=settings.password,
        explicit_token=settings.token,
    )
    return Services(
        auth=AuthService(session),
        catalog=CatalogService(session),
        people=PeopleService(session),
        assignments=AssignmentService(session),
    )
