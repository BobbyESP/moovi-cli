"""Comandos de autenticación."""

from __future__ import annotations

import argparse
import sys

from moovi.cli.context import Services
from moovi.cli.credentials import prompt_password, prompt_username
from moovi.cli.formats.base import Formatter
from moovi.domain.errors import ConfigError, InvalidTokenError


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
    login.add_argument(
        "--no-input",
        action="store_true",
        help=(
            "No preguntar credenciales; usar MOOVI_USER y MOOVI_PASSWORD "
            "del entorno"
        ),
    )
    login.set_defaults(handler=_login)

    whoami = subparsers.add_parser(
        "whoami",
        parents=[common],
        help="Mostrar la identidad y el sitio de Moovi",
    )
    whoami.set_defaults(handler=_whoami)


def _login(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    if args.no_input:
        try:
            info = services.auth.login(force=args.force)
        except ConfigError as exc:
            raise ConfigError(
                "No hay credenciales para --no-input. Define MOOVI_USER y "
                "MOOVI_PASSWORD en el entorno."
            ) from exc
        formatter.site_info(info)
        return 0

    if not args.force:
        try:
            formatter.site_info(services.auth.login())
            return 0
        except (ConfigError, InvalidTokenError):
            pass

    suggested = services.auth.suggested_username()
    username = prompt_username(suggested)
    password = prompt_password()
    info = services.auth.login_interactive(username, password)
    formatter.site_info(info)
    if suggested is not None and username != suggested:
        sys.stderr.write(
            f"Aviso: token guardado para '{username}'. Actualiza o elimina "
            "MOOVI_USER para usar esta cuenta en futuras ejecuciones.\n"
        )
    return 0


def _whoami(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    formatter.site_info(services.auth.whoami())
    return 0
