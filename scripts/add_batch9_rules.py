# -*- coding: utf-8 -*-
"""第9批：向 auto_compile_huangjince_candidate_rules.py 追加 6 个 builder 函数与模板条目。

从编译队列中选择的 6 条（覆盖求馆/天时/求财/行人/通用父母持世/六畜财空）：
  - queue line 78 (求馆): "动象临财,难称意"  → _qiuguan_cai_dong
  - queue line 96 (天时): "应乃太虚,逢空而雨晴难拟" → _tianshi_ying_empty
  - queue line 47 (求财): "财来就我,终须易" → _cai_lai_jiu_wo
  - queue line 130 (行人): "近出何妨主象伏,偏利逢冲" → _xingren_feng_chong
  - queue line 119 (蚕桑/通用): "父母持世,心劳而蚕必难为" → _fumu_chi_shi
  - queue line 60 (六畜/通用): "财若空亡,虽利暂时无远力" → _cai_kong_shi

执行方式：
    python scripts/add_batch9_rules.py
"""

import ast
from pathlib import Path

AUTO_COMPILE_PATH = Path("scripts/auto_compile_huangjince_candidate_rules.py")

# ── 6 个新 builder 函数 ────────────────────────────────────────────────

NEW_BUILDERS = r'''
def _qiuguan_cai_dong(judgement: dict[str, Any]) -> dict[str, Any]:
    """求馆: 动象临财,难称意 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_qiuguan_cai_dong",
        priority=86,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
                _line_liu_qin("shi", "妻财"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 求馆动象临财",
        explanation="《黄金策》云: 动象临财,难称意。求馆占中世爻发动且临妻财,财动妨馆事难成,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "qiuguan_cai_dong"}, {"type": "score_delta", "value": -1}],
    )


def _tianshi_ying_empty(judgement: dict[str, Any]) -> dict[str, Any]:
    """天时: 应乃太虚,逢空而雨晴难拟 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_tianshi_ying_empty",
        priority=87,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("ying"),
                {"fact_type": "line.is_empty", "subject": "ying", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 天时应空难定",
        explanation="《黄金策》云: 应乃太虚,逢空而雨晴难拟。天时占中应爻空亡,气象无定晴雨难测,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "tianshi_ying_empty"}, {"type": "score_delta", "value": -1}],
    )


def _cai_lai_jiu_wo(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 财来就我,终须易 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_lai_jiu_wo",
        priority=88,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财来就我",
        explanation="《黄金策》云: 财来就我,终须易。求财占中世爻临妻财,财来寻我而非我去寻财,求财易得,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_lai_jiu_wo"}, {"type": "score_delta", "value": 1}],
    )


def _xingren_feng_chong(judgement: dict[str, Any]) -> dict[str, Any]:
    """行人: 近出何妨主象伏,偏利逢冲 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_xingren_feng_chong",
        priority=89,
        conditions={
            "op": "AND",
            "children": [
                _question_type("chuxing"),
                _line_exists("primary_yong"),
                _line_exists("shi"),
                {"fact_type": "relationship.chong", "subject": "primary_yong", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 行人主象逢冲",
        explanation="《黄金策》云: 近出何妨主象伏,偏利逢冲。行人占中用神与世爻相冲,冲则动行人可归,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "xingren_feng_chong"}, {"type": "score_delta", "value": 1}],
    )


def _fumu_chi_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """通用: 父母持世,心劳而蚕必难为 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_fumu_chi_shi",
        priority=90,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "父母"),
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 父母持世辛劳",
        explanation="《黄金策》云: 父母持世,心劳而蚕必难为。父母持世主辛劳费心,所求之事多波折劳苦,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "fumu_chi_shi"}, {"type": "score_delta", "value": -1}],
    )


def _cai_kong_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """通用: 财若空亡,虽利暂时无远力 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_kong_shi",
        priority=91,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 财爻空亡利暂",
        explanation="《黄金策》云: 财若空亡,虽利暂时无远力。世爻临妻财而空亡,虽有短期小利却无长远之力,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_kong_shi"}, {"type": "score_delta", "value": -1}],
    )
'''

# ── 6 个新模板条目（使用真实的 classic_judgement_id 作为 key） ────

NEW_ENTRIES = r'''    # 第九批: 6个新增模板
    "classic_huangjince_c0500123b276": _qiuguan_cai_dong,
    "classic_huangjince_1b5bd6fa713e": _tianshi_ying_empty,
    "classic_huangjince_e3a016ab43d1": _cai_lai_jiu_wo,
    "classic_huangjince_95b746989412": _xingren_feng_chong,
    "classic_huangjince_0bbb18b44908": _fumu_chi_shi,
    "classic_huangjince_992af61aee72": _cai_kong_shi,
'''

# ── AUTO_COMPILED_RULE_IDS 更新 ────────────────────────────────────────

NEW_RULE_IDS = [
    "classic_huangjince_dynamic_qiuguan_cai_dong",
    "classic_huangjince_dynamic_tianshi_ying_empty",
    "classic_huangjince_dynamic_cai_lai_jiu_wo",
    "classic_huangjince_dynamic_xingren_feng_chong",
    "classic_huangjince_dynamic_fumu_chi_shi",
    "classic_huangjince_dynamic_cai_kong_shi",
]


def main() -> int:
    source = AUTO_COMPILE_PATH.read_text("utf-8")

    # ── 插入 builder 函数 ──
    # 在 _jue_feng_sheng 的 return 语句之后、AUTO_COMPILE_TEMPLATES 之前插入
    insert_pos = source.find("AUTO_COMPILE_TEMPLATES:")
    if insert_pos == -1:
        print("ERROR: cannot find AUTO_COMPILE_TEMPLATES")
        return 1

    before_templates = source[:insert_pos].rstrip("\n")
    after_templates = source[insert_pos:]
    source = before_templates + "\n\n" + NEW_BUILDERS + "\n\n" + after_templates

    # ── 插入模板条目 ──
    # 在最后一个模板条目的 } 之前插入
    closing_brace = source.rfind("\n}")
    if closing_brace == -1:
        print("ERROR: cannot find closing brace of AUTO_COMPILE_TEMPLATES")
        return 1

    # 在 "}" 之前插入新条目
    before_brace = source[:closing_brace]
    after_brace = source[closing_brace:]
    source = before_brace + "\n" + NEW_ENTRIES + after_brace

    # ── 验证语法 ──
    try:
        ast.parse(source)
    except SyntaxError as e:
        print(f"SYNTAX ERROR after insert: {e}")
        print("Check for encoding issues (Chinese quotes in Python strings)")
        return 1

    # ── 写出 ──
    AUTO_COMPILE_PATH.write_text(source, "utf-8")
    print(f"Wrote {AUTO_COMPILE_PATH}")
    print(f"New builders: _qiuguan_cai_dong, _tianshi_ying_empty, _cai_lai_jiu_wo, _xingren_feng_chong, _fumu_chi_shi, _cai_kong_shi")

    # ── 打印测试断言更新 ──
    print("\n" + "=" * 60)
    print("请在 tests/test_huangjince_auto_compile.py 中添加:")
    print(f"    assert len(generated) == {45 + 6}")
    print(f"    assert len(merged_once) == {48 + 6}")
    print("\n请在 AUTO_COMPILED_RULE_IDS 中添加:")
    for rid in NEW_RULE_IDS:
        print(f'    "{rid}",')
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
