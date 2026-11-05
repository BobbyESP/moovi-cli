"""Comandos de personas matriculadas."""

from __future__ import annotations

import argparse

from moovi.cli.context import Services
from moovi.cli.formats.base import Formatter
from moovi.cli.tables import ParticipantsTable


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    participants = subparsers.add_parser(
        "participants",
        parents=[common],
        help="Listar las personas matriculadas en un curso",
    )
    participants.add_argument("course_id", type=int, metavar="COURSE_ID")
    participants.add_argument(
        "--emails",
        action="store_true",
        help="Incluir direcciones de correo (por defecto se omiten)",
    )
    participants.set_defaults(handler=_participants)


def _participants(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    participants = services.people.list_participants(
        args.course_id, include_email=args.emails
    )
    limit = getattr(args, "limit", None)
    if limit:
        participants = participants[:limit]
    formatter.render(
        ParticipantsTable(participants, include_email=args.emails)
    )
    return 0
