from liuyao.domain.hexagram import Hexagram
from liuyao.application.use_cases.analysis import run_analysis

cases = [
    ("例3", [8, 7, 7, 7, 9, 6], "巳", "未", ["辰", "巳"], "fumu", "凶"),
    ("例4", [7, 8, 8, 6, 8, 8], "卯", "卯", ["申", "酉"], "xiongdi", "吉"),
    ("例5", [6, 8, 6, 7, 7, 6], "卯", "辰", ["戌", "亥"], "fumu", "凶"),
    ("例14", [7, 7, 8, 9, 7, 7], "未", "午", ["辰", "巳"], "zinv", "凶"),
    ("例15", [8, 6, 7, 7, 7, 7], "申", "午", ["子", "丑"], "bing", "凶"),
    ("例20", [8, 7, 9, 8, 7, 7], "未", "辰", ["戌", "亥"], "guan", "凶"),
    ("例108", [7, 8, 7, 8, 9, 7], "辰", "卯", ["子", "丑"], "cai", "凶"),
    ("例205", [7, 8, 7, 6, 8, 8], "未", "未", ["子", "丑"], "cai", "吉"),
]

for cid, yao, month, day, kong, qtype, expected in cases:
    h = Hexagram.from_ganzhi(yao, month_zhi=month, day_zhi=day, xun_kong=kong)
    report = run_analysis(h, question_type=qtype)
    print("\n", cid, h.ben_gua_name, "->", h.bian_gua_name, qtype, "expected", expected)
    for l in h.lines:
        print(l.position, l.di_zhi, l.liu_qin, "世" if l.is_shi else "应" if l.is_ying else "", "动" if l.is_moving else "", "->" + str(l.bian_di_zhi) + str(l.bian_liu_qin) if l.is_moving else "")
    print(report.jixiong_result)
