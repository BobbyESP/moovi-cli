import json
import os
import stat
from pathlib import Path

from moovi.domain.values import Token
from moovi.infra.token_store import FileTokenStore

SITE = "https://moovi.uvigo.gal"
USER = "profesor"


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    store = FileTokenStore(tmp_path / "cache" / "token.json")

    store.save(SITE, USER, Token("abc123"))

    loaded = store.load(SITE, USER)
    assert loaded is not None
    assert loaded.value == "abc123"


def test_file_permissions_are_0600(tmp_path: Path) -> None:
    path = tmp_path / "cache" / "token.json"
    store = FileTokenStore(path)

    store.save(SITE, USER, Token("abc123"))

    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600


def test_file_does_not_contain_password(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    FileTokenStore(path).save(SITE, USER, Token("abc123"))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"site": SITE, "username": USER, "token": "abc123"}


def test_load_rejects_other_site_or_user(tmp_path: Path) -> None:
    store = FileTokenStore(tmp_path / "token.json")
    store.save(SITE, USER, Token("abc123"))

    assert store.load("https://otro.example", USER) is None
    assert store.load(SITE, "otra") is None


def test_corrupt_cache_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    path.write_text("no es json", encoding="utf-8")

    assert FileTokenStore(path).load(SITE, USER) is None


def test_clear_removes_only_matching_token(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    store = FileTokenStore(path)
    store.save(SITE, USER, Token("abc123"))

    store.clear(SITE, "otra")
    assert path.exists()

    store.clear(SITE, USER)
    assert not path.exists()
