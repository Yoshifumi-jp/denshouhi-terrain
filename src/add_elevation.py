import argparse
import sys
import math
import time
import datetime
from pathlib import Path
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).parent.parent

try:
    from src.prefectures import PREFECTURES
except ImportError:
    from prefectures import PREFECTURES

# 地球の半径 (m)
EARTH_RADIUS = 6371000

def calc_delta_degrees(lat_deg, lon_deg, distance_m=10):
    """
    指定した距離(m)に相当する緯度・経度の差（度）を計算する。
    """
    lat_rad = math.radians(lat_deg)
    
    # 緯度1度あたりの距離: 2 * pi * R / 360 = pi * R / 180
    lat_m_per_deg = (math.pi * EARTH_RADIUS) / 180
    delta_lat = distance_m / lat_m_per_deg
    
    # 経度1度あたりの距離 (緯度による補正): cos(lat) * 2 * pi * R / 360
    lon_m_per_deg = math.cos(lat_rad) * (math.pi * EARTH_RADIUS) / 180
    delta_lon = distance_m / lon_m_per_deg
    
    return delta_lat, delta_lon

def fetch_elevation_api(lat, lon, timeout=10):
    """
    国土地理院の標高APIに問い合わせて結果を返す。
    テスト時にモックに差し替えられるよう独立させる。
    """
    url = f"https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php?lon={lon}&lat={lat}&outtype=JSON"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def sleep_func(seconds):
    """テスト時にモックに差し替えられるようにする。"""
    time.sleep(seconds)

def get_elevation_with_cache(lat, lon, cache_df, cache_file, fetch_func, sleep_fn, stats):
    """
    キャッシュがあればそれを返し、なければAPIから取得してキャッシュに保存する。
    戻り値: (elevation_val, hsrc_val, status_msg)
    """
    # 緯度・経度を小数6桁に丸めてキーにする
    lat_key = round(lat, 6)
    lon_key = round(lon, 6)
    
    # キャッシュを検索 (浮動小数点の誤差を考慮して丸めた値で比較)
    mask = (cache_df['緯度'].round(6) == lat_key) & (cache_df['経度'].round(6) == lon_key)
    match = cache_df[mask]
    
    if not match.empty:
        stats['cache_hits'] += 1
        row = match.iloc[0]
        return row['標高'], row['標高データ種別'], "OK"
    
    # キャッシュになければ取得
    stats['api_calls'] += 1
    
    # 1秒待機
    if stats['api_calls'] > 1 or stats['cache_hits'] > 0:
        sleep_fn(1.0)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            data = fetch_func(lat, lon)
            elev = data.get("elevation")
            hsrc = data.get("hsrc")
            
            # APIの戻り値が "-----" などの文字列か数値か
            # 数値なら float にする、"-----"ならそのまま
            if elev == "-----":
                elev_val = "-----"
                hsrc_val = hsrc
            else:
                try:
                    elev_val = float(elev)
                    hsrc_val = hsrc
                except (ValueError, TypeError):
                    elev_val = "-----"
                    hsrc_val = hsrc
                    
            # キャッシュに保存
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = pd.DataFrame([{
                '緯度': lat_key,
                '経度': lon_key,
                '標高': elev_val,
                '標高データ種別': hsrc_val,
                '取得日時': now_str
            }])
            new_row.to_csv(cache_file, mode='a', header=not cache_file.exists(), index=False, encoding='utf-8-sig')
            
            # cache_df にも追加
            cache_df.loc[len(cache_df)] = new_row.iloc[0]
            cache_df['緯度'] = cache_df['緯度'].astype(float)
            cache_df['経度'] = cache_df['経度'].astype(float)
            
            return elev_val, hsrc_val, "OK"
            
        except Exception:
            if attempt < max_retries - 1:
                sleep_fn(1.0)
            else:
                return None, None, "通信エラー"

def calculate_slope(center_lat, center_lon, fetch_func, sleep_fn, cache_df, cache_file, stats):
    """
    中心座標から東西南北に10m離れた4地点の標高を取得し、傾斜(度)を計算する。
    戻り値: (slope_deg, status)
    """
    delta_lat, delta_lon = calc_delta_degrees(center_lat, center_lon, 10)
    
    points = {
        'N': (center_lat + delta_lat, center_lon),
        'S': (center_lat - delta_lat, center_lon),
        'E': (center_lat, center_lon + delta_lon),
        'W': (center_lat, center_lon - delta_lon)
    }
    
    elevations = {}
    for pt, (lat, lon) in points.items():
        elev, _, status = get_elevation_with_cache(lat, lon, cache_df, cache_file, fetch_func, sleep_fn, stats)
        if status == "通信エラー":
            return None, "通信エラー"
        if status != "OK" or elev == "-----":
            return None, "データなし"
        elevations[pt] = float(elev)
        
    ew_gradient = (elevations['E'] - elevations['W']) / 20.0
    ns_gradient = (elevations['N'] - elevations['S']) / 20.0
    
    slope_rad = math.atan(math.sqrt(ew_gradient**2 + ns_gradient**2))
    slope_deg = math.degrees(slope_rad)
    
    return round(slope_deg, 1), "OK"

def load_cache(cache_file):
    empty_cache = pd.DataFrame({
        '緯度': pd.Series(dtype='float64'),
        '経度': pd.Series(dtype='float64'),
        '標高': pd.Series(dtype='object'),
        '標高データ種別': pd.Series(dtype='object'),
        '取得日時': pd.Series(dtype='object')
    })
    
    if cache_file.exists():
        try:
            df = pd.read_csv(cache_file, encoding='utf-8-sig', dtype={'緯度': float, '経度': float})
            if not {'緯度', '経度', '標高'}.issubset(df.columns):
                raise ValueError("必要な列がありません")
            return df
        except Exception:
            print(f"警告: キャッシュファイル {cache_file} を読めません。ファイルを確認してください。")
            sys.exit(1)
            
    return empty_cache

def process_monuments(df, pref_code, cache_dir, output_file, fetch_func=fetch_elevation_api, sleep_fn=sleep_func):
    cache_file = cache_dir / "elevation_cache.csv"
    cache_df = load_cache(cache_file)
    
    stats = {
        'api_calls': 0,
        'cache_hits': 0,
        'success': 0,
        'error_nodata': 0,
        'error_network': 0,
        'error_network_ids': [],
        'error_nodata_ids': []
    }
    
    results = []
    total = len(df)
    
    print(f"処理を開始します（全 {total} 件）")
    
    try:
        for idx, row in df.iterrows():
            mon_id = row['ID']
            name = row['碑名']
            lat_str = str(row['緯度'])
            lon_str = str(row['経度'])
            
            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                # 緯度経度が数値でない場合
                results.append({
                    'ID': mon_id, '碑名': name, '緯度': lat_str, '経度': lon_str,
                    '標高_m': None, '標高データ種別': None, '傾斜_度': None,
                    '取得状態': '取得不可（データなし）',
                    '取得日': datetime.date.today().strftime("%Y-%m-%d")
                })
                stats['error_nodata'] += 1
                stats['error_nodata_ids'].append(mon_id)
                print(f"{idx+1}/{total} {mon_id} 標高 取得不可 傾斜 取得不可")
                continue

            # 中心の標高を取得
            elev_val, hsrc_val, status = get_elevation_with_cache(lat, lon, cache_df, cache_file, fetch_func, sleep_fn, stats)
            
            if status == "通信エラー":
                results.append({
                    'ID': mon_id, '碑名': name, '緯度': lat, '経度': lon,
                    '標高_m': None, '標高データ種別': None, '傾斜_度': None,
                    '取得状態': '取得不可（通信エラー）',
                    '取得日': datetime.date.today().strftime("%Y-%m-%d")
                })
                stats['error_network'] += 1
                stats['error_network_ids'].append(mon_id)
                print(f"{idx+1}/{total} {mon_id} 標高 通信エラー 傾斜 通信エラー")
                continue
                
            if elev_val == "-----":
                results.append({
                    'ID': mon_id, '碑名': name, '緯度': lat, '経度': lon,
                    '標高_m': None, '標高データ種別': hsrc_val, '傾斜_度': None,
                    '取得状態': '取得不可（データなし）',
                    '取得日': datetime.date.today().strftime("%Y-%m-%d")
                })
                stats['error_nodata'] += 1
                stats['error_nodata_ids'].append(mon_id)
                print(f"{idx+1}/{total} {mon_id} 標高 データなし 傾斜 データなし")
                continue
                
            # 傾斜を計算
            slope, slope_status = calculate_slope(lat, lon, fetch_func, sleep_fn, cache_df, cache_file, stats)
            
            if slope is None:
                if slope_status == "通信エラー":
                    results.append({
                        'ID': mon_id, '碑名': name, '緯度': lat, '経度': lon,
                        '標高_m': elev_val, '標高データ種別': hsrc_val, '傾斜_度': None,
                        '取得状態': '取得不可（通信エラー）',
                        '取得日': datetime.date.today().strftime("%Y-%m-%d")
                    })
                    stats['error_network'] += 1
                    stats['error_network_ids'].append(mon_id)
                    print(f"{idx+1}/{total} {mon_id} 標高 {elev_val}m 傾斜 通信エラー")
                else:
                    results.append({
                        'ID': mon_id, '碑名': name, '緯度': lat, '経度': lon,
                        '標高_m': elev_val, '標高データ種別': hsrc_val, '傾斜_度': None,
                        '取得状態': '取得不可（データなし）',
                        '取得日': datetime.date.today().strftime("%Y-%m-%d")
                    })
                    stats['error_nodata'] += 1
                    stats['error_nodata_ids'].append(mon_id)
                    print(f"{idx+1}/{total} {mon_id} 標高 {elev_val}m 傾斜 データなし")
            else:
                results.append({
                    'ID': mon_id, '碑名': name, '緯度': lat, '経度': lon,
                    '標高_m': elev_val, '標高データ種別': hsrc_val, '傾斜_度': slope,
                    '取得状態': '取得済',
                    '取得日': datetime.date.today().strftime("%Y-%m-%d")
                })
                stats['success'] += 1
                print(f"{idx+1}/{total} {mon_id} 標高 {elev_val}m 傾斜 {slope}度")
                
    except KeyboardInterrupt:
        print("\n中断しました。もう一度実行すると続きから再開します。")
        sys.exit(0)
        
    # 保存
    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values('ID')
    res_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # まとめ表示
    print("-" * 30)
    print(f"対象の県名: {PREFECTURES.get(pref_code, '不明')}")
    print(f"基数: {total}")
    print(f"取得済の件数: {stats['success']}")
    print(f"取得不可の件数: {stats['error_nodata'] + stats['error_network']} (データなし:{stats['error_nodata']}, 通信エラー:{stats['error_network']})")
    print(f"今回サーバーに問い合わせた回数: {stats['api_calls']}")
    print(f"キャッシュから読んだ回数: {stats['cache_hits']}")
    print(f"保存先のファイル名: {output_file.name}")
    
    if stats['error_network_ids']:
        print(f"通信エラーID: {', '.join(stats['error_network_ids'])}")
    if stats['error_nodata_ids']:
        print(f"データなしID: {', '.join(stats['error_nodata_ids'])}")

def get_filenames(pref, target, base_dir=PROJECT_ROOT / "data" / "processed"):
    if target == "points":
        return base_dir / f"points_{pref}.csv", base_dir / f"elevation_points_{pref}.csv"
    else:
        return base_dir / f"monuments_{pref}.csv", base_dir / f"elevation_{pref}.csv"

def main():
    parser = argparse.ArgumentParser(description='標高・傾斜の取得')
    parser.add_argument('--pref', type=str, required=True, help='県コード (01-47)')
    parser.add_argument('--target', type=str, choices=['monuments', 'points'], default='monuments', help='処理対象')
    args = parser.parse_args()
    
    pref_code = args.pref
    if pref_code == "all" or pref_code not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)
        
    input_file, output_file = get_filenames(pref_code, args.target)
    if not input_file.exists():
        if args.target == "points":
            print(f"先に python src/make_comparison_points.py --pref {pref_code} を実行してください")
        else:
            print(f"先に python src/load_monuments.py --pref {pref_code} を実行してください")
        sys.exit(1)
        
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig', dtype={'ID': str})
    except Exception as e:
        print(f"エラー: CSVの読み込みに失敗しました: {e}")
        sys.exit(1)
        
    cache_dir = PROJECT_ROOT / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    process_monuments(df, pref_code, cache_dir, output_file)

if __name__ == "__main__":
    main()
