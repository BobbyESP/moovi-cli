"""Comandos de personas matriculadas."""

from __future__ import annotations

import argparse

from moovi.cli.context import Services
from moovi.cli.render import print_json, render_participants


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    students = subparsers.add_parser(
        "students",
        parents=[common],
        help="Listar las personas matriculadas en un curso",
    )
    students.add_argument("course_id", type=int, metavar="COURSE_ID")
    students.add_argument(
        "--emails",
        action="store_true",
        help="Incluir direcciones de correo (por defecto se omiten)",
    )
    students.set_defaults(handler=_students)


def _students(args: argparse.Namespace, services: Services) -> int:
    participants = services.people.list_participants(
        args.course_id, include_email=args.emails
    )
    limit = getattr(args, "limit", None)
    if limit:
        participants = participants[:limit]
    if getattr(args, "json", False):
        print_json(participants)
    else:
        render_participants(participants, include_email=args.emails)
    return 0
