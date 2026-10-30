"""Sesión autenticada contra Moodle.

Resuelve el token (entorno, caché o login), lo renueva una vez si caduca y
delega las llamadas en el puerto ``MoodleGateway``. No formatea ni imprime.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from moovi.domain.errors import ConfigError, InvalidTokenError
from moovi.domain.models import (
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)
from moovi.domain.values import Token
from moovi.logic.ports import MoodleGateway, TokenStore

T = TypeVar("T")


class MoodleSession:
    def __init__(
        self,
        gateway: MoodleGateway,
        store: TokenStore,
        *,
        site: str,
        username: str,
        password: str | None = None,
        explicit_token: Token | None = None,
    ) -> None:
        self._gateway = gateway
        self._store = store
        self._site = site
        self._username = username
        self._password = password
        self._explicit_token = explicit_token
        self._token = explicit_token
        self._site_info: SiteInfo | None = None

    def relogin(self) -> None:
        """Fuerza un login nuevo e invalida la información del sitio cacheada."""
        self._site_info = None
        if self._explicit_token is not None:
            self._token = self._explicit_token
            return
        self._token = self._login()

    def _login(self) -> Token:
        if not self._password:
            raise ConfigError(
                "No hay contraseña de Moovi disponible. Define MOOVI_PASSWORD en "
                ".env o proporciona MOOVI_TOKEN."
            )
        token = self._gateway.login(self._username, self._password)
        self._store.save(self._site, self._username, token)
        return token

    def _get_token(self) -> Token:
        if self._token is not None:
            return self._token
        stored = self._store.load(self._site, self._username)
        if stored is not None:
            self._token = stored
            return stored
        self._token = self._login()
        return self._token

    def _call(self, method: Callable[[Token], T]) -> T:
        token = self._get_token()
        try:
            return method(token)
        except InvalidTokenError:
            self._token = self._login()
            return method(self._token)

    def site_info(self) -> SiteInfo:
        if self._site_info is None:
            self._site_info = self._call(self._gateway.site_info)
        return self._site_info

    def courses(self) -> list[Course]:
        info = self.site_info()
        return self._call(
            lambda token: self._gateway.users_courses(token, info.user_id)
        )

    def contents(self, course_id: int) -> list[Section]:
        return self._call(
            lambda token: self._gateway.course_contents(token, course_id)
        )

    def participants(self, course_id: int) -> list[Participant]:
        return self._call(
            lambda token: self._gateway.enrolled_users(token, course_id)
        )

    def assignments(self, course_ids: Sequence[int]) -> list[Assignment]:
        return self._call(
            lambda token: self._gateway.assignments(token, course_ids)
        )
