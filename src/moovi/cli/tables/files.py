"""Tablas de datos de archivos y resultados de descarga."""

from __future__ import annotations

from collections.abc import Sequence

from moovi.cli.tables.base import Column, RichValue, Table
from moovi.domain.models import CourseFile, DownloadResult

_STATUS_LABELS = {
    "downloaded": "descargado",
    "skipped": "al día",
    "conflict": "conflicto",
    "failed": "error",
}


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB"):
        if value < 1024:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def _size_value(size: int) -> RichValue:
    return RichValue(raw=size, text=format_size(size), csv_text=str(size))


class FilesTable(Table):
    def __init__(self, files: Sequence[CourseFile]) -> None:
        self._files = files

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("module_id", "MÓDULO"),
            Column("path", "RUTA"),
            Column("size", "TAMAÑO"),
            Column("modified", "MODIFICADO"),
            Column("mime_type", "TIPO", table=False),
            Column("url", "URL", table=False),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return [
            (
                item.module_id,
                item.path,
                _size_value(item.file.size),
                item.file.modified,
                item.file.mime_type,
                item.file.url,
            )
            for item in self._files
        ]

    @property
    def single_row(self) -> bool:
        return False


class DownloadsTable(Table):
    def __init__(self, results: Sequence[DownloadResult]) -> None:
        self._results = results

    @property
    def columns(self) -> Sequence[Column]:
        return [
            Column("status", "ESTADO"),
            Column("module_id", "MÓDULO"),
            Column("path", "RUTA"),
            Column("size", "TAMAÑO"),
            Column("error", "DETALLE"),
        ]

    @property
    def rows(self) -> Sequence[Sequence[object]]:
        return [
            (
                RichValue(
                    raw=result.status,
                    text=_STATUS_LABELS[result.status],
                    csv_text=result.status,
                ),
                result.file.module_id,
                result.file.path,
                _size_value(result.file.file.size),
                result.error,
            )
            for result in self._results
        ]

    @property
    def single_row(self) -> bool:
        return False
