# zhushi.liuyao

朱辰彬六爻分析系统 —— 基于《古筮真诠》理论体系的纳甲六爻自动排卦与断卦引擎。

---

## 目录

- [功能概览](#功能概览)
- [项目结构](#项目结构)
- [快速上手](#快速上手)
- [CLI 使用说明](#cli-使用说明)
- [Python API](#python-api)
- [双视角输出](#双视角输出)
- [问事类型对照表](#问事类型对照表)
- [理论依据](#理论依据)

---

## 功能概览

| 模块 | 功能 |
|------|------|
| **排卦引擎** | 自动推算干支四柱、纳甲、六亲、六神、世应、旬空 |
| **旺衰分析** | 月建四旺四衰 × 日辰五旺二衰，综合判定每爻旺衰 |
| **动变分析** | 识别有用/无用动爻（回头克/回头生/进退神/化绝/化破），检测暗动 |
| **吉凶判断** | 实现卦局通论八大卦局，含特例处理（求财/失物/问病/行人/忧患） |
| **应期推断** | 旺静逢冲、衰静逢值、动爻逢合、旬空填冲出 |
| **双视角输出** | 失物（父母/妻财）、问病（官鬼/子孙）自动并行两套用神，共享旺衰动变，各自给出吉凶与应期，末尾输出综合结论 |
| **CLI** | 命令行一键排卦+分析，支持摇卦值或卦名+动爻两种输入方式 |

---

## 项目结构

```text
zhushi.liuyao/
├── liuyao/
│   ├── __init__.py                  # 公开 Python API
│   ├── __main__.py                  # python -m liuyao 入口
│   ├── main.py                      # CLI 兼容 facade
│   ├── domain/                      # 排卦、旺衰、动变、吉凶、应期等纯领域逻辑
│   ├── application/use_cases/       # analysis / dto / verdict
│   └── interfaces/cli/              # CLI 与文本报告适配器
├── api/
│   ├── app.py                       # FastAPI application factory
│   ├── core/                        # 配置、日志、异常
│   ├── application/use_cases/       # readings / feedback / templates / engine / support
│   ├── infrastructure/              # Redis 与 SQLAlchemy 实现
│   └── interfaces/http/             # FastAPI dependencies、routers 与 Pydantic schemas
├── data/                            # 经典规则与象法数据
├── docs/                            # 架构文档与理论资料
├── examples/                        # 示例与报告归档
├── migrations/                      # Alembic 迁移
├── scripts/                         # 数据抽取、规则构建、覆盖率脚本
└── tests/                           # 领域、API、规则与回归测试
```

架构边界与重建蓝图见 [`docs/clean-architecture.md`](docs/clean-architecture.md)。边界守护测试见 [`tests/test_architecture_boundaries.py`](tests/test_architecture_boundaries.py)，用于防止内核反向依赖交付层、API 绕过 `liuyao/__init__.py` 公开门面直连内核内部、HTTP router 直连数据库 session 实现、旧平行目录复活、以及新增 `shared/common/utils` 大杂烩目录。

---

## 快速上手

### 安装依赖

```bash
pip install sxtwl
```

### 命令行排卦（最简用法）

```bash
# 输入六次摇卦值（6=老阴 7=少阳 8=少阴 9=老阳），从初爻到上爻
python3 -m liuyao --date 2026-05-25 --yao 9 8 7 9 6 6 --hour 14 --question-type shiwu
```

### Python 代码调用

```python
from liuyao import Hexagram, run_analysis, format_report

# 排卦：2026-05-25 14:28，雷火丰
h = Hexagram([9, 8, 7, 9, 6, 6], 2026, 5, 25, hour=14)
h.display()

# 单视角分析（失物，默认用神：父母）
report = run_analysis(h, "shiwu")
print(format_report(report))
```

```python
from liuyao import Hexagram, run_dual_analysis, format_dual_report

# 双视角分析（失物：父母视角 + 妻财视角）
h = Hexagram([9, 8, 7, 9, 6, 6], 2026, 5, 25, hour=14)
dual = run_dual_analysis(h, "shiwu")
print(format_dual_report(dual))
```

---

## CLI 使用说明

```
python3 -m liuyao --date YYYY-MM-DD [选项]
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--date` | 占卦日期（必填） | `--date 2026-05-25` |
| `--yao 6个值` | 摇卦值，6/7/8/9，从初爻到上爻 | `--yao 9 8 7 9 6 6` |
| `--name 卦名` | 直接指定卦名（与 `--moving` 配合） | `--name 雷火丰` |
| `--moving 爻位…` | 动爻位置（1-6，与 `--name` 配合） | `--moving 1 4 5 6` |
| `--hour` | 时辰（0-23，默认12） | `--hour 14` |
| `--question-type` | 问事类型（见下表） | `--question-type shiwu` |
| `--dual` | 强制启用双视角（非默认双视角类型时） | `--dual` |
| `--no-dual` | 强制单视角（覆盖默认双视角） | `--no-dual` |

---

## Python API

### 排卦

```python
from liuyao import Hexagram

h = Hexagram(yao_values, year, month, day, hour=12)
# yao_values: list[int]，6个值，每个为 6/7/8/9
# 6=老阴(动)  7=少阳(静)  8=少阴(静)  9=老阳(动)
```

### 单视角分析

```python
from liuyao import run_analysis, format_report

report = run_analysis(hexagram, question_type="cai")
# report.jixiong_result  -> {"pattern": "...", "ji_xiong": "吉"/"凶"/"平", "explanation": "..."}
# report.yingqi_results  -> [{"position": n, "di_zhi": "...", "candidates": [...]}]
print(format_report(report))
```

### 双视角分析

```python
from liuyao import run_dual_analysis, format_dual_report

dual = run_dual_analysis(hexagram, question_type="shiwu")
# dual.perspectives      -> [AnalysisReport, AnalysisReport]
# dual.consensus         -> "两视角一致定性: 凶" 或 "视角分歧: ..."
print(format_dual_report(dual))
```

---

## 双视角输出

部分问事类型存在两个同等合理的用神选项，系统自动并行运算，输出对照结论：

| 问事类型 | 视角 1 | 视角 2 | 说明 |
|----------|--------|--------|------|
| `shiwu`（失物） | 父母（物件本相） | 妻财（贵重财物价值） | 物件类取父母，金钱财宝类可兼取妻财 |
| `bing`（疾病） | 官鬼（病势消长） | 子孙（药效医疗） | 官鬼看病情，子孙看治愈力 |

双视角共享旺衰分析与动变分析（只计算一次），各自独立完成吉凶判断与应期推断，末尾输出综合结论（一致/分歧）。

---

## 问事类型对照表

| 类型值 | 中文 | 默认用神 | 是否双视角 |
|--------|------|----------|-----------|
| `cai` | 财运 | 妻财 | 否 |
| `guan` | 官运/工作 | 官鬼 | 否 |
| `hun_male` | 婚姻（男问） | 妻财 | 否 |
| `hun_female` | 婚姻（女问） | 官鬼 | 否 |
| `bing` | 疾病 | 官鬼 | **是** |
| `kaoshi` | 考试/文书 | 父母 | 否 |
| `zinv` | 子女 | 子孙 | 否 |
| `xingRen` | 行人 | 官鬼 | 否 |
| `youHuan` | 忧患 | 子孙 | 否 |
| `shiwu` | 失物 | 父母 | **是** |
| `other` | 其他/综合 | 官鬼 | 否 |

---

## 理论依据

本系统基于朱辰彬《古筮真诠》理论体系实现，核心理论文档：

- `liuyao-gushizhenquan_part1.md` ～ `part23.md`：《古筮真诠》原文分段
- `zhishidianzongjie.md`：知识点汇总（旺衰、动变、卦局通论、应期、双视角用神等）

主要参考规则：
- **用旺世兴**：用神旺相 + 世爻得日月扶助 = 吉
- **用神克世（短期失物特例）**：用神动克旺世 = 短期可成（失物找回）
- **财动化鬼**：妻财动变官鬼 = 物已易主，凶
- **冲飞露伏**：飞神旬空时短期事件用神（藏伏）吉
