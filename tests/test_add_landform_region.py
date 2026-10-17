"""src/add_landform_region.py の自動テスト"""

import csv
import json
import pytest

from src.add_landform_region import (
    PROJECT_ROOT,
    lonlat_to_tile,
    process_monuments,
)


def _make_polygon_feature(code, lon_min=133.9, lat_min=33.9, lon_max=134.1, lat_max=34.1):
    """テスト用の矩形Polygon地物を作る"""
    return {
        "type": "Feature",
        "properties": {"code": str(code)},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [lon_min, lat_min],
                    [lon_max, lat_min],
                    [lon_max, lat_max],
                    [lon_min, lat_max],
                    [lon_min, lat_min],
                ]
            ],
        },
    }


def test_lonlat_to_tile_z13_z8():
    # (a) タイル番号：経度 134.584699・緯度 34.066366 の z=13 → (7158, 3270)、z=8 → (223, 102)
    assert lonlat_to_tile(134.584699, 34.066366, 13) == (7158, 3270)
    assert lonlat_to_tile(134.584699, 34.066366, 8) == (223, 102)


def test_z13_covered(tmp_path):
    # (b) z=13 で覆う地物あり → 取得済（地域版）・名前・コード・重なり数
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text("ID,碑名,緯度,経度\n01,テスト碑,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    calls = []

    def fake_fetch(z, x, y):
        calls.append((z, x, y))
        if z == 13:
            return {"type": "FeatureCollection", "features": [_make_polygon_feature("51")]}
        return {"type": "FeatureCollection", "features": []}

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["地域版_状態"] == "取得済（地域版）"
    assert rows[0]["地域版_地形分類名"] == "低地"
    assert rows[0]["地域版_コード"] == "51"
    assert rows[0]["地域版_重なり数"] == "1"
    assert rows[0]["取得日"] != ""
    # z=13 で見つかったので z=8 は呼ばれない
    assert [c[0] for c in calls] == [13]


def test_z13_not_covered_z8_covered(tmp_path):
    # (c) z=13 は地物あるが覆わない、z=8 で覆う → 取得済（広域版）・広域版の名前
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text("ID,碑名,緯度,経度\n01,テスト碑,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    def fake_fetch(z, x, y):
        if z == 13:
            # 点(134.0, 34.0)を覆わないポリゴン
            return {"type": "FeatureCollection", "features": [_make_polygon_feature("51", 135.0, 35.0, 135.1, 35.1)]}
        if z == 8:
            return {"type": "FeatureCollection", "features": [_make_polygon_feature("1")]}
        return None

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_状態"] == "取得済（広域版）"
    assert rows[0]["地域版_地形分類名"] == "山地・丘陵"
    assert rows[0]["地域版_コード"] == "1"
    assert rows[0]["地域版_重なり数"] == "1"
    assert rows[0]["取得日"] != ""


def test_both_404_no_data(tmp_path):
    # (d) z=13・z=8 とも 404 → データなし（キャッシュには空の FeatureCollection が残る）
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    lon, lat = 134.0, 34.0
    input_csv.write_text(f"ID,碑名,緯度,経度\n01,テスト碑,{lat},{lon}\n", encoding="utf-8-sig", newline="\n")

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), lambda z, x, y: None, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_状態"] == "データなし"
    assert rows[0]["地域版_地形分類名"] == ""
    assert rows[0]["地域版_コード"] == ""
    assert rows[0]["地域版_重なり数"] == "0"
    assert rows[0]["取得日"] != ""

    x13, y13 = lonlat_to_tile(lon, lat, 13)
    x8, y8 = lonlat_to_tile(lon, lat, 8)
    c13 = cache_dir / "13" / str(x13) / f"{y13}.geojson"
    c8 = cache_dir / "8" / str(x8) / f"{y8}.geojson"
    assert c13.exists()
    assert c8.exists()
    assert json.loads(c13.read_text(encoding="utf-8")) == {"type": "FeatureCollection", "features": []}
    assert json.loads(c8.read_text(encoding="utf-8")) == {"type": "FeatureCollection", "features": []}


def test_z13_network_error(tmp_path):
    # (e) z=13 が通信エラー → 取得不可・取得日は空・z=8 は呼ばれない・z=13 のキャッシュファイルはできない
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    lon, lat = 134.0, 34.0
    input_csv.write_text(f"ID,碑名,緯度,経度\n01,テスト碑,{lat},{lon}\n", encoding="utf-8-sig", newline="\n")

    calls = []

    def fake_fetch(z, x, y):
        calls.append((z, x, y))
        raise RuntimeError("network error")

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_状態"] == "取得不可"
    assert rows[0]["地域版_地形分類名"] == ""
    assert rows[0]["地域版_コード"] == ""
    assert rows[0]["地域版_重なり数"] == "0"
    assert rows[0]["取得日"] == ""
    # z=8 は呼ばれない
    assert [c[0] for c in calls] == [13]
    # z=13 のキャッシュファイルはできない
    x13, y13 = lonlat_to_tile(lon, lat, 13)
    assert not (cache_dir / "13" / str(x13) / f"{y13}.geojson").exists()


def test_z13_not_covered_z8_network_error(tmp_path):
    # (f) z=13 は覆わない、z=8 が通信エラー → 取得不可
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    lon, lat = 134.0, 34.0
    input_csv.write_text(f"ID,碑名,緯度,経度\n01,テスト碑,{lat},{lon}\n", encoding="utf-8-sig", newline="\n")

    def fake_fetch(z, x, y):
        if z == 13:
            return {"type": "FeatureCollection", "features": []}
        raise RuntimeError("z=8 network error")

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_状態"] == "取得不可"
    assert rows[0]["地域版_地形分類名"] == ""
    assert rows[0]["地域版_コード"] == ""
    assert rows[0]["地域版_重なり数"] == "0"
    assert rows[0]["取得日"] == ""
    x8, y8 = lonlat_to_tile(lon, lat, 8)
    assert not (cache_dir / "8" / str(x8) / f"{y8}.geojson").exists()


def test_point_on_polygon_boundary(tmp_path):
    # (g) 点がポリゴンの辺の上 → 覆う（取得済）
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    # 点 (134.0, 34.0) がポリゴンの右辺 lon=134.0 上にある
    input_csv.write_text("ID,碑名,緯度,経度\n01,境界碑,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    def fake_fetch(z, x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature("11", 133.9, 33.9, 134.0, 34.1)]}

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_状態"] == "取得済（地域版）"
    assert rows[0]["地域版_地形分類名"] == "山地"


def test_unknown_code(tmp_path, capsys):
    # (h) 表にない code → 名前 不明（code=99）、表にないcodeの件数 1
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text("ID,碑名,緯度,経度\n01,不明碑,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    def fake_fetch(z, x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature("99")]}

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_地形分類名"] == "不明（code=99）"
    assert rows[0]["地域版_コード"] == "99"
    out = capsys.readouterr().out
    assert "表にないcodeの件数: 1" in out


def test_two_overlapping_features(tmp_path):
    # (i) 2つの地物が覆う → 重なり数 2、コードは最初の地物
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text("ID,碑名,緯度,経度\n01,重複碑,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    def fake_fetch(z, x, y):
        return {
            "type": "FeatureCollection",
            "features": [
                _make_polygon_feature("41"),
                _make_polygon_feature("51"),
            ],
        }

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版_重なり数"] == "2"
    assert rows[0]["地域版_コード"] == "41"
    assert rows[0]["地域版_地形分類名"] == "台地・段丘"


def test_same_tile_two_points(tmp_path):
    # (j) 同じタイルの2地点 → 問い合わせは1回
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text(
        "ID,碑名,緯度,経度\n01,地点1,34.0,134.0\n02,地点2,34.0001,134.0001\n",
        encoding="utf-8-sig",
        newline="\n",
    )

    calls = []

    def fake_fetch(z, x, y):
        calls.append((z, x, y))
        return {"type": "FeatureCollection", "features": [_make_polygon_feature("51")]}

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)
    assert len(calls) == 1


def test_second_run_uses_cache(tmp_path, capsys):
    # (k) 2回目の実行（同じキャッシュ）→ 問い合わせ 0、結果は1回目と同じ
    input_csv = tmp_path / "in.csv"
    output_csv1 = tmp_path / "out1.csv"
    output_csv2 = tmp_path / "out2.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text("ID,碑名,緯度,経度\n01,地点1,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    calls = []

    def fake_fetch(z, x, y):
        calls.append((z, x, y))
        return {"type": "FeatureCollection", "features": [_make_polygon_feature("11")]}

    process_monuments(str(input_csv), str(output_csv1), str(cache_dir), fake_fetch, lambda: None)
    capsys.readouterr()
    assert len(calls) == 1

    calls.clear()
    process_monuments(str(input_csv), str(output_csv2), str(cache_dir), fake_fetch, lambda: None)
    out2 = capsys.readouterr().out
    assert len(calls) == 0
    assert "問い合わせ回数: 0" in out2
    assert "キャッシュから読んだ回数: 1" in out2
    assert output_csv1.read_bytes() == output_csv2.read_bytes()


def test_output_columns_and_lf(tmp_path):
    # (l) 出力の列名と順番、改行が LF（ファイルに \r がない）
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text("ID,碑名,緯度,経度\n01,地点1,34.0,134.0\n", encoding="utf-8-sig", newline="\n")

    def fake_fetch(z, x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature("51")]}

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    raw = output_csv.read_bytes()
    assert b"\r" not in raw

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == [
        "ID",
        "碑名",
        "緯度",
        "経度",
        "地域版_地形分類名",
        "地域版_コード",
        "地域版_重なり数",
        "地域版_状態",
        "取得日",
    ]


def test_summary_output(tmp_path, capsys):
    # (m) まとめ表示の文言（capsys で、状態の4行が件数0でも出ること）
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    input_csv.write_text(
        "ID,碑名,緯度,経度\n"
        "01,地点1,34.0,134.0\n"
        "02,地点2,34.0001,134.0001\n",
        encoding="utf-8-sig",
        newline="\n",
    )

    def fake_fetch(z, x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature("51")]}

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None, clock=lambda: 0.0)
    out = capsys.readouterr().out
    expected_block = (
        "対象件数: 2\n"
        "  取得済（地域版）: 2件\n"
        "  取得済（広域版）: 0件\n"
        "  データなし: 0件\n"
        "  取得不可: 0件\n"
        "問い合わせ回数: 1\n"
        "キャッシュから読んだ回数: 0\n"
        "表にないcodeの件数: 0\n"
        "地形分類名ごとの件数:\n"
        "  低地: 2件"
    )
    assert expected_block in out


def test_real_data_verification(tmp_path):
    # (n) 実データの照合（キャッシュだけを読む。キャッシュがなければ pytest.skip）：8件
    expected_cases = [
        ("monuments_36.csv", "36207-001", "山地", "取得済（地域版）"),
        ("monuments_36.csv", "36204-003", "山地", "取得済（地域版）"),
        ("monuments_36.csv", "36383-002", "", "データなし"),
        ("monuments_03.csv", "03202-007", "丘陵・小起伏地", "取得済（地域版）"),
        ("monuments_03.csv", "03207-002", "台地・段丘", "取得済（地域版）"),
        ("monuments_35.csv", "35204-004", "火山地形（やや不明瞭）", "取得済（地域版）"),
        ("monuments_35.csv", "35202-001", "低地", "取得済（地域版）"),
        ("points_03.csv", "03202-003-P4", "", "データなし"),
    ]

    processed_dir = PROJECT_ROOT / "data" / "processed"
    real_cache_dir = PROJECT_ROOT / "data" / "cache" / "landform"

    target_rows = []
    for csv_name, target_id, exp_name, exp_status in expected_cases:
        csv_path = processed_dir / csv_name
        if not csv_path.exists():
            pytest.skip(f"入力CSVが存在しないためスキップ: {csv_name}")
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            found = None
            for r in csv.DictReader(f):
                if r["ID"] == target_id:
                    found = r
                    break
        if found is None:
            pytest.skip(f"対象IDが見つからないためスキップ: {target_id}")

        lon = float(found["経度"])
        lat = float(found["緯度"])
        x13, y13 = lonlat_to_tile(lon, lat, 13)
        if not (real_cache_dir / "13" / str(x13) / f"{y13}.geojson").exists():
            pytest.skip(f"z=13 キャッシュ未取得のためスキップ: 13/{x13}/{y13}")
        if exp_status == "データなし":
            x8, y8 = lonlat_to_tile(lon, lat, 8)
            if not (real_cache_dir / "8" / str(x8) / f"{y8}.geojson").exists():
                pytest.skip(f"z=8 キャッシュ未取得のためスキップ: 8/{x8}/{y8}")

        target_rows.append(found)

    input_csv = tmp_path / "real_in.csv"
    output_csv = tmp_path / "real_out.csv"
    with open(input_csv, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "碑名", "緯度", "経度"], lineterminator="\n")
        writer.writeheader()
        for r in target_rows:
            writer.writerow({"ID": r["ID"], "碑名": r["碑名"], "緯度": r["緯度"], "経度": r["経度"]})

    def fail_fetch(z, x, y):
        pytest.fail(f"実データ照合テストでネットへの問い合わせが発生しました: z={z}, x={x}, y={y}")

    process_monuments(str(input_csv), str(output_csv), str(real_cache_dir), fail_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_by_id = {r["ID"]: r for r in csv.DictReader(f)}

    for _, target_id, exp_name, exp_status in expected_cases:
        actual = out_by_id[target_id]
        assert actual["地域版_地形分類名"] == exp_name, f"{target_id}: 地形分類名が不一致"
        assert actual["地域版_状態"] == exp_status, f"{target_id}: 状態が不一致"

