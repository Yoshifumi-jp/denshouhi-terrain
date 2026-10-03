import argparse
import sys
import os
import csv
import math
import random
from pathlib import Path
from collections import Counter
import datetime
import time

PROJECT_ROOT = Path(__file__).parent.parent

try:
    from src.prefectures import PREFECTURES
    from src.add_elevation import get_elevation_with_cache, load_cache, fetch_elevation_api, sleep_func
except ImportError:
    from prefectures import PREFECTURES
    from add_elevation import get_elevation_with_cache, load_cache, fetch_elevation_api, sleep_func

EARTH_RADIUS = 6371000

def get_offset_latlon(lat, lon, dist_m, angle_deg):
    """ 指定した距離(m)と方角(度、北=0)から新しい緯度経度を計算する """
    # 角度をラジアンに変換
    theta = math.radians(angle_deg)
    
    # 距離のX成分(経度方向)、Y成分(緯度方向)
    dx = dist_m * math.sin(theta)
    dy = dist_m * math.cos(theta)
    
    # 緯度の変化量 (1度は地球の円周 / 360)
    delta_lat = math.degrees(dy / EARTH_RADIUS)
    
    # 経度の変化量 (緯度によって円周が変わるため cos(lat) で調整)
    # math.cosにはラジアンを渡す
    delta_lon = math.degrees(dx / (EARTH_RADIUS * math.cos(math.radians(lat))))
    
    new_lat = lat + delta_lat
    new_lon = lon + delta_lon
    
    return round(new_lat, 6), round(new_lon, 6)

def main():
    parser = argparse.ArgumentParser(description="比較地点を作成する")
    parser.add_argument("--pref", type=str, required=True, help="都道府県コード (例: 36)")
    parser.add_argument("--seed", type=int, default=20261002, help="乱数シード")
    args = parser.parse_args()

    pref = args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)

    input_csv = PROJECT_ROOT / "data" / "processed" / f"monuments_{pref}.csv"
    output_csv = PROJECT_ROOT / "data" / "processed" / f"points_{pref}.csv"
    cache_dir = PROJECT_ROOT / "data" / "cache"
    
    if not input_csv.exists():
        print(f"エラー: 入力ファイル {input_csv} が見つかりません。")
        sys.exit(1)

    process_points(input_csv, output_csv, cache_dir, args.seed, fetch_elevation_api, sleep_func)

def process_points(input_csv, output_csv, cache_dir, seed, fetch_func, sleep_fn):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "elevation_cache.csv"
    cache_df = load_cache(cache_file)
    
    stats = {
        "api_calls": 0,
        "cache_hits": 0,
        "total_monuments": 0,
        "total_points": 0,
        "discarded_sea": 0,
        "error_network": 0,
        "under_5_points": [] # (id, count)
    }

    results = []
    
    try:
        with open(input_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            monuments = list(reader)
            
        print(f"開始します（全 {len(monuments)} 基）")
            
        for row in monuments:
            stats["total_monuments"] += 1
            mon_id = row["ID"]
            lon = float(row["経度"])
            lat = float(row["緯度"])
            
            # 各碑についてシード値を固定
            rng = random.Random(f"{seed}-{mon_id}")
            
            points_found = 0
            attempts = 0
            
            while points_found < 5 and attempts < 50:
                attempts += 1
                
                # 乱数生成
                u = rng.random()
                r = math.sqrt(u * (2000**2 - 100**2) + 100**2)
                angle = rng.uniform(0, 360)
                
                new_lat, new_lon = get_offset_latlon(lat, lon, r, angle)
                
                # 標高チェック (海上の点は除く)
                elev_val, hsrc_val, status = get_elevation_with_cache(
                    new_lat, new_lon, cache_df, cache_file, fetch_func, sleep_fn, stats
                )
                
                if status == "通信エラー":
                    stats["error_network"] += 1
                    continue
                    
                if elev_val == "-----":
                    stats["discarded_sea"] += 1
                    continue
                    
                # 採用
                points_found += 1
                stats["total_points"] += 1
                
                new_row = {
                    "ID": f"{mon_id}-P{points_found}",
                    "碑名": "比較地点",
                    "元の碑ID": mon_id,
                    "碑からの距離_m": int(round(r)),
                    "方角_度": int(round(angle)),
                    "緯度": new_lat,
                    "経度": new_lon,
                    "県コード": row.get("県コード", ""),
                    "災害種別": row.get("災害種別", ""),
                    "種別_洪水": row.get("種別_洪水", ""),
                    "種別_土砂災害": row.get("種別_土砂災害", ""),
                    "種別_火山災害": row.get("種別_火山災害", ""),
                    "種別_地震": row.get("種別_地震", ""),
                    "種別_その他": row.get("種別_その他", ""),
                    "シード値": seed
                }
                
                # 津波と高潮も7列に含まれるためコピー
                if "種別_津波" in row:
                    new_row["種別_津波"] = row["種別_津波"]
                if "種別_高潮" in row:
                    new_row["種別_高潮"] = row["種別_高潮"]
                    
                results.append(new_row)
                
            if points_found < 5:
                stats["under_5_points"].append((mon_id, points_found))
                
            print(f"{stats['total_monuments']}/{len(monuments)} {mon_id} 比較地点作成完了 ({points_found}点)")
            
    except KeyboardInterrupt:
        print("\n中断しました。もう一度実行すると続きから再開します。")
        sys.exit(0)
        
    # 出力列を整理
    fieldnames = [
        "ID", "碑名", "元の碑ID", "碑からの距離_m", "方角_度", "緯度", "経度",
        "県コード", "災害種別", "種別_洪水", "種別_土砂災害", "種別_津波", "種別_火山災害", "種別_地震", "種別_高潮", "種別_その他", "シード値"
    ]
    
    # 元のCSVに存在しない列は除外
    if monuments:
        first_row = monuments[0]
        actual_fields = ["ID", "碑名", "元の碑ID", "碑からの距離_m", "方角_度", "緯度", "経度"]
        for col in ["県コード", "災害種別", "種別_洪水", "種別_地震", "種別_津波", "種別_土砂災害", "種別_高潮", "種別_火山災害", "種別_その他"]:
            if col in first_row:
                actual_fields.append(col)
        actual_fields.append("シード値")
        fieldnames = actual_fields
        
    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
        
    print("-" * 30)
    # 対象の県名／碑の数／作った比較地点の数／海上などで捨てた候補の数／通信エラーの数／5点に届かなかった碑（IDと点数）／今回サーバーに問い合わせた回数／キャッシュから読んだ回数／保存先
    pref_code = ""
    if monuments:
        pref_code = monuments[0].get("県コード", "")
    if not pref_code:
        # try to extract from input_csv path
        name_parts = Path(input_csv).stem.split("_")
        if len(name_parts) > 1:
            pref_code = name_parts[1]

    print(f"対象の県名: {PREFECTURES.get(pref_code, '不明')}")
    print(f"碑の数: {stats['total_monuments']}")
    print(f"作った比較地点の数: {stats['total_points']}")
    print(f"海上などで捨てた候補の数: {stats['discarded_sea']}")
    print(f"通信エラーの数: {stats['error_network']}")
    
    under_5_str = "なし"
    if stats['under_5_points']:
        under_5_str = ", ".join([f"{pid}({cnt}点)" for pid, cnt in stats['under_5_points']])
    print(f"5点に届かなかった碑: {under_5_str}")
    
    print(f"今回サーバーに問い合わせた回数: {stats['api_calls']}")
    print(f"キャッシュから読んだ回数: {stats['cache_hits']}")
    print(f"保存先: {output_csv.name}")

if __name__ == "__main__":
    main()

