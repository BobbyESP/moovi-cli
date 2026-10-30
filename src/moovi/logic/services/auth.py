"""Casos de uso de autenticación."""

from __future__ import annotations

from moovi.domain.models import SiteInfo
from moovi.logic.session import MoodleSession


class AuthService:
    def __init__(self, session: MoodleSession) -> None:
        self._session = session

    def login(self, *, force: bool = False) -> SiteInfo:
        if force:
            self._session.relogin()
        return self._session.site_info()

    def whoami(self) -> SiteInfo:
        return self._session.site_info()

    def login_interactive(self, username: str, password: str) -> SiteInfo:
        return self._session.login_with(username, password)

    def suggested_username(self) -> str | None:
        return self._session.username
