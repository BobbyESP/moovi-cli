"""Tablas de datos por entidad."""

from moovi.cli.tables.announcements import (
    AnnouncementContentTable,
    AnnouncementsTable,
)
from moovi.cli.tables.assignments import AssignmentsTable
from moovi.cli.tables.contents import ContentsTable
from moovi.cli.tables.courses import CoursesTable
from moovi.cli.tables.participants import ParticipantsTable
from moovi.cli.tables.site import SiteInfoTable

__all__ = [
    "AnnouncementContentTable",
    "AnnouncementsTable",
    "AssignmentsTable",
    "ContentsTable",
    "CoursesTable",
    "ParticipantsTable",
    "SiteInfoTable",
]
