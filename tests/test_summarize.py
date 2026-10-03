import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch
import matplotlib
matplotlib.use('Agg')

from src import summarize

def create_dummy_data(tmp_path):
    pref = '99'
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # 碑データ作成
    # 碑A(01): 移転あり, 津波(1), 洪水(0). 標高10, 河川状態:取得済（参考値：10mメッシュ）
    # 碑B(02): 移設あり, 津波(1), 洪水(1). 標高20, 河川状態:取得済
    # 碑C(03): 移転なし, 津波(0), 洪水(1). 標高30, 河川状態:取得済, 地形コード空
    
    mon_main = pd.DataFrame({
        'ID': ['01', '02', '03'],
        '碑名': ['碑A', '碑B', '碑C'],
        '所在地': ['所A', '所B', '所C'],
        '伝承内容': ['あいう移転えお', 'かき移設くけ', 'さしすせそ'],
        '種別_洪水': [0, 1, 1],
        '種別_地震': [0, 0, 0],
        '種別_津波': [1, 1, 0],
        '種別_土砂災害': [0, 0, 0],
        '種別_高潮': [0, 0, 0],
        '種別_火山災害': [0, 0, 0],
        '種別_その他': [0, 0, 0]
    })
    
    mon_elev = pd.DataFrame({
        'ID': ['01', '02', '03'],
        '標高_m': [10.0, 20.0, 30.0],
        '傾斜_度': [1.0, 2.0, 3.0],
        '取得状態': ['取得済', '取得済', '取得済']
    })
    
    mon_rc = pd.DataFrame({
        'ID': ['01', '02', '03'],
        '河川までの距離_m': [100, 200, 300],
        '河川との高さの差_m': [1.0, 2.0, 3.0],
        '河川_状態': ['取得済（参考値：10mメッシュ）', '取得済', '取得済'],
        '海岸までの距離_m': [1000, 2000, 3000],
        '海岸_状態': ['取得済', '取得済', '取得済']
    })
    
    mon_lf = pd.DataFrame({
        'ID': ['01', '02', '03'],
        '地形分類名': ['山地', '平野', '台地'],
        '地形分類コード': ['01', '02', ''],
        '地形分類_状態': ['取得済', '取得済', '取得済']
    })
    
    # 比較地点データ作成
    # 碑Aの比較地点: A1, A2
    # 碑Bの比較地点: B1, B2, B3
    # 碑Cの比較地点: なし (あるいは取得不可にして「使える比較地点0」にする)
    
    pt_main = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
        '元の碑ID': ['01', '01', '02', '02', '02', '03'],
        '種別_洪水': [0, 0, 1, 1, 1, 1],
        '種別_地震': [0, 0, 0, 0, 0, 0],
        '種別_津波': [1, 1, 1, 1, 1, 0],
        '種別_土砂災害': [0, 0, 0, 0, 0, 0],
        '種別_高潮': [0, 0, 0, 0, 0, 0],
        '種別_火山災害': [0, 0, 0, 0, 0, 0],
        '種別_その他': [0, 0, 0, 0, 0, 0]
    })
    
    pt_elev = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
        '標高_m': [5.0, 7.0, 22.0, 30.0, 40.0, 99.0],
        '傾斜_度': [1.0, 1.0, 2.0, 2.0, 2.0, 9.0],
        '取得状態': ['取得済', '取得済', '取得済', '取得済', '取得済', '取得不可']
    })
    
    pt_rc = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
        '河川までの距離_m': [110, 120, 210, 220, 230, np.nan],
        '河川との高さの差_m': [1.1, 1.2, 2.1, 2.2, 2.3, np.nan],
        '河川_状態': ['取得済', '取得済', '取得済', '取得済', '取得済', 'データなし'],
        '海岸までの距離_m': [1100, 1200, 2100, 2200, 2300, np.nan],
        '海岸_状態': ['取得済', '取得済', '取得済', '取得済', '取得済', 'データなし']
    })
    
    pt_lf = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4', 'p5', 'p6'],
        '地形分類名': ['山地', '山地', '平野', '平野', '平野', '台地'],
        '地形分類コード': ['01', '01', '02', '02', '02', '03'],
        '地形分類_状態': ['取得済', '取得済', '取得済', '取得済', '取得済', '取得不可']
    })
    
    mon_main.to_csv(data_dir / f"monuments_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_elev.to_csv(data_dir / f"elevation_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_rc.to_csv(data_dir / f"river_coast_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_lf.to_csv(data_dir / f"landform_{pref}.csv", index=False, encoding='utf-8-sig')
    
    pt_main.to_csv(data_dir / f"points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_elev.to_csv(data_dir / f"elevation_points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_rc.to_csv(data_dir / f"river_coast_points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_lf.to_csv(data_dir / f"landform_points_{pref}.csv", index=False, encoding='utf-8-sig')
    
    return pref

def test_tick_positions():
    # 種別5つのときの positions
    # (1, 1.4), (2.5, 2.9), (4.0, 4.4), (5.5, 5.9), (7.0, 7.4)
    positions = [1.0, 1.4, 2.5, 2.9, 4.0, 4.4, 5.5, 5.9, 7.0, 7.4]
    expected = [1.2, 2.7, 4.2, 5.7, 7.2]
    result = summarize.tick_positions(positions)
    for r, e in zip(result, expected):
        assert abs(r - e) < 1e-9

def test_invalid_pref(monkeypatch, capsys):
    with patch("sys.argv", ["summarize.py", "--pref", "99"]):
        with pytest.raises(SystemExit):
            summarize.main()
    captured = capsys.readouterr()
    assert "エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。" in captured.out

    with patch("sys.argv", ["summarize.py", "--pref", "all"]):
        with pytest.raises(SystemExit):
            summarize.main()
    captured = capsys.readouterr()
    assert "エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。" in captured.out

def test_summarize_logic(tmp_path, monkeypatch):
    monkeypatch.setitem(summarize.PREFECTURES, '99', 'テスト県')
    monkeypatch.setattr(summarize, "PROJECT_ROOT", tmp_path)
    pref = create_dummy_data(tmp_path)
    
    with patch("sys.argv", ["summarize.py", "--pref", pref]):
        summarize.main()
        
    out_dir = tmp_path / "output"
    
    # グラフ等の存在確認
    assert (out_dir / f"summary_{pref}.csv").exists()
    assert (out_dir / f"landform_{pref}.csv").exists()
    assert (out_dir / f"relocated_{pref}.csv").exists()
    
    summary_df = pd.read_csv(out_dir / f"summary_{pref}.csv", encoding='utf-8-sig')
    if len(summary_df) > 0 and str(summary_df.iloc[-1, 0]).startswith('注'):
        summary_df = summary_df.iloc[:-1]
        
    lf_df = pd.read_csv(out_dir / f"landform_{pref}.csv", encoding='utf-8-sig')
    if len(lf_df) > 0 and str(lf_df.iloc[-1, 0]).startswith('注'):
        lf_df = lf_df.iloc[:-1]
        
    relocated_df = pd.read_csv(out_dir / f"relocated_{pref}.csv", encoding='utf-8-sig', dtype={'ID': str})
    
    # a. 碑3基、比較地点各2~3点の偽データで、手計算の値と一致する
    # 標高_m の 全碑・全種別
    row_df = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == '標高_m')]
    row = row_df.iloc[0]
    # 碑: 10, 20, 30 -> 中央値 20.0
    # 比較: 5, 7, 22, 30, 40 -> 中央値 22.0
    # 差:
    # A (10) - pt_med(6.0) = 4.0
    # B (20) - pt_med(30.0) = -10.0
    # C (30) - pt_medなし (除外) -> 組に入らない
    # 組の数: 2
    # 差の中央値: -3.0
    # 大きい割合: 0.5
    assert row['碑_中央値'] == 20.0
    assert row['比較地点_中央値'] == 22.0
    assert row['組の数'] == 2
    assert row['差の中央値'] == -3.0
    assert row['碑の方が大きい割合'] == 0.5
    
    # 別の指標(河川との高さの差_m)でも1つ確かめる
    row_riv_a = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == '河川との高さの差_m')].iloc[0]
    assert row_riv_a['碑_中央値'] == 2.5
    assert row_riv_a['比較地点_中央値'] == 2.1
    assert row_riv_a['組の数'] == 1
    assert row_riv_a['差の中央値'] == pytest.approx(-0.2)
    assert row_riv_a['碑の方が大きい割合'] == 0.0
    
    # b. 伝承内容に「移転」「移設」がある碑は外れる
    # 移転碑: A, B
    # 移転碑を除く範囲では C のみ。Cは標高30。比較地点は0点
    row_ex = summary_df[(summary_df['範囲'] == '移転碑を除く') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == '標高_m')].iloc[0]
    assert row_ex['碑_中央値'] == 30.0
    assert row_ex['碑_数'] == 1
    assert row_ex['比較地点_数'] == 0
    
    assert len(relocated_df) == 2
    assert set(relocated_df['ID']) == {'01', '02'}
    
    # c. 河川_状態が「取得済（参考値：10mメッシュ）」の碑(A)は、河川との高さの差だけ除外。他の指標には入る
    row_riv = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == '河川との高さの差_m')].iloc[0]
    # 碑は B, C が有効。A(10mメッシュ)は除外
    assert row_riv['碑_除外数'] == 1
    assert row_riv['碑_数'] == 2 # B, C
    row_elev = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == '標高_m')].iloc[0]
    assert row_elev['碑_除外数'] == 0
    assert row_elev['碑_数'] == 3
    
    # d. 地形分類コードが空の行(C)は地形分類の除外に数えられ、構成比の分母に入らない
    lf_all = lf_df[(lf_df['範囲'] == '全碑') & (lf_df['災害種別'] == '全種別')]
    assert lf_all['碑_件数'].sum() == 2 # A, B のみ
    
    # e. 種別を2つ持つ碑(B:津波,洪水)が、両方の種別の行に数えられる
    row_tsunami = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '津波') & (summary_df['指標'] == '標高_m')].iloc[0]
    row_flood = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '洪水') & (summary_df['指標'] == '標高_m')].iloc[0]
    assert row_tsunami['碑_数'] == 2 # A, B
    assert row_flood['碑_数'] == 2 # B, C
    
    # f. 使える比較地点が0点の碑(C)は「組」に入らない
    # A, Bのみが組になるため組の数は2
    assert row_elev['組の数'] == 2
    
    # g. 2回実行でCSVが一致する
    # 1回目の内容を保持
    summary_txt1 = (out_dir / f"summary_{pref}.csv").read_text(encoding='utf-8-sig')
    lf_txt1 = (out_dir / f"landform_{pref}.csv").read_text(encoding='utf-8-sig')
    relocated_txt1 = (out_dir / f"relocated_{pref}.csv").read_text(encoding='utf-8-sig')
    
    with patch("sys.argv", ["summarize.py", "--pref", pref]):
        summarize.main()
        
    summary_txt2 = (out_dir / f"summary_{pref}.csv").read_text(encoding='utf-8-sig')
    lf_txt2 = (out_dir / f"landform_{pref}.csv").read_text(encoding='utf-8-sig')
    relocated_txt2 = (out_dir / f"relocated_{pref}.csv").read_text(encoding='utf-8-sig')
    
    assert summary_txt1 == summary_txt2
    assert lf_txt1 == lf_txt2
    assert relocated_txt1 == relocated_txt2
    
def test_missing_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(summarize.PREFECTURES, '98', 'テスト県2')
    monkeypatch.setattr(summarize, "PROJECT_ROOT", tmp_path)
    pref = '98'
    
    # フォルダだけ作成
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    with patch("sys.argv", ["summarize.py", "--pref", pref]):
        with pytest.raises(SystemExit):
            summarize.main()
            
    captured = capsys.readouterr()
    assert "ファイルが見つかりません" in captured.out
    assert "monuments_98.csv" in captured.out
    assert "points_98.csv" in captured.out
    assert "先に実行してください" in captured.out

def test_proportion_calculation(tmp_path, monkeypatch):
    monkeypatch.setitem(summarize.PREFECTURES, '97', 'テスト県3')
    monkeypatch.setattr(summarize, "PROJECT_ROOT", tmp_path)
    pref = '97'
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # 碑3基
    # 碑1: 標高10 (比較地点中央値 5) -> 差 +5
    # 碑2: 標高10 (比較地点中央値 10) -> 差 0
    # 碑3: 標高10 (比較地点中央値 15) -> 差 -5
    mon_main = pd.DataFrame({
        'ID': ['1', '2', '3'],
        '碑名': ['A', 'B', 'C'],
        '所在地': ['A', 'B', 'C'],
        '伝承内容': ['A', 'B', 'C'],
        '種別_洪水': [0, 0, 0],
        '種別_地震': [0, 0, 0],
        '種別_津波': [1, 1, 1],
        '種別_土砂災害': [0, 0, 0],
        '種別_高潮': [0, 0, 0],
        '種別_火山災害': [0, 0, 0],
        '種別_その他': [0, 0, 0]
    })
    
    mon_elev = pd.DataFrame({
        'ID': ['1', '2', '3'],
        '標高_m': [10.0, 10.0, 10.0],
        '傾斜_度': [0.0, 0.0, 0.0],
        '取得状態': ['取得済', '取得済', '取得済']
    })
    
    mon_rc = pd.DataFrame({
        'ID': ['1', '2', '3'],
        '河川までの距離_m': [100, 100, 100],
        '河川との高さの差_m': [1.0, 1.0, 1.0],
        '河川_状態': ['取得済', '取得済', '取得済'],
        '海岸までの距離_m': [1000, 1000, 1000],
        '海岸_状態': ['取得済', '取得済', '取得済']
    })
    
    mon_lf = pd.DataFrame({
        'ID': ['1', '2', '3'],
        '地形分類名': ['山地', '山地', '山地'],
        '地形分類コード': ['01', '01', '01'],
        '地形分類_状態': ['取得済', '取得済', '取得済']
    })
    
    pt_main = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3'],
        '元の碑ID': ['1', '2', '3'],
        '種別_洪水': [0, 0, 0],
        '種別_地震': [0, 0, 0],
        '種別_津波': [1, 1, 1],
        '種別_土砂災害': [0, 0, 0],
        '種別_高潮': [0, 0, 0],
        '種別_火山災害': [0, 0, 0],
        '種別_その他': [0, 0, 0]
    })
    
    pt_elev = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3'],
        '標高_m': [5.0, 10.0, 15.0],
        '傾斜_度': [0.0, 0.0, 0.0],
        '取得状態': ['取得済', '取得済', '取得済']
    })
    
    pt_rc = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3'],
        '河川までの距離_m': [100, 100, 100],
        '河川との高さの差_m': [1.0, 1.0, 1.0],
        '河川_状態': ['取得済', '取得済', '取得済'],
        '海岸までの距離_m': [1000, 1000, 1000],
        '海岸_状態': ['取得済', '取得済', '取得済']
    })
    
    pt_lf = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3'],
        '地形分類名': ['山地', '山地', '山地'],
        '地形分類コード': ['01', '01', '01'],
        '地形分類_状態': ['取得済', '取得済', '取得済']
    })
    
    mon_main.to_csv(data_dir / f"monuments_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_elev.to_csv(data_dir / f"elevation_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_rc.to_csv(data_dir / f"river_coast_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_lf.to_csv(data_dir / f"landform_{pref}.csv", index=False, encoding='utf-8-sig')
    
    pt_main.to_csv(data_dir / f"points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_elev.to_csv(data_dir / f"elevation_points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_rc.to_csv(data_dir / f"river_coast_points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_lf.to_csv(data_dir / f"landform_points_{pref}.csv", index=False, encoding='utf-8-sig')
    
    with patch("sys.argv", ["summarize.py", "--pref", pref]):
        summarize.main()
        
    out_dir = tmp_path / "output"
    summary_df = pd.read_csv(out_dir / f"summary_{pref}.csv", encoding='utf-8-sig')
    
    row_elev = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == '標高_m')].iloc[0]
    # 大きい割合が 0.333 になることを確認
    assert row_elev['碑の方が大きい割合'] == pytest.approx(0.333, abs=0.001)
