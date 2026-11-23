import pytest

from moovi.domain.paths import safe_name, safe_parts, with_label


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Tema 1.pdf", "Tema 1.pdf"),
        ("a/b\\c.pdf", "a_b_c.pdf"),
        ("..", "_"),
        ("   ", "_"),
        ("nombre. ", "nombre"),
        ("CON", "_CON"),
        ("nul.txt", "_nul.txt"),
        ("a:b*c?.txt", "a_b_c_.txt"),
        ("línea\nnueva.txt", "línea_nueva.txt"),
    ],
)
def test_safe_name(raw: str, expected: str) -> None:
    assert safe_name(raw) == expected


def test_safe_name_truncates_and_keeps_extension() -> None:
    result = safe_name("a" * 300 + ".pdf")

    assert len(result) == 120
    assert result.endswith(".pdf")


def test_safe_parts_neutralizes_traversal() -> None:
    assert safe_parts("../../etc\\passwd") == ["_", "_", "etc", "passwd"]


def test_with_label_goes_before_extension() -> None:
    assert with_label("apuntes.pdf", "12") == "apuntes (12).pdf"
    assert with_label("LEEME", "12") == "LEEME (12)"
