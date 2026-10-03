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
    
    # history (完了と失敗が混ざる)
    df_hist = pd.DataFrame([
        {'実行日時': '2026-08-10 10:00', '新データ取得日': '2026-08-01', '新基数': '70', '追加': '1', '変更': '0', '削除': '0', '結果': '完了'},
        {'実行日時': '2026-08-20 11:00', '新データ取得日': '2026-08-02', '新基数': '70', '追加': '0', '変更': '0', '削除': '0', '結果': '失敗（中断）'},
        {'実行日時': '2026-08-30 12:00', '新データ取得日': '2026-08-03', '新基数': '71', '追加': '1', '変更': '0', '削除': '0', '結果': '完了'}
    ])
    df_hist.to_csv(out_dir / f"update_history_{pref}.csv", index=False, encoding='utf-8-sig')
    
    # data/processed/monuments
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    df_mon = pd.DataFrame({'ID': [f'{pref}001', f'{pref}002'], 'データ取得日': ['2026-09-20', '2026-09-24']})
    df_mon.to_csv(data_dir / f"monuments_{pref}.csv", index=False, encoding='utf-8-sig')
    
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
    assert idx_text.count('<img src="fig/') == 6
    assert 'href="data/summary_36.csv"' in idx_text
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
