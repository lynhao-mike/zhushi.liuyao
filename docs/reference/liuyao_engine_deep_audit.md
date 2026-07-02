# 六爻卦分析引擎深度审计报告

唯一知识标准：[zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3)

审计对象：分析编排入口 [run_analysis()](liuyao/application/use_cases/analysis.py:69)、路由 [route_analysis()](liuyao/domain/analysis_router.py:90)、旺衰 [analyze_hexagram_wangshuai()](liuyao/domain/wangshuai.py:226)、动变 [analyze_dongbian()](liuyao/domain/dongbian.py:434)、模式 [analyze_all_patterns()](liuyao/domain/patterns.py:867)、吉凶 [judge_jixiong()](liuyao/domain/jixiong.py:393)、应期 [analyze_yingqi()](liuyao/domain/yingqi.py:316)。

## 1. Thesis

高格局判断：当前引擎不是“以 [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) 为源头的系统断卦引擎”，而是“基础流程 + 若干 P0/P1 案例校正规则 + 报告展示层”的混合体。它已经覆盖日月、动变、部分结构模式、通用吉凶和应期，但大量知识点只停留在识别、报告提示或静态理论索引，尚未进入统一裁决流程。

ponytail 判断：不要立刻重写成大而全专家系统。最小可落地方案是加一张“知识点执行登记表”，把每个知识点标记为事实、候选、裁决、应期、报告，并让测试验证调用路径；先补矩阵和缺口，再补规则。

## 2. 覆盖率统计

按 [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) 的主知识簇审计，归并为 32 个可执行知识簇：

| 状态 | 数量 | 占比 | 说明 |
|---|---:|---:|---|
| 覆盖 | 8 | 25.0% | 已进入事实抽取与吉凶/应期调用，且报告可见 |
| 部分覆盖 | 14 | 43.8% | 能识别或提示，但不稳定参与终局裁决，或只覆盖窄场景 |
| 缺失 | 10 | 31.2% | 文档有知识点，代码未见明确触发、调用或协同 |

### 覆盖

1. 日月基础旺衰：由 [yue_jian_wangshuai()](liuyao/domain/wangshuai.py:23)、[ri_chen_wangshuai()](liuyao/domain/wangshuai.py:85)、[analyze_line_wangshuai()](liuyao/domain/wangshuai.py:148) 输出旺衰事实。
2. 动变基础趋势：由 [analyze_moving_line()](liuyao/domain/dongbian.py:55) 输出回头生、回头克、化进、化退、化绝、化破、化出临日月。
3. 有用/无用动爻：由 [analyze_moving_line()](liuyao/domain/dongbian.py:111) 标记，再由 [check_dong_yao_interaction()](liuyao/domain/dongbian.py:156) 过滤作用。
4. 暗动六类：由 [detect_an_dong()](liuyao/domain/dongbian.py:336) 输出，报告在 [\_format_dongbian()](liuyao/interfaces/cli/reporting.py:99) 展示。
5. 三合局优先：由 [find_san_he_ju()](liuyao/domain/dongbian.py:131)、[SanHeJuPriorityRule.evaluate()](liuyao/domain/rules/p0_rules.py:210) 进入吉凶裁决。
6. 动卦通用吉凶卦局：由 [P0_RULES](liuyao/domain/rules/p0_rules.py:1546) 注册多个通用规则，如用神衰败、世用受克、用旺世兴。
7. 静卦三步法：由 [judge_jing_gua()](liuyao/domain/jixiong.py:252) 实现用忌持世、世用生克、用旺世兴。
8. 应期基础公式：由 [estimate_yingqi()](liuyao/domain/yingqi.py:68) 与 [analyze_yingqi()](liuyao/domain/yingqi.py:316) 覆盖旬空、月破、入墓、三绊、反吟、伏吟、动静爻、三合局等。

### 部分覆盖

1. 矛盾趋势辨别：内重外轻由 [SelfChangeTerminalRule.evaluate()](liuyao/domain/rules/p0_rules.py:442) 覆盖，但“动能轨迹终点”“重动轻静”“自占世变特殊六亲定性”未形成统一优先级模型。
2. 复合之动：由 [analyze_compound_movement()](liuyao/domain/dongbian.py:233) 与 [CompoundMovementFinalTargetRule.evaluate()](liuyao/domain/rules/p0_rules.py:280) 覆盖部分连动；但多动场景有保守让路，目标判定对代占/主控性代占仍粗。
3. 世用关系与作用次序：通用规则覆盖部分，但“先用神后世爻”“吉凶与细节分层并存”没有显式双阶段裁决。
4. 意念与代占：只有 [route_analysis()](liuyao/domain/analysis_router.py:90) 的轻量模式标签，缺主控性代占、失控性代占、被动性代占的用神切换。
5. 卦象显示特征：心态卦由 [detect_xintai_gua()](liuyao/domain/patterns.py:469) 与 [MindsetRouteRule.evaluate()](liuyao/domain/rules/p0_rules.py:1307) 部分消费，但“只答心念不答口述”“多问简显”等未落地。
6. 卦意分析法：仅 8 个检测器进入 [analyze_kuayi_patterns()](liuyao/domain/patterns.py:789)，且多数只进报告补充，不统一改判。
7. 月令细节与日令细节：旺衰与应期有覆盖，但“吉凶层面月合只论合旺、日合动爻论绊”等层级差异未集中建模。
8. 旬空：应期层面覆盖 [estimate_yingqi()](liuyao/domain/yingqi.py:95)，吉凶层面“动空化空是假空”等只在特定规则中窄覆盖。
9. 六冲六合与互化：由 [detect_chong_he_gua()](liuyao/domain/patterns.py:318) 识别，主要作为结构提示，较少参与主判。
10. 三墓、三绊、反吟、伏吟：由 [detect_ru_mu()](liuyao/domain/patterns.py:32)、[detect_san_ban()](liuyao/domain/patterns.py:130)、[detect_fan_yin()](liuyao/domain/patterns.py:207)、[detect_fu_yin()](liuyao/domain/patterns.py:272) 识别；只有真绊、伏吟目标爻等少数进入吉凶。
11. 心态卦：已有路由与喜忧神最小规则，但 6 类心态模式未系统覆盖。
12. 变爻为用：由 [TransformedYongMediatorRule.evaluate()](liuyao/domain/rules/p0_rules.py:1048) 窄覆盖，限制在已校验样本。
13. 特殊日月组合：废爻、金刚型、月冲日冲非衰败在 [RuleContext.special_day_month_combo()](liuyao/domain/rules/context.py:137) 与规则层部分覆盖，但特殊组合体系不完整。
14. 近占远占：短占、终身、日/月时效有零散规则，如 [ShortTermNoJinTuiRule.evaluate()](liuyao/domain/rules/p0_rules.py:543)、[LifetimeShixiaoRule.evaluate()](liuyao/domain/rules/p0_rules.py:567)，但长短占是横切维度，未统一进入所有规则。

### 缺失

1. 知识标准自动覆盖账本：现有 [THEORY_RULE_CASE_MAP](liuyao/domain/rules/theory_map.py:18) 只列少量案例驱动规则，不覆盖 [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) 的完整 160 个标题。
2. 客观现状对证机制：日月冲合克扶冲突需结合现状，但当前输入模型没有“现状证据”字段或决策入口。
3. 主控性/失控性/被动性代占分流：代码只有问事类型表 [YONG_SHEN_TABLE](liuyao/domain/jixiong.py:17)，没有代占控制权模型。
4. 用神真假、拓扑取用、藏伏取用：静态索引 [THEORY_MODULES](liuyao/domain/theory.py:564) 有条目，但执行链路未系统消费。
5. 指导卦、现状卦、灾卦、应期卦的专门路由：仅有 [route_analysis()](liuyao/domain/analysis_router.py:90) 的 event/mindset/timing/lifetime/designated_target，粒度不足。
6. 连占卦原则：仅有 [ZaizhanSimplifiedRule.evaluate()](liuyao/domain/rules/p0_rules.py:519) 粗放处理，未形成连占前后卦关系模型。
7. 太过卦象尺度：应期有 [estimate_yingqi_atypical()](liuyao/domain/yingqi.py:283) 的多发逢墓/太过逢克，吉凶主判缺太旺/太衰尺度。
8. 双核卦象完整模型：仅有 [DualCoreDesignatedTargetRule.evaluate()](liuyao/domain/rules/p0_rules.py:855) 的最小干预，未覆盖双核三类对比信息。
9. 无用动爻转有用五种情况：当前先由 [analyze_moving_line()](liuyao/domain/dongbian.py:111) 定无用，再过滤作用，后续“无用转有用”缺统一逆转机制。
10. 化解凶卦办法：无执行或报告结构承载“化解建议”。

## 3. 知识点调用矩阵

| 知识簇 | 标准位置 | 代码入口 | 触发条件 | 推理阶段 | 协同关系 | 覆盖 |
|---|---|---|---|---|---|---|
| 日月旺衰 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) | [analyze_hexagram_wangshuai()](liuyao/domain/wangshuai.py:226) | 每卦必跑 | 事实抽取 | 被动变、规则、应期消费 | 覆盖 |
| 月合/日合差异 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:19) | [yue_jian_wangshuai()](liuyao/domain/wangshuai.py:23)、[ri_chen_wangshuai()](liuyao/domain/wangshuai.py:85) | 月合、静爻日合 | 事实抽取 | 未显式区分吉凶层/应期层 | 部分 |
| 动变趋旺趋衰 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:35) | [analyze_moving_line()](liuyao/domain/dongbian.py:55) | 动爻有变爻 | 动变事实 | 供有用无用与 P0/P1 规则 | 覆盖 |
| 无用动爻 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:47) | [analyze_moving_line()](liuyao/domain/dongbian.py:111) | 回头克、化退、化破、化绝 | 动变事实 | 过滤 [check_dong_yao_interaction()](liuyao/domain/dongbian.py:156) | 覆盖 |
| 矛盾趋势 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:49) | [SelfChangeTerminalRule.evaluate()](liuyao/domain/rules/p0_rules.py:442) | 世/用自身化衰 | 吉凶裁决 | 与时效卦、复合动存在优先级竞争 | 部分 |
| 复合动 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:63) | [analyze_compound_movement()](liuyao/domain/dongbian.py:233) | 多个有用动爻 | 动变聚合 | 三合优先，目标爻由 [\_determine_compound_final_target()](liuyao/domain/dongbian.py:195) 判定 | 部分 |
| 世用关系 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:81) | [P0_RULES](liuyao/domain/rules/p0_rules.py:1546) | 动卦吉凶 | 吉凶裁决 | 依赖旺衰、动爻作用 | 覆盖 |
| 代占 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:97) | [route_analysis()](liuyao/domain/analysis_router.py:90) | 问事类型 | 前置路由 | 只给模式标签，未改取用 | 部分 |
| 卦象显示 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:119) | [detect_xintai_gua()](liuyao/domain/patterns.py:469) | 用神不现且子鬼活跃 | 模式识别 | 被心态规则消费 | 部分 |
| 动卦吉凶通论 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:133) | [judge_dong_gua()](liuyao/domain/jixiong.py:171) | 有动爻 | 吉凶裁决 | 全部经 [RuleEngine.evaluate()](liuyao/domain/rules/engine.py:27) | 覆盖 |
| 动卦特例 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:163) | [CaiKeShiSpecialRule.evaluate()](liuyao/domain/rules/p0_rules.py:1150)、[BingZiSunKeShiRule.evaluate()](liuyao/domain/rules/p0_rules.py:1197)、[XingRenKeShiRule.evaluate()](liuyao/domain/rules/p0_rules.py:1221)、[YouHuanZiSunKeShiRule.evaluate()](liuyao/domain/rules/p0_rules.py:1241) | 财、病、行人、忧患 | 吉凶裁决 | 问事类型强绑定 | 部分 |
| 暗动 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:177) | [detect_an_dong()](liuyao/domain/dongbian.py:336) | 日冲静/动爻 | 动变事实、报告 | 较少参与主判 | 部分 |
| 静卦三步 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:221) | [judge_jing_gua()](liuyao/domain/jixiong.py:252) | 无动爻 | 吉凶裁决 | 使用旺衰与用忌表 | 覆盖 |
| 卦意直读 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:297) | [analyze_kuayi_patterns()](liuyao/domain/patterns.py:789) | 触发各检测器 | 模式识别、报告补充 | 由 [\_attach_jixiong_extras()](liuyao/application/use_cases/analysis.py:58) 附加 | 部分 |
| 月令应期 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:493) | [estimate_yingqi()](liuyao/domain/yingqi.py:68) | 月破、临值、补破 | 应期 | 与旺衰事实协同 | 覆盖 |
| 旬空 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:561) | [estimate_yingqi()](liuyao/domain/yingqi.py:95) | 爻旬空 | 应期 | 吉凶层只窄覆盖 | 部分 |
| 六冲六合 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:604) | [detect_chong_he_gua()](liuyao/domain/patterns.py:318) | 主变卦冲合 | 模式识别、报告 | 主判消费不足 | 部分 |
| 三墓 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:865) | [detect_ru_mu()](liuyao/domain/patterns.py:32) | 日墓、动墓、化墓 | 模式识别、应期 | 吉凶只间接参与 | 部分 |
| 三绊 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:927) | [detect_san_ban()](liuyao/domain/patterns.py:130)、[ZhenBanRule.evaluate()](liuyao/domain/rules/p0_rules.py:976) | 日绊、动绊、化绊 | 模式识别、吉凶 | 真绊才改判 | 部分 |
| 反吟伏吟 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:967) | [detect_fan_yin()](liuyao/domain/patterns.py:207)、[detect_fu_yin()](liuyao/domain/patterns.py:272)、[FuYinTerminalRule.evaluate()](liuyao/domain/rules/p0_rules.py:415) | 反吟/伏吟结构 | 模式、应期、少量吉凶 | 反吟未主判 | 部分 |
| 心态卦 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1211) | [detect_xintai_gua()](liuyao/domain/patterns.py:469)、[MindsetXiYouSignalRule.evaluate()](liuyao/domain/rules/p0_rules.py:1265) | 明/暗心态 | 路由、模式、吉凶 | 跳过普通事卦直断 | 部分 |
| 特殊日月组合 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1413) | [RuleContext.special_day_month_combo()](liuyao/domain/rules/context.py:137) | 废爻、金刚型等 | 吉凶裁决 | 多个 P0/P1 规则消费 | 部分 |
| 灾卦/指导卦/现状卦 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1457) | 无明确统一入口 | 无 | 缺失 | 无协同 | 缺失 |
| 特殊时效卦 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1569) | [YueLingShixiaoRule.evaluate()](liuyao/domain/rules/p0_rules.py:130)、[RiLingShixiaoRule.evaluate()](liuyao/domain/rules/p0_rules.py:154)、[LifetimeShixiaoRule.evaluate()](liuyao/domain/rules/p0_rules.py:567) | 月/日/终身时效 | 吉凶裁决 | 优先级高但分散 | 部分 |
| 连占卦 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1637) | [ZaizhanSimplifiedRule.evaluate()](liuyao/domain/rules/p0_rules.py:519) | question_type=zaizhan | 吉凶粗判 | 无前后卦状态 | 部分 |
| 近占远占 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1741) | [RuleContext.shixiao_context()](liuyao/domain/rules/context.py:158) | 问事类型 | 横切上下文 | 未统一注入所有规则 | 部分 |
| 双核卦象 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1845) | [DualCoreDesignatedTargetRule.evaluate()](liuyao/domain/rules/p0_rules.py:855) | 指定目标问事 | P1 吉凶 | 最小干预 | 部分 |
| 无用转有用 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1915) | 无统一逆转入口 | 无 | 缺失 | 与有用/无用冲突 | 缺失 |
| 化解凶卦 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1953) | 无 | 无 | 缺失 | 无报告段 | 缺失 |
| 应爻特殊分析 | [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:1973) | [find_ying_line()](liuyao/domain/jixiong.py:142)、[RuleContext.intervening_positions](liuyao/domain/rules/context.py:91) | 少数模式 | 辅助事实 | 未成独立模型 | 部分 |

## 4. 推理流程图

```mermaid
flowchart TD
  A[输入 Hexagram + question_type] --> B[route_analysis 前置路由]
  B --> C[determine_yong_shen / find_yong_shen_lines / find_shi_line]
  C --> D[analyze_hexagram_wangshuai 日月旺衰]
  D --> E[analyze_dongbian 动变/暗动/复合动/三合]
  E --> F[analyze_all_patterns 结构模式与卦意]
  F --> G[star_spirits 星煞]
  G --> H[yimao_imagery 报告细节]
  H --> I[judge_jixiong]
  I --> J{动卦?}
  J -->|是| K[RuleContext]
  K --> L[RuleEngine(P0_RULES)]
  L --> M[首个 stop=True 命中终止]
  M --> N[dynamic classic candidates 仅候选]
  J -->|否| O[judge_jing_gua 静卦三步]
  N --> P[analyze_yingqi]
  O --> P
  P --> Q[format_report / readable_report]
```

关键断点：

1. [analyze_all_patterns()](liuyao/domain/patterns.py:867) 产出的多数结构模式没有自动进入 [RuleEngine.evaluate()](liuyao/domain/rules/engine.py:27)，除非特定规则主动读取。
2. [evaluate_dynamic_classic_rules()](liuyao/domain/rules/dynamic_rules.py:136) 只作为候选附加，不改变主判。
3. [THEORY_MODULES](liuyao/domain/theory.py:564) 是静态知识索引，不在 [run_analysis()](liuyao/application/use_cases/analysis.py:69) 中参与调用。

## 5. 问题清单

| 等级 | 问题 | 证据 | 影响 |
|---|---|---|---|
| P0 | 缺完整知识覆盖账本 | [THEORY_RULE_CASE_MAP](liuyao/domain/rules/theory_map.py:18) 只含少量案例映射 | 无法证明已覆盖 [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) 全部知识 |
| P0 | 规则优先级不是理论优先级 | [P0_RULES](liuyao/domain/rules/p0_rules.py:1546) 混合 P0/P1/反馈规则，且优先级区间交叉 | 同一卦可能被较窄反馈规则抢断 |
| P0 | 事实、模式、裁决层边界不清 | [detect_ru_mu()](liuyao/domain/patterns.py:32) 等多数只识别，部分规则才消费 | 知识存在但不参与断卦 |
| P1 | 代占/主控性模型缺失 | [route_analysis()](liuyao/domain/analysis_router.py:90) 只按 question_type 粗路由 | 用神、世应、目标爻可能错位 |
| P1 | 长短占是局部规则，不是全局上下文 | [RuleContext.shixiao_context()](liuyao/domain/rules/context.py:158) 只被部分规则调用 | 暗动、进退、六冲六合、三合三绊的长短占差异无法统一 |
| P1 | 卦意法主要是报告提示 | [analyze_kuayi_patterns()](liuyao/domain/patterns.py:789) 与 [\_attach_jixiong_extras()](liuyao/application/use_cases/analysis.py:58) | 卦意与卦理冲突时缺统一仲裁 |
| P1 | 动态经典规则不改判 | [\_attach_classic_rule_candidates()](liuyao/domain/jixiong.py:234) 明确只附加候选 | 经典知识扩展不能系统影响结果 |
| P2 | 报告缺知识调用追踪 | [\_format_jixiong_block()](liuyao/interfaces/cli/reporting.py:210) 只展示命中规则 | 用户看不到未命中但已检查的规则链 |

## 6. 改进方案

### Clean target

把引擎目标改成“知识标准驱动的分层裁决机”：每个知识点必须登记为事实、模式、裁决、应期、报告之一；每条终局规则必须声明依赖事实、触发条件、优先级层、冲突让路关系、适用长短占。

### Staged clean path

1. 新增知识执行登记表：用普通 Python 字典即可，不要新框架。字段：knowledge_id、source_line、stage、status、code_refs、trigger、consumers、gaps。
2. 把 [THEORY_RULE_CASE_MAP](liuyao/domain/rules/theory_map.py:18) 扩展为全量知识覆盖矩阵，不再只记案例规则。
3. 在 [RuleResult](liuyao/domain/rules/result.py:19) 增加 optional trace 字段或复用 evidence，输出“检查过/命中/让路/未适用”的最小链路。
4. 将 [RuleContext](liuyao/domain/rules/context.py:15) 升级为统一上下文：增加占类模式、时效范围、代占控制权、现状证据四个字段。
5. 先补三类最影响主判的缺口：代占取用、长短占横切、卦意/卦理冲突仲裁。

### Conservative path

继续按反馈样本往 [P0_RULES](liuyao/domain/rules/p0_rules.py:1546) 加规则。短期最省事，但覆盖率无法证明，规则优先级会越来越难维护。

### What not to do

1. 不要把 [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) 直接切成 160 条规则硬塞进 [P0_RULES](liuyao/domain/rules/p0_rules.py:1546)。这会制造更大的优先级灾难。
2. 不要新增复杂 DSL。现有 [RuleEngine](liuyao/domain/rules/engine.py:21) 已足够，先补登记表和测试。
3. 不要让报告层承担推理。报告层如 [\_format_patterns_block()](liuyao/interfaces/cli/reporting.py:253) 只能展示，不能成为隐形规则。
4. 不要把候选经典规则当主判。除非明确进入核心优先级体系，否则 [evaluate_dynamic_classic_rules()](liuyao/domain/rules/dynamic_rules.py:136) 只能提示。

## 7. 验证路径

第一证明点：选 10 个知识簇，每个至少一个测试样例，断言“事实抽取 → 模式识别 → 吉凶规则/应期 → 报告输出”链路完整。优先覆盖：代占、心态卦、特殊日月组合、长短占、卦意/卦理冲突、三绊、复合动、无用转有用、静卦暗动、应爻特殊分析。

可证伪条件：如果补完登记表后发现多数知识点已经有稳定消费者、触发条件和测试覆盖，则“当前不是知识标准驱动引擎”的判断被推翻；反之，若大量条目只能指向静态索引或报告提示，则该判断成立。

## 8. 最小执行清单

1. 建立全量覆盖矩阵，先覆盖 [zhishidianzongjie.md](docs/reference/zhishidianzongjie.md:3) 的 160 个标题，不写新规则。
2. 为每个矩阵条目填 `stage=status=code_refs=trigger=consumer` 五列。
3. 给 [run_analysis()](liuyao/application/use_cases/analysis.py:69) 输出调试 trace，仅在技术报告显示。
4. 重排 [P0_RULES](liuyao/domain/rules/p0_rules.py:1546) 为四层：硬事实终局、占类特例、卦意仲裁、通用兜底。
5. 再补缺失规则，避免继续靠反馈补丁堆叠。
