"""Tests end-to-end de `moovi files` y `moovi download`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def course_files(fake_moodle) -> None:
    fake_moodle.files = {"a.pdf": b"contenido", "b.txt": b"otro"}
    entry = {"type": "file", "timemodified": 1704067200, "filepath": "/"}
    fake_moodle.contents = [
        {
            "id": 1,
            "name": "Tema 1",
            "summary": "",
            "modules": [
                {
                    "id": 21,
                    "name": "Apuntes",
                    "modname": "resource",
                    "visible": 1,
                    "contents": [
                        {
                            **entry,
                            "filename": "a.pdf",
                            "filesize": 9,
                            "fileurl": fake_moodle.file_url("a.pdf"),
                        }
                    ],
                },
                {
                    "id": 22,
                    "name": "Material",
                    "modname": "folder",
                    "visible": 1,
                    "contents": [
                        {
                            **entry,
                            "filepath": "/sub/",
                            "filename": "b.txt",
                            "filesize": 4,
                            "fileurl": fake_moodle.file_url("b.txt"),
                        }
                    ],
                },
            ],
        }
    ]


def login(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0


def test_files_lists_paths(run_cli, credentials, course_files) -> None:
    login(run_cli, credentials)

    result = run_cli("files", "101", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert [item["path"] for item in json.loads(result.stdout)] == [
        "Tema 1/a.pdf",
        "Tema 1/Material/sub/b.txt",
    ]


def test_download_course_then_skip(
    run_cli, credentials, course_files, tmp_path: Path, fake_moodle
) -> None:
    login(run_cli, credentials)

    first = run_cli("download", "101", "-o", "out", "--json", extra_env=credentials)
    second = run_cli("download", "101", "-o", "out", "--json", extra_env=credentials)

    assert first.returncode == 0, first.stderr
    assert {item["status"] for item in json.loads(first.stdout)} == {"downloaded"}
    assert {item["status"] for item in json.loads(second.stdout)} == {"skipped"}
    assert (tmp_path / "out/Tema 1/a.pdf").read_bytes() == b"contenido"
    assert (tmp_path / "out/Tema 1/Material/sub/b.txt").read_bytes() == b"otro"
    assert fake_moodle.valid_token not in first.stdout + first.stderr


def test_download_single_module_uses_default_folder(
    run_cli, credentials, course_files, tmp_path: Path
) -> None:
    login(run_cli, credentials)

    result = run_cli("download", "101", "22", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "moovi-101/Tema 1/Material/sub/b.txt").exists()
    assert not (tmp_path / "moovi-101/Tema 1/a.pdf").exists()


def test_conflict_exits_1_until_overwrite(
    run_cli, credentials, course_files, tmp_path: Path
) -> None:
    login(run_cli, credentials)
    local = tmp_path / "out/Tema 1/a.pdf"
    local.parent.mkdir(parents=True)
    local.write_bytes(b"editado por mi")

    conflict = run_cli("download", "101", "21", "-o", "out", extra_env=credentials)
    assert conflict.returncode == 1
    assert local.read_bytes() == b"editado por mi"

    replaced = run_cli(
        "download", "101", "21", "-o", "out", "--overwrite", extra_env=credentials
    )
    assert replaced.returncode == 0, replaced.stderr
    assert local.read_bytes() == b"contenido"


def test_unknown_module_exits_2(run_cli, credentials, course_files) -> None:
    login(run_cli, credentials)

    result = run_cli("download", "101", "999", extra_env=credentials)

    assert result.returncode == 2
    assert "999" in result.stderr


def test_renews_token_during_download(
    run_cli, credentials, course_files, fake_moodle, tmp_path: Path
) -> None:
    login(run_cli, credentials)
    contents = run_cli("files", "101", "--json", extra_env=credentials)
    assert contents.returncode == 0
    fake_moodle.valid_token = "token-nuevo"

    result = run_cli("download", "101", "21", "-o", "out", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out/Tema 1/a.pdf").exists()
