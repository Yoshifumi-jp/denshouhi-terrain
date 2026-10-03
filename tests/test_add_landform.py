import os
import json
import gzip
from datetime import datetime
import pytest

from src.add_landform import lonlat_to_tile, process_monuments, default_fetch_func
from src.landform_codes import LANDFORM_CODES, _RAW_MAPPING

def test_lonlat_to_tile():
    # a. タイル番号：緯度 34.066366・経度 134.584699・z=16 → (57268, 26164)
    x, y = lonlat_to_tile(134.584699, 34.066366, 16)
    assert (x, y) == (57268, 26164)

def test_no_duplicate_codes_in_mapping():
    # j. 対応表の code に重複がない（1つの code が2つの名前に入っていない）
    seen_codes = {}
    for name, codes in _RAW_MAPPING.items():
        for code in codes:
            assert code not in seen_codes, f"Duplicate code {code} found in {name} and {seen_codes[code]}"
            seen_codes[code] = name
    
    assert len(seen_codes) == len(LANDFORM_CODES)

def test_process_monuments(tmp_path):
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"
    
    input_csv.write_text(
        "ID,碑名,緯度,経度\n"
        "01,内側,34.0,134.0\n"        # (x, y) = (57161, 26179) -> code 3030101 (氾濫平野・海岸平野)
        "02,外側,34.01,134.0\n"       # (x, y) = (57161, 26177) -> データなし
        "03,404,34.02,134.0\n"        # (x, y) = (57161, 26175) -> 404
        "04,通信エラー,34.03,134.0\n"    # (x, y) = (57161, 26172) -> HTTP Error
        "05,同タイル1,34.04,134.0\n"     # (x, y) = (57161, 26170) -> code 5010301 (旧水部)
        "06,同タイル2,34.04,134.0\n"     # 同一タイル
        "07,境界上,34.05,134.0\n"       # (x, y) = (57161, 26168) -> 境界上 (covers)
        "08,不明コード,34.06,134.0\n"    # (x, y) = (57161, 26166) -> code 9999999
        "09,エラー2,34.07,134.0\n"       # (x, y) = (57161, 26164) -> HTTP Error
        , encoding="utf-8-sig"
    )

    fetch_calls = []

    def mock_fetch(x, y):
        fetch_calls.append((x, y))
        # 01: 内側
        if (x, y) == (57161, 26179):
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"code": 3030101}, # 氾濫平野・海岸平野
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[133.9, 33.9], [134.1, 33.9], [134.1, 34.1], [133.9, 34.1], [133.9, 33.9]]]
                    }
                }]
            }
        # 02: 外側 (ポリゴンはあるが点を含まない)
        elif (x, y) == (57161, 26177):
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"code": 3030101},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[135.0, 35.0], [135.1, 35.0], [135.1, 35.1], [135.0, 35.1], [135.0, 35.0]]]
                    }
                }]
            }
        # 03: 404
        elif (x, y) == (57161, 26175):
            return None
        # 04: 通信エラー
        elif (x, y) == (57161, 26172):
            raise Exception("Network Error")
        # 05/06: 同タイル
        elif (x, y) == (57161, 26170):
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"code": 5010301}, # 旧水部
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[133.9, 34.0], [134.1, 34.0], [134.1, 34.1], [133.9, 34.1], [133.9, 34.0]]]
                    }
                }]
            }
        # 07: 境界線上
        elif (x, y) == (57161, 26168):
            # 点が (134.0, 34.05) なので、ポリゴンのエッジを 134.0 にする
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"code": 10101}, # 山地斜面等
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[133.9, 34.0], [134.0, 34.0], [134.0, 34.1], [133.9, 34.1], [133.9, 34.0]]]
                    }
                }]
            }
        # 08: 不明コード
        elif (x, y) == (57161, 26166):
            return {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"code": 9999999}, # 不明コード
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[133.9, 34.0], [134.1, 34.0], [134.1, 34.1], [133.9, 34.1], [133.9, 34.0]]]
                    }
                }]
            }
        # 09: エラー2
        elif (x, y) == (57161, 26164):
            raise Exception("Network Error 2")
        return {"type": "FeatureCollection", "features": []}

    sleep_calls = [0]
    def mock_sleep():
        sleep_calls[0] += 1
    
    cache_dir = tmp_path / "cache"
    
    process_monuments(str(input_csv), str(output_csv), str(cache_dir), mock_fetch, mock_sleep)
    
    # Check results
    lines = output_csv.read_text(encoding="utf-8-sig").splitlines()
    assert len(lines) == 10 # ヘッダ + 9件
    
    # 01: 内側
    assert "01,内側,34.0,134.0,氾濫平野・海岸平野,3030101,1,取得済" in lines[1]
    # 02: 外側 (c)
    assert "02,外側,34.01,134.0,,,0,データなし" in lines[2]
    # 03: 404 (d)
    assert "03,404,34.02,134.0,,,0,データなし" in lines[3]
    # 04: 通信エラー (e)
    assert "04,通信エラー,34.03,134.0,,,0,取得不可" in lines[4]
    # 05: 同タイル1 (i)
    assert "05,同タイル1,34.04,134.0,旧水部,5010301,1,取得済" in lines[5]
    # 06: 同タイル2
    assert "06,同タイル2,34.04,134.0,旧水部,5010301,1,取得済" in lines[6]
    # 07: 境界上 (g)
    assert "07,境界上,34.05,134.0,山地斜面等,10101,1,取得済" in lines[7]
    # 08: 不明コード (i)
    assert "08,不明コード,34.06,134.0,不明（code=9999999）,9999999,1,取得済" in lines[8]
    # 09: エラー2
    assert "09,エラー2,34.07,134.0,,,0,取得不可" in lines[9]

    # l. 通信エラーのタイルが2つあるとき、sleep_fn が2回呼ばれる（通信エラーに限らず全取得につき1回）
    # 全取得は8回 (01, 02, 03, 04(err), 05, 07, 08, 09(err))
    assert sleep_calls[0] == 8
    
    # f. 同じタイルの碑が2基 → 取得関数の呼び出しは1回
    assert fetch_calls.count((57161, 26170)) == 1
    
    # d. 404 → キャッシュファイルができる、2回目の実行で取得関数が呼ばれない
    # 2回目を実行
    fetch_calls.clear()
    process_monuments(str(input_csv), str(output_csv), str(cache_dir), mock_fetch, mock_sleep)
    
    # 404の(57161, 26175) はキャッシュから読まれるのでフェッチされない
    # 取得不可の(57161, 26172) はキャッシュされないのでフェッチされる
    assert (57161, 26175) not in fetch_calls
    assert (57161, 26172) in fetch_calls
    
    # e. 通信エラー → キャッシュファイルができない
    assert not os.path.exists(f"{cache_dir}/57161/26172.geojson")
    assert os.path.exists(f"{cache_dir}/57161/26175.geojson")

def test_gzip_response():
    # h. gzip 圧縮のバイト列が返る → 展開して正しく読める
    class MockResponse:
        def __init__(self, data):
            self._data = data
        def read(self):
            return self._data
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    import urllib.request
    original_urlopen = urllib.request.urlopen

    def mock_urlopen(req, timeout=10):
        # gzip 圧縮した GeoJSON を返す
        raw_json = b'{"type": "FeatureCollection", "features": []}'
        compressed = gzip.compress(raw_json)
        return MockResponse(compressed)

    try:
        urllib.request.urlopen = mock_urlopen
        data = default_fetch_func(0, 0)
        assert data == {"type": "FeatureCollection", "features": []}
    finally:
        urllib.request.urlopen = original_urlopen

def test_pref_validation(monkeypatch):
    from src.add_landform import main
    import sys
    
    # "99" should fail
    monkeypatch.setattr(sys, "argv", ["add_landform.py", "--pref", "99"])
    with pytest.raises(SystemExit) as e:
        main()
    assert e.value.code == 1
    
    # "all" should fail
    monkeypatch.setattr(sys, "argv", ["add_landform.py", "--pref", "all"])
    with pytest.raises(SystemExit) as e2:
        main()
    assert e2.value.code == 1

def test_cache_untouched(tmp_path):
    # k. テスト実行の前後で、本物のキャッシュフォルダの中身（ファイル名の一覧）が変わらない
    from pathlib import Path
    from src.add_landform import PROJECT_ROOT
    
    real_cache_dir = PROJECT_ROOT / "data" / "cache" / "landform" / "16"
    
    def get_all_files(d):
        if not d.exists():
            return set()
        return {str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()}
        
    before_files = get_all_files(real_cache_dir)
    
    # Run the test
    test_process_monuments(tmp_path)
    
    after_files = get_all_files(real_cache_dir)
    assert before_files == after_files
