import pytest
import pandas as pd
from pathlib import Path
from src.prefectures import JPC_EPSG, ZONE_NAMES, PREF_ZONE, select_zone, select_epsg, HOKKAIDO_ZONE11_CODES, HOKKAIDO_ZONE13_CODES, NEIGHBORS, LANDLOCKED

def test_jpc_epsg_and_zone_names():
    assert len(JPC_EPSG) == 19
    assert JPC_EPSG[1] == 6669
    assert JPC_EPSG[4] == 6672
    assert JPC_EPSG[9] == 6677
    assert JPC_EPSG[19] == 6687
    
    assert len(ZONE_NAMES) == 19
    assert ZONE_NAMES[4] == "IV"
    assert ZONE_NAMES[14] == "XIV"

def test_pref_zone():
    assert len(PREF_ZONE) == 43
    assert "01" not in PREF_ZONE
    assert "13" not in PREF_ZONE
    assert "46" not in PREF_ZONE
    assert "47" not in PREF_ZONE

    expected = {
        "42": 1, "40": 2, "41": 2, "43": 2, "44": 2, "45": 2,
        "35": 3, "32": 3, "34": 3,
        "37": 4, "38": 4, "36": 4, "39": 4,
        "28": 5, "31": 5, "33": 5,
        "26": 6, "27": 6, "18": 6, "25": 6, "24": 6, "29": 6, "30": 6,
        "17": 7, "16": 7, "21": 7, "23": 7,
        "15": 8, "20": 8, "19": 8, "22": 8,
        "07": 9, "09": 9, "08": 9, "11": 9, "12": 9, "10": 9, "14": 9,
        "02": 10, "05": 10, "06": 10, "03": 10, "04": 10,
    }
    for pref, expected_zone in expected.items():
        assert select_zone(pref, 35.0, 135.0) == expected_zone

def test_select_zone_locations():
    cases = [
        ("13", 34.75, 139.37, None, 9),  # 大島
        ("13", 33.10, 139.78, None, 9),  # 八丈島
        ("13", 27.09, 142.19, None, 14), # 父島
        ("13", 20.42, 136.08, None, 18), # 沖ノ鳥島
        ("13", 24.28, 153.98, None, 19), # 南鳥島
        ("47", 26.21, 127.68, None, 15), # 那覇
        ("47", 24.34, 124.16, None, 16), # 石垣島
        ("47", 24.47, 123.00, None, 16), # 与那国島
        ("47", 25.84, 131.23, None, 17), # 南大東島
        ("46", 31.60, 130.56, None, 2),  # 鹿児島市
        ("46", 31.68, 129.71, None, 1),  # 下甑島
        ("46", 30.35, 130.53, None, 2),  # 屋久島
        ("46", 30.60, 130.98, None, 2),  # 種子島
        ("46", 29.85, 129.86, None, 1),  # トカラ列島 中之島
        ("46", 28.38, 129.49, None, 1),  # 奄美大島
        ("46", 28.30, 130.02, None, 1),  # 喜界島の東岸
        ("46", 27.05, 128.42, None, 1),  # 与論島
        ("01", 43.19, 141.00, "01203", 11), # 小樽市
        ("01", 43.08, 140.81, "01409", 11), # 赤井川村
        ("01", 42.57, 140.82, "01584", 11), # 洞爺湖町
        ("01", 42.55, 141.36, "01578", 12), # 白老町
        ("01", 43.06, 141.35, "01100", 12), # 札幌市
        ("01", 44.02, 143.52, "01559", 12), # 湧別町
        ("01", 43.92, 144.17, "01564", 13), # 大空町
        ("01", 43.33, 145.58, "01223", 13), # 根室市
        ("01", 45.40, 148.40, "01700", 13), # 蘂取村
    ]
    for pref, lat, lon, muni_code, expected_zone in cases:
        assert select_zone(pref, lat, lon, muni_code) == expected_zone

def test_select_zone_errors():
    with pytest.raises(ValueError):
        select_zone("01", 43.0, 141.0, None)
    with pytest.raises(ValueError):
        select_zone("01", 43.0, 141.0, "36201")
    with pytest.raises(ValueError):
        select_zone("48", 35.0, 135.0)
        
    assert len(HOKKAIDO_ZONE11_CODES) == 42
    assert len(HOKKAIDO_ZONE13_CODES) == 49
    assert len(HOKKAIDO_ZONE11_CODES & HOKKAIDO_ZONE13_CODES) == 0

def test_real_data():
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    
    files = [processed_dir / f"monuments_{str(i).zfill(2)}.csv" for i in range(1, 48)]
    if not all(f.exists() for f in files):
        pytest.skip("実データが揃っていないためスキップ")
        
    total_count = 0
    zone_counts = {z: 0 for z in ZONE_NAMES.values()}
    
    for f in files:
        pref = f.stem.split('_')[1]
        df = pd.read_csv(f, dtype={'ID': str, '市区町村コード': str})
        for _, row in df.iterrows():
            muni = str(row['市区町村コード']).zfill(5) if pd.notna(row.get('市区町村コード')) else None
            z = select_zone(pref, float(row['緯度']), float(row['経度']), muni)
            zone_counts[ZONE_NAMES[z]] += 1
            total_count += 1
            
    assert total_count == 2481
    assert zone_counts["I"] == 51
    assert zone_counts["II"] == 232
    assert zone_counts["III"] == 164
    assert zone_counts["IV"] == 220
    assert zone_counts["V"] == 162
    assert zone_counts["VI"] == 336
    assert zone_counts["VII"] == 167
    assert zone_counts["VIII"] == 281
    assert zone_counts["IX"] == 488
    assert zone_counts["X"] == 318
    assert zone_counts["XI"] == 15
    assert zone_counts["XII"] == 24
    assert zone_counts["XIII"] == 15
    assert zone_counts["XV"] == 4
    assert zone_counts["XVI"] == 3
    assert zone_counts["XVII"] == 1
    assert zone_counts["XIV"] == 0
    assert zone_counts["XVIII"] == 0
    assert zone_counts["XIX"] == 0
    
    # 個別の碑
    expected_epsg = {
        "01367-001": 6679,
        "01460-005": 6680,
        "01206-001": 6681,
        "13401-001": 6677,
        "46222-001": 6669,
        "46201-003": 6670,
        "47209-001": 6683,
        "47214-001": 6684,
        "47357-001": 6685,
        "36201-001": 6672,
    }
    
    for f in files:
        pref = f.stem.split('_')[1]
        df = pd.read_csv(f, dtype={'ID': str, '市区町村コード': str})
        for _, row in df.iterrows():
            if row['ID'] in expected_epsg:
                muni = str(row['市区町村コード']).zfill(5) if pd.notna(row.get('市区町村コード')) else None
                epsg = select_epsg(pref, float(row['緯度']), float(row['経度']), muni)
                assert epsg == expected_epsg[row['ID']]



def test_neighbors():
    # NEIGHBORS が47件
    assert len(NEIGHBORS) == 47

    # 各県のリストの合計が174（87組×2）
    total = sum(len(n) for n in NEIGHBORS.values())
    assert total == 174

    # 左右が対応している、自分自身を含まない
    for pref, neighbors in NEIGHBORS.items():
        assert pref not in neighbors
        for n in neighbors:
            assert pref in NEIGHBORS[n]

    # 個別の検証
    assert NEIGHBORS["01"] == []
    assert NEIGHBORS["47"] == []
    assert NEIGHBORS["36"] == ["37", "38", "39"]
    assert NEIGHBORS["42"] == ["41"]
    assert NEIGHBORS["20"] == ["10", "11", "15", "16", "19", "21", "22", "23"]
    assert "37" in NEIGHBORS["33"]

def test_landlocked():
    # LANDLOCKED が8件ちょうど
    assert len(LANDLOCKED) == 8
    expected = {"09", "10", "11", "19", "20", "21", "25", "29"}
    assert LANDLOCKED == expected
