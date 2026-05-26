"""
卦意分析模块 - Gua-Yi (Hexagram Meaning / Direct Reading) Analysis

实现9种卦意分析法, 作为高层解读层叠加在结构性五行分析之上。
"""

from .data import (
    DI_ZHI_WU_XING, WU_XING_SHENG, WU_XING_KE,
    LIU_CHONG, LIU_HE, SAN_HE,
)
from .jixiong import JI_SHEN_TABLE, find_ying_line
from .dongbian import is_hui_tou_sheng, is_hui_tou_ke


def analyze_guayi(hexagram, dongbian_results, wangshuai_results,
                  yong_shen_liu_qin, question_type, shi_line, yong_lines):
    """
    卦意分析主入口。

    Returns:
        list[dict]: 每个dict为 {"method": str, "description": str,
                    "ji_xiong": "吉"/"凶"/"中性", "details": str}
    """
    if not shi_line or not yong_lines:
        return []

    findings = []

    # Method 1: 世化用忌法
    r = _shi_hua_yong_ji(hexagram, shi_line, yong_shen_liu_qin,
                         wangshuai_results)
    if r:
        findings.append(r)

    # Method 2: 用忌互化法
    r = _yong_ji_huhua(hexagram, yong_lines, dongbian_results,
                       yong_shen_liu_qin)
    if r:
        findings.append(r)

    # Method 3: 鬼用互化法
    r = _gui_yong_huhua(hexagram, yong_lines, dongbian_results,
                        yong_shen_liu_qin)
    if r:
        findings.append(r)

    # Method 4: 世动化鬼法
    r = _shi_dong_hua_gui(hexagram, shi_line, dongbian_results,
                          yong_shen_liu_qin, wangshuai_results)
    if r:
        findings.append(r)

    # Method 5: 世用背向法
    r = _shi_yong_bei_xiang(hexagram, shi_line, yong_lines,
                            dongbian_results, wangshuai_results)
    if r:
        findings.append(r)

    # Method 6: 搭桥趋变法
    r = _da_qiao_qu_bian(hexagram, dongbian_results, shi_line, yong_lines)
    if r:
        findings.append(r)

    # Method 7: 牵连聚合法
    r = _qianlian_juhe(hexagram, shi_line, yong_lines, dongbian_results)
    if r:
        findings.append(r)

    # Method 8: 代入确认法
    r = _dairu_queren(hexagram, shi_line, yong_lines)
    if r:
        findings.append(r)

    # Method 9: 间爻阻隔法
    r = _jianyao_zuge(hexagram, shi_line, yong_lines, wangshuai_results,
                      dongbian_results)
    if r:
        findings.append(r)

    return findings


def _shi_hua_yong_ji(hexagram, shi_line, yong_shen_liu_qin, wangshuai_results):
    """
    世化用忌法: 世爻动变化出用神或忌神。
    """
    if not shi_line.is_moving:
        return None

    bian_lq = shi_line.bian_liu_qin
    if not bian_lq:
        return None

    ji_shen = JI_SHEN_TABLE.get(yong_shen_liu_qin, "")

    # 世化用神
    if bian_lq == yong_shen_liu_qin:
        # 特殊: 用神为官鬼时, 需检查变爻旺衰
        if yong_shen_liu_qin == "官鬼":
            bian_ws = wangshuai_results[shi_line.position - 1]
            if bian_ws["overall"] == "衰":
                return {
                    "method": "世化用忌法",
                    "description": "世爻动变化官鬼(用神), 但变爻衰弱为祸患之鬼",
                    "ji_xiong": "凶",
                    "details": "世化官鬼衰弱, 非官星乃祸鬼",
                }
        return {
            "method": "世化用忌法",
            "description": f"世爻动变化出{yong_shen_liu_qin}(用神)",
            "ji_xiong": "吉",
            "details": f"世爻变爻六亲为{bian_lq}, 即用神, 世与用神趋同",
        }

    # 世化忌神
    if bian_lq == ji_shen:
        return {
            "method": "世化用忌法",
            "description": f"世爻动变化出{ji_shen}(忌神)",
            "ji_xiong": "凶",
            "details": f"世爻变爻六亲为{bian_lq}, 即忌神, 世与忌神趋同",
        }

    return None


def _yong_ji_huhua(hexagram, yong_lines, dongbian_results, yong_shen_liu_qin):
    """
    用忌互化法: 用神与忌神互相变化。
    """
    ji_shen = JI_SHEN_TABLE.get(yong_shen_liu_qin, "")
    if not ji_shen:
        return None

    # 用神动化忌神
    for yl in yong_lines:
        if yl.is_moving and yl.bian_liu_qin == ji_shen:
            return {
                "method": "用忌互化法",
                "description": f"用神({yong_shen_liu_qin})动变化出忌神({ji_shen})",
                "ji_xiong": "凶",
                "details": "用神化忌神, 所求之事纠缠不清, 凶",
            }

    # 忌神动化用神
    for line in hexagram.lines:
        if line.liu_qin == ji_shen and line.is_moving:
            if line.bian_liu_qin == yong_shen_liu_qin:
                return {
                    "method": "用忌互化法",
                    "description": f"忌神({ji_shen})动变化出用神({yong_shen_liu_qin})",
                    "ji_xiong": "凶",
                    "details": "忌神化用神, 障碍缠绕所求之事, 凶",
                }

    return None


def _gui_yong_huhua(hexagram, yong_lines, dongbian_results, yong_shen_liu_qin):
    """
    鬼用互化法: 官鬼与用神互相变化(官鬼不是用神时)。
    """
    if yong_shen_liu_qin == "官鬼":
        return None

    # 官鬼动化用神
    for line in hexagram.lines:
        if line.liu_qin == "官鬼" and line.is_moving:
            if line.bian_liu_qin == yong_shen_liu_qin:
                return {
                    "method": "鬼用互化法",
                    "description": "官鬼动变化出用神六亲",
                    "ji_xiong": "凶",
                    "details": "灾祸与所求之事纠缠, 凶",
                }

    # 用神动化官鬼
    for yl in yong_lines:
        if yl.is_moving and yl.bian_liu_qin == "官鬼":
            return {
                "method": "鬼用互化法",
                "description": "用神动变化出官鬼",
                "ji_xiong": "凶",
                "details": "所求之事化为灾祸, 凶",
            }

    return None


def _shi_dong_hua_gui(hexagram, shi_line, dongbian_results,
                      yong_shen_liu_qin, wangshuai_results):
    """
    世动化鬼法: 世爻动化官鬼。
    """
    if not shi_line.is_moving:
        return None
    if shi_line.bian_liu_qin != "官鬼":
        return None

    # Exception (a): 官鬼就是用神且变爻不衰
    if yong_shen_liu_qin == "官鬼":
        ws = wangshuai_results[shi_line.position - 1]
        if ws["overall"] != "衰":
            return {
                "method": "世动化鬼法",
                "description": "世爻动化官鬼(用神), 变爻不衰为官星",
                "ji_xiong": "吉",
                "details": "官鬼为用神且不衰, 为官星而非祸鬼",
            }

    # Exception (b): 父母持世化官鬼 + 回头生
    if shi_line.liu_qin == "父母":
        if shi_line.bian_di_zhi and is_hui_tou_sheng(
                shi_line.di_zhi, shi_line.bian_di_zhi):
            return {
                "method": "世动化鬼法",
                "description": "父母持世化官鬼回头生(心态卦吉象)",
                "ji_xiong": "吉",
                "details": "父母持世化官鬼得回头生, 心态卦吉利格局",
            }

    return {
        "method": "世动化鬼法",
        "description": "世爻动变化出官鬼",
        "ji_xiong": "凶",
        "details": "灾祸将纠缠问卦人自身, 凶",
    }


def _shi_yong_bei_xiang(hexagram, shi_line, yong_lines, dongbian_results,
                        wangshuai_results):
    """
    世用背向法: 世爻与用神的趋向关系(合=向, 冲=背)。
    """
    if not yong_lines:
        return None

    primary_yong = yong_lines[0]
    for yl in yong_lines:
        if yl.is_moving:
            primary_yong = yl
            break
        ws = wangshuai_results[yl.position - 1]
        if ws["overall"] == "旺":
            primary_yong = yl

    ying_line = find_ying_line(hexagram)
    yong_ws = wangshuai_results[primary_yong.position - 1]
    shi_ws = wangshuai_results[shi_line.position - 1]

    # Check for回头作用 override
    def _has_hui_tou(line):
        if not line.is_moving or not line.bian_di_zhi:
            return False
        return (is_hui_tou_sheng(line.di_zhi, line.bian_di_zhi) or
                is_hui_tou_ke(line.di_zhi, line.bian_di_zhi))

    # 吉 pattern 1: 世旺 + 用神动 + 用神变爻合世
    if (shi_ws["overall"] == "旺" and primary_yong.is_moving and
            primary_yong.bian_di_zhi):
        if not _has_hui_tou(primary_yong):
            he_partner = LIU_HE.get(primary_yong.bian_di_zhi)
            if he_partner and he_partner[0] == shi_line.di_zhi:
                return {
                    "method": "世用背向法",
                    "description": "世旺+用神动+变爻合世(趋向)",
                    "ji_xiong": "吉",
                    "details": f"用神{primary_yong.di_zhi}动变{primary_yong.bian_di_zhi}"
                              f"合世爻{shi_line.di_zhi}, 用向世趋",
                }

    # 吉 pattern 2: 用旺 + 世动 + 世变爻合用
    if (yong_ws["overall"] == "旺" and shi_line.is_moving and
            shi_line.bian_di_zhi):
        if not _has_hui_tou(shi_line):
            he_partner = LIU_HE.get(shi_line.bian_di_zhi)
            if he_partner and he_partner[0] == primary_yong.di_zhi:
                return {
                    "method": "世用背向法",
                    "description": "用旺+世动+变爻合用(趋向)",
                    "ji_xiong": "吉",
                    "details": f"世爻{shi_line.di_zhi}动变{shi_line.bian_di_zhi}"
                              f"合用神{primary_yong.di_zhi}, 世向用趋",
                }

    # 吉 pattern 3: 用旺不动 + 应爻动 + 应变爻合世
    if (yong_ws["overall"] == "旺" and not primary_yong.is_moving and
            ying_line and ying_line.is_moving and ying_line.bian_di_zhi):
        if not _has_hui_tou(ying_line):
            he_partner = LIU_HE.get(ying_line.bian_di_zhi)
            if he_partner and he_partner[0] == shi_line.di_zhi:
                return {
                    "method": "世用背向法",
                    "description": "用旺不动+应爻动+变爻合世(趋向)",
                    "ji_xiong": "吉",
                    "details": f"应爻{ying_line.di_zhi}动变{ying_line.bian_di_zhi}"
                              f"合世爻{shi_line.di_zhi}, 应助世趋",
                }

    # 凶 pattern 1: 用神动 + 变爻冲世
    if primary_yong.is_moving and primary_yong.bian_di_zhi:
        if not _has_hui_tou(primary_yong):
            if LIU_CHONG.get(primary_yong.bian_di_zhi) == shi_line.di_zhi:
                return {
                    "method": "世用背向法",
                    "description": "用神动+变爻冲世(背离)",
                    "ji_xiong": "凶",
                    "details": f"用神{primary_yong.di_zhi}动变{primary_yong.bian_di_zhi}"
                              f"冲世爻{shi_line.di_zhi}, 用背世离",
                }

    # 凶 pattern 2: 世动 + 变爻冲用
    if shi_line.is_moving and shi_line.bian_di_zhi:
        if not _has_hui_tou(shi_line):
            if LIU_CHONG.get(shi_line.bian_di_zhi) == primary_yong.di_zhi:
                return {
                    "method": "世用背向法",
                    "description": "世动+变爻冲用(背离)",
                    "ji_xiong": "凶",
                    "details": f"世爻{shi_line.di_zhi}动变{shi_line.bian_di_zhi}"
                              f"冲用神{primary_yong.di_zhi}, 世背用离",
                }

    # 凶 pattern 3: 用不动 + 应爻动 + 应变爻冲世
    if (not primary_yong.is_moving and ying_line and
            ying_line.is_moving and ying_line.bian_di_zhi):
        if not _has_hui_tou(ying_line):
            if LIU_CHONG.get(ying_line.bian_di_zhi) == shi_line.di_zhi:
                return {
                    "method": "世用背向法",
                    "description": "用不动+应爻动+变爻冲世(背离)",
                    "ji_xiong": "凶",
                    "details": f"应爻{ying_line.di_zhi}动变{ying_line.bian_di_zhi}"
                              f"冲世爻{shi_line.di_zhi}, 应冲世离",
                }

    return None


def _da_qiao_qu_bian(hexagram, dongbian_results, shi_line, yong_lines):
    """
    搭桥趋变法: 两个动爻通过变爻地支搭桥。
    """
    moving_analyses = dongbian_results.get("moving_analyses", {})
    moving_lines = [(pos, hexagram.lines[pos - 1])
                    for pos in moving_analyses]

    if len(moving_lines) < 2:
        return None

    # Find bridge: one dong_yao's bian_zhi == another dong_yao's ben_zhi
    for i, (pos_a, line_a) in enumerate(moving_lines):
        if not line_a.bian_di_zhi:
            continue
        for j, (pos_b, line_b) in enumerate(moving_lines):
            if i == j:
                continue
            if not line_b.bian_di_zhi:
                continue
            # Bridge: A's bian == B's ben
            if line_a.bian_di_zhi == line_b.di_zhi:
                # Check 4 conditions
                # (1) no direct sheng/ke between two dong toward world/yong
                a_wx = DI_ZHI_WU_XING[line_a.di_zhi]
                b_wx = DI_ZHI_WU_XING[line_b.di_zhi]
                shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]
                has_direct = (WU_XING_SHENG[a_wx] == shi_wx or
                              WU_XING_KE[a_wx] == shi_wx or
                              WU_XING_SHENG[b_wx] == shi_wx or
                              WU_XING_KE[b_wx] == shi_wx)
                if has_direct:
                    continue

                # (2) no回头生克 from each bian toward world/yong
                bian_a_wx = DI_ZHI_WU_XING[line_a.bian_di_zhi]
                bian_b_wx = DI_ZHI_WU_XING[line_b.bian_di_zhi]
                has_huitou_to_target = (
                    WU_XING_SHENG[bian_a_wx] == a_wx or
                    WU_XING_KE[bian_a_wx] == a_wx or
                    WU_XING_SHENG[bian_b_wx] == b_wx or
                    WU_XING_KE[bian_b_wx] == b_wx)
                if has_huitou_to_target:
                    continue

                # (3) two bian don't form san-he together
                bian_set = {line_a.bian_di_zhi, line_b.bian_di_zhi}
                forms_sanhe = False
                for wx, members in SAN_HE.items():
                    if bian_set.issubset(set(members)):
                        forms_sanhe = True
                        break
                if forms_sanhe:
                    continue

                # (4) jixiong by final bian's liu_qin
                final_bian_lq = line_b.bian_liu_qin
                if not final_bian_lq:
                    continue

                # Determine jixiong from final bian liu_qin
                ji_xiong = "中性"
                if final_bian_lq in ("子孙", "妻财"):
                    ji_xiong = "吉"
                elif final_bian_lq in ("官鬼",):
                    ji_xiong = "凶"

                return {
                    "method": "搭桥趋变法",
                    "description": (
                        f"第{pos_a}爻变{line_a.bian_di_zhi}="
                        f"第{pos_b}爻{line_b.di_zhi}, "
                        f"最终变{line_b.bian_di_zhi}"),
                    "ji_xiong": ji_xiong,
                    "details": (
                        f"搭桥: {line_a.di_zhi}->{line_a.bian_di_zhi}="
                        f"{line_b.di_zhi}->{line_b.bian_di_zhi}, "
                        f"终点六亲{final_bian_lq}"),
                }

    return None


def _qianlian_juhe(hexagram, shi_line, yong_lines, dongbian_results):
    """
    牵连聚合法: 动变之间形成连接或三合局。
    """
    if not yong_lines:
        return None

    primary_yong = yong_lines[0]
    yong_shen_liu_qin = primary_yong.liu_qin

    # Pattern 1: 世爻动变用神 = 牵连
    if shi_line.is_moving and shi_line.bian_liu_qin == yong_shen_liu_qin:
        return {
            "method": "牵连聚合法",
            "description": f"世爻动变{yong_shen_liu_qin}(用神), 世用牵连",
            "ji_xiong": "吉",
            "details": "世爻动化出用神六亲, 自身与所求之事相连",
        }

    # Pattern 2: 多动爻+变爻形成三合局含世和用
    moving_zhis = set()
    for line in hexagram.lines:
        if line.is_moving:
            moving_zhis.add(line.di_zhi)
            if line.bian_di_zhi:
                moving_zhis.add(line.bian_di_zhi)

    shi_zhi = shi_line.di_zhi
    yong_zhi = primary_yong.di_zhi

    for wx, members in SAN_HE.items():
        member_set = set(members)
        if shi_zhi in member_set and yong_zhi in member_set:
            if member_set.issubset(moving_zhis | {shi_zhi, yong_zhi}):
                return {
                    "method": "牵连聚合法",
                    "description": (
                        f"动变形成{wx}局三合, "
                        f"世({shi_zhi})用({yong_zhi})皆在局中"),
                    "ji_xiong": "吉",
                    "details": "世爻与用神通过三合局聚合, 所求之事与己相连",
                }

    return None


def _dairu_queren(hexagram, shi_line, yong_lines):
    """
    代入确认法(替身法): 找到与世/用同属性、相冲、相合的爻。
    """
    if not yong_lines:
        return None

    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]
    substitutes = []

    for line in hexagram.lines:
        if line.position == shi_line.position:
            continue
        if any(line.position == yl.position for yl in yong_lines):
            continue

        line_wx = DI_ZHI_WU_XING[line.di_zhi]
        relations = []

        # 同五行
        if line_wx == shi_wx:
            relations.append("同属性")
        # 六冲
        if LIU_CHONG.get(line.di_zhi) == shi_line.di_zhi:
            relations.append("相冲(对手)")
        # 六合
        he_info = LIU_HE.get(line.di_zhi)
        if he_info and he_info[0] == shi_line.di_zhi:
            relations.append("相合(朋友/配偶)")

        if relations:
            substitutes.append({
                "position": line.position,
                "di_zhi": line.di_zhi,
                "liu_qin": line.liu_qin,
                "relations": relations,
            })

    if not substitutes:
        return None

    details_parts = []
    for sub in substitutes[:3]:
        details_parts.append(
            f"第{sub['position']}爻{sub['di_zhi']}{sub['liu_qin']}"
            f"({','.join(sub['relations'])})")

    return {
        "method": "代入确认法",
        "description": f"找到{len(substitutes)}个替身/代入爻",
        "ji_xiong": "中性",
        "details": "替身: " + "; ".join(details_parts),
    }


def _jianyao_zuge(hexagram, shi_line, yong_lines, wangshuai_results,
                  dongbian_results):
    """
    间爻阻隔法: 世爻与用神之间的爻如果旺相或有用动, 形成阻隔。
    """
    if not yong_lines:
        return None

    primary_yong = yong_lines[0]
    shi_pos = shi_line.position
    yong_pos = primary_yong.position

    if shi_pos == yong_pos:
        return None

    min_pos = min(shi_pos, yong_pos)
    max_pos = max(shi_pos, yong_pos)

    if max_pos - min_pos <= 1:
        return None

    # Get lines between shi and yong (exclusive)
    jian_yao = []
    useful_moving = dongbian_results.get("useful_moving", [])

    for pos in range(min_pos + 1, max_pos):
        line = hexagram.lines[pos - 1]
        ws = wangshuai_results[pos - 1]
        is_obstruction = False

        if ws["overall"] == "旺":
            is_obstruction = True
        elif pos in useful_moving:
            is_obstruction = True

        if is_obstruction:
            jian_yao.append({
                "position": pos,
                "di_zhi": line.di_zhi,
                "liu_qin": line.liu_qin,
                "reason": "旺相" if ws["overall"] == "旺" else "有用动爻",
            })

    if not jian_yao:
        return None

    details_parts = [
        f"第{j['position']}爻{j['di_zhi']}{j['liu_qin']}({j['reason']})"
        for j in jian_yao
    ]

    return {
        "method": "间爻阻隔法",
        "description": f"世({shi_pos})与用({yong_pos})之间有{len(jian_yao)}个阻隔爻",
        "ji_xiong": "凶",
        "details": "阻隔: " + "; ".join(details_parts),
    }
