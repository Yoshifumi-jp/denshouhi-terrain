import os
import sys
import csv
import math
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
    from src.landform_codes import LANDFORM_CODES
    from src.prefectures import PREFECTURES
except ImportError:
    from landform_codes import LANDFORM_CODES
    from prefectures import PREFECTURES

def lonlat_to_tile(lon, lat, z=16):
    """経度・緯度からタイル座標(x, y)を計算する"""
    x = int((lon + 180.0) / 360.0 * (2.0 ** z))
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + (1.0 / math.cos(lat_rad))) / math.pi) / 2.0 * (2.0 ** z))
    return x, y

def default_fetch_func(x, y):
    """タイルを取得する。404の場合はNoneを返し、その他のエラーは例外を発生させる"""
    url = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_landformclassification1/16/{x}/{y}.geojson"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            if data.startswith(b'\x1f\x8b'):
                data = gzip.decompress(data)
            return json.loads(data)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise e

def default_sleep_fn():
    """標準のウェイト関数"""
    time.sleep(1.0)

def get_filenames(pref, target, base_dir=PROJECT_ROOT / "data" / "processed"):
    if target == "points":
        return base_dir / f"points_{pref}.csv", base_dir / f"landform_points_{pref}.csv"
    else:
        return base_dir / f"monuments_{pref}.csv", base_dir / f"landform_{pref}.csv"

def main():
    parser = argparse.ArgumentParser(description="地形分類データを追加する")
    parser.add_argument("--pref", type=str, required=True, help="都道府県コード (例: 36)")
    parser.add_argument("--target", type=str, choices=['monuments', 'points'], default='monuments', help='処理対象')
    args = parser.parse_args()

    pref = args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)

    input_csv, output_csv = get_filenames(pref, args.target)
    cache_dir = PROJECT_ROOT / "data" / "cache" / "landform" / "16"

    if not input_csv.exists():
        if args.target == "points":
            print(f"先に python src/make_comparison_points.py --pref {pref} を実行してください")
        else:
            print(f"先に python src/load_monuments.py --pref {pref} を実行してください")
        sys.exit(1)

    process_monuments(str(input_csv), str(output_csv), str(cache_dir), default_fetch_func, default_sleep_fn)

def process_monuments(input_csv, output_csv, cache_dir, fetch_func, sleep_fn):
    os.makedirs(cache_dir, exist_ok=True)

    results = []
    stats = {
        "total": 0,
        "status": Counter(),
        "names": Counter(),
        "fetch_count": 0,
        "cache_count": 0,
        "unknown_code_count": 0
    }

    # タイルごとのキャッシュデータを保持（複数碑が同じタイルの場合に再読込しないため）
    # key: (x, y), value: geojson_dict or "error"
    in_memory_tiles = {}

    today_str = datetime.now().strftime("%Y-%m-%d")

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total"] += 1
            lon = float(row["経度"])
            lat = float(row["緯度"])
            x, y = lonlat_to_tile(lon, lat, 16)
            
            geojson_data = None
            status = ""
            landform_name = ""
            landform_code = ""
            overlap_count = 0

            # 1. メモリ内またはディスクキャッシュから取得
            if (x, y) in in_memory_tiles:
                geojson_data = in_memory_tiles[(x, y)]
            else:
                cache_file = os.path.join(cache_dir, str(x), f"{y}.geojson")
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as cf:
                            geojson_data = json.load(cf)
                        in_memory_tiles[(x, y)] = geojson_data
                        stats["cache_count"] += 1
                    except Exception:
                        pass
                
                # 2. キャッシュにない場合はフェッチ
                if geojson_data is None:
                    os.makedirs(os.path.join(cache_dir, str(x)), exist_ok=True)
                    stats["fetch_count"] += 1
                    try:
                        fetched = fetch_func(x, y)
                        
                        if fetched is None: # 404
                            geojson_data = {"type": "FeatureCollection", "features": []}
                        else:
                            geojson_data = fetched
                        
                        # キャッシュに保存
                        with open(cache_file, "w", encoding="utf-8") as cf:
                            json.dump(geojson_data, cf, ensure_ascii=False)
                        in_memory_tiles[(x, y)] = geojson_data
                        
                    except Exception as e:
                        # 取得エラー
                        geojson_data = "error"
                        in_memory_tiles[(x, y)] = geojson_data
                        # エラー時はキャッシュファイルを作らない
                    finally:
                        sleep_fn()

            # 3. GeoJSONからポリゴン判定
            if geojson_data == "error":
                status = "取得不可"
            else:
                features = geojson_data.get("features", [])
                if not features:
                    status = "データなし"
                else:
                    pt = Point(lon, lat)
                    overlapping_features = []
                    for feature in features:
                        geom = shape(feature["geometry"])
                        if geom.covers(pt):
                            overlapping_features.append(feature)
                    
                    if overlapping_features:
                        status = "取得済"
                        overlap_count = len(overlapping_features)
                        first_feature = overlapping_features[0]
                        code_val = first_feature.get("properties", {}).get("code")
                        
                        if code_val is not None:
                            try:
                                code_int = int(code_val)
                            except ValueError:
                                code_int = code_val
                            
                            landform_code = str(code_val)
                            landform_name = LANDFORM_CODES.get(code_int, f"不明（code={code_val}）")
                            if code_int not in LANDFORM_CODES:
                                stats["unknown_code_count"] += 1
                    else:
                        status = "データなし"
            
            stats["status"][status] += 1
            if status == "取得済":
                stats["names"][landform_name] += 1
            
            out_row = {
                "ID": row["ID"],
                "碑名": row["碑名"],
                "緯度": row["緯度"],
                "経度": row["経度"],
                "地形分類名": landform_name,
                "地形分類コード": landform_code,
                "地形分類_重なり数": overlap_count,
                "地形分類_状態": status,
                "取得日": today_str if status != "取得不可" else ""
            }
            results.append(out_row)

    # CSV書き出し
    fieldnames = ["ID", "碑名", "緯度", "経度", "地形分類名", "地形分類コード", "地形分類_重なり数", "地形分類_状態", "取得日"]
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # まとめ表示
    print(f"対象件数: {stats['total']}")
    for s, c in stats["status"].items():
        print(f"  {s}: {c}件")
    print(f"問い合わせ回数: {stats['fetch_count']}")
    print(f"キャッシュから読んだ回数: {stats['cache_count']}")
    print(f"表にないcodeの件数: {stats['unknown_code_count']}")
    print("地形分類名ごとの件数:")
    for name, c in stats["names"].most_common():
        print(f"  {name}: {c}件")

if __name__ == "__main__":
    main()
