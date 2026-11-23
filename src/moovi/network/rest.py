"""Adaptador REST de Moodle.

Implementa el puerto de salida ``MoodleGateway``. No conoce la CLI, la
configuración ni la caché de tokens: recibe el token en cada llamada.
"""

from __future__ import annotations

import io
import json
import time
from collections.abc import Callable, Mapping, Sequence
from http.client import HTTPException
from types import TracebackType
from typing import Any, Self
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from moovi.domain.errors import (
    ApiError,
    NetworkError,
    ReadOnlyViolation,
)
from moovi.domain.models import (
    Announcement,
    AnnouncementContent,
    Assignment,
    Course,
    Forum,
    Participant,
    Section,
    SiteInfo,
)
from moovi.domain.values import Token
from moovi.logic.ports import MoodleGateway
from moovi.network.errors import raise_for_moodle_error
from moovi.network.mappers import (
    map_announcement_content,
    map_announcements,
    map_assignments,
    map_courses,
    map_forums,
    map_participants,
    map_sections,
    map_site_info,
)
from moovi.network.params import flatten_params

_RETRY_DELAY_SECONDS = 0.2
_FILE_ENDPOINT = "/webservice/pluginfile.php/"
_FILE_BUFFER_BYTES = 64 * 1024

# Único punto donde se declara qué se puede llamar. Si añades una función,
# añádela aquí y crea su comando correspondiente.
READ_ONLY_FUNCTIONS = frozenset(
    {
        "core_webservice_get_site_info",
        "core_enrol_get_users_courses",
        "core_course_get_contents",
        "core_enrol_get_enrolled_users",
        "mod_assign_get_assignments",
        "mod_forum_get_forums_by_courses",
        "mod_forum_get_forum_discussions",
        "mod_forum_get_discussion_post",
    }
)


class MoodleRestClient(MoodleGateway):
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
        with self._open(request) as response:
            return response.read().decode("utf-8")

    def _open(self, request: Request) -> Any:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                return self._opener(request, timeout=self._timeout)
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

    def course_forums(self, token: Token, course_id: int) -> list[Forum]:
        data = self.call(
            token,
            "mod_forum_get_forums_by_courses",
            courseids=[course_id],
        )
        return map_forums(data)

    def forum_discussions(
        self, token: Token, forum_id: int, limit: int
    ) -> list[Announcement]:
        data = self.call(
            token,
            "mod_forum_get_forum_discussions",
            forumid=forum_id,
            sortorder=-1,
            page=0,
            perpage=limit,
        )
        return map_announcements(data)

    def discussion_post(
        self, token: Token, post_id: int
    ) -> AnnouncementContent:
        data = self.call(
            token,
            "mod_forum_get_discussion_post",
            postid=post_id,
        )
        return map_announcement_content(data)

    def open_file(self, token: Token, url: str) -> _RemoteStream:
        self._require_file_url(url)
        # El token va en el cuerpo: así no aparece en URLs, logs ni redirecciones.
        request = Request(
            url,
            data=urlencode({"token": token.value}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self._open(request)
        reader = io.BufferedReader(response, buffer_size=_FILE_BUFFER_BYTES)
        try:
            _raise_for_file_error(reader, response.headers.get("Content-Type", ""))
        except BaseException:
            reader.close()
            raise
        return _RemoteStream(reader)

    def _require_file_url(self, url: str) -> None:
        """Impide enviar el token a un destino que no sea este Moodle."""

        base = urlsplit(self._base_url)
        target = urlsplit(url)
        if (
            target.scheme != base.scheme
            or target.netloc != base.netloc
            or not target.path.startswith(base.path + _FILE_ENDPOINT)
        ):
            raise ApiError(
                "invalidfileurl", "La URL del archivo no pertenece a Moovi."
            )


class _RemoteStream:
    """Flujo de un fichero remoto que traduce los fallos a errores de dominio."""

    def __init__(self, reader: io.BufferedReader) -> None:
        self._reader = reader

    def read(self, size: int = -1, /) -> bytes:
        try:
            return self._reader.read(size)
        except (HTTPException, OSError) as exc:
            raise NetworkError(f"Se interrumpió la descarga: {exc}") from exc

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._reader.close()


def _raise_for_file_error(reader: io.BufferedReader, content_type: str) -> None:
    """Moodle puede responder HTTP 200 con un error JSON en lugar del fichero."""

    if "json" not in content_type.lower():
        return
    try:
        payload = json.loads(reader.peek(_FILE_BUFFER_BYTES))
    except ValueError:
        return
    if isinstance(payload, Mapping):
        raise_for_moodle_error(payload)


def _as_mapping(data: object) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ApiError("invalidresponse", "Moovi devolvió una respuesta inesperada.")
    return data
