"""Errores de dominio. La CLI los traduce a mensajes y códigos de salida."""

from __future__ import annotations


class MooviError(Exception):
    """Base de todos los errores controlados de Moovi."""


class ConfigError(MooviError):
    """Falta configuración o no es válida."""


class InvalidCredentialsError(MooviError):
    """Usuario o contraseña incorrectos."""


class InvalidTokenError(MooviError):
    """El token ha caducado o no es válido."""


class AuthorizationError(MooviError):
    """Moovi ha denegado el acceso a la operación."""


class NetworkError(MooviError):
    """No se pudo hablar con Moovi."""


class ReadOnlyViolation(MooviError):
    """Se intentó llamar a una función que no está permitida en modo lectura."""


class NoAnnouncementsForumError(MooviError):
    """El curso no tiene el foro de noticias de Moovi."""

    def __init__(self, course_id: int, forums: object) -> None:
        self.course_id = course_id
        self.forums = tuple(forums)  # type: ignore[arg-type]
        super().__init__(
            f"El curso {course_id} no tiene foro de noticias de Moovi."
        )


class AmbiguousForumError(MooviError):
    """Hay varios foros de noticias y no se puede elegir uno solo."""

    def __init__(self, course_id: int, forums: object) -> None:
        self.course_id = course_id
        self.forums = tuple(forums)  # type: ignore[arg-type]
        super().__init__(
            f"Hay varios foros de noticias en el curso {course_id}."
        )


class ApiError(MooviError):
    """Error devuelto por la API de Moodle."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}" if code else message)
