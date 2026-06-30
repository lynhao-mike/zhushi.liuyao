"""《黄金策》候选规则自动保守编译测试。"""

from __future__ import annotations

import json
from pathlib import Path

from liuyao.domain.rules.classic_rule_schema import validate_classic_rules
from scripts.auto_compile_huangjince_candidate_rules import (
    build_auto_compiled_rules,
    merge_candidate_rules,
)

ROOT = Path(__file__).resolve().parents[1]
CLASSIC_JUDGEMENTS_PATH = ROOT / "data" / "classic_judgements.jsonl"
CANDIDATE_RULES_PATH = ROOT / "data" / "huangjince_candidate_rules.jsonl"

AUTO_COMPILED_RULE_IDS = {
    "classic_huangjince_dynamic_primary_yong_moving_decline",
    "classic_huangjince_dynamic_shi_ying_empty_he",
    "classic_huangjince_dynamic_chuxing_ying_ke_shi",
    "classic_huangjince_dynamic_chuxing_ying_empty",
    "classic_huangjince_dynamic_hun_shi_ying_relationships",
    "classic_huangjince_dynamic_hun_shi_ying_he",
    "classic_huangjince_dynamic_hun_ying_moving_or_empty",
    "classic_huangjince_dynamic_hun_shi_ying_both_empty",
    "classic_huangjince_dynamic_bing_shi_ghost",
    "classic_huangjince_dynamic_chuxing_shi_empty",
    "classic_huangjince_dynamic_bing_shi_fumu",
    "classic_huangjince_dynamic_hun_shi_wang",
    "classic_huangjince_dynamic_kaoshi_shi_empty",
    "classic_huangjince_dynamic_chuxing_shi_ying_both_empty",
    # 第四批
    "classic_huangjince_dynamic_kaoshi_shi_wang",
    "classic_huangjince_dynamic_cisong_shi_ying_sheng_he",
    "classic_huangjince_dynamic_shiwu_chuxing_yong_sheng_shi",
    # 第五批
    "classic_huangjince_dynamic_bing_ghost_moving",
    "classic_huangjince_dynamic_guan_ke_shi",
    "classic_huangjince_dynamic_shi_empty",
    "classic_huangjince_dynamic_cai_ghost_moving_sheng_shi",
    "classic_huangjince_dynamic_shiwu_shi_wang",
    "classic_huangjince_dynamic_ying_ke_shi",
    # 第六批
    "classic_huangjince_dynamic_fu_gui_ju_kong",
    "classic_huangjince_dynamic_hun_cai_gui_kong",
    "classic_huangjince_dynamic_cai_hua_zi_sun",
    "classic_huangjince_dynamic_cai_fu_chi_shi",
    "classic_huangjince_dynamic_fu_hua_ji_yao",
    "classic_huangjince_dynamic_hun_shi_ying_hua_kong",
    # 第七批
    "classic_huangjince_dynamic_dong_bian_jiao_zheng",
    "classic_huangjince_dynamic_zi_kong_hua_kong",
    "classic_huangjince_dynamic_he_zhu_chong_po",
    "classic_huangjince_dynamic_xiu_qiu_sheng_wang",
    "classic_huangjince_dynamic_hun_liu_he",
    "classic_huangjince_dynamic_hun_liu_chong",
    "classic_huangjince_dynamic_hun_ri_he_bi_he",
    "classic_huangjince_dynamic_cisong_shi_wang_ying_shuai",
    # 第八批
    "classic_huangjince_dynamic_liu_xu_shi_wang_cai_xing",
    "classic_huangjince_dynamic_cai_dong_xiu_wang_xuan",
    "classic_huangjince_dynamic_cai_zuo_xiu_xiu_hua_di",
    "classic_huangjince_dynamic_chuxing_jian_ju_kong",
    "classic_huangjince_dynamic_yong_wang_er_fei",
    "classic_huangjince_dynamic_chuxing_yong_shang_ru_mu",
    "classic_huangjince_dynamic_sui_jun_yi_jing",
    "classic_huangjince_dynamic_jue_feng_sheng",
    # 第九批
    "classic_huangjince_dynamic_qiuguan_cai_dong",
    "classic_huangjince_dynamic_tianshi_ying_empty",
    "classic_huangjince_dynamic_cai_lai_jiu_wo",
    "classic_huangjince_dynamic_xingren_feng_chong",
    "classic_huangjince_dynamic_fumu_chi_shi",
    "classic_huangjince_dynamic_cai_kong_shi",
    # 第十批
    "classic_huangjince_dynamic_hun_gui_ke_fei_yao",
    "classic_huangjince_dynamic_cisong_fu_dong_guan_hua_fu",
    "classic_huangjince_dynamic_cai_ju_he_fu_shen",
    "classic_huangjince_dynamic_cai_xiong_lian_gui_ke",
    "classic_huangjince_dynamic_cai_dong_shen_xing",
    "classic_huangjince_dynamic_qiushi_jing_he_fu_yao",
    # 第十一批
    "classic_huangjince_dynamic_hun_yong_sheng_he_shi",
    "classic_huangjince_dynamic_liuxu_cai_kong_fu_dong",
    "classic_huangjince_dynamic_shiwu_cai_dong_bu_yi",
    "classic_huangjince_dynamic_cai_cai_an_gui_jing",
    "classic_huangjince_dynamic_zhongzuo_fu_de_kong_wang",
    "classic_huangjince_dynamic_kaoshi_shen_xing_bian_gui",
}


def _jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def test_auto_compile_builds_known_conservative_templates():
    judgements = _jsonl(CLASSIC_JUDGEMENTS_PATH)

    generated = build_auto_compiled_rules(judgements)

    assert len(generated) == 63
    assert {rule["id"] for rule in generated} == AUTO_COMPILED_RULE_IDS
    assert validate_classic_rules(generated) == []
    assert all(rule["execution_tier"] == "candidate_only" for rule in generated)
    assert all(rule["safety"]["allow_override"] is False for rule in generated)
    assert all(rule["safety"]["p0_safe"] is True for rule in generated)
    assert all("仅编译现有事实抽取器可表达的部分" in rule["safety"]["notes"] for rule in generated)


def test_auto_compile_merge_is_deterministic_and_idempotent():
    judgements = _jsonl(CLASSIC_JUDGEMENTS_PATH)
    candidate_rules = _jsonl(CANDIDATE_RULES_PATH)
    generated = build_auto_compiled_rules(judgements)

    merged_once = merge_candidate_rules(candidate_rules, generated)
    merged_twice = merge_candidate_rules(merged_once, generated)

    assert merged_once == merged_twice
    assert len(merged_once) == 66
    assert validate_classic_rules(merged_once) == []
    assert {rule["id"] for rule in generated}.issubset({rule["id"] for rule in merged_once})
    assert [rule["id"] for rule in merged_once[:3]] == [rule["id"] for rule in candidate_rules[:3]]
