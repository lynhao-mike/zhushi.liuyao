"""
报告格式化模块 - Report Formatter

将分析结果格式化为中文文本报告。
- format_report: 单视角报告（六部分）
- format_dual_report: 双（多）视角报告（共享+各视角对照）

【输出规范 — 第十章基础知识】
─────────────────────────────────────────────────────
六冲：统一使用"XY互冲"表述，绝不出现"X冲Y"单向写法。
  正确：巳亥互冲、子午互冲、寅申互冲、卯酉互冲、丑未互冲、辰戌互冲
  错误：亥冲巳、午冲子……

月破描述："{爻支}受月破"（月令冲爻）
日冲暗动："{爻支}与{日支}互冲冲起暗动"

三合局输出：注明帝旺归宿，如"巳酉丑合酉金局（能量归酉）"
─────────────────────────────────────────────────────
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
        lines.append("  静卦，无动爻。")
    else:
        for pos, ma in sorted(moving_analyses.items()):
            line = hexagram.lines[pos - 1]
            useful_mark = "有用" if not ma["is_useless"] else f"无用({ma['useless_reason']})"
            lines.append(f"  第{pos}爻 {line.di_zhi} → {ma['bian_zhi']} [{useful_mark}]")
            if ma["趋旺"]:
                lines.append(f"    趋旺: {', '.join(ma['趋旺'])}")
            if ma["趋衰"]:
                lines.append(f"    趋衰: {', '.join(ma['趋衰'])}")

        san_he = dongbian_results.get("san_he_ju", [])
        if san_he:
            for sh in san_he:
                wang_zhi = sh.get("wang_zhi", "")
                wang_note = f"（能量归{wang_zhi}）" if wang_zhi else ""
                members_str = "".join(sh["members"])
                lines.append(
                    f"  三合局: {members_str}合{sh['wu_xing']}局{wang_note}"
                )

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
            lines.append("  暗动/冲起:")
            for ad in an_dong:
                type_label = "【暗动】" if ad["type"] == "暗动" else "【冲起】"
                lines.append(f"    第{ad['position']}爻({ad['di_zhi']}) {type_label} {ad['reason']}")
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
    """
    格式化应期推断段落。
    ★ 候选项已在 yingqi.py 中按"XY互冲"规范生成，此处直接输出。
    """
    lines = []
    lines.append("=" * 60)
    lines.append("【应期推断】")
    lines.append("=" * 60)
    if yingqi_results:
        for yq in yingqi_results:
            lines.append(f"  用神第{yq['position']}爻（{yq['di_zhi']} {yq['liu_qin']}）:")
            for candidate in yq["candidates"]:
                lines.append(f"    · {candidate}")
    else:
        lines.append("  无法推断应期（用神不现）")
    lines.append("")
    return lines


# ============================================================================
# 单视角报告
# ============================================================================

def _format_shuanghe_block(report):
    """格式化双合卦分析段落"""
    lines = []
    if report.shuanghe_type == "normal":
        return lines
    lines.append("=" * 60)
    lines.append("【双合卦分析】")
    lines.append("=" * 60)
    type_label = {"te_zhi": "特指", "jia_jie": "嫁接"}.get(report.shuanghe_type, "")
    lines.append(f"  类型: {type_label}")
    if report.shuanghe_ying_role:
        role = report.shuanghe_ying_role["role"]
        role_label = {"wu_guan": "无关", "dui_bi": "对比", "guan_lian": "关联"}.get(role, role)
        lines.append(f"  应爻参与度: {role_label}")
        lines.append(f"  说明: {report.shuanghe_ying_role['details']}")
    if report.shuanghe_jixiong:
        sj = report.shuanghe_jixiong
        match_label = "一致" if sj["te_zhi_match"] else "偏离"
        lines.append(f"  与指定目标: {match_label}")
        lines.append(f"  应爻强度: {sj['ying_strength']}")
        lines.append(f"  解释: {sj['explanation']}")
    lines.append("")
    return lines


def _format_tuopu_block(report):
    """格式化拓扑用神段落"""
    lines = []
    if not report.tuopu_result:
        return lines
    lines.append("=" * 60)
    lines.append("【拓扑用神选择】")
    lines.append("=" * 60)
    tr = report.tuopu_result
    lines.append(f"  方法: {tr['details']}")
    if tr["lines"]:
        pos_list = [f"第{l.position}爻({l.di_zhi})" for l in tr["lines"]]
        lines.append(f"  选取爻: {', '.join(pos_list)}")
    else:
        lines.append("  选取爻: 无")
    lines.append("")
    return lines


def _format_fushen_block(report):
    """格式化伏神分析段落"""
    lines = []
    if not report.fushen_result:
        return lines
    lines.append("=" * 60)
    lines.append("【伏神分析】")
    lines.append("=" * 60)
    fr = report.fushen_result
    fi = fr["fu_shen_info"]
    lines.append(f"  伏神: {fi['fu_liu_qin']} {fi['fu_tian_gan']}{fi['fu_di_zhi']}"
                 f"({fi['fu_wu_xing']}) 伏于第{fi['position']}爻下")
    lines.append(f"  飞神: {fi['fei_liu_qin']} {fi['fei_di_zhi']}({fi['fei_wu_xing']})")

    fs = fr["fu_status"]
    status_items = []
    if fs["fu_kong"]:
        status_items.append("伏空")
    if fs["fu_po"]:
        status_items.append("伏破")
    if fs["fei_kong"]:
        status_items.append("飞空")
    if fs["fei_po"]:
        status_items.append("飞破")
    if not status_items:
        status_items.append("正常")
    lines.append(f"  状态: {', '.join(status_items)}")

    fj = fr["fu_jixiong"]
    lines.append(f"  吉凶: {fj['ji_xiong']}({fj['pattern']})")
    lines.append(f"  解释: {fj['explanation']}")

    fy = fr["fu_yingqi"]
    lines.append(f"  应期:")
    for cand in fy["candidates"]:
        lines.append(f"    - {cand}")
    lines.append("")
    return lines


def _format_xintai_block(report):
    """格式化心态卦识别段落"""
    lines = []
    if not report.xintai_result:
        return lines
    lines.append("=" * 60)
    lines.append("【心态卦识别】")
    lines.append("=" * 60)
    det = report.xintai_result["detection"]
    ana = report.xintai_result["analysis"]
    lines.append(f"  置信度: {det['confidence']:.0%}")
    lines.append(f"  心态类型: {det['xintai_type']}")
    lines.append(f"  指标:")
    for ind in det["indicators"]:
        lines.append(f"    - {ind}")
    lines.append(f"  判定: {ana['verdict']}")
    lines.append(f"  解释: {ana['explanation']}")
    lines.append("")
    return lines


def _format_guaci_block(report):
    """格式化卦辞寓意段落"""
    lines = []
    if not report.guaci_result:
        return lines
    lines.append("=" * 60)
    lines.append("【卦辞寓意】")
    lines.append("=" * 60)
    gr = report.guaci_result

    # 卦辞解读
    gi = gr.get("guaci_interpretation")
    if gi:
        lines.append(f"  变卦寓意: {', '.join(gi['keywords'])}")
        lines.append(f"  指导: {gi['guidance']}")

    # 六冲/六合
    lc = gr.get("liuchong", {})
    if lc.get("ben_is_liuchong") or lc.get("bian_is_liuchong"):
        lines.append(f"  六冲卦: {lc.get('liuchong_gua', '')}")
        if lc.get("special_pattern"):
            lines.append(f"    特殊模式: {lc['special_pattern']}")
        imp = lc.get("implications", {})
        if imp.get("short_term"):
            lines.append(f"    短期: {imp['short_term']}")

    lh = gr.get("liuhe", {})
    if lh.get("ben_is_liuhe") or lh.get("bian_is_liuhe"):
        lines.append(f"  六合卦: 是")
        imp = lh.get("implications", {})
        if imp.get("short_term"):
            lines.append(f"    短期: {imp['short_term']}")

    # 反吟/伏吟
    ff = gr.get("fanyin_fuyin", {})
    if ff.get("fan_yin"):
        lines.append(f"  反吟: {ff['implications']}")
    if ff.get("fu_yin"):
        lines.append(f"  伏吟: {ff['implications']}")

    # 指导建议
    guidance = gr.get("guidance")
    if guidance:
        lines.append(f"  建议: {guidance}")
    lines.append("")
    return lines


def format_report(report):
    """
    将AnalysisReport格式化为中文文本。
    包含: 排卦/日月/旺衰/动变/吉凶/应期, 以及扩展模块(如有)。
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
    lines.extend(_format_guaci_block(report))
    lines.extend(_format_shuanghe_block(report))
    lines.extend(_format_tuopu_block(report))
    lines.extend(_format_fushen_block(report))
    lines.extend(_format_xintai_block(report))
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
