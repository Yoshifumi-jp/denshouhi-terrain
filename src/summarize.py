# -*- coding: utf-8 -*-
import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

try:
    from src.prefectures import PREFECTURES
except ImportError:
    from prefectures import PREFECTURES

PROJECT_ROOT = Path(__file__).parent.parent

# 災害種別列（元のファイルにあると想定）
DISASTER_TYPES = [
    "種別_洪水", "種別_地震", "種別_津波", "種別_土砂災害", "種別_高潮", "種別_火山災害", "種別_その他"
]

def tick_positions(positions):
    return [(positions[i] + positions[i+1]) / 2 for i in range(0, len(positions), 2)]

def set_jp_font():
    fonts = ["Yu Gothic", "Meiryo", "MS Gothic"]
    font_found = False
    for font in fonts:
        if any(f.name == font for f in fm.fontManager.ttflist):
            plt.rcParams['font.family'] = font
            font_found = True
            break
    if not font_found:
        print("警告: 日本語フォントが見つかりません。文字化けする可能性があります。")

def get_filenames(pref, target, base_dir=None):
    if base_dir is None:
        base_dir = PROJECT_ROOT / "data" / "processed"
    if target == "points":
        return {
            "main": base_dir / f"points_{pref}.csv",
            "elevation": base_dir / f"elevation_points_{pref}.csv",
            "river_coast": base_dir / f"river_coast_points_{pref}.csv",
            "landform": base_dir / f"landform_points_{pref}.csv"
        }
    else:
        return {
            "main": base_dir / f"monuments_{pref}.csv",
            "elevation": base_dir / f"elevation_{pref}.csv",
            "river_coast": base_dir / f"river_coast_{pref}.csv",
            "landform": base_dir / f"landform_{pref}.csv"
        }

def check_files_exist(pref):
    missing_files = []
    
    monuments = get_filenames(pref, "monuments")
    if not monuments["main"].exists(): missing_files.append((monuments["main"], f"python src/load_monuments.py --pref {pref}"))
    if not monuments["elevation"].exists(): missing_files.append((monuments["elevation"], f"python src/add_elevation.py --pref {pref}"))
    if not monuments["river_coast"].exists(): missing_files.append((monuments["river_coast"], f"python src/add_river_coast.py --pref {pref}"))
    if not monuments["landform"].exists(): missing_files.append((monuments["landform"], f"python src/add_landform.py --pref {pref}"))
    
    points = get_filenames(pref, "points")
    if not points["main"].exists(): missing_files.append((points["main"], f"python src/make_comparison_points.py --pref {pref}"))
    if not points["elevation"].exists(): missing_files.append((points["elevation"], f"python src/add_elevation.py --pref {pref} --target points"))
    if not points["river_coast"].exists(): missing_files.append((points["river_coast"], f"python src/add_river_coast.py --pref {pref} --target points"))
    if not points["landform"].exists(): missing_files.append((points["landform"], f"python src/add_landform.py --pref {pref} --target points"))
    
    if missing_files:
        for file, cmd in missing_files:
            print(f"ファイルが見つかりません: {file.name}")
            print(f"先に実行してください: {cmd}")
        sys.exit(1)

def load_and_merge(pref):
    mon_files = get_filenames(pref, "monuments")
    mon_main = pd.read_csv(mon_files["main"], dtype={'ID': str}, encoding='utf-8-sig')
    mon_elev = pd.read_csv(mon_files["elevation"], dtype={'ID': str}, encoding='utf-8-sig')
    mon_rc = pd.read_csv(mon_files["river_coast"], dtype={'ID': str}, encoding='utf-8-sig')
    mon_lf = pd.read_csv(mon_files["landform"], dtype={'ID': str}, encoding='utf-8-sig')
    
    mon_merged = mon_main.merge(mon_elev[['ID', '標高_m', '傾斜_度', '取得状態']], on='ID', how='left')
    mon_merged = mon_merged.merge(mon_rc[['ID', '河川までの距離_m', '河川との高さの差_m', '河川_状態', '海岸までの距離_m', '海岸_状態']], on='ID', how='left')
    mon_merged = mon_merged.merge(mon_lf[['ID', '地形分類名', '地形分類コード', '地形分類_状態']], on='ID', how='left')
    
    pt_files = get_filenames(pref, "points")
    pt_main = pd.read_csv(pt_files["main"], dtype={'ID': str, '元の碑ID': str}, encoding='utf-8-sig')
    pt_elev = pd.read_csv(pt_files["elevation"], dtype={'ID': str}, encoding='utf-8-sig')
    pt_rc = pd.read_csv(pt_files["river_coast"], dtype={'ID': str}, encoding='utf-8-sig')
    pt_lf = pd.read_csv(pt_files["landform"], dtype={'ID': str}, encoding='utf-8-sig')
    
    pt_merged = pt_main.merge(pt_elev[['ID', '標高_m', '傾斜_度', '取得状態']], on='ID', how='left')
    pt_merged = pt_merged.merge(pt_rc[['ID', '河川までの距離_m', '河川との高さの差_m', '河川_状態', '海岸までの距離_m', '海岸_状態']], on='ID', how='left')
    pt_merged = pt_merged.merge(pt_lf[['ID', '地形分類名', '地形分類コード', '地形分類_状態']], on='ID', how='left')
    
    return mon_merged, pt_merged

def extract_relocated(mon_df):
    relocated = []
    for _, row in mon_df.iterrows():
        content = str(row.get('伝承内容', ''))
        if '移転' in content or '移設' in content:
            keyword = '移転' if '移転' in content else '移設'
            idx = content.find(keyword)
            start = max(0, idx - 30)
            end = min(len(content), idx + len(keyword) + 30)
            context = content[start:end]
            relocated.append({
                'ID': row['ID'],
                '碑名': row['碑名'],
                '所在地': row['所在地'],
                '該当語': keyword,
                '前後30字': context
            })
    return pd.DataFrame(relocated, columns=['ID', '碑名', '所在地', '該当語', '前後30字'])

def get_valid_series(df, indicator):
    if indicator == '標高_m':
        valid = df[df['取得状態'] == '取得済']
        return valid['標高_m'], df.shape[0] - valid.shape[0]
    elif indicator == '傾斜_度':
        valid = df[df['取得状態'] == '取得済']
        return valid['傾斜_度'], df.shape[0] - valid.shape[0]
    elif indicator == '河川までの距離_m':
        valid = df[df['河川までの距離_m'].notna()]
        return valid['河川までの距離_m'], df.shape[0] - valid.shape[0]
    elif indicator == '河川との高さの差_m':
        valid = df[df['河川_状態'] == '取得済']
        return valid['河川との高さの差_m'], df.shape[0] - valid.shape[0]
    elif indicator == '海岸までの距離_m':
        valid = df[df['海岸_状態'] == '取得済']
        return valid['海岸までの距離_m'], df.shape[0] - valid.shape[0]
    elif indicator == '地形分類名':
        valid = df[(df['地形分類_状態'] == '取得済') & (df['地形分類コード'].notna()) & (df['地形分類コード'] != '')]
        return valid['地形分類名'], df.shape[0] - valid.shape[0]
    return pd.Series(dtype=float), 0

def calc_stats(series):
    if series.empty:
        return np.nan, np.nan, np.nan
    return series.median(), series.quantile(0.25, interpolation='linear'), series.quantile(0.75, interpolation='linear')

def analyze_indicator(mon_subset, pt_subset, indicator):
    mon_vals, mon_exc = get_valid_series(mon_subset, indicator)
    mon_count = len(mon_vals)
    mon_med, mon_q1, mon_q3 = calc_stats(mon_vals)
    
    pt_vals, pt_exc = get_valid_series(pt_subset, indicator)
    pt_count = len(pt_vals)
    pt_med, pt_q1, pt_q3 = calc_stats(pt_vals)
    
    pairs_count = 0
    diffs = []
    
    valid_mon_ids = mon_vals.index
    for idx in valid_mon_ids:
        mon_id = mon_subset.loc[idx, 'ID']
        mon_val = mon_vals.loc[idx]
        
        pts_for_mon = pt_subset[pt_subset['元の碑ID'] == mon_id]
        pt_vals_for_mon, _ = get_valid_series(pts_for_mon, indicator)
        
        if len(pt_vals_for_mon) > 0:
            pt_med_for_mon = pt_vals_for_mon.median()
            diffs.append(mon_val - pt_med_for_mon)
            pairs_count += 1
            
    diff_med = np.median(diffs) if diffs else np.nan
    greater_ratio = sum(1 for d in diffs if d > 0) / pairs_count if pairs_count > 0 else np.nan
    
    return [
        mon_count, mon_exc, mon_med, mon_q1, mon_q3,
        pt_count, pt_exc, pt_med, pt_q1, pt_q3,
        pairs_count, diff_med, greater_ratio
    ], mon_vals, pt_vals

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pref', type=str, required=True)
    args = parser.parse_args()
    pref = args.pref
    
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)
        
    pref_name = PREFECTURES[pref]
    
    check_files_exist(pref)
    
    mon_df, pt_df = load_and_merge(pref)
    
    relocated_df = extract_relocated(mon_df)
    relocated_ids = relocated_df['ID'].tolist()
    
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    fig_dir = out_dir / "fig"
    fig_dir.mkdir(exist_ok=True)
    
    relocated_df.rename(columns={'前後30字': '伝承内容の該当箇所の前後30字'}, inplace=True)
    relocated_file = out_dir / f"relocated_{pref}.csv"
    relocated_df.to_csv(relocated_file, index=False, encoding='utf-8-sig')
    
    indicators = ['標高_m', '傾斜_度', '河川までの距離_m', '河川との高さの差_m', '海岸までの距離_m']
    
    summary_data = []
    landform_data = []
    
    plot_data = {ind: {} for ind in indicators}
    landform_plot_data = {}
    
    ranges = ['全碑', '移転碑を除く']
    disaster_types = ['全種別'] + DISASTER_TYPES
    
    total_mon_count = len(mon_df)
    total_pt_count = len(pt_df)
    ex_mon_count = len(mon_df[~mon_df['ID'].isin(relocated_ids)])
    ex_pt_count = len(pt_df[~pt_df['元の碑ID'].isin(relocated_ids)])
    
    exc_counts = {ind: {'mon': 0, 'pt': 0} for ind in indicators + ['地形分類名']}
    
    for r in ranges:
        if r == '全碑':
            m_df = mon_df
            p_df = pt_df
        else:
            m_df = mon_df[~mon_df['ID'].isin(relocated_ids)]
            p_df = pt_df[~pt_df['元の碑ID'].isin(relocated_ids)]
            
        for dt in disaster_types:
            if dt == '全種別':
                dt_name = '全種別'
                m_sub = m_df
                p_sub = p_df
            else:
                dt_name = dt.replace('種別_', '')
                m_sub = m_df[m_df[dt] == 1]
                p_sub = p_df[p_df[dt] == 1]
                
            for ind in indicators:
                stats, m_vals, p_vals = analyze_indicator(m_sub, p_sub, ind)
                row = [r, dt_name, ind] + stats
                summary_data.append(row)
                
                if r == '全碑' and dt == '全種別':
                    exc_counts[ind]['mon'] = stats[1]
                    exc_counts[ind]['pt'] = stats[6]
                
                if r == '全碑':
                    if dt not in plot_data[ind]:
                        plot_data[ind][dt] = {'mon': m_vals, 'pt': p_vals}
                        
            # 地形分類
            m_lf, m_lf_exc = get_valid_series(m_sub, '地形分類名')
            p_lf, p_lf_exc = get_valid_series(p_sub, '地形分類名')
            
            if r == '全碑' and dt == '全種別':
                exc_counts['地形分類名']['mon'] = m_lf_exc
                exc_counts['地形分類名']['pt'] = p_lf_exc
                lf_order = p_lf.value_counts().index.tolist()
                
            m_lf_counts = m_lf.value_counts()
            p_lf_counts = p_lf.value_counts()
            
            m_lf_total = len(m_lf)
            p_lf_total = len(p_lf)
            
            all_lfs = lf_order + [x for x in m_lf_counts.index if x not in lf_order] + [x for x in p_lf_counts.index if x not in lf_order]
            seen = set()
            unique_lfs = []
            for x in all_lfs:
                if x not in seen:
                    unique_lfs.append(x)
                    seen.add(x)
                    
            for lf in unique_lfs:
                m_c = m_lf_counts.get(lf, 0)
                p_c = p_lf_counts.get(lf, 0)
                m_r = m_c / m_lf_total if m_lf_total > 0 else 0
                p_r = p_c / p_lf_total if p_lf_total > 0 else 0
                landform_data.append([r, dt_name, lf, m_c, m_r, p_c, p_r])
                
            if r == '全碑' and dt == '全種別':
                landform_plot_data = {'order': unique_lfs, 'mon': m_lf_counts, 'pt': p_lf_counts, 'mon_total': m_lf_total, 'pt_total': p_lf_total}

    # Summary CSV出力
    summary_cols = ['範囲', '災害種別', '指標', '碑_数', '碑_除外数', '碑_中央値', '碑_第1四分位', '碑_第3四分位', 
                    '比較地点_数', '比較地点_除外数', '比較地点_中央値', '比較地点_第1四分位', '比較地点_第3四分位',
                    '組の数', '差の中央値', '碑の方が大きい割合']
    summary_df = pd.DataFrame(summary_data, columns=summary_cols)
    
    for col in ['碑_中央値', '碑_第1四分位', '碑_第3四分位', '比較地点_中央値', '比較地点_第1四分位', '比較地点_第3四分位', '差の中央値']:
        summary_df[col] = summary_df[col].round(2)
    summary_df['碑の方が大きい割合'] = summary_df['碑の方が大きい割合'].round(3)
    
    summary_file = out_dir / f"summary_{pref}.csv"
    with open(summary_file, 'w', encoding='utf-8-sig', newline='') as f:
        summary_df.to_csv(f, index=False)
        f.write("注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。\n")
    
    # Landform CSV出力
    lf_cols = ['範囲', '災害種別', '地形分類名', '碑_件数', '碑_割合', '比較地点_件数', '比較地点_割合']
    lf_df = pd.DataFrame(landform_data, columns=lf_cols)
    lf_df['碑_割合'] = lf_df['碑_割合'].round(3)
    lf_df['比較地点_割合'] = lf_df['比較地点_割合'].round(3)
    
    lf_file = out_dir / f"landform_{pref}.csv"
    with open(lf_file, 'w', encoding='utf-8-sig', newline='') as f:
        lf_df.to_csv(f, index=False)
        f.write("注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。\n")
    
    # グラフ作成
    set_jp_font()
    
    valid_dts = ['全種別']
    for dt in DISASTER_TYPES:
        if dt in mon_df.columns and mon_df[dt].sum() >= 5:
            valid_dts.append(dt)
            
    ind_filenames = {
        '標高_m': 'elevation',
        '傾斜_度': 'slope',
        '河川までの距離_m': 'river_dist',
        '河川との高さの差_m': 'river_height',
        '海岸までの距離_m': 'coast_dist'
    }
    
    footer_text = "出典：国土地理院（自然災害伝承碑、標高、地形分類）、国土数値情報（河川、海岸線）を加工して作成"
    
    for ind in indicators:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        positions = []
        data = []
        labels = []
        
        pos = 1
        for dt in valid_dts:
            m_v = plot_data[ind][dt]['mon'].dropna()
            p_v = plot_data[ind][dt]['pt'].dropna()
            
            data.append(m_v)
            data.append(p_v)
            positions.extend([pos, pos + 0.4])
            labels.append(dt.replace('種別_', ''))
            pos += 1.5
            
        if any(len(d) > 0 for d in data):
            bp = ax.boxplot(data, positions=positions, patch_artist=True, widths=0.3)
            
            for i, patch in enumerate(bp['boxes']):
                if i % 2 == 0:
                    patch.set_facecolor('lightblue')
                else:
                    patch.set_facecolor('lightgreen')
                    
            ax.plot([], [], color='lightblue', linewidth=8, label='碑')
            ax.plot([], [], color='lightgreen', linewidth=8, label='比較地点')
            ax.legend()
            
        ax.set_xticks(tick_positions(positions))
        ax.set_xticklabels(labels)
        ax.set_ylabel(ind)
        ax.set_title(f"{ind}の分布（{pref_name}）")
        
        plt.figtext(0.5, 0.01, footer_text, ha="center", fontsize=9)
        plt.tight_layout(rect=[0, 0.03, 1, 1])
        
        fname = fig_dir / f"box_{ind_filenames[ind]}_{pref}.png"
        plt.savefig(fname)
        plt.close(fig)
        
    fig, ax = plt.subplots(figsize=(10, 6))
    
    order = landform_plot_data['order']
    m_pcts = [landform_plot_data['mon'].get(x, 0) / landform_plot_data['mon_total'] * 100 if landform_plot_data['mon_total'] > 0 else 0 for x in order]
    p_pcts = [landform_plot_data['pt'].get(x, 0) / landform_plot_data['pt_total'] * 100 if landform_plot_data['pt_total'] > 0 else 0 for x in order]
    
    y = np.arange(len(order))
    height = 0.35
    
    if len(order) > 0:
        ax.barh(y - height/2, m_pcts, height, label='碑', color='lightblue')
        ax.barh(y + height/2, p_pcts, height, label='比較地点', color='lightgreen')
        
        ax.set_yticks(y)
        ax.set_yticklabels(order)
        ax.invert_yaxis()
        ax.set_xlabel('割合 (%)')
        ax.set_title(f"地形分類の構成比（{pref_name}・全種別）")
        ax.legend()
    
    plt.figtext(0.5, 0.01, footer_text, ha="center", fontsize=9)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    fname = fig_dir / f"bar_landform_{pref}.png"
    plt.savefig(fname)
    plt.close(fig)
    
    print(f"対象の県名: {pref_name}")
    print(f"碑の数: 全碑 {total_mon_count} / 移転碑を除く {ex_mon_count}")
    print(f"比較地点の数: 全碑 {total_pt_count} / 移転碑を除く {ex_pt_count}")
    print("移転碑:")
    for _, row in relocated_df.iterrows():
        print(f"  {row['ID']} {row['碑名']}")
        
    print("指標ごとの除外数（碑 / 比較地点）:")
    for ind in indicators + ['地形分類名']:
        print(f"  {ind}: {exc_counts[ind]['mon']} / {exc_counts[ind]['pt']}")
        
    print("出力ファイル:")
    print(f"  {summary_file.name}")
    print(f"  {lf_file.name}")
    print(f"  {relocated_file.name}")
    for ind in indicators:
        print(f"  box_{ind_filenames[ind]}_{pref}.png")
    print(f"  bar_landform_{pref}.png")

if __name__ == "__main__":
    main()
