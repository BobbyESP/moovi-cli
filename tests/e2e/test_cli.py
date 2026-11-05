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


def test_participants_hide_email_by_default(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("participants", "101", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    participants = json.loads(result.stdout)
    ana = next(
        item
        for item in participants
        if item["first_name"] == "Ana" and item["last_name"] == "Alumna"
    )
    assert ana["full_name"] == "Ana Alumna"
    assert ana["email"] is None
    assert ana["groups"] == [
        {"id": 146, "name": "PROII_1 (Laboratorio)"},
        {"id": 147, "name": "MODALIDAD_GLOBAL"},
    ]
    assert ana["roles"] == [{"id": 5, "short_name": "student", "name": ""}]


def test_participants_without_groups_return_empty_list(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("participants", "101", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    participants = json.loads(result.stdout)
    sin_grupo = next(
        item for item in participants if item["full_name"] == "Sin Grupo"
    )
    assert sin_grupo["groups"] == []


def test_participants_can_include_email(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "participants", "101", "--emails", "--json", extra_env=credentials
    )

    assert result.returncode == 0, result.stderr
    participants = json.loads(result.stdout)
    ana = next(
        item
        for item in participants
        if item["first_name"] == "Ana" and item["last_name"] == "Alumna"
    )
    assert ana["email"] == "ana@uvigo.gal"


def test_participants_table_shows_role_labels(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("participants", "101", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert "NOMBRE" in result.stdout
    assert "APELLIDOS" in result.stdout
    assert "GRUPOS" in result.stdout
    assert "PROII_1 (Laboratorio); MODALIDAD_GLOBAL" in result.stdout
    assert "Alumno/a" in result.stdout
    assert "Profesor/a" in result.stdout


def test_permission_error_exit_code(run_cli, credentials, fake_moodle) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0
    fake_moodle.forbidden.add("core_enrol_get_enrolled_users")

    result = run_cli("participants", "101", extra_env=credentials)

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


def test_participants_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("participants", "101", "--format", "raw", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == [
        "id",
        "first_name",
        "last_name",
        "groups",
        "roles",
        "last_access",
        "email",
    ]
    ana = next(row for row in rows if row[1] == "Ana" and row[2] == "Alumna")
    assert ana[3] == "PROII_1 (Laboratorio);MODALIDAD_GLOBAL"
    assert ana[4] == "student"
    assert ana[6] == ""


def test_contents_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("contents", "101", "--format", "raw", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == [
        "section_id",
        "section_name",
        "summary_text",
        "modules",
    ]
    assert rows[1][3] == "forum:Foro de avisos:1;resource:Apuntes:0"


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


def test_announcement_content_json(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "announcement-content", "9001", "--json", extra_env=credentials
    )

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["subject"] == "Aviso importante"
    assert data["author"] == "Profesor Uno"
    assert data["discussion_id"] == 8001
    assert data["message_format"] == 1
    assert data["message"] == "<p>Hola, mundo</p><p>Segundo párrafo</p>"
    assert data["message_text"] == "Hola, mundo\nSegundo párrafo"


def test_announcement_content_table(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("announcement-content", "9001", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert "ASUNTO: Aviso importante" in result.stdout
    assert "AUTOR: Profesor Uno" in result.stdout
    assert "MENSAJE: Hola, mundo" in result.stdout
    assert "  Segundo párrafo" in result.stdout


def test_announcement_content_raw(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "announcement-content",
        "9001",
        "--format",
        "raw",
        extra_env=credentials,
    )

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == [
        "id",
        "discussion_id",
        "subject",
        "author",
        "created",
        "modified",
        "message_text",
    ]
    assert rows[1][6] == "Hola, mundo Segundo párrafo"


def test_announcement_content_invalid_id(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "announcement-content", "123", "--json", extra_env=credentials
    )

    assert result.returncode == 3
    payload = json.loads(result.stderr)
    assert payload["error"]["type"] == "ApiError"


def test_announcements_json(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("announcements", "101", "--json", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data[0]["subject"] == "Aviso importante"
    assert data[0]["author"] == "Profesor Uno"


def test_announcements_table(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("announcements", "101", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert "ASUNTO" in result.stdout
    assert "Aviso importante" in result.stdout
    assert "Profesor Uno" in result.stdout


def test_announcements_raw_csv(run_cli, credentials) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "announcements", "101", "--format", "raw", extra_env=credentials
    )

    assert result.returncode == 0, result.stderr
    rows = list(csv.reader(io.StringIO(result.stdout)))
    assert rows[0] == [
        "id",
        "created",
        "author",
        "subject",
        "num_replies",
        "pinned",
        "locked",
    ]
    assert rows[1][3] == "Aviso importante"


def test_announcements_limit_is_sent_to_the_api(
    run_cli, credentials, fake_moodle
) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "announcements", "101", "--limit", "1", "--json", extra_env=credentials
    )

    assert result.returncode == 0, result.stderr
    requests = [
        params
        for _, params in fake_moodle.requests
        if params.get("wsfunction") == "mod_forum_get_forum_discussions"
    ]
    assert requests[-1]["perpage"] == "1"


def test_announcements_ambiguity_lists_candidates(
    run_cli, credentials, fake_moodle
) -> None:
    fake_moodle.forums = [
        {
            "id": 2217,
            "course": 101,
            "name": "Foro de novas",
            "type": "news",
            "forcesubscribe": 1,
        },
        {
            "id": 2219,
            "course": 101,
            "name": "Avisos",
            "type": "news",
            "forcesubscribe": 1,
        },
    ]

    result = run_cli("announcements", "101", extra_env=credentials)

    assert result.returncode == 2
    assert "2217" in result.stderr
    assert "2219" in result.stderr
    assert "--forum-id" in result.stderr


def test_announcements_forum_id_resolves_ambiguity(
    run_cli, credentials, fake_moodle
) -> None:
    fake_moodle.forums = [
        {
            "id": 2217,
            "course": 101,
            "name": "Foro de novas",
            "type": "news",
            "forcesubscribe": 1,
        },
        {
            "id": 2219,
            "course": 101,
            "name": "Avisos",
            "type": "news",
            "forcesubscribe": 1,
        },
    ]

    result = run_cli(
        "announcements",
        "101",
        "--forum-id",
        "2219",
        "--json",
        extra_env=credentials,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["subject"] == "Aviso importante"


def test_announcements_without_news_forum_lists_available_forums(
    run_cli, credentials, fake_moodle
) -> None:
    fake_moodle.forums = [
        {
            "id": 2218,
            "course": 101,
            "name": "Foro xeral",
            "type": "general",
            "forcesubscribe": 0,
        }
    ]

    result = run_cli("announcements", "101", extra_env=credentials)

    assert result.returncode == 2
    assert "2218" in result.stderr
    assert "Foro xeral" in result.stderr
    assert "--forum-id" in result.stderr


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


def test_login_force_reauthenticates_with_no_input(
    run_cli, credentials, fake_moodle
) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("login", "--force", "--no-input", extra_env=credentials)

    assert result.returncode == 0, result.stderr
    assert fake_moodle.count("/login/token.php") == 2


def test_login_no_input_requires_credentials(run_cli, credentials) -> None:
    result = run_cli(
        "login", "--no-input", extra_env={"MOOVI_URL": credentials["MOOVI_URL"]}
    )

    assert result.returncode == 2
    assert "credenciales" in result.stderr.lower()


def test_commands_work_with_only_the_cached_token(
    run_cli, credentials, fake_moodle
) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli(
        "courses", "--json", extra_env={"MOOVI_URL": fake_moodle.url}
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["short_name"] == "M1"


def test_login_with_valid_token_does_not_prompt_without_tty(
    run_cli, credentials, fake_moodle
) -> None:
    assert run_cli("login", extra_env=credentials).returncode == 0

    result = run_cli("login", extra_env={"MOOVI_URL": fake_moodle.url})

    assert result.returncode == 0, result.stderr
    assert "terminal" not in result.stderr.lower()


def test_command_without_session_tells_to_login(run_cli, fake_moodle) -> None:
    result = run_cli("courses", extra_env={"MOOVI_URL": fake_moodle.url})

    assert result.returncode == 2
    assert "moovi login" in result.stderr


def test_login_force_without_tty_fails_cleanly(run_cli, fake_moodle) -> None:
    result = run_cli(
        "login", "--force", extra_env={"MOOVI_URL": fake_moodle.url}
    )

    assert result.returncode == 2
    assert "terminal" in result.stderr.lower()
