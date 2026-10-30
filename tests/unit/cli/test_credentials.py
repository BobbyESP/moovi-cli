from __future__ import annotations

import pytest

from moovi.cli import credentials
from moovi.domain.errors import ConfigError


class _TTY:
    def isatty(self) -> bool:
        return True


class _NoTTY:
    def isatty(self) -> bool:
        return False


def test_prompt_username_uses_default(monkeypatch) -> None:
    monkeypatch.setattr(credentials.sys, "stdin", _TTY())
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    assert credentials.prompt_username("profesor") == "profesor"


def test_prompt_username_accepts_value(monkeypatch) -> None:
    monkeypatch.setattr(credentials.sys, "stdin", _TTY())
    monkeypatch.setattr("builtins.input", lambda prompt: " otra ")

    assert credentials.prompt_username("profesor") == "otra"


def test_prompt_username_rejects_empty(monkeypatch) -> None:
    monkeypatch.setattr(credentials.sys, "stdin", _TTY())
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    with pytest.raises(ConfigError, match="usuario"):
        credentials.prompt_username(None)


def test_prompt_password_hides_input(monkeypatch) -> None:
    monkeypatch.setattr(credentials.sys, "stdin", _TTY())
    monkeypatch.setattr(credentials.getpass, "getpass", lambda prompt: "secreto")

    assert credentials.prompt_password() == "secreto"


def test_prompt_rejects_empty_password(monkeypatch) -> None:
    monkeypatch.setattr(credentials.sys, "stdin", _TTY())
    monkeypatch.setattr(credentials.getpass, "getpass", lambda prompt: "")

    with pytest.raises(ConfigError, match="contraseña"):
        credentials.prompt_password()


def test_prompt_requires_a_tty(monkeypatch) -> None:
    monkeypatch.setattr(credentials.sys, "stdin", _NoTTY())

    with pytest.raises(ConfigError, match="terminal"):
        credentials.prompt_username(None)
    with pytest.raises(ConfigError, match="terminal"):
        credentials.prompt_password()
