import argparse
import sys
import datetime
import math
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import nearest_points

PROJECT_ROOT = Path(__file__).parent.parent

# 河川から遠すぎる場合は対象外とする距離（m）
MAX_RIVER_DIST_M = 1000
# 河川最近点から碑の方向へずらして標高を調べる距離（m）
BANK_OFFSETS_M = [5, 10, 20, 30, 50, 100]
# 水際（最初に精しい値が出た地点）から、何mまでの範囲で最低値を選ぶか
WATER_EDGE_WINDOW_M = 20

def make_bank_points(river_xy, monument_xy, dist_m, offsets):
    """
    平面直角座標（m）で、河川最近点 P から碑 M の方向へ、offsets の各距離だけ進んだ点の一覧を返す。
    距離が dist_m 以上のものは含めない。
    """
    pts = []
    # 常に0（最近点そのもの）は含める
    pts.append((0, Point(river_xy.x, river_xy.y)))
    
    if dist_m <= 0:
        return pts
        
    dx = monument_xy.x - river_xy.x
    dy = monument_xy.y - river_xy.y
    length = math.hypot(dx, dy)
    if length == 0:
        return pts
    ux = dx / length
    uy = dy / length
    
    for offset in offsets:
        if offset >= dist_m:
            break
        nx = river_xy.x + ux * offset
        ny = river_xy.y + uy * offset
        pts.append((offset, Point(nx, ny)))
        
    return pts

def choose_bank_elevation(results, window_m=WATER_EDGE_WINDOW_M):
    """
    results: list of (offset, elevation, hsrc, status, lat, lon)
    """
    has_comm_error = any(r[3] == "通信エラー" for r in results)
    if has_comm_error:
        return None, None, None, None, "高さの差 取得不可（通信エラー）"
        
    detailed_results = []
    for r in results:
        offset, elev, hsrc, status, lat, lon = r
        if elev != "-----" and not pd.isna(elev):
            try:
                elev_val = float(elev)
                hsrc_str = str(hsrc) if pd.notna(hsrc) else ""
                if not hsrc_str.startswith("10m"):
                    detailed_results.append((offset, elev_val, hsrc_str, lat, lon))
            except ValueError:
                pass
                
    if detailed_results:
        # ずらし距離が最も小さい精しい値の地点のずらし距離を d0 とする
        d0 = min(detailed_results, key=lambda x: x[0])[0]
        # ずらし距離が d0 + window_m 以下のものの中で最も低い値を採用
        candidates = [r for r in detailed_results if r[0] <= d0 + window_m]
        best = min(candidates, key=lambda x: x[1])
        return best[1], best[2], best[3], best[4], "取得済"
        
    p0_result = next((r for r in results if r[0] == 0), results[0])
    p0_elev = p0_result[1]
    p0_hsrc = p0_result[2]
    p0_lat = p0_result[4]
    p0_lon = p0_result[5]
    
    if p0_elev != "-----" and not pd.isna(p0_elev):
        try:
            elev_val = float(p0_elev)
            hsrc_str = str(p0_hsrc) if pd.notna(p0_hsrc) else ""
            return elev_val, hsrc_str, p0_lat, p0_lon, "取得済（参考値：10mメッシュ）"
        except ValueError:
            pass
            
    return None, None, None, None, "高さの差 取得不可（河川の標高なし）"

try:
    from src.prefectures import PREFECTURES, EPSG_CODES
    from src.add_elevation import get_elevation_with_cache, load_cache, fetch_elevation_api, sleep_func
except ImportError:
    from prefectures import PREFECTURES, EPSG_CODES
    from add_elevation import get_elevation_with_cache, load_cache, fetch_elevation_api, sleep_func

def read_line_shapefile(shp_path):
    gdf = gpd.read_file(shp_path, encoding="cp932")
    gdf.set_crs("EPSG:4612", inplace=True)
    return gdf

def find_shapefile(base_dir, pattern, pref_name):
    """
    指定されたパターンに一致するシェープファイルを探す。
    複数見つかった場合はエラーにして止める。
    """
    files = list(base_dir.glob(pattern))
    if not files:
        return None
    if len(files) > 1:
        print(f"エラー: {pref_name} のファイルが複数見つかりました。どれを使うか決めてください。")
        for f in files:
            print(f"  - {f}")
        sys.exit(1)
    return files[0]

def calc_distance_and_nearest(monument_geom, lines_gdf):
    if lines_gdf is None or lines_gdf.empty:
        return None, None, None

    temp_gdf = lines_gdf.copy()
    temp_gdf['temp_id'] = range(len(temp_gdf))
    
    monument_gdf = gpd.GeoDataFrame(geometry=[monument_geom], crs=lines_gdf.crs)
    nearest = gpd.sjoin_nearest(monument_gdf, temp_gdf, distance_col="dist")
    
    if nearest.empty:
        return None, None, None
        
    nearest_row = nearest.iloc[0]
    line_geom = temp_gdf.loc[nearest_row['temp_id'], 'geometry']
    dist = nearest_row['dist']
    
    _, p2 = nearest_points(monument_geom, line_geom)
    
    return nearest_row, dist, p2

def process_river_coast(pref_code, monuments_df, elevation_df, rivers_shp, coast_shp, epsg_code, cache_dir, out_file, fetch_func, sleep_fn, max_river_dist_m=MAX_RIVER_DIST_M, bank_offsets_m=BANK_OFFSETS_M, water_edge_window_m=WATER_EDGE_WINDOW_M):
    epsg_crs = f"EPSG:{epsg_code}"
    
    monuments_df['geometry'] = monuments_df.apply(lambda row: Point(float(row['経度']), float(row['緯度'])), axis=1)
    monuments_gdf = gpd.GeoDataFrame(monuments_df, geometry='geometry', crs="EPSG:6668")
    monuments_gdf = monuments_gdf.to_crs(epsg_crs)
    
    elevation_dict = dict(zip(elevation_df['ID'], elevation_df['標高_m']))
    
    try:
        rivers_gdf = read_line_shapefile(rivers_shp)
        rivers_gdf = rivers_gdf.to_crs(epsg_crs)
        named_rivers_gdf = rivers_gdf[rivers_gdf['W05_004'] != '名称不明'].copy()
        named_rivers_gdf.reset_index(drop=True, inplace=True)
    except Exception as e:
        print(f"エラー: 河川ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)
        
    coast_gdf = None
    if coast_shp:
        try:
            coast_gdf = read_line_shapefile(coast_shp)
            coast_gdf = coast_gdf.to_crs(epsg_crs)
        except Exception as e:
            print(f"エラー: 海岸線ファイルの読み込みに失敗しました: {e}")
            sys.exit(1)
            
    cache_file = cache_dir / "elevation_cache.csv"
    cache_df = load_cache(cache_file)
    
    stats = {
        'api_calls': 0, 'cache_hits': 0, 
        'river_status_counts': {}, 'river_minus': 0,
        'river_unknown_name': 0, 'coast_nodata': 0,
        'river_named_separately': 0
    }
    
    results = []
    total = len(monuments_gdf)
    
    print(f"処理を開始します（全 {total} 件）")
    
    try:
        for idx, row in monuments_gdf.iterrows():
            mon_id = row['ID']
            name = row['碑名']
            mon_lat = float(row['緯度'])
            mon_lon = float(row['経度'])
            mon_elev = elevation_dict.get(mon_id)
            if pd.isna(mon_elev):
                mon_elev = None
                
            mon_geom = row['geometry']
            
            river_row, river_dist, river_nearest_pt = calc_distance_and_nearest(mon_geom, rivers_gdf)
            river_name = river_row['W05_004'] if river_row is not None else None
            river_code = str(river_row['W05_002']) if river_row is not None else None
            
            if river_dist is not None:
                river_dist_rounded = int(round(river_dist))
            else:
                river_dist_rounded = None

            named_river_name = None
            named_river_code = None
            named_river_dist_rounded = None
            
            if river_name == "名称不明":
                stats['river_unknown_name'] += 1
                named_river_row, named_river_dist, _ = calc_distance_and_nearest(mon_geom, named_rivers_gdf)
                if named_river_row is not None:
                    named_river_name = named_river_row['W05_004']
                    named_river_code = str(named_river_row['W05_002'])
                    named_river_dist_rounded = int(round(named_river_dist))
                    stats['river_named_separately'] += 1
            else:
                named_river_name = river_name
                named_river_code = river_code
                named_river_dist_rounded = river_dist_rounded
                
            river_lat_wgs = None
            river_lon_wgs = None
            
            bank_elev = None
            bank_hsrc = None
            bank_lat = None
            bank_lon = None
            height_diff = None
            river_status = "取得済"
            
            if river_dist_rounded is not None and river_dist_rounded > max_river_dist_m:
                river_status = "高さの差 対象外（河川まで1000m超）"
                if river_nearest_pt is not None:
                    pt_gdf = gpd.GeoDataFrame(geometry=[river_nearest_pt], crs=epsg_crs)
                    pt_gdf = pt_gdf.to_crs("EPSG:6668")
                    river_lat_wgs = round(pt_gdf.geometry.y.iloc[0], 6)
                    river_lon_wgs = round(pt_gdf.geometry.x.iloc[0], 6)
            elif river_nearest_pt is not None:
                # 河川最近点の緯度経度を計算して保持
                pt_gdf_p = gpd.GeoDataFrame(geometry=[river_nearest_pt], crs=epsg_crs)
                pt_gdf_p = pt_gdf_p.to_crs("EPSG:6668")
                river_lat_wgs = round(pt_gdf_p.geometry.y.iloc[0], 6)
                river_lon_wgs = round(pt_gdf_p.geometry.x.iloc[0], 6)
                
                bank_pts = make_bank_points(river_nearest_pt, mon_geom, river_dist, bank_offsets_m)
                bank_results = []
                for offset, pt in bank_pts:
                    pt_gdf = gpd.GeoDataFrame(geometry=[pt], crs=epsg_crs)
                    pt_gdf = pt_gdf.to_crs("EPSG:6668")
                    plat = round(pt_gdf.geometry.y.iloc[0], 6)
                    plon = round(pt_gdf.geometry.x.iloc[0], 6)
                    
                    elev_val, hsrc_val, status = get_elevation_with_cache(
                        plat, plon, cache_df, cache_file, fetch_func, sleep_fn, stats
                    )
                    bank_results.append((offset, elev_val, hsrc_val, status, plat, plon))
                    
                c_elev, c_hsrc, c_lat, c_lon, river_status = choose_bank_elevation(bank_results, window_m=water_edge_window_m)
                
                if river_status in ("取得済", "取得済（参考値：10mメッシュ）"):
                    if mon_elev is None:
                        river_status = "高さの差 取得不可（碑の標高なし）"
                    else:
                        bank_elev = c_elev
                        bank_hsrc = c_hsrc
                        bank_lat = c_lat
                        bank_lon = c_lon
                        height_diff = round(mon_elev - bank_elev, 1)
                        if height_diff < 0:
                            stats['river_minus'] += 1
            else:
                river_status = "高さの差 取得不可（河川の標高なし）"
                
            stats['river_status_counts'][river_status] = stats['river_status_counts'].get(river_status, 0) + 1
            
            coast_dist_rounded = None
            coast_status = "取得済"
            if coast_gdf is not None:
                _, coast_dist, _ = calc_distance_and_nearest(mon_geom, coast_gdf)
                if coast_dist is not None:
                    coast_dist_rounded = int(round(coast_dist))
            else:
                coast_status = "データなし"
                stats['coast_nodata'] += 1
                
            results.append({
                'ID': mon_id,
                '碑名': name,
                '緯度': mon_lat,
                '経度': mon_lon,
                '最寄り河川名': river_name,
                '河川コード': river_code,
                '河川までの距離_m': river_dist_rounded,
                '河川最近点_緯度': river_lat_wgs,
                '河川最近点_経度': river_lon_wgs,
                '名前のある最寄り河川名': named_river_name,
                '名前のある最寄り河川コード': named_river_code,
                '名前のある河川までの距離_m': named_river_dist_rounded,
                '河川側の標高_m': bank_elev,
                '河川側の標高_種別': bank_hsrc,
                '河川側の標高_緯度': bank_lat,
                '河川側の標高_経度': bank_lon,
                '碑の標高_m': mon_elev,
                '河川との高さの差_m': height_diff,
                '河川_状態': river_status,
                '海岸までの距離_m': coast_dist_rounded,
                '海岸_状態': coast_status,
                '取得日': datetime.date.today().strftime("%Y-%m-%d")
            })
            
            hd_str = f"{height_diff:+.1f}m" if height_diff is not None else "取得不可"
            rd_str = f"{river_dist_rounded:,}m" if river_dist_rounded is not None else "取得不可"
            cd_str = f"{coast_dist_rounded:,}m" if coast_dist_rounded is not None else "データなし"
            
            display_status = ""
            if river_status == "取得済（参考値：10mメッシュ）":
                display_status = "（参考値）"
            elif river_status == "高さの差 対象外（河川まで1000m超）":
                display_status = "対象外"
                
            print(f"{idx+1}/{total} {mon_id} 河川 {river_name} {rd_str} 高さの差 {hd_str}{display_status} 海岸 {cd_str}")
            
    except KeyboardInterrupt:
        print("\n中断しました。もう一度実行すると続きから再開します。")
        sys.exit(0)
        
    res_df = pd.DataFrame(results)
    res_df = res_df.sort_values('ID')
    res_df.to_csv(out_file, index=False, encoding='utf-8-sig')
    
    print("-" * 30)
    print(f"対象の県名: {PREFECTURES.get(pref_code, '不明')}")
    print(f"基数: {total}")
    print("河川_状態の内訳:")
    status_types = [
        "取得済",
        "取得済（参考値：10mメッシュ）",
        "高さの差 対象外（河川まで1000m超）",
        "高さの差 取得不可（碑の標高なし）",
        "高さの差 取得不可（河川の標高なし）",
        "高さの差 取得不可（通信エラー）"
    ]
    for st in status_types:
        count = stats['river_status_counts'].get(st, 0)
        print(f"  {st}: {count}")
    print(f"高さの差がマイナスの件数: {stats['river_minus']}")
    print(f"河川名が「名称不明」の件数: {stats['river_unknown_name']}")
    print(f"最寄りが名称不明で、名前のある河川を別に記録した件数: {stats['river_named_separately']}")
    print(f"海岸「データなし」の件数: {stats['coast_nodata']}")
    print(f"今回サーバーに問い合わせた回数: {stats['api_calls']}")
    print(f"キャッシュから読んだ回数: {stats['cache_hits']}")
    print(f"保存先のファイル名: {out_file.name}")

def get_filenames(pref, target, base_dir=PROJECT_ROOT / "data" / "processed"):
    if target == "points":
        return base_dir / f"points_{pref}.csv", base_dir / f"elevation_points_{pref}.csv", base_dir / f"river_coast_points_{pref}.csv"
    else:
        return base_dir / f"monuments_{pref}.csv", base_dir / f"elevation_{pref}.csv", base_dir / f"river_coast_{pref}.csv"

def main():
    parser = argparse.ArgumentParser(description='河川・海岸線までの距離計算')
    parser.add_argument('--pref', type=str, required=True, help='県コード (01-47)')
    parser.add_argument('--target', type=str, choices=['monuments', 'points'], default='monuments', help='処理対象')
    args = parser.parse_args()
    
    pref_code = args.pref
    if pref_code == "all" or pref_code not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)
        
    if pref_code not in EPSG_CODES:
        print("この県の座標系は未設定です")
        sys.exit(1)
        
    epsg_code = EPSG_CODES[pref_code]
    
    monuments_file, elevation_file, output_file = get_filenames(pref_code, args.target)
    if not monuments_file.exists():
        if args.target == "points":
            print(f"先に python src/make_comparison_points.py --pref {pref_code} を実行してください")
        else:
            print(f"先に python src/load_monuments.py --pref {pref_code} を実行してください")
        sys.exit(1)
        
    if not elevation_file.exists():
        print(f"先に python src/add_elevation.py --pref {pref_code} --target {args.target} を実行してください")
        sys.exit(1)
        
    monuments_df = pd.read_csv(monuments_file, encoding='utf-8-sig', dtype={'ID': str})
    elevation_df = pd.read_csv(elevation_file, encoding='utf-8-sig', dtype={'ID': str})
    
    pref_name = PREFECTURES[pref_code]
    
    rivers_dir = PROJECT_ROOT / "data" / "raw" / "rivers"
    river_pattern = f"W05-*_{pref_code}_GML/*_Stream.shp"
    rivers_shp = find_shapefile(rivers_dir, river_pattern, pref_name)
    if not rivers_shp:
        print(f"河川データ（国土数値情報 W05）の {pref_name} 分を data/raw/rivers/ に置いてください")
        sys.exit(1)
        
    coast_dir = PROJECT_ROOT / "data" / "raw" / "coastline"
    coast_pattern = f"C23-*_{pref_code}_GML/*_Coastline.shp"
    coast_shp = find_shapefile(coast_dir, coast_pattern, pref_name)
    if not coast_shp:
        print("海岸線ファイルが見つかりません。全件の海岸を「データなし」として処理します。")
        
    cache_dir = PROJECT_ROOT / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    process_river_coast(
        pref_code, monuments_df, elevation_df, rivers_shp, coast_shp, epsg_code, 
        cache_dir, output_file, fetch_elevation_api, sleep_func
    )

if __name__ == "__main__":
    main()
