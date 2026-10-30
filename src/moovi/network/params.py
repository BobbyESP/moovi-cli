"""Conversión de parámetros al formato que espera Moodle (``a[b][0][c]``)."""

from __future__ import annotations

from collections.abc import Mapping


def flatten_params(
    params: Mapping[str, object], prefix: str = ""
) -> dict[str, str]:
    flat: dict[str, str] = {}
    for key, value in params.items():
        full_key = f"{prefix}[{key}]" if prefix else str(key)
        if isinstance(value, Mapping):
            flat.update(flatten_params(value, full_key))
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                indexed_key = f"{full_key}[{index}]"
                if isinstance(item, Mapping):
                    flat.update(flatten_params(item, indexed_key))
                elif item is not None:
                    flat[indexed_key] = _scalar(item)
        elif value is not None:
            flat[full_key] = _scalar(value)
    return flat


def _scalar(value: object) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
