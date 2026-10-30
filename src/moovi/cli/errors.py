"""Errores de presentación."""

from __future__ import annotations

import json
import sys
from typing import TextIO


def print_error(
    error: Exception, *, as_json: bool, stream: TextIO | None = None
) -> None:
    target = stream or sys.stderr
    if as_json:
        json.dump(
            {
                "error": {
                    "type": type(error).__name__,
                    "code": getattr(error, "code", None),
                    "message": str(error),
                }
            },
            target,
            ensure_ascii=False,
        )
        target.write("\n")
    else:
        target.write(f"Error: {error}\n")
