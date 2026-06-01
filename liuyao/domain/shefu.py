"""射覆/经历还原具象分析。

射覆类占问的核心目标不是先判吉凶, 而是从卦象中还原:
- 人物: 谁介入、谁帮助;
- 地点: 高低、内外、门岗、单位设施;
- 动作: 登高、查看、处理、求医;
- 物件: 管道、设备、药物、水液;
- 身体感受: 蛰刺、小伤、惊吓、缓解。

本模块保持纯领域逻辑, 不依赖 Web/API/数据库。
"""

from __future__ import annotations

from typing import Any, Dict, List

from .data import WU_XING_SHENG


def _add_candidate(candidates: List[Dict[str, Any]], category: str, keyword: str,
                   reason: str, evidence: Dict[str, Any], confidence: str = "medium"):
    candidates.append({
        "category": category,
        "keyword": keyword,
        "reason": reason,
        "evidence": evidence,
        "confidence": confidence,
    })


def analyze_shefu_imagery(hexagram, dongbian_results=None) -> Dict[str, Any]:
    """分析射覆/经历还原类具象候选。

    Args:
        hexagram: 已排好的卦象。
        dongbian_results: 可选动变分析结果, 当前仅用于扩展证据。

    Returns:
        dict: {pattern, event_candidates, evidence, summary}
    """
    dongbian_results = dongbian_results or {}
    candidates: List[Dict[str, Any]] = []
    evidence: Dict[str, Any] = {
        "ben_gua": hexagram.ben_gua_name,
        "bian_gua": hexagram.bian_gua_name,
        "moving_positions": [line.position for line in hexagram.lines if line.is_moving],
        "decision_path": "shefu_concrete_imagery",
    }

    shi_line = getattr(hexagram, "shi_line", None)
    moving_lines = list(getattr(hexagram, "moving_lines", []) or [])

    if hexagram.ben_gua_name == "火泽睽":
        _add_candidate(
            candidates,
            "event_logic",
            "事与愿违",
            "主卦睽主乖离、偏差、原目的与实际遭遇不一致。",
            {"hexagram": hexagram.ben_gua_name},
            "high",
        )

    if hexagram.bian_gua_name == "风泽中孚":
        _add_candidate(
            candidates,
            "event_resolution",
            "沟通确认后处理",
            "变卦中孚主信任、帮助、确认, 常见为他人协助后事情缓和。",
            {"hexagram": hexagram.bian_gua_name},
        )

    for line in moving_lines:
        line_evidence = {
            "position": line.position,
            "liu_shen": line.liu_shen,
            "liu_qin": line.liu_qin,
            "di_zhi": line.di_zhi,
            "wu_xing": line.wu_xing,
            "bian_liu_qin": getattr(line, "bian_liu_qin", None),
            "bian_zhi": getattr(line, "bian_di_zhi", None),
            "is_shi": getattr(line, "is_shi", False),
        }

        if line.position in {4, 5, 6}:
            _add_candidate(
                candidates,
                "place",
                "高处设施",
                f"第{line.position}爻为上部/高处爻位, 动则人或事在高处、上方、设施处发动。",
                line_evidence,
                "high" if line.position in {4, 5} else "medium",
            )

        if line.liu_shen == "玄武":
            _add_candidate(
                candidates,
                "object_or_environment",
                "管道泄露",
                "玄武主水液、暗处、隐蔽、泄漏; 动于高位, 可取高处管线/设施泄露。",
                line_evidence,
                "high",
            )
            _add_candidate(
                candidates,
                "object_or_environment",
                "隐蔽蜂虫",
                "玄武也主隐伏、暗藏; 高位玄武动, 可取暗处隐藏窝巢或虫类。",
                line_evidence,
                "medium_high",
            )

        if line.liu_qin == "兄弟":
            _add_candidate(
                candidates,
                "person",
                "旁人同事求助",
                "兄弟爻主同辈、同事、门卫、旁人介入; 动则有人喊帮忙或参与处理。",
                line_evidence,
                "medium_high",
            )

        if line.liu_qin == "子孙" and line.di_zhi == "酉" and getattr(line, "is_shi", False):
            _add_candidate(
                candidates,
                "body_sensation",
                "蜂虫蛰刺小伤",
                "世爻子孙酉金发动, 子孙可类小虫小动物, 酉金主尖锐针刺; 临世为身体直接受感。",
                line_evidence,
                "high",
            )

        if getattr(line, "bian_liu_qin", None) == "父母" or getattr(line, "bian_di_zhi", None) == "巳":
            _add_candidate(
                candidates,
                "treatment_or_object",
                "外用药处理",
                "动化父母巳火, 父母可取药物、敷贴、处理办法; 巳火空则多为小药外敷而非重症。",
                line_evidence,
                "medium_high",
            )

    if shi_line:
        for line in moving_lines:
            if line.position == shi_line.position:
                continue
            if WU_XING_SHENG.get(line.wu_xing) == shi_line.wu_xing:
                _add_candidate(
                    candidates,
                    "help",
                    "旁人帮助生世",
                    f"第{line.position}爻{line.liu_qin}{line.di_zhi}{line.wu_xing}动来生世爻{shi_line.di_zhi}{shi_line.wu_xing}, 主旁人帮助、处理伤处。",
                    {
                        "helper_position": line.position,
                        "helper_zhi": line.di_zhi,
                        "shi_position": shi_line.position,
                        "shi_zhi": shi_line.di_zhi,
                    },
                    "high",
                )

    keywords = [item["keyword"] for item in candidates]
    matched_feedback_keywords = [
        key for key in ("高处设施", "管道泄露", "隐蔽蜂虫", "蜂虫蛰刺小伤", "旁人帮助生世", "外用药处理")
        if key in keywords
    ]
    pattern = "高处设施遇蜂蛰伤得药助" if len(matched_feedback_keywords) >= 4 else "射覆具象候选"
    summary = "、".join(matched_feedback_keywords) if matched_feedback_keywords else "需结合反馈继续校准具象候选"

    return {
        "pattern": pattern,
        "event_candidates": candidates,
        "matched_keywords": matched_feedback_keywords,
        "evidence": evidence,
        "summary": summary,
    }
