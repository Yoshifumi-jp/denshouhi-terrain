"""地形分類（人工地形）を碑・比較地点に付与するプログラム。

国土地理院ベクトルタイル提供実験「地形分類（人工地形）」（z=16）を取得し、
自然地形（詳細版）が「取得済」の地点に対して人工地形の判定を行う。

出典:
- 国土地理院ベクトルタイル提供実験「地形分類（人工地形）」
  https://cyberjapandata.gsi.go.jp/xyz/experimental_landformclassification2/16/{x}/{y}.geojson
- 凡例・コード対応表
  https://github.com/gsi-cyberjapan/experimental_landformclassification
"""

import os
import sys
import csv
import json
import time
import gzip
import argparse
import urllib.request
from urllib.error import HTTPError
from datetime import datetime
from collections import Counter
from pathlib import Path
from shapely.geometry import shape, Point

PROJECT_ROOT = Path(__file__).parent.parent

try:
    from src.add_landform import lonlat_to_tile
    from src.landform_codes import LANDFORM_CODES
    from src.prefectures import PREFECTURES
    from src.progress import should_print, progress_line
except ImportError:
    from add_landform import lonlat_to_tile
    from landform_codes import LANDFORM_CODES
    from prefectures import PREFECTURES
    from progress import should_print, progress_line

# 人工地形として扱う分類名
ARTIFICIAL_NAMES = {
    "切土地",
    "農耕平坦化地",
    "干拓地",
    "盛土地・埋立地",
    "改変工事中",
}


def default_fetch_func(x, y):
    """指定タイル座標(z=16)のGeoJSONを取得する。404はNoneを返し、その他のエラーは例外を送出する"""
    url = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_landformclassification2/16/{x}/{y}.geojson"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            if data.startswith(b"\x1f\x8b"):
                data = gzip.decompress(data)
            return json.loads(data)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise e


def default_sleep_fn():
    """標準のウェイト関数（1秒待機）"""
    time.sleep(1.0)


def get_filenames(pref, target, base_dir=None):
    """都道府県コードと対象種別から入力・詳細版・出力CSVのパスを返す"""
    if base_dir is None:
        base_dir = PROJECT_ROOT / "data" / "processed"
    if target == "points":
        return (
            base_dir / f"points_{pref}.csv",
            base_dir / f"landform_points_{pref}.csv",
            base_dir / f"landform_artificial_points_{pref}.csv",
        )
    else:
        return (
            base_dir / f"monuments_{pref}.csv",
            base_dir / f"landform_{pref}.csv",
            base_dir / f"landform_artificial_{pref}.csv",
        )


def _get_tile_data(x, y, cache_dir, in_memory_tiles, fetch_func, sleep_fn, stats):
    """指定タイル(x, y)のGeoJSONデータをメモリ・ディスクキャッシュ・通信のいずれかから取得する"""
    key = (x, y)
    if key in in_memory_tiles:
        return in_memory_tiles[key]

    cache_file = os.path.join(cache_dir, str(x), f"{y}.geojson")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as cf:
                geojson_data = json.load(cf)
            in_memory_tiles[key] = geojson_data
            stats["cache_count"] += 1
            return geojson_data
        except Exception:
            pass

    # キャッシュにない場合はネットに問い合わせる
    os.makedirs(os.path.join(cache_dir, str(x)), exist_ok=True)
    stats["fetch_count"] += 1
    try:
        fetched = fetch_func(x, y)
        if fetched is None:  # 404
            geojson_data = {"type": "FeatureCollection", "features": []}
        else:
            geojson_data = fetched

        # キャッシュに保存（LF）
        with open(cache_file, "w", encoding="utf-8", newline="\n") as cf:
            json.dump(geojson_data, cf, ensure_ascii=False)
        in_memory_tiles[key] = geojson_data
    except Exception:
        # 通信エラー時はキャッシュファイルを作らない
        geojson_data = "error"
        in_memory_tiles[key] = geojson_data
    finally:
        sleep_fn()

    return geojson_data


def _find_covering_features(geojson_data, pt):
    """GeoJSONの地物一覧から、点ptを覆う（covers）地物のリストを返す"""
    features = geojson_data.get("features", [])
    if not features:
        return []
    overlapping = []
    for feature in features:
        geom = shape(feature["geometry"])
        if geom.covers(pt):
            overlapping.append(feature)
    return overlapping


def _resolve_code(first_feature, stats):
    """先頭地物のcodeから（人工地形名, コード文字列）を返す"""
    code_val = first_feature.get("properties", {}).get("code")
    if code_val is None:
        return "", ""
    try:
        code_int = int(code_val)
    except (ValueError, TypeError):
        code_int = code_val
    code_str = str(code_val)
    name = LANDFORM_CODES.get(code_int)
    if name in ARTIFICIAL_NAMES:
        return name, code_str
    stats["unknown_code_count"] += 1
    return f"不明（code={code_str}）", code_str


def process_monuments(input_csv, landform_csv, output_csv, cache_dir, fetch_func, sleep_fn, clock=time.monotonic):
    """入力CSVの各行について人工地形（z=16）の地形分類を判定しCSVに書き出す"""
    start = clock()
    label = "地形分類（人工地形）"
    os.makedirs(cache_dir, exist_ok=True)

    results = []
    stats = {
        "total": 0,
        "status": Counter(),
        "names": Counter(),
        "fetch_count": 0,
        "cache_count": 0,
        "unknown_code_count": 0,
    }

    # 1回の実行の中で同じタイルを読み直さないためのメモリキャッシュ
    # key: (x, y), value: geojson_dict or "error"
    in_memory_tiles = {}

    today_str = datetime.now().strftime("%Y-%m-%d")

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    with open(landform_csv, "r", encoding="utf-8-sig") as f:
        landform_status_by_id = {
            r["ID"]: r.get("地形分類_状態", "") for r in csv.DictReader(f)
        }

    total_rows = len(rows)
    for row in rows:
        stats["total"] += 1
        lon = float(row["経度"])
        lat = float(row["緯度"])

        detail_status = landform_status_by_id.get(row["ID"], "")
        status = ""
        artificial_name = ""
        artificial_code = ""
        overlap_count = 0

        if detail_status == "取得済":
            x, y = lonlat_to_tile(lon, lat, 16)
            data = _get_tile_data(x, y, cache_dir, in_memory_tiles, fetch_func, sleep_fn, stats)
            if data == "error":
                status = "取得不可"
            else:
                pt = Point(lon, lat)
                overlapping = _find_covering_features(data, pt)
                if overlapping:
                    status = "取得済"
                    overlap_count = len(overlapping)
                    artificial_name, artificial_code = _resolve_code(overlapping[0], stats)
                else:
                    status = "人工地形なし"
        elif detail_status == "データなし":
            status = "範囲外"
        else:
            status = "取得不可"

        stats["status"][status] += 1
        if status == "取得済":
            stats["names"][artificial_name] += 1

        out_row = {
            "ID": row["ID"],
            "碑名": row["碑名"],
            "緯度": row["緯度"],
            "経度": row["経度"],
            "人工地形名": artificial_name,
            "人工地形コード": artificial_code,
            "人工地形_重なり数": overlap_count,
            "人工地形_状態": status,
            "取得日": today_str if status != "取得不可" else "",
        }
        results.append(out_row)

        done = stats["total"]
        if should_print(done, total_rows):
            print(
                progress_line(label, done, total_rows, clock() - start, stats["fetch_count"], stats["cache_count"]),
                flush=True,
            )

    # CSV書き出し（UTF-8 BOM付き、改行LF）
    fieldnames = [
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
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)

    # まとめ表示（状態の4行は件数0でも必ず出す）
    status_order = ["取得済", "人工地形なし", "範囲外", "取得不可"]
    print(f"対象件数: {stats['total']}")
    for s in status_order:
        print(f"  {s}: {stats['status'][s]}件")
    print(f"問い合わせ回数: {stats['fetch_count']}")
    print(f"キャッシュから読んだ回数: {stats['cache_count']}")
    print(f"表にないcodeの件数: {stats['unknown_code_count']}")
    print("人工地形名ごとの件数:")
    for name, c in sorted(stats["names"].items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {name}: {c}件")


def main(args=None):
    parser = argparse.ArgumentParser(description="地形分類データ（人工地形）を追加する")
    parser.add_argument("--pref", type=str, required=True, help="都道府県コード (例: 36)")
    parser.add_argument("--target", type=str, choices=["monuments", "points"], default="monuments", help="処理対象")
    parsed_args = parser.parse_args(args)

    pref = parsed_args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)

    input_csv, landform_csv, output_csv = get_filenames(pref, parsed_args.target)
    cache_dir = PROJECT_ROOT / "data" / "cache" / "artificial" / "16"

    if not input_csv.exists():
        if parsed_args.target == "points":
            print(f"先に python src/make_comparison_points.py --pref {pref} を実行してください")
        else:
            print(f"先に python src/load_monuments.py --pref {pref} を実行してください")
        sys.exit(1)

    if not landform_csv.exists():
        print(f"先に python src/add_landform.py --pref {pref}（比較地点は --target points も）を実行してください")
        sys.exit(1)

    process_monuments(
        str(input_csv),
        str(landform_csv),
        str(output_csv),
        str(cache_dir),
        default_fetch_func,
        default_sleep_fn,
    )


if __name__ == "__main__":
    main()

