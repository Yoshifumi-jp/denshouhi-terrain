import pytest
import pandas as pd

from src.add_elevation import (
    calc_delta_degrees,
    calculate_slope,
    get_elevation_with_cache,
    process_monuments,
    load_cache
)

def test_calc_delta_degrees():
    # d. 10m を緯度の差に直した値が約 0.0000899度（小数7桁で一致）であること
    # 赤道上でなくても緯度の差は一定のはず (地球を球としているため)
    lat_diff, _ = calc_delta_degrees(35.0, 135.0, 10)
    assert round(lat_diff, 7) == 0.0000899

def test_calculate_slope(tmp_path):
    cache_file = tmp_path / "cache.csv"
    cache_df = load_cache(cache_file)
    
    stats = {
        'api_calls': 0, 'cache_hits': 0, 'success': 0, 'error_nodata': 0, 'error_network': 0
    }
    
    def dummy_sleep(s):
        pass

    # a. 4地点が同じ標高 → 0.0度
    def mock_fetch_flat(lat, lon):
        return {"elevation": 10.0, "hsrc": "5m"}
    
    slope, _ = calculate_slope(35.0, 135.0, mock_fetch_flat, dummy_sleep, cache_df, cache_file, stats)
    assert slope == 0.0

    cache_file.unlink(missing_ok=True)
    cache_df = load_cache(cache_file)
    
    # b. 東が西より20m高く、南北は同じ → 45.0度
    def mock_fetch_east_high(lat, lon):
        delta_lat, delta_lon = calc_delta_degrees(35.0, 135.0, 10)
        if round(lon, 6) == round(135.0 + delta_lon, 6):
            return {"elevation": 30.0, "hsrc": "5m"} # East
        elif round(lon, 6) == round(135.0 - delta_lon, 6):
            return {"elevation": 10.0, "hsrc": "5m"} # West
        else:
            return {"elevation": 20.0, "hsrc": "5m"} # N, S (center not fetched here)
            
    slope, _ = calculate_slope(35.0, 135.0, mock_fetch_east_high, dummy_sleep, cache_df, cache_file, stats)
    assert slope == 45.0

    cache_file.unlink(missing_ok=True)
    cache_df = load_cache(cache_file)

    # c. 北が南より2m高く、東西は同じ（勾配10%） → 5.7度
    def mock_fetch_north_high(lat, lon):
        delta_lat, delta_lon = calc_delta_degrees(35.0, 135.0, 10)
        if round(lat, 6) == round(35.0 + delta_lat, 6):
            return {"elevation": 12.0, "hsrc": "5m"} # North
        elif round(lat, 6) == round(35.0 - delta_lat, 6):
            return {"elevation": 10.0, "hsrc": "5m"} # South
        else:
            return {"elevation": 11.0, "hsrc": "5m"} # E, W
            
    slope, _ = calculate_slope(35.0, 135.0, mock_fetch_north_high, dummy_sleep, cache_df, cache_file, stats)
    assert slope == 5.7


def test_api_result_parsing(tmp_path):
    # e. APIの戻り値の読み取り：数値のときは数値、"-----" のときは「データなし」と判定される
    cache_file = tmp_path / "cache.csv"
    cache_df = load_cache(cache_file)
    
    stats = {'api_calls': 0, 'cache_hits': 0}
    
    def dummy_sleep(s):
        pass

    def mock_fetch_num(lat, lon):
        return {"elevation": 1.5, "hsrc": "5m"}
        
    elev, hsrc, status = get_elevation_with_cache(35.0, 135.0, cache_df, cache_file, mock_fetch_num, dummy_sleep, stats)
    assert elev == 1.5
    assert status == "OK"
    
    def mock_fetch_nodata(lat, lon):
        return {"elevation": "-----", "hsrc": "-----"}
        
    elev, hsrc, status = get_elevation_with_cache(36.0, 136.0, cache_df, cache_file, mock_fetch_nodata, dummy_sleep, stats)
    assert elev == "-----"
    assert status == "OK"


def test_cache_reused(tmp_path, capsys):
    # f. キャッシュ：2基分を処理したあと同じ内容で再実行すると、問い合わせ回数が0回になる
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'},
        {'ID': '00000-002', '碑名': 'B', '緯度': '36.0', '経度': '136.0'}
    ])
    
    call_count = 0
    def mock_fetch(lat, lon):
        nonlocal call_count
        call_count += 1
        return {"elevation": 10.0, "hsrc": "5m"}
        
    def dummy_sleep(s):
        pass
        
    # 1回目の実行
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch, sleep_fn=dummy_sleep)
    
    # 2基 x 5地点(中心+東西南北) = 10回の呼び出し
    assert call_count == 10
    
    # 2回目の実行
    call_count = 0
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch, sleep_fn=dummy_sleep)
    
    # 再実行時は0回になる
    assert call_count == 0
    res_df = pd.read_csv(out_file)
    assert len(res_df) == 2


def test_resume(tmp_path):
    # g. 再開：偽物の問い合わせ関数を途中（例：3回目）でKeyboardInterruptを出すようにして止め、
    # その後正常な関数で再実行すると、中断・再開が正しく行われることを確かめる
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'},
        {'ID': '00000-002', '碑名': 'B', '緯度': '36.0', '経度': '136.0'}
    ])
    
    call_count_1 = 0
    def mock_fetch_interrupt(lat, lon):
        nonlocal call_count_1
        call_count_1 += 1
        if call_count_1 == 3: # 3回目で中断
            raise KeyboardInterrupt()
        return {"elevation": 10.0, "hsrc": "5m"}
        
    def dummy_sleep(s):
        pass
        
    # 1回目の実行 (3回目で中断)
    with pytest.raises(SystemExit):
        process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch_interrupt, sleep_fn=dummy_sleep)
    
    # 2回目の実行 (正常)
    call_count_2 = 0
    def mock_fetch_success(lat, lon):
        nonlocal call_count_2
        call_count_2 += 1
        return {"elevation": 10.0, "hsrc": "5m"}
        
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch_success, sleep_fn=dummy_sleep)
    
    # 2回目の問い合わせ回数は 10 - 2 = 8回
    assert call_count_2 == 8
    
    # キャッシュの行数は10
    cache_df = pd.read_csv(cache_dir / "elevation_cache.csv")
    assert len(cache_df) == 10
    
    # 結果が全件(2件)そろい、かつ両方とも「取得済」になっているか確認
    res_df = pd.read_csv(out_file)
    assert len(res_df) == 2
    assert (res_df['取得状態'] == '取得済').all()


def test_missing_point_nodata(tmp_path):
    # h. 4地点のうち1つが「データなし」のとき、標高は記録され、傾斜は空欄・取得状態は「取得済」ではなくなる
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'}
    ])
    
    def mock_fetch(lat, lon):
        # 北の地点だけデータなし
        delta_lat, _ = calc_delta_degrees(35.0, 135.0, 10)
        if round(lat, 6) == round(35.0 + delta_lat, 6):
            return {"elevation": "-----", "hsrc": "-----"}
        return {"elevation": 10.0, "hsrc": "5m"}
        
    def dummy_sleep(s):
        pass
        
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch, sleep_fn=dummy_sleep)
    res_df = pd.read_csv(out_file)
    assert len(res_df) == 1
    row = res_df.iloc[0]
    
    assert row['標高_m'] == 10.0
    assert pd.isna(row['傾斜_度'])
    assert row['取得状態'] == '取得不可（データなし）'

def test_missing_point_network_error(tmp_path):
    # 4. テストを1件追加する：周囲の1地点だけが3回とも通信エラーになる偽物の関数で実行する
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'}
    ])
    
    def mock_fetch_fail(lat, lon):
        # 西の地点だけ通信エラー
        _, delta_lon = calc_delta_degrees(35.0, 135.0, 10)
        if round(lon, 6) == round(135.0 - delta_lon, 6):
            raise Exception("Network Error")
        return {"elevation": 10.0, "hsrc": "5m"}
        
    def dummy_sleep(s):
        pass
        
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch_fail, sleep_fn=dummy_sleep)
    res_df = pd.read_csv(out_file)
    assert len(res_df) == 1
    row = res_df.iloc[0]
    
    assert row['標高_m'] == 10.0
    assert pd.isna(row['傾斜_度'])
    assert row['取得状態'] == '取得不可（通信エラー）'
    
    # 失敗した地点はキャッシュに保存されないことを確認 (中心、南、東、西 の4地点が保存されている)
    cache_file = cache_dir / "elevation_cache.csv"
    cache_df = pd.read_csv(cache_file)
    assert len(cache_df) == 4
    
    # 正常な関数で再実行すると「取得済」になる
    def mock_fetch_success(lat, lon):
        return {"elevation": 10.0, "hsrc": "5m"}
        
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch_success, sleep_fn=dummy_sleep)
    
    res_df_2 = pd.read_csv(out_file)
    assert len(res_df_2) == 1
    assert res_df_2.iloc[0]['取得状態'] == '取得済'

def test_no_cache_initial_run(tmp_path):
    # a. キャッシュファイルがない状態で1基を処理すると、問い合わせ5回で「取得済」になる（初回実行の確認）
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'}
    ])
    
    call_count = 0
    def mock_fetch(lat, lon):
        nonlocal call_count
        call_count += 1
        return {"elevation": 10.0, "hsrc": "5m"}
        
    def dummy_sleep(s):
        pass
        
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch, sleep_fn=dummy_sleep)
    
    assert call_count == 5
    res_df = pd.read_csv(out_file)
    assert res_df.iloc[0]['取得状態'] == '取得済'


def test_cache_with_nodata(tmp_path):
    # b. 「-----」（データなし）を含むキャッシュを読み込んでも、数値の地点は数値として正しく使われる
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    # 意図的に "-----" を含むキャッシュを作成
    cache_file = cache_dir / "elevation_cache.csv"
    with open(cache_file, "w", encoding="utf-8-sig") as f:
        f.write("緯度,経度,標高,標高データ種別,取得日時\n")
        f.write("35.0,135.0,10.0,5m,2026-09-28 10:00:00\n")
        f.write("35.1,135.0,-----,-----,2026-09-28 10:00:00\n")
    
    # dfに両方の地点を登録
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'},
        {'ID': '00000-002', '碑名': 'B', '緯度': '35.1', '経度': '135.0'}
    ])
    
    call_count = 0
    def mock_fetch(lat, lon):
        nonlocal call_count
        call_count += 1
        return {"elevation": 10.0, "hsrc": "5m"}
        
    def dummy_sleep(s):
        pass
        
    process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch, sleep_fn=dummy_sleep)
    res_df = pd.read_csv(out_file)
    
    row_a = res_df[res_df['ID'] == '00000-001'].iloc[0]
    assert row_a['標高_m'] == 10.0
    
    row_b = res_df[res_df['ID'] == '00000-002'].iloc[0]
    assert pd.isna(row_b['標高_m'])
    assert row_b['取得状態'] == '取得不可（データなし）'


def test_corrupt_cache(tmp_path, capsys):
    # c. 壊れたキャッシュファイル（例：中身が1行のでたらめな文字）を置いて実行すると、処理が止まる
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    cache_file = cache_dir / "elevation_cache.csv"
    with open(cache_file, "w", encoding="utf-8-sig") as f:
        f.write("this is some random corrupt string without enough columns\n")
        f.write("and this makes it unparseable when dtype is enforced\n")
        
    df = pd.DataFrame([
        {'ID': '00000-001', '碑名': 'A', '緯度': '35.0', '経度': '135.0'}
    ])
    
    def dummy_sleep(s): pass
    def mock_fetch(lat, lon): return {"elevation": 10.0, "hsrc": "5m"}
    
    with pytest.raises(SystemExit):
        process_monuments(df, "00", cache_dir, out_file, fetch_func=mock_fetch, sleep_fn=dummy_sleep)
        
    captured = capsys.readouterr()
    assert "警告: キャッシュファイル" in captured.out
    assert "を読めません。ファイルを確認してください。" in captured.out

def test_cache_dtype_after_append(tmp_path):
    # 2. テストを1件追加する：空のキャッシュから2地点を取得したあと、キャッシュの「緯度」「経度」の列が数値型であることを確かめる。
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    out_file = out_dir / "elevation_00.csv"
    
    def dummy_sleep(s): pass
    def mock_fetch(lat, lon): return {"elevation": 10.0, "hsrc": "5m"}
    
    # process_monuments は内部で cache_df を持っているが、出力後のファイルで型を確認する
    # あるいはモックなどで get_elevation_with_cache に渡される cache_df を確認する？
    # テストの意図は「1行追加したあとも緯度・経度が float のままになる」なので、
    # 実際には process_monuments 実行中にエラーにならなければOK。
    # しかし「数値型であることを確かめる」とあるので、
    # get_elevation_with_cache を直接呼んでキャッシュの状態を確認する。
    
    from src.add_elevation import load_cache
    cache_file = cache_dir / "elevation_cache.csv"
    cache_df = load_cache(cache_file)
    stats = {'api_calls': 0, 'cache_hits': 0}
    
    # 1地点目
    get_elevation_with_cache(35.0, 135.0, cache_df, cache_file, mock_fetch, dummy_sleep, stats)
    # 2地点目
    get_elevation_with_cache(36.0, 136.0, cache_df, cache_file, mock_fetch, dummy_sleep, stats)
    
    # 緯度と経度が数値型であることを確認
    assert pd.api.types.is_numeric_dtype(cache_df['緯度'])
    assert pd.api.types.is_numeric_dtype(cache_df['経度'])
    assert len(cache_df) == 2
