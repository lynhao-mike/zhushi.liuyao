from liuyao.domain.hexagram import Hexagram

cases = [
    ('例3', [8, 7, 7, 7, 9, 6], '巳', '未', '乙'),
    ('例4', [7, 8, 6, 8, 8, 8], '卯', '卯', '己'),
    ('例5', [6, 8, 6, 7, 7, 6], '卯', '辰', '戊'),
    ('例14', [7, 7, 8, 9, 7, 7], '未', '午', '甲'),
    ('例15', [7, 6, 7, 7, 7, 7], '申', '午', '戊'),
    ('例20', [8, 7, 9, 8, 7, 7], '未', '辰', '戊'),
]

for cid, yao, month, day, day_gan in cases:
    print('\n', cid)
    try:
        h = Hexagram.from_ganzhi(yao, month_zhi=month, day_zhi=day, day_gan=day_gan)
        print(h.ben_gua_name, '->', h.bian_gua_name, h.xun_kong)
        for line in h.lines:
            flags = []
            if line.is_shi:
                flags.append('世')
            if line.is_ying:
                flags.append('应')
            if line.is_moving:
                flags.append('动')
            bian = f"->{line.bian_di_zhi} {line.bian_liu_qin}" if line.bian_di_zhi else ''
            print(line.position, line.di_zhi, line.liu_qin, ''.join(flags), bian)
    except Exception as exc:
        print(type(exc).__name__, exc)
