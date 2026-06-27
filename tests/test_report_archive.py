"""Report archive utility tests."""

from liuyao.domain.hexagram import Hexagram
from liuyao.report_archive import HEXAGRAM_INPUT_LABELS, build_hexagram_input_snapshot



def test_build_hexagram_input_snapshot_keeps_archive_metadata_stable():
    yao_values = [9, 8, 7, 9, 6, 6]
    hexagram = Hexagram(yao_values, 2026, 5, 25, hour=14)

    snapshot = build_hexagram_input_snapshot(
        question="金首饰丢失能否找回",
        question_type="shiwu",
        is_dual=True,
        date="2026-05-25",
        hour=14,
        yao_values=yao_values,
        hexagram=hexagram,
    )

    assert snapshot["question"] == "金首饰丢失能否找回"
    assert snapshot["question_type"] == "shiwu"
    assert snapshot["is_dual"] is True
    assert snapshot["date"] == "2026-05-25"
    assert snapshot["hour"] == 14
    assert snapshot["yao_values"] == [9, 8, 7, 9, 6, 6]
    assert snapshot["yao_values"] is not yao_values
    assert snapshot["ben_gua_name"] == hexagram.ben_gua_name
    assert snapshot["bian_gua_name"] == hexagram.bian_gua_name
    assert snapshot["gan_zhi"] == hexagram.gan_zhi
    assert snapshot["xun_kong"] == list(hexagram.xun_kong)
    assert len(snapshot["lines"]) == 6
    assert snapshot["lines"][0]["position"] == 1
    assert "is_moving" in snapshot["lines"][0]
    assert "is_xun_kong" in snapshot["lines"][0]



def test_hexagram_input_labels_keep_human_facing_archive_headings_stable():
    assert HEXAGRAM_INPUT_LABELS["question"] == "占问事项"
    assert HEXAGRAM_INPUT_LABELS["date"] == "起卦日期"
    assert HEXAGRAM_INPUT_LABELS["ben_gua_name"] == "本卦"
    assert HEXAGRAM_INPUT_LABELS["lines"] == "六爻明细"
