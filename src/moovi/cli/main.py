"""Punto de entrada de la CLI y composition root."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from moovi import __version__
from moovi.cli.commands import assignments, auth, courses, people
from moovi.cli.context import build_services
from moovi.cli.errors import print_error
from moovi.cli.exit_codes import exit_code_for
from moovi.cli.formats import FORMATS, create_formatter
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
        help="Alias de --format json",
    )
    common.add_argument(
        "--format",
        choices=FORMATS,
        default=argparse.SUPPRESS,
        help="Formato de salida: table (por defecto), json o raw (CSV)",
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


def _resolve_format(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> str:
    chosen = getattr(args, "format", None)
    if getattr(args, "json", False):
        if chosen is not None and chosen != "json":
            parser.error("--json y --format no pueden contradecirse")
        chosen = "json"
    return chosen or "table"


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_format = _resolve_format(args, parser)
    try:
        formatter = create_formatter(output_format)
        services = build_services(load_settings())
        return int(args.handler(args, services, formatter))
    except MooviError as exc:
        print_error(exc, as_json=output_format == "json")
        return exit_code_for(exc)
    except BrokenPipeError:
        # `moovi ... | head` cierra el pipe antes de terminar; no es un error.
        _silence_broken_pipe()
        return 0
    except KeyboardInterrupt:
        return 130


def _silence_broken_pipe() -> None:
    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        os.close(devnull)
    except OSError:
        pass
