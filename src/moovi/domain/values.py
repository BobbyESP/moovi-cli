"""Value objects del dominio."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Token:
    """Token de la API de Moodle.

    Su representación textual está redactada a propósito: así no se filtra en
    logs, trazas ni mensajes de error.
    """

    value: str = field(repr=False)

    def __repr__(self) -> str:
        return "Token(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"
