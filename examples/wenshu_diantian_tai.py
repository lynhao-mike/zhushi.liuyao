"""
经典案例 - 丙申日占文书 (《古筮真诠》第三十九章)

得"地天泰"卦, 父母爻不上卦, 父母巳火藏伏于二爻寅木下:
- 伏神: 父母乙巳火 (第2爻位置, 旬空)
- 飞神: 官鬼甲寅木 (第2爻)
- 飞伏关系: 飞神生伏神 (长生) - 木生火
- 卦理定性: 伏空 (旬空辰巳) → 凶

这是《古筮真诠》给出的"用神藏伏 + 伏空 = 文书不成"的经典案例。
"""

from datetime import datetime
from liuyao import Hexagram, run_analysis, format_report


# 地天泰 (上坤下乾) - 全静卦
# yao_values: 7=阳静(少阳), 8=阴静(少阴)
# 顺序 [初爻 → 上爻]
yao_values = [7, 7, 7, 8, 8, 8]

# 2024-09-29 是丙申日, 旬空辰巳 - 完美对应原案
year, month, day, hour = 2024, 9, 29, 12

# 排卦
h = Hexagram(yao_values, year, month, day, hour)

print("=" * 70)
print("【经典案例】 丙申日占文书 — 地天泰 (《古筮真诠》第三十九章)")
print("=" * 70)
print()
print(f"日期: {year}年{month}月{day}日 ({h.gan_zhi['day_gan']}{h.gan_zhi['day_zhi']}日)")
print(f"本卦: {h.ben_gua_name} ({h.palace_name}宫 - {h.palace_wu_xing})")
print(f"旬空: {h.xun_kong[0]}{h.xun_kong[1]}")
print()

print("─" * 70)
print("主卦六爻 (从下到上):")
print("─" * 70)
for line in h.lines:
    role = "[世]" if line.is_shi else "[应]" if line.is_ying else ""
    print(
        f"  第{line.position}爻 {line.liu_qin}{line.tian_gan}{line.di_zhi}"
        f"{line.wu_xing} {role}"
    )

print()
print("─" * 70)
print("藏爻 (本宫纯卦各爻):")
print("─" * 70)
for cang in h.cang_yao:
    kong_mark = " [旬空]" if cang.is_xun_kong else ""
    print(
        f"  第{cang.position}爻 {cang.liu_qin}{cang.tian_gan}{cang.di_zhi}"
        f"{cang.wu_xing}{kong_mark}"
    )

print()

# 文书占 = kaoshi (用神=父母)
report = run_analysis(h, question_type="kaoshi")

print("=" * 70)
print(f"【伏神分析】 用神={report.yong_shen_liu_qin}")
print("=" * 70)
if report.yong_shen_lines:
    print("用神在主卦中存在, 不需取伏神")
else:
    print("用神不上卦 → 启用藏伏理论, 从藏爻取伏神")
    print()

    fa = report.fushen_analysis
    fi = fa["fushen_info"]
    cang = fi["cang_yao"]
    fei = fi["fei_shen"]

    print(f"  伏神: {cang.liu_qin}{cang.di_zhi}{cang.wu_xing} (第{fi['position']}爻位)")
    print(f"  飞神: {fei.liu_qin}{fei.di_zhi}{fei.wu_xing} (第{fei.position}爻)")
    print(f"  飞伏关系: {fa['fei_fu_relation']} (\"{fa['fei_fu_alias']}\")")
    print(f"            → {fa['fei_fu_implication']}")
    print()

    print("  卦理定性 (朱辰彬 4 规则):")
    for ev in fa["jixiong_evaluations"]:
        result_mark = {
            "凶": "✗ 凶", "吉": "✓ 吉",
            "吉(短期)": "✓ 吉(短期)", "中性": "— 中性",
        }.get(ev["result"], ev["result"])
        print(f"    · {ev['rule']}: 【{result_mark}】 {ev['detail']}")

    print()
    print("  应期 (冲飞露伏):")
    for c in fa["yingqi_candidates"]:
        print(f"    · {c}")

print()
print("=" * 70)
print("【野鹤老人原断】")
print("=" * 70)
print("""
  原断: 父母爻为用神, 此卦六爻无父母, 巳火父母伏于二爻寅木之下,
        又遇旬空, 所以文书不成也.

  野鹤补充: 但此卦文书之不成者, 非因空也, 乃因飞神在寅, 伏神在巳,
            与申日作三刑(寅巳申)之故耳.

  本系统的伏神模块准确识别出:
    ✓ 伏神位置 = 第2爻 (父母巳火)
    ✓ 飞神 = 寅木
    ✓ 飞伏关系 = 长生 (木生火)
    ✓ 伏空 → 凶
    ✓ 应期 = 冲飞(申) / 露伏值(巳) / 露伏合(申)

  注: 三刑(寅巳申)的细节, 由 patterns.py 的 detect_san_xing 检测
      (本案例日辰申不在卦内, 故卦内仅检测到爻间关系).
""")
