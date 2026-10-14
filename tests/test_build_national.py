# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path
import pandas as pd
import pytest

from src import build_national
from src.build_national import (
    TILE_LAYOUT,
    COLOR_CLASSES,
    short_name,
    color_class,
    landform_options,
    required_files,
    load_monument_list,
    build_national as run_build_national,
)
from src.prefectures import PREFECTURES

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_tile_layout():
    """1. TILE_LAYOUT：キーが PREFECTURES と同じ47、位置の重なりなし、行0〜10・列0〜13の範囲"""
    assert set(TILE_LAYOUT.keys()) == set(PREFECTURES.keys())
    assert len(TILE_LAYOUT) == 47

    # 位置の重なりなし
    positions = list(TILE_LAYOUT.values())
    assert len(positions) == len(set(positions))

    # 行0〜10、列0〜13
    for r, c in positions:
        assert 0 <= r <= 10
        assert 0 <= c <= 13


def test_short_name():
    """2. short_name：北海道・東京都・京都府・大阪府・神奈川県・鹿児島県"""
    assert short_name("北海道") == "北海道"
    assert short_name("東京都") == "東京"
    assert short_name("京都府") == "京都"
    assert short_name("大阪府") == "大阪"
    assert short_name("神奈川県") == "神奈川"
    assert short_name("鹿児島県") == "鹿児島"

    # 県コードでも動作することを確認
    assert short_name("01") == "北海道"
    assert short_name("13") == "東京"
    assert short_name("26") == "京都"
    assert short_name("27") == "大阪"
    assert short_name("14") == "神奈川"
    assert short_name("46") == "鹿児島"


def test_color_class():
    """3. color_class：0・1・9・10・19・20・49・50・99・100・163"""
    assert len(COLOR_CLASSES) == 6
    assert [c["label"] for c in COLOR_CLASSES] == ["0", "1〜9", "10〜19", "20〜49", "50〜99", "100以上"]
    assert color_class(0) == "0"
    assert color_class(1) == "1〜9"
    assert color_class(9) == "1〜9"
    assert color_class(10) == "10〜19"
    assert color_class(19) == "10〜19"
    assert color_class(20) == "20〜49"
    assert color_class(49) == "20〜49"
    assert color_class(50) == "50〜99"
    assert color_class(99) == "50〜99"
    assert color_class(100) == "100以上"
    assert color_class(163) == "100以上"


def test_landform_options():
    """4. landform_options：偽の表（同数の名前を含む）で、多い順・同数は名前順・最後が「データなし」"""
    # 地形A: 5件, 地形B: 3件, 地形C: 3件, データなし: 2件
    data = {
        'ID': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13'],
        '地形分類名': [
            '地形A', '地形A', '地形A', '地形A', '地形A',
            '地形C', '地形C', '地形C',
            '地形B', '地形B', '地形B',
            'データなし', 'データなし'
        ]
    }
    df = pd.DataFrame(data)
    options = landform_options(df)
    # 多い順: 地形A (5), 同数は名前順: 地形B (3) < 地形C (3), 最後: データなし
    assert options == ['地形A', '地形B', '地形C', 'データなし']


def test_missing_files(tmp_path, capsys):
    """5. 足りないファイルがあるとき：tmp_path で呼び、終了コード1・何も書かない"""
    out_dir = tmp_path / "output"
    site_dir = tmp_path / "docs"
    data_dir = tmp_path / "data"

    out_dir.mkdir()
    site_dir.mkdir()
    data_dir.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        run_build_national(output_dir=out_dir, site_dir=site_dir, data_dir=data_dir)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "エラー：ファイルが足りません：" in captured.out
    assert "先に実行してください：python src/summarize_national.py、python src/make_national_pdf.py と python src/build_site.py --pref all" in captured.out

    # docs 配下に何も生成されていないこと
    assert list(site_dir.rglob('*')) == []


def test_fake_data_generation(tmp_path, monkeypatch):
    """
    6. 偽のデータ（tmp_path に2県分）で作った index.html に：
    pref_XX.html へのリンク、埋め込み JSON を取り出して json.loads できること・行数、
    碑名に </script><b> を含めても </script> がそのまま出ないこと
    """
    out_dir = tmp_path / "output"
    site_dir = tmp_path / "docs"
    data_dir = tmp_path / "data"

    out_dir.mkdir()
    (out_dir / "fig").mkdir()
    site_dir.mkdir()
    data_dir.mkdir()

    # 2県分に差し替え
    fake_prefs = {"01": "北海道", "02": "青森県"}
    fake_tile = {"01": (0, 0), "02": (0, 1)}
    monkeypatch.setattr(build_national, "PREFECTURES", fake_prefs)
    monkeypatch.setattr(build_national, "TILE_LAYOUT", fake_tile)

    # 必要なファイルを準備
    # output CSVs
    sum_csv = (
        "範囲,災害種別,指標,碑_中央値,比較地点_中央値,差の中央値,碑の方が大きい割合\n"
        "全碑,全種別,標高_m,10.0,20.0,-10.0,0.3\n"
        "全碑,全種別,傾斜_度,5.0,10.0,-5.0,0.4\n"
        "全碑,全種別,河川までの距離_m,100.0,200.0,-100.0,0.3\n"
        "全碑,全種別,河川との高さの差_m,2.0,5.0,-3.0,0.2\n"
        "全碑,全種別,海岸までの距離_m,1000.0,1500.0,-500.0,0.4\n"
    )
    (out_dir / "summary_all.csv").write_text(sum_csv, encoding='utf-8-sig')

    haz_csv = (
        "範囲,災害種別,ハザード,碑_数,碑_区域内,比較地点_数,比較地点_区域内,碑_3m以上,比較地点_3m以上\n"
        "全碑,全種別,洪水（想定最大規模）,2,1,10,2,0,0\n"
        "全碑,全種別,津波,2,1,10,1,1,0\n"
        "全碑,全種別,高潮,2,0,10,0,0,0\n"
        "全碑,全種別,土砂災害,2,0,10,1,,\n"
    )
    (out_dir / "hazard_summary_all.csv").write_text(haz_csv, encoding='utf-8-sig')

    lf_csv = (
        "範囲,災害種別,地形分類名,碑_件数,碑_割合,比較地点_件数,比較地点_割合\n"
        "全碑,全種別,氾濫平野・海岸平野,1,0.5,5,0.5\n"
        "全碑,全種別,台地・段丘,1,0.5,5,0.5\n"
    )
    (out_dir / "landform_all.csv").write_text(lf_csv, encoding='utf-8-sig')

    (out_dir / "relocated_all.csv").write_text("ID,碑名\n01001,移転テスト\n", encoding='utf-8-sig')

    pref_counts_csv = (
        "県コード,県名,碑_数,移転碑_数,比較地点_数,種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "01,北海道,1,1,5,1,0,0,0,0,0,0\n"
        "02,青森県,1,0,5,0,0,1,0,0,0,0\n"
        "全国,合計,2,1,10,1,0,1,0,0,0,0\n"
    )
    (out_dir / "pref_counts_all.csv").write_text(pref_counts_csv, encoding='utf-8-sig')

    (out_dir / "years_all.csv").write_text("年代,碑_数\n", encoding='utf-8-sig')

    # グラフ画像とPDF
    (out_dir / "fig" / "years_all.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00dummy")
    (out_dir / "fig" / "pref_counts_all.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00dummy")
    (out_dir / "national_report.pdf").write_bytes(b"%PDF-1.4 dummy")

    # monuments と landform
    # 01 の碑名に </script><b> を含める
    mon_01 = (
        "ID,碑名,建立年,所在地,災害種別,緯度,経度,データ取得日,県コード,市区町村コード,"
        "種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "01001,</script><b>危険碑</b>,1900,北海道某所,洪水,43.0,141.0,2026-09-24,01,01001,"
        "1,0,0,0,0,0,0\n"
    )
    (data_dir / "monuments_01.csv").write_text(mon_01, encoding='utf-8-sig')
    (data_dir / "landform_01.csv").write_text("ID,地形分類名,地形分類_状態\n01001,氾濫平野・海岸平野,取得済\n", encoding='utf-8-sig')
    (data_dir / "landform_points_01.csv").write_text("ID,地形分類_状態\n01001-P1,取得済\n", encoding='utf-8-sig')

    mon_02 = (
        "ID,碑名,建立年,所在地,災害種別,緯度,経度,データ取得日,県コード,市区町村コード,"
        "種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "02001,青森碑,1950,青森某所,津波,40.0,140.0,2026-09-24,02,02001,"
        "0,0,1,0,0,0,0\n"
    )
    (data_dir / "monuments_02.csv").write_text(mon_02, encoding='utf-8-sig')
    (data_dir / "landform_02.csv").write_text("ID,地形分類名,地形分類_状態\n02001,台地・段丘,取得済\n", encoding='utf-8-sig')
    (data_dir / "landform_points_02.csv").write_text("ID,地形分類_状態\n02001-P1,取得済\n", encoding='utf-8-sig')

    # site_dir に pref_01.html, pref_02.html を作成
    (site_dir / "pref_01.html").write_text("<html><body>北海道</body></html>", encoding='utf-8')
    (site_dir / "pref_02.html").write_text("<html><body>青森県</body></html>", encoding='utf-8')

    # 実行
    created = run_build_national(output_dir=out_dir, site_dir=site_dir, data_dir=data_dir, quiet=True)
    assert len(created) == 10

    idx_path = site_dir / "index.html"
    assert idx_path.exists()
    content = idx_path.read_text(encoding='utf-8')

    # PDF へのリンク
    assert 'href="national_report.pdf"' in content

    # pref_XX.html へのリンク
    assert 'href="pref_01.html"' in content
    assert 'href="pref_02.html"' in content

    # </script> がそのまま script 内に現れないこと
    assert "</script><b>" not in content
    assert r"<\/script><b>" in content

    # 埋め込み JSON を取り出して json.loads できること・行数
    m = re.search(r'const MONUMENTS = (\[.*?\]);', content, re.DOTALL)
    assert m is not None, "MONUMENTS JSON が見つかりません"
    json_text = m.group(1)
    loaded_mons = json.loads(json_text)
    assert len(loaded_mons) == 2
    assert loaded_mons[0][0] == "01001"
    assert loaded_mons[0][1] == "</script><b>危険碑</b>"
    assert loaded_mons[1][0] == "02001"


def test_real_data():
    """
    7. 実データ（ファイルがなければ skip、書き込まない）：
    load_monument_list が2,481行・データなし929、県×種別の件数が pref_counts_all と47県×7種別すべて一致、
    色分けの区分ごとの県の数が既知の答えと一致、landform_options が既知の答えの順
    """
    proc_dir = PROJECT_ROOT / "data" / "processed"
    out_dir = PROJECT_ROOT / "output"
    site_dir = PROJECT_ROOT / "docs"

    reqs = required_files(out_dir, proc_dir, site_dir)
    if any(not f.exists() for f in reqs):
        pytest.skip("実データまたは中間ファイルが存在しないためスキップします")

    # load_monument_list の検証
    df_mon = load_monument_list(proc_dir)
    assert len(df_mon) == 2481
    assert (df_mon['地形分類名'] == 'データなし').sum() == 929

    # ID 重複なし
    assert df_mon['ID'].nunique() == 2481

    # pref_counts_all との照合
    df_pc = pd.read_csv(out_dir / "pref_counts_all.csv", dtype=str, encoding='utf-8-sig')
    disaster_cols = ['洪水', '地震', '津波', '土砂災害', '高潮', '火山災害', 'その他']

    for p in sorted(PREFECTURES.keys()):
        p_row = df_pc[df_pc['県コード'] == p]
        assert not p_row.empty, f"pref_counts_all に県 {p} がありません"
        p_row = p_row.iloc[0]

        # 碑の数
        expected_mon_count = int(p_row['碑_数'])
        actual_mon_count = len(df_mon[df_mon['県コード'] == p])
        assert actual_mon_count == expected_mon_count, f"県 {p} の碑の数不一致: {actual_mon_count} != {expected_mon_count}"

        # 7種別
        for d in disaster_cols:
            col_name = f"種別_{d}"
            expected_count = int(p_row[col_name])
            actual_count = len(df_mon[(df_mon['県コード'] == p) & (df_mon[col_name] == '1')])
            assert actual_count == expected_count, f"県 {p} の種別_{d} 不一致: {actual_count} != {expected_count}"

    # 色分けの区分ごとの県の数が既知の答えと一致
    # 既知の答え（0／1〜9／10〜19／20〜49／50〜99／100以上）
    expected_dist = {
        '碑_数': [0, 1, 6, 18, 15, 7],
        '種別_洪水': [1, 5, 20, 17, 4, 0],
        '種別_地震': [3, 24, 7, 9, 3, 1],
        '種別_津波': [20, 15, 3, 6, 2, 1],
        '種別_土砂災害': [1, 24, 12, 8, 2, 0],
        '種別_高潮': [27, 16, 3, 1, 0, 0],
        '種別_火山災害': [35, 7, 5, 0, 0, 0],
        '種別_その他': [12, 32, 3, 0, 0, 0],
    }
    class_order = ["0", "1〜9", "10〜19", "20〜49", "50〜99", "100以上"]

    for col, exp_counts in expected_dist.items():
        counts = {lbl: 0 for lbl in class_order}
        for p in sorted(PREFECTURES.keys()):
            val = int(df_pc[df_pc['県コード'] == p].iloc[0][col])
            c_lbl = color_class(val)
            counts[c_lbl] += 1
        actual_dist = [counts[lbl] for lbl in class_order]
        assert actual_dist == exp_counts, f"{col} の区分分布不一致: {actual_dist} != {exp_counts}"

    # landform_options が既知の答えの順
    expected_lf_order = [
        '氾濫平野・海岸平野', '山地斜面等', '自然堤防', '台地・段丘', '砂州・砂丘', '扇状地',
        '旧水部', '山麓堆積地形', '旧河道', '水部', '後背低地・湿地', '河川敷・浜',
        '天井川等', '崖・段丘崖', '地すべり地形', '凹地・浅い谷', '落堀', 'データなし'
    ]
    assert landform_options(df_mon) == expected_lf_order


def test_build_national_quiet_private_info_error(tmp_path, monkeypatch):
    """find_private_info が1件返すよう差し替えて quiet=True で呼ぶと RuntimeError"""
    out_dir = tmp_path / "output"
    site_dir = tmp_path / "docs"
    data_dir = tmp_path / "data"

    out_dir.mkdir()
    (out_dir / "fig").mkdir()
    site_dir.mkdir()
    data_dir.mkdir()

    fake_prefs = {"01": "北海道"}
    fake_tile = {"01": (0, 0)}
    monkeypatch.setattr(build_national, "PREFECTURES", fake_prefs)
    monkeypatch.setattr(build_national, "TILE_LAYOUT", fake_tile)

    # 最小限の必要ファイルを生成
    (out_dir / "summary_all.csv").write_text("範囲,災害種別,指標,碑_中央値,比較地点_中央値,差の中央値,碑の方が大きい割合\n", encoding='utf-8-sig')
    (out_dir / "hazard_summary_all.csv").write_text("範囲,災害種別,ハザード,碑_数,碑_区域内,比較地点_数,比較地点_区域内,碑_3m以上,比較地点_3m以上\n", encoding='utf-8-sig')
    (out_dir / "landform_all.csv").write_text("範囲,災害種別,地形分類名,碑_件数,碑_割合,比較地点_件数,比較地点_割合\n", encoding='utf-8-sig')
    (out_dir / "relocated_all.csv").write_text("ID,碑名\n", encoding='utf-8-sig')
    (out_dir / "pref_counts_all.csv").write_text(
        "県コード,県名,碑_数,移転碑_数,比較地点_数,種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "01,北海道,0,0,0,0,0,0,0,0,0,0\n"
        "全国,合計,0,0,0,0,0,0,0,0,0,0\n",
        encoding='utf-8-sig'
    )
    (out_dir / "years_all.csv").write_text("年代,碑_数\n", encoding='utf-8-sig')
    (out_dir / "fig" / "years_all.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00dummy")
    (out_dir / "fig" / "pref_counts_all.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00dummy")
    (out_dir / "national_report.pdf").write_bytes(b"%PDF-1.4 dummy")

    (data_dir / "monuments_01.csv").write_text("ID,碑名,建立年,所在地,災害種別,緯度,経度,データ取得日,県コード,市区町村コード\n", encoding='utf-8-sig')
    (data_dir / "landform_01.csv").write_text("ID,地形分類名,地形分類_状態\n", encoding='utf-8-sig')
    (data_dir / "landform_points_01.csv").write_text("ID,地形分類_状態\n", encoding='utf-8-sig')
    (site_dir / "pref_01.html").write_text("<html></html>", encoding='utf-8')

    # find_private_info を差し替えて1件返すようにする
    monkeypatch.setattr(
        build_national,
        "find_private_info",
        lambda paths: [("dummy_path.html", 1, "メールアドレス")]
    )

    with pytest.raises(RuntimeError) as exc_info:
        run_build_national(output_dir=out_dir, site_dir=site_dir, data_dir=data_dir, quiet=True)

    assert "公開前チェック：問題あり（1件）" in str(exc_info.value)

