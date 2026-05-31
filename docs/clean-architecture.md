# Clean Architecture

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
