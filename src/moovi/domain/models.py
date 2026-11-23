"""Modelos de dominio que devuelven los casos de uso."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

DownloadStatus = Literal["downloaded", "skipped", "conflict", "failed"]


@dataclass(frozen=True, slots=True)
class SiteInfo:
    user_id: int
    username: str
    full_name: str
    site_name: str
    release: str
    functions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Course:
    id: int
    short_name: str
    full_name: str
    visible: bool
    start_date: datetime | None = None


@dataclass(frozen=True, slots=True)
class RemoteFile:
    """Fichero alojado en Moodle, tal como lo describe su módulo."""

    name: str
    url: str
    folder: str = ""
    size: int = 0
    modified: datetime | None = None
    mime_type: str | None = None


@dataclass(frozen=True, slots=True)
class Module:
    id: int
    name: str
    mod_name: str
    visible: bool
    url: str | None = None
    files: tuple[RemoteFile, ...] = ()


@dataclass(frozen=True, slots=True)
class Section:
    id: int
    name: str
    summary: str
    modules: tuple[Module, ...] = ()


@dataclass(frozen=True, slots=True)
class Role:
    id: int
    short_name: str
    name: str = ""


@dataclass(frozen=True, slots=True)
class Group:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class Participant:
    id: int
    first_name: str
    last_name: str
    groups: tuple[Group, ...] = ()
    roles: tuple[Role, ...] = ()
    last_access: datetime | None = None
    email: str | None = None
    id_number: str | None = None

    @property
    def full_name(self) -> str:
        return " ".join(
            part for part in (self.first_name, self.last_name) if part
        ).strip()


@dataclass(frozen=True, slots=True)
class Assignment:
    id: int
    course_id: int
    name: str
    due_date: datetime | None = None
    cutoff_date: datetime | None = None
    max_grade: float | None = None


@dataclass(frozen=True, slots=True)
class Forum:
    id: int
    course_id: int
    name: str
    type: str
    force_subscribe: bool


@dataclass(frozen=True, slots=True)
class Announcement:
    id: int
    subject: str
    author: str
    created: datetime | None = None
    num_replies: int = 0
    pinned: bool = False
    locked: bool = False


@dataclass(frozen=True, slots=True)
class AnnouncementContent:
    id: int
    discussion_id: int
    subject: str
    author: str
    created: datetime | None = None
    modified: datetime | None = None
    message_format: int = 1
    message: str = ""


@dataclass(frozen=True, slots=True)
class CourseFile:
    """Fichero descargable de un curso y su ruta local relativa y segura."""

    module_id: int
    module_name: str
    section_name: str
    file: RemoteFile
    path: str


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Metadatos de un fichero ya guardado en el destino."""

    size: int
    modified: datetime


@dataclass(frozen=True, slots=True)
class DownloadResult:
    file: CourseFile
    status: DownloadStatus
    error: str | None = None
