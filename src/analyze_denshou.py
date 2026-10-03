import argparse
import sys
import pandas as pd
import numpy as np
import unicodedata
import re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from src.prefectures import PREFECTURES
except ImportError:
    from prefectures import PREFECTURES

from src.summarize import set_jp_font, get_valid_series, calc_stats
from src.make_map import main_type

def parse_disasters(text):
    if pd.isna(text) or str(text).strip() == "":
        return []
    
    text = unicodedata.normalize('NFKC', str(text))
    results = []
    
    pattern = re.compile(r'\((\d{3,4})年')
    matches = list(pattern.finditer(text))
    
    last_end = 0
    for match in matches:
        start_idx = match.start()
        if start_idx < last_end:
            continue
            
        year = int(match.group(1))
        
        depth = 0
        close_idx = -1
        for i in range(start_idx, len(text)):
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
                if depth == 0:
                    close_idx = i
                    break
        
        if close_idx == -1:
            close_idx = len(text) - 1
            
        raw_name = text[last_end:start_idx]
        raw_name = raw_name.strip(' \t\n\r、,・')
        raw_name = raw_name.replace('ほか', '')
        raw_name = raw_name.strip(' \t\n\r、,・')
        
        name = raw_name if raw_name else '（名称なし）'
        results.append((name, year))
        
        last_end = close_idx + 1
        
    return results

def parse_built_year(text):
    if pd.isna(text) or str(text).strip() == "":
        return None
    text = unicodedata.normalize('NFKC', str(text))
    matches = re.findall(r'\d{3,4}', text)
    if not matches:
        return None
    years = [int(m) for m in matches]
    return min(years)

def classify_monument(disasters, built_year):
    if not disasters:
        return "不明（災害名に年なし）", None
    
    if built_year is None:
        return "対象外（建立年不明）", None
        
    oldest_disaster_year = min(y for n, y in disasters)
    
    if built_year < oldest_disaster_year:
        return "災害前の建立", built_year - oldest_disaster_year
    else:
        return "差あり", built_year - oldest_disaster_year

def is_just_numbers(text):
    if pd.isna(text): return False
    text = unicodedata.normalize('NFKC', str(text)).strip()
    return bool(re.fullmatch(r'\d+', text))

def check_files_exist_local(pref, root):
    missing_files = []
    base_dir = root / "data" / "processed"
    
    f_main = base_dir / f"monuments_{pref}.csv"
    if not f_main.exists():
        missing_files.append((f_main, f"python src/load_monuments.py --pref {pref}"))
        
    f_elev = base_dir / f"elevation_{pref}.csv"
    if not f_elev.exists():
        missing_files.append((f_elev, f"python src/add_elevation.py --pref {pref}"))
        
    f_rc = base_dir / f"river_coast_{pref}.csv"
    if not f_rc.exists():
        missing_files.append((f_rc, f"python src/add_river_coast.py --pref {pref}"))
        
    if missing_files:
        for f, cmd in missing_files:
            print(f"ファイルが見つかりません: {f.name}")
            print(f"先に実行してください: {cmd}")
        sys.exit(1)
    
    return f_main, f_elev, f_rc

def load_inputs(pref, root):
    f_main, f_elev, f_rc = check_files_exist_local(pref, root)
    mon_main = pd.read_csv(f_main, dtype={'ID': str}, encoding='utf-8-sig')
    mon_elev = pd.read_csv(f_elev, dtype={'ID': str}, encoding='utf-8-sig')
    mon_rc = pd.read_csv(f_rc, dtype={'ID': str}, encoding='utf-8-sig')
    
    df = mon_main.merge(mon_elev[['ID', '標高_m', '取得状態']], on='ID', how='left')
    df = df.merge(mon_rc[['ID', '海岸までの距離_m', '海岸_状態']], on='ID', how='left')
    return df

def build_denshou_table(df):
    denshou_data = []
    for idx, row in df.iterrows():
        disasters = parse_disasters(row.get('災害名'))
        built_year = parse_built_year(row.get('建立年'))
        kbn, diff = classify_monument(disasters, built_year)
        
        parsed_str = "；".join(f"{n}({y})" for n, y in disasters) if disasters else ""
        year_count = len(disasters)
        occur_year = min((y for n, y in disasters), default=np.nan) if disasters else np.nan
        
        notes = []
        if built_year is not None and not is_just_numbers(row.get('建立年')):
            notes.append("建立年の記載に注記あり（最も古い年を使用）")
        if year_count >= 2:
            notes.append("複数の災害（最も古い年を使用）")
        note_str = "／".join(notes)
        
        main_t = main_type(row)
        
        denshou_data.append({
            'ID': row['ID'],
            '碑名': row['碑名'],
            '主な種別': main_t,
            '災害名（元の表記）': row.get('災害名', ''),
            '取り出した災害': parsed_str,
            '年の数': year_count if year_count > 0 else 0,
            '発生年': occur_year if pd.notna(occur_year) else "",
            '建立年（元の表記）': row.get('建立年', ''),
            '建立年_数値': built_year if built_year is not None else "",
            '建立までの年数': diff if diff is not None else "",
            '区分': kbn,
            '注記': note_str
        })
    res_df = pd.DataFrame(denshou_data)
    res_df.sort_values(by='ID', inplace=True)
    return res_df

def build_summary(denshou_df):
    summary_data = []
    def make_summary_row(name, subset):
        total = len(subset)
        if total == 0:
            return None
        c_diff = len(subset[subset['区分'] == '差あり'])
        c_pre = len(subset[subset['区分'] == '災害前の建立'])
        c_out = len(subset[subset['区分'] == '対象外（建立年不明）'])
        c_unk = len(subset[subset['区分'] == '不明（災害名に年なし）'])
        diff_sub = pd.to_numeric(subset[subset['区分'] == '差あり']['建立までの年数'], errors='coerce').dropna()
        if len(diff_sub) > 0:
            med, q1, q3 = calc_stats(diff_sub)
            c_min = diff_sub.min()
            c_max = diff_sub.max()
        else:
            med = q1 = q3 = c_min = c_max = np.nan
        return {
            '主な種別': name,
            '碑の数': total,
            '差あり': c_diff,
            '災害前の建立': c_pre,
            '対象外（建立年不明）': c_out,
            '不明（災害名に年なし）': c_unk,
            '年数_中央値': med,
            '年数_第1四分位': q1,
            '年数_第3四分位': q3,
            '年数_最小': c_min,
            '年数_最大': c_max
        }

    row_all = make_summary_row('全種別', denshou_df)
    if row_all:
        summary_data.append(row_all)
        
    order = ['津波', '高潮', '洪水', '土砂災害', '火山災害', '地震', 'その他']
    for t in order:
        sub = denshou_df[denshou_df['主な種別'] == t]
        r = make_summary_row(t, sub)
        if r:
            summary_data.append(r)
            
    sum_df = pd.DataFrame(summary_data)
    return sum_df

def build_groups(df):
    group_data = {}
    for idx, row in df.iterrows():
        disasters = parse_disasters(row.get('災害名'))
        for name, y in disasters:
            key = (name, y)
            if key not in group_data:
                group_data[key] = []
            group_data[key].append(idx)
            
    groups_list = []
    for (name, y), indices in group_data.items():
        subset = df.loc[indices]
        
        elev_valid, elev_exc = get_valid_series(subset, '標高_m')
        coast_valid, coast_exc = get_valid_series(subset, '海岸までの距離_m')
        
        def min_max(s):
            if len(s) > 0:
                return s.median(), s.min(), s.max()
            return np.nan, np.nan, np.nan
            
        em, emin, emax = min_max(elev_valid)
        cm, cmin, cmax = min_max(coast_valid)
        
        ids = sorted(subset['ID'].tolist())
        
        groups_list.append({
            '災害の名前': name,
            '発生年': y,
            '碑の数': len(indices),
            '標高_中央値': em,
            '標高_最小': emin,
            '標高_最大': emax,
            '標高_除外数': elev_exc,
            '海岸までの距離_中央値': cm,
            '海岸までの距離_最小': cmin,
            '海岸までの距離_最大': cmax,
            '海岸までの距離_除外数': coast_exc,
            '碑のID': "；".join(ids),
            '_indices': indices # グラフ作成用の隠し列
        })
        
    g_df = pd.DataFrame(groups_list)
    if not g_df.empty:
        g_df.sort_values(by=['碑の数', '発生年', '災害の名前'], ascending=[False, True, True], inplace=True)
    return g_df

def choose_yscale(values):
    if len(values) > 0 and min(values) > 0:
        return "log"
    return "linear"

def draw_group_axis(ax, data_lst, labels, title):
    all_vals = []
    for d in data_lst:
        all_vals.extend(d)
        
    ax.boxplot(data_lst, positions=range(1, len(labels)+1), widths=0.4)
    for i, d in enumerate(data_lst):
        np.random.seed(42 + i)
        x = np.random.normal(i + 1, 0.05, size=len(d))
        ax.scatter(x, d, alpha=0.6, color='blue', s=15)
        
    ax.set_xticks(range(1, len(labels)+1))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    
    yscale = choose_yscale(all_vals)
    ax.set_yscale(yscale)
    if yscale == "log":
        ax.set_ylabel(f"{title}（m）（対数目盛）")
    else:
        ax.set_ylabel(f"{title}（m）")

def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--pref', type=str, required=True)
    parsed_args = parser.parse_args(args)
    pref = parsed_args.pref
    
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください。all は指定できません。")
        sys.exit(1)
        
    pref_name = PREFECTURES[pref]
    
    df = load_inputs(pref, PROJECT_ROOT)
    res_df = build_denshou_table(df)
    sum_df = build_summary(res_df)
    g_df = build_groups(df)
    
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(exist_ok=True, parents=True)
    fig_dir = out_dir / "fig"
    fig_dir.mkdir(exist_ok=True, parents=True)
    
    res_df.to_csv(out_dir / f"denshou_{pref}.csv", index=False, encoding='utf-8-sig')
    
    sum_df_out = sum_df.copy()
    for col in ['年数_中央値', '年数_第1四分位', '年数_第3四分位', '年数_最小', '年数_最大']:
        sum_df_out[col] = sum_df_out[col].apply(lambda x: round(x, 1) if pd.notna(x) else "")
    sum_df_out.to_csv(out_dir / f"denshou_summary_{pref}.csv", index=False, encoding='utf-8-sig')
    
    g_df_out = g_df.drop(columns=['_indices']) if not g_df.empty else g_df
    if not g_df_out.empty:
        for col in ['標高_中央値', '標高_最小', '標高_最大', '海岸までの距離_中央値', '海岸までの距離_最小', '海岸までの距離_最大']:
            g_df_out[col] = g_df_out[col].apply(lambda x: round(x, 1) if pd.notna(x) else "")
    g_df_out.to_csv(out_dir / f"disaster_groups_{pref}.csv", index=False, encoding='utf-8-sig')
    
    set_jp_font()
    
    order = ['津波', '高潮', '洪水', '土砂災害', '火山災害', '地震', 'その他']
    valid_types = []
    for t in order:
        if len(res_df[(res_df['主な種別'] == t) & (res_df['区分'] == '差あり')]) > 0:
            valid_types.append(t)
            
    fig, ax = plt.subplots(figsize=(10, 6))
    x_labels_years = []
    for i, t in enumerate(valid_types):
        sub = res_df[(res_df['主な種別'] == t) & (res_df['区分'] == '差あり')].copy()
        sub['建立までの年数'] = pd.to_numeric(sub['建立までの年数'], errors='coerce')
        sub = sub['建立までの年数'].dropna()
        x_labels_years.append(f"{t}（{len(sub)}）")
        
        np.random.seed(42 + i)
        x = np.random.normal(i + 1, 0.08, size=len(sub))
        ax.scatter(x, sub.values, alpha=0.6, color='blue', s=20)
        
        med = sub.median()
        ax.hlines(med, i + 0.7, i + 1.3, color='red', linewidth=2)
        
    if valid_types:
        ax.set_xticks(range(1, len(valid_types) + 1))
        ax.set_xticklabels(x_labels_years)
    ax.set_ylabel("建立までの年数（年）")
    ax.set_title(f"災害から碑の建立までの年数（{pref_name}）")
    plt.tight_layout()
    plt.savefig(fig_dir / f"denshou_years_{pref}.png")
    plt.close(fig)
    
    if not g_df.empty:
        big_groups = g_df[g_df['碑の数'] >= 5]
    else:
        big_groups = pd.DataFrame()
        
    if len(big_groups) > 0:
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        x_labels_grp = []
        elev_data = []
        coast_data = []
        
        for _, row in big_groups.iterrows():
            n = row['災害の名前']
            y = row['発生年']
            c = row['碑の数']
            x_labels_grp.append(f"{n}({y})\n{c}基")
            
            indices = row['_indices']
            sub = df.loc[indices]
            
            ev, _ = get_valid_series(sub, '標高_m')
            elev_data.append(ev.dropna().values)
            
            cv, _ = get_valid_series(sub, '海岸までの距離_m')
            coast_data.append(cv.dropna().values)
            
        for ax, data_lst, title in zip(axes, [elev_data, coast_data], ["標高", "海岸までの距離"]):
            draw_group_axis(ax, data_lst, x_labels_grp, title)
            
        fig.suptitle(f"同じ災害を伝える碑群の比較（{pref_name}）")
        plt.tight_layout()
        plt.savefig(fig_dir / f"disaster_groups_{pref}.png")
        plt.close(fig)
    else:
        print("5基以上の碑群がないため、碑群の比較グラフは作成しませんでした。")
        
    t_total = len(res_df)
    c_diff = len(res_df[res_df['区分'] == '差あり'])
    c_pre = len(res_df[res_df['区分'] == '災害前の建立'])
    c_out = len(res_df[res_df['区分'] == '対象外（建立年不明）'])
    c_unk = len(res_df[res_df['区分'] == '不明（災害名に年なし）'])
    
    diff_sub = pd.to_numeric(res_df[res_df['区分'] == '差あり']['建立までの年数'], errors='coerce').dropna()
    if len(diff_sub) > 0:
        med = round(diff_sub.median(), 1)
        c_min = int(diff_sub.min())
        c_max = int(diff_sub.max())
        med_str = f"{med:.1f}"
    else:
        med_str = "NaN"
        c_min = "NaN"
        c_max = "NaN"
        
    print(f"伝承内容の分析：{pref_name}（{pref}）")
    print(f"碑の数：{t_total}基")
    print(f"区分：差あり {c_diff}／災害前の建立 {c_pre}／対象外（建立年不明） {c_out}／不明（災害名に年なし） {c_unk}（合計 {t_total}）")
    if c_diff > 0:
        print(f"建立までの年数（差あり {c_diff}基）：中央値 {med_str}年（最小 {c_min}年、最大 {c_max}年）")
    else:
        print(f"建立までの年数（差あり {c_diff}基）：データなし")
        
    top_groups = []
    if not g_df.empty:
        for _, r in g_df.head(5).iterrows():
            top_groups.append(f"{r['災害の名前']}({r['発生年']}) {r['碑の数']}基")
    top_str = "／".join(top_groups) if top_groups else "なし"
    print(f"碑の数が多い災害：{top_str}")
    
    out_files = [
        f"output/denshou_{pref}.csv",
        f"output/denshou_summary_{pref}.csv",
        f"output/disaster_groups_{pref}.csv",
        f"output/fig/denshou_years_{pref}.png"
    ]
    if len(big_groups) > 0:
        out_files.append(f"output/fig/disaster_groups_{pref}.png")
        
    print("出力：")
    for f in out_files:
        print(f"  {f}")

if __name__ == '__main__':
    main()
