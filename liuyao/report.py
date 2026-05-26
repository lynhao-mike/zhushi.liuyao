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

            # Show event duration if available
            if "event_duration" in yq:
                dur_names = {"short": "短事", "medium": "常事", "long": "长事"}
                dur = dur_names.get(yq["event_duration"], yq["event_duration"])
                lines.append(f"    事件类型: {dur}")

            # Show ranked candidates if available
            if "ranked_candidates" in yq and yq["ranked_candidates"]:
                lines.append("    推荐应期:")
                for i, rc in enumerate(yq["ranked_candidates"][:5]):
                    formulas_str = ", ".join(rc["formulas"]) if rc["formulas"] else ""
                    lines.append(
                        f"      {i+1}. {rc['timing']} "
                        f"(评分:{rc['score']})"
                        f"{' [' + formulas_str + ']' if formulas_str else ''}"
                    )
            else:
                # Fallback to original candidates
                for candidate in yq["candidates"]:
                    lines.append(f"    - {candidate}")

            # Show modifiers if present
            if "modifiers" in yq:
                mod = yq["modifiers"]
                if mod.get("acceleration"):
                    lines.append(
                        f"    加速信号: {', '.join(mod['acceleration'])}")
                if mod.get("deceleration"):
                    lines.append(
                        f"    减速信号: {', '.join(mod['deceleration'])}")

            # Show yuan_shen timing if present
            if "yuan_shen_timing" in yq and yq["yuan_shen_timing"]:
                lines.append("    元神应期:")
                for yst in yq["yuan_shen_timing"]:
                    lines.append(
                        f"      {yst['timing']} ({yst['formula']})")
    else:
        lines.append("  无法推断应期(用神不现)")

    lines.append("")
    lines.append("=" * 60)

    # =========================================================================
    # 第七部分: 连动分析
    # =========================================================================
    if hasattr(report, 'liandong_results') and report.liandong_results:
        ldr = report.liandong_results
        has_content = (ldr.get("san_he_jixiong") or
                       ldr.get("jia_san_he") or
                       ldr.get("liandong_chains"))
        if has_content:
            lines.append("")
            lines.append("=" * 60)
            lines.append("【连动分析】")
            lines.append("=" * 60)

            # 三合局吉凶
            san_he_jx = ldr.get("san_he_jixiong", [])
            if san_he_jx:
                lines.append("  三合局吉凶:")
                for shj in san_he_jx:
                    ji_mark = {"吉": "吉", "凶": "凶", "平": "平"}[shj["ji_xiong"]]
                    lines.append(
                        f"    {' '.join(shj['members'])}合{shj['wu_xing']}局 "
                        f"【{ji_mark}】 {shj['pattern']}")
                    lines.append(f"      {shj['explanation']}")

            # 假三合局
            jia_sh = ldr.get("jia_san_he", [])
            if jia_sh:
                lines.append("  假三合局:")
                for jsh in jia_sh:
                    lines.append(
                        f"    {' '.join(jsh['members'])}合{jsh['wu_xing']}局 "
                        f"(假) - {jsh['reason']}")

            # 连动链
            chains = ldr.get("liandong_chains", [])
            if chains:
                lines.append("  连动链:")
                for chain in chains:
                    lines.append(
                        f"    [{chain['type']}] "
                        f"{' -> '.join(chain['chain'])} -> {chain['target']}")
                    lines.append(f"      效果: {chain['effect']}")
                    lines.append(f"      {chain['explanation']}")

            if ldr.get("san_he_priority"):
                lines.append("  注: 三合局优先于单爻判断")
            if ldr.get("san_he_override_individual"):
                lines.append("  注: 三合局成员不受个体规则(回头克/化破绝)约束(世爻除外)")

    # =========================================================================
    # 第八部分: 六冲六合卦分析
    # =========================================================================
    if report.liuchong_liuhe_results:
        lines.append("")
        lines.append("=" * 60)
        lines.append("【六冲六合卦分析】")
        lines.append("=" * 60)

        lcr = report.liuchong_liuhe_results

        # 六冲卦
        liu_chong = lcr.get("liu_chong", {})
        if liu_chong.get("is_liu_chong"):
            chong_type = liu_chong.get("type", "")
            type_map = {"main": "主卦六冲", "bian": "变卦六冲",
                        "both": "主卦+变卦六冲"}
            lines.append(f"  六冲卦: {type_map.get(chong_type, chong_type)}")

        # 六合卦
        liu_he = lcr.get("liu_he", {})
        if liu_he.get("is_liu_he"):
            he_type = liu_he.get("type", "")
            type_map = {"main": "主卦六合", "bian": "变卦六合",
                        "both": "主卦+变卦六合"}
            lines.append(f"  六合卦: {type_map.get(he_type, he_type)}")

        # 六冲六合互化
        huhua = lcr.get("chong_he_huhua", {})
        if huhua.get("pattern"):
            lines.append(f"  互化模式: {huhua['pattern']}")
            lines.append(f"    含义: {huhua['meaning']}")

        # 动爻趋合
        quhe = lcr.get("dong_yao_quhe", [])
        if quhe:
            lines.append("  动爻趋合:")
            for q in quhe:
                lines.append(
                    f"    第{q['dong_position']}爻({q['dong_zhi']}) "
                    f"趋合 第{q['jing_position']}爻({q['jing_zhi']}) "
                    f"- {q['type']}: {q['note']}")

        # 日绊
        ri_ban = lcr.get("ri_ban", [])
        if ri_ban:
            lines.append("  日绊:")
            for rb in ri_ban:
                lines.append(
                    f"    第{rb['position']}爻({rb['di_zhi']}) "
                    f"{rb['ban_target']}被日合 - {rb['ban_type']}: "
                    f"{rb['note']}")

        if (not liu_chong.get("is_liu_chong") and
                not liu_he.get("is_liu_he") and
                not huhua.get("pattern") and not quhe and not ri_ban):
            lines.append("  无六冲六合卦特征")

    # =========================================================================
    # 第九部分: 旬空分析
    # =========================================================================
    if report.xunkong_results:
        lines.append("")
        lines.append("=" * 60)
        lines.append("【旬空分析】")
        lines.append("=" * 60)

        xkr = report.xunkong_results
        kong_lines_analysis = xkr.get("kong_lines", [])

        if not kong_lines_analysis:
            lines.append("  卦中无旬空爻")
        else:
            for kl in kong_lines_analysis:
                role = ""
                if kl.get("is_shi"):
                    role = "[世]"
                elif kl.get("is_yong"):
                    role = "[用]"

                jia_kong = kl.get("jia_kong", {})
                kong_status = "假空" if jia_kong.get("is_jia_kong") else "待定"

                zhen_kong = kl.get("zhen_kong")
                if zhen_kong and zhen_kong.get("is_zhen_kong"):
                    kong_status = "真空"
                elif zhen_kong and not zhen_kong.get("is_zhen_kong"):
                    kong_status = "假空"

                lines.append(
                    f"  第{kl['position']}爻 {kl['liu_qin']}{kl['di_zhi']}"
                    f"{role}: 【{kong_status}】")

                if jia_kong.get("is_jia_kong"):
                    lines.append(f"    {jia_kong['reason']}")
                elif zhen_kong:
                    lines.append(f"    {zhen_kong['reason']}")

                chu_kong = kl.get("chu_kong", {})
                if chu_kong.get("tian_kong"):
                    lines.append(
                        f"    出空: {chu_kong['tian_kong']}; "
                        f"{chu_kong['chong_kong']}; {chu_kong['chu_xun']}")

        # 特殊应用
        specials = xkr.get("specials", [])
        if specials:
            lines.append("  特殊应用:")
            for sp in specials:
                lines.append(f"    [{sp['type']}] {sp['description']}")
                if sp.get("note"):
                    lines.append(f"      注: {sp['note']}")

    # =========================================================================
    # 第十部分: 月破真假分析
    # =========================================================================
    if report.yuepo_results:
        ypr = report.yuepo_results
        if ypr.get("has_po") or ypr.get("maodun_qushi"):
            lines.append("")
            lines.append("=" * 60)
            lines.append("【月破真假分析】")
            lines.append("=" * 60)

            po_analyses = ypr.get("po_analyses", [])
            if po_analyses:
                for pa in po_analyses:
                    analysis = pa.get("analysis", {})
                    po_type = "真破" if analysis.get("is_zhen_po") else "假破"
                    target = "本爻" if pa.get("is_yue_po") else "变爻"
                    lines.append(
                        f"  第{pa['position']}爻({pa['di_zhi']}) "
                        f"{target}月破: 【{po_type}】")
                    lines.append(f"    {analysis.get('reason', '')}")

            # 矛盾趋势
            maodun = ypr.get("maodun_qushi", [])
            if maodun:
                lines.append("  矛盾趋势分析:")
                for md in maodun:
                    shi_mark = "[世]" if md.get("is_shi") else ""
                    lines.append(
                        f"    第{md['position']}爻({md['di_zhi']})"
                        f"{shi_mark}:")
                    lines.append(
                        f"      趋旺: {', '.join(md['wang_reasons'])}")
                    lines.append(
                        f"      趋衰: {', '.join(md['shuai_reasons'])}")
                    lines.append(
                        f"      原则: {md['principle']}")
                    lines.append(
                        f"      结论: {md['conclusion']}")

    lines.append("")
    lines.append("=" * 60)

    # =========================================================================
    # 第十一部分: 卦意分析
    # =========================================================================
    if hasattr(report, 'guayi_results') and report.guayi_results:
        lines.append("")
        lines.append("=" * 60)
        lines.append("【卦意分析】")
        lines.append("=" * 60)

        for finding in report.guayi_results:
            ji_mark = {"吉": "吉", "凶": "凶", "中性": "中"}[finding["ji_xiong"]]
            lines.append(
                f"  [{finding['method']}] 【{ji_mark}】")
            lines.append(f"    {finding['description']}")
            lines.append(f"    {finding['details']}")

    # =========================================================================
    # 第十二部分: 世爻特殊规则
    # =========================================================================
    if hasattr(report, 'shiyao_analysis') and report.shiyao_analysis:
        sa = report.shiyao_analysis
        if sa.get("override_reason") and sa["override_reason"] != "世爻未动":
            lines.append("")
            lines.append("=" * 60)
            lines.append("【世爻特殊规则】")
            lines.append("=" * 60)

            if sa.get("hua_po_is_false"):
                lines.append("  世爻化破: 不论破(假破)")
            if sa.get("liu_qin_priority"):
                lines.append(f"  六亲定性: {sa['liu_qin_priority']}")
            lines.append(f"  规则: {sa['override_reason']}")
            if sa.get("effective_trend"):
                lines.append(f"  趋势: {sa['effective_trend']}")

    return "\n".join(lines)
