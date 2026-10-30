"""Entrada de credenciales por terminal."""

from __future__ import annotations

import getpass
import sys

from moovi.domain.errors import ConfigError

_NO_TTY = (
    "No hay terminal para pedir credenciales. Usa `moovi login --no-input` "
    "con MOOVI_USER y MOOVI_PASSWORD, o ejecuta el comando en una terminal."
)


def prompt_username(default: str | None) -> str:
    _require_tty()
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"Usuario de Moovi{suffix}: ").strip()
    except EOFError as exc:
        raise ConfigError(_NO_TTY) from exc
    username = value or default or ""
    if not username:
        raise ConfigError("El usuario no puede estar vacío.")
    return username


def prompt_password() -> str:
    _require_tty()
    try:
        value = getpass.getpass("Contraseña de Moovi: ")
    except EOFError as exc:
        raise ConfigError(_NO_TTY) from exc
    if not value:
        raise ConfigError("La contraseña no puede estar vacía.")
    return value


def _require_tty() -> None:
    if not sys.stdin.isatty():
        raise ConfigError(_NO_TTY)
