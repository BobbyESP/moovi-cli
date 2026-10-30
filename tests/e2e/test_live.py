"""Tests contra una instancia real de Moovi. Desactivados por defecto."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.live


def _skip_unless_enabled() -> None:
    if os.environ.get("MOOVI_E2E") != "1":
        pytest.skip("Define MOOVI_E2E=1 para ejecutar los tests live")
    if not (ROOT / ".env").exists():
        pytest.skip("Falta .env en la raíz del repositorio")


def test_live_whoami() -> None:
    _skip_unless_enabled()

    result = subprocess.run(
        [sys.executable, "-m", "moovi", "whoami"],
        cwd=str(ROOT),
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "Usuario:" in result.stdout


def test_live_courses() -> None:
    _skip_unless_enabled()

    result = subprocess.run(
        [sys.executable, "-m", "moovi", "courses", "--json"],
        cwd=str(ROOT),
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("[")
