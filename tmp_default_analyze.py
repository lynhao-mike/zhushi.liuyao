from tests.fixtures.zengshan_230_cases import CASE_03, CASE_04, CASE_05, CASE_14, CASE_15, CASE_20
from tests.test_zengshan_cases import _build_hexagram
from liuyao.application.use_cases.analysis import run_analysis

for c in [CASE_03, CASE_04, CASE_05, CASE_14, CASE_15, CASE_20]:
    try:
        h = _build_hexagram(c)
        r = run_analysis(h, question_type=c.get('question_type', 'other'))
        print(c['id'], r.yong_shen_liu_qin, r.jixiong_result)
    except Exception as exc:
        print(c['id'], type(exc).__name__, exc)
