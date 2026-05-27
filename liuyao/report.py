"""
报告格式化模块 - Report Formatter

将分析结果格式化为中文文本报告。
- format_report:          单视角技术报告(六部分，供研习/存档)
- format_dual_report:     双(多)视角技术报告(共享+各视角对照)
- format_readable_report: 可读性断卦报告(面向客户，供易师直接解读)
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
            if yq.get('position', 0) > 0:
                lines.append(
                    f"  用神第{yq['position']}爻({yq['di_zhi']} {yq['liu_qin']}):"
                )
            else:
                lines.append(f"  {yq.get('liu_qin', '附加')}应期:")
            for candidate in yq["candidates"]:
                lines.append(f"    - {candidate}")
    else:
        lines.append("  无法推断应期(用神不现)")
    lines.append("")
    return lines


def _format_patterns_block(patterns_results):
    """格式化卦象结构模式识别段落 (入墓/三绊/反吟/伏吟/六冲六合卦/三刑/六害/三会/心态卦/卦意法)"""
    if not patterns_results:
        return []

    lines = []
    lines.append("=" * 60)
    lines.append("【卦象结构模式】")
    lines.append("=" * 60)

    # 六冲六合卦
    chong_he = patterns_results.get("chong_he_gua", {})
    if chong_he and chong_he.get("pattern"):
        lines.append(f"  ◆ 卦体特征: {chong_he['pattern']}")
        if chong_he.get("implication"):
            lines.append(f"      {chong_he['implication']}")

    # 反吟
    fan_yin = patterns_results.get("fan_yin", {})
    if fan_yin:
        fan_yin_signals = []
        if fan_yin.get("卦象反吟"):
            fan_yin_signals.append("卦象反吟(主变冲)")
        if fan_yin.get("卦宫反吟"):
            fan_yin_signals.extend(fan_yin["卦宫反吟"])
        if fan_yin.get("爻动反吟"):
            for pp in fan_yin["爻动反吟"]:
                fan_yin_signals.append(f"爻动反吟(第{pp[0]}↔{pp[1]}爻冲)")
        if fan_yin.get("爻化反吟"):
            for p in fan_yin["爻化反吟"]:
                fan_yin_signals.append(f"爻化反吟(第{p}爻动变冲)")
        if fan_yin_signals:
            lines.append("  ◆ 反吟: " + ", ".join(fan_yin_signals))
            lines.append("      寓意反复折腾, 事多周折; 占功名仕途反复, "
                         "占财物聚散无常, 占婚姻感情周折")

    # 伏吟
    fu_yin = patterns_results.get("fu_yin", {})
    if fu_yin:
        fu_signals = []
        if fu_yin.get("内卦伏吟"):
            fu_signals.append("内卦伏吟")
        if fu_yin.get("外卦伏吟"):
            fu_signals.append("外卦伏吟")
        if fu_yin.get("爻动伏吟"):
            for p in fu_yin["爻动伏吟"]:
                fu_signals.append(f"第{p}爻爻动伏吟")
        if fu_signals:
            lines.append("  ◆ 伏吟: " + ", ".join(fu_signals))
            lines.append("      寓意呻吟、哀怨、不宁; 占功名宦途哀怨, "
                         "求财利进退两难, 占行人在外忧愁")

    # 入墓
    ru_mu_list = patterns_results.get("ru_mu", [])
    if ru_mu_list:
        lines.append("  ◆ 入墓:")
        for mu in ru_mu_list:
            real_mark = "(真墓)" if mu["is_real"] else "(假墓)"
            lines.append(
                f"      第{mu['position']}爻{mu['line_zhi']} - {mu['mu_type']}"
                f" {real_mark}: {mu['reason']}"
            )

    # 三绊
    san_ban = patterns_results.get("san_ban", [])
    if san_ban:
        lines.append("  ◆ 三绊:")
        for ban in san_ban:
            lines.append(f"      {ban['ban_type']}: {ban['reason']}")

    # 三刑
    san_xing = patterns_results.get("san_xing", [])
    if san_xing:
        lines.append("  ◆ 三刑(细节):")
        for xing in san_xing:
            positions = ",".join(f"第{p}爻" for p in xing["positions"])
            lines.append(
                f"      {xing['type']} ({'-'.join(xing['group'])}): {positions}"
            )

    # 六害
    liu_hai = patterns_results.get("liu_hai", [])
    if liu_hai:
        lines.append("  ◆ 六害(细节):")
        for hai in liu_hai:
            lines.append(f"      {hai['reason']}")

    # 三会局 (细节层面)
    san_hui = patterns_results.get("san_hui", [])
    if san_hui:
        lines.append("  ◆ 三会局(细节):")
        for hui in san_hui:
            lines.append(
                f"      {' '.join(hui['members'])} 会 {hui['wu_xing']}局"
            )

    # 心态卦
    xintai = patterns_results.get("xintai_gua", {})
    if xintai and xintai.get("is_xintai"):
        lines.append(f"  ◆ {xintai['type']}心态卦: 喜神={xintai['xi_shen']}, "
                     f"忧神={xintai['you_shen']}")
        for sig in xintai.get("signals", []):
            lines.append(f"      信号: {sig}")
        if xintai.get("implication"):
            lines.append(f"      {xintai['implication']}")

    # 卦意分析法
    kuayi = patterns_results.get("kuayi_patterns", [])
    if kuayi:
        lines.append("  ◆ 卦意分析法识别:")
        for k in kuayi:
            lines.append(
                f"      {k['method']} → 【{k['result']}】 {k['detail']}"
            )

    if len(lines) <= 3:
        # 没有任何模式信号
        lines.append("  无特殊结构模式")

    lines.append("")
    return lines


def _format_star_spirits_block(star_spirits, hexagram):
    """格式化13星煞展示 (细节层面)"""
    if not star_spirits:
        return []

    lines = []
    lines.append("=" * 60)
    lines.append("【神煞 — 实用十三星煞】")
    lines.append("=" * 60)

    # 收集卦中各爻的地支
    line_zhis = {l.position: l.di_zhi for l in hexagram.lines}

    # 标准化展示, 列出星煞与对应卦中爻
    name_order = [
        "贵人", "禄神", "羊刃", "文昌", "驿马",
        "桃花", "将星", "劫煞", "华盖", "谋星",
        "天医", "天喜", "灾煞",
    ]

    for name in name_order:
        zhi = star_spirits.get(name, "")
        if not zhi:
            continue
        zhi_list = zhi if isinstance(zhi, (tuple, list)) else (zhi,)
        # 找出对应的爻
        matched = []
        for pos, lzhi in line_zhis.items():
            if lzhi in zhi_list:
                matched.append(f"第{pos}爻")
        zhi_str = "/".join(zhi_list)
        if matched:
            lines.append(f"  {name:<3}: {zhi_str}  → 入卦于 {', '.join(matched)}")
        else:
            lines.append(f"  {name:<3}: {zhi_str}  (不入卦)")

    lines.append("")
    return lines


def _format_kuayi_supplements(jixiong_result):
    """格式化卦意法补充判断段落"""
    kuayi = jixiong_result.get("kuayi_supplements", [])
    if not kuayi:
        return []
    lines = []
    lines.append("  - 卦意法补充:")
    for k in kuayi:
        lines.append(
            f"      {k['method']} → 【{k['result']}】 {k['detail']}"
        )
    return lines


def _format_fushen_block(fushen_analysis):
    """
    格式化伏神(藏伏)分析段落.

    据《古筮真诠》第三十九章, 仅当用神不上卦时启用.
    """
    if not fushen_analysis:
        return []

    fa = fushen_analysis
    fi = fa["fushen_info"]
    cang = fi["cang_yao"]
    fei = fi["fei_shen"]

    lines = []
    lines.append("=" * 60)
    lines.append("【伏神分析 — 用神不上卦, 启用藏伏理论】")
    lines.append("=" * 60)
    lines.append(
        f"  伏神: {cang.liu_qin}{cang.tian_gan}{cang.di_zhi}{cang.wu_xing} "
        f"(伏于第{fi['position']}爻)"
    )
    lines.append(
        f"  飞神: 第{fi['position']}爻 {fei.liu_qin}{fei.tian_gan}"
        f"{fei.di_zhi}{fei.wu_xing} (盖在伏神上)"
    )

    # 飞伏关系 (信息性, 非主导)
    rel = fa.get("fei_fu_relation", "")
    alias = fa.get("fei_fu_alias", "")
    impl = fa.get("fei_fu_implication", "")
    lines.append(f"  飞伏关系: {rel} (\"{alias}\") - {impl}")

    # 卦理定性
    lines.append("  卦理定性:")
    for ev in fa.get("jixiong_evaluations", []):
        result_mark = {
            "凶": "✗ 凶",
            "吉": "✓ 吉",
            "吉(短期)": "✓ 吉(短期)",
            "中性": "— 中性",
        }.get(ev["result"], ev["result"])
        lines.append(f"    · {ev['rule']}: 【{result_mark}】 {ev['detail']}")

    # 应期 (应期块也会单独展示, 这里仅做提示)
    lines.append("  应期总则: 冲飞露伏 (《黄金策》: 伏无提挈终徒尔, 飞不推开亦枉然)")

    if cang.is_xun_kong:
        lines.append("  ⚠ 伏神旬空")

    short_term = "短期" if fa.get("is_short_term") else "长期"
    lines.append(f"  事态时效: {short_term}事占")
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
    # 新增: 卦象结构模式 (入墓/三绊/反吟/伏吟/六冲六合卦/三刑/六害/三会/心态卦/卦意法)
    if getattr(report, "patterns_results", None):
        lines.extend(_format_patterns_block(report.patterns_results))
    # 新增: 13星煞
    if getattr(report, "star_spirits", None):
        lines.extend(_format_star_spirits_block(report.star_spirits, report.hexagram))
    # 新增: 伏神分析 (仅用神不上卦时)
    if getattr(report, "fushen_analysis", None):
        lines.extend(_format_fushen_block(report.fushen_analysis))
    lines.extend(_format_jixiong_block(report.jixiong_result))
    # 新增: 卦意法补充判断 (附在吉凶判断块)
    kuayi_lines = _format_kuayi_supplements(report.jixiong_result)
    if kuayi_lines:
        lines.extend(kuayi_lines)
        lines.append("")
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
        # 用神不上卦, 显示伏神信息
        fa = getattr(p, "fushen_analysis", None)
        if fa:
            fi = fa["fushen_info"]
            cang = fi["cang_yao"]
            kong_mark = "[空]" if cang.is_xun_kong else ""
            lines.append(
                f"    用神爻: 卦中不现, 伏于第{fi['position']}爻下"
                f"({cang.di_zhi}{cang.wu_xing}){kong_mark}"
            )
            lines.append(
                f"    飞伏关系: {fa.get('fei_fu_relation', '')}"
                f" ({fa.get('fei_fu_alias', '')})"
            )
        else:
            lines.append("    用神爻: 卦中不现, 藏爻中亦无")

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

    # 卦意法补充提示 (各视角不同)
    kuayi = (p.jixiong_result or {}).get("kuayi_supplements", [])
    if kuayi:
        lines.append("    卦意法补充:")
        for k in kuayi:
            lines.append(f"      · {k['method']} → 【{k['result']}】 {k['detail']}")

    # 伏神卦理定性补充
    fa = getattr(p, "fushen_analysis", None)
    if fa:
        evals = fa.get("jixiong_evaluations", [])
        non_neutral = [e for e in evals if e["result"] != "中性"]
        if non_neutral:
            lines.append("    伏神卦理:")
            for ev in non_neutral:
                rmark = {"凶": "✗ 凶", "吉": "✓ 吉", "吉(短期)": "✓ 吉(短期)"}.get(
                    ev["result"], ev["result"])
                lines.append(f"      · {ev['rule']} 【{rmark}】 {ev['detail']}")

    # 视角专属模式信号 (心态卦 / 间爻阻隔 / 反伏吟)
    pat = getattr(p, "patterns_results", None) or {}
    xt = pat.get("xintai_gua", {})
    if xt and xt.get("is_xintai"):
        lines.append(f"    心态卦: {xt['type']}心态卦 (喜神={xt['xi_shen']}, 忧神={xt['you_shen']})")

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

    # 共享: 13星煞 (各视角共用)
    if getattr(dual_report, "star_spirits", None):
        lines.extend(_format_star_spirits_block(dual_report.star_spirits, h))

    # 共享: 卦象结构模式 (取第一个视角的 patterns - 结构性模式与用神无关)
    if dual_report.perspectives:
        first_pat = getattr(dual_report.perspectives[0], "patterns_results", {}) or {}
        # 仅展示与用神无关的结构性模式 (排除 xintai_gua 和 kuayi_patterns)
        structural_pat = {
            k: v for k, v in first_pat.items()
            if k not in ("xintai_gua", "kuayi_patterns")
        }
        if structural_pat:
            lines.extend(_format_patterns_block(structural_pat))

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



# ============================================================================
# 可读性断卦报告 — 面向客户，供易师直接解读
# ============================================================================

# 六神描述（对客户友好）
_LIU_SHEN_DESC = {
    "青龙": "青龙（贵人、喜庆、财禄）",
    "朱雀": "朱雀（口舌、文书、信息）",
    "勾陈": "勾陈（拖延、纠缠、土地）",
    "螣蛇": "螣蛇（虚惊、缠绕、暗动）",
    "白虎": "白虎（凶险、官司、强硬）",
    "玄武": "玄武（隐秘、盗贼、暗昧）",
}

# 六亲对失物占的物象含义
_LIU_QIN_SHIWU_DESC = {
    "父母": "所失物件本身（物之实体）",
    "妻财": "所失物件的价值（财物之象）",
    "官鬼": "持有者、阻碍力量",
    "兄弟": "耗散、竞争、阻隔",
    "子孙": "寻物者的疏忽/喜神",
}

# 卦局白话解释
_GUA_JU_BAIHUA = {
    "世用受克局":   "用神与世爻合一却遭受动爻克伤——失物与主人的缘分已断，凶。",
    "世爻受伤局":   "世爻被有力的动爻克伤——主人追寻此物的力量受阻，凶。",
    "世用受生局":   "用神与世爻合一且受动爻生扶——失物有归还之象，吉。",
    "用神生世局":   "用神主动生旺世爻——物与主人气场相连，有望寻回，吉。",
    "用旺世兴局":   "用神旺盛，世爻亦得日月扶助——天时地利俱备，可寻回，吉。",
    "用旺世衰局":   "用神虽旺，世爻却衰弱——物虽存在，主人无力追回，凶。",
    "用神克世局":   "用神动而克世——物事对主人有所伤损，凶（短期失物若世旺可酌情看吉）。",
    "用神衰败局":   "用神本身衰弱——所失之物已残损或难觅踪迹，凶。",
    "失物特例(用克世)": "用神动克世但世爻有日月扶助——短期内有望寻回（属特例之吉）。",
    "静卦用旺世兴": "静卦中用神旺、世爻兴——物在某处静候，可寻，吉。",
    "静卦用衰":     "静卦用神衰败——物已难觅，凶。",
    "静卦用克世":   "静卦用神克世——寻物对主人构成损耗，凶。",
    "用神持世":     "用神就是世爻——物与人同在，情形密切，可寻，吉。",
    "平局":         "卦局平和，吉凶未明，需结合细节综合研判。",
}

# 应期候选白话前缀
_YINGQI_PREFIX = "关键时节："


def _readable_gua_tu(hexagram):
    """生成可读性卦图（六神+六亲+爻符+世应+动变）"""
    rows = []
    rows.append("  六神    六亲 地支 爻符        变爻")
    rows.append("  " + "─" * 46)
    # 从上爻到初爻（卦图习惯由上至下）
    for line in reversed(hexagram.lines):
        pos = line.position
        shen = line.liu_shen
        qin  = line.liu_qin
        zhi  = line.di_zhi

        # 爻符
        if line.yin_yang == 1:
            yao_sym = "━━━━━━━"   # 阳爻
        else:
            yao_sym = "━━ ━━"     # 阴爻

        # 动变标记
        if line.is_moving:
            if line.yao_type == 9:   # 老阳变阴
                dong_mark = " ×"
                bian_sym  = "━━ ━━"
            else:                    # 老阴变阳
                dong_mark = " ○"
                bian_sym  = "━━━━━━━"
            bian_str = f"  →  {line.bian_liu_qin or ''}{line.bian_di_zhi or ''} {bian_sym}"
        else:
            dong_mark = "  "
            bian_str  = ""

        # 世应标记
        if line.is_shi:
            role = "世"
        elif line.is_ying:
            role = "应"
        else:
            role = "  "

        # 旬空标记
        kong = "（空）" if line.is_xun_kong else "      "

        rows.append(
            f"  {shen:<4}  {qin}{zhi}  {yao_sym}{dong_mark} {role} {kong}{bian_str}"
        )
    rows.append("  " + "─" * 46)
    return rows


def _readable_wangshuai_summary(hexagram, wangshuai_results):
    """生成旺衰白话摘要（一爻一行，用自然语言描述）"""
    lines = []
    for ws in wangshuai_results:
        pos   = ws["position"]
        line  = hexagram.lines[pos - 1]
        level = ws["overall"]
        level_word = {"旺": "当令旺相", "衰": "失令衰弱", "平": "平和中性"}[level]

        role = ""
        if line.is_shi:
            role = "（世爻）"
        elif line.is_ying:
            role = "（应爻）"
        dong = "动爻" if line.is_moving else "静爻"
        kong = "，本旬旬空" if line.is_xun_kong else ""

        lines.append(
            f"  第{pos}爻  {line.liu_shen} {line.liu_qin}{line.di_zhi}{line.wu_xing}"
            f"  {dong}{role}  ➜  {level_word}{kong}"
        )
    return lines


def _readable_dongbian_summary(hexagram, dongbian_results):
    """生成动变白话摘要"""
    lines = []
    moving_analyses = dongbian_results.get("moving_analyses", {})
    if not moving_analyses:
        lines.append("  本卦为纯静卦，六爻无一发动，卦象稳定，所问事宜处于静止状态。")
        return lines

    useful, useless = [], []
    for pos, ma in sorted(moving_analyses.items()):
        line = hexagram.lines[pos - 1]
        entry = (
            f"第{pos}爻 {line.liu_qin}{line.di_zhi} → {ma['bian_zhi']}"
        )
        if ma["is_useless"]:
            useless.append(entry + f"（{ma['useless_reason']}，此动无效）")
        else:
            entry_str = entry
            if ma["趋旺"]:
                entry_str += "，动而趋旺（" + "、".join(ma["趋旺"]) + "）"
            elif ma["趋衰"]:
                entry_str += "，动而趋衰（" + "、".join(ma["趋衰"]) + "）"
            useful.append(entry_str)

    if useful:
        lines.append("  ◎ 有效动爻（影响吉凶走势）：")
        for u in useful:
            lines.append(f"    · {u}")
    if useless:
        lines.append("  ○ 无效动爻（不参与吉凶定性）：")
        for u in useless:
            lines.append(f"    · {u}")

    # 动爻克世
    interactions = dongbian_results.get("interactions", {})
    shi_line = None
    for l in hexagram.lines:
        if l.is_shi:
            shi_line = l
            break
    if shi_line and shi_line.position in interactions:
        inter = interactions[shi_line.position]
        if inter["受克"]:
            lines.append(f"  ⚠  世爻受克：{' / '.join(inter['受克'])}  克伤主人持物之力")
        if inter["受生"]:
            lines.append(f"  ✦  世爻受生：{' / '.join(inter['受生'])}  扶助主人追寻之力")
    return lines


def _readable_yingqi_summary(yingqi_results):
    """生成应期白话摘要"""
    lines = []
    if not yingqi_results:
        lines.append("  用神不现卦中，应期难以推算。")
        return lines
    for yq in yingqi_results:
        cands = yq.get("candidates", [])
        if cands:
            lines.append(
                f"  第{yq['position']}爻（{yq['di_zhi']} {yq.get('liu_qin','')}）"
                f"  关键时节：{' / '.join(cands[:4])}"
            )
    return lines


def _readable_conclusion(dual_report):
    """
    生成综合结论段落。
    支持 DualPerspectiveReport（双视角）和 AnalysisReport（单视角）。
    """
    lines = []
    is_dual = hasattr(dual_report, "perspectives") and dual_report.perspectives

    if is_dual:
        p1, p2 = dual_report.perspectives[0], dual_report.perspectives[1]
        j1 = p1.jixiong_result
        j2 = p2.jixiong_result
        both_xiong = (j1.get("ji_xiong") == "凶" and j2.get("ji_xiong") == "凶")
        both_ji    = (j1.get("ji_xiong") == "吉" and j2.get("ji_xiong") == "吉")

        if both_xiong:
            verdict = "凶——此物难以寻回"
            tone = (
                "从物件本相（父母爻）与财物价值（妻财爻）两个角度审视，"
                "卦象均指向同一结论：\n"
                f"  · {p1.perspective_label}：{_GUA_JU_BAIHUA.get(j1['pattern'], j1['explanation'])}\n"
                f"  · {p2.perspective_label}：{_GUA_JU_BAIHUA.get(j2['pattern'], j2['explanation'])}\n"
                "两路相验，结论趋同，说明卦象给出的信号相当确定。"
            )
        elif both_ji:
            verdict = "吉——此物有望寻回"
            tone = (
                "两个视角均显示吉象：\n"
                f"  · {p1.perspective_label}：{_GUA_JU_BAIHUA.get(j1['pattern'], j1['explanation'])}\n"
                f"  · {p2.perspective_label}：{_GUA_JU_BAIHUA.get(j2['pattern'], j2['explanation'])}\n"
                "双视角互证，寻回可期。"
            )
        else:
            v1 = j1.get("ji_xiong", "平")
            v2 = j2.get("ji_xiong", "平")
            verdict = f"两视角分歧（{p1.yong_shen_liu_qin}视角：{v1} / {p2.yong_shen_liu_qin}视角：{v2}）"
            tone = (
                "两个用神角度给出不同信号，宜谨慎研判，\n"
                "建议以吉凶更明显的一方为主，结合问卦人实际情况综合判断。"
            )
        lines.append(f"  综合断语：【{verdict}】")
        lines.append("")
        lines.append(f"  {tone}")

        # 应期合并
        all_yq = []
        for p in dual_report.perspectives:
            all_yq.extend(p.yingqi_results or [])
        seen = set()
        uniq_yq = []
        for yq in all_yq:
            key = yq["position"]
            if key not in seen:
                seen.add(key)
                uniq_yq.append(yq)
        if uniq_yq:
            lines.append("")
            lines.append("  应期参考（若有线索浮现，多在以下时节）：")
            lines.extend(_readable_yingqi_summary(uniq_yq))

    else:
        # 单视角
        jx = dual_report.jixiong_result
        ji_xiong = jx.get("ji_xiong", "平")
        pattern  = jx.get("pattern", "")
        verdict_map = {"吉": "吉——事可成", "凶": "凶——事难成", "平": "平——尚待观望"}
        lines.append(f"  综合断语：【{verdict_map.get(ji_xiong, ji_xiong)}】")
        lines.append("")
        lines.append(f"  {_GUA_JU_BAIHUA.get(pattern, jx.get('explanation', ''))}")
        lines.append("")
        lines.append("  应期参考：")
        lines.extend(_readable_yingqi_summary(dual_report.yingqi_results or []))

    return lines


def format_readable_report(analysis, meta=None):
    """
    生成面向客户的可读性断卦报告。

    报告风格：简洁、白话、结构清晰，方便易师向客户直接解读。
    支持单视角（AnalysisReport）和双视角（DualPerspectiveReport）两种输入。

    Args:
        analysis : AnalysisReport 或 DualPerspectiveReport
        meta     : 可选 dict，补充客户信息，支持以下键：
                     question  (str)  占问事宜，如"金首饰丢失能否找回"
                     querent   (str)  卦主姓名或称呼
                     datetime  (str)  起卦时间，如"2026-05-25 14:28"
                     note      (str)  额外备注

    Returns:
        str: 格式化后的可读性报告文本
    """
    meta = meta or {}
    is_dual = hasattr(analysis, "perspectives") and analysis.perspectives
    hexagram = analysis.hexagram
    gz = hexagram.gan_zhi

    W = 58  # 报告宽度

    out = []

    # ── 封面 ──────────────────────────────────────────────────────────
    out.append("╔" + "═" * W + "╗")
    out.append("║" + "  断  卦  报  告".center(W) + "║")
    out.append("╚" + "═" * W + "╝")
    out.append("")

    # ── 一、基本信息 ──────────────────────────────────────────────────
    out.append("▌ 一、基本信息")
    out.append("─" * (W + 2))

    question = meta.get("question", "（未填写）")
    querent  = meta.get("querent",  "（未填写）")
    dt_str   = meta.get("datetime", f"{hexagram.year}年{hexagram.month}月{hexagram.day}日")

    out.append(f"  占问事宜：{question}")
    out.append(f"  卦  主：  {querent}")
    out.append(f"  起卦时间：{dt_str}")
    out.append(f"  干支四柱：{gz['year_gan']}{gz['year_zhi']}年  "
               f"{gz['month_gan']}{gz['month_zhi']}月  "
               f"{gz['day_gan']}{gz['day_zhi']}日")
    out.append(f"  旬    空：{hexagram.xun_kong[0]}、{hexagram.xun_kong[1]}")
    out.append("")

    # ── 二、卦象 ──────────────────────────────────────────────────────
    out.append("▌ 二、卦象")
    out.append("─" * (W + 2))
    out.append(f"  本卦：{hexagram.ben_gua_name}（{hexagram.palace_name}宫）"
               f"  →  变卦：{hexagram.bian_gua_name}")
    out.append("")
    out.extend(_readable_gua_tu(hexagram))
    out.append("")
    out.append("  说明：× 为老阳动爻（阳变阴），○ 为老阴动爻（阴变阳）；")
    out.append("        世爻代表问卦人，应爻代表对方或所问之事；")
    out.append("        旬空之爻暂时力量虚悬，待出空方能论其效用。")
    out.append("")

    # ── 三、旺衰总览 ──────────────────────────────────────────────────
    out.append("▌ 三、各爻旺衰总览")
    out.append("─" * (W + 2))
    out.append(f"  月建：{gz['month_zhi']}（{DI_ZHI_WU_XING[gz['month_zhi']]}）"
               f"  日辰：{gz['day_zhi']}（{DI_ZHI_WU_XING[gz['day_zhi']]}）")
    out.append("")
    if is_dual:
        ws_results = analysis.wangshuai_results
    else:
        ws_results = analysis.wangshuai_results
    out.extend(_readable_wangshuai_summary(hexagram, ws_results))
    out.append("")
    out.append("  旺相之爻力量充足，衰弱之爻力量不足，平和之爻不偏不倚。")
    out.append("")

    # ── 四、动变解析 ──────────────────────────────────────────────────
    out.append("▌ 四、动变解析")
    out.append("─" * (W + 2))
    if is_dual:
        db_results = analysis.dongbian_results
    else:
        db_results = analysis.dongbian_results
    out.extend(_readable_dongbian_summary(hexagram, db_results))
    out.append("")

    # ── 五、用神分析 ──────────────────────────────────────────────────
    out.append("▌ 五、用神分析")
    out.append("─" * (W + 2))
    if is_dual:
        for idx, p in enumerate(analysis.perspectives, 1):
            label = p.perspective_label
            ys    = p.yong_shen_liu_qin
            ys_lines = p.yong_shen_lines or []
            jx    = p.jixiong_result
            ji_mark = {"吉": "✓ 吉", "凶": "✗ 凶", "平": "— 平"}.get(
                jx.get("ji_xiong", "平"), jx.get("ji_xiong", "平"))

            out.append(f"  【视角{idx}】{label}")
            if ys_lines:
                for l in ys_lines:
                    tags = []
                    if l.is_moving: tags.append("动")
                    if l.is_shi:    tags.append("世")
                    if l.is_ying:   tags.append("应")
                    if l.is_xun_kong: tags.append("旬空")
                    ws_lv = ws_results[l.position - 1]["overall"]
                    tag_s = "、".join(tags) if tags else "静"
                    out.append(
                        f"  用神：{ys}——第{l.position}爻 {l.liu_shen} {l.di_zhi}{l.wu_xing}"
                        f"  （{tag_s}，{ws_lv}相）"
                    )
            else:
                out.append(f"  用神：{ys}——卦中未现，用神不上卦（此为不利之象）")

            out.append(f"  卦局：{jx.get('pattern', '-')}")
            out.append(f"  判断：{ji_mark}")
            baihua = _GUA_JU_BAIHUA.get(jx.get("pattern",""), jx.get("explanation",""))
            out.append(f"  释义：{baihua}")
            out.append("")
    else:
        ys = analysis.yong_shen_liu_qin
        ys_lines = analysis.yong_shen_lines or []
        jx = analysis.jixiong_result
        ji_mark = {"吉": "✓ 吉", "凶": "✗ 凶", "平": "— 平"}.get(
            jx.get("ji_xiong", "平"), jx.get("ji_xiong", "平"))
        if ys_lines:
            for l in ys_lines:
                tags = []
                if l.is_moving: tags.append("动")
                if l.is_shi:    tags.append("世")
                if l.is_ying:   tags.append("应")
                ws_lv = ws_results[l.position - 1]["overall"]
                tag_s = "、".join(tags) if tags else "静"
                out.append(
                    f"  用神：{ys}——第{l.position}爻 {l.liu_shen} {l.di_zhi}{l.wu_xing}"
                    f"  （{tag_s}，{ws_lv}相）"
                )
        else:
            out.append(f"  用神：{ys}——卦中未现")
        out.append(f"  卦局：{jx.get('pattern', '-')}")
        out.append(f"  判断：{ji_mark}")
        out.append(f"  释义：{_GUA_JU_BAIHUA.get(jx.get('pattern',''), jx.get('explanation',''))}")
        out.append("")

    # ── 六、综合结论 ──────────────────────────────────────────────────
    out.append("▌ 六、综合结论")
    out.append("─" * (W + 2))
    out.extend(_readable_conclusion(analysis))
    out.append("")

    # ── 七、建议 ──────────────────────────────────────────────────────
    out.append("▌ 七、给卦主的建议")
    out.append("─" * (W + 2))
    # 取综合吉凶
    if is_dual:
        ji_set = {p.jixiong_result.get("ji_xiong") for p in analysis.perspectives}
        overall_ji = ji_set.pop() if len(ji_set) == 1 else "平"
    else:
        overall_ji = analysis.jixiong_result.get("ji_xiong", "平")

    if overall_ji == "凶":
        out.append("  · 卦象显示寻回可能性极低，建议尽早放下执念，避免在追查上")
        out.append("    投入过多时间与金钱，以免二次损耗。")
        out.append("  · 若有保险或官方渠道（如报警备案），可走正规途径留存记录，")
        out.append('    不宜轻信"帮忙寻物"的中间人，谨防再度受损。')
        out.append("  · 将此次失物视为一次提醒：贵重物品宜妥善保管，出门前")
        out.append("    养成清点携带物的习惯。")
    elif overall_ji == "吉":
        out.append("  · 卦象显示有望寻回，宜保持耐心，在应期所示时节留意线索。")
        out.append("  · 可通过正规渠道（报警、发布寻物信息）主动出击，")
        out.append("    增加寻回的机会。")
        out.append("  · 寻回后宜多加小心，做好防范，避免再度遗失。")
    else:
        out.append("  · 卦象平和，吉凶未定，建议持续关注事态发展，")
        out.append("    不宜过于急切，也不宜完全放弃。")
        out.append("  · 在应期所示时节，留意是否有相关线索出现。")

    if meta.get("note"):
        out.append("")
        out.append(f"  备注：{meta['note']}")
    out.append("")

    # ── 尾部 ──────────────────────────────────────────────────────────
    out.append("═" * (W + 2))
    out.append("  ※ 本报告依据纳甲六爻《古筮真诠》理论体系生成，")
    out.append("    供易学研习与参考，最终判断以易师解读为准。")
    out.append("═" * (W + 2))

    return "\n".join(out)
