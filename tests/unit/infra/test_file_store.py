from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path

import pytest

from moovi.domain.errors import IncompleteDownloadError
from moovi.infra.file_store import LocalFileStore

MODIFIED = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_save_creates_folders_and_preserves_mtime(tmp_path: Path) -> None:
    store = LocalFileStore(tmp_path)

    written = store.save("a/b/c.txt", io.BytesIO(b"hola"), size=4, modified=MODIFIED)

    assert written == 4
    assert (tmp_path / "a/b/c.txt").read_bytes() == b"hola"
    stored = store.stat("a/b/c.txt")
    assert stored is not None
    assert stored.size == 4
    assert stored.modified == MODIFIED


def test_stat_missing_file(tmp_path: Path) -> None:
    assert LocalFileStore(tmp_path).stat("no.txt") is None


def test_incomplete_download_keeps_previous_file(tmp_path: Path) -> None:
    target = tmp_path / "c.txt"
    target.write_bytes(b"anterior")
    store = LocalFileStore(tmp_path)

    with pytest.raises(IncompleteDownloadError):
        store.save("c.txt", io.BytesIO(b"xx"), size=10)

    assert target.read_bytes() == b"anterior"
    assert [path.name for path in tmp_path.iterdir()] == ["c.txt"]


@pytest.mark.parametrize("path", ["../fuera.txt", "a/../../fuera.txt", "."])
def test_rejects_paths_outside_root(tmp_path: Path, path: str) -> None:
    store = LocalFileStore(tmp_path / "destino")

    with pytest.raises(PermissionError):
        store.save(path, io.BytesIO(b"x"))

    assert not (tmp_path / "fuera.txt").exists()
