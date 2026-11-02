"""Conversión de las respuestas de Moodle a modelos de dominio."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from moovi.domain.models import (
    Announcement,
    Assignment,
    Course,
    Forum,
    Group,
    Module,
    Participant,
    Role,
    Section,
    SiteInfo,
)


def timestamp(value: object) -> datetime | None:
    try:
        seconds = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if seconds <= 0:
        return None
    return datetime.fromtimestamp(seconds, tz=timezone.utc)


def map_site_info(data: Mapping[str, Any]) -> SiteInfo:
    functions: list[str] = []
    for function in data.get("functions") or ():
        if isinstance(function, Mapping):
            name = function.get("name")
            if name:
                functions.append(str(name))
        else:
            functions.append(str(function))
    return SiteInfo(
        user_id=int(data.get("userid", 0)),
        username=str(data.get("username", "")),
        full_name=str(data.get("fullname", "")),
        site_name=str(data.get("sitename", "")),
        release=str(data.get("release", "")),
        functions=tuple(functions),
    )


def map_courses(data: object) -> list[Course]:
    return [_map_course(item) for item in _items(data)]


def _map_course(item: Mapping[str, Any]) -> Course:
    return Course(
        id=int(item.get("id", 0)),
        short_name=str(item.get("shortname", "")),
        full_name=str(item.get("fullname", "")),
        visible=bool(item.get("visible", 1)),
        start_date=timestamp(item.get("startdate")),
    )


def map_sections(data: object) -> list[Section]:
    return [_map_section(item) for item in _items(data)]


def _map_section(item: Mapping[str, Any]) -> Section:
    modules = tuple(
        _map_module(module)
        for module in item.get("modules") or ()
        if isinstance(module, Mapping)
    )
    return Section(
        id=int(item.get("id", 0)),
        name=str(item.get("name", "")),
        summary=str(item.get("summary", "")),
        modules=modules,
    )


def _map_module(item: Mapping[str, Any]) -> Module:
    url = item.get("url")
    return Module(
        id=int(item.get("id", 0)),
        name=str(item.get("name", "")),
        mod_name=str(item.get("modname", "")),
        visible=bool(item.get("visible", 1)),
        url=str(url) if url else None,
    )


def map_participants(data: object) -> list[Participant]:
    return [_map_participant(item) for item in _items(data)]


def _map_participant(item: Mapping[str, Any]) -> Participant:
    roles = tuple(
        _map_role(role)
        for role in item.get("roles") or ()
        if isinstance(role, Mapping)
    )
    groups = tuple(
        _map_group(group)
        for group in item.get("groups") or ()
        if isinstance(group, Mapping)
    )
    first_name = str(item.get("firstname") or "").strip()
    last_name = str(item.get("lastname") or "").strip()
    if not first_name and not last_name:
        first_name = str(item.get("fullname") or "").strip()
    email = item.get("email")
    return Participant(
        id=int(item.get("id", 0)),
        first_name=first_name,
        last_name=last_name,
        groups=groups,
        roles=roles,
        last_access=timestamp(item.get("lastcourseaccess")),
        email=str(email) if email else None,
    )


def _map_group(item: Mapping[str, Any]) -> Group:
    try:
        group_id = int(item.get("id", 0) or 0)
    except (TypeError, ValueError):
        group_id = 0
    return Group(
        id=group_id,
        name=str(item.get("name") or "").strip(),
    )


def _map_role(item: Mapping[str, Any]) -> Role:
    try:
        role_id = int(item.get("roleid", 0) or 0)
    except (TypeError, ValueError):
        role_id = 0
    return Role(
        id=role_id,
        short_name=str(item.get("shortname") or "").strip(),
        name=str(item.get("name") or "").strip(),
    )


def map_assignments(data: object) -> list[Assignment]:
    if not isinstance(data, Mapping):
        return []
    assignments: list[Assignment] = []
    for course in data.get("courses") or ():
        if not isinstance(course, Mapping):
            continue
        course_id = int(course.get("id", 0))
        for item in course.get("assignments") or ():
            if isinstance(item, Mapping):
                assignments.append(_map_assignment(item, course_id))
    return assignments


def _map_assignment(item: Mapping[str, Any], course_id: int) -> Assignment:
    raw_grade = item.get("grade")
    max_grade: float | None
    try:
        max_grade = float(raw_grade)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        max_grade = None
    return Assignment(
        id=int(item.get("id", 0)),
        course_id=course_id,
        name=str(item.get("name", "")),
        due_date=timestamp(item.get("duedate")),
        cutoff_date=timestamp(item.get("cutoffdate")),
        max_grade=max_grade,
    )


def map_forums(data: object) -> list[Forum]:
    return [_map_forum(item) for item in _items(data)]


def _map_forum(item: Mapping[str, Any]) -> Forum:
    return Forum(
        id=int(item.get("id", 0)),
        course_id=int(item.get("course", 0)),
        name=str(item.get("name", "")),
        type=str(item.get("type", "")),
        force_subscribe=_as_bool(item.get("forcesubscribe")),
    )


def map_announcements(data: object) -> list[Announcement]:
    if not isinstance(data, Mapping):
        return []
    return [
        _map_announcement(item)
        for item in data.get("discussions") or ()
        if isinstance(item, Mapping)
    ]


def _map_announcement(item: Mapping[str, Any]) -> Announcement:
    return Announcement(
        id=int(item.get("id", 0)),
        subject=str(item.get("name", "")),
        author=str(item.get("userfullname", "")),
        created=timestamp(item.get("created")),
        num_replies=int(item.get("numreplies", 0) or 0),
        pinned=_as_bool(item.get("pinned")),
        locked=_as_bool(item.get("locked")),
    )


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no"}
    return bool(value)


def _items(data: object) -> list[Mapping[str, Any]]:
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, Mapping)]
