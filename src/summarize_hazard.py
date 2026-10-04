# -*- coding: utf-8 -*-
import argparse
import sys
import pandas as pd
from pathlib import Path

try:
    from src.prefectures import PREFECTURES
    from src.summarize import extract_relocated
    from src.hazard_layers import SHINSUI_3M_IJOU
except ImportError:
    from prefectures import PREFECTURES
    from summarize import extract_relocated
    from hazard_layers import SHINSUI_3M_IJOU

def get_project_root():
    return Path(__file__).resolve().parent.parent

def check_files(pref, base_dir=None):
    """必要な入力ファイルが揃っているか確認し、不足があればエラーを出して終了する"""
    if base_dir is None:
        base_dir = get_project_root() / "data" / "processed"
    else:
        base_dir = Path(base_dir)
        
    missing = []
    
    m_main = base_dir / f"monuments_{pref}.csv"
    m_haz = base_dir / f"hazard_{pref}.csv"
    p_main = base_dir / f"points_{pref}.csv"
    p_haz = base_dir / f"hazard_points_{pref}.csv"
    
    if not m_main.exists(): missing.append((m_main, f"python src/load_monuments.py --pref {pref}"))
    if not m_haz.exists(): missing.append((m_haz, f"python src/add_hazard.py --pref {pref}"))
    if not p_main.exists(): missing.append((p_main, f"python src/make_comparison_points.py --pref {pref}"))
    if not p_haz.exists(): missing.append((p_haz, f"python src/add_hazard.py --pref {pref} --target points"))
    
    if missing:
        for file, cmd in missing:
            print(f"ファイルが見つかりません: {file.name}")
            print(f"先に実行してください: {cmd}")
        sys.exit(1)
    
    return m_main, m_haz, p_main, p_haz

def calc_hazard_stats(df, hazard_prefix, count_3m):
    """データフレームから指定されたハザードの区域内・取得不可・3m以上の件数と割合を計算する"""
    status_col = f"{hazard_prefix}状態"
    depth_col = f"{hazard_prefix}浸水深"
    
    total = 0
    in_area = 0
    not_acquired = 0
    over_3m = 0
    
    for _, row in df.iterrows():
        status = str(row.get(status_col, ''))
        if status in ('区域内', '区域外'):
            total += 1
            if status == '区域内':
                in_area += 1
        elif status == '取得不可':
            not_acquired += 1
            
        if count_3m and status == '区域内':
            depth = str(row.get(depth_col, ''))
            if depth in SHINSUI_3M_IJOU:
                over_3m += 1
                
    in_area_ratio = round(in_area / total, 3) if total > 0 else ''
    if count_3m:
        over_3m_ratio = round(over_3m / total, 3) if total > 0 else ''
    else:
        over_3m = ''
        over_3m_ratio = ''
        
    return total, not_acquired, in_area, in_area_ratio, over_3m, over_3m_ratio

def summarize(pref, base_dir=None, out_dir=None):
    """ハザードの集計を行い、CSVに出力して結果を画面に表示する"""
    if base_dir is None:
        base_dir = get_project_root() / "data" / "processed"
    if out_dir is None:
        out_dir = get_project_root() / "output"
        
    m_main_path, m_haz_path, p_main_path, p_haz_path = check_files(pref, base_dir)
    
    m_main = pd.read_csv(m_main_path, dtype={'ID': str}, encoding='utf-8-sig')
    m_haz = pd.read_csv(m_haz_path, dtype={'ID': str}, encoding='utf-8-sig')
    p_main = pd.read_csv(p_main_path, dtype={'ID': str, '元の碑ID': str}, encoding='utf-8-sig')
    p_haz = pd.read_csv(p_haz_path, dtype={'ID': str}, encoding='utf-8-sig')
    
    drop_cols_m = [c for c in ['碑名', '緯度', '経度'] if c in m_haz.columns]
    m_haz = m_haz.drop(columns=drop_cols_m)
    
    drop_cols_p = [c for c in ['碑名', '緯度', '経度', '元の碑ID'] if c in p_haz.columns]
    p_haz = p_haz.drop(columns=drop_cols_p)

    mon = pd.merge(m_main, m_haz, on='ID', how='inner')
    pt = pd.merge(p_main, p_haz, on='ID', how='inner')
    
    ranges = ['全碑', '移転碑を除く']
    disaster_types = ['全種別', '洪水', '地震', '津波', '土砂災害', '高潮', '火山災害', 'その他']
    hazards = [
        ('洪水（想定最大規模）', '洪水_', True),
        ('津波', '津波_', True),
        ('高潮', '高潮_', True),
        ('土砂災害', '土砂_', False)
    ]
    
    summary = []
    print_info = {}
    
    for r in ranges:
        if r == '全碑':
            m_df = mon
            p_df = pt
        else:
            relocated_df = extract_relocated(m_main)
            relocated_ids = relocated_df['ID'].tolist()
            m_df = mon[~mon['ID'].isin(relocated_ids)]
            p_df = pt[~pt['元の碑ID'].isin(relocated_ids)]
            
        print_info[f"{r}_m_count"] = len(m_df)
        print_info[f"{r}_p_count"] = len(p_df)
        
        for dt in disaster_types:
            if dt == '全種別':
                m_sub = m_df
                p_sub = p_df
            else:
                col = f"種別_{dt}"
                if col in m_df.columns:
                    m_sub = m_df[m_df[col] == 1]
                    p_sub = p_df[p_df[col] == 1]
                else:
                    m_sub = pd.DataFrame(columns=m_df.columns)
                    p_sub = pd.DataFrame(columns=p_df.columns)
                    
            if len(m_sub) == 0:
                continue
                
            for h_name, h_prefix, count_3m in hazards:
                m_total, m_na, m_in, m_in_r, m_3m, m_3m_r = calc_hazard_stats(m_sub, h_prefix, count_3m)
                p_total, p_na, p_in, p_in_r, p_3m, p_3m_r = calc_hazard_stats(p_sub, h_prefix, count_3m)
                
                summary.append([
                    r, dt, h_name,
                    m_total, m_na, m_in, m_in_r, m_3m, m_3m_r,
                    p_total, p_na, p_in, p_in_r, p_3m, p_3m_r
                ])
                
                if r == '全碑' and dt == '全種別':
                    if h_name not in print_info:
                        print_info[h_name] = {}
                    print_info[h_name]['m_in_r'] = m_in_r
                    print_info[h_name]['m_3m_r'] = m_3m_r
                    print_info[h_name]['p_in_r'] = p_in_r
                    print_info[h_name]['p_3m_r'] = p_3m_r
                    
                    if 'm_na_total' not in print_info:
                        print_info['m_na_total'] = 0
                        print_info['p_na_total'] = 0
                    print_info['m_na_total'] += m_na
                    print_info['p_na_total'] += p_na
                    
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    out_file = out_dir / f"hazard_summary_{pref}.csv"
    
    cols = ['範囲', '災害種別', 'ハザード', 
            '碑_数', '碑_取得不可', '碑_区域内', '碑_区域内の割合', '碑_3m以上', '碑_3m以上の割合', 
            '比較地点_数', '比較地点_取得不可', '比較地点_区域内', '比較地点_区域内の割合', '比較地点_3m以上', '比較地点_3m以上の割合']
    
    df_out = pd.DataFrame(summary, columns=cols)
    with open(out_file, 'w', encoding='utf-8-sig', newline='') as f:
        df_out.to_csv(f, index=False)
        f.write("注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。\n")
        f.write("注：想定区域との重なりを示すもので、危険度の判定ではありません。出典：ハザードマップポータルサイト（加工して作成）\n")
        
    print(f"ハザード区域との重なりの集計：{PREFECTURES[pref]}（{pref}）")
    print(f"碑：全碑 {print_info['全碑_m_count']}基／移転碑を除く {print_info['移転碑を除く_m_count']}基　比較地点：全碑 {print_info['全碑_p_count']}点／移転碑を除く {print_info['移転碑を除く_p_count']}点")
    print("全碑・全種別の区域内の割合（かっこ内は浸水深3m以上の割合）")
    
    def fmt(val):
        return f"{val:.3f}" if val != '' else ''
        
    def fmt_both(in_r, r3m, has_3m):
        in_s = fmt(in_r)
        if has_3m:
            r3m_s = fmt(r3m)
            return f"{in_s}（{r3m_s}）"
        else:
            return in_s

    print(f"  洪水（想定最大規模）：碑 {fmt_both(print_info['洪水（想定最大規模）']['m_in_r'], print_info['洪水（想定最大規模）']['m_3m_r'], True)}／比較地点 {fmt_both(print_info['洪水（想定最大規模）']['p_in_r'], print_info['洪水（想定最大規模）']['p_3m_r'], True)}")
    print(f"  津波：碑 {fmt_both(print_info['津波']['m_in_r'], print_info['津波']['m_3m_r'], True)}／比較地点 {fmt_both(print_info['津波']['p_in_r'], print_info['津波']['p_3m_r'], True)}")
    print(f"  高潮：碑 {fmt_both(print_info['高潮']['m_in_r'], print_info['高潮']['m_3m_r'], True)}／比較地点 {fmt_both(print_info['高潮']['p_in_r'], print_info['高潮']['p_3m_r'], True)}")
    print(f"  土砂災害：碑 {fmt_both(print_info['土砂災害']['m_in_r'], '', False)}／比較地点 {fmt_both(print_info['土砂災害']['p_in_r'], '', False)}")
    print(f"取得不可：碑 {print_info['m_na_total']}件／比較地点 {print_info['p_na_total']}件")
    
    try:
        rel_path = out_file.relative_to(get_project_root())
    except ValueError:
        rel_path = out_file
    print(f"出力：{rel_path.as_posix()}")

def main(args=None):
    """コマンドライン引数をパースし、ハザードの集計処理を実行する"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--pref', type=str, required=True)
    parsed = parser.parse_args(args)
    pref = parsed.pref
    
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)
        
    summarize(pref)

if __name__ == "__main__":
    main()
