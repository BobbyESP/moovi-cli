import pytest

from moovi.domain.errors import ApiError, InvalidTokenError, NetworkError
from moovi.domain.values import Token
from moovi.network.mappers import map_sections
from moovi.network.rest import MoodleRestClient

TOKEN = Token("test-token")


def test_open_file_streams_content(fake_moodle) -> None:
    fake_moodle.files["a.pdf"] = b"contenido"
    client = MoodleRestClient(fake_moodle.url)

    with client.open_file(TOKEN, fake_moodle.file_url("a.pdf")) as stream:
        assert stream.read() == b"contenido"


def test_token_travels_in_body_not_in_url(fake_moodle) -> None:
    fake_moodle.files["a.pdf"] = b"x"
    client = MoodleRestClient(fake_moodle.url)

    with client.open_file(TOKEN, fake_moodle.file_url("a.pdf")) as stream:
        stream.read()

    path, params = fake_moodle.requests[-1]
    assert TOKEN.value not in path
    assert params["token"] == TOKEN.value


def test_json_error_with_http_200_is_mapped(fake_moodle) -> None:
    fake_moodle.files["a.pdf"] = b"x"
    client = MoodleRestClient(fake_moodle.url)

    with pytest.raises(InvalidTokenError):
        client.open_file(Token("caducado"), fake_moodle.file_url("a.pdf"))


def test_missing_file_is_a_network_error(fake_moodle) -> None:
    client = MoodleRestClient(fake_moodle.url)

    with pytest.raises(NetworkError):
        client.open_file(TOKEN, fake_moodle.file_url("no.pdf"))


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/webservice/pluginfile.php/1/a.pdf",
        "{base}/login/token.php",
        "{base}.evil.example/webservice/pluginfile.php/1/a.pdf",
    ],
)
def test_token_is_never_sent_to_foreign_urls(fake_moodle, url: str) -> None:
    client = MoodleRestClient(fake_moodle.url)

    with pytest.raises(ApiError):
        client.open_file(TOKEN, url.format(base=fake_moodle.url))

    assert fake_moodle.requests == []


def test_mapper_keeps_only_real_files() -> None:
    [section] = map_sections(
        [
            {
                "id": 1,
                "name": "Tema",
                "modules": [
                    {
                        "id": 2,
                        "name": "Carpeta",
                        "modname": "folder",
                        "contents": [
                            {
                                "type": "file",
                                "filename": "a.pdf",
                                "filepath": "/sub/dir/",
                                "filesize": 12,
                                "fileurl": "https://m/a.pdf",
                                "timemodified": 1704067200,
                                "mimetype": "application/pdf",
                            },
                            {"type": "url", "filename": "x", "fileurl": "https://x"},
                            {"type": "content", "filename": "structure"},
                        ],
                    }
                ],
            }
        ]
    )

    [remote] = section.modules[0].files
    assert (remote.name, remote.folder, remote.size) == ("a.pdf", "sub/dir", 12)
    assert remote.mime_type == "application/pdf"
