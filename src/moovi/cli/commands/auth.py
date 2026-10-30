"""Comandos de autenticación."""

from __future__ import annotations

import argparse

from moovi.cli.context import Services
from moovi.cli.render import print_json, render_site_info


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    login = subparsers.add_parser(
        "login",
        parents=[common],
        help="Autenticarse contra Moovi y guardar el token",
    )
    login.add_argument(
        "--force",
        action="store_true",
        help="Ignorar el token guardado y volver a autenticarse",
    )
    login.set_defaults(handler=_login)

    whoami = subparsers.add_parser(
        "whoami",
        parents=[common],
        help="Mostrar la identidad y el sitio de Moovi",
    )
    whoami.set_defaults(handler=_whoami)


def _login(args: argparse.Namespace, services: Services) -> int:
    info = services.auth.login(force=args.force)
    _output_info(args, info)
    return 0


def _whoami(args: argparse.Namespace, services: Services) -> int:
    info = services.auth.whoami()
    _output_info(args, info)
    return 0


def _output_info(args: argparse.Namespace, info) -> None:
    if getattr(args, "json", False):
        print_json(info)
    else:
        render_site_info(info)
