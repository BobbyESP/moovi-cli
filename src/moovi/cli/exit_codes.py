"""Traducción de errores de dominio a códigos de salida."""

from __future__ import annotations

from moovi.domain.errors import (
    ApiError,
    AuthorizationError,
    ConfigError,
    InvalidCredentialsError,
    InvalidTokenError,
    MooviError,
    NetworkError,
    ReadOnlyViolation,
)


def exit_code_for(error: MooviError) -> int:
    if isinstance(error, (ConfigError, InvalidCredentialsError, InvalidTokenError)):
        return 2
    if isinstance(error, (AuthorizationError, ReadOnlyViolation)):
        return 4
    if isinstance(error, (ApiError, NetworkError)):
        return 3
    return 1
