from tests.fixtures.zengshan_230_cases import CASE_03, CASE_04, CASE_05, CASE_14, CASE_15, CASE_20
from tests.test_zengshan_cases import _build_hexagram
from liuyao.application.use_cases.analysis import run_analysis

for c in [CASE_03, CASE_04, CASE_05, CASE_14, CASE_15, CASE_20]:
    print('\n', c['id'])
    try:
        h = _build_hexagram(c)
        r = run_analysis(h, question_type=c.get('question_type', 'other'), yong_shen_override=c.get('yong_shen'))
        print(h.ben_gua_name, '->', h.bian_gua_name)
        print('yong', r.yong_shen_liu_qin, 'shi', [(l.position, l.di_zhi, l.liu_qin) for l in h.lines if l.is_shi])
        print(r.jixiong_result)
        print('dong', r.dongbian_results)
    except Exception as e:
        print(type(e).__name__, e)
