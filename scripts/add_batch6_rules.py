# -*- coding: utf-8 -*-
"""添加第六批6个builder函数"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

batch6_builders = r'''

def _fu_gui_ju_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """医药病不求医：福鬼俱空，当不治而自愈。
    原文：福鬼俱空，当不治而自愈；子官皆动，宜内补而外修。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_fu_gui_ju_kong",
        priority=64,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                {
                    "op": "OR",
                    "children": [
                        _line_liu_qin("shi", "子孙"),
                        _line_liu_qin("shi", "官鬼"),
                    ],
                },
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：医药福鬼俱空自愈",
        explanation="《黄金策》云：福鬼俱空，当不治而自愈。疾病占中福神子孙或官鬼空亡，病势自退，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "fu_gui_ju_kong"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _hun_cai_gui_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻：如逢财鬼空亡，乃婚姻之大忌。
    原文：如逢财鬼空亡，乃婚姻之大忌；苟遇阴阳得位，实天命之所关。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_cai_gui_kong",
        priority=65,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                {
                    "op": "OR",
                    "children": [
                        _line_liu_qin("shi", "妻财"),
                        _line_liu_qin("shi", "官鬼"),
                    ],
                },
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：婚姻财鬼空亡大忌",
        explanation="《黄金策》云：如逢财鬼空亡，乃婚姻之大忌。婚姻占中财爻或官鬼空亡，大忌之象，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_cai_gui_kong"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _cai_hua_zi_sun(judgement: dict[str, Any]) -> dict[str, Any]:
    """产育：财化子孙，分娩即当勿药喜。
    原文：胎临官鬼，怀胎便有采薪忧；财化子孙，分娩即当勿药喜。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_hua_zi_sun",
        priority=66,
        conditions={
            "op": "AND",
            "children": [
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "子孙"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：产育财化子孙勿药喜",
        explanation="《黄金策》云：财化子孙，分娩即当勿药喜。财爻动化子孙，分娩吉兆，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cai_hua_zi_sun"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _cai_fu_chi_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财：六畜血财,尤喜福兴持世。
    原文：六畜血财,尤喜福兴持世。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_fu_chi_shi",
        priority=67,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                _line_liu_qin("shi", "子孙"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：求财福神持世",
        explanation="《黄金策》云：六畜血财,尤喜福兴持世。求财占中子孙爻持世，福神临身得利，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cai_fu_chi_shi"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _fu_hua_ji_yao(judgement: dict[str, Any]) -> dict[str, Any]:
    """医药：福化忌爻，误服杀身之恶剂。
    原文：福化忌爻，误服杀身之恶剂；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_fu_hua_ji_yao",
        priority=68,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_liu_qin("shi", "子孙"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "官鬼"},
                        {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "兄弟"},
                    ],
                },
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：医药福化忌爻误服",
        explanation="《黄金策》云：福化忌爻，误服杀身之恶剂。疾病占中子孙爻动化官鬼或兄弟，用药有误之兆，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "fu_hua_ji_yao"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _hun_shi_ying_hua_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻：世应化空，始成而终悔。
    原文：世应化空，始成而终悔。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_shi_ying_hua_kong",
        priority=69,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：婚姻世应化空始成终悔",
        explanation="《黄金策》云：世应化空，始成而终悔。婚姻占中世应皆空，先成后悔之兆，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_shi_ying_hua_kong"},
            {"type": "score_delta", "value": -1},
        ],
    )
'''

# 在_ying_ke_shi之后、AUTO_COMPILE_TEMPLATES之前插入
marker = "AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {"
insert_pos = content.find(marker)
if insert_pos > 0:
    content = content[:insert_pos] + batch6_builders + '\n\n' + content[insert_pos:]
    print("Inserted batch6 builders")
else:
    print("Could not find insertion point")

# 更新字典末尾
old_end = '''    "classic_huangjince_2c5fd1238961": _ying_ke_shi,
}'''

new_end = '''    "classic_huangjince_2c5fd1238961": _ying_ke_shi,
    # 第六批：6个新增模板
    "classic_huangjince_0136069ef46b": _fu_gui_ju_kong,
    "classic_huangjince_7e599b005c33": _hun_cai_gui_kong,
    "classic_huangjince_d4610eaac6a5": _cai_hua_zi_sun,
    "classic_huangjince_b5b2d8a74803": _cai_fu_chi_shi,
    "classic_huangjince_cd1e3335381f": _fu_hua_ji_yao,
    "classic_huangjince_9dd8f3982e60": _hun_shi_ying_hua_kong,
}'''

if old_end in content:
    content = content.replace(old_end, new_end)
    print("Updated AUTO_COMPILE_TEMPLATES")
else:
    print("Could not find old end marker")

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Batch 6 builders added")
