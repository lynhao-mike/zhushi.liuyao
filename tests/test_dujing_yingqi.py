"""独静卦应期最小回归测试。"""

from liuyao.domain.hexagram import Hexagram
from liuyao.domain.yingqi import estimate_yingqi_dujing


def test_dujing_five_moving_one_static():
    """五动一静，独静爻戌土，应期候选应包含逢值和逢冲。"""
    h = Hexagram.from_ganzhi(
        [9, 9, 9, 9, 9, 7],
        month_zhi="子", day_zhi="子", day_gan="甲",
    )
    candidates = estimate_yingqi_dujing(h, [])
    assert any("独静: 戌" in c for c in candidates)
    assert any("辰" in c for c in candidates)


def test_dujing_non_dujing_returns_empty():
    """非独静卦返回空列表。"""
    h = Hexagram.from_ganzhi(
        [9, 7, 7, 7, 7, 8],
        month_zhi="子", day_zhi="子", day_gan="甲",
    )
    assert estimate_yingqi_dujing(h, []) == []


def test_dujing_all_static_returns_empty():
    """全静卦返回空列表。"""
    h = Hexagram.from_ganzhi(
        [7, 7, 8, 8, 7, 8],
        month_zhi="子", day_zhi="子", day_gan="甲",
    )
    assert estimate_yingqi_dujing(h, []) == []
