"""
动变模块专项测试 - Dedicated unit tests for liuyao/dongbian.py
"""

from types import SimpleNamespace

from liuyao.domain.dongbian import (
    analyze_compound_movement,
    analyze_dongbian,
    is_hua_jin_shen,
    is_hua_jue,
    is_hua_po,
    is_hua_tui_shen,
    is_hui_tou_ke,
    is_hui_tou_sheng,
)
from liuyao.domain.hexagram import Hexagram
from liuyao.domain.wangshuai import analyze_hexagram_wangshuai


class TestIsHuiTouSheng:
    """回头生: 变爻五行生本爻五行"""

    def test_positive_water_generates_wood(self):
        # 亥水生寅木
        assert is_hui_tou_sheng("寅", "亥") is True

    def test_positive_fire_generates_earth(self):
        # 午火生丑土
        assert is_hui_tou_sheng("丑", "午") is True

    def test_negative_wood_does_not_generate_metal(self):
        assert is_hui_tou_sheng("酉", "寅") is False

    def test_same_element_not_sheng(self):
        # 寅木 <- 卯木 (同五行不是生)
        assert is_hui_tou_sheng("寅", "卯") is False


class TestIsHuiTouKe:
    """回头克: 变爻五行克本爻五行"""

    def test_positive_metal_overcomes_wood(self):
        # 申金克寅木
        assert is_hui_tou_ke("寅", "申") is True

    def test_positive_fire_overcomes_metal(self):
        # 午火克酉金
        assert is_hui_tou_ke("酉", "午") is True

    def test_negative(self):
        assert is_hui_tou_ke("寅", "亥") is False


class TestIsHuaJinShen:
    """化进神: 同五行前进"""

    def test_yin_to_mao(self):
        assert is_hua_jin_shen("寅", "卯") is True

    def test_si_to_wu(self):
        assert is_hua_jin_shen("巳", "午") is True

    def test_shen_to_you(self):
        assert is_hua_jin_shen("申", "酉") is True

    def test_hai_to_zi(self):
        assert is_hua_jin_shen("亥", "子") is True

    def test_negative(self):
        assert is_hua_jin_shen("卯", "寅") is False


class TestIsHuaTuiShen:
    """化退神: 同五行后退"""

    def test_mao_to_yin(self):
        assert is_hua_tui_shen("卯", "寅") is True

    def test_wu_to_si(self):
        assert is_hua_tui_shen("午", "巳") is True

    def test_negative(self):
        assert is_hua_tui_shen("寅", "卯") is False


class TestIsHuaJue:
    """化绝: 本爻五行在变爻处于绝地"""

    def test_metal_jue_at_yin(self):
        # 酉金绝在寅
        assert is_hua_jue("酉", "寅") is True

    def test_water_jue_at_si(self):
        # 子水绝在巳
        assert is_hua_jue("子", "巳") is True

    def test_negative(self):
        assert is_hua_jue("寅", "亥") is False


class TestIsHuaPo:
    """化破: 本爻与变爻互冲"""

    def test_zi_wu(self):
        assert is_hua_po("子", "午") is True

    def test_yin_shen(self):
        assert is_hua_po("寅", "申") is True

    def test_negative(self):
        assert is_hua_po("子", "丑") is False


class TestAnalyzeDongbian:
    """完整动变分析"""

    def test_static_hexagram(self):
        h = Hexagram([7, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        assert result["moving_analyses"] == {}
        assert result["useful_moving"] == []
        assert result["useless_moving"] == []

    def test_moving_hexagram_has_analyses(self):
        h = Hexagram([9, 7, 7, 7, 7, 7], 2024, 3, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        assert 1 in result["moving_analyses"]

    def test_useful_useless_classification(self):
        # 9=老阳动, create a hexagram with moving lines
        h = Hexagram([9, 8, 7, 9, 7, 8], 2024, 6, 15)
        ws = analyze_hexagram_wangshuai(h)
        result = analyze_dongbian(h, ws)
        total = len(result["useful_moving"]) + len(result["useless_moving"])
        assert total == len(result["moving_analyses"])

    def test_compound_movement_chain_generates(self):
        h = SimpleNamespace(
            shi_line=SimpleNamespace(position=2, di_zhi="巳", wu_xing="火"),
            moving_lines=[
                SimpleNamespace(position=1, di_zhi="寅", wu_xing="木"),
                SimpleNamespace(position=2, di_zhi="巳", wu_xing="火"),
            ],
        )
        result = analyze_compound_movement(h, {}, [1, 2])
        assert result[0]["mode"] == "chain_sheng"
        assert result[0]["path"] == [1, 2]

    def test_compound_movement_chain_overcomes(self):
        h = SimpleNamespace(
            shi_line=SimpleNamespace(position=2, di_zhi="寅", wu_xing="木"),
            moving_lines=[
                SimpleNamespace(position=1, di_zhi="申", wu_xing="金"),
                SimpleNamespace(position=2, di_zhi="寅", wu_xing="木"),
            ],
        )
        result = analyze_compound_movement(h, {}, [1, 2])
        assert result[0]["mode"] == "chain_ke_cancel"
        assert result[0]["path"] == [1, 2]

    def test_compound_movement_leave_job_case_uses_only_original_moving_lines(self):
        h = SimpleNamespace(
            shi_line=SimpleNamespace(position=3, di_zhi="卯", wu_xing="木"),
            lines_by_position={3: SimpleNamespace(position=3, di_zhi="卯", wu_xing="木")},
            moving_lines=[
                SimpleNamespace(position=2, di_zhi="巳", wu_xing="火", bian_di_zhi="辰", bian_wu_xing="土"),
                SimpleNamespace(position=4, di_zhi="午", wu_xing="火", bian_di_zhi="戌", bian_wu_xing="土"),
                SimpleNamespace(position=5, di_zhi="申", wu_xing="金", bian_di_zhi="子", bian_wu_xing="水"),
            ],
        )
        result = analyze_compound_movement(h, {}, [2, 4, 5], question_type="other")
        paths = {(item["mode"], tuple(item["path"]), item["acts_on_target"]) for item in result}
        assert ("chain_ke_cancel", (2, 5, 3), "protect") in paths
        assert ("chain_ke_cancel", (4, 5, 3), "protect") in paths
        assert not any("变" in item["path"] for item in result)

    def test_compound_movement_san_he_has_priority(self):
        h = SimpleNamespace(moving_lines=[])
        result = analyze_compound_movement(
            h, {}, [], san_he_ju=[{"wu_xing": "水", "members": ["申", "子", "辰"]}]
        )
        assert result == [{
            "mode": "san_he",
            "final_target_kind": "unknown",
            "final_target_position": None,
            "path": [],
            "aggregated_to_position": None,
            "acts_on_target": "none",
            "valid": True,
            "reason": "三合局优先于单爻连动",
            "source_positions": [],
            "ju": {"wu_xing": "水", "members": ["申", "子", "辰"]},
        }]
