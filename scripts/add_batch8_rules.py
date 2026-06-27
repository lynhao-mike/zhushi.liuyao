# -*- coding: utf-8 -*-
"""第8批: 追加8个builder函数"""

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

batch8_builders = r'''

def _liu_xu_shi_wang_cai_xing(judgement: dict[str, Any]) -> dict[str, Any]:
    """六畜: 或赌或斗皆宜世旺财兴 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_liu_xu_shi_wang_cai_xing",
        priority=78,
        conditions={
            "op": "AND",
            "children": [
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
        pattern="经典候选: 六畜世旺财兴",
        explanation="《黄金策》云: 或赌或斗,皆宜世旺财兴。世爻旺相,博弈竞争易胜,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "liu_xu_shi_wang_cai_xing"}, {"type": "score_delta", "value": 1}],
    )


def _cai_dong_xiu_wang_xuan(judgement: dict[str, Any]) -> dict[str, Any]:
    """求名: 财若交重休望青钱中选 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_dong_xiu_wang_xuan",
        priority=79,
        conditions={
            "op": "AND",
            "children": [
                {"fact_type": "question.type", "relation": "eq", "value": "kaoshi"},
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 考试财动休望中选",
        explanation="《黄金策》云: 财若交重,休望青钱中选。考试占财爻发动,不利功名,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_dong_xiu_wang_xuan"}, {"type": "score_delta", "value": -1}],
    )


def _cai_zuo_xiu_xiu_hua_di(judgement: dict[str, Any]) -> dict[str, Any]:
    """求馆: 财作束修不宜化弟 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_cai_zuo_xiu_xiu_hua_di",
        priority=80,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                _line_liu_qin("shi", "妻财"),
                {"fact_type": "line.bian.liu_qin", "subject": "shi", "relation": "eq", "value": "兄弟"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 束修财化兄弟不利",
        explanation="《黄金策》云: 财作束修,不宜化弟。财爻化兄弟,束修受损,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "cai_zuo_xiu_xiu_hua_di"}, {"type": "score_delta", "value": -1}],
    )


def _chuxing_jian_ju_kong(judgement: dict[str, Any]) -> dict[str, Any]:
    """出行: 两间齐空独行则吉 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_jian_ju_kong",
        priority=81,
        conditions={
            "op": "AND",
            "children": [
                {"fact_type": "question.type", "relation": "eq", "value": "chuxing"},
                _line_exists("shi"),
                {"fact_type": "line.is_empty", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 出行间爻皆空独行吉",
        explanation="《黄金策》云: 两间齐空,独行则吉。出行占间爻空亡,独行无碍,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "chuxing_jian_ju_kong"}, {"type": "score_delta", "value": 1}],
    )


def _yong_wang_er_fei(judgement: dict[str, Any]) -> dict[str, Any]:
    """身命: 用旺儿肥终易养主衰儿弱必难为 -> 吉(用旺)"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_yong_wang_er_fei",
        priority=82,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("primary_yong"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "旺"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "相"},
                    ],
                },
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 用旺儿肥终易养",
        explanation="《黄金策》云: 用旺儿肥终易养。用神旺相,所问之事根基扎实,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "yong_wang_er_fei"}, {"type": "score_delta", "value": 1}],
    )


def _chuxing_yong_shang_ru_mu(judgement: dict[str, Any]) -> dict[str, Any]:
    """行人: 远行最怕用爻伤尤嫌入墓 -> 凶"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_chuxing_yong_shang_ru_mu",
        priority=83,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("primary_yong"),
                {
                    "op": "OR",
                    "children": [
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "衰"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "休"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "囚"},
                        {"fact_type": "line.wangshuai.overall", "subject": "primary_yong", "relation": "eq", "value": "死"},
                    ],
                },
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 远行用爻伤及入墓",
        explanation="《黄金策》云: 远行最怕用爻伤,尤嫌入墓。用神休囚死绝,出行不利,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "chuxing_yong_shang_ru_mu"}, {"type": "score_delta", "value": -1}],
    )


def _sui_jun_yi_jing(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 最恶者岁君宜静而不宜动 -> 凶(动)"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_sui_jun_yi_jing",
        priority=84,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.is_moving", "subject": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="凶",
        pattern="经典候选: 岁君宜静不宜动",
        explanation="《黄金策》云: 最恶者岁君,宜静而不宜动。世爻发动,宜静反动,可作凶象候选证据。",
        effects=[{"type": "sign", "value": "sui_jun_yi_jing"}, {"type": "score_delta", "value": -1}],
    )


def _jue_feng_sheng(judgement: dict[str, Any]) -> dict[str, Any]:
    """总断千金赋: 绝逢生而事成 -> 吉"""
    return _base_rule(
        judgement,
        rule_id="classic_huangjince_dynamic_jue_feng_sheng",
        priority=85,
        conditions={
            "op": "AND",
            "children": [
                _line_exists("shi"),
                {"fact_type": "line.wangshuai.overall", "subject": "shi", "relation": "eq", "value": "衰"},
                {"fact_type": "relationship.sheng", "subject": "shi", "object": "shi", "relation": "is_true"},
            ],
        },
        ji_xiong="吉",
        pattern="经典候选: 绝处逢生事成",
        explanation="《黄金策》云: 绝逢生而事成。世爻衰绝而得生助,绝处逢生,可作吉象候选证据。",
        effects=[{"type": "sign", "value": "jue_feng_sheng"}, {"type": "score_delta", "value": 1}],
    )
'''

marker = "AUTO_COMPILE_TEMPLATES: dict[str, RuleBuilder] = {"
insert_pos = content.find(marker)
if insert_pos > 0:
    content = content[:insert_pos] + batch8_builders + '\n\n' + content[insert_pos:]

old_end = '''    "classic_huangjince_903555b3f3bb": _cisong_shi_wang_ying_shuai,
}'''

new_end = '''    "classic_huangjince_903555b3f3bb": _cisong_shi_wang_ying_shuai,
    # 第八批: 8个新增模板
    "classic_huangjince_ba4986179311": _liu_xu_shi_wang_cai_xing,
    "classic_huangjince_9537ac3bd02e": _cai_dong_xiu_wang_xuan,
    "classic_huangjince_68d70eea00a7": _cai_zuo_xiu_xiu_hua_di,
    "classic_huangjince_9acc5ae8c313": _chuxing_jian_ju_kong,
    "classic_huangjince_2722b52d14be": _yong_wang_er_fei,
    "classic_huangjince_4aa2e9b05ff6": _chuxing_yong_shang_ru_mu,
    "classic_huangjince_ce908ed3a7a7": _sui_jun_yi_jing,
    "classic_huangjince_3705ea743805": _jue_feng_sheng,
}'''

if old_end in content:
    content = content.replace(old_end, new_end)

with open('scripts/auto_compile_huangjince_candidate_rules.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Batch 8 builders added")
