"""
连动/复合动爻分析模块 - Lian-Dong (Complex Moving Line) System

分析多个动爻形成的连动链(生链/克链)以及三合局吉凶判断。
核心规则:
1. 三合局优先于单爻连动
2. 连动必须有明确的目标方向(世爻或用神)
3. 自占自事时, 世爻不参与连动(只接收)
4. 三合局一旦成立, 成员不再受个体规则(回头克/化破绝)约束(世爻除外)
"""

from .data import (
    DI_ZHI_WU_XING,
    WU_XING_SHENG, WU_XING_KE,
    SAN_HE, SAN_HE_BY_ZHI,
    LIU_CHONG,
)


def analyze_liandong(hexagram, dongbian_results, wangshuai_results,
                     yong_shen_lines, shi_line, question_type="other"):
    """
    连动分析主入口。

    Args:
        hexagram: Hexagram对象
        dongbian_results: 动变分析结果
        wangshuai_results: 旺衰分析结果
        yong_shen_lines: 用神爻列表
        shi_line: 世爻
        question_type: 问事类型

    Returns:
        dict: {
            "san_he_jixiong": 三合局吉凶分析结果列表,
            "san_he_priority": bool 是否有三合局优先,
            "jia_san_he": 假三合局列表,
            "liandong_chains": 连动链列表,
            "san_he_override_individual": bool 三合局是否覆盖个体规则,
        }
    """
    result = {
        "san_he_jixiong": [],
        "san_he_priority": False,
        "jia_san_he": [],
        "liandong_chains": [],
        "san_he_override_individual": False,
    }

    if not shi_line:
        return result

    month_zhi = hexagram.gan_zhi["month_zhi"]
    day_zhi = hexagram.gan_zhi["day_zhi"]

    # 获取动爻信息
    moving_lines = [l for l in hexagram.lines if l.is_moving]
    moving_analyses = dongbian_results.get("moving_analyses", {})
    useful_moving = dongbian_results.get("useful_moving", [])

    # Step 1: 三合局优先分析
    san_he_ju = dongbian_results.get("san_he_ju", [])
    if san_he_ju:
        result["san_he_priority"] = True
        result["san_he_override_individual"] = True

        # 检查假三合局
        jia_san_he = _detect_jia_san_he(hexagram, san_he_ju, moving_lines)
        result["jia_san_he"] = jia_san_he

        # 对每个真三合局进行吉凶判断
        jia_members_set = set()
        for jsh in jia_san_he:
            for m in jsh.get("members", []):
                jia_members_set.add(m)

        for sh in san_he_ju:
            # 检查是否为假三合
            is_jia = any(m in jia_members_set for m in sh["members"])
            if is_jia:
                continue

            jixiong = _judge_san_he_jixiong(
                sh, hexagram, shi_line, yong_shen_lines,
                wangshuai_results, moving_analyses,
                month_zhi, day_zhi, question_type
            )
            result["san_he_jixiong"].append(jixiong)

    # Step 2: 连动链分析(三合局不存在或处理完后)
    if moving_lines and len(moving_lines) >= 2:
        chains = _find_liandong_chains(
            hexagram, moving_lines, shi_line, yong_shen_lines,
            moving_analyses, useful_moving, question_type
        )
        result["liandong_chains"] = chains

    return result


def _find_san_he_priority(hexagram, dongbian_results):
    """
    检查动爻中是否有三合局。三合局优先于个体连动。

    Returns:
        list: 三合局列表(来自dongbian_results)
    """
    return dongbian_results.get("san_he_ju", [])


def _detect_jia_san_he(hexagram, san_he_ju, moving_lines):
    """
    检测假三合局。

    假三合局条件: 某个动爻(不在该三合局内)冲三合局成员之一(双方都必须是动爻)。

    Args:
        hexagram: Hexagram对象
        san_he_ju: 三合局列表
        moving_lines: 动爻列表

    Returns:
        list: 假三合局信息
    """
    jia_results = []
    moving_zhis = {l.di_zhi for l in moving_lines}

    for sh in san_he_ju:
        members = set(sh["members"])
        is_jia = False
        clash_info = ""

        for member_zhi in sh["members"]:
            # 找冲该成员的地支
            chong_zhi = LIU_CHONG.get(member_zhi)
            # 冲方必须是动爻, 且冲方不在该三合局成员中
            if chong_zhi and chong_zhi in moving_zhis and chong_zhi not in members:
                is_jia = True
                clash_info = f"动爻{chong_zhi}冲三合局成员{member_zhi}"
                break

        if is_jia:
            jia_results.append({
                "wu_xing": sh["wu_xing"],
                "members": sh["members"],
                "reason": clash_info,
            })

    return jia_results


def _judge_san_he_jixiong(san_he, hexagram, shi_line, yong_shen_lines,
                           wangshuai_results, moving_analyses,
                           month_zhi, day_zhi, question_type):
    """
    判断单个三合局的吉凶。

    5吉:
    1. 用神与世爻同在三合局内 + 非忌神局 + 世爻无回头克
    2. 含用神在内的三合局动而生旺世爻
    3. 有用神动生世爻 + 世爻构成三合局 + 无回头克
    4. 动爻构成三合局生旺用神 + 世爻得力(有日月扶)
    5. 动爻构成三合局生旺世爻 + 用神旺相

    5凶:
    1. 世爻在三合局内但动变回头克
    2. 用神构成三合局动克世爻(例外: 疾病/忧患/求财/行人)
    3. 动爻构成三合局动克用神
    4. 世爻与合局无生克关系 + 用神在三合局内 + 世爻在局外
    5. 世爻没与用神构成三合局 + 反而与用神相冲之爻合成三合局
    """
    members = san_he["members"]
    san_he_wx = san_he["wu_xing"]
    shi_wx = DI_ZHI_WU_XING[shi_line.di_zhi]

    # 判断世爻是否在三合局中
    shi_in_ju = shi_line.di_zhi in members

    # 判断用神是否在三合局中
    yong_in_ju = False
    yong_wx = None
    for yl in yong_shen_lines:
        if yl.di_zhi in members:
            yong_in_ju = True
            yong_wx = DI_ZHI_WU_XING[yl.di_zhi]
            break

    if not yong_wx and yong_shen_lines:
        yong_wx = DI_ZHI_WU_XING[yong_shen_lines[0].di_zhi]

    # 三合局五行与世爻的关系
    ju_sheng_shi = WU_XING_SHENG[san_he_wx] == shi_wx  # 局生世
    ju_ke_shi = WU_XING_KE[san_he_wx] == shi_wx  # 局克世

    # 三合局五行与用神的关系
    ju_sheng_yong = False
    ju_ke_yong = False
    if yong_wx:
        ju_sheng_yong = WU_XING_SHENG[san_he_wx] == yong_wx
        ju_ke_yong = WU_XING_KE[san_he_wx] == yong_wx

    # 世爻是否有回头克
    shi_hui_tou_ke = False
    if shi_line.position in moving_analyses:
        shi_ma = moving_analyses[shi_line.position]
        if "回头克" in shi_ma.get("趋衰", []):
            shi_hui_tou_ke = True

    # 世爻是否得日月扶
    shi_has_support = _has_day_month_support(shi_line.di_zhi, month_zhi, day_zhi)

    # 用神是否旺相
    yong_is_wang = False
    for yl in yong_shen_lines:
        ws = wangshuai_results[yl.position - 1]
        if ws["overall"] == "旺":
            yong_is_wang = True
            break

    # 是否为忌神局 (三合局五行克用神)
    is_ji_shen_ju = ju_ke_yong

    # =========================================================================
    # 5吉判断
    # =========================================================================

    # 吉1: 用神与世爻同在三合局内 + 非忌神局 + 世爻无回头克
    if shi_in_ju and yong_in_ju and not is_ji_shen_ju and not shi_hui_tou_ke:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "用世同在三合局(吉)",
            "ji_xiong": "吉",
            "explanation": f"用神与世爻同在{san_he_wx}局内, 非忌神局且世爻无回头克, 吉",
        }

    # 吉2: 含用神在内的三合局动而生旺世爻
    if yong_in_ju and ju_sheng_shi:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "三合局含用神生世(吉)",
            "ji_xiong": "吉",
            "explanation": f"含用神在内的{san_he_wx}三合局生旺世爻{shi_wx}, 吉",
        }

    # 吉3: 有用神动生世爻 + 世爻构成三合局 + 无回头克
    yong_dong_sheng_shi = False
    for yl in yong_shen_lines:
        if yl.is_moving:
            yl_wx = DI_ZHI_WU_XING[yl.di_zhi]
            if WU_XING_SHENG[yl_wx] == shi_wx:
                yong_dong_sheng_shi = True
                break
    if yong_dong_sheng_shi and shi_in_ju and not shi_hui_tou_ke:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "用神动生世+世在三合局(吉)",
            "ji_xiong": "吉",
            "explanation": f"用神动生世爻, 世爻在{san_he_wx}三合局中且无回头克, 吉",
        }

    # 吉4: 动爻构成三合局生旺用神 + 世爻得力(有日月扶)
    if ju_sheng_yong and shi_has_support:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "三合局生用神+世得力(吉)",
            "ji_xiong": "吉",
            "explanation": f"{san_he_wx}三合局生旺用神, 世爻得日月扶助, 吉",
        }

    # 吉5: 动爻构成三合局生旺世爻 + 用神旺相
    if ju_sheng_shi and yong_is_wang:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "三合局生世+用神旺(吉)",
            "ji_xiong": "吉",
            "explanation": f"{san_he_wx}三合局生旺世爻, 用神旺相, 吉",
        }

    # =========================================================================
    # 5凶判断
    # =========================================================================

    # 凶1: 世爻在三合局内但动变回头克
    if shi_in_ju and shi_hui_tou_ke:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "世在三合局但回头克(凶)",
            "ji_xiong": "凶",
            "explanation": f"世爻在{san_he_wx}三合局内但动变回头克, 凶",
        }

    # 凶2: 用神构成三合局动克世爻 (例外: 疾病/忧患/求财/行人)
    if yong_in_ju and ju_ke_shi:
        exception_types = ("bing", "youHuan", "cai", "xingRen")
        if question_type in exception_types:
            return {
                "wu_xing": san_he_wx,
                "members": members,
                "pattern": f"三合局克世({question_type}特例吉)",
                "ji_xiong": "吉",
                "explanation": f"用神在{san_he_wx}三合局克世, 但{question_type}类为特例, 吉",
            }
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "三合局含用神克世(凶)",
            "ji_xiong": "凶",
            "explanation": f"用神构成{san_he_wx}三合局动克世爻, 凶",
        }

    # 凶3: 动爻构成三合局动克用神
    if ju_ke_yong and not yong_in_ju:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "三合局克用神(凶)",
            "ji_xiong": "凶",
            "explanation": f"{san_he_wx}三合局动克用神, 凶",
        }

    # 凶4: 世爻与合局无生克关系 + 用神在三合局内 + 世爻在局外
    shi_no_relation = (not ju_sheng_shi and not ju_ke_shi and
                       san_he_wx != shi_wx and
                       WU_XING_SHENG[shi_wx] != san_he_wx and
                       WU_XING_KE[shi_wx] != san_he_wx)
    if shi_no_relation and yong_in_ju and not shi_in_ju:
        return {
            "wu_xing": san_he_wx,
            "members": members,
            "pattern": "世与局无关+用在局内(凶)",
            "ji_xiong": "凶",
            "explanation": f"世爻与{san_he_wx}三合局无生克关系, 用神在局内世在局外, 凶",
        }

    # 凶5: 世爻没与用神构成三合局 + 反而与用神相冲之爻合成三合局
    if not yong_in_ju and shi_in_ju:
        # 检查三合局中是否有与用神相冲的爻
        has_chong_yong = False
        for yl in yong_shen_lines:
            yong_chong = LIU_CHONG.get(yl.di_zhi)
            if yong_chong and yong_chong in members:
                has_chong_yong = True
                break
        if has_chong_yong:
            return {
                "wu_xing": san_he_wx,
                "members": members,
                "pattern": "世与冲用之爻合局(凶)",
                "ji_xiong": "凶",
                "explanation": f"世爻与用神相冲之爻合成{san_he_wx}三合局, 凶",
            }

    # 无明显吉凶模式
    return {
        "wu_xing": san_he_wx,
        "members": members,
        "pattern": "三合局(平)",
        "ji_xiong": "平",
        "explanation": f"{san_he_wx}三合局无明显吉凶倾向",
    }


def _find_liandong_chains(hexagram, moving_lines, shi_line, yong_shen_lines,
                           moving_analyses, useful_moving, question_type):
    """
    寻找连动链(生链和克链)。

    连动链条件:
    1. 多个动爻形成连续的生或克关系
    2. 链必须有明确目标方向(世爻或用神)
    3. 自占自事时, 世爻不参与连动(只接收)

    Returns:
        list: 连动链信息
    """
    chains = []

    # 获取有效动爻(排除无用动爻)
    valid_moving = []
    for line in moving_lines:
        if line.position in useful_moving:
            valid_moving.append(line)

    if len(valid_moving) < 2:
        return chains

    # 确定目标爻(世爻或用神)
    targets = []
    if shi_line:
        targets.append(("世爻", shi_line))
    for yl in yong_shen_lines:
        if not yl.is_shi:  # 避免重复
            targets.append(("用神", yl))

    # 自占自事: 世爻不参与连动(只接收)
    actor_lines = []
    for line in valid_moving:
        if line.is_shi:
            continue  # 世爻不作为连动的发起者
        actor_lines.append(line)

    if not actor_lines:
        return chains

    # 寻找生链: A生B生C -> 目标
    sheng_chains = _analyze_liandong_sheng(actor_lines, targets, hexagram)
    chains.extend(sheng_chains)

    # 寻找克链: A克B, C克目标
    ke_chains = _analyze_liandong_ke(actor_lines, targets, hexagram)
    chains.extend(ke_chains)

    return chains


def _analyze_liandong_sheng(moving_lines, targets, hexagram):
    """
    分析连动生链。

    多个动爻形成链式生关系: A生B生C, C生/作用于目标。
    生链的最终效果: 增强链末端的力量, 使其对目标的生或克更有力。

    Returns:
        list: 生链信息
    """
    chains = []

    for target_name, target_line in targets:
        target_wx = DI_ZHI_WU_XING[target_line.di_zhi]

        # 建立五行到动爻的映射
        wx_to_lines = {}
        for line in moving_lines:
            if line.position == target_line.position:
                continue
            wx = DI_ZHI_WU_XING[line.di_zhi]
            if wx not in wx_to_lines:
                wx_to_lines[wx] = []
            wx_to_lines[wx].append(line)

        # 寻找生链: 从某个动爻开始, 沿着五行相生方向, 最终到达目标
        # 寻找 X -> Y -> target 的模式 (X生Y, Y生target)
        for wx, lines in wx_to_lines.items():
            # wx生的五行
            next_wx = WU_XING_SHENG[wx]
            if next_wx in wx_to_lines:
                # next_wx生target_wx?
                if WU_XING_SHENG[next_wx] == target_wx:
                    # 找到生链: wx -> next_wx -> target
                    chain_members = []
                    chain_members.extend(lines)
                    chain_members.extend(wx_to_lines[next_wx])

                    chains.append({
                        "type": "生链",
                        "chain": [f"{l.di_zhi}({DI_ZHI_WU_XING[l.di_zhi]})"
                                  for l in chain_members],
                        "target": f"{target_name}({target_line.di_zhi}{target_wx})",
                        "effect": "生",
                        "explanation": (
                            f"{wx}生{next_wx}生{target_wx}, "
                            f"连动生链增强{target_name}力量"
                        ),
                    })

            # 也检查直接: wx生target_wx, 且有另一爻生wx
            if WU_XING_SHENG[wx] == target_wx:
                # 寻找生wx的动爻
                source_wx = None
                for sw, sl in wx_to_lines.items():
                    if sw != wx and WU_XING_SHENG[sw] == wx:
                        source_wx = sw
                        break
                if source_wx:
                    chain_members = []
                    chain_members.extend(wx_to_lines[source_wx])
                    chain_members.extend(lines)
                    chains.append({
                        "type": "生链",
                        "chain": [f"{l.di_zhi}({DI_ZHI_WU_XING[l.di_zhi]})"
                                  for l in chain_members],
                        "target": f"{target_name}({target_line.di_zhi}{target_wx})",
                        "effect": "生",
                        "explanation": (
                            f"{source_wx}生{wx}生{target_wx}, "
                            f"连动生链增强{target_name}力量"
                        ),
                    })

    # 去重
    seen = set()
    unique_chains = []
    for c in chains:
        key = (c["type"], tuple(c["chain"]), c["target"])
        if key not in seen:
            seen.add(key)
            unique_chains.append(c)

    return unique_chains


def _analyze_liandong_ke(moving_lines, targets, hexagram):
    """
    分析连动克链。

    多个动爻形成克关系: 当多个动爻都克同一目标时, 力量叠加。
    当动爻之间互克时, 计算净力方向。

    Returns:
        list: 克链信息
    """
    chains = []

    for target_name, target_line in targets:
        target_wx = DI_ZHI_WU_XING[target_line.di_zhi]

        # 找出所有克目标的动爻
        ke_target_lines = []
        for line in moving_lines:
            if line.position == target_line.position:
                continue
            line_wx = DI_ZHI_WU_XING[line.di_zhi]
            if WU_XING_KE[line_wx] == target_wx:
                ke_target_lines.append(line)

        if len(ke_target_lines) >= 2:
            # 多爻同克目标 - 力量叠加
            chains.append({
                "type": "克链(叠加)",
                "chain": [f"{l.di_zhi}({DI_ZHI_WU_XING[l.di_zhi]})"
                          for l in ke_target_lines],
                "target": f"{target_name}({target_line.di_zhi}{target_wx})",
                "effect": "克",
                "explanation": (
                    f"多动爻同克{target_name}{target_wx}, "
                    f"克力叠加"
                ),
            })

        # 寻找链式克: A克B, B克target
        wx_to_lines = {}
        for line in moving_lines:
            if line.position == target_line.position:
                continue
            wx = DI_ZHI_WU_XING[line.di_zhi]
            if wx not in wx_to_lines:
                wx_to_lines[wx] = []
            wx_to_lines[wx].append(line)

        for wx, lines in wx_to_lines.items():
            # wx克next_wx, next_wx克target?
            ke_wx = WU_XING_KE[wx]
            if ke_wx in wx_to_lines:
                if WU_XING_KE[ke_wx] == target_wx:
                    chain_members = []
                    chain_members.extend(lines)
                    chain_members.extend(wx_to_lines[ke_wx])
                    chains.append({
                        "type": "克链(间接)",
                        "chain": [f"{l.di_zhi}({DI_ZHI_WU_XING[l.di_zhi]})"
                                  for l in chain_members],
                        "target": f"{target_name}({target_line.di_zhi}{target_wx})",
                        "effect": "克(削弱后)",
                        "explanation": (
                            f"{wx}克{ke_wx}, {ke_wx}克{target_wx}, "
                            f"但{wx}克{ke_wx}削弱了克{target_name}的力量"
                        ),
                    })

    # 去重
    seen = set()
    unique_chains = []
    for c in chains:
        key = (c["type"], tuple(c["chain"]), c["target"])
        if key not in seen:
            seen.add(key)
            unique_chains.append(c)

    return unique_chains


def _has_day_month_support(line_zhi, month_zhi, day_zhi):
    """检查爻是否得日月之一扶助"""
    line_wx = DI_ZHI_WU_XING[line_zhi]
    month_wx = DI_ZHI_WU_XING[month_zhi]
    day_wx = DI_ZHI_WU_XING[day_zhi]

    # 月扶: 同五行或月生
    month_support = (month_wx == line_wx) or (WU_XING_SHENG[month_wx] == line_wx)
    # 日扶: 同五行或日生
    day_support = (day_wx == line_wx) or (WU_XING_SHENG[day_wx] == line_wx)
    # 临月/临日
    month_lin = (line_zhi == month_zhi)
    day_lin = (line_zhi == day_zhi)

    return month_support or day_support or month_lin or day_lin
