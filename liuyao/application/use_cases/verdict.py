"""
分析结果断语构建。

只负责从单视角/双视角分析结果中提取综合断语，供 CLI 与可读性报告复用。
"""

from liuyao.application.use_cases.dto import AnalysisReport, DualPerspectiveReport


# 卦局白话解释 — 权威来源 (reporting.py 从此处导入, 不再重复定义)
GUA_JU_BAIHUA: dict = {
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


def build_verdict(analysis: AnalysisReport | DualPerspectiveReport) -> dict:
    """
    从 AnalysisReport 或 DualPerspectiveReport 中提取综合断语。

    返回:
        {
            "verdict":      str,
            "tone":         str,
            "yingqi_lines": list,
        }
    """
    is_dual = hasattr(analysis, "perspectives") and bool(analysis.perspectives)

    if is_dual:
        perspectives = analysis.perspectives
        j1 = perspectives[0].jixiong_result
        j2 = perspectives[1].jixiong_result if len(perspectives) > 1 else j1
        p1_label = perspectives[0].perspective_label
        p2_label = perspectives[1].perspective_label if len(perspectives) > 1 else ""

        both_xiong = j1.get("ji_xiong") == "凶" and j2.get("ji_xiong") == "凶"
        both_ji = j1.get("ji_xiong") == "吉" and j2.get("ji_xiong") == "吉"

        if both_xiong:
            verdict = "凶——此物难以寻回"
            tone = (
                "从物件本相（父母爻）与财物价值（妻财爻）两个角度审视，"
                "卦象均指向同一结论：\n"
                f"  · {p1_label}：{GUA_JU_BAIHUA.get(j1['pattern'], j1.get('explanation', ''))}\n"
                f"  · {p2_label}：{GUA_JU_BAIHUA.get(j2['pattern'], j2.get('explanation', ''))}\n"
                "两路相验，结论趋同，说明卦象给出的信号相当确定。"
            )
        elif both_ji:
            verdict = "吉——此物有望寻回"
            tone = (
                "两个视角均显示吉象：\n"
                f"  · {p1_label}：{GUA_JU_BAIHUA.get(j1['pattern'], j1.get('explanation', ''))}\n"
                f"  · {p2_label}：{GUA_JU_BAIHUA.get(j2['pattern'], j2.get('explanation', ''))}\n"
                "双视角互证，寻回可期。"
            )
        else:
            v1 = j1.get("ji_xiong", "平")
            v2 = j2.get("ji_xiong", "平")
            p1_ys = perspectives[0].yong_shen_liu_qin
            p2_ys = perspectives[1].yong_shen_liu_qin if len(perspectives) > 1 else ""
            verdict = f"两视角分歧（{p1_ys}视角：{v1} / {p2_ys}视角：{v2}）"
            tone = (
                "两个用神角度给出不同信号，宜谨慎研判，\n"
                "建议以吉凶更明显的一方为主，结合问卦人实际情况综合判断。"
            )

        seen: set = set()
        yingqi_lines = []
        for perspective in perspectives:
            for yq in (perspective.yingqi_results or []):
                key = yq["position"]
                if key not in seen:
                    seen.add(key)
                    yingqi_lines.append(yq)
    else:
        jx = analysis.jixiong_result
        ji_xiong = jx.get("ji_xiong", "平")
        pattern = jx.get("pattern", "")
        verdict_map = {"吉": "吉——事可成", "凶": "凶——事难成", "平": "平——尚待观望"}
        verdict = verdict_map.get(ji_xiong, ji_xiong)
        tone = GUA_JU_BAIHUA.get(pattern, jx.get("explanation", ""))
        yingqi_lines = analysis.yingqi_results or []

    return {"verdict": verdict, "tone": tone, "yingqi_lines": yingqi_lines}
