# -*- coding: utf-8 -*-
"""Clean Architecture 边界守护测试。"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE_DIRS = ("api", "liuyao")
LEGACY_API_DIRS = ("services", "routers", "schemas", "cache", "db", "domain")
FORBIDDEN_SHARED_DIRS = ("shared", "common", "utils")


def _python_files(*roots: str):
    for root in roots:
        yield from (ROOT / root).rglob("*.py")


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)

    return imported


def test_liuyao_core_does_not_import_api_delivery_layer():
    """六爻内核不能反向依赖 HTTP / DB / Redis 交付层。"""
    offenders = []

    for path in _python_files("liuyao"):
        for module in _imports(path):
            if module == "api" or module.startswith("api."):
                offenders.append(f"{path.relative_to(ROOT)} imports {module}")

    assert offenders == []


def test_legacy_parallel_api_directories_do_not_reappear():
    """旧平行目录不能绕过 interfaces/application/infrastructure 新边界。"""
    offenders = [name for name in LEGACY_API_DIRS if (ROOT / "api" / name).exists()]

    assert offenders == []


def test_legacy_reading_use_case_facade_does_not_reappear():
    """旧单数 reading facade 不能重新掩盖 readings 主用例入口。"""
    assert not (ROOT / "api" / "application" / "use_cases" / "reading.py").exists()



def test_shared_common_utils_directories_do_not_become_architecture_escape_hatches():
    """不新增 shared/common/utils 大杂烩目录。"""
    offenders = []

    for source_dir in PYTHON_SOURCE_DIRS:
        for dirname in FORBIDDEN_SHARED_DIRS:
            path = ROOT / source_dir / dirname
            if path.exists():
                offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []



def test_api_uses_liuyao_public_facade_instead_of_internal_modules():
    """API 交付层只通过 liuyao 公开门面接触分析内核。"""
    offenders = []

    for path in _python_files("api"):
        for module in _imports(path):
            if module.startswith("liuyao.domain") or module.startswith("liuyao.application"):
                offenders.append(f"{path.relative_to(ROOT)} imports {module}")

    assert offenders == []



def test_readings_use_case_does_not_reexport_other_use_cases():
    """readings 用例不聚合 feedback/templates 的入口职责。"""
    imports = _imports(ROOT / "api" / "application" / "use_cases" / "readings.py")

    assert "api.application.use_cases.feedback" not in imports
    assert "api.application.use_cases.templates" not in imports



def test_module_cli_entrypoint_bypasses_compatibility_facade():
    """python -m liuyao 入口不经由 liuyao.main 兼容 facade。"""
    imports = _imports(ROOT / "liuyao" / "__main__.py")

    assert "liuyao.main" not in imports
    assert "liuyao.interfaces.cli.main" in imports



def test_http_routers_use_interface_dependencies_for_database_sessions():
    """HTTP router 不直接绑定数据库 session 实现。"""
    offenders = []

    for path in (ROOT / "api" / "interfaces" / "http" / "routers").rglob("*.py"):
        for module in _imports(path):
            if module == "api.infrastructure.database.session":
                offenders.append(f"{path.relative_to(ROOT)} imports {module}")

    assert offenders == []
