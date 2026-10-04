import argparse
import sys
import os
import csv
import math
import time
import urllib.request
from urllib.error import HTTPError
from datetime import datetime
from pathlib import Path
from io import BytesIO
from PIL import Image
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from src.prefectures import PREFECTURES
    from src.hazard_layers import LAYERS, SHINSUI_LEGEND, DOSHA_NAMES, DOSHA_LEGENDS, SHINSUI_NAMES
except ImportError:
    from prefectures import PREFECTURES
    from hazard_layers import LAYERS, SHINSUI_LEGEND, DOSHA_NAMES, DOSHA_LEGENDS, SHINSUI_NAMES

def default_sleep_fn():
    time.sleep(1.0)

def default_fetch_func(path, z, x, y):
    url = f"https://disaportaldata.gsi.go.jp/raster/{path}/{z}/{x}/{y}.png"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read()
    except HTTPError as e:
        if e.code == 404:
            return None
        raise e

def lonlat_to_pixel(lon, lat, z=17):
    lat_rad = math.radians(lat)
    fx = (lon + 180) / 360 * (2 ** z)
    fy = (1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * (2 ** z)
    x = int(fx)
    y = int(fy)
    i = int((fx - x) * 256)
    j = int((fy - y) * 256)
    i = max(0, min(255, i))
    j = max(0, min(255, j))
    return x, y, i, j

def classify_pixel(rgba, palette):
    if rgba is None:
        return '区域外', '', ''
    r, g, b, a = rgba
    if a < 128:
        return '区域外', '', ''
        
    for color, label in palette:
        if (r, g, b) == color:
            return '区域内', label, '完全一致'
            
    min_dist = float('inf')
    best_label = None
    for color, label in palette:
        pr, pg, pb = color
        dist = (r - pr)**2 + (g - pg)**2 + (b - pb)**2
        if dist < min_dist:
            min_dist = dist
            best_label = label
            
    return '区域内', best_label, '近い色'

def summarize_dosha(dosha_results):
    if any(res[0] == '取得不可' for res in dosha_results.values()):
        return '取得不可', '', '', '', ''
        
    active_layers = []
    for key in ['doseki', 'kyukei', 'jisuberi']:
        if dosha_results[key][0] == '区域内':
            active_layers.append((key, dosha_results[key][1], dosha_results[key][2]))
            
    if not active_layers:
        return '区域外', '', '', '', ''
        
    has_tokubetsu = any('特別警戒区域' in item[1] for item in active_layers)
    kubun = '特別警戒区域' if has_tokubetsu else '警戒区域'
    
    gensho = '・'.join(DOSHA_NAMES[item[0]] for item in active_layers)
    
    has_yotei = any('指定予定' in item[1] for item in active_layers)
    yotei = 'あり' if has_yotei else ''
    
    if all(item[2] == '完全一致' for item in active_layers):
        icchi = '完全一致'
    else:
        icchi = '近い色'
        
    return '区域内', kubun, gensho, yotei, icchi

def get_filenames(pref, target, base_dir=None):
    if base_dir is None:
        base_dir = PROJECT_ROOT / "data" / "processed"
    if target == "points":
        return base_dir / f"points_{pref}.csv", base_dir / f"hazard_points_{pref}.csv"
    else:
        return base_dir / f"monuments_{pref}.csv", base_dir / f"hazard_{pref}.csv"
def main(args=None):
    parser = argparse.ArgumentParser(description="ハザード区域の判定")
    parser.add_argument("--pref", type=str, required=True, help="都道府県コード（例 36）")
    parser.add_argument("--target", type=str, choices=['monuments', 'points'], default='monuments', help='処理対象')
    parsed_args = parser.parse_args(args)

    pref = parsed_args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)

    input_csv, output_csv = get_filenames(pref, parsed_args.target)
    cache_base_dir = PROJECT_ROOT / "data" / "cache" / "hazard"

    if not input_csv.exists():
        if parsed_args.target == "points":
            print(f"先に python src/make_comparison_points.py --pref {pref} を実行してください")
        else:
            print(f"先に python src/load_monuments.py --pref {pref} を実行してください")
        sys.exit(1)

    process_monuments(pref, parsed_args.target, str(input_csv), str(output_csv), str(cache_base_dir), default_fetch_func, default_sleep_fn)
def process_monuments(pref, target, input_csv, output_csv, cache_base_dir, fetch_func, sleep_fn):
    results = []
    stats = {
        "total": 0,
        "fetch_count": 0,
        "cache_count": 0,
        "flood": Counter(),
        "flood_shinsui": Counter(),
        "tsunami": Counter(),
        "tsunami_shinsui": Counter(),
        "hightide": Counter(),
        "hightide_shinsui": Counter(),
        "dosha": Counter(),
        "dosha_kubun": Counter(),
        "dosha_yotei": 0,
        "chiakai_iro": 0
    }
    
    in_memory_tiles = {k: {} for k in LAYERS.keys()}
    today_str = datetime.now().strftime("%Y-%m-%d")

    def get_tile(layer_key, z, x, y):
        if (x, y) in in_memory_tiles[layer_key]:
            return in_memory_tiles[layer_key][(x, y)]
            
        layer_path = LAYERS[layer_key]
        cache_dir = os.path.join(cache_base_dir, layer_key, str(z), str(x))
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{y}.png")
        none_file = os.path.join(cache_dir, f"{y}.none")
        
        img = None
        if os.path.exists(none_file):
            img = '404'
            stats["cache_count"] += 1
        elif os.path.exists(cache_file):
            try:
                img = Image.open(cache_file).convert("RGBA")
                stats["cache_count"] += 1
            except Exception:
                pass
                
        if img is None:
            stats["fetch_count"] += 1
            try:
                fetched = fetch_func(layer_path, z, x, y)
                if fetched is None:
                    open(none_file, 'w').close()
                    img = '404'
                else:
                    with open(cache_file, "wb") as f:
                        f.write(fetched)
                    img = Image.open(BytesIO(fetched)).convert("RGBA")
            except Exception:
                img = "error"
            finally:
                sleep_fn()
                
        in_memory_tiles[layer_key][(x, y)] = img
        return img

    with open(input_csv, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["total"] += 1
            lon = float(row["経度"])
            lat = float(row["緯度"])
            x, y, i, j = lonlat_to_pixel(lon, lat, 17)
            
            layer_results = {}
            has_error = False
            chiakai_records = []
            
            for key in ['flood', 'tsunami', 'hightide']:
                img = get_tile(key, 17, x, y)
                if img == "error":
                    layer_results[key] = ('取得不可', '', '')
                    has_error = True
                elif img == '404':
                    layer_results[key] = ('区域外', '', '')
                else:
                    rgba = img.getpixel((i, j))
                    layer_results[key] = classify_pixel(rgba, SHINSUI_LEGEND)
                    if layer_results[key][2] == '近い色':
                        r, g, b, a = rgba
                        chiakai_records.append(f"{SHINSUI_NAMES[key]}={r},{g},{b},{a}")
                        
            dosha_res = {}
            for key in ['doseki', 'kyukei', 'jisuberi']:
                img = get_tile(key, 17, x, y)
                if img == "error":
                    dosha_res[key] = ('取得不可', '', '')
                    has_error = True
                elif img == '404':
                    dosha_res[key] = ('区域外', '', '')
                else:
                    rgba = img.getpixel((i, j))
                    dosha_res[key] = classify_pixel(rgba, DOSHA_LEGENDS[key])
                    if dosha_res[key][2] == '近い色':
                        r, g, b, a = rgba
                        chiakai_records.append(f"{DOSHA_NAMES[key]}={r},{g},{b},{a}")
            
            layer_results['dosha'] = summarize_dosha(dosha_res)
            
            for key in ['flood', 'tsunami', 'hightide']:
                st = layer_results[key][0]
                stats[key][st] += 1
                if st == '区域内':
                    stats[f"{key}_shinsui"][layer_results[key][1]] += 1
                    
            ds_st = layer_results['dosha'][0]
            stats['dosha'][ds_st] += 1
            if ds_st == '区域内':
                kubun = layer_results['dosha'][1]
                stats['dosha_kubun'][kubun] += 1
                if layer_results['dosha'][3] == 'あり':
                    stats['dosha_yotei'] += 1
                    
            if chiakai_records:
                stats['chiakai_iro'] += 1
            
            out_row = {
                "ID": row["ID"],
                "碑名": row["碑名"],
                "緯度": row["緯度"],
                "経度": row["経度"],
            }
            if target == "points":
                out_row["元の碑ID"] = row["元の碑ID"]
                
            out_row.update({
                "洪水_状態": layer_results['flood'][0],
                "洪水_浸水深": layer_results['flood'][1] if layer_results['flood'][0] == '区域内' else '',
                "洪水_色の一致": layer_results['flood'][2] if layer_results['flood'][0] == '区域内' else '',
                "津波_状態": layer_results['tsunami'][0],
                "津波_浸水深": layer_results['tsunami'][1] if layer_results['tsunami'][0] == '区域内' else '',
                "津波_色の一致": layer_results['tsunami'][2] if layer_results['tsunami'][0] == '区域内' else '',
                "高潮_状態": layer_results['hightide'][0],
                "高潮_浸水深": layer_results['hightide'][1] if layer_results['hightide'][0] == '区域内' else '',
                "高潮_色の一致": layer_results['hightide'][2] if layer_results['hightide'][0] == '区域内' else '',
                "土砂_状態": layer_results['dosha'][0],
                "土砂_区分": layer_results['dosha'][1] if layer_results['dosha'][0] == '区域内' else '',
                "土砂_現象": layer_results['dosha'][2] if layer_results['dosha'][0] == '区域内' else '',
                "土砂_指定予定": layer_results['dosha'][3] if layer_results['dosha'][0] == '区域内' else '',
                "土砂_色の一致": layer_results['dosha'][4] if layer_results['dosha'][0] == '区域内' else '',
                "近い色の記録": "；".join(chiakai_records),
                "取得日": "" if has_error else today_str
            })
            results.append(out_row)

    fieldnames = ["ID", "碑名"]
    if target == "points":
        fieldnames.append("元の碑ID")
    fieldnames.extend(["緯度", "経度", "洪水_状態", "洪水_浸水深", "洪水_色の一致", "津波_状態", "津波_浸水深", "津波_色の一致", "高潮_状態", "高潮_浸水深", "高潮_色の一致", "土砂_状態", "土砂_区分", "土砂_現象", "土砂_指定予定", "土砂_色の一致", "近い色の記録", "取得日"])
    
    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    target_str = "碑" if target == "monuments" else "比較地点"
    pref_name = PREFECTURES.get(pref, "")
    print(f"ハザード区域の判定：{pref_name}（{pref}）・{target_str}")
    print(f"対象：{stats['total']}件（タイルの問い合わせ {stats['fetch_count']}件、キャッシュ利用 {stats['cache_count']}件）")
    
    def print_shinsui(key, title):
        print(f"{title}：区域内 {stats[key]['区域内']}／区域外 {stats[key]['区域外']}／取得不可 {stats[key]['取得不可']}")
        if stats[key]['区域内'] > 0:
            shinsui_parts = []
            for _color, label in SHINSUI_LEGEND:
                c = stats[f"{key}_shinsui"].get(label, 0)
                if c > 0:
                    shinsui_parts.append(f"{label} {c}")
            if shinsui_parts:
                print("  浸水深：" + "／".join(shinsui_parts))

    print_shinsui('flood', '洪水（想定最大規模）')
    print_shinsui('tsunami', '津波')
    print_shinsui('hightide', '高潮')
    
    dosha_in = stats['dosha']['区域内']
    print(f"土砂災害：区域内 {dosha_in}（特別警戒区域 {stats['dosha_kubun']['特別警戒区域']}・警戒区域 {stats['dosha_kubun']['警戒区域']}、指定予定を含む {stats['dosha_yotei']}）／区域外 {stats['dosha']['区域外']}／取得不可 {stats['dosha']['取得不可']}")
    
    print(f"近い色で判定：{stats['chiakai_iro']}件")
    try:
        rel_out = Path(output_csv).relative_to(PROJECT_ROOT)
    except ValueError:
        rel_out = Path(output_csv)
    print(f"出力：{rel_out.as_posix()}")
    
    return results

if __name__ == "__main__":
    main()

