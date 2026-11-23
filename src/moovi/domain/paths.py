"""Nombres de fichero seguros a partir de datos remotos no confiables."""

from __future__ import annotations

_FORBIDDEN = frozenset('<>:"/\\|?*')
_RESERVED = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)
_MAX_NAME_LENGTH = 120
_MAX_EXTENSION_LENGTH = 20


def safe_name(name: str) -> str:
    """Convierte ``name`` en un único componente de ruta válido en cualquier SO."""

    cleaned = "".join(
        "_" if char in _FORBIDDEN or ord(char) < 32 or ord(char) == 127 else char
        for char in name
    )
    cleaned = cleaned.strip().rstrip(". ")
    if not cleaned:
        return "_"
    if cleaned.split(".", 1)[0].upper() in _RESERVED:
        cleaned = f"_{cleaned}"
    return _truncate(cleaned)


def safe_parts(path: str) -> list[str]:
    """Sanea cada componente de una ruta remota, descartando los vacíos."""

    return [
        safe_name(part)
        for part in path.replace("\\", "/").split("/")
        if part.strip()
    ]


def with_label(name: str, label: str) -> str:
    """Añade ``label`` antes de la extensión: ``a.pdf`` → ``a (label).pdf``."""

    stem, extension = _split_extension(name)
    return f"{stem} ({label}){extension}"


def _truncate(name: str) -> str:
    if len(name) <= _MAX_NAME_LENGTH:
        return name
    stem, extension = _split_extension(name)
    return stem[: _MAX_NAME_LENGTH - len(extension)].rstrip(". ") + extension


def _split_extension(name: str) -> tuple[str, str]:
    stem, dot, extension = name.rpartition(".")
    if not dot or not stem or len(extension) >= _MAX_EXTENSION_LENGTH:
        return name, ""
    return stem, f".{extension}"
