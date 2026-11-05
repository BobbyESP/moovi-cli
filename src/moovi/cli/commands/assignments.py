"""Comandos de tareas."""

from __future__ import annotations

import argparse

from moovi.cli.context import Services
from moovi.cli.formats.base import Formatter
from moovi.cli.tables import AssignmentsTable


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    assignments = subparsers.add_parser(
        "assignments",
        parents=[common],
        help="Listar las tareas de un curso",
    )
    assignments.add_argument("course_id", type=int, metavar="COURSE_ID")
    assignments.set_defaults(handler=_assignments)


def _assignments(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    items = services.assignments.list_assignments(args.course_id)
    limit = getattr(args, "limit", None)
    if limit:
        items = items[:limit]
    formatter.render(AssignmentsTable(items))
    return 0
