"""Comprueba que se respeta la regla de dependencias entre capas."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

# Capas y prefijos de import permitidos dentro del propio proyecto.
FORBIDDEN = {
    "domain": ("moovi.logic", "moovi.network", "moovi.infra", "moovi.cli"),
    "logic": ("moovi.network", "moovi.infra", "moovi.cli"),
    "network": ("moovi.infra", "moovi.cli"),
    "infra": ("moovi.network", "moovi.cli"),
    "cli": (),
}


def _module_name(path: Path) -> tuple[str, str]:
    relative = path.relative_to(SRC).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    module = ".".join(parts)
    package = module if path.name == "__init__.py" else module.rsplit(".", 1)[0]
    return module, package


def _resolve_import(node: ast.ImportFrom, package: str) -> str:
    if node.level == 0:
        return node.module or ""
    parts = package.split(".")
    base = parts[: len(parts) - (node.level - 1)]
    if node.module:
        base.append(node.module)
    return ".".join(base)


def _imports(path: Path) -> list[str]:
    _, package = _module_name(path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(_resolve_import(node, package))
    return imported


def test_layers_respect_dependency_rule() -> None:
    violations: list[str] = []
    for path in sorted((SRC / "moovi").rglob("*.py")):
        layer = path.relative_to(SRC / "moovi").parts[0]
        if layer not in FORBIDDEN:
            continue
        for imported in _imports(path):
            for forbidden in FORBIDDEN[layer]:
                if imported == forbidden or imported.startswith(forbidden + "."):
                    violations.append(
                        f"{path.relative_to(SRC)} importa {imported} "
                        f"(prohibido en la capa {layer})"
                    )
    assert not violations, "\n".join(violations)


def test_formats_only_depend_on_generic_helpers() -> None:
    allowed = (
        "moovi.cli.tables.base",
        "moovi.cli.text",
    )
    forbidden = (
        "moovi.domain",
        "moovi.logic",
        "moovi.network",
        "moovi.infra",
        "moovi.cli.tables.",
    )
    violations: list[str] = []
    for path in sorted((SRC / "moovi" / "cli" / "formats").rglob("*.py")):
        for imported in _imports(path):
            if not imported.startswith("moovi."):
                continue
            if any(
                imported == prefix or imported.startswith(prefix + ".")
                for prefix in allowed
            ):
                continue
            if any(
                imported == prefix or imported.startswith(prefix)
                for prefix in forbidden
            ):
                violations.append(f"{path.name} importa {imported}")
    assert not violations, "\n".join(violations)


def test_tables_do_not_depend_on_formatters() -> None:
    violations: list[str] = []
    for path in sorted((SRC / "moovi" / "cli" / "tables").rglob("*.py")):
        for imported in _imports(path):
            if imported == "moovi.cli.formats" or imported.startswith(
                "moovi.cli.formats."
            ):
                violations.append(f"{path.name} importa {imported}")
    assert not violations, "\n".join(violations)


def test_formats_do_not_parse_html() -> None:
    violations: list[str] = []
    for path in sorted((SRC / "moovi" / "cli" / "formats").rglob("*.py")):
        if "html.parser" in _imports(path):
            violations.append(path.name)
    assert not violations, f"HTMLParser en formats: {violations}"


def test_domain_has_no_third_party_imports() -> None:
    allowed_roots = {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "typing",
    }
    violations: list[str] = []
    for path in sorted((SRC / "moovi" / "domain").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots = [(node.module or "").split(".")[0]]
            for root in roots:
                if root and root not in allowed_roots and root != "moovi":
                    violations.append(f"{path.name} importa {root}")
    assert not violations, "\n".join(violations)
