import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from unittest.mock import patch
import html

from src import make_map

def test_main_type():
    assert make_map.main_type({'種別_地震': 1, '種別_津波': 1}) == '津波'
    assert make_map.main_type({'種別_高潮': 1, '種別_地震': 1, '種別_津波': 1}) == '津波'
    assert make_map.main_type({'種別_地震': 1}) == '地震'
    assert make_map.main_type({'種別_洪水': 1, '種別_土砂災害': 1}) == '洪水'
    assert make_map.main_type({'種別_津波': 0, '種別_地震': 0}) == 'その他'

def test_compare_with_surroundings():
    # 碑 5.0、比較地点 [3.0, 10.0, 20.0] → 中央値 10.0、「5.0 m 低い」を含む
    res1 = make_map.compare_with_surroundings(5.0, "取得済", [3.0, 10.0, 20.0])
    assert "5.0 m 低い" in res1
    
    # 碑 12.0、比較地点 [10.0, 11.0] → 中央値 10.5、「1.5 m 高い」を含む
    res2 = make_map.compare_with_surroundings(12.0, "取得済", [10.0, 11.0])
    assert "1.5 m 高い" in res2
    
    # 碑 10.4、比較地点 [10.0] →「ほぼ同じ」を含む
    res3 = make_map.compare_with_surroundings(10.4, "取得済", [10.0])
    assert "ほぼ同じ" in res3
    
    # 比較地点 [] →「比較地点なし」
    assert make_map.compare_with_surroundings(10.0, "取得済", []) == "比較地点なし"
    
    # 碑の状態が取得済でない →「比較地点なし」
    assert make_map.compare_with_surroundings(10.0, "データなし", [10.0]) == "比較地点なし"

def test_compare_boundaries():
    # 差がちょうど 1.0 →「高い」
    res1 = make_map.compare_with_surroundings(11.0, "取得済", [10.0])
    assert "1.0 m 高い" in res1
    
    # ちょうど −1.0 →「低い」
    res2 = make_map.compare_with_surroundings(9.0, "取得済", [10.0])
    assert "1.0 m 低い" in res2
    
    # 0.9 →「ほぼ同じ」
    res3 = make_map.compare_with_surroundings(10.9, "取得済", [10.0])
    assert "ほぼ同じ" in res3

def test_sanitize():
    row = {'伝承内容': '<script>alert(1)</script>'}
    html_str = make_map.build_popup_html(row, "比較", False)
    assert '<script>' not in html_str
    assert '&lt;script&gt;' in html_str

def test_missing_values():
    # 地形分類_状態「データなし」→「データなし」
    row = {'地形分類_状態': 'データなし'}
    html_str = make_map.build_popup_html(row, "比較", False)
    assert '地形分類：データなし' in html_str
    
    # 河川_状態「高さの差 対象外（河川まで1000m超）」→その文字列
    row2 = {'河川_状態': '高さの差 対象外（河川まで1000m超）'}
    html_str2 = make_map.build_popup_html(row2, "比較", False)
    assert '高さの差 対象外（河川まで1000m超）' in html_str2
    
    # 参考値→「（参考値）」
    row3 = {'河川との高さの差_m': 5.0, '河川_状態': '取得済（参考値：10mメッシュ）'}
    html_str3 = make_map.build_popup_html(row3, "比較", False)
    assert '5.0 m（参考値）' in html_str3
    
    # 標高が NaN →「データなし」
    row4 = {'標高_m': np.nan, '取得状態': '取得済'}
    html_str4 = make_map.build_popup_html(row4, "比較", False)
    assert '標高：データなし' in html_str4
    
    # どの場合もポップアップに「nan」を含まない
    for h in [html_str, html_str2, html_str3, html_str4]:
        assert 'nan' not in h.lower()

def test_relocated():
    row1 = {'伝承内容': 'あいう移設えお'}
    html_str1 = make_map.build_popup_html(row1, "比較", True)
    assert '※この碑は移設されています' in html_str1
    
    row2 = {'伝承内容': 'あいうえお'}
    html_str2 = make_map.build_popup_html(row2, "比較", False)
    assert '※この碑は移設されています' not in html_str2

def test_popup_contents():
    # j
    row_j = {
        '最寄り河川名': '名称不明',
        '河川までの距離_m': 100,
        '名前のある最寄り河川名': '瀬戸川',
        '名前のある河川までの距離_m': 3416,
        '河川_状態': '取得済',
    }
    html_j = make_map.build_popup_html(row_j, "比較", False)
    assert '瀬戸川（3416 m）' in html_j
    assert 'データなし' not in html_j.split('最寄り河川：')[1].split('</li>')[0]

    # k
    row_k1 = {
        '標高_m': 1.6,
        '標高データ種別': '1m（レーザ）',
        '取得状態': '取得済'
    }
    html_k1 = make_map.build_popup_html(row_k1, "比較", False)
    assert '1.6 m（1m（レーザ））' in html_k1
    
    row_k2 = {
        '標高_m': 1.6,
        '標高データ種別': '',
        '取得状態': '取得済'
    }
    html_k2 = make_map.build_popup_html(row_k2, "比較", False)
    assert '標高：1.6 m</li>' in html_k2
    assert '（' not in html_k2.split('標高：')[1].split('</li>')[0]

    # l
    row_l = {
        '建立年': '不明',
        '災害名': '地震',
        '所在地': '徳島'
    }
    html_l = make_map.build_popup_html(row_l, "比較", False)
    assert '建立年：不明' in html_l
    assert '災害名：地震' in html_l
    assert '所在地：徳島' in html_l

def test_main_integration(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(make_map.PREFECTURES, '99', 'テスト県')
    monkeypatch.setattr(make_map, "PROJECT_ROOT", tmp_path)
    from src import summarize
    monkeypatch.setattr(summarize, "PROJECT_ROOT", tmp_path)
    pref = '99'
    
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # 碑4基・主な種別3種類・比較地点あり
    mon_main = pd.DataFrame({
        'ID': ['01', '02', '03', '04'],
        '碑名': ['A', 'B', 'C', 'D'],
        '緯度': [35.0, 35.1, 35.2, 35.3],
        '経度': [135.0, 135.1, 135.2, 135.3],
        '所在地': ['A', 'B', 'C', 'D'],
        '伝承内容': ['A', 'B', 'C', 'D'],
        '種別_津波': [1, 0, 0, 0],
        '種別_洪水': [0, 1, 0, 0],
        '種別_地震': [0, 0, 1, 0],
        '種別_土砂災害': [0, 0, 0, 0],
        '種別_高潮': [0, 0, 0, 0],
        '種別_火山災害': [0, 0, 0, 0],
        '種別_その他': [0, 0, 0, 0]
        # Dはその他
    })
    
    mon_elev = pd.DataFrame({
        'ID': ['01', '02', '03', '04'],
        '標高_m': [10.0, 20.0, 30.0, 40.0],
        '標高データ種別': ['1m', '1m', '1m', '1m'],
        '傾斜_度': [0.0, 0.0, 0.0, 0.0],
        '取得状態': ['取得済', '取得済', '取得済', '取得済']
    })
    
    mon_rc = pd.DataFrame({
        'ID': ['01', '02', '03', '04'],
        '最寄り河川名': ['名称不明', '川B', '川C', '川D'],
        '名前のある最寄り河川名': ['川A', None, None, None],
        '河川までの距離_m': [100, 100, 100, 100],
        '名前のある河川までの距離_m': [200, None, None, None],
        '河川との高さの差_m': [1.0, 1.0, 1.0, 1.0],
        '河川_状態': ['取得済', '取得済', '取得済', '取得済'],
        '海岸までの距離_m': [1000, 1000, 1000, 1000],
        '海岸_状態': ['取得済', '取得済', '取得済', '取得済']
    })
    
    mon_lf = pd.DataFrame({
        'ID': ['01', '02', '03', '04'],
        '地形分類名': ['山地', '山地', '山地', '山地'],
        '地形分類コード': ['01', '01', '01', '01'],
        '地形分類_状態': ['取得済', '取得済', '取得済', '取得済']
    })
    
    pt_main = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4'],
        '元の碑ID': ['01', '02', '03', '04'],
    })
    
    pt_elev = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4'],
        '標高_m': [5.0, 10.0, 15.0, 20.0],
        '取得状態': ['取得済', '取得済', '取得済', '取得済']
    })
    
    pt_rc = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4']
    })
    
    pt_lf = pd.DataFrame({
        'ID': ['p1', 'p2', 'p3', 'p4']
    })
    
    mon_main.to_csv(data_dir / f"monuments_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_elev.to_csv(data_dir / f"elevation_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_rc.to_csv(data_dir / f"river_coast_{pref}.csv", index=False, encoding='utf-8-sig')
    mon_lf.to_csv(data_dir / f"landform_{pref}.csv", index=False, encoding='utf-8-sig')
    
    pt_main.to_csv(data_dir / f"points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_elev.to_csv(data_dir / f"elevation_points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_rc.to_csv(data_dir / f"river_coast_points_{pref}.csv", index=False, encoding='utf-8-sig')
    pt_lf.to_csv(data_dir / f"landform_points_{pref}.csv", index=False, encoding='utf-8-sig')
    
    with patch("sys.argv", ["make_map.py", "--pref", pref]):
        make_map.main()
        
    out_file = tmp_path / "output" / f"map_{pref}.html"
    assert out_file.exists()
    
    html_content = out_file.read_text(encoding='utf-8')
    assert '01' in html_content
    assert '02' in html_content
    assert '03' in html_content
    assert '04' in html_content
    
    assert '国土数値情報' in html_content
    assert '相関' in html_content
    
    # 凡例の件数の合計が4か
    assert '碑の数: 4' in html_content
    
    # 0基の種別名が凡例に出ない
    assert '高潮 0基' not in html_content
    assert '土砂災害 0基' not in html_content
    assert '津波 1基' in html_content
    assert '洪水 1基' in html_content
    assert '地震 1基' in html_content
    assert 'その他 1基' in html_content

def test_missing_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(make_map.PREFECTURES, '98', 'テスト県2')
    monkeypatch.setattr(make_map, "PROJECT_ROOT", tmp_path)
    from src import summarize
    monkeypatch.setattr(summarize, "PROJECT_ROOT", tmp_path)
    pref = '98'
    
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    with patch("sys.argv", ["make_map.py", "--pref", pref]):
        with pytest.raises(SystemExit):
            make_map.main()
            
    captured = capsys.readouterr()
    assert "ファイルが見つかりません" in captured.out
