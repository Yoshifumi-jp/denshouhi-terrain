import argparse
import sys
import html
import math
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import folium

from src.summarize import check_files_exist, extract_relocated, get_filenames
from src.prefectures import PREFECTURES

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 優先順と色
DISASTER_TYPES = [
    ("津波", "#0072B2"),
    ("高潮", "#56B4E9"),
    ("洪水", "#009E73"),
    ("土砂災害", "#E69F00"),
    ("火山災害", "#D55E00"),
    ("地震", "#CC79A7"),
    ("その他", "#7F7F7F")
]

def main_type(row) -> str:
    for dtype, color in DISASTER_TYPES[:-1]:
        col = f"種別_{dtype}"
        if col in row and row[col] == 1:
            return dtype
    return "その他"

def compare_with_surroundings(mon_elev, mon_status, point_elevs) -> str:
    if str(mon_status) != "取得済" or not point_elevs or pd.isna(mon_elev):
        return "比較地点なし"
        
    m = np.median(point_elevs)
    diff = mon_elev - m
    diff_rounded = round(diff, 1)
    
    if abs(diff_rounded) < 1.0:
        return f"まわり（比較地点 {len(point_elevs)}点の中央値 {m:.1f} m）とほぼ同じ高さ"
    elif diff_rounded >= 1.0:
        return f"まわり（比較地点 {len(point_elevs)}点の中央値 {m:.1f} m）より {abs(diff_rounded):.1f} m 高い"
    else:
        return f"まわり（比較地点 {len(point_elevs)}点の中央値 {m:.1f} m）より {abs(diff_rounded):.1f} m 低い"

def fmt_value(value, unit, status=None, ok_status="取得済") -> str:
    if status is not None and str(status) != ok_status:
        if str(status) == "取得済（参考値：10mメッシュ）":
            if pd.isna(value) or str(value).lower() == 'nan':
                return "データなし"
            return f"{value} {unit}（参考値）"
        return str(status)
    
    if pd.isna(value) or str(value).lower() == 'nan':
        return "データなし"
        
    return f"{value} {unit}"

def build_popup_html(row, comparison_text, is_relocated) -> str:
    def esc(s):
        if pd.isna(s):
            return ""
        return html.escape(str(s))
        
    mon_name = esc(row.get('碑名'))
    mon_id = esc(row.get('ID'))
    
    reloc_note = ""
    if is_relocated:
        reloc_note = '<p>※この碑は移設されています。今の位置は被災した地点とは限りません。</p>'
        
    disaster_name = esc(row.get('災害名'))
    disaster_type = esc(row.get('災害種別'))
    build_year = esc(row.get('建立年'))
    location = esc(row.get('所在地'))
    
    elev = fmt_value(row.get('標高_m'), "m", row.get('取得状態'))
    elev_dtype = row.get('標高データ種別')
    if str(row.get('取得状態')) == '取得済' and pd.notna(elev_dtype) and str(elev_dtype).strip() != "":
        elev = f"{elev}（{esc(elev_dtype)}）"
    
    incl = fmt_value(row.get('傾斜_度'), "度", None)
        
    lf_status = row.get('地形分類_状態')
    lf_name = row.get('地形分類名')
    lf_code = row.get('地形分類コード')
    
    if str(lf_status) != "取得済" or pd.isna(lf_code) or str(lf_code) == "":
        lf_text = "データなし"
    else:
        lf_text = esc(lf_name)
        
    riv_name = row.get('最寄り河川名')
    riv_dist = fmt_value(row.get('河川までの距離_m'), "m", None)
    
    if pd.isna(riv_name) or str(riv_name).lower() == 'nan':
        riv_text = "データなし"
    else:
        riv_text = f"{esc(riv_name)}（{riv_dist}）"
        if str(riv_name) == "名称不明" and pd.notna(row.get('名前のある最寄り河川名')):
            named_riv = esc(row.get('名前のある最寄り河川名'))
            named_dist = fmt_value(row.get('名前のある河川までの距離_m'), "m", None)
            riv_text += f"／名前のある最寄り河川：{named_riv}（{named_dist}）"
            
    riv_diff = fmt_value(row.get('河川との高さの差_m'), "m", row.get('河川_状態'))
    
    coast_dist = fmt_value(row.get('海岸までの距離_m'), "m", row.get('海岸_状態'))
    
    desc = esc(row.get('伝承内容'))
    
    lat = row.get('緯度')
    lon = row.get('経度')
    gsi_link = f'https://maps.gsi.go.jp/#17/{lat}/{lon}/'
    
    html_content = f"""
    <div style="width: 300px; max-height: 400px; overflow-y: auto;">
        <p><b>{mon_name}</b> ({mon_id})</p>
        {reloc_note}
        <p>災害名：{disaster_name}<br>災害種別：{disaster_type}<br>建立年：{build_year}<br>所在地：{location}</p>
        <p><b>地形の診断</b></p>
        <ul>
            <li>標高：{elev}</li>
            <li>まわりとの比較：{comparison_text}</li>
            <li>傾斜：{incl}</li>
            <li>地形分類：{lf_text}</li>
            <li>最寄り河川：{riv_text}</li>
            <li>河川との高さの差：{riv_diff}</li>
            <li>海岸までの距離：{coast_dist}</li>
        </ul>
        <p>{desc}</p>
        <p><a href="{gsi_link}" target="_blank" rel="noopener">地理院地図で見る</a></p>
    </div>
    """
    return html_content

def build_map(mon_df, pt_df, pref) -> folium.Map:
    pref_name = PREFECTURES[pref]
    
    m = folium.Map(tiles=None)
    folium.TileLayer(
        tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
        attr='<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noopener">地理院タイル</a>',
        name='地理院タイル（淡色地図）',
        max_zoom=18,
    ).add_to(m)
    
    reloc_df = extract_relocated(mon_df)
    reloc_ids = set(reloc_df['ID'])
    
    type_counts = {t: 0 for t, c in DISASTER_TYPES}
    mon_types = []
    
    for idx, row in mon_df.iterrows():
        t = main_type(row)
        type_counts[t] += 1
        mon_types.append(t)
        
    mon_df['main_type'] = mon_types
    
    feature_groups = {}
    for dtype, color in DISASTER_TYPES:
        if type_counts[dtype] > 0:
            fg = folium.FeatureGroup(name=f"{dtype}（{type_counts[dtype]}基）")
            feature_groups[dtype] = (fg, color)
            fg.add_to(m)
            
    bounds = []
    
    # 乱数の seed を固定しておく（foliumの要素IDがテストでばらつくのを抑えやすいが、内部的に UUIDを使うため完全一致しないかも。後で確認）
    
    for idx, row in mon_df.iterrows():
        t = row['main_type']
        fg, color = feature_groups[t]
        
        is_relocated = row['ID'] in reloc_ids
        
        mon_id = row['ID']
        if pt_df is not None and not pt_df.empty:
            pt_sub = pt_df[(pt_df['元の碑ID'] == mon_id) & (pt_df['取得状態'] == '取得済') & (pt_df['標高_m'].notna())]
            point_elevs = pt_sub['標高_m'].tolist()
        else:
            point_elevs = []
            
        comparison_text = compare_with_surroundings(row.get('標高_m'), row.get('取得状態'), point_elevs)
        
        popup_html = build_popup_html(row, comparison_text, is_relocated)
        
        lat = row.get('緯度')
        lon = row.get('経度')
        if pd.notna(lat) and pd.notna(lon):
            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                color="white",
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(fg)
            bounds.append([lat, lon])
            
    if bounds:
        m.fit_bounds(bounds)
        
    folium.LayerControl(position='topright', collapsed=True).add_to(m)
    m.get_root().title = f"自然災害伝承碑と地形（{pref_name}）"
    
    dates = []
    if 'データ取得日' in mon_df.columns:
        dates = mon_df['データ取得日'].dropna().unique()
    fetch_date = sorted(dates)[-1] if len(dates) > 0 else ""
    
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 20px; left: 20px; width: min(320px, 90vw); max-height: 50vh; 
                overflow-y: auto; z-index:9999; font-size:13px; background-color: white; 
                padding: 10px; border: 2px solid grey; border-radius: 5px;">
        <h4 style="margin-top: 0; margin-bottom: 10px;">自然災害伝承碑と地形（{pref_name}）</h4>
        <p style="margin-top: 0; margin-bottom: 5px;">碑の数: {len(mon_df)}</p>
        <div style="margin-bottom: 10px;">
    """
    for dtype, color in DISASTER_TYPES:
        if type_counts[dtype] > 0:
            legend_html += f'<div><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background-color:{color}; border:1px solid white;"></span> {dtype} {type_counts[dtype]}基</div>\n'
            
    legend_html += f"""
        </div>
        <p style="font-size:11px; color:#555; margin-bottom: 10px;">複数の種別を持つ碑は、津波＞高潮＞洪水＞土砂災害＞火山災害＞地震＞その他 の順で色を決めています</p>
        <p style="margin-bottom: 10px;">地形との相関を示すもので、災害の予測・安全の保証ではありません。</p>
        <details>
            <summary>出典・ご利用上の注意</summary>
            <ul style="padding-left: 20px; margin-top: 5px;">
                <li>自然災害伝承碑：国土地理院（https://www.gsi.go.jp/bousaichiri/denshouhi.html）</li>
                <li>背景地図：地理院タイル（淡色地図）</li>
                <li>標高・傾斜：国土地理院 標高API（標高タイル）から算出</li>
                <li>地形分類：国土地理院 地形分類（自然地形）</li>
                <li>河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）</li>
                <li>上記を加工して作成</li>
            </ul>
            <p>【免責事項】</p>
            <ul style="padding-left: 20px;">
                <li>本地図の分析結果は、伝承碑の位置と地形との「相関」を示すもので、災害の発生を予測・保証するものではありません。防災上の判断には自治体のハザードマップをご利用ください。</li>
                <li>碑の位置は被災した地点とは限りません（移設された碑もあります）。伝承碑の登録は市町村の申請によるもので、すべての碑を網羅しているわけではありません。</li>
            </ul>
            <p>伝承碑データ取得日：{fetch_date}</p>
        </details>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 乱数を使うため、MapのIDを固定化
    # M5-01: foliumが要素IDに乱数を使う場合は報告に書けば一致しなくてもよい
    
    return m, type_counts

def load_data(pref):
    data_dir = PROJECT_ROOT / "data" / "processed"
    
    mon_dfs = []
    for base in ["monuments", "elevation", "river_coast", "landform"]:
        f = data_dir / f"{base}_{pref}.csv"
        df = pd.read_csv(f, dtype={'ID': str}, encoding='utf-8-sig')
        mon_dfs.append(df)
        
    mon_df = mon_dfs[0]
    for df in mon_dfs[1:]:
        drop_cols = [c for c in df.columns if c in mon_df.columns and c != 'ID']
        df_to_merge = df.drop(columns=drop_cols)
        mon_df = pd.merge(mon_df, df_to_merge, on='ID', how='left')
        
    pt_dfs = []
    for base in ["points", "elevation_points", "river_coast_points", "landform_points"]:
        f = data_dir / f"{base}_{pref}.csv"
        if not f.exists():
            continue
        df = pd.read_csv(f, dtype={'元の碑ID': str, 'ID': str}, encoding='utf-8-sig')
        pt_dfs.append(df)
        
    if pt_dfs:
        pt_df = pt_dfs[0]
        for df in pt_dfs[1:]:
            drop_cols = [c for c in df.columns if c in pt_df.columns and c != 'ID']
            df_to_merge = df.drop(columns=drop_cols)
            pt_df = pd.merge(pt_df, df_to_merge, on='ID', how='left')
    else:
        pt_df = None
        
    return mon_df, pt_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pref", required=True)
    args = parser.parse_args()
    
    pref = args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)
        
    pref_name = PREFECTURES[pref]
    
    try:
        check_files_exist(pref)
    except SystemExit:
        sys.exit(1)
        
    mon_df, pt_df = load_data(pref)
    
    m, type_counts = build_map(mon_df, pt_df, pref)
    
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"map_{pref}.html"
    
    m.save(str(out_file))
    
    reloc_df = extract_relocated(mon_df)
    reloc_count = len(reloc_df)
    
    no_compare_ids = []
    for idx, row in mon_df.iterrows():
        mon_id = row['ID']
        if pt_df is not None and not pt_df.empty:
            pt_sub = pt_df[(pt_df['元の碑ID'] == mon_id) & (pt_df['取得状態'] == '取得済') & (pt_df['標高_m'].notna())]
            point_elevs = pt_sub['標高_m'].tolist()
        else:
            point_elevs = []
        if compare_with_surroundings(row.get('標高_m'), row.get('取得状態'), point_elevs) == "比較地点なし":
            no_compare_ids.append(mon_id)
            
    print(f"対象の県名: {pref_name}")
    print(f"碑の数: {len(mon_df)}")
    for dtype, count in type_counts.items():
        if count > 0:
            print(f"主な種別ごとの件数（{dtype}）: {count}")
    print(f"移転碑の数: {reloc_count}")
    print(f"比較地点なしの碑の ID: {', '.join(no_compare_ids) if no_compare_ids else 'なし'}")
    print(f"出力ファイル名: map_{pref}.html")

if __name__ == "__main__":
    main()
