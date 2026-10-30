"""Utilidades comunes a los tests e2e de la CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def credentials(fake_moodle) -> dict[str, str]:
    return {
        "MOOVI_URL": fake_moodle.url,
        "MOOVI_USER": "profesor",
        "MOOVI_PASSWORD": "secreto",
    }


@pytest.fixture
def run_cli(fake_moodle, tmp_path: Path) -> Callable[..., subprocess.CompletedProcess[str]]:
    home = tmp_path / "home"
    cache = tmp_path / "cache"
    home.mkdir()
    cache.mkdir()

    base_env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("MOOVI_")
    }
    base_env.update(
        {
            "PYTHONPATH": str(ROOT / "src"),
            "HOME": str(home),
            "XDG_CACHE_HOME": str(cache),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )

    def run(
        *args: str,
        extra_env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = {**base_env, **(extra_env or {})}
        return subprocess.run(
            [sys.executable, "-m", "moovi", *args],
            cwd=str(cwd or tmp_path),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    return run


def token_path(tmp_path: Path) -> Path:
    return tmp_path / "cache" / "moovi" / "token.json"
