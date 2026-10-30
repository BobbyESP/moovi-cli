from moovi.domain.values import Token


def test_token_repr_and_str_are_redacted() -> None:
    token = Token("super-secret")

    assert token.value == "super-secret"
    assert "super-secret" not in repr(token)
    assert "super-secret" not in str(token)
    assert "redacted" in repr(token)
