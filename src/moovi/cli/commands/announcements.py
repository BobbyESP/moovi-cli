"""Comando específico para el foro de noticias de Moovi."""

from __future__ import annotations

import argparse
import sys

from moovi.cli.context import Services
from moovi.cli.formats.base import Formatter
from moovi.cli.tables import AnnouncementContentTable, AnnouncementsTable
from moovi.domain.errors import (
    AmbiguousForumError,
    NoAnnouncementsForumError,
)
from moovi.domain.models import Forum
from moovi.logic.services.announcements import DEFAULT_ANNOUNCEMENTS_LIMIT


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    announcements = subparsers.add_parser(
        "announcements",
        parents=[common],
        help="Listar el foro de noticias de Moovi",
    )
    announcements.add_argument("course_id", type=int, metavar="COURSE_ID")
    announcements.add_argument(
        "--forum-id",
        type=_positive_int,
        default=None,
        metavar="ID",
        help="Usar un foro concreto si hay ambigüedad",
    )
    announcements.set_defaults(handler=_announcements)

    content = subparsers.add_parser(
        "announcement-content",
        parents=[common],
        help="Ver el contenido de un anuncio de Moovi",
    )
    content.add_argument(
        "announcement_id", type=_positive_int, metavar="ANNOUNCEMENT_ID"
    )
    content.set_defaults(handler=_announcement_content)


def _announcements(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    limit = getattr(args, "limit", None) or DEFAULT_ANNOUNCEMENTS_LIMIT
    try:
        items = services.announcements.list_announcements(
            args.course_id,
            forum_id=args.forum_id,
            limit=limit,
        )
    except AmbiguousForumError as exc:
        _print_forums(
            exc.course_id, exc.forums, "Hay varios foros de noticias"
        )
        sys.stderr.write(
            "Usa --forum-id <ID> para elegir uno de ellos.\n"
        )
        return 2
    except NoAnnouncementsForumError as exc:
        _print_forums(
            exc.course_id,
            exc.forums,
            "Este curso no tiene foro de noticias. Foros disponibles",
        )
        sys.stderr.write(
            "Si quieres consultar otro foro, usa --forum-id <ID>.\n"
        )
        return 2

    formatter.render(AnnouncementsTable(items))
    return 0


def _announcement_content(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    content = services.announcements.get_content(args.announcement_id)
    formatter.render(AnnouncementContentTable(content))
    return 0


def _print_forums(course_id: int, forums: tuple[Forum, ...], title: str) -> None:
    sys.stderr.write(f"{title} (curso {course_id}):\n")
    if not forums:
        sys.stderr.write("  (no hay foros en este curso)\n")
        return
    for forum in forums:
        sys.stderr.write(f"  - {forum.id}: {forum.name} [{forum.type}]\n")


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"'{value}' no es un número entero"
        ) from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("el id debe ser mayor que cero")
    return number
