from pathlib import Path

import pytest

from moovi.domain.errors import ConfigError
from moovi.infra.settings import DEFAULT_SITE, load_settings


def write_env(tmp_path: Path, content: str) -> Path:
    path = tmp_path / ".env"
    path.write_text(content, encoding="utf-8")
    return path


def test_reads_dotenv(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path,
        """
        # comentario
        MOOVI_USER=profesor
        MOOVI_PASSWORD="secreto con espacios"
        MOOVI_URL=https://moovi.uvigo.gal/
        """,
    )

    settings = load_settings(env_file=env_file, environ={})

    assert settings.username == "profesor"
    assert settings.password == "secreto con espacios"
    assert settings.site == "https://moovi.uvigo.gal"


def test_environment_overrides_dotenv(tmp_path: Path) -> None:
    env_file = write_env(tmp_path, "MOOVI_USER=fichero\nMOOVI_PASSWORD=uno\n")

    settings = load_settings(
        env_file=env_file,
        environ={"MOOVI_USER": "entorno", "MOOVI_PASSWORD": "dos"},
    )

    assert settings.username == "entorno"
    assert settings.password == "dos"


def test_uses_default_site(tmp_path: Path) -> None:
    env_file = write_env(tmp_path, "MOOVI_USER=profesor\n")

    settings = load_settings(env_file=env_file, environ={})

    assert settings.site == DEFAULT_SITE


def test_requires_username(tmp_path: Path) -> None:
    env_file = write_env(tmp_path, "MOOVI_PASSWORD=x\n")

    with pytest.raises(ConfigError, match="MOOVI_USER"):
        load_settings(env_file=env_file, environ={})


def test_rejects_plain_http_outside_localhost(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path, "MOOVI_USER=profesor\nMOOVI_URL=http://moovi.uvigo.gal\n"
    )

    with pytest.raises(ConfigError, match="https"):
        load_settings(env_file=env_file, environ={})


def test_allows_http_on_loopback(tmp_path: Path) -> None:
    env_file = write_env(
        tmp_path, "MOOVI_USER=profesor\nMOOVI_URL=http://127.0.0.1:8080\n"
    )

    settings = load_settings(env_file=env_file, environ={})

    assert settings.site == "http://127.0.0.1:8080"


def test_token_and_cache_path(tmp_path: Path) -> None:
    env_file = write_env(tmp_path, "MOOVI_USER=profesor\nMOOVI_TOKEN=abc\n")

    settings = load_settings(
        env_file=env_file,
        environ={"XDG_CACHE_HOME": str(tmp_path / "cache")},
    )

    assert settings.token is not None
    assert settings.token.value == "abc"
    assert settings.cache_path == tmp_path / "cache" / "moovi" / "token.json"


def test_supports_export_prefix(tmp_path: Path) -> None:
    env_file = write_env(tmp_path, "export MOOVI_USER=profesor\n")

    assert load_settings(env_file=env_file, environ={}).username == "profesor"


def test_missing_env_file_is_not_an_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="MOOVI_USER"):
        load_settings(env_file=tmp_path / "no-existe", environ={})
