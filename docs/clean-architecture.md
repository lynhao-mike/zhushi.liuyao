# Clean Architecture Rebuild

## Thesis

本项目的 Clean Architecture 目标不是继续堆层，而是把真实系统边界收口成两个可独立理解的产品：`liuyao/` 是纯六爻分析内核，`api/` 是 HTTP、缓存、数据库、归档等交付组合器。

行为保持不变；结构改善的标准是依赖方向更清楚、变更影响面更小、伪抽象更少。

## Confidence

中高。

不确定点不在目标方向，而在迁移节奏：当前测试大量直接引用 `liuyao.domain.*` 与 `liuyao.application.use_cases.*`，说明这些路径已经是事实上的内部开发 API。它们可以整理，但不应在一次重建里强行打断。

## The Trap

继承约束是“看起来已经有 Clean Architecture 目录，所以继续细分 layer / port / repository”。这个约束不真实。

真实约束只有这些：

- `liuyao.__init__` 的公共导出面。
- CLI 入口 `python -m liuyao` 与兼容入口 `liuyao/main.py`。
- FastAPI 路由与响应 schema 的外部契约。
- 数据库模型、迁移与已持久化字段。
- 现有测试描述的分析行为。

不真实约束包括旧目录命名、兼容 facade、单实现 service interface、为了“像架构”而存在的空壳层。

## High-格局 Direction

目标模型：一个内核，两个交付面；API 到内核的唯一稳定接触点是 `liuyao/__init__.py` 公开门面。

```text
zhushi.liuyao/
├── liuyao/                         # 六爻分析内核：无 HTTP / DB / Redis 依赖
│   ├── __init__.py                 # 公共 Python API
│   ├── __main__.py                 # python -m liuyao，主 CLI 入口
│   ├── main.py                     # CLI 兼容 facade，只转发，文档不再推广
│   ├── report_archive.py           # 本地报告归档，属于交付辅助
│   ├── application/
│   │   └── use_cases/
│   │       ├── analysis.py         # 分析编排：调用领域规则，生成 report
│   │       ├── dto.py              # AnalysisReport / DualPerspectiveReport
│   │       └── verdict.py          # 综合断语构建
│   ├── domain/
│   │   ├── hexagram.py             # 排卦模型与核心对象
│   │   ├── calendar_utils.py       # 历法与干支工具
│   │   ├── data.py                 # 静态卦象、纳甲、六亲数据
│   │   ├── wangshuai.py            # 旺衰规则
│   │   ├── dongbian.py             # 动变规则
│   │   ├── patterns.py             # 结构模式
│   │   ├── jixiong.py              # 吉凶判断
│   │   ├── yingqi.py               # 应期推断
│   │   ├── classic_*.py            # 古籍证据检索
│   │   └── rules/                  # 动态经典规则引擎
│   └── interfaces/
│       └── cli/
│           ├── main.py             # CLI 参数解析与用例调用
│           └── reporting.py        # 文本报告格式化
├── api/                            # 交付应用：组合 HTTP / cache / DB / engine bridge
│   ├── app.py                      # FastAPI composition root
│   ├── core/                       # 配置、日志、异常注册
│   ├── application/
│   │   └── use_cases/
│   │       ├── dto.py              # API command DTO
│   │       ├── engine.py           # async bridge to sync liuyao engine
│   │       ├── readings.py         # reading 主事务脚本
│   │       ├── reading_support.py  # payload / response helper
│   │       ├── feedback.py         # feedback 事务脚本
│   │       └── templates.py        # template 事务脚本
│   ├── infrastructure/
│   │   ├── cache/
│   │   │   └── redis_client.py
│   │   └── database/
│   │       ├── models.py
│   │       └── session.py
│   └── interfaces/
│       └── http/
│           ├── dependencies.py      # FastAPI dependency adapters
│           ├── routers/            # HTTP routing only
│           └── schemas/            # Pydantic request / response / mappers
├── migrations/                     # DB schema history
├── scripts/                        # one-off data/rule maintenance tools
├── tests/                          # behavior contract
└── docs/
```

## Architecture

依赖方向固定为：

```text
api.interfaces.http -> api.application.use_cases -> api.infrastructure
api.application.use_cases.engine -> liuyao public facade -> liuyao.application.use_cases -> liuyao.domain
liuyao.interfaces.cli -> liuyao.application.use_cases -> liuyao.domain
```

核心原则：

- `liuyao/domain/` 不依赖 FastAPI、SQLAlchemy、Redis、Pydantic settings。
- `liuyao/application/use_cases/analysis.py` 只编排分析流程，不知道 HTTP、缓存、数据库。
- `api/` 不直接导入 `liuyao.domain.*` 或 `liuyao.application.*`；需要跨边界使用的内核能力先进入 `liuyao/__init__.py`。
- `api/interfaces/http/dependencies.py` 是 HTTP dependency 到 infrastructure provider 的薄出口。
- `api/interfaces/http/routers/` 只做协议层输入输出，不直接导入数据库 session 实现，不直接碰 ORM 细节。
- `api/interfaces/http/schemas/mappers.py` 是 HTTP request 到 application command 的边界。
- `api/application/use_cases/readings.py` 可以是事务脚本，负责 cache-aside、DB session、engine 调用的顺序。
- `api/application/use_cases/readings.py` 不 re-export feedback/templates；HTTP 入口直接导入各自用例模块。
- `api/application/use_cases/engine.py` 是异步 API 到同步内核的 bridge，不再额外制造 `port` / `adapter` 接口。

## Frame-Opening Move

采用 Zero-Legacy Thought Experiment：如果今天从零开始，只会建 `liuyao` 内核包和 `api` 交付应用，不会建 `services/`、`db/`、`schemas/`、`routers/` 的平行旧目录，也不会为单个 Redis、单个 SQLAlchemy、单个分析引擎创建接口森林。

这揭示当前最该控制的不是“层数不够”，而是“伪层复活”。

## Bold Takes

- 删除比新增更重要：所有历史平行目录都不应恢复。
- `api/application/use_cases/readings.py` 现在偏胖但可接受；只有当 reading 流程继续增长时，才拆 `repositories.py` 或 `cache.py`。
- HTTP router 依赖数据库 session 的写法应收口到 `api/interfaces/http/dependencies.py`，不用为此创建完整 DI 容器。
- `readings.py` 不应该成为所有 reading-adjacent 用例的聚合桶；feedback/templates 有自己的入口。
- 不新增 `shared/`、`common/`、`utils/`。如果不知道放哪，说明边界没想清楚。
- `liuyao/domain/rules/` 可以保留为子域，因为动态经典规则有独立 schema、fact extraction、engine、result 生命周期。
- `report_archive.py` 长期应归到交付侧；但当前 CLI 与 API 都用它，本轮不移动，避免无收益破坏路径。

## Kill List

长期禁止恢复：

- `api/services/`
- `api/routers/`
- `api/schemas/`
- `api/cache/`
- `api/db/`
- `api/domain/`
- 单实现 `ports/`、`repositories/`、`factories/` 目录
- 跨层大杂烩 `shared/`、`common/`、`utils/`

当前允许短期存在：

- `liuyao/main.py`：CLI 兼容 facade，保留成本极低，但标准入口是 `python -m liuyao`。

## Options

| Option | Shape | Upside | Cost | Verdict |
|---|---|---|---|---|
| Conservative path | 只维持现状，补少量说明 | 零行为风险 | 架构意图继续靠人脑记忆 | 不推荐 |
| Clean target | 立即移动归档、拆 repo/cache、删除 facade | 目录最干净 | 大量导入变更，行为验证成本高 | 方向正确但不适合一步到位 |
| Staged clean path | 文档先定目标，只删除伪层，按证据拆胖文件 | 风险低，持续变干净 | 需要守住规则，不让旧层复活 | 推荐 |

## What Not To Do

- 不为 `ReadingCacheRepo` 和 `ReadingRepo` 立刻抽接口；它们现在只是 `readings.py` 内的局部组织手段。
- 不把所有 DTO 搬到顶层 `application/dto/`；现有 `use_cases/dto.py` 已足够明确。
- 不为了“领域纯粹”把古籍数据文件全部改成 repository；它们是静态知识源，不是持久化业务实体。
- 不做大规模导入路径改名，除非先证明旧路径没有事实契约。
- 不用兼容层掩盖边界错误；公共契约才兼容，内部调用直接改。

## Migration Plan

### Stage 1: Freeze Target

- 以本文档作为目标结构定义。
- 新代码直接导入 `api.application.use_cases.readings`。
- 新 HTTP 能力只进入 `api/interfaces/http/routers/` 与 `api/interfaces/http/schemas/`。
- 新分析规则只进入 `liuyao/domain/` 或 `liuyao/domain/rules/`。

### Stage 2: Shrink Compatibility

- `api/application/use_cases/reading.py` 已确认无项目内引用并删除，且由边界测试防止复活。
- 保留 `liuyao/main.py`，因为它是低成本 CLI 兼容入口；公开文档统一使用 `python -m liuyao`。

### Stage 3: Split Only When Proven

只在出现以下证据时拆文件：

- `api/application/use_cases/readings.py` 的 cache、ORM、workflow 变更互相冲突。
- `api/application/use_cases/engine.py` 的 serialization、archive、thread-pool bridge 需要分别演化。
- `liuyao/application/use_cases/analysis.py` 新增第三种分析流程，导致单/双视角共享逻辑重复。

候选拆分方式：

```text
api/application/use_cases/
├── readings.py          # workflow only
├── reading_cache.py     # cache-aside only, if needed
└── reading_repo.py      # ORM persistence only, if needed
```

只有当上述证据出现时才拆；否则保持现在更简单。

## Verification Path

第一证明点：运行架构边界守护测试。

```cmd
python -m pytest tests/test_architecture_boundaries.py
```

第二证明点：运行最小行为契约测试。

```cmd
python -m pytest tests/test_analysis.py tests/test_api_response_contract.py tests/test_create_reading_unit.py
```

第三证明点：检查架构导入方向。

```cmd
python -m pytest tests/test_cache_keys.py tests/test_db_session.py
```

第四证明点：全量回归。

```cmd
python -m pytest
```

## Falsifier

以下证据会推翻本文目标：

- 出现真实外部用户直接依赖 `api.application.use_cases.reading` 的证据，说明删除 facade 破坏公开契约。
- `liuyao` 内核必须直接访问数据库或 Redis 才能完成核心分析。
- API response schema 无法通过 mapper 与 application command 隔离，必须泄漏到内核。
- `report_archive.py` 的归档副作用导致测试或 API 行为不可控，必须先重新归属。

## Definition of Done

Clean Architecture Rebuild 完成不以“目录更多”衡量，而以这些结果衡量：

- 新功能能一眼判断应该进入 `liuyao` 还是 `api`。
- HTTP、DB、Redis 变更不会影响 `liuyao/domain/`。
- API 交付层只通过 `liuyao/__init__.py` 接触内核公开能力。
- HTTP router 只依赖接口层 dependency adapter 获取数据库 session。
- 分析规则变更不需要修改 FastAPI router。
- 用例模块不通过无契约 re-export 伪装成 service facade。
- 兼容 facade 有明确删除条件。
- 测试证明行为未变。
