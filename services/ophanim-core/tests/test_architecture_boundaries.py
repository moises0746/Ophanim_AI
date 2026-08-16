"""Minimal dependency-direction checks for S01-T01 package scaffolding."""

from __future__ import annotations

import ast
from pathlib import Path

CORE_ROOT = Path(__file__).resolve().parents[1] / "ophanim"
FORBIDDEN_DOMAIN_ROOTS = {
    "fastapi",
    "pydantic",
    "sqlalchemy",
    "redis",
    "celery",
    "playwright",
    "browser_use",
    "mcp",
    "anythingllm",
    "lmstudio",
    "ollama",
}
FORBIDDEN_DOMAIN_MODULES = {
    "ophanim.application",
    "ophanim.adapters",
    "ophanim.infrastructure",
    "ophanim.api",
    "ophanim.observability",
}


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_domain_package_has_no_forbidden_framework_or_runtime_imports() -> None:
    domain_files = list((CORE_ROOT / "domain").rglob("*.py"))
    assert domain_files
    imports = {module.split(".", 1)[0] for path in domain_files for module in _imports(path)}
    assert not imports.intersection(FORBIDDEN_DOMAIN_ROOTS)
    assert not any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for path in domain_files
        for module in _imports(path)
        for forbidden in FORBIDDEN_DOMAIN_MODULES
    )


def test_layer_packages_import_without_runtime_wiring() -> None:
    import ophanim.api
    import ophanim.application
    import ophanim.domain
    import ophanim.observability
    import ophanim.ports

    assert all(
        package is not None
        for package in (
            ophanim.api,
            ophanim.application,
            ophanim.domain,
            ophanim.observability,
            ophanim.ports,
        )
    )
