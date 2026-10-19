# -*- coding: utf-8 -*-
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from src import make_national_pdf as mnp
from src import build_national as bn
from src.make_national_pdf import make_national_pdf, get_required_files

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_missing_files(tmp_path, capsys):
    """足りないファイルがあるとき：tmp_path で呼び、終了コード1・何も書かない"""
    out_dir = tmp_path / "output"
    data_dir = tmp_path / "data"
    out_pdf = tmp_path / "national_report.pdf"

    out_dir.mkdir()
    data_dir.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        make_national_pdf(output_dir=out_dir, data_dir=data_dir, out_path=out_pdf, quiet=True)

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "エラー：ファイルが足りません：" in captured.out
    assert "先に実行してください：python src/summarize_national.py" in captured.out

    # PDF が作成されていないこと
    assert not out_pdf.exists()


def test_fake_data_generation(tmp_path, monkeypatch):
    """
    偽のデータ（tmp_path に2県分）で PDF を作り、
    (a) 戻り値が8
    (b) ファイルが %PDF で始まる
    (c) バイト列の中の /Type /Page（/Type /Pages を除く）の数が8
    (d) /MediaBox [ 0 0 595.44 841.68 ] が8回現れる（A4 縦）
    (e) Matplotlib と CreationDate の文字が含まれない
    """
    out_dir = tmp_path / "output"
    data_dir = tmp_path / "data"
    out_pdf = tmp_path / "national_report.pdf"

    out_dir.mkdir()
    (out_dir / "fig").mkdir()
    data_dir.mkdir()

    # 2県分に差し替え
    fake_prefs = {"01": "北海道", "02": "青森県"}
    fake_tile = {"01": (0, 0), "02": (0, 1)}
    monkeypatch.setattr(mnp, "PREFECTURES", fake_prefs)
    monkeypatch.setattr(mnp, "TILE_LAYOUT", fake_tile)
    monkeypatch.setattr(bn, "PREFECTURES", fake_prefs)
    monkeypatch.setattr(bn, "TILE_LAYOUT", fake_tile)

    # 必要なファイルを準備
    sum_csv = (
        "範囲,災害種別,指標,碑_中央値,比較地点_中央値,差の中央値,碑の方が大きい割合\n"
        "全碑,全種別,標高_m,10.0,20.0,-10.0,0.3\n"
        "全碑,全種別,傾斜_度,5.0,10.0,-5.0,0.4\n"
        "全碑,全種別,河川までの距離_m,100.0,200.0,-100.0,0.3\n"
        "全碑,全種別,河川との高さの差_m,2.0,5.0,-3.0,0.2\n"
        "全碑,全種別,海岸までの距離_m,1000.0,1500.0,-500.0,0.4\n"
    )
    (out_dir / "summary_all.csv").write_text(sum_csv, encoding="utf-8-sig")

    haz_csv = (
        "範囲,災害種別,ハザード,碑_数,碑_区域内,比較地点_数,比較地点_区域内,碑_3m以上,比較地点_3m以上\n"
        "全碑,全種別,洪水（想定最大規模）,2,1,10,2,0,0\n"
        "全碑,全種別,津波,2,1,10,1,1,0\n"
        "全碑,全種別,高潮,2,0,10,0,0,0\n"
        "全碑,全種別,土砂災害,2,0,10,1,,\n"
    )
    (out_dir / "hazard_summary_all.csv").write_text(haz_csv, encoding="utf-8-sig")

    lf_csv = (
        "範囲,災害種別,地形分類名,碑_件数,碑_割合,比較地点_件数,比較地点_割合\n"
        "全碑,全種別,氾濫平野・海岸平野,1,0.5,5,0.5\n"
        "全碑,全種別,台地・段丘,1,0.5,5,0.5\n"
    )
    (out_dir / "landform_all.csv").write_text(lf_csv, encoding="utf-8-sig")

    (out_dir / "relocated_all.csv").write_text("ID,碑名\n01001,移転テスト\n", encoding="utf-8-sig")

    pref_counts_csv = (
        "県コード,県名,碑_数,移転碑_数,比較地点_数,種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "01,北海道,1,1,5,1,0,0,0,0,0,0\n"
        "02,青森県,1,0,5,0,0,1,0,0,0,0\n"
        "全国,合計,2,1,10,1,0,1,0,0,0,0\n"
    )
    (out_dir / "pref_counts_all.csv").write_text(pref_counts_csv, encoding="utf-8-sig")

    # グラフ画像（matplotlib で実際に小さな PNG を作成）
    fig1, ax1 = plt.subplots(figsize=(2, 2))
    ax1.plot([1, 2], [3, 4])
    fig1.savefig(out_dir / "fig" / "years_all.png")
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(2, 2))
    ax2.plot([1, 2], [3, 4])
    fig2.savefig(out_dir / "fig" / "pref_counts_all.png")
    plt.close(fig2)

    # monuments と landform
    mon_01 = (
        "ID,碑名,建立年,所在地,災害種別,緯度,経度,データ取得日,県コード,市区町村コード,"
        "種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "01001,北海道碑,1900,北海道某所,洪水,43.0,141.0,2026-09-24,01,01001,"
        "1,0,0,0,0,0,0\n"
    )
    (data_dir / "monuments_01.csv").write_text(mon_01, encoding="utf-8-sig")
    (data_dir / "landform_01.csv").write_text("ID,地形分類名,地形分類_状態\n01001,氾濫平野・海岸平野,取得済\n", encoding="utf-8-sig")
    (data_dir / "landform_points_01.csv").write_text("ID,地形分類_状態\n01001-P1,取得済\n", encoding="utf-8-sig")

    mon_02 = (
        "ID,碑名,建立年,所在地,災害種別,緯度,経度,データ取得日,県コード,市区町村コード,"
        "種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n"
        "02001,青森碑,1950,青森某所,津波,40.0,140.0,2026-09-24,02,02001,"
        "0,0,1,0,0,0,0\n"
    )
    (data_dir / "monuments_02.csv").write_text(mon_02, encoding="utf-8-sig")
    (data_dir / "landform_02.csv").write_text("ID,地形分類名,地形分類_状態\n02001,台地・段丘,取得済\n", encoding="utf-8-sig")
    (data_dir / "landform_points_02.csv").write_text("ID,地形分類_状態\n02001-P1,取得済\n", encoding="utf-8-sig")

    # PDF 生成実行
    pages = make_national_pdf(output_dir=out_dir, data_dir=data_dir, out_path=out_pdf, quiet=True)

    # (a) 戻り値が8
    assert pages == 8
    assert out_pdf.exists()

    pdf_bytes = out_pdf.read_bytes()

    # (b) ファイルが %PDF で始まる
    assert pdf_bytes.startswith(b"%PDF")

    # (c) バイト列の中の /Type /Page（/Type /Pages を除く）の数が8
    page_count = pdf_bytes.count(b"/Type /Page") - pdf_bytes.count(b"/Type /Pages")
    assert page_count == 8

    # (d) /MediaBox [ 0 0 595.44 841.68 ] が8回現れる（A4 縦）
    assert pdf_bytes.count(b"/MediaBox [ 0 0 595.44 841.68 ]") == 8

    # (e) Matplotlib と CreationDate の文字が含まれない
    assert b"Matplotlib" not in pdf_bytes
    assert b"CreationDate" not in pdf_bytes


def test_real_data(tmp_path):
    """実データ（ファイルがなければ skip。書き込みは tmp_path だけ）：ページ数8"""
    proc_dir = PROJECT_ROOT / "data" / "processed"
    out_dir = PROJECT_ROOT / "output"

    reqs = get_required_files(out_dir, proc_dir)
    if any(not f.exists() for f in reqs):
        pytest.skip("実データまたは中間ファイルが存在しないためスキップします")

    out_pdf = tmp_path / "national_report.pdf"
    pages = make_national_pdf(output_dir=out_dir, data_dir=proc_dir, out_path=out_pdf, quiet=True)

    assert pages == 8
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0


def test_page_region_table(tmp_path):
    """landform_region_all.csv があるとき：表の見出し・並び順・割合・題名と注を確かめる"""
    lf_reg_csv = (
        "範囲,災害種別,地形分類名,地形分類コード,碑_件数,碑_割合,比較地点_件数,比較地点_割合\n"
        "全碑,全種別,山地,11,472,0.191,4078,0.332\n"
        "全碑,全種別,低地,51,1325,0.535,4331,0.353\n"
        "全碑,全種別,台地・段丘,41,264,0.107,1160,0.094\n"
        "移転碑を除く,全種別,低地,51,1200,0.520,4000,0.350\n"
    )
    (tmp_path / "landform_region_all.csv").write_text(lf_reg_csv, encoding="utf-8-sig", newline="\n")

    fig = mnp.make_page_region(tmp_path, 5, 118, "2026-09-24")
    try:
        assert len(fig.axes) == 1
        assert len(fig.axes[0].tables) == 1
        table = fig.axes[0].tables[0]
        celld = table.get_celld()

        # 見出し＋データ3行の計4行×5列
        assert len(celld) == 4 * 5

        headers = [celld[(0, c)].get_text().get_text().strip() for c in range(5)]
        assert headers == ["地形分類", "碑の数", "碑の割合", "まわりの数", "まわりの割合"]

        rows = [
            [celld[(r, c)].get_text().get_text().strip() for c in range(5)]
            for r in range(1, 4)
        ]
        assert rows == [
            ["低地", "1325", "53.5%", "4331", "35.3%"],
            ["山地", "472", "19.1%", "4078", "33.2%"],
            ["台地・段丘", "264", "10.7%", "1160", "9.4%"],
        ]

        texts = [t.get_text() for t in fig.texts]
        assert "地形分類（地域版・全碑・全種別）" in texts
        assert "地域版で値が取れなかった碑 5基・まわりの地点 118点は、割合の計算から除いています。" in texts
        assert (
            "地域版は詳細版より分類が粗い（中分類12種）ため、"
            "碑とまわりの地点（100m〜2,000m）が同じ分類になりやすく、差が出にくくなります。"
        ) in texts
    finally:
        plt.close(fig)


def test_page_region_missing(tmp_path):
    """landform_region_all.csv がないとき：表がなく、「表はありません」の文がある"""
    fig = mnp.make_page_region(tmp_path, 5, 118, "2026-09-24")
    try:
        assert all(len(ax.tables) == 0 for ax in fig.axes)
        texts = [t.get_text() for t in fig.texts]
        assert "地形分類（地域版・全碑・全種別）" in texts
        assert any("表はありません" in t for t in texts)
        assert not any("割合の計算から除いています" in t for t in texts)
    finally:
        plt.close(fig)


def test_page_artificial_tables(tmp_path):
    """landform_artificial_all.csv と landform_artificial_cross_all.csv があるとき：表A・表Bの並び・割合・見出し・注を確かめる"""
    lf_art_csv = (
        "範囲,災害種別,人工地形名,人工地形コード,碑_件数,碑_割合,比較地点_件数,比較地点_割合\n"
        "全碑,全種別,人工地形なし,0,1264,0.814,6312,0.841\n"
        "全碑,全種別,切土地,11201,39,0.025,214,0.029\n"
        "全碑,全種別,盛土地・埋立地,11202,199,0.128,732,0.098\n"
        "全碑,全種別,干拓地,11203,47,0.030,222,0.030\n"
        "全碑,洪水,盛土地・埋立地,11202,100,0.150,400,0.100\n"
    )
    (tmp_path / "landform_artificial_all.csv").write_text(lf_art_csv, encoding="utf-8-sig", newline="\n")

    lf_cross_csv = (
        "範囲,自然地形名,人工地形名,人工地形コード,碑_件数,碑_割合,比較地点_件数,比較地点_割合\n"
        "全碑,旧水部,干拓地,11203,47,0.412,219,0.472\n"
        "全碑,氾濫平野・海岸平野,盛土地・埋立地,11202,97,0.215,317,0.168\n"
        "全碑,旧水部,人工地形なし,0,1,0.009,3,0.006\n"
        "全碑,台地・段丘,干拓地,11203,0,0.000,2,0.003\n"
        "全碑,旧河道,切土地,11201,1,0.018,0,0.000\n"
        "全碑,崖・段丘崖,盛土地・埋立地,11202,1,0.143,0,0.000\n"
        "移転碑を除く,氾濫平野・海岸平野,盛土地・埋立地,11202,80,0.200,300,0.160\n"
        "注：割合は同じ自然地形の碑のうち人工地形を調べたものに対する割合です。,,,,,,,\n"
        "出典：国土地理院 地形分類（自然地形・人工地形）を加工して作成,,,,,,,\n"
    )
    (tmp_path / "landform_artificial_cross_all.csv").write_text(lf_cross_csv, encoding="utf-8-sig", newline="\n")

    fig = mnp.make_page_artificial(tmp_path, 929, 4890, "2026-09-24")
    try:
        assert len(fig.axes) == 2
        assert len(fig.axes[0].tables) == 1
        assert len(fig.axes[1].tables) == 1

        # 表Aの検証
        table_a = fig.axes[0].tables[0]
        celld_a = table_a.get_celld()
        assert len(celld_a) == 5 * 5

        headers_a = [celld_a[(0, c)].get_text().get_text().strip() for c in range(5)]
        assert headers_a == ["人工地形", "碑の数", "碑の割合", "まわりの数", "まわりの割合"]

        rows_a = [
            [celld_a[(r, c)].get_text().get_text().strip() for c in range(5)]
            for r in range(1, 5)
        ]
        assert rows_a == [
            ["盛土地・埋立地", "199", "12.8%", "732", "9.8%"],
            ["干拓地", "47", "3.0%", "222", "3.0%"],
            ["切土地", "39", "2.5%", "214", "2.9%"],
            ["人工地形なし", "1264", "81.4%", "6312", "84.1%"],
        ]

        # 表Bの検証（人工地形なし・碑_件数0・移転碑を除く・注・出典は入らない）
        table_b = fig.axes[1].tables[0]
        celld_b = table_b.get_celld()
        assert len(celld_b) == 5 * 6

        headers_b = [celld_b[(0, c)].get_text().get_text().strip() for c in range(6)]
        assert headers_b == ["自然地形", "人工地形", "碑の数", "碑の割合", "まわりの数", "まわりの割合"]

        rows_b = [
            [celld_b[(r, c)].get_text().get_text().strip() for c in range(6)]
            for r in range(1, 5)
        ]
        assert rows_b == [
            ["氾濫平野・海岸平野", "盛土地・埋立地", "97", "21.5%", "317", "16.8%"],
            ["旧水部", "干拓地", "47", "41.2%", "219", "47.2%"],
            ["崖・段丘崖", "盛土地・埋立地", "1", "14.3%", "0", "0.0%"],
            ["旧河道", "切土地", "1", "1.8%", "0", "0.0%"],
        ]

        texts = [t.get_text() for t in fig.texts]
        assert "地形分類（人工地形・全碑・全種別）" in texts
        assert "自然地形×人工地形（全碑）" in texts
        joined_texts = "".join(texts)
        assert "人工地形を調べていない碑 929基・まわりの地点 4,890点" in joined_texts
    finally:
        plt.close(fig)


def test_page_artificial_missing(tmp_path):
    """2つの CSV がないとき：表がなく、「表はありません」の文が2つある"""
    fig = mnp.make_page_artificial(tmp_path, 929, 4890, "2026-09-24")
    try:
        assert all(len(ax.tables) == 0 for ax in fig.axes)
        texts = [t.get_text() for t in fig.texts]
        assert "地形分類（人工地形・全碑・全種別）" in texts
        assert "自然地形×人工地形（全碑）" in texts
        missing_msgs = [t for t in texts if "表はありません" in t]
        assert len(missing_msgs) == 2
        assert not any("割合の計算から除いています" in t for t in texts)
    finally:
        plt.close(fig)



