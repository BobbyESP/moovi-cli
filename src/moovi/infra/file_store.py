"""Adaptador de ``FileStore``: directorio local con escritura atómica."""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from moovi.domain.errors import IncompleteDownloadError
from moovi.domain.models import StoredFile
from moovi.logic.ports import ByteStream, FileStore


class LocalFileStore(FileStore):
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)

    def stat(self, path: str) -> StoredFile | None:
        target = self._resolve(path)
        try:
            info = target.stat()
        except FileNotFoundError:
            return None
        return StoredFile(
            size=info.st_size,
            modified=datetime.fromtimestamp(info.st_mtime, tz=timezone.utc),
        )

    def save(
        self,
        path: str,
        source: ByteStream,
        *,
        size: int | None = None,
        modified: datetime | None = None,
    ) -> int:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            dir=target.parent, prefix=".moovi-", suffix=".part"
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                shutil.copyfileobj(source, handle)
                written = handle.tell()
            if size is not None and written != size:
                raise IncompleteDownloadError(size, written)
            if modified is not None:
                timestamp = modified.timestamp()
                os.utime(temporary, (timestamp, timestamp))
            os.replace(temporary, target)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
        return written

    def _resolve(self, path: str) -> Path:
        root = self._root.resolve()
        target = (root / path).resolve()
        if target == root or not target.is_relative_to(root):
            raise PermissionError(f"Ruta fuera del destino: {path}")
        return target
