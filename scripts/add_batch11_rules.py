# -*- coding: utf-8 -*-
"""
Batch 11: 添加第11批《黄金策》候选规则 builder 到自动编译脚本
涵盖: 婚姻、六畜、失物、求财、种作、求名考试
"""
from pathlib import Path

# 6个新的 builder 函数
NEW_BUILDERS = '''
def _hun_yong_sheng_he_shi(judgement: dict[str, Any]) -> dict[str, Any]:
    """婚姻: 用爻生合世爻,必得其力 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_hun_yong_sheng_he_shi",
        priority=93,
        conditions={
            "op": "AND",
            "children": [
                _question_type("hun_male"),
                _line_exists("primary_yong"),
                _line_exists("shi"),
                {
                    "op": "OR",
                    "children": [
                        _relationship("sheng", "primary_yong", "shi"),
                        _relationship("he", "primary_yong", "shi"),
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 婚姻用神生合世爻",
        explanation="《黄金策》云: 用爻生合世爻,必得其力。婚姻占中主用神生世或合世,对方/事体能助益自身,可作吉象候选证据。未编译克冲身象一侧,避免混合分句扩大判断。",
        effects=[{"type": "sign", "value": "hun_yong_sheng_he_shi"}, {"type": "score_delta", "value": 1}],
    )


def _liuxu_cai_kong_fu_dong(judgement: dict[str, Any]) -> dict[str, Any]:
    """六畜: 财空福动,纵迟钝而可观 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_liuxu_cai_kong_fu_dong",
        priority=94,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("cai"),
                {"fact_type": "line.is_empty", "subject": "cai", "relation": "is_true"},
                _line_exists("zi"),
                {"fact_type": "line.is_moving", "subject": "zi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 六畜财空福动",
        explanation="《黄金策》云: 财空福动,纵迟钝而可观。六畜占中财爻空亡而福德子孙发动,虽起势迟缓仍有可观之象,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "liuxu_cai_kong_fu_dong"}, {"type": "score_delta", "value": 1}],
    )


def _shiwu_cai_dong_bu_yi(judgement: dict[str, Any]) -> dict[str, Any]:
    """失物: 失舟车衣服,不宜妻位交重 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_shiwu_cai_dong_bu_yi",
        priority=95,
        conditions={
            "op": "AND",
            "children": [
                _question_type("shiwu"),
                _line_exists("cai"),
                {"fact_type": "line.is_moving", "subject": "cai", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 失物财爻发动不宜",
        explanation="《黄金策》云: 倘失舟车衣服,不宜妻位交重。失物占中财爻发动,物象不安、转移难寻,可作凶象候选证据。仅编译舟车衣服失物分句,不扩展至亡走兽飞禽。",
        effects=[{"type": "sign", "value": "shiwu_cai_dong_bu_yi"}, {"type": "score_delta", "value": -1}],
    )


def _cai_cai_an_gui_jing(judgement: dict[str, Any]) -> dict[str, Any]:
    """求财: 停榻者,喜财安而鬼静 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_cai_an_gui_jing",
        priority=96,
        conditions={
            "op": "AND",
            "children": [
                _question_type("cai"),
                _line_exists("cai"),
                {"fact_type": "line.is_moving", "subject": "cai", "relation": "is_false"},
                _line_exists("gui"),
                {"fact_type": "line.is_moving", "subject": "gui", "relation": "is_false"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求财财安鬼静",
        explanation="《黄金策》云: 停榻者,喜财安而鬼静。求财停榻经营之占中财爻安静且官鬼不动,财事安稳少扰,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "cai_cai_an_gui_jing"}, {"type": "score_delta", "value": 1}],
    )


def _zhongzuo_fu_de_kong_wang(judgement: dict[str, Any]) -> dict[str, Any]:
    """种作: 空亡福德,损耗难凭 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_zhongzuo_fu_de_kong_wang",
        priority=97,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("zi"),
                {"fact_type": "line.is_empty", "subject": "zi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 种作福德空亡",
        explanation="《黄金策》云: 空亡福德,损耗难凭。种作占中福德子孙空亡,收成护持不足、损耗难免,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "zhongzuo_fu_de_kong_wang"}, {"type": "score_delta", "value": -1}],
    )


def _kaoshi_shen_xing_bian_gui(judgement: dict[str, Any]) -> dict[str, Any]:
    """求名考试: 身兴变鬼,来试方成 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_kaoshi_shen_xing_bian_gui",
        priority=98,
        conditions={
            "op": "AND",
            "children": [
                _question_type("kaoshi"),
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "in", "value": ["旺", "相"]},
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "官鬼"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 求名身兴变鬼",
        explanation="《黄金策》云: 身兴变鬼,来试方成。求名考试占中世爻旺相并化官鬼,自身状态足以承接名位考试之象,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "kaoshi_shen_xing_bian_gui"}, {"type": "score_delta", "value": 1}],
    )
'''

# 6个新的模板条目
NEW_ENTRIES = '''
    # 第十一批: 6个新增模板
    "classic_huangjince_89b7ac9834eb": _hun_yong_sheng_he_shi,
    "classic_huangjince_44bcba94b554": _liuxu_cai_kong_fu_dong,
    "classic_huangjince_11bfc1cee9b4": _shiwu_cai_dong_bu_yi,
    "classic_huangjince_42f7ef7b3b21": _cai_cai_an_gui_jing,
    "classic_huangjince_f35e5ee390b4": _zhongzuo_fu_de_kong_wang,
    "classic_huangjince_9779698aa51c": _kaoshi_shen_xing_bian_gui,
'''

BUILDER_MARKER = "def _hun_yong_sheng_he_shi("
ENTRY_ANCHOR = '    "classic_huangjince_525c267fac83": _qiushi_jing_he_fu_yao,'
TEMPLATES_ANCHOR = "\n\n\nAUTO_COMPILE_TEMPLATES:"


def main() -> None:
    script_path = Path(__file__).parent / "auto_compile_huangjince_candidate_rules.py"
    content = script_path.read_text(encoding="utf-8")

    if BUILDER_MARKER in content:
        print("[SKIP] Batch 11 builders already exist")
        return
    if ENTRY_ANCHOR not in content:
        raise ValueError("Cannot find Batch 10 template anchor")
    if TEMPLATES_ANCHOR not in content:
        raise ValueError("Cannot find AUTO_COMPILE_TEMPLATES insertion anchor")

    content = content.replace(TEMPLATES_ANCHOR, "\n" + NEW_BUILDERS + TEMPLATES_ANCHOR, 1)
    content = content.replace(ENTRY_ANCHOR, ENTRY_ANCHOR + "\n" + NEW_ENTRIES, 1)

    script_path.write_text(content, encoding="utf-8")
    print(f"[OK] Added 6 Batch 11 builder functions to {script_path}")
    print("  - _hun_yong_sheng_he_shi")
    print("  - _liuxu_cai_kong_fu_dong")
    print("  - _shiwu_cai_dong_bu_yi")
    print("  - _cai_cai_an_gui_jing")
    print("  - _zhongzuo_fu_de_kong_wang")
    print("  - _kaoshi_shen_xing_bian_gui")


if __name__ == "__main__":
    main()
