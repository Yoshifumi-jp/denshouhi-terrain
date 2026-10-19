"""src/add_landform_artificial.py の自動テスト"""

import csv
import json
import pytest

from src.add_landform_artificial import (
    PROJECT_ROOT,
    lonlat_to_tile,
    main,
    process_monuments,
)


def _make_polygon_feature(code, lon_min=133.9, lat_min=33.9, lon_max=134.1, lat_max=34.1):
    """テスト用の矩形Polygon地物を作る"""
    return {
        "type": "Feature",
        "properties": {"code": code},
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


def _write_csv(path, content):
    """UTF-8 BOM・LF でテスト用CSVを書き出す"""
    path.write_text(content, encoding="utf-8-sig", newline="\n")


def test_a_covered(tmp_path):
    # (a) 詳細版が取得済・覆う地物あり → 取得済・名前・コード・重なり数1・取得日あり
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(input_csv, "ID,碑名,緯度,経度\n01,テスト碑,34.0,134.0\n")
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,テスト碑,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n",
    )

    def fake_fetch(x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature(11014)]}

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["人工地形_状態"] == "取得済"
    assert rows[0]["人工地形名"] == "盛土地・埋立地"
    assert rows[0]["人工地形コード"] == "11014"
    assert rows[0]["人工地形_重なり数"] == "1"
    assert rows[0]["取得日"] != ""


def test_b_not_covered(tmp_path):
    # (b) 詳細版が取得済・タイルはあるが覆う地物なし → 人工地形なし
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(input_csv, "ID,碑名,緯度,経度\n01,テスト碑,34.0,134.0\n")
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,テスト碑,34.0,134.0,砂州・砂丘,10504,1,取得済,2026-10-01\n",
    )

    def fake_fetch(x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature(11014, 135.0, 35.0, 135.1, 35.1)]}

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["人工地形_状態"] == "人工地形なし"
    assert rows[0]["人工地形名"] == ""
    assert rows[0]["人工地形コード"] == ""
    assert rows[0]["人工地形_重なり数"] == "0"
    assert rows[0]["取得日"] != ""


def test_c_404_tile(tmp_path):
    # (c) 詳細版が取得済・404 → 人工地形なし、キャッシュに空の FeatureCollection が保存される
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    lon, lat = 134.0, 34.0

    _write_csv(input_csv, f"ID,碑名,緯度,経度\n01,テスト碑,{lat},{lon}\n")
    _write_csv(
        landform_csv,
        f"ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        f"01,テスト碑,{lat},{lon},氾濫平野・海岸平野,10701,1,取得済,2026-10-01\n",
    )

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), lambda x, y: None, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["人工地形_状態"] == "人工地形なし"
    assert rows[0]["人工地形名"] == ""
    assert rows[0]["人工地形コード"] == ""
    assert rows[0]["人工地形_重なり数"] == "0"
    assert rows[0]["取得日"] != ""

    x, y = lonlat_to_tile(lon, lat, 16)
    cache_file = cache_dir / str(x) / f"{y}.geojson"
    assert cache_file.exists()
    assert json.loads(cache_file.read_text(encoding="utf-8")) == {"type": "FeatureCollection", "features": []}


def test_d_detail_no_data(tmp_path):
    # (d) 詳細版がデータなし → 範囲外、fetch が呼ばれない
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(input_csv, "ID,碑名,緯度,経度\n01,テスト碑,34.0,134.0\n")
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,テスト碑,34.0,134.0,,,0,データなし,2026-10-01\n",
    )

    calls = []

    def fake_fetch(x, y):
        calls.append((x, y))
        return None

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    assert len(calls) == 0
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["人工地形_状態"] == "範囲外"
    assert rows[0]["人工地形名"] == ""
    assert rows[0]["人工地形コード"] == ""
    assert rows[0]["人工地形_重なり数"] == "0"
    assert rows[0]["取得日"] != ""


def test_e_detail_unavailable_or_missing_id(tmp_path):
    # (e) 詳細版が取得不可・詳細版に ID がない → 取得不可、fetch が呼ばれない、取得日が空
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(
        input_csv,
        "ID,碑名,緯度,経度\n"
        "01,取得不可碑,34.0,134.0\n"
        "02,空状態碑,34.01,134.01\n"
        "03,IDなし碑,34.02,134.02\n",
    )
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,取得不可碑,34.0,134.0,,,0,取得不可,\n"
        "02,空状態碑,34.01,134.01,,,0,,\n",
    )

    calls = []

    def fake_fetch(x, y):
        calls.append((x, y))
        return None

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    assert len(calls) == 0
    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    for r in rows:
        assert r["人工地形_状態"] == "取得不可"
        assert r["人工地形名"] == ""
        assert r["人工地形コード"] == ""
        assert r["人工地形_重なり数"] == "0"
        assert r["取得日"] == ""


def test_f_network_error(tmp_path):
    # (f) 通信エラー → 取得不可、キャッシュを作らない、取得日が空
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"
    lon, lat = 134.0, 34.0

    _write_csv(input_csv, f"ID,碑名,緯度,経度\n01,テスト碑,{lat},{lon}\n")
    _write_csv(
        landform_csv,
        f"ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        f"01,テスト碑,{lat},{lon},旧水部,10904,1,取得済,2026-10-01\n",
    )

    def fake_fetch(x, y):
        raise RuntimeError("network error")

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["人工地形_状態"] == "取得不可"
    assert rows[0]["人工地形名"] == ""
    assert rows[0]["人工地形コード"] == ""
    assert rows[0]["人工地形_重なり数"] == "0"
    assert rows[0]["取得日"] == ""

    x, y = lonlat_to_tile(lon, lat, 16)
    assert not (cache_dir / str(x) / f"{y}.geojson").exists()


def test_g_two_overlapping_features(tmp_path):
    # (g) 地物が2つ重なる → 重なり数2、先頭の地物の名前
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(input_csv, "ID,碑名,緯度,経度\n01,重複碑,34.0,134.0\n")
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,重複碑,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n",
    )

    def fake_fetch(x, y):
        return {
            "type": "FeatureCollection",
            "features": [
                _make_polygon_feature(11001),  # 切土地
                _make_polygon_feature(11014),  # 盛土地・埋立地
            ],
        }

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["人工地形_状態"] == "取得済"
    assert rows[0]["人工地形_重なり数"] == "2"
    assert rows[0]["人工地形名"] == "切土地"
    assert rows[0]["人工地形コード"] == "11001"


def test_h_non_artificial_and_unknown_code(tmp_path, capsys):
    # (h) 人工地形以外のコード（例 10701 氾濫平野）と表にないコード（例 99999）→「不明（code=…）」、表にないcodeの件数2
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(
        input_csv,
        "ID,碑名,緯度,経度\n"
        "01,自然地形コード碑,34.0,134.0\n"
        "02,未定義コード碑,34.05,134.05\n",
    )
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,自然地形コード碑,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n"
        "02,未定義コード碑,34.05,134.05,旧水部,10904,1,取得済,2026-10-01\n",
    )

    x1, y1 = lonlat_to_tile(134.0, 34.0, 16)
    x2, y2 = lonlat_to_tile(134.05, 34.05, 16)

    def fake_fetch(x, y):
        if (x, y) == (x1, y1):
            return {"type": "FeatureCollection", "features": [_make_polygon_feature(10701, 133.9, 33.9, 134.1, 34.1)]}
        if (x, y) == (x2, y2):
            return {"type": "FeatureCollection", "features": [_make_polygon_feature(99999, 133.9, 33.9, 134.1, 34.1)]}
        return None

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["人工地形名"] == "不明（code=10701）"
    assert rows[0]["人工地形コード"] == "10701"
    assert rows[1]["人工地形名"] == "不明（code=99999）"
    assert rows[1]["人工地形コード"] == "99999"

    out = capsys.readouterr().out
    assert "表にないcodeの件数: 2" in out


def test_i_same_tile_two_points(tmp_path):
    # (i) 同じタイルの2地点 → 問い合わせ1回
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(
        input_csv,
        "ID,碑名,緯度,経度\n"
        "01,地点1,34.0,134.0\n"
        "02,地点2,34.0001,134.0001\n",
    )
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,地点1,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n"
        "02,地点2,34.0001,134.0001,旧水部,10904,1,取得済,2026-10-01\n",
    )

    calls = []

    def fake_fetch(x, y):
        calls.append((x, y))
        return {"type": "FeatureCollection", "features": [_make_polygon_feature(11014)]}

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)
    assert len(calls) == 1


def test_j_second_run_uses_cache(tmp_path, capsys):
    # (j) 2回目の実行はキャッシュだけで済む（問い合わせ0、キャッシュから読んだ回数＝タイル数）
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv1 = tmp_path / "out1.csv"
    output_csv2 = tmp_path / "out2.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(
        input_csv,
        "ID,碑名,緯度,経度\n"
        "01,地点1,34.0,134.0\n"
        "02,地点2,34.05,134.05\n",
    )
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,地点1,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n"
        "02,地点2,34.05,134.05,旧水部,10904,1,取得済,2026-10-01\n",
    )

    calls = []

    def fake_fetch(x, y):
        calls.append((x, y))
        return {"type": "FeatureCollection", "features": [_make_polygon_feature(11014)]}

    process_monuments(str(input_csv), str(landform_csv), str(output_csv1), str(cache_dir), fake_fetch, lambda: None)
    capsys.readouterr()
    assert len(calls) == 2

    calls.clear()
    process_monuments(str(input_csv), str(landform_csv), str(output_csv2), str(cache_dir), fake_fetch, lambda: None)
    out2 = capsys.readouterr().out
    assert len(calls) == 0
    assert "問い合わせ回数: 0" in out2
    assert "キャッシュから読んだ回数: 2" in out2
    assert output_csv1.read_bytes() == output_csv2.read_bytes()


def test_k_output_columns_bom_lf(tmp_path):
    # (k) 出力の列名・順番、BOM、改行 LF
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(input_csv, "ID,碑名,緯度,経度\n01,地点1,34.0,134.0\n")
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,地点1,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n",
    )

    def fake_fetch(x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature(11014)]}

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(cache_dir), fake_fetch, lambda: None)

    raw = output_csv.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
    assert header == [
        "ID",
        "碑名",
        "緯度",
        "経度",
        "人工地形名",
        "人工地形コード",
        "人工地形_重なり数",
        "人工地形_状態",
        "取得日",
    ]


def test_l_summary_output(tmp_path, capsys):
    # (l) まとめ表示の文（状態4行が0件でも出る）
    input_csv = tmp_path / "in.csv"
    landform_csv = tmp_path / "landform.csv"
    output_csv = tmp_path / "out.csv"
    cache_dir = tmp_path / "cache"

    _write_csv(
        input_csv,
        "ID,碑名,緯度,経度\n"
        "01,地点1,34.0,134.0\n"
        "02,地点2,34.0001,134.0001\n",
    )
    _write_csv(
        landform_csv,
        "ID,碑名,緯度,経度,地形分類名,地形分類コード,地形分類_重なり数,地形分類_状態,取得日\n"
        "01,地点1,34.0,134.0,旧水部,10904,1,取得済,2026-10-01\n"
        "02,地点2,34.0001,134.0001,旧水部,10904,1,取得済,2026-10-01\n",
    )

    def fake_fetch(x, y):
        return {"type": "FeatureCollection", "features": [_make_polygon_feature(11014)]}

    process_monuments(
        str(input_csv),
        str(landform_csv),
        str(output_csv),
        str(cache_dir),
        fake_fetch,
        lambda: None,
        clock=lambda: 0.0,
    )
    out = capsys.readouterr().out
    expected_block = (
        "対象件数: 2\n"
        "  取得済: 2件\n"
        "  人工地形なし: 0件\n"
        "  範囲外: 0件\n"
        "  取得不可: 0件\n"
        "問い合わせ回数: 1\n"
        "キャッシュから読んだ回数: 0\n"
        "表にないcodeの件数: 0\n"
        "人工地形名ごとの件数:\n"
        "  盛土地・埋立地: 2件"
    )
    assert expected_block in out


def test_m_missing_landform_csv(tmp_path, monkeypatch, capsys):
    # (m) 詳細版の CSV がないとき終了コード1と案内文（main の引数で確かめる）
    monkeypatch.setattr("src.add_landform_artificial.PROJECT_ROOT", tmp_path)
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(processed_dir / "monuments_36.csv", "ID,碑名,緯度,経度\n36001-001,碑A,34.0,134.0\n")

    with pytest.raises(SystemExit) as e:
        main(["--pref", "36"])
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "先に python src/add_landform.py --pref 36（比較地点は --target points も）を実行してください" in out


def test_n_real_data_verification(tmp_path):
    # (n) 実データの照合（キャッシュだけを読む。キャッシュがなければ pytest.skip。偽の fetch はネットに出たら fail）：9件
    expected_cases = [
        ("monuments_36.csv", "landform_36.csv", "36383-001", "取得済", "盛土地・埋立地", "11014"),
        ("monuments_36.csv", "landform_36.csv", "36401-001", "取得済", "盛土地・埋立地", "11014"),
        ("monuments_13.csv", "landform_13.csv", "13101-004", "取得済", "切土地", "11001"),
        ("monuments_13.csv", "landform_13.csv", "13103-001", "取得済", "盛土地・埋立地", "11005"),
        ("monuments_41.csv", "landform_41.csv", "41208-004", "取得済", "干拓地", "4010101"),
        ("monuments_36.csv", "landform_36.csv", "36201-001", "人工地形なし", "", ""),
        ("monuments_41.csv", "landform_41.csv", "41203-001", "人工地形なし", "", ""),
        ("monuments_36.csv", "landform_36.csv", "36207-001", "範囲外", "", ""),
        ("points_41.csv", "landform_points_41.csv", "41401-001-P4", "取得済", "改変工事中", "11010"),
    ]

    processed_dir = PROJECT_ROOT / "data" / "processed"
    real_cache_dir = PROJECT_ROOT / "data" / "cache" / "artificial" / "16"

    target_rows = []
    landform_rows = []
    for csv_name, lf_name, target_id, exp_status, exp_name, exp_code in expected_cases:
        csv_path = processed_dir / csv_name
        lf_path = processed_dir / lf_name
        if not csv_path.exists() or not lf_path.exists():
            pytest.skip(f"入力または詳細版CSVが存在しないためスキップ: {csv_name}, {lf_name}")

        found_in = None
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r["ID"] == target_id:
                    found_in = r
                    break
        if found_in is None:
            pytest.skip(f"対象IDが見つからないためスキップ: {target_id}")

        found_lf = None
        with open(lf_path, "r", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r["ID"] == target_id:
                    found_lf = r
                    break
        if found_lf is None:
            pytest.skip(f"詳細版に対象IDが見つからないためスキップ: {target_id}")

        if exp_status != "範囲外":
            lon = float(found_in["経度"])
            lat = float(found_in["緯度"])
            x, y = lonlat_to_tile(lon, lat, 16)
            if not (real_cache_dir / str(x) / f"{y}.geojson").exists():
                pytest.skip(f"z=16 人工地形キャッシュ未取得のためスキップ: 16/{x}/{y}")

        target_rows.append(found_in)
        landform_rows.append(found_lf)

    input_csv = tmp_path / "real_in.csv"
    landform_csv = tmp_path / "real_lf.csv"
    output_csv = tmp_path / "real_out.csv"

    with open(input_csv, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "碑名", "緯度", "経度"], lineterminator="\n")
        writer.writeheader()
        for r in target_rows:
            writer.writerow({"ID": r["ID"], "碑名": r["碑名"], "緯度": r["緯度"], "経度": r["経度"]})

    with open(landform_csv, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ID", "碑名", "緯度", "経度", "地形分類名", "地形分類コード", "地形分類_重なり数", "地形分類_状態", "取得日"],
            lineterminator="\n",
        )
        writer.writeheader()
        for r in landform_rows:
            writer.writerow(r)

    def fail_fetch(x, y):
        pytest.fail(f"実データ照合テストでネットへの問い合わせが発生しました: x={x}, y={y}")

    process_monuments(str(input_csv), str(landform_csv), str(output_csv), str(real_cache_dir), fail_fetch, lambda: None)

    with open(output_csv, "r", encoding="utf-8-sig") as f:
        out_by_id = {r["ID"]: r for r in csv.DictReader(f)}

    for _, _, target_id, exp_status, exp_name, exp_code in expected_cases:
        actual = out_by_id[target_id]
        assert actual["人工地形_状態"] == exp_status, f"{target_id}: 状態が不一致"
        assert actual["人工地形名"] == exp_name, f"{target_id}: 人工地形名が不一致"
        assert actual["人工地形コード"] == exp_code, f"{target_id}: コードが不一致"

