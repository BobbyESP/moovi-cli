"""Persistencia del token en un fichero local con permisos 0600."""

from __future__ import annotations

import json
import os
from pathlib import Path

from moovi.domain.values import Token


class FileTokenStore:
    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def load(self, site: str, username: str) -> Token | None:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        if data.get("site") != site or data.get("username") != username:
            return None
        token = data.get("token")
        if not isinstance(token, str) or not token:
            return None
        return Token(token)

    def save(self, site: str, username: str, token: Token) -> None:
        parent = self._path.parent
        parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except OSError:
            pass

        payload = json.dumps(
            {"site": site, "username": username, "token": token.value},
            ensure_ascii=False,
        )
        temporary = self._path.with_name(self._path.name + ".tmp")
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temporary, self._path)
        finally:
            if temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass
        os.chmod(self._path, 0o600)

    def clear(self, site: str, username: str) -> None:
        if self.load(site, username) is None:
            return
        try:
            self._path.unlink()
        except OSError:
            pass
