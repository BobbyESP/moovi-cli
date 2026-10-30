"""Modelos de dominio que devuelven los casos de uso."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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
class Module:
    id: int
    name: str
    mod_name: str
    visible: bool
    url: str | None = None


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
class Participant:
    id: int
    full_name: str
    roles: tuple[Role, ...] = ()
    last_access: datetime | None = None
    email: str | None = None


@dataclass(frozen=True, slots=True)
class Assignment:
    id: int
    course_id: int
    name: str
    due_date: datetime | None = None
    cutoff_date: datetime | None = None
    max_grade: float | None = None
