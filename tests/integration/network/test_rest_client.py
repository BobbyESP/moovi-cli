import pytest

from moovi.domain.errors import (
    AuthorizationError,
    InvalidCredentialsError,
    InvalidTokenError,
    NetworkError,
    ReadOnlyViolation,
)
from moovi.domain.values import Token
from moovi.network.rest import MoodleRestClient


def client(fake_moodle) -> MoodleRestClient:
    return MoodleRestClient(fake_moodle.url)


def test_login_success(fake_moodle) -> None:
    token = client(fake_moodle).login("profesor", "secreto")

    assert token.value == "test-token"


def test_login_failure(fake_moodle) -> None:
    with pytest.raises(InvalidCredentialsError):
        client(fake_moodle).login("profesor", "mal")


def test_site_info(fake_moodle) -> None:
    info = client(fake_moodle).site_info(Token("test-token"))

    assert info.user_id == 42
    assert info.functions[0] == "core_webservice_get_site_info"


def test_invalid_token_is_mapped(fake_moodle) -> None:
    with pytest.raises(InvalidTokenError):
        client(fake_moodle).site_info(Token("caducado"))


def test_permission_error_is_mapped(fake_moodle) -> None:
    fake_moodle.forbidden.add("core_enrol_get_enrolled_users")

    with pytest.raises(AuthorizationError):
        client(fake_moodle).enrolled_users(Token("test-token"), 101)


def test_read_only_allowlist_rejects_other_functions(fake_moodle) -> None:
    with pytest.raises(ReadOnlyViolation):
        client(fake_moodle).call(
            Token("test-token"), "core_course_delete_courses", courseids=[101]
        )


def test_http_500_becomes_network_error(fake_moodle) -> None:
    fake_moodle.server_errors.add("core_webservice_get_site_info")

    with pytest.raises(NetworkError):
        client(fake_moodle).site_info(Token("test-token"))

    # Un reintento además del intento inicial.
    assert fake_moodle.count("/webservice/rest/server.php") == 2


def test_nested_params_use_moodle_notation(fake_moodle) -> None:
    client(fake_moodle).assignments(Token("test-token"), [101])

    _, params = fake_moodle.requests[-1]
    assert params["courseids[0]"] == "101"
    assert params["wsfunction"] == "mod_assign_get_assignments"
    assert params["moodlewsrestformat"] == "json"


def test_course_forums(fake_moodle) -> None:
    forums = client(fake_moodle).course_forums(Token("test-token"), 101)

    assert forums[0].type == "news"
    assert forums[0].force_subscribe is True
    _, params = fake_moodle.requests[-1]
    assert params["courseids[0]"] == "101"


def test_forum_discussions(fake_moodle) -> None:
    announcements = client(fake_moodle).forum_discussions(
        Token("test-token"), 2217, 3
    )

    assert announcements[0].subject == "Aviso importante"
    _, params = fake_moodle.requests[-1]
    assert params["forumid"] == "2217"
    assert params["sortorder"] == "-1"
    assert params["page"] == "0"
    assert params["perpage"] == "3"
