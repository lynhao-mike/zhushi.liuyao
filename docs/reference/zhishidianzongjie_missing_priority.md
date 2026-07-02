# zhishidianzongjie 缺失知识优先级清单

来源矩阵：[zhishidianzongjie_execution_matrix.md](zhishidianzongjie_execution_matrix.md:1)

原则：只处理“缺失”节点；不重构规则引擎；先补最小可触发标签和测试，再考虑改判。

## 总览

| 优先级 | 范围 | 节点 | 处理策略 |
|---|---|---|---|
| P0 | 会改变断卦主路径 | K147-K150、K172-K176 | 先补上下文/标签，避免误判 |
| P1 | 会改变报告解释与复核 | K130-K146、K169-K171 | 先做模式识别，不直接改判 |
| P2 | 只影响建议/后处理 | K174 | 单独做报告建议段，不进吉凶 |

## P0：必须先补的最小能力

### 1. 特殊时效卦/连占卦路由

- 节点：K147-K150，对应 [zhishidianzongjie.md:1569](zhishidianzongjie.md:1569)、[zhishidianzongjie.md:1595](zhishidianzongjie.md:1595)、[zhishidianzongjie.md:1631](zhishidianzongjie.md:1631)、[zhishidianzongjie.md:1637](zhishidianzongjie.md:1637)。
- 现状：矩阵指向 [route_analysis()](../../liuyao/domain/analysis_router.py:90)，但没有稳定消费者。
- 最小做法：扩展 [route_analysis()](../../liuyao/domain/analysis_router.py:90) 的 `mode/time_scope` 标签，不新增规则类。
- 验证：构造 `dangri`、`zhongshen_*`、`zaizhan` 三类样例，断言路由标签存在且报告可见。
- 不做：暂不改 [P0_RULES](../../liuyao/domain/rules/p0_rules.py:1546) 优先级。

### 2. 无用动爻转有用

- 节点：K172-K173，对应 [zhishidianzongjie.md:1915](zhishidianzongjie.md:1915)、[zhishidianzongjie.md:1919](zhishidianzongjie.md:1919)。
- 现状：[analyze_moving_line()](../../liuyao/domain/dongbian.py:55) 先定无用，[check_dong_yao_interaction()](../../liuyao/domain/dongbian.py:156) 直接过滤，缺“反转入口”。
- 最小做法：在 [analyze_dongbian()](../../liuyao/domain/dongbian.py:434) 输出 `reactivated_moving` 字段，只标记不参与改判。
- 验证：新增一个动爻化退/化破但被特殊条件重新标记的单元测试，先断言字段，不断言吉凶。
- 不做：暂不让无用转有用直接覆盖主判。

### 3. 应爻特殊分析/用神克世思维

- 节点：K175-K176，对应 [zhishidianzongjie.md:1973](zhishidianzongjie.md:1973)、[zhishidianzongjie.md:1997](zhishidianzongjie.md:1997)。
- 现状：只有 [find_ying_line()](../../liuyao/domain/jixiong.py:142) 和 [RuleContext.intervening_positions](../../liuyao/domain/rules/context.py:91) 零散支持。
- 最小做法：在 [RuleContext](../../liuyao/domain/rules/context.py:15) 增加 `ying_line` 访问器或复用现有 `hexagram.ying_line`，报告中增加“应爻复核”提示。
- 验证：指定目标卦样例中展示应爻位置、六亲、与世/用关系。
- 不做：暂不新增双核大模型。

## P1：先识别，不改判

### 4. 灾卦

- 节点：K130-K134，对应 [zhishidianzongjie.md:1457](zhishidianzongjie.md:1457) 到 [zhishidianzongjie.md:1483](zhishidianzongjie.md:1483)。
- 最小做法：在 [analyze_perspective_patterns()](../../liuyao/domain/patterns.py:846) 增加 `risk_gua` 提示字段。
- 输出：只进技术报告，不进 [judge_jixiong()](../../liuyao/domain/jixiong.py:393)。

### 5. 应期卦真假/意外

- 节点：K135-K138，对应 [zhishidianzongjie.md:1487](zhishidianzongjie.md:1487) 到 [zhishidianzongjie.md:1503](zhishidianzongjie.md:1503)。
- 现状：[estimate_yingqi_gen()](../../liuyao/domain/yingqi.py:242) 已有无根提示。
- 最小做法：把 `无根提示` 升级为结构化字段 `timing_risk`，报告照旧展示。
- 不做：不引入新的应期推断算法。

### 6. 指导卦/现状卦

- 节点：K139-K146，对应 [zhishidianzongjie.md:1517](zhishidianzongjie.md:1517) 到 [zhishidianzongjie.md:1555](zhishidianzongjie.md:1555)。
- 最小做法：复用已有动变事实：化墓、暗动、临日、临月，输出 `guidance_signals` 与 `current_state_signals`。
- 位置：优先放在 [patterns.py](../../liuyao/domain/patterns.py:1)，因为这是模式识别，不是终局规则。
- 不做：不让指导卦直接给吉凶。

### 7. 双核卦象

- 节点：K169-K171，对应 [zhishidianzongjie.md:1845](zhishidianzongjie.md:1845) 到 [zhishidianzongjie.md:1903](zhishidianzongjie.md:1903)。
- 现状：[DualCoreDesignatedTargetRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:855) 是最小规则。
- 最小做法：先在报告增加双核候选列表：相冲、同类、相同三个关系。
- 不做：不扩展为复杂竞争/替身系统。

## P2：报告建议，不进推理

### 8. 化解凶卦办法

- 节点：K174，对应 [zhishidianzongjie.md:1953](zhishidianzongjie.md:1953)。
- 最小做法：新增报告段 `化解建议`，仅当 [jixiong_result](../../liuyao/domain/jixiong.py:393) 为凶时展示。
- 不做：不参与吉凶、不参与应期、不影响规则。

## 下一步最小执行顺序

1. 先做 P0-1：扩展 [route_analysis()](../../liuyao/domain/analysis_router.py:90) 标签，并加 3 个路由测试。
2. 再做 P1-5：把 [estimate_yingqi_gen()](../../liuyao/domain/yingqi.py:242) 的无根提示结构化。
3. 再做 P1-6：在 [patterns.py](../../liuyao/domain/patterns.py:1) 输出指导卦/现状卦信号。
4. 最后评估 P0-2：无用动爻转有用，只标记不改判。

## ponytail 结论

最小有用下一步不是写规则，而是补“标签/信号/报告可见性”。等这些缺失知识点能被稳定检测，再决定哪些值得进入 [RuleEngine](../../liuyao/domain/rules/engine.py:21)。
