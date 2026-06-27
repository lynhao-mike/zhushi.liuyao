# Clean Architecture

本项目的 Clean Architecture 目标不是继续增加层数，而是把真实边界收口成两个系统：[`liuyao/`](../liuyao) 作为纯分析引擎，[`api/`](../api) 作为 HTTP / 持久化交付层。

## Thesis

- [`liuyao/`](../liuyao) 是核心产品：负责排卦、分析、断语、报告。
- [`api/`](../api) 是适配器应用：负责 HTTP、缓存、数据库、异步执行桥接。
- 目录结构应该直接表达依赖方向，而不是保留历史空壳层名。
- 兼容包装只能作为迁移手段，不能继续当正式架构层。

## 目标目录结构

```text
zhushi.liuyao/
├── liuyao/
│   ├── __init__.py                  # 对外公共 Python API
│   ├── __main__.py                  # python -m 入口
│   ├── main.py                      # 兼容 CLI 入口 facade
│   ├── report_archive.py
│   ├── application/
│   │   ├── dto/
│   │   └── use_cases/
│   │       ├── analysis.py          # 分析编排
│   │       ├── dto.py               # AnalysisReport / DualPerspectiveReport
│   │       └── verdict.py           # 综合断语提取
│   ├── domain/
│   │   ├── hexagram.py
│   │   ├── wangshuai.py
│   │   ├── dongbian.py
│   │   ├── jixiong.py
│   │   ├── yingqi.py
│   │   ├── patterns.py
│   │   └── rules/
│   └── interfaces/
│       └── cli/
│           ├── main.py
│           └── reporting.py
├── api/
│   ├── app.py
│   ├── core/                        # 配置、日志、异常
│   ├── application/
│   │   ├── dto.py                   # API command DTO
│   │   ├── engine.py                # async bridge to liuyao
│   │   └── use_cases/
│   │       ├── readings.py          # readings 主事务脚本入口
│   │       ├── feedback.py
│   │       ├── templates.py
│   │       ├── reading_support.py   # 共享 payload / response helper
│   │       └── reading.py           # 最薄兼容 facade
│   ├── infrastructure/
│   │   ├── cache/
│   │   │   └── redis_client.py
│   │   └── database/
│   │       ├── models.py
│   │       └── session.py
│   └── interfaces/
│       └── http/
│           ├── routers/
│           └── schemas/
└── tests/
```

## 依赖方向

```text
api.interfaces.http -> api.application -> api.infrastructure
api.application -> liuyao.application -> liuyao.domain
liuyao.interfaces.cli -> liuyao.application -> liuyao.domain
```

补充约束：

- [`liuyao/domain/`](../liuyao/domain) 不依赖 FastAPI、SQLAlchemy、Redis。
- [`liuyao/application/use_cases/analysis.py`](../liuyao/application/use_cases/analysis.py) 只做分析编排，不接触 HTTP / DB。
- [`liuyao/interfaces/cli/reporting.py`](../liuyao/interfaces/cli/reporting.py) 只做文本格式化与展示。
- [`api/interfaces/http/routers/`](../api/interfaces/http/routers) 只做协议层转换。
- [`api/interfaces/http/schemas/mappers.py`](../api/interfaces/http/schemas/mappers.py) 负责 HTTP DTO 到 application command 的边界映射。
- [`api/application/use_cases/engine.py`](../api/application/use_cases/engine.py) 是 API 到同步分析引擎的桥，不再额外包一层 port。

## Keep

保留这些边界：

- [`liuyao/__init__.py`](../liuyao/__init__.py) 作为公共 Python API 导出面。
- [`liuyao/main.py`](../liuyao/main.py) 作为 CLI 兼容入口 facade。
- [`api/interfaces/http/schemas/mappers.py`](../api/interfaces/http/schemas/mappers.py) 作为协议模型与应用命令的分界线。

## Kill List

这些内容不应再作为长期架构的一部分，并已在确认无业务引用后删除：

- `api/services/`
- `api/routers/`
- `api/schemas/`
- `api/cache/`
- `api/db/`
- `api/domain/`

如果未来需要兼容，只保留明确入口 facade，不再恢复空壳目录。

## Ponytail 约束

- 不为单实现创建 interface / factory / repository abstraction。
- 不新增 `shared/`、`common/`、`utils/` 之类大杂烩目录。
- 文件过胖才拆；拆到可读即可，不追求教科书式分层。
- 优先删除伪层，少于新增抽象。

## 当前落地策略

本轮只做最小有效重建：

1. 更新 [`docs/clean-architecture.md`](./clean-architecture.md) 为目标结构文档。
2. 从 [`liuyao/application/use_cases/analysis.py`](../liuyao/application/use_cases/analysis.py) 中拆出 DTO 与断语构建逻辑。
3. 保持 [`liuyao/__init__.py`](../liuyao/__init__.py) 与现有测试导入路径不变。
4. 用现有测试验证行为未变。

## 验证点

- [`tests/test_analysis.py`](../tests/test_analysis.py)
- [`tests/test_api_response_contract.py`](../tests/test_api_response_contract.py)

只要导出面与测试行为不变，这次重构就是成功的。
