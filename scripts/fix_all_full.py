# -*- coding: utf-8 -*-
"""添加缺失的第三批4个builder函数，并修复字典"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 第三批4个builder函数，插入在 _chuxing_shi_empty 之后、_kaoshi_shi_wang 之前
batch3_builders = r'''

def _bing_shi_fumu(judgement: dict[str, Any]) -> dict[str, Any]:
    """疾病章节：世持父母，药效不显之象。
    原文：世为敌者，父母加临，非比寻常之药饵。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_bing_shi_fumu",
        priority=49,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("shi"),
                _line_liu_qin("shi", "父母"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：疾病世持父母爻",
        explanation="《黄金策》云：世为敌者，父母加临，非比寻常之药饵。疾病占中世爻为父母，药效不显，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "bing_shi_fumu"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _hun_shi_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻章节：世爻旺相，吉象。
    原文：旺相在生乡，定有利名之志。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_hun_shi_wang",
        priority=48,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：婚姻世爻旺相",
        explanation="《黄金策》云：旺相在生乡，定有利名之志。婚姻占中世爻旺相，自身状态佳，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_shi_wang"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _kaoshi_shi_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """考试章节：世爻空亡，考试不利。
    原文：世若无根，难期雁塔之题。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_kaoshi_shi_empty",
        priority=47,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：考试世爻空亡",
        explanation="《黄金策》云：世若无根，难期雁塔之题。考试占中世爻空亡，自身根基不实，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "kaoshi_shi_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _chuxing_shi_ying_both_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """出行章节：世应皆空，出行不宜。
    原文：世应皆空，动则目前和好；旁爻少合，言其事后睽违。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_chuxing_shi_ying_both_empty",
        priority=46,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：出行世应皆空",
        explanation="《黄金策》云：世应皆空，动则目前和好；旁爻少合，言其事后睽违。出行占中世应双方皆空，内外条件均不具备，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "chuxing_shi_ying_both_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )
'''

# 在_chuxing_shi_empty结束之后、_kaoshi_shi_wang开始之前插入
marker = "\n\n\n\ndef _kaoshi_shi_wang("
insert_pos = content.find(marker)
if insert_pos > 0:
    content = content[:insert_pos] + batch3_builders + content[insert_pos:]
    print(f"Inserted batch3 builders at position {insert_pos}")
else:
    print("Could not find insertion point")

# 修复AUTO_COMPILE_TEMPLATES字典
old_dict = '''AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {
    "classic_huangjince_90e429f17b7c": _primary_yong_moving_decline,
    "classic_huangjince_6b9330281536": _shi_ying_empty_he,
    "classic_huangjince_e5b514484df7": _chuxing_ying_ke_shi,
    "classic_huangjince_d3ba2859902b": _chuxing_ying_empty,
    "classic_huangjince_3e9aa6a9b461": _hun_shi_ying_relationships,
    "classic_huangjince_eefbc0805e37": _hun_shi_ying_he,
    "classic_huangjince_e17691681a8f": _hun_ying_moving_or_empty,
    "classic_huangjince_2caba4ce3669": _hun_shi_ying_both_empty,
    "classic_huangjince_a346e5ba72f2": _bing_shi_ghost,
    "classic_huangjince_fe880f90b7d4": _chuxing_shi_empty,
}'''

new_dict = '''AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {
    "classic_huangjince_90e429f17b7c": _primary_yong_moving_decline,
    "classic_huangjince_6b9330281536": _shi_ying_empty_he,
    "classic_huangjince_e5b514484df7": _chuxing_ying_ke_shi,
    "classic_huangjince_d3ba2859902b": _chuxing_ying_empty,
    "classic_huangjince_3e9aa6a9b461": _hun_shi_ying_relationships,
    "classic_huangjince_eefbc0805e37": _hun_shi_ying_he,
    "classic_huangjince_e17691681a8f": _hun_ying_moving_or_empty,
    "classic_huangjince_2caba4ce3669": _hun_shi_ying_both_empty,
    "classic_huangjince_a346e5ba72f2": _bing_shi_ghost,
    "classic_huangjince_fe880f90b7d4": _chuxing_shi_empty,
    # 第三批
    "classic_huangjince_fb65e40b559f": _bing_shi_fumu,
    "classic_huangjince_dd137759d041": _hun_shi_wang,
    "classic_huangjince_fda6078e13b5": _kaoshi_shi_empty,
    "classic_huangjince_56e35c8c5439": _chuxing_shi_ying_both_empty,
    # 第四批：3个新增模板
    "classic_huangjince_e22183be6692": _kaoshi_shi_wang,
    "classic_huangjince_902d8f46b5d2": _cisong_shi_ying_sheng_he,
    "classic_huangjince_315234a45a5b": _shiwu_chuxing_yong_sheng_shi,
}'''

if old_dict in content:
    content = content.replace(old_dict, new_dict)
    print("Replaced AUTO_COMPILE_TEMPLATES dict")
else:
    print("Could not find old dict pattern")

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
