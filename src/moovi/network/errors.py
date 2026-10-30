"""Traducción de errores de Moodle a errores de dominio."""

from __future__ import annotations

from collections.abc import Mapping

from moovi.domain.errors import (
    ApiError,
    AuthorizationError,
    InvalidCredentialsError,
    InvalidTokenError,
)

_PERMISSION_CODES = frozenset(
    {
        "accessexception",
        "nopermissions",
        "required_capability_exception",
        "webservice_access_exception",
    }
)


def raise_for_moodle_error(payload: Mapping[str, object]) -> None:
    """Lanza el error de dominio adecuado si ``payload`` es un error de Moodle.

    Moodle devuelve HTTP 200 incluso en los errores; el discriminante es la
    presencia de ``errorcode`` (o, en algunos endpoints, ``exception``).
    """

    errorcode = str(payload.get("errorcode") or "").strip()
    if not errorcode and not payload.get("exception"):
        return
    if not errorcode:
        errorcode = "unknown"

    message = str(payload.get("message") or payload.get("error") or errorcode)

    if errorcode == "invalidlogin":
        raise InvalidCredentialsError(
            "Credenciales incorrectas. Revisa MOOVI_USER y MOOVI_PASSWORD."
        )
    if errorcode == "invalidtoken":
        raise InvalidTokenError("El token de Moovi no es válido o ha caducado.")
    if errorcode in _PERMISSION_CODES:
        raise AuthorizationError(f"Moovi ha denegado el acceso: {message}")
    raise ApiError(errorcode, message)
