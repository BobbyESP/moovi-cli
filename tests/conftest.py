"""Fixtures compartidas: servidor Moodle falso y datos de ejemplo."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs

import pytest

SITE_INFO: dict[str, Any] = {
    "sitename": "Moovi UVigo",
    "username": "profesor",
    "fullname": "Profesor de Prueba",
    "userid": 42,
    "release": "4.5 (Build: 20241007)",
    "functions": [
        {"name": "core_webservice_get_site_info", "version": "4.5"},
        {"name": "core_enrol_get_users_courses", "version": "4.5"},
    ],
}

COURSES: list[dict[str, Any]] = [
    {
        "id": 101,
        "shortname": "M1",
        "fullname": "Matemáticas I",
        "visible": 1,
        "startdate": 1704067200,
    },
    {
        "id": 102,
        "shortname": "M2",
        "fullname": "Matemáticas II",
        "visible": 0,
        "startdate": 0,
    },
]

CONTENTS: list[dict[str, Any]] = [
    {
        "id": 1,
        "name": "Tema 1",
        "summary": "<p>Introducción</p>",
        "modules": [
            {
                "id": 11,
                "name": "Foro de avisos",
                "modname": "forum",
                "visible": 1,
                "url": "https://moovi.uvigo.gal/mod/forum/view.php?id=11",
            },
            {
                "id": 12,
                "name": "Apuntes",
                "modname": "resource",
                "visible": 0,
            },
        ],
    }
]

PARTICIPANTS: list[dict[str, Any]] = [
    {
        "id": 7,
        "firstname": "Ana",
        "lastname": "Alumna",
        "fullname": "Ana Alumna",
        "groups": [
            {"id": 146, "name": "PROII_1 (Laboratorio)"},
            {"id": 147, "name": "MODALIDAD_GLOBAL"},
        ],
        "roles": [
            {"roleid": 5, "name": "", "shortname": "student", "sortorder": 0}
        ],
        "lastcourseaccess": 1700000000,
        "email": "ana@uvigo.gal",
    },
    {
        "id": 8,
        "firstname": "Profesor",
        "lastname": "Uno",
        "fullname": "Profesor Uno",
        "groups": [{"id": 150, "name": "PROII_A (Teoría)"}],
        "roles": [
            {
                "roleid": 3,
                "name": "",
                "shortname": "editingteacher",
                "sortorder": 0,
            }
        ],
        "lastcourseaccess": 1700000001,
        "email": "profesor@uvigo.gal",
    },
    {
        "id": 9,
        "firstname": "Sin",
        "lastname": "Grupo",
        "fullname": "Sin Grupo",
        "groups": [],
        "roles": [
            {"roleid": 5, "name": "", "shortname": "student", "sortorder": 0}
        ],
        "lastcourseaccess": 0,
        "email": "singrupo@uvigo.gal",
    },
]

ASSIGNMENTS: dict[str, Any] = {
    "courses": [
        {
            "id": 101,
            "assignments": [
                {
                    "id": 501,
                    "name": "Práctica 1",
                    "duedate": 1704067200,
                    "cutoffdate": 0,
                    "grade": 100,
                }
            ],
        }
    ]
}

FORUMS: list[dict[str, Any]] = [
    {
        "id": 2217,
        "course": 101,
        "name": "Foro de novas",
        "type": "news",
        "forcesubscribe": 1,
    },
    {
        "id": 2218,
        "course": 101,
        "name": "Foro xeral",
        "type": "general",
        "forcesubscribe": 0,
    },
]

ANNOUNCEMENTS: dict[str, Any] = {
    "discussions": [
        {
            "id": 9001,
            "name": "Aviso importante",
            "userfullname": "Profesor Uno",
            "created": 1704067200,
            "numreplies": 0,
            "pinned": False,
            "locked": False,
        },
        {
            "id": 9002,
            "name": "Segundo aviso",
            "userfullname": "Profesor Uno",
            "created": 1704153600,
            "numreplies": 2,
            "pinned": True,
            "locked": False,
        },
    ],
    "warnings": [],
}


class FakeMoodle:
    def __init__(self) -> None:
        self.valid_token = "test-token"
        self.username = "profesor"
        self.password = "secreto"
        self.invalid_token_once = False
        self.forbidden: set[str] = set()
        self.server_errors: set[str] = set()
        self.forums: list[dict[str, Any]] = list(FORUMS)
        self.announcements: dict[str, Any] = ANNOUNCEMENTS
        self.requests: list[tuple[str, dict[str, str]]] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        assert self._server is not None
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> None:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: object) -> None:
                pass

            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8")
                params = {key: values[0] for key, values in parse_qs(body).items()}
                outer.requests.append((self.path, params))
                if self.path == "/login/token.php":
                    outer._login(self, params)
                elif self.path == "/webservice/rest/server.php":
                    outer._webservice(self, params)
                else:
                    outer._send(self, 404, {"error": "not found"})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def count(self, path: str) -> int:
        return sum(1 for requested, _ in self.requests if requested == path)

    def _login(
        self, handler: BaseHTTPRequestHandler, params: dict[str, str]
    ) -> None:
        if (
            params.get("username") == self.username
            and params.get("password") == self.password
        ):
            self._send(handler, 200, {"token": self.valid_token})
        else:
            self._send(
                handler,
                200,
                {"error": "Invalid login, please try again", "errorcode": "invalidlogin"},
            )

    def _webservice(
        self, handler: BaseHTTPRequestHandler, params: dict[str, str]
    ) -> None:
        if params.get("wstoken") != self.valid_token:
            self._send(
                handler,
                200,
                {
                    "exception": "moodle_exception",
                    "errorcode": "invalidtoken",
                    "message": "Invalid token",
                },
            )
            return

        if self.invalid_token_once:
            self.invalid_token_once = False
            self._send(
                handler,
                200,
                {
                    "exception": "moodle_exception",
                    "errorcode": "invalidtoken",
                    "message": "Invalid token",
                },
            )
            return

        function = params.get("wsfunction", "")
        if function in self.forbidden:
            self._send(
                handler,
                200,
                {
                    "exception": "webservice_access_exception",
                    "errorcode": "accessexception",
                    "message": "Access control exception",
                },
            )
            return
        if function in self.server_errors:
            self._send(handler, 500, {"error": "boom"})
            return

        responses: dict[str, object] = {
            "core_webservice_get_site_info": SITE_INFO,
            "core_enrol_get_users_courses": COURSES,
            "core_course_get_contents": CONTENTS,
            "core_enrol_get_enrolled_users": PARTICIPANTS,
            "mod_assign_get_assignments": ASSIGNMENTS,
            "mod_forum_get_forums_by_courses": self.forums,
            "mod_forum_get_forum_discussions": self.announcements,
        }
        if function not in responses:
            self._send(
                handler,
                200,
                {
                    "exception": "moodle_exception",
                    "errorcode": "invalidfunction",
                    "message": function,
                },
            )
            return
        self._send(handler, 200, responses[function])

    @staticmethod
    def _send(
        handler: BaseHTTPRequestHandler, status: int, payload: object
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)


@pytest.fixture
def fake_moodle() -> FakeMoodle:
    server = FakeMoodle()
    server.start()
    try:
        yield server
    finally:
        server.stop()
