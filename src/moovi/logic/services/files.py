"""Casos de uso de archivos: listar y descargar recursos y carpetas."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Iterator

from moovi.domain.errors import (
    ApiError,
    AuthorizationError,
    IncompleteDownloadError,
    NetworkError,
    UnknownModuleError,
)
from moovi.domain.models import (
    CourseFile,
    DownloadResult,
    Module,
    RemoteFile,
    Section,
    StoredFile,
)
from moovi.domain.paths import safe_name, safe_parts, with_label
from moovi.logic.ports import FileStore
from moovi.logic.session import MoodleSession

DOWNLOADABLE_MODULES = frozenset({"resource", "folder"})

# Algunos sistemas de ficheros solo guardan la fecha con resolución de 2 s.
_MTIME_TOLERANCE_SECONDS = 2

# Un fallo en un archivo no aborta el resto. Un token inválido sí se propaga,
# porque afectaría a todas las descargas.
_PER_FILE_ERRORS = (
    ApiError,
    AuthorizationError,
    IncompleteDownloadError,
    NetworkError,
    OSError,
)


class FileService:
    def __init__(self, session: MoodleSession) -> None:
        self._session = session

    def list_files(
        self, course_id: int, module_ids: Collection[int] = ()
    ) -> list[CourseFile]:
        """Lista los archivos del curso, opcionalmente solo de ``module_ids``."""

        wanted = set(module_ids)
        # Las rutas se calculan sobre todo el curso para que sean estables:
        # un archivo no cambia de ruta según qué módulos se seleccionen.
        files = [
            item
            for item in _course_files(self._session.contents(course_id))
            if not wanted or item.module_id in wanted
        ]
        missing = wanted - {item.module_id for item in files}
        if missing:
            raise UnknownModuleError(course_id, missing)
        return files

    def iter_download(
        self,
        files: Iterable[CourseFile],
        into: FileStore,
        *,
        overwrite: bool = False,
    ) -> Iterator[DownloadResult]:
        """Descarga los archivos uno a uno y produce cada resultado al terminar."""

        for item in files:
            yield self._download_one(item, into, overwrite=overwrite)

    def download(
        self,
        files: Iterable[CourseFile],
        into: FileStore,
        *,
        overwrite: bool = False,
    ) -> list[DownloadResult]:
        """Descarga todos los archivos y devuelve sus resultados."""

        return list(self.iter_download(files, into, overwrite=overwrite))

    def _download_one(
        self, item: CourseFile, store: FileStore, *, overwrite: bool
    ) -> DownloadResult:
        remote = item.file
        try:
            stored = store.stat(item.path)
            if stored is not None:
                if _is_current(stored, remote):
                    return DownloadResult(item, "skipped")
                if not overwrite:
                    return DownloadResult(
                        item,
                        "conflict",
                        "El archivo local es distinto; usa --overwrite.",
                    )
            with self._session.open_file(remote.url) as stream:
                store.save(
                    item.path,
                    stream,
                    size=remote.size or None,
                    modified=remote.modified,
                )
        except _PER_FILE_ERRORS as exc:
            return DownloadResult(item, "failed", str(exc))
        return DownloadResult(item, "downloaded")


def _course_files(sections: Iterable[Section]) -> list[CourseFile]:
    taken: set[str] = set()
    files: list[CourseFile] = []
    for section in sections:
        for module in section.modules:
            if module.mod_name not in DOWNLOADABLE_MODULES:
                continue
            for remote in module.files:
                path = _unique_path(_local_parts(section, module, remote), module.id, taken)
                files.append(
                    CourseFile(module.id, module.name, section.name, remote, path)
                )
    return files


def _local_parts(section: Section, module: Module, remote: RemoteFile) -> list[str]:
    parts = [safe_name(section.name)]
    if module.mod_name == "folder":
        parts.append(safe_name(module.name))
    parts.extend(safe_parts(remote.folder))
    parts.append(safe_name(remote.name))
    return parts


def _unique_path(parts: list[str], module_id: int, taken: set[str]) -> str:
    """Evita colisiones, también en sistemas que no distinguen mayúsculas."""

    *folders, name = parts
    candidate = "/".join(parts)
    attempt = 1
    while candidate.casefold() in taken:
        label = str(module_id) if attempt == 1 else f"{module_id}-{attempt}"
        candidate = "/".join([*folders, with_label(name, label)])
        attempt += 1
    taken.add(candidate.casefold())
    return candidate


def _is_current(stored: StoredFile, remote: RemoteFile) -> bool:
    if stored.size != remote.size:
        return False
    if remote.modified is None:
        return True
    delta = abs((stored.modified - remote.modified).total_seconds())
    return delta <= _MTIME_TOLERANCE_SECONDS
