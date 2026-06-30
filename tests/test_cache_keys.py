"""缓存键确定性与隔离性回归测试。"""

from api.infrastructure.cache.redis_client import CacheKey, build_fingerprint, build_ganzhi_key


def test_analysis_fingerprint_preserves_yao_order():
    """六爻顺序决定本卦/变卦，不能把相同元素的不同排列打成同一缓存。"""
    ganzhi_key = build_ganzhi_key(2026, 6, 27, 12, None)

    first = build_fingerprint([6, 7, 8, 9, 7, 8], ganzhi_key, "cai", False)
    second = build_fingerprint([8, 7, 6, 9, 7, 8], ganzhi_key, "cai", False)

    assert first != second


def test_analysis_fingerprint_uses_structured_context_without_separator_collision():
    """上下文字段即使含分隔符，也不能因字符串拼接产生同一指纹。"""
    first = build_fingerprint(
        [6, 7, 8, 9, 7, 8],
        {"ganzhi": "2026-6-27-12", "question": "a|b", "querent_name": "c"},
        "cai",
        False,
    )
    second = build_fingerprint(
        [6, 7, 8, 9, 7, 8],
        {"ganzhi": "2026-6-27-12|a", "question": "b", "querent_name": "c"},
        "cai",
        False,
    )

    assert first != second


def test_listing_cache_key_includes_ji_xiong_filter():
    """同一问事类型分页下，吉凶筛选不同必须命中不同列表缓存。"""
    ji_key = CacheKey.listing("all", 1, 20, "吉")
    xiong_key = CacheKey.listing("all", 1, 20, "凶")
    unfiltered_key = CacheKey.listing("all", 1, 20)

    assert ji_key != xiong_key
    assert ji_key != unfiltered_key
    assert xiong_key != unfiltered_key
