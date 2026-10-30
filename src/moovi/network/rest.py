"""Cliente REST de Moodle.

Implementa el puerto ``MoodleGateway``. No conoce la CLI, la configuración ni
la caché de tokens: recibe el token en cada llamada.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from moovi.domain.errors import (
    ApiError,
    NetworkError,
    ReadOnlyViolation,
)
from moovi.domain.models import (
    Assignment,
    Course,
    Participant,
    Section,
    SiteInfo,
)
from moovi.domain.values import Token
from moovi.network.errors import raise_for_moodle_error
from moovi.network.mappers import (
    map_assignments,
    map_courses,
    map_participants,
    map_sections,
    map_site_info,
)
from moovi.network.params import flatten_params

_RETRY_DELAY_SECONDS = 0.2

# Único punto donde se declara qué se puede llamar. Si añades una función,
# añádela aquí y crea su comando correspondiente.
READ_ONLY_FUNCTIONS = frozenset(
    {
        "core_webservice_get_site_info",
        "core_enrol_get_users_courses",
        "core_course_get_contents",
        "core_enrol_get_enrolled_users",
        "mod_assign_get_assignments",
    }
)


class MoodleRestClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._opener = opener or urlopen

    def login(self, username: str, password: str) -> Token:
        payload = {
            "username": username,
            "password": password,
            "service": "moodle_mobile_app",
        }
        data = self._post("/login/token.php", payload)
        if not isinstance(data, Mapping):
            raise ApiError(
                "invalidresponse", "Moovi devolvió una respuesta inesperada al iniciar sesión."
            )
        raise_for_moodle_error(data)
        token = data.get("token")
        if not token:
            raise ApiError(
                "invalidresponse", "Moovi no devolvió ningún token al iniciar sesión."
            )
        return Token(str(token))

    def call(self, token: Token, function: str, /, **params: object) -> object:
        if function not in READ_ONLY_FUNCTIONS:
            raise ReadOnlyViolation(
                f"La función '{function}' no está permitida en modo de solo lectura."
            )
        payload: dict[str, str] = flatten_params(params)
        payload["wstoken"] = token.value
        payload["wsfunction"] = function
        payload["moodlewsrestformat"] = "json"
        data = self._post("/webservice/rest/server.php", payload)
        if isinstance(data, Mapping):
            raise_for_moodle_error(data)
        return data

    def _post(self, path: str, payload: Mapping[str, str]) -> object:
        body = urlencode(payload).encode("utf-8")
        request = Request(
            self._base_url + path,
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        raw = self._read(request)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ApiError(
                "invalidresponse", "Moovi devolvió una respuesta que no es JSON."
            ) from exc

    def _read(self, request: Request) -> str:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with self._opener(request, timeout=self._timeout) as response:
                    return response.read().decode("utf-8")
            except HTTPError as exc:
                last_error = exc
                if exc.code >= 500 and attempt == 0:
                    time.sleep(_RETRY_DELAY_SECONDS)
                    continue
                raise NetworkError(
                    f"Moovi respondió con HTTP {exc.code}."
                ) from exc
            except URLError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(_RETRY_DELAY_SECONDS)
                    continue
                raise NetworkError(
                    f"No se pudo conectar con Moovi: {exc.reason}"
                ) from exc
        raise NetworkError(f"No se pudo conectar con Moovi: {last_error}")

    def site_info(self, token: Token) -> SiteInfo:
        data = self.call(token, "core_webservice_get_site_info")
        return map_site_info(_as_mapping(data))

    def users_courses(self, token: Token, user_id: int) -> list[Course]:
        data = self.call(token, "core_enrol_get_users_courses", userid=user_id)
        return map_courses(data)

    def course_contents(self, token: Token, course_id: int) -> list[Section]:
        data = self.call(token, "core_course_get_contents", courseid=course_id)
        return map_sections(data)

    def enrolled_users(self, token: Token, course_id: int) -> list[Participant]:
        data = self.call(token, "core_enrol_get_enrolled_users", courseid=course_id)
        return map_participants(data)

    def assignments(
        self, token: Token, course_ids: Sequence[int]
    ) -> list[Assignment]:
        data = self.call(
            token, "mod_assign_get_assignments", courseids=list(course_ids)
        )
        return map_assignments(data)


def _as_mapping(data: object) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ApiError("invalidresponse", "Moovi devolvió una respuesta inesperada.")
    return data
