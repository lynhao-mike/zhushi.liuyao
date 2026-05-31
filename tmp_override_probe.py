from tests.fixtures.zengshan_230_cases import ZENGSHAN_CASES
from tests.test_zengshan_cases import _build_hexagram
from liuyao.application.use_cases.analysis import run_analysis

for c in ZENGSHAN_CASES:
    try:
        h = _build_hexagram(c)
        r1 = run_analysis(h, question_type=c.get('question_type', 'other'))
        r2 = run_analysis(h, question_type=c.get('question_type', 'other'), yong_shen_override=c.get('yong_shen'))
    except Exception as e:
        print(c['id'], 'ERR', e)
        continue
    j1 = r1.jixiong_result.get('ji_xiong')
    j2 = r2.jixiong_result.get('ji_xiong')
    if j1 != j2 or r1.yong_shen_liu_qin != r2.yong_shen_liu_qin:
        print(c['id'], c.get('question_type'), c.get('yong_shen'), 'default', r1.yong_shen_liu_qin, j1, r1.jixiong_result.get('pattern'), 'override', r2.yong_shen_liu_qin, j2, r2.jixiong_result.get('pattern'), 'expected', c.get('expected_ji_xiong'))
