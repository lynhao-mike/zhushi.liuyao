# -*- coding: utf-8 -*-
"""第7批: 追加8个builder函数,覆盖总断千金赋/婚姻/词讼/种作"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

batch7_builders = r'''

def _dong_bian_jiao_zheng(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 动为始变为终最怕交争 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_dong_bian_jiao_zheng",
        priority=70,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "in", "value": ["官鬼", "兄弟"]},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 动变交争世爻化忌",
        explanation="《黄金策》云: 动为始,变为终,最怕交争。世爻动而化忌神(官鬼/兄弟),可作凶象候选证据。",
        effects=[{"type": "sign", "value": "dong_bian_jiao_zheng"}, {"type": "score_delta", "value": -1}],
    )


def _zi_kong_hua_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 自空化空必成凶咎 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_zi_kong_hua_kong",
        priority=71,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 自空化空必成凶咎",
        explanation="《黄金策》云: 自空化空,必成凶咎。世爻自身空亡又发动,事主落空更兼变动,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "zi_kong_hua_kong"}, {"type": "score_delta", "value": -1}],
    )


def _he_zhu_chong_po(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 如逢合住须冲破以成功 -> 中性"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_he_zhu_chong_po",
        priority=72,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="平",
        pattern="经典候选: 合住须冲破",
        explanation="《黄金策》云: 如逢合住,须冲破以成功。世应合住事情纠缠,须外力冲破方能成事,可作平象候选证据。",
        effects=[{"type": "sign", "value": "he_zhu_chong_po"}, {"type": "score_delta", "value": 0}],
    )


def _xiu_qiu_sheng_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 若遇休囚必生旺而成事 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_xiu_qiu_sheng_wang",
        priority=73,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "休"},
                {"fact_type": "relationship.sheng", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 休囚得生旺而成事",
        explanation="《黄金策》云: 若遇休囚,必生旺而成事。世爻休囚而得生助,则事终可成,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "xiu_qiu_sheng_wang"}, {"type": "score_delta", "value": 1}],
    )


def _hun_liu_he(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 六合则易而且吉 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_liu_he",
        priority=74,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 婚姻六合则易且吉",
        explanation="《黄金策》云: 六合则易而且吉。婚姻占世应六合,双方和合易成,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "hun_liu_he"}, {"type": "score_delta", "value": 1}],
    )


def _hun_liu_chong(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 六冲则难而又凶 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_liu_chong",
        priority=75,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.chong", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 婚姻六冲难而且凶",
        explanation="《黄金策》云: 六冲则难而又凶。婚姻占世应相冲,双方冲突难成,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "hun_liu_chong"}, {"type": "score_delta", "value": -1}],
    )


def _hun_ri_he_bi_he(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 如日合而世应比和因人成事 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_ri_he_bi_he",
        priority=76,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 婚姻日合世应比和",
        explanation="《黄金策》云: 如日合而世应比和,因人成事。婚姻占世应相合或比和,可借外力成事,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "hun_ri_he_bi_he"}, {"type": "score_delta", "value": 1}],
    )


def _cisong_shi_wang_ying_shuai(judgement: dict[str, Any]) -> dict[str, Any]:
    """词讼: 应乃对头要见休囚死绝;世为原告宜临帝旺长生 -> 吉(世旺应衰)"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cisong_shi_wang_ying_shuai",
        priority=77,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "in", "value": ["旺", "相"]},
                    ],
                },
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "ying", "relation": "in", "value": ["衰", "休", "囚"]},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 词讼世旺应衰",
        explanation="《黄金策》云: 应乃对头,要见休囚死绝;世为原告,宜临帝旺长生。词讼占中世旺应衰,原告势强,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cisong_shi_wang_ying_shuai"}, {"type": "score_delta", "value": 1}],
    )
'''

# 在上一批之后插入
marker = "AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {"
insert_pos = content.find(marker)
if insert_pos > 0:
    content = content[:insert_pos] + batch7_builders + '\n\n' + content[insert_pos:]
    print("Inserted batch7 builders")
else:
    print("Could not find insertion point")

# 更新字典末尾
old_end = '''    "classic_huangjince_9dd8f3982e60": _hun_shi_ying_hua_kong,
}'''

new_end = '''    "classic_huangjince_9dd8f3982e60": _hun_shi_ying_hua_kong,
    # 第七批: 8个新增模板
    "classic_huangjince_ea7f03d649e3": _dong_bian_jiao_zheng,
    "classic_huangjince_3df5877fb633": _zi_kong_hua_kong,
    "classic_huangjince_392c4fc88df6": _he_zhu_chong_po,
    "classic_huangjince_4026a281d537": _xiu_qiu_sheng_wang,
    "classic_huangjince_f5db80eae9d2": _hun_liu_he,
    "classic_huangjince_c4e29ffd49b4": _hun_liu_chong,
    "classic_huangjince_b6f05d3e19cf": _hun_ri_he_bi_he,
    "classic_huangjince_903555b3f3bb": _cisong_shi_wang_ying_shuai,
}'''

if old_end in content:
    content = content.replace(old_end, new_end)
    print("Updated AUTO_COMPILE_TEMPLATES")
else:
    print("Could not find old end marker")

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Batch 7 builders added")
