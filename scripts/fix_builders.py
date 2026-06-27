# -*- coding: utf-8 -*-
"""修复auto_compile脚本：添加第三批和第四批的builder函数及TEMPLATES映射"""
import re

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 第三批的4个builder函数（在_chuxing_ying_empty定义之后、_hun_shi_ying_relationships之前插入）
batch3_functions = r'''

def _hun_ying_moving_or_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻章节：应爻动或空，婚姻不定。
    原文：应位或兴或空，世动或冲或并；大率应期难定。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_hun_ying_moving_or_empty",
        priority=50,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("ying"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.is_moving", "subject": "ying", "relation": "is_true"},
                        {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
                    ],
                },
            ],
        },
        ji_xiong="待审",
        pattern="经典候选：婚姻应爻发动或空亡",
        explanation="《黄金策》云：应位或兴或空，世动或冲或并；大率应期难定。婚姻占中应爻发动或空亡，应交难定，可作待审候选证据。",
        effects=[
            {"type": "sign", "value": "hun_ying_moving_or_empty"},
            {"type": "score_delta", "value": 0},
        ],
    )


def _hun_shi_ying_both_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻章节：世应皆空，婚姻不成之象。
    原文：世应皆空，动则目前和好；旁爻少合，言其事后睽违。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_hun_shi_ying_both_empty",
        priority=51,
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
        pattern="经典候选：婚姻世应皆空",
        explanation="《黄金策》云：世应皆空，动则目前和好；旁爻少合，言其事后睽违。婚姻占中世应双方皆空亡，关系基础不实，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "hun_shi_ying_both_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _bing_shi_ghost(judgement: dict[str, Any]) -> dict[str, Any]:
    """疾病章节：世爻官鬼，病缠身之象。
    原文：身临鬼动，剖腹陷胸；命在空亡，离乡远嫁。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_bing_shi_ghost",
        priority=52,
        conditions={
            "op": "AND",
            "children": [
                _question_type("bing"),
                _line_exists("shi"),
                {"fact_type": "line.liu_qin", "subject": "shi", "relation": "eq", "value": "官鬼"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：疾病世爻临官鬼",
        explanation="《黄金策》云：身临鬼动，剖腹陷胸。疾病占中世爻为官鬼，病缠身之象，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "bing_shi_ghost"},
            {"type": "score_delta", "value": -1},
        ],
    )


def _chuxing_shi_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """出行章节：世爻空亡，出行不利。
    原文：世爻临空，动则积忧而积闷。
    """
    return _base_rule(
        judgement,
        rule_id="dynamic_huangjince_chuxing_shi_empty",
        priority=53,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选：出行世爻空亡",
        explanation="《黄金策》云：世爻临空，动则积忧而积闷。出行占中世爻空亡，出行不利，可作凶象候选证据。",
        effects=[
            {"type": "sign", "value": "chuxing_shi_empty"},
            {"type": "score_delta", "value": -1},
        ],
    )
'''

# 插入第三批4个函数到_chuxing_ying_empty之后
pattern = r'def _chuxing_ying_empty\(judgement: dict\[str, Any\]\) -> dict\[str, Any\]:'
match = re.search(pattern, content)
if match:
    # 找到_chuxing_ying_empty函数结束位置（下一个def之前）
    func_start = match.start()
    # 搜索下一个def
    next_def = content.find('\ndef _hun', func_start)
    if next_def > 0:
        insert_pos = next_def
        # 在_chuxing_ying_empty函数后、_hun_shi_ying_relationships之前插入
        # 但注意 _chuxing_ying_empty 的结尾可能在别处
        # 更好的方法：在最后一行 _chuxing_ying_empty 的 effects 和 ) 之后
        pass

# 更简单的方法：在第四批函数之前插入第三批函数
# 先在文件末尾找到 `def _kaoshi_shi_wang` 或找到第四批函数插入点
# 查找第四批的3个函数是否已存在
if 'def _kaoshi_shi_wang' not in content:
    # 第四批函数不存在，需一并添加
    pass

# 直接找到_chuxing_ying_empty的return语句结束位置
lines = content.split('\n')
new_lines = []
batch3_inserted = False
batch4_inserted = False
in_batch4_funcs = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # 在 _chuxing_ying_empty 函数结束后插入第三批4个函数
    # 判断：遇到下一个 def _hun_shi_ying_relationships 时
    if line.strip().startswith('def _hun_shi_ying_relationships'):
        if not batch3_inserted:
            # 在 _hun_shi_ying_relationships 之前插入第三批函数
            new_lines.pop()  # 移除这一行
            new_lines.append(batch3_functions.strip())
            new_lines.append('\n\n')
            new_lines.append(line)
            batch3_inserted = True
    
    # 在 _bing_shi_ghost 函数结束后插入第四批3个函数
    if line.strip().startswith('def _bing_shi_ghost'):
        # 第四批函数加在第三批之后，不需要额外插入
        # 第三批中已经有_bing_shi_ghost和_chuxing_shi_empty
        pass
    
    # 修复AUTO_COMPILE_TEMPLATES字典
    if line.strip() == 'AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {':
        new_lines.append('    "classic_huangjince_fb65e40b559f": _bing_shi_fumu,')
        new_lines.append('    "classic_huangjince_dd137759d041": _hun_shi_wang,')
        new_lines.append('    "classic_huangjince_fda6078e13b5": _kaoshi_shi_empty,')
        new_lines.append('    "classic_huangjince_56e35c8c5439": _chuxing_shi_ying_both_empty,')

content = '\n'.join(new_lines)

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fix attempt completed")
