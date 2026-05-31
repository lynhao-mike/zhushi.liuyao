from pathlib import Path

root = Path('.')

for d in [
    'liuyao/domain',
    'liuyao/application/use_cases',
    'liuyao/application/dto',
    'liuyao/interfaces/cli',
    'api/application/use_cases',
    'api/domain',
    'api/infrastructure/cache',
    'api/infrastructure/database',
    'api/interfaces/http/routers',
    'api/interfaces/http/schemas',
]:
    (root / d).mkdir(parents=True, exist_ok=True)
    init = root / d / '__init__.py'
    if not init.exists():
        init.write_text('', encoding='utf-8')

core_modules = [
    'calendar_utils.py', 'data.py', 'dongbian.py', 'exceptions.py', 'hexagram.py', 'jixiong.py',
    'patterns.py', 'theory.py', 'theory_chapters08_12.py', 'theory_chapters13_16.py',
    'theory_chapters17_20.py', 'theory_chapters21_23.py', 'theory_chapters26_28.py',
    'theory_chapters29_31.py', 'theory_chapters32_40.py', 'wangshuai.py', 'yingqi.py',
]

for name in core_modules:
    src = root / 'liuyao' / name
    dst = root / 'liuyao/domain' / name
    text = src.read_text(encoding='utf-8')
    text = text.replace('from liuyao.theory_chapters', 'from liuyao.domain.theory_chapters')
    dst.write_text(text, encoding='utf-8')

analyzer = (root / 'liuyao/analyzer.py').read_text(encoding='utf-8')
for old, new in {
    'from .hexagram import Hexagram': 'from liuyao.domain.hexagram import Hexagram',
    'from .data import get_star_spirits': 'from liuyao.domain.data import get_star_spirits',
    'from .wangshuai import analyze_hexagram_wangshuai': 'from liuyao.domain.wangshuai import analyze_hexagram_wangshuai',
    'from .dongbian import analyze_dongbian': 'from liuyao.domain.dongbian import analyze_dongbian',
    'from .jixiong import (': 'from liuyao.domain.jixiong import (',
    'from .yingqi import analyze_yingqi': 'from liuyao.domain.yingqi import analyze_yingqi',
    'from .patterns import analyze_all_patterns': 'from liuyao.domain.patterns import analyze_all_patterns',
    'from .exceptions import AnalysisError': 'from liuyao.domain.exceptions import AnalysisError',
}.items():
    analyzer = analyzer.replace(old, new)
(root / 'liuyao/application/use_cases/analysis.py').write_text(analyzer, encoding='utf-8')

report = (root / 'liuyao/report.py').read_text(encoding='utf-8')
report = report.replace('from .analyzer import', 'from liuyao.application.use_cases.analysis import')
report = report.replace('from .hexagram import', 'from liuyao.domain.hexagram import')
report = report.replace('from .data import', 'from liuyao.domain.data import')
(root / 'liuyao/interfaces/cli/reporting.py').write_text(report, encoding='utf-8')

main = (root / 'liuyao/main.py').read_text(encoding='utf-8')
main = main.replace('from .hexagram import Hexagram', 'from liuyao.domain.hexagram import Hexagram')
main = main.replace('from .data import HEXAGRAM_BY_NAME, BINARY_TO_GUA, BA_GUA', 'from liuyao.domain.data import HEXAGRAM_BY_NAME, BINARY_TO_GUA, BA_GUA')
main = main.replace('from .analyzer import run_analysis, run_dual_analysis', 'from liuyao.application.use_cases.analysis import run_analysis, run_dual_analysis')
main = main.replace('from .jixiong import DUAL_PERSPECTIVE_TABLE', 'from liuyao.domain.jixiong import DUAL_PERSPECTIVE_TABLE')
main = main.replace('from .report import format_report, format_dual_report', 'from liuyao.interfaces.cli.reporting import format_report, format_dual_report')
(root / 'liuyao/interfaces/cli/main.py').write_text(main, encoding='utf-8')

mapping = {
    'api/services/engine.py': 'api/application/use_cases/engine.py',
    'api/services/reading.py': 'api/application/use_cases/reading.py',
    'api/schemas/reading.py': 'api/interfaces/http/schemas/reading.py',
    'api/routers/readings.py': 'api/interfaces/http/routers/readings.py',
    'api/routers/templates.py': 'api/interfaces/http/routers/templates.py',
    'api/routers/health.py': 'api/interfaces/http/routers/health.py',
    'api/cache/redis_client.py': 'api/infrastructure/cache/redis_client.py',
    'api/db/models.py': 'api/infrastructure/database/models.py',
    'api/db/session.py': 'api/infrastructure/database/session.py',
}

for src_path, dst_path in mapping.items():
    text = (root / src_path).read_text(encoding='utf-8')
    text = text.replace('from api.cache.redis_client import', 'from api.infrastructure.cache.redis_client import')
    text = text.replace('from api.db.models import', 'from api.infrastructure.database.models import')
    text = text.replace('from api.db.session import', 'from api.infrastructure.database.session import')
    text = text.replace('from api.schemas.reading import', 'from api.interfaces.http.schemas.reading import')
    text = text.replace('from api.services.engine import', 'from api.application.use_cases.engine import')
    text = text.replace('from api.services import reading as reading_svc', 'from api.application.use_cases import reading as reading_svc')
    text = text.replace('from api.routers import health, readings, templates', 'from api.interfaces.http.routers import health, readings, templates')
    text = text.replace('from liuyao.data import QUESTION_TYPE_LABELS', 'from liuyao.domain.data import QUESTION_TYPE_LABELS')
    text = text.replace('from liuyao.jixiong import DUAL_PERSPECTIVE_TABLE', 'from liuyao.domain.jixiong import DUAL_PERSPECTIVE_TABLE')
    (root / dst_path).write_text(text, encoding='utf-8')

app = (root / 'api/app.py').read_text(encoding='utf-8')
app = app.replace('from api.cache.redis_client import close_redis, init_redis', 'from api.infrastructure.cache.redis_client import close_redis, init_redis')
app = app.replace('from api.db.session import close_engine', 'from api.infrastructure.database.session import close_engine')
app = app.replace('from api.routers import health, readings, templates', 'from api.interfaces.http.routers import health, readings, templates')
(root / 'api/app.py').write_text(app, encoding='utf-8')

wrappers = {
    'api/services/engine.py': 'from api.application.use_cases.engine import *  # noqa: F401,F403\n',
    'api/services/reading.py': 'from api.application.use_cases.reading import *  # noqa: F401,F403\n',
    'api/schemas/reading.py': 'from api.interfaces.http.schemas.reading import *  # noqa: F401,F403\n',
    'api/routers/readings.py': 'from api.interfaces.http.routers.readings import *  # noqa: F401,F403\n',
    'api/routers/templates.py': 'from api.interfaces.http.routers.templates import *  # noqa: F401,F403\n',
    'api/routers/health.py': 'from api.interfaces.http.routers.health import *  # noqa: F401,F403\n',
    'api/cache/redis_client.py': 'from api.infrastructure.cache.redis_client import *  # noqa: F401,F403\n',
    'api/db/models.py': 'from api.infrastructure.database.models import *  # noqa: F401,F403\n',
    'api/db/session.py': 'from api.infrastructure.database.session import *  # noqa: F401,F403\n',
}
for path, text in wrappers.items():
    (root / path).write_text(text, encoding='utf-8')

liu_wrappers = {
    'analyzer.py': 'from liuyao.application.use_cases.analysis import *  # noqa: F401,F403\n',
    'report.py': 'from liuyao.interfaces.cli.reporting import *  # noqa: F401,F403\n',
    'main.py': 'from liuyao.interfaces.cli.main import *  # noqa: F401,F403\n\nif __name__ == "__main__":\n    main()\n',
}
for path, text in liu_wrappers.items():
    (root / 'liuyao' / path).write_text(text, encoding='utf-8')

for name in core_modules:
    (root / 'liuyao' / name).write_text(
        f'from liuyao.domain.{name[:-3]} import *  # noqa: F401,F403\n', encoding='utf-8'
    )

init = (root / 'liuyao/__init__.py').read_text(encoding='utf-8')
init = init.replace('from .hexagram import Hexagram, YaoLine', 'from liuyao.domain.hexagram import Hexagram, YaoLine')
init = init.replace('from .analyzer import (', 'from liuyao.application.use_cases.analysis import (')
init = init.replace('from .report import format_report, format_dual_report, format_readable_report', 'from liuyao.interfaces.cli.reporting import format_report, format_dual_report, format_readable_report')
init = init.replace('from .exceptions import LiuyaoError, ArrangementError, AnalysisError, CalendarError', 'from liuyao.domain.exceptions import LiuyaoError, ArrangementError, AnalysisError, CalendarError')
init = init.replace('from .data import JiXiong, QUESTION_TYPE_LABELS', 'from liuyao.domain.data import JiXiong, QUESTION_TYPE_LABELS')
(root / 'liuyao/__init__.py').write_text(init, encoding='utf-8')

mig = root / 'migrations/env.py'
if mig.exists():
    text = mig.read_text(encoding='utf-8')
    text = text.replace('from api.db.models import Base', 'from api.infrastructure.database.models import Base')
    mig.write_text(text, encoding='utf-8')

(root / 'docs').mkdir(exist_ok=True)
(root / 'docs/clean-architecture.md').write_text('''# Clean Architecture

本项目已按 Clean Architecture 分层组织，同时保留旧导入路径作为兼容适配层，确保既有测试、CLI 与 API 行为不变。

## 目录结构

```text
liuyao/
  domain/                 # 六爻核心领域模型、规则、算法：无 Web/DB/Redis 依赖
  application/use_cases/  # 应用用例编排：分析流程、双视角流程
  interfaces/cli/         # CLI 与文本报告适配器
  *.py                    # 旧路径兼容包装，转发到新分层

api/
  application/use_cases/  # API 用例：占卜分析、读数/模板业务流程
  infrastructure/cache/   # Redis 适配器与缓存键实现
  infrastructure/database/# SQLAlchemy 模型与会话实现
  interfaces/http/        # FastAPI 路由与 Pydantic HTTP DTO
  core/                   # 配置、日志、异常等横切关注点
  cache|db|routers|schemas|services/ # 旧路径兼容包装
```

## 依赖方向

```text
interfaces -> application -> domain
application -> infrastructure（通过当前项目的轻量适配器调用；后续可抽象为 ports）
infrastructure -> core
domain -> 标准库/纯算法数据
```

## 迁移策略

- 领域算法复制到 `liuyao/domain`，旧 `liuyao/*.py` 作为兼容 facade。
- 分析编排迁移到 `liuyao/application/use_cases/analysis.py`。
- 报告与 CLI 迁移到 `liuyao/interfaces/cli`。
- FastAPI 路由/Schema 迁移到 `api/interfaces/http`。
- Redis/SQLAlchemy 迁移到 `api/infrastructure`。
- API 服务流程迁移到 `api/application/use_cases`。

## 结果

- 领域层不依赖 FastAPI、SQLAlchemy、Redis。
- API 展示层不直接承载业务流程，只转调用例。
- 保留旧模块路径，降低一次性重构风险。
''', encoding='utf-8')
