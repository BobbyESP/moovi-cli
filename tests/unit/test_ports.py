from moovi.infra.token_store import FileTokenStore
from moovi.logic.ports import MoodleGateway, TokenStore
from moovi.network.rest import MoodleRestClient


def test_moodle_rest_client_is_the_gateway_adapter() -> None:
    assert MoodleGateway in MoodleRestClient.__mro__


def test_file_token_store_is_the_token_store_adapter() -> None:
    assert TokenStore in FileTokenStore.__mro__
