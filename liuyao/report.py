"""
报告格式化模块 - Report Formatter

将分析结果格式化为中文文本报告。
- format_report: 单视角报告(六部分)
- format_dual_report: 双(多)视角报告(共享+各视角对照)
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
    "shiwu": "失物",
    "other": "综合",
}


# ============================================================================
# 共享段落格式化 (供单视角与双视角共用)
# ============================================================================

def _format_paigua_header(hexagram, question_type, yong_shen_liu_qin=None,
                          yong_shen_lines=None, shi_line=None):
    """格式化排卦信息段落"""
    lines = []
    lines.append("=" * 60)
    lines.append("【排卦信息】")
    lines.append("=" * 60)
    lines.append(f"  本卦: {hexagram.ben_gua_name} ({hexagram.palace_name}宫 - {hexagram.palace_wu_xing})")
    lines.append(f"  变卦: {hexagram.bian_gua_name}")
    lines.append(f"  问事: {QUESTION_TYPE_NAMES.get(question_type, '综合')}")

    if yong_shen_liu_qin is not None:
        lines.append(f"  用神: {yong_shen_liu_qin}")
        if yong_shen_lines:
            yong_pos = [f"第{l.position}爻({l.di_zhi}{l.wu_xing})" for l in yong_shen_lines]
            lines.append(f"  用神爻: {', '.join(yong_pos)}")
        else:
            lines.append("  用神爻: 卦中不现")

    if shi_line:
        lines.append(f"  世爻: 第{shi_line.position}爻"
                     f"({shi_line.di_zhi}{shi_line.wu_xing} "
                     f"{shi_line.liu_qin})")
    lines.append("")
    return lines


def _format_riyue(hexagram):
    """格式化日月信息段落"""
    lines = []
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
    return lines


def _format_wangshuai(hexagram, wangshuai_results):
    """格式化各爻旺衰段落"""
    lines = []
    lines.append("=" * 60)
    lines.append("【各爻旺衰】")
    lines.append("=" * 60)

    for ws in wangshuai_results:
        pos = ws["position"]
        line = hexagram.lines[pos - 1]
        status_mark = {"旺": "+", "衰": "-", "平": "="}[ws["overall"]]

        role = ""
        if line.is_shi:
            role = "[世]"
        elif line.is_ying:
            role = "[应]"

        dong = "动" if line.is_moving else "静"
        kong = "(空)" if line.is_xun_kong else ""

        line_desc = (
            f"  第{pos}爻 {line.liu_qin}{line.di_zhi}{line.wu_xing} "
            f"{dong}{role}{kong}: "
            f"【{ws['overall']}】{status_mark} {ws['details']}"
        )
        lines.append(line_desc)
    lines.append("")
    return lines


def _format_dongbian(hexagram, dongbian_results):
    """格式化动变分析段落"""
    lines = []
    lines.append("=" * 60)
    lines.append("【动变分析】")
    lines.append("=" * 60)

    moving_analyses = dongbian_results.get("moving_analyses", {})

    if not moving_analyses:
        lines.append("  静卦, 无动爻。")
    else:
        for pos, ma in sorted(moving_analyses.items()):
            line = hexagram.lines[pos - 1]
            useful_mark = "有用" if not ma["is_useless"] else f"无用({ma['useless_reason']})"
            lines.append(f"  第{pos}爻 {line.di_zhi} -> {ma['bian_zhi']} [{useful_mark}]")
            if ma["趋旺"]:
                lines.append(f"    趋旺: {', '.join(ma['趋旺'])}")
            if ma["趋衰"]:
                lines.append(f"    趋衰: {', '.join(ma['趋衰'])}")

        san_he = dongbian_results.get("san_he_ju", [])
        if san_he:
            for sh in san_he:
                lines.append(f"  三合局: {' '.join(sh['members'])} 合 {sh['wu_xing']}局")

        interactions = dongbian_results.get("interactions", {})
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

        an_dong = dongbian_results.get("an_dong", [])
        if an_dong:
            lines.append("  暗动:")
            for ad in an_dong:
                lines.append(f"    第{ad['position']}爻({ad['di_zhi']}): {ad['reason']}")
    lines.append("")
    return lines


def _format_jixiong_block(jixiong_result):
    """格式化吉凶判断段落"""
    lines = []
    lines.append("=" * 60)
    lines.append("【吉凶判断】")
    lines.append("=" * 60)
    jx = jixiong_result
    ji_xiong_mark = {"吉": "吉", "凶": "凶", "平": "平"}.get(jx["ji_xiong"], jx["ji_xiong"])
    lines.append(f"  卦局: {jx['pattern']}")
    lines.append(f"  判断: 【{ji_xiong_mark}】")
    lines.append(f"  解释: {jx['explanation']}")
    lines.append("")
    return lines


def _format_yingqi_block(yingqi_results):
    """格式化应期推断段落"""
    lines = []
    lines.append("=" * 60)
    lines.append("【应期推断】")
    lines.append("=" * 60)
    if yingqi_results:
        for yq in yingqi_results:
            lines.append(f"  用神第{yq['position']}爻({yq['di_zhi']} {yq['liu_qin']}):")
            for candidate in yq["candidates"]:
                lines.append(f"    - {candidate}")
    else:
        lines.append("  无法推断应期(用神不现)")
    lines.append("")
    return lines


# ============================================================================
# 单视角报告
# ============================================================================

def format_report(report):
    """
    将AnalysisReport格式化为中文文本(六部分: 排卦/日月/旺衰/动变/吉凶/应期)。
    """
    lines = []
    lines.extend(_format_paigua_header(
        report.hexagram, report.question_type,
        report.yong_shen_liu_qin, report.yong_shen_lines, report.shi_line,
    ))
    lines.extend(_format_riyue(report.hexagram))
    lines.extend(_format_wangshuai(report.hexagram, report.wangshuai_results))
    lines.extend(_format_dongbian(report.hexagram, report.dongbian_results))
    lines.extend(_format_jixiong_block(report.jixiong_result))
    lines.extend(_format_yingqi_block(report.yingqi_results))
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================================
# 双视角报告
# ============================================================================

def _format_perspective_block(idx, perspective):
    """格式化单个视角的吉凶+应期摘要段落"""
    lines = []
    p = perspective

    # 视角标题
    lines.append(f"  ◆ 视角{idx}: {p.perspective_label}")
    lines.append(f"    用神: {p.yong_shen_liu_qin}")

    # 用神爻 (附带身份/动静标记)
    if p.yong_shen_lines:
        yong_pos = []
        for l in p.yong_shen_lines:
            tags = []
            if l.is_moving:
                tags.append("动")
            if l.is_shi:
                tags.append("世")
            if l.is_ying:
                tags.append("应")
            if l.is_xun_kong:
                tags.append("空")
            tag_str = f"[{','.join(tags)}]" if tags else ""
            yong_pos.append(f"第{l.position}爻({l.di_zhi}{l.wu_xing}){tag_str}")
        lines.append(f"    用神爻: {', '.join(yong_pos)}")
    else:
        lines.append("    用神爻: 卦中不现")

    # 吉凶
    jx = p.jixiong_result
    ji_xiong_mark = {"吉": "✓ 吉", "凶": "✗ 凶", "平": "— 平"}.get(
        jx.get("ji_xiong", "平"), jx.get("ji_xiong", "平"))
    lines.append(f"    卦局: {jx.get('pattern', '-')}")
    lines.append(f"    判断: 【{ji_xiong_mark}】")
    lines.append(f"    解释: {jx.get('explanation', '-')}")

    # 应期摘要 (仅展示前2个用神爻, 各最多3个候选)
    if p.yingqi_results:
        lines.append("    应期摘要:")
        for yq in p.yingqi_results[:2]:
            cands = yq.get("candidates", [])
            cand_str = "; ".join(cands[:3])
            lines.append(f"      第{yq['position']}爻({yq['di_zhi']} {yq.get('liu_qin', '')}): {cand_str}")

    return lines


def format_dual_report(dual_report):
    """
    将DualPerspectiveReport格式化为中文文本。

    共享部分(排卦/日月/旺衰/动变)只输出一次, 之后并列展示各视角的
    用神/吉凶/应期, 末尾给出综合结论。
    """
    lines = []
    h = dual_report.hexagram

    # 共享部分: 排卦头(不带用神)
    lines.extend(_format_paigua_header(
        h, dual_report.question_type,
        yong_shen_liu_qin=None, yong_shen_lines=None,
        shi_line=dual_report.shi_line,
    ))

    # 共享: 日月 / 旺衰 / 动变
    lines.extend(_format_riyue(h))
    lines.extend(_format_wangshuai(h, dual_report.wangshuai_results))
    lines.extend(_format_dongbian(h, dual_report.dongbian_results))

    # 双视角对照
    lines.append("=" * 60)
    lines.append(f"【双视角吉凶判断 — 共 {len(dual_report.perspectives)} 个视角】")
    lines.append("=" * 60)

    for i, p in enumerate(dual_report.perspectives, 1):
        lines.append("")
        lines.extend(_format_perspective_block(i, p))

    # 综合结论
    lines.append("")
    lines.append("-" * 60)
    lines.append(f"  ▶ 综合: {dual_report.consensus}")
    lines.append("=" * 60)

    return "\n".join(lines)
