# Clean Architecture Rebuild

## Thesis

本项目的 Clean Architecture Rebuild 不应该围绕对外 API 展开。真实使用方式是 Codex 直接读取资料、调用或检查本地六爻分析内核，因此正确目标是：`liuyao/` 成为可独立运行、可测试、无交付依赖的本地分析内核；`data/` 与 `docs/` 成为知识输入；`api/` 只是冻结的可选交付层，不是近期主轴。

行为保持不变。重建只改结构边界：本地分析优先、知识资料清晰、交付副作用靠边、伪抽象更少。

## Confidence

中高。

方向比较确定，因为现有代码已经显露出自然边界：CLI 与 API 都围绕同一个同步六爻内核运行；FastAPI、Redis、SQLAlchemy 都是交付侧能力，不属于核心分析。唯一不确定点是迁移节奏：现有测试和内部调用已经把部分路径当作事实契约，不能为了“目录更漂亮”一次性打断。

## The Trap

继承约束是“项目已经有 Clean Architecture 目录，所以继续补 ports、repositories、services、factories”。这个约束不真实。

真实约束只有：

- `liuyao/__init__.py` 的公开 Python API。
- `python -m liuyao` CLI 入口与低成本兼容入口 `liuyao/main.py`。
- FastAPI 路由、请求 schema、响应 schema 的外部契约。
- 数据库模型、迁移与已持久化字段。
- 现有测试证明的分析行为。

不真实约束包括：旧目录名、内部导入习惯、单实现接口、为了“像架构”而拆出来的空层、未来也许会用到的扩展点、暂时不需要的对外 HTTP 产品化。

## High-格局 Direction

目标模型：一个本地分析内核，一个知识资料库，一个冻结的可选 API 外壳。

```text
zhushi.liuyao/
├── liuyao/                         # 六爻分析内核：不依赖 HTTP / DB / Redis
│   ├── __init__.py                 # 稳定公开 Python API，API 交付层只能从这里接触内核
│   ├── __main__.py                 # python -m liuyao 主入口
│   ├── main.py                     # CLI 兼容 facade，只转发，不扩大职责
│   ├── application/
│   │   └── use_cases/
│   │       ├── analysis.py         # 分析编排：调用领域规则，生成报告对象
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
│   │   └── rules/                  # 动态经典规则子域
│   └── interfaces/
│       └── cli/
│           ├── main.py             # CLI 参数解析与用例调用
│           └── reporting.py        # 文本报告格式化
├── api/                            # 可选交付应用：暂时冻结，不作为近期演化主轴
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
│           ├── dependencies.py     # FastAPI dependency adapters
│           ├── routers/            # HTTP routing only
│           └── schemas/            # Pydantic request / response / mappers
├── data/                           # Codex 与内核共同读取的经典规则与象法数据
├── migrations/                     # DB schema history
├── scripts/                        # one-off data/rule maintenance tools
├── tests/                          # behavior and architecture contracts
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
- 近期新增能力优先进入 `liuyao/`、`data/`、`docs/`；不要为了暂时不用的对外接口扩展 `api/`。
- `api/` 若继续保留，不直接导入 `liuyao.domain.*` 或 `liuyao.application.*`；跨边界能力先进入 `liuyao/__init__.py`。
- `api/interfaces/http/routers/` 只做协议层输入输出，不直接绑定数据库 session 实现。
- `api/interfaces/http/dependencies.py` 是 HTTP dependency 到 infrastructure provider 的薄适配层。
- `api/interfaces/http/schemas/mappers.py` 是 HTTP request 到 application command 的边界。
- `api/application/use_cases/readings.py` 可以是事务脚本，负责 cache-aside、DB session、engine 调用顺序。
- `api/application/use_cases/readings.py` 不 re-export feedback/templates；HTTP 入口直接导入对应用例模块。
- `api/application/use_cases/engine.py` 是异步 API 到同步内核的 bridge，不为单个分析引擎制造 port / adapter 接口。

## Frame-Opening Move

采用 Zero-Legacy Thought Experiment：如果今天从零开始且没有对外 API 需求，只会建 `liuyao` 内核包、`data` 知识资料、`docs` 分析说明；`api` 最多作为以后需要产品化时再启用的外壳，不会为单个 Redis、单个 SQLAlchemy、单个分析引擎创建接口森林。

它揭示真正要重建的不是“层数”，而是“本地分析闭环”：资料能被 Codex 读懂，内核能被测试证明，交付副作用不干扰判断。

## Ponytail Constraint

最懒、最稳的 Clean Architecture 是：先守住边界，不提前拆文件。

- 不新增单实现 interface。
- 不新增 `ports/`、`repositories/`、`factories/` 目录。
- 不新增跨层 `shared/`、`common/`、`utils/`。
- 不为未来 API 产品化预留目录；等真的要对外服务再恢复投入。
- 不移动 `report_archive.py`，除非归档副作用真的开始污染测试或 API 行为。
- 不把 `readings.py` 立即拆成多个文件；只有变更冲突被测试或维护成本证明后再拆。

## Bold Takes

- 删除比新增更重要：所有历史平行目录都不应恢复。
- `api/application/use_cases/readings.py` 偏胖但近期可冻结；现在拆会增加文件和跳转，不会服务当前 Codex 本地分析工作流。
- `ReadingCacheRepo` 与 `ReadingRepo` 当前只是同文件内的局部组织方式，不值得升级成全局 repository 层。
- HTTP router 依赖数据库 session 的写法应收口到 `api/interfaces/http/dependencies.py`，不用完整 DI 容器。
- `liuyao/domain/rules/` 可以保留为子域，因为动态经典规则有独立 schema、fact extraction、engine、result 生命周期。
- `liuyao/main.py` 保留为兼容 facade；标准入口是 `python -m liuyao`，文档不再推广旧入口。
- `report_archive.py` 长期更像交付侧归档能力；本轮不移动，避免无收益破坏路径。

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

- `liuyao/main.py`：CLI 兼容 facade，保留成本极低。
- `api/application/use_cases/readings.py` 内部的 `ReadingCacheRepo` / `ReadingRepo`：局部类，不形成全局架构层。

## Options

| Option | Shape | Upside | Cost | Verdict |
|---|---|---|---|---|
| Conservative path | 维持现状，只补少量说明 | 零行为风险 | 架构意图继续靠人脑记忆 | 不推荐 |
| Clean target | 立即移动归档、拆 repo/cache、删除 facade | 目录最干净 | 大量导入变更，行为验证成本高 | 方向正确但不适合一步到位 |
| Staged clean path | 文档先定目标，冻结 API，优先强化本地内核与资料 | 风险低，贴合真实用法 | 需要持续拒绝伪层复活 | 推荐 |

## What Not To Do

- 不为 `ReadingCacheRepo` 和 `ReadingRepo` 立刻抽接口；单实现接口是噪声。
- 不把所有 DTO 搬到顶层 `application/dto/`；现有 `use_cases/dto.py` 已足够明确。
- 不为了“领域纯粹”把古籍数据文件全部改成 repository；它们是静态知识源，不是业务持久化实体。
- 不做大规模导入路径改名，除非先证明旧路径没有事实契约。
- 不用兼容层掩盖边界错误；公共契约才兼容，内部调用直接改。
- 不把 `api/application/use_cases/engine.py` 拆成 serializer/archive/threadpool 三层，除非这些职责开始独立变化。

## Migration Plan

### Stage 1: Freeze Target

- 以本文档作为目标结构定义。
- 新代码优先通过 `liuyao/__init__.py`、`liuyao/application/use_cases/analysis.py` 或 CLI 本地入口接入分析能力。
- 近期不新增 HTTP 能力；确实需要时才进入 `api/interfaces/http/routers/` 与 `api/interfaces/http/schemas/`。
- 新分析规则只进入 `liuyao/domain/` 或 `liuyao/domain/rules/`。
- 新知识资料进入 `data/` 或 `docs/reference/`，不要塞进 API 层。
- 新 API 到内核的调用必须先进入 `liuyao/__init__.py` 公开门面。

### Stage 2: Shrink Compatibility

- `api/application/use_cases/reading.py` 不恢复；边界测试防止旧单数 facade 复活。
- 保留 `liuyao/main.py`，因为它是低成本 CLI 兼容入口；公开文档统一使用 `python -m liuyao`。
- 发现内部调用旧路径时直接改调用方，不新增 shim。

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

## First Proof Point

第一证明点：本地分析行为测试通过。

```cmd
python -m pytest tests/test_analysis.py
```

第二证明点：架构边界守护测试通过。

```cmd
python -m pytest tests/test_architecture_boundaries.py
```

第三证明点：API 仍未被现有边界破坏。

```cmd
python -m pytest tests/test_analysis.py tests/test_api_response_contract.py tests/test_create_reading_unit.py
```

第四证明点：缓存与数据库边界仍可作为冻结层回归。

```cmd
python -m pytest tests/test_cache_keys.py tests/test_db_session.py
```

第五证明点：全量回归通过。

```cmd
python -m pytest
```

## Falsifier

以下证据会推翻本文目标：

- 出现真实外部用户直接依赖已删除或禁止恢复的内部路径，说明该路径其实是公开契约。
- `liuyao` 内核必须直接访问数据库或 Redis 才能完成核心分析。
- API response schema 无法通过 mapper 与 application command 隔离，必须泄漏到内核。
- 重新出现明确对外 API 交付需求，且 Codex 本地读取分析不再是主用法。
- `api/application/use_cases/readings.py` 的局部 repo/cache 类开始被多个模块复用，说明它们已经变成真实独立概念。
- `report_archive.py` 的归档副作用导致测试或 API 行为不可控，必须先重新归属。

## Definition of Done

Clean Architecture Rebuild 完成不以“目录更多”衡量，而以这些结果衡量：

- 新功能能一眼判断应该进入 `liuyao`、`data`、`docs`，还是少数情况下进入冻结的 `api`。
- HTTP、DB、Redis 变更不会影响 `liuyao/domain/`。
- API 交付层只通过 `liuyao/__init__.py` 接触内核公开能力。
- HTTP router 只依赖接口层 dependency adapter 获取数据库 session。
- 分析规则和知识资料变更不需要修改 FastAPI router。
- 用例模块不通过无契约 re-export 伪装成 service facade。
- 兼容 facade 有明确删除条件。
- 测试证明行为未变。
