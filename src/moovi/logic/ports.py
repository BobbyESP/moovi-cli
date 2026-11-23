"""Puertos que la lógica necesita y que implementan los adaptadores."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self

from moovi.domain.models import (
    Announcement,
    AnnouncementContent,
    Assignment,
    Course,
    Forum,
    Participant,
    Section,
    SiteInfo,
    StoredFile,
)
from moovi.domain.values import Token


class ByteStream(Protocol):
    """Flujo binario de lectura que se usa con ``with``."""

    def read(self, size: int = -1, /) -> bytes: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...


class MoodleGateway(Protocol):
    """Acceso tipado a las funciones de Moodle que usa la aplicación."""

    def login(self, username: str, password: str) -> Token: ...

    def site_info(self, token: Token) -> SiteInfo: ...

    def users_courses(self, token: Token, user_id: int) -> list[Course]: ...

    def course_contents(self, token: Token, course_id: int) -> list[Section]: ...

    def enrolled_users(self, token: Token, course_id: int) -> list[Participant]:
        """Devuelve los participantes del curso.

        Es una operación Moodle: incluye los datos crudos disponibles, como el
        email, y no aplica políticas de privacidad.
        """
        ...

    def assignments(
        self, token: Token, course_ids: Sequence[int]
    ) -> list[Assignment]: ...

    def course_forums(self, token: Token, course_id: int) -> list[Forum]: ...

    def forum_discussions(
        self, token: Token, forum_id: int, limit: int
    ) -> list[Announcement]: ...

    def discussion_post(
        self, token: Token, post_id: int
    ) -> AnnouncementContent: ...

    def open_file(self, token: Token, url: str) -> ByteStream:
        """Abre un fichero de Moodle.

        Los errores de autenticación se lanzan aquí, no al leer, para que la
        sesión pueda renovar el token y reintentar.
        """
        ...


class FileStore(Protocol):
    """Destino de las descargas. Las rutas son relativas y usan ``/``."""

    def stat(self, path: str) -> StoredFile | None: ...

    def save(
        self,
        path: str,
        source: ByteStream,
        *,
        size: int | None = None,
        modified: datetime | None = None,
    ) -> int:
        """Guarda ``source`` de forma atómica y devuelve los bytes escritos.

        Si ``size`` no coincide, lanza ``IncompleteDownloadError`` y conserva
        el fichero anterior.
        """
        ...


class TokenStore(Protocol):
    """Persistencia del token entre ejecuciones."""

    def load(self, site: str, username: str | None = None) -> Token | None: ...

    def load_username(self, site: str) -> str | None: ...

    def save(self, site: str, username: str, token: Token) -> None: ...

    def clear(self, site: str, username: str | None = None) -> None: ...
