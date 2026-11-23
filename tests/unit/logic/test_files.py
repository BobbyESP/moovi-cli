from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest

from moovi.domain.errors import (
    AuthorizationError,
    InvalidTokenError,
    UnknownModuleError,
)
from moovi.domain.models import Module, RemoteFile, Section, StoredFile
from moovi.logic.services.files import FileService

MODIFIED = datetime(2026, 1, 1, tzinfo=timezone.utc)


def remote(name: str, folder: str = "", data: bytes = b"data") -> RemoteFile:
    return RemoteFile(name, f"https://m/{name}", folder, len(data), MODIFIED)


SECTIONS = [
    Section(
        1,
        "Tema 1",
        "",
        (
            Module(10, "Apuntes", "resource", True, files=(remote("a.pdf"),)),
            Module(
                11,
                "Prácticas",
                "folder",
                True,
                files=(remote("b.pdf", "sub/dir"), remote("c.pdf", "../..")),
            ),
            Module(12, "Web", "url", True, files=(remote("x.html"),)),
            Module(13, "Foro", "forum", True),
        ),
    ),
    Section(
        2,
        "Tema 1",
        "",
        (Module(14, "Apuntes 2", "resource", True, files=(remote("A.PDF"),)),),
    ),
]


class FakeSession:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.opened: list[str] = []

    def contents(self, course_id: int) -> list[Section]:
        return SECTIONS

    def open_file(self, url: str) -> io.BytesIO:
        self.opened.append(url)
        if self.error:
            raise self.error
        return io.BytesIO(b"data")


class MemoryStore:
    def __init__(self, existing: dict[str, StoredFile] | None = None) -> None:
        self.existing = existing or {}
        self.saved: dict[str, bytes] = {}

    def stat(self, path: str) -> StoredFile | None:
        return self.existing.get(path)

    def save(self, path, source, *, size=None, modified=None) -> int:
        self.saved[path] = source.read()
        return len(self.saved[path])


def test_list_files_builds_safe_unique_paths() -> None:
    files = FileService(FakeSession()).list_files(101)

    assert [item.path for item in files] == [
        "Tema 1/a.pdf",
        "Tema 1/Prácticas/sub/dir/b.pdf",
        "Tema 1/Prácticas/_/_/c.pdf",
        "Tema 1/A (14).PDF",
    ]


def test_list_files_filters_by_module() -> None:
    files = FileService(FakeSession()).list_files(101, [11])

    assert {item.module_id for item in files} == {11}


def test_paths_do_not_depend_on_the_selection() -> None:
    service = FileService(FakeSession())

    [selected] = service.list_files(101, [14])

    assert selected.path == "Tema 1/A (14).PDF"


@pytest.mark.parametrize("module_id", [12, 13, 999])
def test_list_files_rejects_non_downloadable_modules(module_id: int) -> None:
    with pytest.raises(UnknownModuleError):
        FileService(FakeSession()).list_files(101, [module_id])


def test_download_saves_files() -> None:
    service = FileService(FakeSession())
    store = MemoryStore()

    results = service.download(service.list_files(101, [10]), into=store)

    assert [result.status for result in results] == ["downloaded"]
    assert store.saved == {"Tema 1/a.pdf": b"data"}


def test_download_skips_current_file_without_opening_it() -> None:
    session = FakeSession()
    service = FileService(session)
    store = MemoryStore({"Tema 1/a.pdf": StoredFile(4, MODIFIED)})

    [result] = service.download(service.list_files(101, [10]), into=store)

    assert result.status == "skipped"
    assert session.opened == []


def test_download_reports_conflict_and_keeps_local_file() -> None:
    service = FileService(FakeSession())
    store = MemoryStore({"Tema 1/a.pdf": StoredFile(99, MODIFIED)})

    [result] = service.download(service.list_files(101, [10]), into=store)

    assert result.status == "conflict"
    assert store.saved == {}


def test_download_overwrite_replaces_different_file() -> None:
    service = FileService(FakeSession())
    store = MemoryStore({"Tema 1/a.pdf": StoredFile(99, MODIFIED)})

    [result] = service.download(
        service.list_files(101, [10]), into=store, overwrite=True
    )

    assert result.status == "downloaded"
    assert store.saved["Tema 1/a.pdf"] == b"data"


def test_download_continues_after_a_file_error() -> None:
    service = FileService(FakeSession(AuthorizationError("denegado")))

    results = service.download(service.list_files(101), into=MemoryStore())

    assert len(results) == 4
    assert {result.status for result in results} == {"failed"}
    assert results[0].error == "denegado"


def test_download_propagates_invalid_token() -> None:
    service = FileService(FakeSession(InvalidTokenError("caducado")))

    with pytest.raises(InvalidTokenError):
        service.download(service.list_files(101), into=MemoryStore())


def test_iter_download_is_lazy() -> None:
    session = FakeSession()
    service = FileService(session)
    files = service.list_files(101)

    iterator = service.iter_download(files, MemoryStore())

    assert session.opened == []
    next(iterator)
    assert len(session.opened) == 1
