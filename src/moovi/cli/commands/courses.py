"""Comandos de cursos y contenido."""

from __future__ import annotations

import argparse

from moovi.cli.context import Services
from moovi.cli.render import (
    print_json,
    render_courses,
    render_sections,
)


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    courses = subparsers.add_parser(
        "courses",
        parents=[common],
        help="Listar los cursos en los que estás matriculado",
    )
    courses.set_defaults(handler=_courses)

    contents = subparsers.add_parser(
        "contents",
        parents=[common],
        help="Ver secciones y actividades de un curso",
    )
    contents.add_argument("course_id", type=int, metavar="COURSE_ID")
    contents.set_defaults(handler=_contents)


def _courses(args: argparse.Namespace, services: Services) -> int:
    courses = _limit(services.catalog.list_courses(), args)
    if getattr(args, "json", False):
        print_json(courses)
    else:
        render_courses(courses)
    return 0


def _contents(args: argparse.Namespace, services: Services) -> int:
    sections = services.catalog.get_contents(args.course_id)
    if getattr(args, "json", False):
        print_json(sections)
    else:
        render_sections(sections)
    return 0


def _limit(items: list, args: argparse.Namespace) -> list:
    limit = getattr(args, "limit", None)
    return items[:limit] if limit else items
