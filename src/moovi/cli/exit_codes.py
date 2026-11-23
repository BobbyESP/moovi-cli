"""Traducción de errores de dominio a códigos de salida."""

from __future__ import annotations

from moovi.domain.errors import (
    AmbiguousForumError,
    ApiError,
    AuthorizationError,
    ConfigError,
    IncompleteDownloadError,
    InvalidCredentialsError,
    InvalidTokenError,
    MooviError,
    NetworkError,
    NoAnnouncementsForumError,
    ReadOnlyViolation,
    UnknownModuleError,
)


def exit_code_for(error: MooviError) -> int:
    if isinstance(
        error,
        (
            ConfigError,
            InvalidCredentialsError,
            InvalidTokenError,
            AmbiguousForumError,
            NoAnnouncementsForumError,
            UnknownModuleError,
        ),
    ):
        return 2
    if isinstance(error, (AuthorizationError, ReadOnlyViolation)):
        return 4
    if isinstance(error, (ApiError, IncompleteDownloadError, NetworkError)):
        return 3
    return 1
