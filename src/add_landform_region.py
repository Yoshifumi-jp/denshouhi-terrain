"""地形分類（自然地形）の地域版（ズーム13、中分類）および広域版（ズーム8、大分類）を付与するプログラム。

国土地理院ベクトルタイル提供実験「地形分類（自然地形）」の地域版（z=13）を全地点に付与し、
地域版で取得できない場合のみ広域版（z=8）で補う。

出典:
- 国土地理院ベクトルタイル提供実験「地形分類（自然地形）」
  https://cyberjapandata.gsi.go.jp/xyz/experimental_landformclassification1/{z}/{x}/{y}.geojson
- 凡例・コード対応表（style.js）
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
    from src.prefectures import PREFECTURES
    from src.progress import should_print, progress_line
except ImportError:
    from add_landform import lonlat_to_tile
    from prefectures import PREFECTURES
    from progress import should_print, progress_line

# 地形分類コードと名前の対応表
# 出典: https://github.com/gsi-cyberjapan/experimental_landformclassification （style.js の凡例）
REGION_CODES_Z13 = {
    "11": "山地",
    "12": "残丘状地形",
    "13": "カルスト地形",
    "21": "丘陵・小起伏地",
    "31": "火山地形（明瞭）",
    "32": "火山地形（やや不明瞭）",
    "33": "火山性丘陵",
    "34": "火山麓地形",
    "41": "台地・段丘",
    "51": "低地",
    "61": "砂丘",
    "71": "湖",
}

# 広域版（z=8）の地形分類コードと名前の対応表
# 出典: https://github.com/gsi-cyberjapan/experimental_landformclassification （style.js の凡例）
WIDE_CODES_Z8 = {
    "1": "山地・丘陵",
    "3": "火山地形",
    "4": "台地・段丘",
    "5": "低地",
    "6": "砂丘",
    "7": "湖",
}


def default_fetch_func(z, x, y):
    """指定ズーム・タイル座標のGeoJSONを取得する。404はNoneを返し、その他のエラーは例外を送出する"""
    url = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_landformclassification1/{z}/{x}/{y}.geojson"
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


def get_filenames(pref, target, base_dir=PROJECT_ROOT / "data" / "processed"):
    """都道府県コードと対象種別から入出力CSVのパスを返す"""
    if target == "points":
        return base_dir / f"points_{pref}.csv", base_dir / f"landform_region_points_{pref}.csv"
    else:
        return base_dir / f"monuments_{pref}.csv", base_dir / f"landform_region_{pref}.csv"


def _get_tile_data(z, x, y, cache_dir, in_memory_tiles, fetch_func, sleep_fn, stats):
    """指定タイル(z, x, y)のGeoJSONデータをメモリ・ディスクキャッシュ・通信のいずれかから取得する"""
    key = (z, x, y)
    if key in in_memory_tiles:
        return in_memory_tiles[key]

    cache_file = os.path.join(cache_dir, str(z), str(x), f"{y}.geojson")
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
    os.makedirs(os.path.join(cache_dir, str(z), str(x)), exist_ok=True)
    stats["fetch_count"] += 1
    try:
        fetched = fetch_func(z, x, y)
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


def _resolve_code(first_feature, code_map, stats):
    """先頭地物のcodeから（地形分類名, コード文字列）を返す"""
    code_val = first_feature.get("properties", {}).get("code")
    if code_val is None:
        return "", ""
    code_str = str(code_val)
    if code_str in code_map:
        return code_map[code_str], code_str
    stats["unknown_code_count"] += 1
    return f"不明（code={code_str}）", code_str


def process_monuments(input_csv, output_csv, cache_dir, fetch_func, sleep_fn, clock=time.monotonic):
    """入力CSVの各行について地域版（z=13）・広域版（z=8）の地形分類を判定しCSVに書き出す"""
    start = clock()
    label = "地形分類（地域版）"
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
    # key: (z, x, y), value: geojson_dict or "error"
    in_memory_tiles = {}

    today_str = datetime.now().strftime("%Y-%m-%d")

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    for row in rows:
        stats["total"] += 1
        lon = float(row["経度"])
        lat = float(row["緯度"])
        pt = Point(lon, lat)

        status = ""
        landform_name = ""
        landform_code = ""
        overlap_count = 0

        # 1. z=13（地域版）で判定
        x13, y13 = lonlat_to_tile(lon, lat, 13)
        data13 = _get_tile_data(13, x13, y13, cache_dir, in_memory_tiles, fetch_func, sleep_fn, stats)

        if data13 == "error":
            status = "取得不可"
        else:
            overlapping13 = _find_covering_features(data13, pt)
            if overlapping13:
                status = "取得済（地域版）"
                overlap_count = len(overlapping13)
                landform_name, landform_code = _resolve_code(overlapping13[0], REGION_CODES_Z13, stats)
            else:
                # 2. z=13で見つからないときだけ z=8（広域版）で判定
                x8, y8 = lonlat_to_tile(lon, lat, 8)
                data8 = _get_tile_data(8, x8, y8, cache_dir, in_memory_tiles, fetch_func, sleep_fn, stats)
                if data8 == "error":
                    status = "取得不可"
                else:
                    overlapping8 = _find_covering_features(data8, pt)
                    if overlapping8:
                        status = "取得済（広域版）"
                        overlap_count = len(overlapping8)
                        landform_name, landform_code = _resolve_code(overlapping8[0], WIDE_CODES_Z8, stats)
                    else:
                        status = "データなし"

        stats["status"][status] += 1
        if status in ("取得済（地域版）", "取得済（広域版）"):
            stats["names"][landform_name] += 1

        out_row = {
            "ID": row["ID"],
            "碑名": row["碑名"],
            "緯度": row["緯度"],
            "経度": row["経度"],
            "地域版_地形分類名": landform_name,
            "地域版_コード": landform_code,
            "地域版_重なり数": overlap_count,
            "地域版_状態": status,
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
        "地域版_地形分類名",
        "地域版_コード",
        "地域版_重なり数",
        "地域版_状態",
        "取得日",
    ]
    os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
    with open(output_csv, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)

    # まとめ表示（状態の4行は件数0でも必ず出す）
    status_order = ["取得済（地域版）", "取得済（広域版）", "データなし", "取得不可"]
    print(f"対象件数: {stats['total']}")
    for s in status_order:
        print(f"  {s}: {stats['status'][s]}件")
    print(f"問い合わせ回数: {stats['fetch_count']}")
    print(f"キャッシュから読んだ回数: {stats['cache_count']}")
    print(f"表にないcodeの件数: {stats['unknown_code_count']}")
    print("地形分類名ごとの件数:")
    for name, c in sorted(stats["names"].items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {name}: {c}件")


def main():
    parser = argparse.ArgumentParser(description="地形分類データ（地域版・広域版）を追加する")
    parser.add_argument("--pref", type=str, required=True, help="都道府県コード (例: 36)")
    parser.add_argument("--target", type=str, choices=["monuments", "points"], default="monuments", help="処理対象")
    args = parser.parse_args()

    pref = args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)

    input_csv, output_csv = get_filenames(pref, args.target)
    cache_dir = PROJECT_ROOT / "data" / "cache" / "landform"

    if not input_csv.exists():
        if args.target == "points":
            print(f"先に python src/make_comparison_points.py --pref {pref} を実行してください")
        else:
            print(f"先に python src/load_monuments.py --pref {pref} を実行してください")
        sys.exit(1)

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), default_fetch_func, default_sleep_fn)


if __name__ == "__main__":
    main()

