import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from pathlib import Path
import math

from src.add_river_coast import (
    calc_distance_and_nearest, process_river_coast, read_line_shapefile,
    make_bank_points, choose_bank_elevation
)

def test_calc_distance_and_nearest_a():
    # a. 平面座標（m）で、線 (0,100)-(100,100) と点 (50,0) → 距離 100m、最近点 (50,100)
    line = LineString([(0, 100), (100, 100)])
    lines_gdf = gpd.GeoDataFrame(geometry=[line])
    point = Point(50, 0)
    
    row, dist, nearest_pt = calc_distance_and_nearest(point, lines_gdf)
    assert dist == 100.0
    assert nearest_pt.x == 50.0
    assert nearest_pt.y == 100.0

def test_calc_distance_and_nearest_b():
    # b. 同じ線と点 (150,0)（線の端より外側）→ 距離 111.8m（小数1桁）、最近点 (100,100)
    line = LineString([(0, 100), (100, 100)])
    lines_gdf = gpd.GeoDataFrame(geometry=[line])
    point = Point(150, 0)
    
    row, dist, nearest_pt = calc_distance_and_nearest(point, lines_gdf)
    assert round(dist, 1) == 111.8
    assert nearest_pt.x == 100.0
    assert nearest_pt.y == 100.0

def test_calc_distance_and_nearest_c():
    # c. 河川が3本あるとき、最も近い河川の河川名・河川コードが選ばれる
    line1 = LineString([(0, 100), (100, 100)]) # dist: 100
    line2 = LineString([(0, 50), (100, 50)])   # dist: 50
    line3 = LineString([(0, 200), (100, 200)]) # dist: 200
    
    lines_gdf = gpd.GeoDataFrame(
        {'W05_004': ['River1', 'River2', 'River3'], 'W05_002': ['001', '002', '003']},
        geometry=[line1, line2, line3]
    )
    point = Point(50, 0)
    
    row, dist, nearest_pt = calc_distance_and_nearest(point, lines_gdf)
    assert row['W05_004'] == 'River2'
    assert row['W05_002'] == '002'

def test_crs_conversion():
    # d. 座標変換：緯度34.0の同じ緯線上で、経度134.50と134.51の2点の距離が EPSG:6672 で 923.8m（±1m以内）
    pt1 = Point(134.50, 34.0)
    pt2 = Point(134.51, 34.0)
    
    gdf = gpd.GeoDataFrame(geometry=[pt1, pt2], crs="EPSG:6668")
    gdf_6672 = gdf.to_crs("EPSG:6672")
    
    dist = gdf_6672.geometry.iloc[0].distance(gdf_6672.geometry.iloc[1])
    assert abs(dist - 923.8) <= 1.0

def test_make_bank_points():
    # a. make_bank_points：P(0,0)・M(0,100)・距離100 → P と (0,5)(0,10)(0,20)(0,30)(0,50) の6点（100 は含まない）
    pts = make_bank_points(Point(0, 0), Point(0, 100), 100, [5, 10, 20, 30, 50, 100])
    assert len(pts) == 6
    assert pts[0][0] == 0
    assert pts[1][0] == 5
    assert pts[5][0] == 50
    assert pts[5][1].y == 50.0

    # b. make_bank_points：P(0,0)・M(0,8)・距離8 → P と (0,5) の2点
    pts = make_bank_points(Point(0, 0), Point(0, 8), 8, [5, 10, 20, 30, 50, 100])
    assert len(pts) == 2
    assert pts[0][0] == 0
    assert pts[1][0] == 5
    assert pts[1][1].y == 5.0

def test_choose_bank_elevation():
    # c. choose_bank_elevation：P＝6.0（10m）、5m先＝3.2（1m（レーザ））、10m先＝2.9（5m（レーザ））→ 2.9 を採用・「取得済」・種別「5m（レーザ）」
    results = [
        (0, 6.0, "10m", "取得済", 34.0, 134.0),
        (5, 3.2, "1m（レーザ）", "取得済", 34.0001, 134.0),
        (10, 2.9, "5m（レーザ）", "取得済", 34.0002, 134.0)
    ]
    elev, hsrc, lat, lon, status = choose_bank_elevation(results)
    assert elev == 2.9
    assert hsrc == "5m（レーザ）"
    assert status == "取得済"

    # d. choose_bank_elevation：P＝6.0（10m）、他はすべて "-----" → 6.0 を採用・「取得済（参考値：10mメッシュ）」
    results = [
        (0, 6.0, "10m", "取得済", 34.0, 134.0),
        (5, "-----", "", "取得済", 34.0001, 134.0),
        (10, "-----", "", "取得済", 34.0002, 134.0)
    ]
    elev, hsrc, lat, lon, status = choose_bank_elevation(results)
    assert elev == 6.0
    assert status == "取得済（参考値：10mメッシュ）"

    # e. choose_bank_elevation：すべて "-----" → 空欄・「高さの差 取得不可（河川の標高なし）」
    results = [
        (0, "-----", "", "取得済", 34.0, 134.0),
        (5, "-----", "", "取得済", 34.0001, 134.0)
    ]
    elev, hsrc, lat, lon, status = choose_bank_elevation(results)
    assert elev is None
    assert status == "高さの差 取得不可（河川の標高なし）"

    # f. choose_bank_elevation：精しい値があっても、1つが「通信エラー」→「高さの差 取得不可（通信エラー）」
    results = [
        (0, 6.0, "10m", "取得済", 34.0, 134.0),
        (5, 3.2, "1m（レーザ）", "通信エラー", 34.0001, 134.0)
    ]
    elev, hsrc, lat, lon, status = choose_bank_elevation(results)
    assert elev is None
    assert status == "高さの差 取得不可（通信エラー）"

    # g. (追加b) 0, 5, 10, 20, 30 が 10m メッシュ、50m=3.1(1m)、100m=2.4(1m) → 3.1 採用
    results_b = [
        (0, 8.0, "10m", "取得済", 34.0, 134.0),
        (5, 8.0, "10m", "取得済", 34.0, 134.0),
        (10, 8.0, "10m", "取得済", 34.0, 134.0),
        (20, 8.0, "10m", "取得済", 34.0, 134.0),
        (30, 7.0, "10m", "取得済", 34.0, 134.0),
        (50, 3.1, "1m（レーザ）", "取得済", 34.0, 134.0),
        (100, 2.4, "1m（レーザ）", "取得済", 34.0, 134.0),
    ]
    elev, _, _, _, status = choose_bank_elevation(results_b, window_m=20)
    assert elev == 3.1
    assert status == "取得済"

    # h. (追加c) 5m=3.0, 20m=2.5, 30m=2.0 (1m), 0m="-----" → 2.5 採用
    results_c = [
        (0, "-----", "", "取得済", 34.0, 134.0),
        (5, 3.0, "1m（レーザ）", "取得済", 34.0, 134.0),
        (20, 2.5, "1m（レーザ）", "取得済", 34.0, 134.0),
        (30, 2.0, "1m（レーザ）", "取得済", 34.0, 134.0),
    ]
    elev, _, _, _, status = choose_bank_elevation(results_c, window_m=20)
    assert elev == 2.5
    assert status == "取得済"

    # i. (追加d) results の順番を逆にしても b と同じ結果になる
    results_d = list(reversed(results_b))
    elev, _, _, _, status = choose_bank_elevation(results_d, window_m=20)
    assert elev == 3.1
    assert status == "取得済"

@pytest.mark.parametrize("case_no, mon_elev, fetch_res, expected_diff, expected_status", [
    (1, 10.0, {"elevation": 3.5, "hsrc": "5m（レーザ）"}, 6.5, '取得済'),
    (2, 2.0, {"elevation": 5.0, "hsrc": "5m（レーザ）"}, -3.0, '取得済'),
    (3, float('nan'), {"elevation": 3.5, "hsrc": "5m（レーザ）"}, None, '高さの差 取得不可（碑の標高なし）'),
    (4, 10.0, {"elevation": "-----", "hsrc": ""}, None, '高さの差 取得不可（河川の標高なし）'),
    (5, 10.0, Exception("Network error"), None, '高さの差 取得不可（通信エラー）'),
    (6, 10.0, {"elevation": 3.5, "hsrc": "10m"}, 6.5, '取得済（参考値：10mメッシュ）')
])
def test_height_diff(tmp_path, case_no, mon_elev, fetch_res, expected_diff, expected_status):
    # e. 高さの差：5つの場合をテストする
    cache_dir = tmp_path / f"cache_{case_no}"
    cache_dir.mkdir()
    out_dir = tmp_path / f"out_{case_no}"
    out_dir.mkdir()
    out_file = out_dir / "river_coast_36.csv"
    
    mon_df = pd.DataFrame([
        {'ID': '001', '碑名': 'A', '緯度': '34.0', '経度': '134.50'}
    ])
    
    elev_df = pd.DataFrame([
        {'ID': '001', '標高_m': mon_elev}
    ])
    
    rivers_dir = tmp_path / f"rivers_{case_no}"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers.shp"
    
    line = LineString([(134.50, 34.005), (134.51, 34.005)])
    rivers_gdf = gpd.GeoDataFrame(
        {'W05_004': ['TestRiver'], 'W05_002': ['123']},
        geometry=[line],
        crs="EPSG:4612"
    )
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    def mock_fetch(lat, lon):
        if isinstance(fetch_res, Exception):
            raise fetch_res
        return fetch_res
        
    def dummy_sleep(s): pass
    
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, dummy_sleep)
    res_df = pd.read_csv(out_file, dtype={'ID': str})
    
    row = res_df.iloc[0]
    
    if expected_diff is None:
        assert pd.isna(row['河川との高さの差_m'])
    else:
        assert row['河川との高さの差_m'] == expected_diff
        
    assert row['河川_状態'] == expected_status
    
    if case_no in (1, 2, 6):
        expected_elev = fetch_res["elevation"]
        assert row['河川側の標高_m'] == expected_elev
        assert row['河川側の標高_種別'] == fetch_res["hsrc"]
        
    if case_no in (4, 5):
        assert pd.isna(row['河川側の標高_m'])
    
def test_encoding_and_crs(tmp_path):
    # f. 文字コード：河川名「吉野川」を持つ小さなシェープファイルを cp932 で tmp_path に作り、.cpg と .prj を削除してから読み込んで「吉野川」と正しく読め、座標系が EPSG:4612 になっている
    rivers_dir = tmp_path / "rivers"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers_enc.shp"
    
    line = LineString([(134.50, 34.005), (134.51, 34.005)])
    rivers_gdf = gpd.GeoDataFrame(
        {'W05_004': ['吉野川'], 'W05_002': ['123']},
        geometry=[line],
        crs="EPSG:4612"
    )
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    # .cpg と .prj を削除
    cpg_file = rivers_dir / "test_rivers_enc.cpg"
    prj_file = rivers_dir / "test_rivers_enc.prj"
    if cpg_file.exists():
        cpg_file.unlink()
    if prj_file.exists():
        prj_file.unlink()
        
    # main 側の読み込み処理をシミュレート
    gdf_read = read_line_shapefile(rivers_shp)
    
    assert gdf_read.iloc[0]['W05_004'] == '吉野川'
    assert gdf_read.crs.to_string() == "EPSG:4612"

def test_no_coastline(tmp_path, capsys):
    # g. 海岸線ファイルがないとき：全件の海岸_状態が「データなし」、海岸までの距離が空欄になり、処理は止まらない
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "river_coast_36.csv"
    
    mon_df = pd.DataFrame([{'ID': '001', '碑名': 'A', '緯度': '34.0', '経度': '134.50'}])
    elev_df = pd.DataFrame([{'ID': '001', '標高_m': 10.0}])
    
    rivers_dir = tmp_path / "rivers"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers.shp"
    
    line = LineString([(134.50, 34.005), (134.51, 34.005)])
    rivers_gdf = gpd.GeoDataFrame({'W05_004': ['TestRiver'], 'W05_002': ['123']}, geometry=[line], crs="EPSG:4612")
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    def mock_fetch(lat, lon): return {"elevation": 3.5, "hsrc": "5m"}
    def dummy_sleep(s): pass
    
    # coast_shp = None で実行
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, dummy_sleep)
    res_df = pd.read_csv(out_file, dtype={'ID': str})
    row = res_df.iloc[0]
    
    assert row['海岸_状態'] == 'データなし'
    assert pd.isna(row['海岸までの距離_m'])

def test_cache_reuse(tmp_path):
    # h. キャッシュ：2基分を処理したあと同じ内容で再実行すると、問い合わせ回数が0回になる
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "river_coast_36.csv"
    
    mon_df = pd.DataFrame([
        {'ID': '001', '碑名': 'A', '緯度': '34.0', '経度': '134.50'},
        {'ID': '002', '碑名': 'B', '緯度': '34.001', '経度': '134.50'}
    ])
    elev_df = pd.DataFrame([
        {'ID': '001', '標高_m': 10.0},
        {'ID': '002', '標高_m': 20.0}
    ])
    
    rivers_dir = tmp_path / "rivers"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers.shp"
    
    line = LineString([(134.50, 34.005), (134.51, 34.005)])
    rivers_gdf = gpd.GeoDataFrame({'W05_004': ['TestRiver'], 'W05_002': ['123']}, geometry=[line], crs="EPSG:4612")
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    call_count = 0
    def mock_fetch(lat, lon):
        nonlocal call_count
        call_count += 1
        return {"elevation": 3.5, "hsrc": "5m"}
    def dummy_sleep(s): pass
    
    # 1回目
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, dummy_sleep)
    assert call_count > 0 # 最低1回は呼ばれる (地点数による)
    
    # 2回目
    call_count = 0
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, dummy_sleep)
    assert call_count == 0 # キャッシュから取得するので0回

def test_out_of_range(tmp_path):
    # g. 河川までの距離が 1200m の碑
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "river_coast_36.csv"
    
    mon_df = pd.DataFrame([
        {'ID': '001', '碑名': 'A', '緯度': '34.0', '経度': '134.50'}
    ])
    elev_df = pd.DataFrame([
        {'ID': '001', '標高_m': 10.0}
    ])
    rivers_dir = tmp_path / "rivers"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers.shp"
    
    line = LineString([(134.520, 34.0), (134.530, 34.0)])
    rivers_gdf = gpd.GeoDataFrame(
        {'W05_004': ['TestRiver'], 'W05_002': ['123']},
        geometry=[line],
        crs="EPSG:4612"
    )
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    call_count = 0
    def mock_fetch(lat, lon):
        nonlocal call_count
        call_count += 1
        return {"elevation": 3.5, "hsrc": "5m"}
        
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, lambda s: None)
    res_df = pd.read_csv(out_file, dtype={'ID': str})
    row = res_df.iloc[0]
    
    assert row['河川_状態'] == '高さの差 対象外（河川まで1000m超）'
    assert pd.isna(row['河川との高さの差_m'])
    assert call_count == 0
    assert row['最寄り河川名'] == 'TestRiver'
    assert row['河川までの距離_m'] > 1000
    assert not pd.isna(row['河川最近点_緯度'])
    assert not pd.isna(row['河川最近点_経度'])

def test_named_river(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "river_coast_36.csv"
    
    mon_df = pd.DataFrame([
        {'ID': '001', '碑名': 'A', '緯度': '34.0', '経度': '134.50'},
        {'ID': '002', '碑名': 'B', '緯度': '34.003', '経度': '134.50'}
    ])
    elev_df = pd.DataFrame([
        {'ID': '001', '標高_m': 10.0},
        {'ID': '002', '標高_m': 10.0}
    ])
    
    rivers_dir = tmp_path / "rivers"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers.shp"
    
    # 50m=約0.00045度, 300m=約0.00270度
    line1 = LineString([(134.49, 34.00045), (134.51, 34.00045)])
    line2 = LineString([(134.49, 34.00270), (134.51, 34.00270)])
    
    rivers_gdf = gpd.GeoDataFrame(
        {'W05_004': ['名称不明', 'テスト川'], 'W05_002': ['000', '123']},
        geometry=[line1, line2],
        crs="EPSG:4612"
    )
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    def mock_fetch(lat, lon):
        return {"elevation": 3.5, "hsrc": "5m"}
        
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, lambda s: None)
    res_df = pd.read_csv(out_file, dtype={'ID': str, '河川コード': str, '名前のある最寄り河川コード': str})
    
    # a. 碑から 50m に「名称不明」、300m に「テスト川」
    row_001 = res_df[res_df['ID'] == '001'].iloc[0]
    assert row_001['最寄り河川名'] == '名称不明'
    assert row_001['名前のある最寄り河川名'] == 'テスト川'
    assert str(row_001['名前のある最寄り河川コード']).replace('.0', '') == '123'
    assert 295 <= row_001['名前のある河川までの距離_m'] <= 305
    
    # b. 最寄りが名前のある川のとき
    row_002 = res_df[res_df['ID'] == '002'].iloc[0]
    assert row_002['最寄り河川名'] == 'テスト川'
    assert row_002['名前のある最寄り河川名'] == 'テスト川'
    assert str(row_002['名前のある最寄り河川コード']).replace('.0', '') == '123'
    assert row_002['河川までの距離_m'] == row_002['名前のある河川までの距離_m']

def test_only_unknown_river(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "river_coast_36.csv"
    
    mon_df = pd.DataFrame([{'ID': '001', '碑名': 'A', '緯度': '34.0', '経度': '134.50'}])
    elev_df = pd.DataFrame([{'ID': '001', '標高_m': 10.0}])
    
    rivers_dir = tmp_path / "rivers"
    rivers_dir.mkdir()
    rivers_shp = rivers_dir / "test_rivers.shp"
    
    line = LineString([(134.49, 34.00045), (134.51, 34.00045)])
    rivers_gdf = gpd.GeoDataFrame(
        {'W05_004': ['名称不明'], 'W05_002': ['000']},
        geometry=[line],
        crs="EPSG:4612"
    )
    rivers_gdf.to_file(rivers_shp, encoding="cp932")
    
    def mock_fetch(lat, lon):
        return {"elevation": 3.5, "hsrc": "5m"}
        
    process_river_coast("36", mon_df, elev_df, rivers_shp, None, 6672, cache_dir, out_file, mock_fetch, lambda s: None)
    res_df = pd.read_csv(out_file, dtype={'ID': str, '河川コード': str, '名前のある最寄り河川コード': str})
    
    row = res_df.iloc[0]
    assert row['最寄り河川名'] == '名称不明'
    assert pd.isna(row['名前のある最寄り河川名'])
    assert pd.isna(row['名前のある最寄り河川コード'])
    assert pd.isna(row['名前のある河川までの距離_m'])
