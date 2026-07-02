from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "reference" / "zhishidianzongjie.md"
OUTPUT = ROOT / "docs" / "reference" / "zhishidianzongjie_execution_matrix.md"


def classify(line_number: int):
    if line_number < 97:
        if line_number < 35:
            return (
                "事实抽取",
                "覆盖",
                "[analyze_hexagram_wangshuai()](../../liuyao/domain/wangshuai.py:226); [analyze_line_wangshuai()](../../liuyao/domain/wangshuai.py:148)",
                "每卦必跑",
                "动变、吉凶、应期",
                "需补月合/日合分层差异",
            )
        if line_number < 63:
            return (
                "动变/裁决",
                "部分覆盖",
                "[analyze_moving_line()](../../liuyao/domain/dongbian.py:55); [SelfChangeTerminalRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:442)",
                "动爻或矛盾趋势",
                "RuleEngine",
                "缺统一冲突仲裁",
            )
        if line_number < 81:
            return (
                "动变聚合",
                "部分覆盖",
                "[analyze_compound_movement()](../../liuyao/domain/dongbian.py:233); [CompoundMovementFinalTargetRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:280)",
                "多动爻",
                "吉凶裁决",
                "代占目标粗",
            )
        return (
            "吉凶裁决",
            "覆盖",
            "[P0_RULES](../../liuyao/domain/rules/p0_rules.py:1546); [judge_dong_gua()](../../liuyao/domain/jixiong.py:171)",
            "动卦",
            "RuleEngine",
            "需显式先用后世",
        )
    if line_number < 133:
        return (
            "前置路由",
            "部分覆盖",
            "[route_analysis()](../../liuyao/domain/analysis_router.py:90); [detect_xintai_gua()](../../liuyao/domain/patterns.py:469)",
            "question_type/用神不现",
            "模式识别、心态规则",
            "代占控制权缺失",
        )
    if line_number < 177:
        return (
            "吉凶裁决",
            "覆盖",
            "[judge_dong_gua()](../../liuyao/domain/jixiong.py:171); [P0_RULES](../../liuyao/domain/rules/p0_rules.py:1546)",
            "有动爻",
            "RuleEngine",
            "占类特例仍分散",
        )
    if line_number < 221:
        return (
            "动变事实/应期",
            "部分覆盖",
            "[detect_an_dong()](../../liuyao/domain/dongbian.py:336); [estimate_yingqi()](../../liuyao/domain/yingqi.py:68)",
            "日冲/旬空/月气",
            "报告、应期",
            "长短占未全局化",
        )
    if line_number < 297:
        return (
            "静卦裁决/应期",
            "覆盖",
            "[judge_jing_gua()](../../liuyao/domain/jixiong.py:252); [analyze_yingqi()](../../liuyao/domain/yingqi.py:316)",
            "无动爻",
            "吉凶、应期",
            "静卦暗动主判不足",
        )
    if line_number < 473:
        return (
            "模式识别/报告",
            "部分覆盖",
            "[analyze_kuayi_patterns()](../../liuyao/domain/patterns.py:789); [_attach_jixiong_extras()](../../liuyao/application/use_cases/analysis.py:58)",
            "卦意检测器命中",
            "报告补充、少量规则",
            "多数不改判",
        )
    if line_number < 795:
        return (
            "事实/模式/应期",
            "部分覆盖",
            "[analyze_hexagram_wangshuai()](../../liuyao/domain/wangshuai.py:226); [detect_chong_he_gua()](../../liuyao/domain/patterns.py:318); [estimate_yingqi()](../../liuyao/domain/yingqi.py:68)",
            "日月冲合空破三合",
            "模式、应期",
            "吉凶消费不足",
        )
    if line_number < 1073:
        return (
            "模式识别/应期",
            "部分覆盖",
            "[detect_ru_mu()](../../liuyao/domain/patterns.py:32); [detect_san_ban()](../../liuyao/domain/patterns.py:130); [detect_fan_yin()](../../liuyao/domain/patterns.py:207); [detect_fu_yin()](../../liuyao/domain/patterns.py:272)",
            "墓绊反吟伏吟",
            "应期、少量规则",
            "反吟/墓主判不足",
        )
    if line_number < 1149:
        return (
            "应期",
            "覆盖",
            "[analyze_yingqi()](../../liuyao/domain/yingqi.py:316); [estimate_yingqi()](../../liuyao/domain/yingqi.py:68)",
            "用神/模式结果",
            "报告",
            "主从/众寡原则未显式",
        )
    if line_number < 1413:
        return (
            "路由/取用/心态",
            "部分覆盖",
            "[route_analysis()](../../liuyao/domain/analysis_router.py:90); [MindsetXiYouSignalRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:1265); [TransformedYongMediatorRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:1048)",
            "心态/变爻用神",
            "RuleEngine、报告",
            "真假用神/拓扑取用缺",
        )
    if line_number < 1640:
        if line_number < 1457:
            return (
                "吉凶裁决",
                "部分覆盖",
                "[RuleContext.special_day_month_combo()](../../liuyao/domain/rules/context.py:137); [YueLingShixiaoRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:130)",
                "特殊日月/时效",
                "RuleEngine",
                "特殊组合不完整",
            )
        return (
            "路由/缺失",
            "缺失",
            "[route_analysis()](../../liuyao/domain/analysis_router.py:90)",
            "灾卦/指导卦/现状卦/连占",
            "无稳定消费者",
            "需新增最小模式标签",
        )
    if line_number < 1845:
        return (
            "横切上下文",
            "部分覆盖",
            "[RuleContext.shixiao_context()](../../liuyao/domain/rules/context.py:158); [ShortTermNoJinTuiRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:543)",
            "长短占/太过/独发",
            "少量规则、应期",
            "未全局注入",
        )
    if line_number < 2027:
        return (
            "缺失/部分覆盖",
            "缺失",
            "[DualCoreDesignatedTargetRule.evaluate()](../../liuyao/domain/rules/p0_rules.py:855)",
            "双核/无用转有用/化解/应爻",
            "少量规则",
            "体系缺失",
        )
    return (
        "案例补充规则",
        "部分覆盖",
        "[THEORY_RULE_CASE_MAP](../../liuyao/domain/rules/theory_map.py:18); [P0_RULES](../../liuyao/domain/rules/p0_rules.py:1546)",
        "案例校正规则",
        "RuleEngine/测试",
        "只覆盖已登记案例",
    )


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    headings = [
        (index + 1, line.strip().lstrip("#").strip())
        for index, line in enumerate(lines)
        if line.lstrip().startswith("#")
    ]

    rows = []
    counts = {"覆盖": 0, "部分覆盖": 0, "缺失": 0}
    for index, (line_number, title) in enumerate(headings, 1):
        stage, status, code_refs, trigger, consumer, gap = classify(line_number)
        counts[status] += 1
        rows.append(
            "| K{index:03d} | [zhishidianzongjie.md:{line}](zhishidianzongjie.md:{line}) | {title} | {stage} | {status} | {refs} | {trigger} | {consumer} | {gap} |".format(
                index=index,
                line=line_number,
                title=markdown_escape(title),
                stage=stage,
                status=status,
                refs=code_refs,
                trigger=markdown_escape(trigger),
                consumer=markdown_escape(consumer),
                gap=markdown_escape(gap),
            )
        )

    content = "\n".join(
        [
            "# zhishidianzongjie 知识执行矩阵",
            "",
            "来源：[zhishidianzongjie.md](zhishidianzongjie.md:3)",
            "",
            "生成原则：只做覆盖账本，不改规则引擎；状态为初始机器归类，后续逐项人工校准。",
            "",
            f"统计：标题节点 {len(headings)} 个；覆盖 {counts['覆盖']} 个；部分覆盖 {counts['部分覆盖']} 个；缺失 {counts['缺失']} 个。",
            "",
            "| ID | 标准位置 | 知识点 | 阶段 | 状态 | 代码引用 | 触发条件 | 消费者 | 缺口/备注 |",
            "|---|---|---|---|---|---|---|---|---|",
            *rows,
            "",
        ]
    )
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(headings)} headings)")


if __name__ == "__main__":
    main()
