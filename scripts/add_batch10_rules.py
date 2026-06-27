# -*- coding: utf-8 -*-
"""
Batch 10: 添加第10批《黄金策》候选规则 builder 到自动编译脚本
涵盖: 婚姻、词讼、求财(3条)、求师
"""
import re
from pathlib import Path

# 6个新的 builder 函数
NEW_BUILDERS = '''
def _hun_gui_ke_fei_yao(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 鬼克飞爻,难嫁 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_gui_ke_fei_yao",
        priority=87,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("cai"),
                _line_exists("gui"),
                _relationship("ke", "gui", "cai"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 婚姻鬼克飞爻",
        explanation="《黄金策》云: 鬼克飞爻,果信绿窗之难嫁。婚占中官鬼克制财爻,女方处境艰难婚事难成,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "hun_gui_ke_fei_yao"}, {"type": "score_delta", "value": -1}],
    )


def _cisong_fu_dong_guan_hua_fu(judgement: dict[str, Any]) -> dict[str, Any]:
    """词讼: 父动官化福,事将成 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cisong_fu_dong_guan_hua_fu",
        priority=88,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("fumu"),
                {"fact_type": "line.is_moving", "subject": "fumu", "relation": "is_true"},
                _line_exists("gui"),
                {"fact_type": "line.is_moving", "subject": "gui", "relation": "is_true"},
                {"fact_type": "line.bian.liu_qin", "subject": "gui", "relation": "eq", "value": "子孙"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 词讼父动官化福",
        explanation="《黄金策》云: 父动而官化福爻,事将成而偶逢兜劝。词讼占中父母发动且官鬼化子孙,状纸已成而有调解之机,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cisong_fu_dong_guan_hua_fu"}, {"type": "score_delta", "value": 1}],
    )


def _cai_ju_he_fu_shen(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 财局合福神,万倍利源 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_ju_he_fu_shen",
        priority=89,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("cai"),
                _line_exists("zi"),
                _relationship("he", "cai", "zi"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财局合福神",
        explanation="《黄金策》云: 财局合福神,万倍利源可取。求财占中财爻与子孙六合,财源广进福神护持,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_ju_he_fu_shen"}, {"type": "score_delta", "value": 1}],
    )


def _cai_xiong_lian_gui_ke(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 兄连鬼克,口舌难逃 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_xiong_lian_gui_ke",
        priority=90,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("xiong"),
                _line_exists("gui"),
                _line_exists("shi"),
                _relationship("ke", "gui", "shi"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 求财兄连鬼克",
        explanation="《黄金策》云: 兄连鬼克,纷纷口舌难逃。求财占中兄弟官鬼同现且鬼克世,破财口舌并至,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_xiong_lian_gui_ke"}, {"type": "score_delta", "value": -1}],
    )


def _cai_dong_shen_xing(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 财动身兴,脱货宜 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_dong_shen_xing",
        priority=91,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("cai"),
                {"fact_type": "line.is_moving", "subject": "cai", "relation": "is_true"},
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "in", "value": ["旺", "相"]},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财动身兴",
        explanation="《黄金策》云: 脱货者,宜财动而身兴。求财占中财爻发动且世爻旺相,货物流通生意兴隆,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_dong_shen_xing"}, {"type": "score_delta", "value": 1}],
    )


def _qiushi_jing_he_fu_yao(judgement: dict[str, Any]) -> dict[str, Any]:
    """求师: 静合福爻,善诱 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_qiushi_jing_he_fu_yao",
        priority=92,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("fumu"),
                {"fact_type": "line.is_moving", "subject": "fumu", "relation": "is_true", "inverted": True},
                _line_exists("zi"),
                _relationship("he", "fumu", "zi"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求师静合福爻",
        explanation="《黄金策》云: 静合福爻,喜遇循循之善诱。求师占中父母静爻六合子孙,师长温和善于教导,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "qiushi_jing_he_fu_yao"}, {"type": "score_delta", "value": 1}],
    )
'''

# 6个新的模板条目
NEW_ENTRIES = '''
    "classic_huangjince_774d6b5442e0": _hun_gui_ke_fei_yao,
    "classic_huangjince_36842a66707c": _cisong_fu_dong_guan_hua_fu,
    "classic_huangjince_24d2e60b3f98": _cai_ju_he_fu_shen,
    "classic_huangjince_bb0611ef4c46": _cai_xiong_lian_gui_ke,
    "classic_huangjince_d41bfe9bbb31": _cai_dong_shen_xing,
    "classic_huangjince_525c267fac83": _qiushi_jing_he_fu_yao,
'''


def main():
    script_path = Path(__file__).parent / "auto_compile_huangjince_candidate_rules.py"
    content = script_path.read_text(encoding="utf-8")

    # 1. 在最后一个 builder 函数后插入新的 builders
    # 找到 _cai_kong_shi 函数的结束位置
    pattern = r'(def _cai_kong_shi\(judgement.*?\n    \)\n)\n\n(AUTO_COMPILE_TEMPLATES:)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError("无法找到 _cai_kong_shi 函数或 AUTO_COMPILE_TEMPLATES 字典的插入点")
    
    content = content[:match.end(1)] + '\n' + NEW_BUILDERS + '\n' + content[match.end(1):]

    # 2. 在 AUTO_COMPILE_TEMPLATES 字典的最后一个条目后插入新条目
    # 找到最后一个条目 (应该是 "classic_huangjince_992af61aee72": _cai_kong_shi,)
    pattern = r'("classic_huangjince_992af61aee72": _cai_kong_shi,)\n'
    match = re.search(pattern, content)
    if not match:
        raise ValueError("无法找到 AUTO_COMPILE_TEMPLATES 字典的最后一个条目")
    
    content = content[:match.end(1)] + '\n' + NEW_ENTRIES + content[match.end(1):]

    # 3. 写回文件
    script_path.write_text(content, encoding="utf-8")
    print(f"[OK] Added 6 new builder functions to {script_path}")
    print("  - _hun_gui_ke_fei_yao")
    print("  - _cisong_fu_dong_guan_hua_fu")
    print("  - _cai_ju_he_fu_shen")
    print("  - _cai_xiong_lian_gui_ke")
    print("  - _cai_dong_shen_xing")
    print("  - _qiushi_jing_he_fu_yao")


if __name__ == "__main__":
    main()
