"""Tests end-to-end de la CLI contra un Moodle falso local."""

from __future__ import annotations

import csv
import io
import json
import os
import stat
from pathlib import Path


def token_path(tmp_path: Path) -> Path:
    return tmp_path / "cache" / "moovi" / "token.json"


def test_login_reads_dotenv_and_stores_token(
    run_cli, tmp_path, fake_moodle
) -> None:
    (tmp_path / ".env").write_text(
        f"MOOVI_URL={fake_moodle.url}\n"
        "MOOVI_USER=profesor\n"
        "MOOVI_PASSWORD=secreto\n",
        encoding="utf-8",
    )

    result = run_cli("login")

    assert result.returncode == 0, result.stderr
    assert "Profesor de Prueba" in result.stdout
    path = token_path(tmp_path)
    assert path.exists()
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert json.loads(path.read_text(encoding="utf-8"))["token"] == "test-token"


def test_courses_json(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("courses", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert [course["short_name"] for course in data] == ["M1", "M2"]
    assert data[0]["full_name"] == "Matemáticas I"


def test_courses_table_and_limit(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("courses", "--limit", "1", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert "M1" in result.stdout
    assert "M2" not in result.stdout
    assert "SHORTNAME" in result.stdout


def test_invalid_credentials_exit_code(run_cli, credentials) -> None:
    wrong = {**credentials, "MOOVI_PASSWORD": "mal"}

    result = run_cli("login", extra_env=wrong)

    assert result.returncode == 2
    assert "Credenciales" in result.stderr


def test_json_error_is_emitted_on_stderr(run_cli, credentials) -> None:
    wrong = {**credentials, "MOOVI_PASSWORD": "mal"}

    result = run_cli("login", "--json", extra_env=wrong)

    assert result.returncode == 2
    payload = json.loads(result.stderr)
    assert payload["error"]["type"] == "InvalidCredentialsError"


def test_token_is_not_leaked(run_cli, credentials, fake_moodle) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("whoami", "--json", extra_env=credentials)

    combined = result.stdout + result.stderr
    assert fake_moodle.valid_token not in combined


def test_retries_after_invalid_token(run_cli, credentials, fake_moodle) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0
    fake_moodle.invalid_token_once = True

    result = run_cli("whoami", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert fake_moodle.count("/login/token.php") == 2


def test_students_hide_email_by_default(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("students", "101", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    participants = json.loads(result.stdout)
    ana = next(item for item in participants if item["full_name"] == "Ana Alumna")
    assert ana["email"] is None
    assert ana["roles"] == [{"id": 5, "short_name": "student", "name": ""}]


def test_students_can_include_email(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "students", "101", "--emails", "--json", extra_env=credentials
    )

    assert result.returncode == 0, result.stderr
    participants = json.loads(result.stdout)
    ana = next(item for item in participants if item["full_name"] == "Ana Alumna")
    assert ana["email"] == "ana@uvigo.gal"


def test_students_table_shows_role_labels(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("students", "101", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert "Alumno/a" in result.stdout
    assert "Profesor/a" in result.stdout


def test_permission_error_exit_code(run_cli, credentials, fake_moodle) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0
    fake_moodle.forbidden.add("core_enrol_get_enrolled_users")

    result = run_cli("students", "101", extra_env=credentials)

    assert result.returncode == 4
    assert "denegado" in result.stderr.lower()


def test_contents_human_output(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("contents", "101", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert "Tema 1" in result.stdout
    assert "Foro de avisos" in result.stdout
    assert "(oculta)" in result.stdout


def test_assignments_json(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("assignments", "101", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    [assignment] = json.loads(result.stdout)
    assert assignment["name"] == "Práctica 1"
    assert assignment["max_grade"] == 100.0


def test_courses_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("courses", "--format", "raw", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == ["id", "short_name", "full_name", "visible", "start_date"]
    assert rows[1][1] == "M1"
    assert rows[2][1] == "M2"
    assert rows[2][3] == "false"


def test_students_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("students", "101", "--format", "raw", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == ["id", "full_name", "roles", "last_access", "email"]
    ana = next(row for row in rows if row[1] == "Ana Alumna")
    assert ana[2] == "student"
    assert ana[4] == ""


def test_contents_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("contents", "101", "--format", "raw", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == [
        "section_id",
        "section_name",
        "module_id",
        "module_name",
        "mod_name",
        "visible",
        "url",
    ]
    assert any(row[4] == "forum" for row in rows[1:])


def test_assignments_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("assignments", "101", "--format", "raw", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == [
        "id",
        "course_id",
        "name",
        "due_date",
        "cutoff_date",
        "max_grade",
    ]
    assert rows[1][2] == "Práctica 1"


def test_format_json_is_an_alias(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("courses", "--format", "json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["short_name"] == "M1"


def test_json_and_raw_format_conflict(run_cli, credentials) -> None:
    result = run_cli(
        "courses", "--json", "--format", "raw", extra_env=credentials
    )

    assert result.returncode == 2
    assert "no pueden contradecirse" in result.stderr


def test_login_without_force_reuses_token(run_cli, credentials, fake_moodle) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0
    assert run_cli("login", extra_env=credentials).returncode == 0

    assert fake_moodle.count("/login/token.php") == 1


def test_login_force_reauthenticates(run_cli, credentials, fake_moodle) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("login", "--force", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert fake_moodle.count("/login/token.php") == 2
