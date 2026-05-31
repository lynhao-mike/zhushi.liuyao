# -*- coding: utf-8 -*-
from tests.test_zengshan_cases import ZENGSHAN_CASES, _build_hexagram, KNOWN_MISMATCH
from liuyao.analyzer import run_analysis

for c in ZENGSHAN_CASES:
    if c["id"] not in KNOWN_MISMATCH:
        continue
    try:
        h = _build_hexagram(c)
        r = run_analysis(h, c.get("question_type", "other"))
        got = r.jixiong_result.get("ji_xiong")
        print(f"{c['id']} exp={c['expected_ji_xiong']} got={got} pattern={r.jixiong_result.get('pattern')} q={c.get('question_type')} yong={r.yong_shen_liu_qin}")
        print("  theory=", " | ".join(c.get("theory_points", [])))
        print("  keywords=", c.get("expected_pattern_keywords", []))
        print("  ys=", [(l.position, l.liu_qin, l.di_zhi, l.is_moving, l.bian_liu_qin, l.bian_di_zhi) for l in r.yong_shen_lines])
        print("  shi=", (r.shi_line.position, r.shi_line.liu_qin, r.shi_line.di_zhi, r.shi_line.is_moving, r.shi_line.bian_liu_qin, r.shi_line.bian_di_zhi) if r.shi_line else None)
        print("  db=", r.dongbian_results)
        print("  san_he=", r.dongbian_results.get("san_he_ju"))
        print("  san_ban=", r.patterns_results.get("san_ban"))
        print("  kuayi=", r.patterns_results.get("kuayi_patterns"))
        print()
    except Exception as e:
        print(f"{c['id']} ERR {e}")
        print("  theory=", " | ".join(c.get("theory_points", [])))
        print()
