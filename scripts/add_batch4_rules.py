# -*- coding: utf-8 -*-
"""添加第四批规则模板到auto_compile脚本"""

import re

# 读取原文件
with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 定义要添加的3个函数
new_functions = '''

def _kaoshi_shi_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """考试章节：世爻旺相，吉象明显。
    原文：若在旺乡，则矜可矜而式可式。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_kaoshi_shi_wang",
        priority=55,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
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
        pattern="经典候选：考试世爻旺相",
        explanation="《黄金策》云：若在旺乡，则矜可矜而式可式。考试占中世爻居旺相之地，应试有利，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "kaoshi_shi_wang"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _cisong_shi_ying_sheng_he(judgement: dict[str, Any]) -> dict[str, Any]:
    """词讼章节：世应相生相合，和解有望。
    原文：相生相合，终成和好之情。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_cisong_shi_ying_sheng_he",
        priority=56,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "relationship.sheng", "subject": "shi", "object": "ying", "relation": "is_true"},
                        {"fact_type": "relationship.sheng", "subject": "ying", "object": "shi", "relation": "is_true"},
                        {"fact_type": "relationship.he", "subject": "shi", "object": "ying", "relation": "is_true"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：世应相生相合",
        explanation="《黄金策》云：相生相合，终成和好之情。世应相生或相合，词讼和解可期，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cisong_shi_ying_sheng_he"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _shiwu_chuxing_yong_sheng_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """失物/出行章节：用神生世，吉象。
    原文：人为利名忘却故乡生处，乐家无音信，全凭周易卦中推，要决归期但寻主象。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_shiwu_chuxing_yong_sheng_shi",
        priority=57,
        conditions={
            "op": "AND",
            "children": [
                {
                    "op": "OR",
                    "children": [
                        _question_type("shiwu"),
                        _question_type("chuxing"),
                    ],
                },
                _line_exists("primary_yong"),
                _line_exists("shi"),
                {"fact_type": "relationship.sheng", "subject": "primary_yong", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：失物/出行用神生世",
        explanation="《黄金策》云：要决归期但寻主象。失物或出行占中用神生世，主象有利，失物可寻行人可归，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "shiwu_chuxing_yong_sheng_shi"},
            {"type": "score_delta", "value": 1},
        ],
    )
'''

# 在AUTO_COMPILE_TEMPLATES之前插入新函数
pattern = r'(AUTO_COMPILE_TEMPLATES: dict\[str, RuleBuilder\] = \{)'
replacement = new_functions + '\n\n' + r'\1'
content = re.sub(pattern, replacement, content)

# 在AUTO_COMPILE_TEMPLATES字典中添加新映射
old_mapping = '    "classic_huangjince_56e35c8c5439": _chuxing_shi_ying_both_empty,\n}'
new_mapping = '''    "classic_huangjince_56e35c8c5439": _chuxing_shi_ying_both_empty,
    # 第四批：3个新增模板
    "classic_huangjince_e22183be6692": _kaoshi_shi_wang,
    "classic_huangjince_902d8f46b5d2": _cisong_shi_ying_sheng_he,
    "classic_huangjince_315234a45a5b": _shiwu_chuxing_yong_sheng_shi,
}'''
content = content.replace(old_mapping, new_mapping)

# 写回文件
with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully added 3 new builder functions for batch 4")
