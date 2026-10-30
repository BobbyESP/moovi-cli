from __future__ import annotations

import pytest

from moovi.domain.errors import ConfigError, InvalidTokenError
from moovi.domain.models import SiteInfo
from moovi.domain.values import Token
from moovi.logic.session import MoodleSession

SITE = SiteInfo(
    user_id=42,
    username="profesor",
    full_name="Profesor de Prueba",
    site_name="Moovi UVigo",
    release="4.5",
)


class FakeGateway:
    def __init__(self) -> None:
        self.login_calls = 0
        self.calls: list[tuple[str, str]] = []
        self.invalid_once = False
        self.users_courses_user_id: int | None = None

    def login(self, username: str, password: str) -> Token:
        self.login_calls += 1
        assert username == "profesor"
        assert password == "secreto"
        return Token("fresh-token")

    def site_info(self, token: Token) -> SiteInfo:
        self.calls.append(("site_info", token.value))
        if self.invalid_once:
            self.invalid_once = False
            raise InvalidTokenError("expired")
        return SITE

    def users_courses(self, token: Token, user_id: int) -> list:
        self.calls.append(("users_courses", token.value))
        self.users_courses_user_id = user_id
        return []

    def course_contents(self, token: Token, course_id: int) -> list:
        self.calls.append(("course_contents", token.value))
        return []

    def enrolled_users(self, token: Token, course_id: int) -> list:
        self.calls.append(("enrolled_users", token.value))
        return []

    def assignments(self, token: Token, course_ids: list[int]) -> list:
        self.calls.append(("assignments", token.value))
        return []


class FakeStore:
    def __init__(
        self, token: Token | None = None, username: str = "profesor"
    ) -> None:
        self.token = token
        self.username = username
        self.saved: list[Token] = []

    def load(self, site: str, username: str | None = None) -> Token | None:
        if self.token is None:
            return None
        if username is not None and username != self.username:
            return None
        return self.token

    def load_username(self, site: str) -> str | None:
        return self.username if self.token is not None else None

    def save(self, site: str, username: str, token: Token) -> None:
        self.token = token
        self.username = username
        self.saved.append(token)

    def clear(self, site: str, username: str | None = None) -> None:
        self.token = None


def build(
    gateway,
    store,
    password="secreto",
    explicit_token=None,
    username: str | None = "profesor",
):
    return MoodleSession(
        gateway,
        store,
        site="https://moovi.uvigo.gal",
        username=username,
        password=password,
        explicit_token=explicit_token,
    )


def test_uses_cached_token_without_login() -> None:
    gateway = FakeGateway()
    store = FakeStore(Token("cached-token"))

    info = build(gateway, store, password=None).site_info()

    assert info == SITE
    assert gateway.login_calls == 0
    assert gateway.calls == [("site_info", "cached-token")]


def test_logs_in_and_saves_token_when_cache_is_empty() -> None:
    gateway = FakeGateway()
    store = FakeStore()

    build(gateway, store).site_info()

    assert gateway.login_calls == 1
    assert [token.value for token in store.saved] == ["fresh-token"]
    assert gateway.calls == [("site_info", "fresh-token")]


def test_requires_login_when_there_is_no_token() -> None:
    gateway = FakeGateway()
    store = FakeStore()

    with pytest.raises(ConfigError, match="moovi login"):
        build(gateway, store, password=None).site_info()


def test_loads_cached_token_without_configured_username() -> None:
    gateway = FakeGateway()
    store = FakeStore(Token("cached-token"), username="profesor")

    session = build(gateway, store, password=None, username=None)
    info = session.site_info()

    assert info == SITE
    assert session.username == "profesor"
    assert gateway.login_calls == 0
    assert gateway.calls == [("site_info", "cached-token")]


def test_login_with_saves_token_and_username() -> None:
    gateway = FakeGateway()
    store = FakeStore()

    session = build(gateway, store, password=None, username=None)
    info = session.login_with("profesor", "secreto")

    assert info == SITE
    assert session.username == "profesor"
    assert gateway.login_calls == 1
    assert store.username == "profesor"
    assert store.token is not None and store.token.value == "fresh-token"
    assert gateway.calls == [("site_info", "fresh-token")]


def test_suggested_username_comes_from_cache() -> None:
    gateway = FakeGateway()
    store = FakeStore(Token("cached-token"), username="profesor")

    session = build(gateway, store, password=None, username=None)

    assert session.username == "profesor"


def test_relogins_once_when_token_is_invalid() -> None:
    gateway = FakeGateway()
    gateway.invalid_once = True
    store = FakeStore(Token("cached-token"))

    build(gateway, store).site_info()

    assert gateway.login_calls == 1
    assert gateway.calls == [
        ("site_info", "cached-token"),
        ("site_info", "fresh-token"),
    ]
    assert store.token is not None and store.token.value == "fresh-token"


def test_explicit_token_takes_precedence_over_cache() -> None:
    gateway = FakeGateway()
    store = FakeStore(Token("cached-token"))

    session = build(gateway, store, password=None, explicit_token=Token("env-token"))
    session.site_info()

    assert gateway.calls == [("site_info", "env-token")]
    assert store.saved == []


def test_invalid_token_without_password_reports_configuration_error() -> None:
    gateway = FakeGateway()
    gateway.invalid_once = True
    store = FakeStore(Token("cached-token"))

    with pytest.raises(ConfigError):
        build(gateway, store, password=None).site_info()


def test_force_login_with_explicit_token_does_not_require_password() -> None:
    gateway = FakeGateway()
    store = FakeStore()

    session = build(
        gateway, store, password=None, explicit_token=Token("env-token")
    )
    session.relogin()

    assert gateway.login_calls == 0
    assert session.site_info().username == "profesor"


def test_courses_uses_the_authenticated_user_id() -> None:
    gateway = FakeGateway()
    store = FakeStore(Token("cached-token"))

    build(gateway, store, password=None).courses()

    assert gateway.users_courses_user_id == 42
