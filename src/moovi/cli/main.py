"""Punto de entrada de la CLI y composition root."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from moovi import __version__
from moovi.cli.commands import assignments, auth, courses, people
from moovi.cli.context import build_services
from moovi.cli.exit_codes import exit_code_for
from moovi.cli.render import print_error
from moovi.domain.errors import MooviError
from moovi.infra.settings import load_settings


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"'{value}' no es un número entero") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("el límite debe ser mayor que cero")
    return number


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Emitir JSON (solo el JSON en stdout)",
    )
    common.add_argument(
        "--limit",
        type=_positive_int,
        default=argparse.SUPPRESS,
        metavar="N",
        help="Máximo de elementos a mostrar",
    )

    parser = argparse.ArgumentParser(
        prog="moovi",
        parents=[common],
        description="Consulta Moovi (Moodle UVigo) en modo de solo lectura.",
    )
    parser.add_argument(
        "--version", action="version", version=f"moovi {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    auth.register(subparsers, common)
    courses.register(subparsers, common)
    people.register(subparsers, common)
    assignments.register(subparsers, common)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    as_json = getattr(args, "json", False)
    try:
        services = build_services(load_settings())
        return int(args.handler(args, services))
    except MooviError as exc:
        print_error(exc, as_json=as_json)
        return exit_code_for(exc)
    except KeyboardInterrupt:
        return 130
