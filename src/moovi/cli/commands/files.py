"""Comandos para listar y descargar archivos de un curso."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from moovi.cli.context import Services
from moovi.cli.formats.base import Formatter
from moovi.cli.tables import DownloadsTable, FilesTable
from moovi.domain.models import CourseFile, DownloadResult
from moovi.infra.file_store import LocalFileStore


def register(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    files = subparsers.add_parser(
        "files",
        parents=[common],
        help="Listar los archivos y carpetas descargables de un curso",
    )
    _add_selection(files)
    files.set_defaults(handler=_files)

    download = subparsers.add_parser(
        "download",
        parents=[common],
        help="Descargar los archivos y carpetas de un curso",
    )
    _add_selection(download)
    download.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directorio de destino (por defecto, moovi-COURSE_ID)",
    )
    download.add_argument(
        "--overwrite",
        action="store_true",
        help="Reemplazar los archivos locales que sean distintos",
    )
    download.set_defaults(handler=_download)


def _add_selection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("course_id", type=int, metavar="COURSE_ID")
    parser.add_argument(
        "module_ids",
        type=int,
        nargs="*",
        metavar="MODULE_ID",
        help="Limitar a estos módulos (recursos o carpetas)",
    )


def _files(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    formatter.render(FilesTable(_selected(args, services)))
    return 0


def _download(
    args: argparse.Namespace, services: Services, formatter: Formatter
) -> int:
    files = _selected(args, services)
    store = LocalFileStore(args.output or Path(f"moovi-{args.course_id}"))
    results: list[DownloadResult] = []
    for result in services.files.iter_download(
        files, store, overwrite=args.overwrite
    ):
        results.append(result)
        _report_progress(result, len(results), len(files))
    formatter.render(DownloadsTable(results))
    return 1 if any(r.status in {"conflict", "failed"} for r in results) else 0


def _selected(args: argparse.Namespace, services: Services) -> list[CourseFile]:
    files = services.files.list_files(args.course_id, args.module_ids)
    limit = getattr(args, "limit", None)
    return files[:limit] if limit else files


def _report_progress(result: DownloadResult, current: int, total: int) -> None:
    if sys.stderr.isatty():
        sys.stderr.write(f"[{current}/{total}] {result.file.path}\n")
