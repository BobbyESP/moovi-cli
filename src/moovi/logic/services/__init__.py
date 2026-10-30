"""Casos de uso de la aplicación."""

from moovi.logic.services.assignments import AssignmentService
from moovi.logic.services.auth import AuthService
from moovi.logic.services.catalog import CatalogService
from moovi.logic.services.people import PeopleService

__all__ = [
    "AssignmentService",
    "AuthService",
    "CatalogService",
    "PeopleService",
]
