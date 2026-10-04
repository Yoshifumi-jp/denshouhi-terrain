import pytest
import shutil
import pandas as pd
from pathlib import Path
from src.build_site import build_site
from src.check_public import find_private_info

def create_fake_output(tmp_path, pref="36"):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    
    (out_dir / "fig").mkdir()
    for f in ["box_elevation", "box_slope", "box_river_dist", "box_river_height", "box_coast_dist", "bar_landform"]:
        (out_dir / "fig" / f"{f}_{pref}.png").write_bytes(b'fake_png')
        
    (out_dir / f"map_{pref}.html").write_text("fake map", encoding="utf-8")
    
    # summary
    df_sum = pd.DataFrame([
        {'範囲': '全碑', '災害種別': '全種別', '指標': '標高_m', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '10', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '5', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '5', '碑の方が大きい割合': '0.143'},
        {'範囲': '全碑', '災害種別': '全種別', '指標': '傾斜_度', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '2', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '1', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '1', '碑の方が大きい割合': '0.8'},
        {'範囲': '全碑', '災害種別': '全種別', '指標': '河川までの距離_m', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '100', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '200', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '-100', '碑の方が大きい割合': '0.3'},
        {'範囲': '全碑', '災害種別': '全種別', '指標': '河川との高さの差_m', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '5', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '3', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '2', '碑の方が大きい割合': '0.6'},
        {'範囲': '全碑', '災害種別': '全種別', '指標': '海岸までの距離_m', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '1000', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '1500', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '-500', '碑の方が大きい割合': '0.2'},
        {'範囲': '移転碑を除く', '災害種別': '全種別', '指標': '標高_m', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '999', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '6', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '5', '碑の方が大きい割合': '0.15'},
        # スクリプトを埋め込んでエスケープをテスト
        {'範囲': '全碑', '災害種別': '全種別', '指標': '<script>alert(1)</script>', '碑_数': '2', '碑_除外数': '0', '碑_中央値': '1', '碑_第1四分位': '0', '碑_第3四分位': '0', '比較地点_数': '10', '比較地点_除外数': '0', '比較地点_中央値': '1', '比較地点_第1四分位': '0', '比較地点_第3四分位': '0', '組の数': '20', '差の中央値': '0', '碑の方が大きい割合': '0'}
    ])
    df_sum = df_sum[['範囲', '災害種別', '指標', '碑_数', '碑_除外数', '碑_中央値', '碑_第1四分位', '碑_第3四分位', '比較地点_数', '比較地点_除外数', '比較地点_中央値', '比較地点_第1四分位', '比較地点_第3四分位', '組の数', '差の中央値', '碑の方が大きい割合']]
    df_sum.to_csv(out_dir / f"summary_{pref}.csv", index=False, encoding='utf-8-sig')
    
    # others
    pd.DataFrame({'dummy': [1]}).to_csv(out_dir / f"landform_{pref}.csv", index=False, encoding='utf-8-sig')
    pd.DataFrame({'dummy': [1]}).to_csv(out_dir / f"relocated_{pref}.csv", index=False, encoding='utf-8-sig')
    
    # denshou
    pd.DataFrame({'ID': ['01']}).to_csv(out_dir / f"denshou_{pref}.csv", index=False, encoding='utf-8-sig')
    pd.DataFrame({
        '主な種別': ['津波', '洪水'],
        '碑の数': ['10', '5'],
        '差あり': ['8', '0'],
        '年数_中央値': ['30', '—'],
        '年数_最小': ['0', '—'],
        '年数_最大': ['100', '—']
    }).to_csv(out_dir / f"denshou_summary_{pref}.csv", index=False, encoding='utf-8-sig')
    pd.DataFrame({
        '災害の名前': ['大津波', '小洪水'],
        '発生年': ['1900', '1950'],
        '碑の数': ['3', '2'],
        '標高_中央値': ['10.5', '5.0'],
        '海岸までの距離_中央値': ['100.0', '500.0']
    }).to_csv(out_dir / f"disaster_groups_{pref}.csv", index=False, encoding='utf-8-sig')
    
    # fig
    fig_dir = out_dir / "fig"
    fig_dir.mkdir(exist_ok=True)
    for f in ["box_elevation", "box_slope", "box_river_dist", "box_river_height", "box_coast_dist", "bar_landform", "denshou_years", "disaster_groups"]:
        (fig_dir / f"{f}_{pref}.png").touch()
    # history (完了と失敗が混ざる)
    df_hist = pd.DataFrame([
        {'実行日時': '2026-08-10 10:00', '新データ取得日': '2026-08-01', '新基数': '70', '追加': '1', '変更': '0', '削除': '0', '結果': '完了'},
        {'実行日時': '2026-08-20 11:00', '新データ取得日': '2026-08-02', '新基数': '70', '追加': '0', '変更': '0', '削除': '0', '結果': '失敗（中断）'},
        {'実行日時': '2026-08-30 12:00', '新データ取得日': '2026-08-03', '新基数': '71', '追加': '1', '変更': '0', '削除': '0', '結果': '完了'}
    ])
    df_hist.to_csv(out_dir / f"update_history_{pref}.csv", index=False, encoding='utf-8-sig')
    
    # data/processed/monuments
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    df_mon = pd.DataFrame({'ID': [f'{pref}001', f'{pref}002'], 'データ取得日': ['2026-09-20', '2026-09-24']})
    df_mon.to_csv(data_dir / f"monuments_{pref}.csv", index=False, encoding='utf-8-sig')
    
    df_haz_csv = pd.DataFrame({'ID': ['1', '2', '3'], '取得日': ['2026-09-30', '2026-10-02', '']})
    df_haz_csv.to_csv(data_dir / f"hazard_{pref}.csv", index=False, encoding='utf-8-sig')
    
    HAZ_COLS = ['範囲', '災害種別', 'ハザード', '碑_数', '碑_取得不可', '碑_区域内', '碑_区域内の割合', '碑_3m以上', '碑_3m以上の割合', '比較地点_数', '比較地点_取得不可', '比較地点_区域内', '比較地点_区域内の割合', '比較地点_3m以上', '比較地点_3m以上の割合']
    haz_rows = [
        ['全碑', '全種別', '洪水（想定最大規模）', 10, 0, 3, 0.999, 1, 0.999, 40, 0, 6, 0.999, 2, 0.999],
        ['全碑', '全種別', '津波', 10, 0, 7, 0.999, 5, 0.999, 40, 0, 10, 0.999, 0, 0.999],
        ['全碑', '全種別', '高潮', 10, 0, 0, 0.999, 0, 0.999, 40, 0, 1, 0.999, 1, 0.999],
        ['全碑', '全種別', '土砂災害', 10, 0, 2, 0.999, '', '', 40, 0, 4, 0.999, '', ''],
        ['移転碑を除く', '全種別', '津波', 9, 0, 9, 1.0, 9, 1.0, 35, 0, 35, 1.0, 35, 1.0],
    ]
    haz_sum_file = out_dir / f"hazard_summary_{pref}.csv"
    pd.DataFrame(haz_rows, columns=HAZ_COLS).to_csv(haz_sum_file, index=False, encoding='utf-8-sig')
    with open(haz_sum_file, 'a', encoding='utf-8-sig') as f:
        f.write("注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。\n")
        f.write("注：想定区域との重なりを示すもので、危険度の判定ではありません。出典：ハザードマップポータルサイト（加工して作成）\n")

    return out_dir

def test_build_site(tmp_path):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    
    # e. dev/ フォルダの中身が変わらないことの確認用
    dev_dir = site_dir / "dev"
    dev_dir.mkdir(parents=True)
    dev_file = dev_dir / "test.txt"
    dev_file.write_text("dev file")
    dev_mtime = dev_file.stat().st_mtime
    
    build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    
    # a. ファイルができる
    assert (site_dir / "index.html").exists()
    assert (site_dir / "map_36.html").exists()
    assert (site_dir / ".nojekyll").exists()
    assert (site_dir / "fig" / "box_elevation_36.png").exists()
    assert (site_dir / "data" / "summary_36.csv").exists()
    
    # b, c, d, g
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    assert '<meta name="viewport"' in idx_text
    assert '伝承碑データ取得日：2026-09-24' in idx_text
    assert '碑の数：2基' in idx_text
    assert 'href="map_36.html"' in idx_text
    assert idx_text.count('<img src="fig/') == 8
    assert 'href="data/summary_36.csv"' in idx_text
    
    # 伝承内容の分析
    assert '<h2>伝承内容の分析</h2>' in idx_text
    assert '災害から建立までの年数（主な種別ごと）' in idx_text
    assert '<td>大津波(1900)</td><td>3</td>' in idx_text
    assert '小洪水' not in idx_text # 2基なので出ない
    
    assert 'href="data/denshou_36.csv"' in idx_text
    assert 'href="data/denshou_summary_36.csv"' in idx_text
    assert 'href="data/disaster_groups_36.csv"' in idx_text
    
    assert (site_dir / "data" / "denshou_36.csv").exists()
    assert (site_dir / "data" / "denshou_summary_36.csv").exists()
    assert (site_dir / "data" / "disaster_groups_36.csv").exists()
    assert (site_dir / "fig" / "denshou_years_36.png").exists()
    assert (site_dir / "fig" / "disaster_groups_36.png").exists()
    
    assert '国土数値情報' in idx_text
    assert '非商用' in idx_text
    
    # c. 割合のフォーマットと行全体の一致
    assert '<tr><td>標高(m)</td><td>10</td><td>5</td><td>5</td><td>14%</td></tr>' in idx_text
    assert '<tr><td>傾斜(度)</td><td>2</td><td>1</td><td>1</td><td>80%</td></tr>' in idx_text
    # 移転碑を除く行が出ていないこと
    assert '999' not in idx_text # 標高の中央値999は「移転碑を除く」の行
    
    # d. 更新履歴 (完了のみ、新しい順)
    history_start = idx_text.find('<h2>更新履歴</h2>')
    assert history_start != -1
    history_html = idx_text[history_start:]
    
    pos_30 = history_html.find('<td>2026-08-30</td>')
    pos_10 = history_html.find('<td>2026-08-10</td>')
    assert pos_30 != -1 and pos_10 != -1
    assert pos_30 < pos_10
    assert '2026-08-20' not in history_html # 失敗
    
    # g. HTMLエスケープ
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in idx_text
    
    # e. devが変わらない
    assert dev_file.read_text() == "dev file"
    assert dev_file.stat().st_mtime == dev_mtime

def test_build_site_missing_file(tmp_path, capsys):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    
    # わざと消す
    (out_dir / "map_36.html").unlink()
    
    with pytest.raises(SystemExit) as exc:
        build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
        
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "map_36.html" in captured.out
    
def test_build_site_no_history(tmp_path):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    
    # history を空にする
    pd.DataFrame(columns=['実行日時', '結果']).to_csv(out_dir / "update_history_36.csv", index=False)
    
    build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    assert '最終更新：—' in idx_text

def test_build_site_missing_columns(tmp_path, capsys):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    
    # summary_36.csv から「碑_中央値」を消す
    sum_csv = out_dir / "summary_36.csv"
    df = pd.read_csv(sum_csv)
    df = df.drop(columns=['碑_中央値'])
    df.to_csv(sum_csv, index=False, encoding='utf-8-sig')
    
    with pytest.raises(SystemExit) as exc:
        build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
        
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "エラー: summary_36.csv に必要な列がありません: 碑_中央値" in captured.out

def test_build_site_real_columns():
    real_csv = Path(__file__).resolve().parent.parent / "output" / "summary_36.csv"
    if not real_csv.exists():
        pytest.skip("本物の output/summary_36.csv がないためスキップします")
        
    df = pd.read_csv(real_csv)
    required_cols = ['指標', '碑_中央値', '比較地点_中央値', '差の中央値', '碑の方が大きい割合']
    for c in required_cols:
        assert c in df.columns

def test_hazard_section_table(tmp_path):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    
    import re
    table_match = re.search(r'<h2>ハザードマップの想定区域との重なり</h2>.*?<tbody>(.*?)</tbody>', idx_text, re.DOTALL)
    assert table_match
    tbody_html = table_match.group(1)
    
    rows = []
    for tr in re.findall(r'<tr>(.*?)</tr>', tbody_html, re.DOTALL):
        cols = re.findall(r'<td>(.*?)</td>', tr, re.DOTALL)
        rows.append(cols)
        
    expected = [
        ['洪水（想定最大規模）', '30%（3／10基）', '15%（6／40点）', '10%（1／10基）', '5%（2／40点）'],
        ['津波', '70%（7／10基）', '25%（10／40点）', '50%（5／10基）', '0%（0／40点）'],
        ['高潮', '0%（0／10基）', '2%（1／40点）', '0%（0／10基）', '2%（1／40点）'],
        ['土砂災害', '20%（2／10基）', '10%（4／40点）', '—', '—'],
    ]
    assert rows == expected
    assert "9／9基" not in idx_text
    assert "35／35点" not in idx_text

def test_hazard_section_texts(tmp_path):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    
    assert "<h2>ハザードマップの想定区域との重なり</h2>" in idx_text
    assert "想定区域との重なりを示すもので、危険度の判定ではありません。" in idx_text
    assert "ハザード情報取得日：2026-10-02" in idx_text
    
    from src.hazard_layers import HAZARD_DATA_NOTES
    assert HAZARD_DATA_NOTES['36'][0] in idx_text
    
    pos_denshou = idx_text.find("<h2>伝承内容の分析</h2>")
    pos_hazard = idx_text.find("<h2>ハザードマップの想定区域との重なり</h2>")
    pos_dl = idx_text.find("<h2>データのダウンロード（CSV、Excel で開けます）</h2>")
    assert pos_denshou < pos_hazard < pos_dl

def test_hazard_notes_only_36(tmp_path, monkeypatch):
    from src import prefectures
    import src.build_site
    new_pref = prefectures.PREFECTURES.copy()
    new_pref["99"] = "テスト県"
    monkeypatch.setattr(src.build_site, "PREFECTURES", new_pref)
    
    out_dir = create_fake_output(tmp_path, "99")
    site_dir = tmp_path / "docs"
    build_site("99", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    
    from src.hazard_layers import HAZARD_DATA_NOTES
    assert HAZARD_DATA_NOTES['36'][0] not in idx_text

def test_hazard_source_and_notice(tmp_path):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    
    assert 'href="https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html"' in idx_text
    assert "{HAZARD_SOURCE_URL}" not in idx_text
    
    notice_text = "ハザードマップの想定区域は国・都道府県が公表した想定です。"
    assert idx_text.count(notice_text) == 1

def test_hazard_summary_copied(tmp_path):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
    
    assert (site_dir / "data" / "hazard_summary_36.csv").exists()
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    assert 'href="data/hazard_summary_36.csv"' in idx_text

def test_missing_hazard_summary(tmp_path, capsys):
    out_dir = create_fake_output(tmp_path, "36")
    site_dir = tmp_path / "docs"
    
    (out_dir / "hazard_summary_36.csv").unlink()
    
    with pytest.raises(SystemExit) as exc:
        build_site("36", output_dir=out_dir, site_dir=site_dir, data_dir=tmp_path / "data" / "processed")
        
    assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "hazard_summary_" in captured.out
    assert "python src/update.py --pref" in captured.out

def test_real_hazard_table(tmp_path):
    proj_root = Path(__file__).resolve().parent.parent
    real_csv = proj_root / "output" / "hazard_summary_36.csv"
    if not real_csv.exists():
        pytest.skip("本物の output/hazard_summary_36.csv がないためスキップします")
        
    site_dir = tmp_path / "docs"
    build_site("36", output_dir=proj_root / "output", site_dir=site_dir, data_dir=proj_root / "data" / "processed")
    idx_text = (site_dir / "index.html").read_text(encoding="utf-8")
    
    import re
    table_match = re.search(r'<h2>ハザードマップの想定区域との重なり</h2>.*?<tbody>(.*?)</tbody>', idx_text, re.DOTALL)
    assert table_match
    tbody_html = table_match.group(1)
    
    rows = []
    for tr in re.findall(r'<tr>(.*?)</tr>', tbody_html, re.DOTALL):
        cols = re.findall(r'<td>(.*?)</td>', tr, re.DOTALL)
        rows.append(cols)
        
    expected_rows = [
        ['洪水（想定最大規模）', '23%（16／71基）', '15%（53／349点）', '6%（4／71基）', '8%（28／349点）'],
        ['津波', '70%（50／71基）', '21%（75／349点）', '55%（39／71基）', '11%（37／349点）'],
        ['高潮', '34%（24／71基）', '15%（53／349点）', '0%（0／71基）', '0%（1／349点）'],
        ['土砂災害', '31%（22／71基）', '9%（30／349点）', '—', '—'],
    ]
    assert rows == expected_rows
    assert "ハザード情報取得日：2026-10-04" in idx_text
