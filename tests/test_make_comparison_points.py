import os
import csv
import math
import pytest
from pathlib import Path

from src.make_comparison_points import process_points

def calc_haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def setup_mock_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["ID", "碑名", "緯度", "経度", "県コード", "災害種別", "種別_洪水", "種別_土砂災害", "種別_津波", "種別_火山災害", "種別_地震", "種別_高潮", "種別_その他"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def mock_sleep_fn(*args):
    pass

@pytest.fixture
def basic_rows():
    return [{"ID": "36-01", "碑名": "Test1", "緯度": 34.0, "経度": 134.0, "県コード": "36", "災害種別": "津波", "種別_洪水": "0", "種別_土砂災害": "0", "種別_津波": "1", "種別_火山災害": "0", "種別_地震": "0", "種別_高潮": "0", "種別_その他": "0"}]

def fetch_mock_success(lat, lon):
    return {"elevation": 10.0, "hsrc": "DEM5A"}


def test_a_same_seed(tmp_path):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    rows = [{"ID": "36-01", "碑名": "Test1", "緯度": 34.0, "経度": 134.0, "県コード": "36", "災害種別": "津波", "種別_洪水": "0", "種別_土砂災害": "0", "種別_津波": "1", "種別_火山災害": "0", "種別_地震": "0", "種別_高潮": "0", "種別_その他": "0"}]
    setup_mock_csv(input_csv, rows)
    
    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    content1 = output_csv.read_text(encoding="utf-8-sig")
    
    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    content2 = output_csv.read_text(encoding="utf-8-sig")
    
    assert content1 == content2

def test_b_different_seed(tmp_path):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    rows = [{"ID": "36-01", "碑名": "Test1", "緯度": 34.0, "経度": 134.0, "県コード": "36", "災害種別": "津波", "種別_洪水": "0", "種別_土砂災害": "0", "種別_津波": "1", "種別_火山災害": "0", "種別_地震": "0", "種別_高潮": "0", "種別_その他": "0"}]
    setup_mock_csv(input_csv, rows)
    
    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    content1 = output_csv.read_text(encoding="utf-8-sig")
    
    process_points(input_csv, output_csv, cache_dir, 5678, fetch_mock_success, mock_sleep_fn)
    content2 = output_csv.read_text(encoding="utf-8-sig")
    
    assert content1 != content2

def test_c_distance_within_range(tmp_path, basic_rows):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    setup_mock_csv(input_csv, basic_rows)
    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_rows = list(csv.DictReader(f))
        
    for r in out_rows:
        dist = calc_haversine(34.0, 134.0, float(r["緯度"]), float(r["経度"]))
        assert 99.0 <= dist <= 2001.0

def test_d_skip_ocean_points(tmp_path, capsys, basic_rows):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    setup_mock_csv(input_csv, basic_rows)
    
    call_count = 0
    skipped_coords = []
    def fetch_mock_skip(lat, lon):
        nonlocal call_count
        call_count += 1
        # 2回目と4回目に "-----" を返す
        if call_count in (2, 4):
            skipped_coords.append((lat, lon))
            return {"elevation": "-----", "hsrc": "-----"}
        return {"elevation": 10.0, "hsrc": "DEM5A"}

    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_skip, mock_sleep_fn)
    
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_rows = list(csv.DictReader(f))
        
    # ③その碑の点は5点そろう
    assert len(out_rows) == 5
    
    # ①その緯度・経度が出力に無い
    out_coords = [(float(r["緯度"]), float(r["経度"])) for r in out_rows]
    for skipped in skipped_coords:
        assert skipped not in out_coords
        
    # ②まとめ表示の「海上などで捨てた候補の数」が 2
    captured = capsys.readouterr()
    assert "海上などで捨てた候補の数: 2" in captured.out

def test_e_max_retry_and_zero_points(tmp_path, capsys, basic_rows):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    setup_mock_csv(input_csv, basic_rows)
    
    call_count = 0
    def fetch_mock_always_skip(lat, lon):
        nonlocal call_count
        call_count += 1
        return {"elevation": "-----", "hsrc": "-----"}

    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_always_skip, mock_sleep_fn)
    
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_rows = list(csv.DictReader(f))
        
    # 呼び出し回数がちょうど50回
    assert call_count == 50
    # その碑の点は0点
    assert len(out_rows) == 0
    
    # まとめ表示に「ID(0点)」が出る
    captured = capsys.readouterr()
    assert "36-01(0点)" in captured.out

def test_f_order_independence(tmp_path):
    input_csv = tmp_path / "monuments.csv"
    output_csv1 = tmp_path / "points1.csv"
    output_csv2 = tmp_path / "points2.csv"
    cache_dir = tmp_path / "cache"
    
    rows = [
        {"ID": "36-01", "碑名": "Test1", "緯度": 34.0, "経度": 134.0, "県コード": "36", "災害種別": "津波", "種別_洪水": "0", "種別_土砂災害": "0", "種別_津波": "1", "種別_火山災害": "0", "種別_地震": "0", "種別_高潮": "0", "種別_その他": "0"},
        {"ID": "36-02", "碑名": "Test2", "緯度": 34.1, "経度": 134.1, "県コード": "36", "災害種別": "洪水", "種別_洪水": "1", "種別_土砂災害": "0", "種別_津波": "0", "種別_火山災害": "0", "種別_地震": "0", "種別_高潮": "0", "種別_その他": "0"},
    ]
    
    setup_mock_csv(input_csv, rows)
    process_points(input_csv, output_csv1, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    
    rows_reversed = list(reversed(rows))
    setup_mock_csv(input_csv, rows_reversed)
    process_points(input_csv, output_csv2, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    
    with open(output_csv1, "r", encoding="utf-8-sig") as f:
        out_rows1 = list(csv.DictReader(f))
    with open(output_csv2, "r", encoding="utf-8-sig") as f:
        out_rows2 = list(csv.DictReader(f))
        
    dict1 = {r["ID"]: (r["緯度"], r["経度"]) for r in out_rows1}
    dict2 = {r["ID"]: (r["緯度"], r["経度"]) for r in out_rows2}
    
    assert dict1 == dict2

def test_g_inherit_disaster_types(tmp_path, basic_rows):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    setup_mock_csv(input_csv, basic_rows)
    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_rows = list(csv.DictReader(f))
        
    for r in out_rows:
        assert r["災害種別"] == "津波"
        assert r["種別_津波"] == "1"
        assert r["種別_洪水"] == "0"

def test_h_id_format_and_count(tmp_path, basic_rows):
    input_csv = tmp_path / "monuments.csv"
    output_csv = tmp_path / "points.csv"
    cache_dir = tmp_path / "cache"
    
    setup_mock_csv(input_csv, basic_rows)
    process_points(input_csv, output_csv, cache_dir, 1234, fetch_mock_success, mock_sleep_fn)
    
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_rows = list(csv.DictReader(f))
        
    counts = {}
    for r in out_rows:
        orig_id = r["元の碑ID"]
        counts[orig_id] = counts.get(orig_id, 0) + 1
        assert r["ID"] == f"{orig_id}-P{counts[orig_id]}"
    assert counts["36-01"] == 5

def test_target_logic():
    # 4. --target のテスト
    from src.add_elevation import get_filenames as get_filenames_elev
    from src.add_river_coast import get_filenames as get_filenames_river
    from src.add_landform import get_filenames as get_filenames_landform
    from pathlib import Path
    
    base = Path("base")
    
    e1, e2 = get_filenames_elev("36", "monuments", base_dir=base)
    assert e1 == base / "monuments_36.csv"
    assert e2 == base / "elevation_36.csv"
    
    e3, e4 = get_filenames_elev("36", "points", base_dir=base)
    assert e3 == base / "points_36.csv"
    assert e4 == base / "elevation_points_36.csv"
    
    r1, r2, r3 = get_filenames_river("36", "monuments", base_dir=base)
    assert r1 == base / "monuments_36.csv"
    assert r3 == base / "river_coast_36.csv"
    
    r4, r5, r6 = get_filenames_river("36", "points", base_dir=base)
    assert r4 == base / "points_36.csv"
    assert r6 == base / "river_coast_points_36.csv"
    
    l1, l2 = get_filenames_landform("36", "monuments", base_dir=base)
    assert l1 == base / "monuments_36.csv"
    assert l2 == base / "landform_36.csv"
    
    l3, l4 = get_filenames_landform("36", "points", base_dir=base)
    assert l3 == base / "points_36.csv"
    assert l4 == base / "landform_points_36.csv"

