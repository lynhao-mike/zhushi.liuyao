# -*- coding: utf-8 -*-
"""添加第五批6个builder函数到auto_compile脚本,覆盖更多章节和问事类型"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# === 第五批6个builder函数 ===
batch5_builders = r'''

def _bing_ghost_moving(judgement: dict[str, Any]) -> dict[str, Any]:
    """医药病不求医：鬼动卦中，眼下速难取效。
    原文：鬼动卦中，眼下速难取效；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_bing_ghost_moving",
        priority=58,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                _line_liu_qin("shi", "官鬼"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：疾病世爻鬼动",
        explanation="《黄金策》云：鬼动卦中，眼下速难取效。疾病占中世爻临官鬼发动，病势当前难速效，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "bing_ghost_moving"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _guan_ke_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """避乱：最怕官爻克世，则必难回避。
    原文：最怕官爻克世，则必难回避；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_guan_ke_shi",
        priority=59,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "官鬼"),
                {"fact_type": "relationship.ke", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：官鬼克世",
        explanation="《黄金策》云：最怕官爻克世，则必难回避。官鬼爻克世爻，事势逼迫难以回避，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "guan_ke_shi"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _shi_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """身命：世居空位，终身作事无成。
    原文：世居空位，终身作事无成；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shi_empty",
        priority=60,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：世爻空亡",
        explanation="《黄金策》云：世居空位，终身作事无成。世爻空亡，自身根基不实，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "shi_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _cai_ghost_moving_sheng_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财：九流术士，偏宜鬼动生身。
    原文：九流术士，偏宜鬼动生身；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_ghost_moving_sheng_shi",
        priority=61,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                _line_liu_qin("shi", "官鬼"),
                {"fact_type": "relationship.sheng", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选：求财鬼动生身",
        explanation="《黄金策》云：九流术士，偏宜鬼动生身。求财占中鬼爻发动而生世爻，偏门得利，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "cai_ghost_moving_sheng_shi"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _shiwu_shi_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """失物：日旺月旺，纵未散而可寻。
    原文：自空化空，皆当置而勿问；日旺月旺，纵未散而可寻。
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shiwu_shi_wang",
        priority=62,
        conditions={
            "op": "AND",
            "children": [
                _question_type("shiwu"),
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
        pattern="经典候选：失物世爻旺相可寻",
        explanation="《黄金策》云：日旺月旺，纵未散而可寻。失物占中世爻旺相，失物纵未散亦可寻，可作吉象候选证据。",
        effects=[
            {"type": "sign", "value": "shiwu_shi_wang"},
            {"type": "score_delta", "value": 1},
        ],
    )


def _ying_ke_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """身命：世值凶而应克，愿听鸡鸣。
    原文：世值凶而应克，愿听鸡鸣；
    """
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_ying_ke_shi",
        priority=63,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_exists("ying"),
                {"fact_type": "relationship.ke", "subject": "ying", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：应克世",
        explanation="《黄金策》云：世值凶而应克，愿听鸡鸣。应爻克世爻，外部因素压制自身，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "ying_ke_shi"},
            {"type": "score_delta", "value": -1},
        ],
    )
'''

# 在_shiwu_chuxing_yong_sheng_shi之后、AUTO_COMPILE_TEMPLATES之前插入
marker = "AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {"
insert_pos = content.find(marker)
if insert_pos > 0:
    # 插入到marker之前（在_shiwu_chuxing_yong_sheng_shi函数结束后的空行位置）
    content = content[:insert_pos] + batch5_builders + '\n\n' + content[insert_pos:]
    print(f"Inserted batch5 builders before AUTO_COMPILE_TEMPLATES")
else:
    print("Could not find insertion point")

# 更新AUTO_COMPILE_TEMPLATES字典
# 找到末尾的 } 并添加新映射
old_end = '''    "classic_huangjince_315234a45a5b": _shiwu_chuxing_yong_sheng_shi,
}'''

new_end = '''    "classic_huangjince_315234a45a5b": _shiwu_chuxing_yong_sheng_shi,
    # 第五批：6个新增模板
    "classic_huangjince_e76a35169ca2": _bing_ghost_moving,
    "classic_huangjince_d6af404498fe": _guan_ke_shi,
    "classic_huangjince_e96377c94507": _shi_empty,
    "classic_huangjince_fa5b1788201c": _cai_ghost_moving_sheng_shi,
    "classic_huangjince_9df0de5a2802": _shiwu_shi_wang,
    "classic_huangjince_2c5fd1238961": _ying_ke_shi,
}'''

if old_end in content:
    content = content.replace(old_end, new_end)
    print("Updated AUTO_COMPILE_TEMPLATES dict")
else:
    print("Could not find old end of AUTO_COMPILE_TEMPLATES")

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Batch 5 builders added successfully")
