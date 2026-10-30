"""Carga de configuración desde variables de entorno y un fichero ``.env``."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from moovi.domain.errors import ConfigError
from moovi.domain.values import Token

DEFAULT_SITE = "https://moovi.uvigo.gal"
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass(frozen=True, slots=True)
class Settings:
    site: str
    username: str | None
    password: str | None
    token: Token | None
    cache_path: Path


def load_settings(
    *,
    env_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    """Lee ``.env`` y el entorno. Las variables de entorno tienen prioridad."""

    values = _read_env_file(env_file or Path(".env"))
    values.update(dict(environ if environ is not None else os.environ))

    site = _validate_site(values.get("MOOVI_URL", DEFAULT_SITE).strip())
    username = values.get("MOOVI_USER", "").strip() or None

    password = values.get("MOOVI_PASSWORD") or None
    raw_token = values.get("MOOVI_TOKEN") or None
    token = Token(raw_token) if raw_token else None

    cache_root = values.get("XDG_CACHE_HOME")
    cache_dir = Path(cache_root) if cache_root else Path.home() / ".cache"
    cache_path = cache_dir / "moovi" / "token.json"

    return Settings(
        site=site,
        username=username,
        password=password,
        token=token,
        cache_path=cache_path,
    )


def _validate_site(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ConfigError(
            f"MOOVI_URL no es una URL válida: {url!r}. Ejemplo: {DEFAULT_SITE}"
        )
    if parsed.scheme == "http" and parsed.hostname not in _LOOPBACK_HOSTS:
        raise ConfigError(
            "Moovi debe usar https. http solo se permite en localhost para tests."
        )
    return url.rstrip("/")


def _read_env_file(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise ConfigError(f"No se pudo leer {path}: {exc}") from exc

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values
