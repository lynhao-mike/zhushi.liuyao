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


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")



def _imports(path: Path) -> set[str]:
    tree = ast.parse(_read_text(path), filename=str(path))
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



def test_docs_keep_local_analysis_as_primary_path():
    """README 与架构文档应继续声明本地分析优先、API 冻结为可选层。"""
    readme = _read_text(ROOT / "README.md")
    architecture_doc = _read_text(ROOT / "docs" / "clean-architecture.md")

    assert "当前主路径不是对外 API，而是本地分析内核 + 知识资料" in readme
    assert "api/` 只是冻结的可选交付层，不是近期主轴" in architecture_doc



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



def test_cli_compatibility_facade_exports_only_main_entrypoint():
    """liuyao.main 兼容 facade 只显式转发 main，不再通配泄漏 CLI 内部名字。"""
    path = ROOT / "liuyao" / "main.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    import_from_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    star_imports = [
        node for node in import_from_nodes
        if node.module == "liuyao.interfaces.cli.main" and any(alias.name == "*" for alias in node.names)
    ]

    assert star_imports == []
    assert 'from liuyao.interfaces.cli.main import main' in source
    assert '__all__ = ["main"]' in source



def test_public_python_facade_keeps_local_analysis_entrypoints():
    """liuyao 公共门面应继续暴露本地分析主路径所需的最小入口。"""
    source = _read_text(ROOT / "liuyao" / "__init__.py")

    required_exports = [
        '"Hexagram"',
        '"run_analysis"',
        '"run_dual_analysis"',
        '"format_report"',
        '"format_dual_report"',
        '"format_readable_report"',
        '"QUESTION_TYPE_LABELS"',
    ]
    for export_name in required_exports:
        assert export_name in source



def test_http_routers_use_interface_dependencies_for_database_sessions():
    """HTTP router 不直接绑定数据库 session 实现。"""
    offenders = []

    for path in (ROOT / "api" / "interfaces" / "http" / "routers").rglob("*.py"):
        for module in _imports(path):
            if module == "api.infrastructure.database.session":
                offenders.append(f"{path.relative_to(ROOT)} imports {module}")

    assert offenders == []


def test_auxiliary_classic_sources_stay_out_of_rule_pipeline():
    """《黄金策》《易冒》等辅助资料只能进报告层, 不能进入核心规则主判。"""
    forbidden_modules = {
        "liuyao.domain.classic_judgements",
        "liuyao.domain.classic_imagery",
        "liuyao.domain.yimao_imagery",
    }
    offenders = []

    for path in (ROOT / "liuyao" / "domain" / "rules").rglob("*.py"):
        for module in _imports(path):
            if module in forbidden_modules:
                offenders.append(f"{path.relative_to(ROOT)} imports {module}")

    assert offenders == []


def test_reports_keep_auxiliary_sources_as_non_judgement_layers():
    """报告层必须明确辅助资料只做校验、印证、取象, 不改主判。"""
    source = _read_text(ROOT / "liuyao" / "interfaces" / "cli" / "reporting.py")

    required_phrases = [
        "《卜筮正宗》只作基础校验和纠偏, 不改判",
        "《黄金策》提供经典断语参考",
        "《易冒》提供方位、人物、状态、物象等古法取象",
        "不作吉凶主判",
    ]
    for phrase in required_phrases:
        assert phrase in source
