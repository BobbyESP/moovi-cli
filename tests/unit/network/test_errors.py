import pytest

from moovi.domain.errors import (
    ApiError,
    AuthorizationError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from moovi.network.errors import raise_for_moodle_error


def test_ignores_success_payloads() -> None:
    raise_for_moodle_error({"userid": 42})
    raise_for_moodle_error({})


def test_maps_invalid_login() -> None:
    with pytest.raises(InvalidCredentialsError, match="Credenciales"):
        raise_for_moodle_error({"errorcode": "invalidlogin", "error": "nope"})


def test_maps_invalid_token() -> None:
    with pytest.raises(InvalidTokenError):
        raise_for_moodle_error({"errorcode": "invalidtoken"})


@pytest.mark.parametrize(
    "code",
    [
        "accessexception",
        "nopermissions",
        "required_capability_exception",
        "webservice_access_exception",
    ],
)
def test_maps_permission_errors(code: str) -> None:
    with pytest.raises(AuthorizationError):
        raise_for_moodle_error({"errorcode": code, "message": "denied"})


def test_maps_other_errors_to_api_error() -> None:
    with pytest.raises(ApiError) as excinfo:
        raise_for_moodle_error({"errorcode": "invalidparameter", "message": "bad"})

    assert excinfo.value.code == "invalidparameter"
    assert "bad" in str(excinfo.value)


def test_treats_exception_without_errorcode_as_api_error() -> None:
    with pytest.raises(ApiError):
        raise_for_moodle_error({"exception": "moodle_exception"})
