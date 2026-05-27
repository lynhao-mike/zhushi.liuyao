"""
报告格式化模块 - Report Formatter

将分析结果格式化为中文文本报告, 包含六个部分:
1. 排卦信息
2. 日月信息
3. 各爻旺衰
4. 动变分析
5. 吉凶判断
6. 应期推断
"""

from .data import DI_ZHI_WU_XING


# 问事类型中文名
QUESTION_TYPE_NAMES = {
    "cai": "财运",
    "guan": "官运/工作",
    "hun_male": "婚姻(男问)",
    "hun_female": "婚姻(女问)",
    "bing": "疾病",
    "kaoshi": "考试/文书",
    "zinv": "子女",
    "xingRen": "行人",
    "youHuan": "忧患",
    "other": "综合",
}


def format_report(report):
    """
    将AnalysisReport格式化为中文文本。

    Args:
        report: AnalysisReport对象

    Returns:
        str: 格式化后的中文报告文本
    """
    lines = []
    hexagram = report.hexagram

    # =========================================================================
    # 第一部分: 排卦信息
    # =========================================================================
    lines.append("=" * 60)
    lines.append("【排卦信息】")
    lines.append("=" * 60)
    lines.append(f"  本卦: {hexagram.ben_gua_name} ({hexagram.palace_name}宫 - {hexagram.palace_wu_xing})")
    lines.append(f"  变卦: {hexagram.bian_gua_name}")
    lines.append(f"  问事: {QUESTION_TYPE_NAMES.get(report.question_type, '综合')}")
    lines.append(f"  用神: {report.yong_shen_liu_qin}")

    # 用神爻位
    if report.yong_shen_lines:
        yong_pos = [f"第{l.position}爻({l.di_zhi}{l.wu_xing})" for l in report.yong_shen_lines]
        lines.append(f"  用神爻: {', '.join(yong_pos)}")
    else:
        lines.append("  用神爻: 卦中不现")

    # 世爻
    if report.shi_line:
        lines.append(f"  世爻: 第{report.shi_line.position}爻"
                     f"({report.shi_line.di_zhi}{report.shi_line.wu_xing} "
                     f"{report.shi_line.liu_qin})")
    lines.append("")

    # =========================================================================
    # 第二部分: 日月信息
    # =========================================================================
    lines.append("=" * 60)
    lines.append("【日月信息】")
    lines.append("=" * 60)
    gz = hexagram.gan_zhi
    lines.append(f"  年柱: {gz['year_gan']}{gz['year_zhi']}")
    lines.append(f"  月柱: {gz['month_gan']}{gz['month_zhi']} "
                 f"(月建 {gz['month_zhi']} - {DI_ZHI_WU_XING[gz['month_zhi']]})")
    lines.append(f"  日柱: {gz['day_gan']}{gz['day_zhi']} "
                 f"(日辰 {gz['day_zhi']} - {DI_ZHI_WU_XING[gz['day_zhi']]})")
    lines.append(f"  旬空: {hexagram.xun_kong[0]} {hexagram.xun_kong[1]}")
    lines.append("")

    # =========================================================================
    # 第三部分: 各爻旺衰
    # =========================================================================
    lines.append("=" * 60)
    lines.append("【各爻旺衰】")
    lines.append("=" * 60)

    for ws in report.wangshuai_results:
        pos = ws["position"]
        line = hexagram.lines[pos - 1]
        status_mark = {"旺": "+", "衰": "-", "平": "="}[ws["overall"]]

        # 标注世应
        role = ""
        if line.is_shi:
            role = "[世]"
        elif line.is_ying:
            role = "[应]"

        # 标注动爻
        dong = "动" if line.is_moving else "静"

        # 标注旬空
        kong = "(空)" if line.is_xun_kong else ""

        line_desc = (
            f"  第{pos}爻 {line.liu_qin}{line.di_zhi}{line.wu_xing} "
            f"{dong}{role}{kong}: "
            f"【{ws['overall']}】{status_mark} {ws['details']}"
        )
        lines.append(line_desc)

    lines.append("")

    # =========================================================================
    # 第四部分: 动变分析
    # =========================================================================
    lines.append("=" * 60)
    lines.append("【动变分析】")
    lines.append("=" * 60)

    dongbian = report.dongbian_results
    moving_analyses = dongbian.get("moving_analyses", {})

    if not moving_analyses:
        lines.append("  静卦, 无动爻。")
    else:
        # 动爻分析
        for pos, ma in sorted(moving_analyses.items()):
            line = hexagram.lines[pos - 1]
            useful_mark = "有用" if not ma["is_useless"] else f"无用({ma['useless_reason']})"

            lines.append(f"  第{pos}爻 {line.di_zhi} -> {ma['bian_zhi']} [{useful_mark}]")
            if ma["趋旺"]:
                lines.append(f"    趋旺: {', '.join(ma['趋旺'])}")
            if ma["趋衰"]:
                lines.append(f"    趋衰: {', '.join(ma['趋衰'])}")

        # 三合局
        san_he = dongbian.get("san_he_ju", [])
        if san_he:
            for sh in san_he:
                lines.append(f"  三合局: {' '.join(sh['members'])} 合 {sh['wu_xing']}局")

        # 动爻交互
        interactions = dongbian.get("interactions", {})
        if interactions:
            lines.append("  动爻作用:")
            for pos, inter in sorted(interactions.items()):
                line = hexagram.lines[pos - 1]
                parts = []
                if inter["受生"]:
                    parts.append(f"受生自{', '.join(inter['受生'])}")
                if inter["受克"]:
                    parts.append(f"受克自{', '.join(inter['受克'])}")
                if parts:
                    lines.append(f"    第{pos}爻({line.di_zhi}): {'; '.join(parts)}")

        # 暗动
        an_dong = dongbian.get("an_dong", [])
        if an_dong:
            lines.append("  暗动:")
            for ad in an_dong:
                lines.append(f"    第{ad['position']}爻({ad['di_zhi']}): {ad['reason']}")

    lines.append("")

    # =========================================================================
    # 第五部分: 吉凶判断
    # =========================================================================
    lines.append("=" * 60)
    lines.append("【吉凶判断】")
    lines.append("=" * 60)

    jx = report.jixiong_result
    ji_xiong_mark = {"吉": "吉", "凶": "凶", "平": "平"}[jx["ji_xiong"]]
    lines.append(f"  卦局: {jx['pattern']}")
    lines.append(f"  判断: 【{ji_xiong_mark}】")
    lines.append(f"  解释: {jx['explanation']}")
    lines.append("")

    # =========================================================================
    # 第六部分: 应期推断
    # =========================================================================
    lines.append("=" * 60)
    lines.append("【应期推断】")
    lines.append("=" * 60)

    if report.yingqi_results:
        for yq in report.yingqi_results:
            lines.append(f"  用神第{yq['position']}爻({yq['di_zhi']} {yq['liu_qin']}):")
            # Show top ranked candidates with formula info
            ranked = yq.get("ranked_candidates", [])
            if ranked:
                top_n = ranked[:3]
                for i, c in enumerate(top_n, 1):
                    speed_tag = ""
                    if c.speed_modifier:
                        speed_tag = " [加速]" if c.speed_modifier == "accelerated" else " [减速]"
                    lines.append(
                        f"    {i}. [{c.formula_name}] {c.di_zhi}"
                        f"({c.timing_type}){speed_tag} - {c.reasoning}"
                    )
                if len(ranked) > 3:
                    lines.append(f"    ... 共{len(ranked)}个候选")
            else:
                for candidate in yq["candidates"]:
                    lines.append(f"    - {candidate}")
    else:
        lines.append("  无法推断应期(用神不现)")

    lines.append("")
    lines.append("=" * 60)

    # =========================================================================
    # 第七部分: 双合卦分析 (仅当检测到双合卦时)
    # =========================================================================
    if hasattr(report, 'shuanghe_type') and report.shuanghe_type != "normal":
        lines.append("")
        lines.append("=" * 60)
        lines.append("【双合卦分析】")
        lines.append("=" * 60)

        type_name = "特指" if report.shuanghe_type == "te_zhi" else "嫁接"
        lines.append(f"  类型: {type_name}卦")

        if report.shuanghe_ying_role:
            role = report.shuanghe_ying_role["role"]
            role_names = {"wu_guan": "无关", "dui_bi": "对比", "guan_lian": "关联"}
            lines.append(f"  应爻参与度: {role_names.get(role, role)}")
            lines.append(f"  详情: {report.shuanghe_ying_role['details']}")

        if report.shuanghe_jixiong:
            sj = report.shuanghe_jixiong
            match_str = "是" if sj["te_zhi_match"] else "否"
            lines.append(f"  指定目标一致: {match_str}")
            lines.append(f"  应爻强度: {sj['ying_strength']}")
            lines.append(f"  判断: {sj['explanation']}")

        lines.append("")

    # =========================================================================
    # 第八部分: 拓扑用神 (仅当启用时)
    # =========================================================================
    if hasattr(report, 'tuopu_result') and report.tuopu_result:
        lines.append("")
        lines.append("=" * 60)
        lines.append("【拓扑用神选择】")
        lines.append("=" * 60)

        tr = report.tuopu_result
        method_names = {
            "liu_qin": "标准六亲法",
            "wuxing": "五行类象法",
            "xingsha": "星煞法",
            "liushen": "六神法",
            "none": "无匹配",
        }
        lines.append(f"  选择方法: {method_names.get(tr['method'], tr['method'])}")
        lines.append(f"  详情: {tr['details']}")
        if tr["lines"]:
            tuopu_pos = [f"第{l.position}爻({l.di_zhi}{l.wu_xing})" for l in tr["lines"]]
            lines.append(f"  选取爻位: {', '.join(tuopu_pos)}")
        else:
            lines.append("  选取爻位: 无")

        lines.append("")

    # =========================================================================
    # 伏神分析 (仅当伏神分析结果存在时)
    # =========================================================================
    if hasattr(report, 'fushen_result') and report.fushen_result:
        lines.append("")
        lines.append("=" * 60)
        lines.append("【伏神分析】")
        lines.append("=" * 60)

        fr = report.fushen_result
        fu_info = fr["fu_shen_info"]
        fu_status = fr["fu_status"]
        fu_jixiong = fr["fu_jixiong"]
        fu_yingqi = fr["fu_yingqi"]

        # 伏神位置
        lines.append(f"  伏神: {fu_info['fu_liu_qin']}{fu_info['fu_tian_gan']}"
                     f"{fu_info['fu_di_zhi']}{fu_info['fu_wu_xing']}"
                     f" (藏于第{fu_info['position']}爻下)")
        lines.append(f"  飞神: {fu_info['fei_liu_qin']}"
                     f"{fu_info['fei_di_zhi']}{fu_info['fei_wu_xing']}")

        # 状态
        status_flags = []
        if fu_status["fu_kong"]:
            status_flags.append("伏神旬空")
        if fu_status["fu_po"]:
            status_flags.append("伏神月破")
        if fu_status["fei_kong"]:
            status_flags.append("飞神旬空")
        if fu_status["fei_po"]:
            status_flags.append("飞神月破")
        if not status_flags:
            status_flags.append("正常")
        lines.append(f"  状态: {', '.join(status_flags)}")

        # 吉凶
        lines.append(f"  判断: 【{fu_jixiong['ji_xiong']}】{fu_jixiong['pattern']}")
        lines.append(f"  解释: {fu_jixiong['explanation']}")

        # 应期
        if fu_yingqi["candidates"]:
            lines.append("  应期:")
            for c in fu_yingqi["candidates"]:
                lines.append(f"    - {c}")

        lines.append("")

    return "\n".join(lines)
