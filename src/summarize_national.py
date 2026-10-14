# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import pandas as pd

import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    from src.prefectures import PREFECTURES
    from src.summarize import (
        get_filenames,
        get_valid_series,
        analyze_indicator,
        extract_relocated,
        DISASTER_TYPES,
        set_jp_font,
    )
    from src.summarize_hazard import calc_hazard_stats
except ImportError:
    from prefectures import PREFECTURES
    from summarize import (
        get_filenames,
        get_valid_series,
        analyze_indicator,
        extract_relocated,
        DISASTER_TYPES,
        set_jp_font,
    )
    from summarize_hazard import calc_hazard_stats


def get_project_root():
    """プロジェクトのルートディレクトリのパスを返す"""
    return Path(__file__).resolve().parent.parent


def load_pref(pref, base_dir=None):
    """
    1県分の processed データを読み込み、結合した DataFrame 4つを返す。
    (mon, pt, mon_haz, pt_haz)
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"

    # mon と pt の読み込みと結合（summarize.py と同じ）
    mon_files = get_filenames(pref, "monuments", proc_dir)
    mon_main = pd.read_csv(mon_files["main"], dtype={'ID': str}, encoding='utf-8-sig')
    mon_elev = pd.read_csv(mon_files["elevation"], dtype={'ID': str}, encoding='utf-8-sig')
    mon_rc = pd.read_csv(mon_files["river_coast"], dtype={'ID': str}, encoding='utf-8-sig')
    mon_lf = pd.read_csv(mon_files["landform"], dtype={'ID': str}, encoding='utf-8-sig')

    mon = mon_main.merge(mon_elev[['ID', '標高_m', '傾斜_度', '取得状態']], on='ID', how='left')
    mon = mon.merge(
        mon_rc[['ID', '河川までの距離_m', '河川との高さの差_m', '河川_状態', '海岸までの距離_m', '海岸_状態']],
        on='ID',
        how='left'
    )
    mon = mon.merge(mon_lf[['ID', '地形分類名', '地形分類コード', '地形分類_状態']], on='ID', how='left')

    pt_files = get_filenames(pref, "points", proc_dir)
    pt_main = pd.read_csv(pt_files["main"], dtype={'ID': str, '元の碑ID': str}, encoding='utf-8-sig')
    pt_elev = pd.read_csv(pt_files["elevation"], dtype={'ID': str}, encoding='utf-8-sig')
    pt_rc = pd.read_csv(pt_files["river_coast"], dtype={'ID': str}, encoding='utf-8-sig')
    pt_lf = pd.read_csv(pt_files["landform"], dtype={'ID': str}, encoding='utf-8-sig')

    pt = pt_main.merge(pt_elev[['ID', '標高_m', '傾斜_度', '取得状態']], on='ID', how='left')
    pt = pt.merge(
        pt_rc[['ID', '河川までの距離_m', '河川との高さの差_m', '河川_状態', '海岸までの距離_m', '海岸_状態']],
        on='ID',
        how='left'
    )
    pt = pt.merge(pt_lf[['ID', '地形分類名', '地形分類コード', '地形分類_状態']], on='ID', how='left')

    # mon_haz と pt_haz の読み込みと結合（summarize_hazard.py と同じ）
    m_haz_path = proc_dir / f"hazard_{pref}.csv"
    p_haz_path = proc_dir / f"hazard_points_{pref}.csv"
    m_haz = pd.read_csv(m_haz_path, dtype={'ID': str}, encoding='utf-8-sig')
    p_haz = pd.read_csv(p_haz_path, dtype={'ID': str}, encoding='utf-8-sig')

    drop_cols_m = [c for c in ['碑名', '緯度', '経度'] if c in m_haz.columns]
    m_haz_clean = m_haz.drop(columns=drop_cols_m)

    drop_cols_p = [c for c in ['碑名', '緯度', '経度', '元の碑ID'] if c in p_haz.columns]
    p_haz_clean = p_haz.drop(columns=drop_cols_p)

    mon_haz = pd.merge(mon_main, m_haz_clean, on='ID', how='inner')
    pt_haz = pd.merge(pt_main, p_haz_clean, on='ID', how='inner')

    return mon, pt, mon_haz, pt_haz


def check_all_files(base_dir=None):
    """
    47都道府県について、必要な11ファイルがそろっているかを調べ、
    足りない県コードのリストを返す。
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"
    out_dir = base_dir / "output"
    missing_prefs = []

    for pref in sorted(PREFECTURES.keys()):
        required_files = [
            proc_dir / f"monuments_{pref}.csv",
            proc_dir / f"elevation_{pref}.csv",
            proc_dir / f"river_coast_{pref}.csv",
            proc_dir / f"landform_{pref}.csv",
            proc_dir / f"hazard_{pref}.csv",
            proc_dir / f"points_{pref}.csv",
            proc_dir / f"elevation_points_{pref}.csv",
            proc_dir / f"river_coast_points_{pref}.csv",
            proc_dir / f"landform_points_{pref}.csv",
            proc_dir / f"hazard_points_{pref}.csv",
            out_dir / f"denshou_{pref}.csv",
        ]
        if not all(p.exists() for p in required_files):
            missing_prefs.append(pref)

    return missing_prefs


def build_summary_tables(mon, pt, relocated_ids):
    """
    mon・pt・移転碑IDリストから、summary と landform の2つの DataFrame を作成して返す。
    """
    indicators = ['標高_m', '傾斜_度', '河川までの距離_m', '河川との高さの差_m', '海岸までの距離_m']
    ranges = ['全碑', '移転碑を除く']
    disaster_types = ['全種別'] + DISASTER_TYPES

    summary_data = []
    landform_data = []
    lf_order = []

    for r in ranges:
        if r == '全碑':
            m_df = mon
            p_df = pt
        else:
            m_df = mon[~mon['ID'].isin(relocated_ids)]
            p_df = pt[~pt['元の碑ID'].isin(relocated_ids)]

        for dt in disaster_types:
            if dt == '全種別':
                dt_name = '全種別'
                m_sub = m_df
                p_sub = p_df
            else:
                dt_name = dt.replace('種別_', '')
                m_sub = m_df[m_df[dt] == 1]
                p_sub = p_df[p_df[dt] == 1]

            # 指標ごとの集計
            for ind in indicators:
                stats, _, _ = analyze_indicator(m_sub, p_sub, ind)
                row = [r, dt_name, ind] + stats
                summary_data.append(row)

            # 地形分類の集計
            m_lf, _ = get_valid_series(m_sub, '地形分類名')
            p_lf, _ = get_valid_series(p_sub, '地形分類名')

            if r == '全碑' and dt == '全種別':
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

    summary_cols = [
        '範囲', '災害種別', '指標', '碑_数', '碑_除外数', '碑_中央値', '碑_第1四分位', '碑_第3四分位',
        '比較地点_数', '比較地点_除外数', '比較地点_中央値', '比較地点_第1四分位', '比較地点_第3四分位',
        '組の数', '差の中央値', '碑の方が大きい割合'
    ]
    summary_df = pd.DataFrame(summary_data, columns=summary_cols)

    for col in ['碑_中央値', '碑_第1四分位', '碑_第3四分位', '比較地点_中央値', '比較地点_第1四分位', '比較地点_第3四分位', '差の中央値']:
        summary_df[col] = summary_df[col].round(2)
    summary_df['碑の方が大きい割合'] = summary_df['碑の方が大きい割合'].round(3)

    lf_cols = ['範囲', '災害種別', '地形分類名', '碑_件数', '碑_割合', '比較地点_件数', '比較地点_割合']
    lf_df = pd.DataFrame(landform_data, columns=lf_cols)
    lf_df['碑_割合'] = lf_df['碑_割合'].round(3)
    lf_df['比較地点_割合'] = lf_df['比較地点_割合'].round(3)

    return summary_df, lf_df


def build_hazard_table(mon_haz, pt_haz, relocated_ids):
    """
    mon_haz・pt_haz・移転碑IDリストから、hazard_summary の DataFrame を作成して返す。
    （碑が0基の災害種別は行を出さない）
    """
    ranges = ['全碑', '移転碑を除く']
    disaster_types = ['全種別', '洪水', '地震', '津波', '土砂災害', '高潮', '火山災害', 'その他']
    hazards = [
        ('洪水（想定最大規模）', '洪水_', True),
        ('津波', '津波_', True),
        ('高潮', '高潮_', True),
        ('土砂災害', '土砂_', False)
    ]

    summary = []

    for r in ranges:
        if r == '全碑':
            m_df = mon_haz
            p_df = pt_haz
        else:
            m_df = mon_haz[~mon_haz['ID'].isin(relocated_ids)]
            p_df = pt_haz[~pt_haz['元の碑ID'].isin(relocated_ids)]

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

    cols = [
        '範囲', '災害種別', 'ハザード',
        '碑_数', '碑_取得不可', '碑_区域内', '碑_区域内の割合', '碑_3m以上', '碑_3m以上の割合',
        '比較地点_数', '比較地点_取得不可', '比較地点_区域内', '比較地点_区域内の割合', '比較地点_3m以上', '比較地点_3m以上の割合'
    ]

    return pd.DataFrame(summary, columns=cols)


def build_pref_counts(base_dir=None):
    """
    都道府県別の件数表を作成して返す。
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"
    rows = []

    pref_counts_cols = [
        "県コード", "県名", "碑_数", "移転碑_数", "比較地点_数",
        "種別_洪水", "種別_地震", "種別_津波", "種別_土砂災害", "種別_高潮", "種別_火山災害", "種別_その他"
    ]

    for pref in sorted(PREFECTURES.keys()):
        m_file = proc_dir / f"monuments_{pref}.csv"
        p_file = proc_dir / f"points_{pref}.csv"
        if not m_file.exists() or not p_file.exists():
            continue

        mon_df = pd.read_csv(m_file, dtype={'ID': str}, encoding='utf-8-sig')
        pt_df = pd.read_csv(p_file, dtype={'ID': str, '元の碑ID': str}, encoding='utf-8-sig')

        relocated_df = extract_relocated(mon_df)
        m_count = len(mon_df)
        p_count = len(pt_df)
        r_count = len(relocated_df)

        row = {
            "県コード": pref,
            "県名": PREFECTURES[pref],
            "碑_数": m_count,
            "移転碑_数": r_count,
            "比較地点_数": p_count,
        }
        for dt_col in DISASTER_TYPES:
            row[dt_col] = int(mon_df[dt_col].sum()) if dt_col in mon_df.columns else 0

        rows.append(row)

    df = pd.DataFrame(rows, columns=pref_counts_cols)

    if not df.empty:
        total_row = {
            "県コード": "全国",
            "県名": "合計",
            "碑_数": int(df["碑_数"].sum()),
            "移転碑_数": int(df["移転碑_数"].sum()),
            "比較地点_数": int(df["比較地点_数"].sum()),
        }
        for dt_col in DISASTER_TYPES:
            total_row[dt_col] = int(df[dt_col].sum())

        total_df = pd.DataFrame([total_row], columns=pref_counts_cols)
        df = pd.concat([df, total_df], ignore_index=True)

    return df


def decade_label(year):
    """
    数値の年を年代の文字列にする。
    1600未満は「1600年より前」、それ以外は「1940年代」の形（年を10で切り捨て）。
    空（NaN）は None。
    """
    if pd.isna(year) or year is None or year == "":
        return None
    try:
        y = int(year)
    except (ValueError, TypeError):
        return None
    if y < 1600:
        return "1600年より前"
    return f"{(y // 10) * 10}年代"


def build_years_table(base_dir=None):
    """
    47都道府県の denshou_XX.csv を県コード順に読んで束ね、年代別の表を返す。
    列：年代,発生年代_碑の数,建立年代_碑の数,発生年代_主な災害
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    out_dir = base_dir / "output"
    dfs = []
    for pref in sorted(PREFECTURES.keys()):
        denshou_file = out_dir / f"denshou_{pref}.csv"
        if denshou_file.exists():
            dfs.append(pd.read_csv(denshou_file, dtype={'ID': str}, encoding='utf-8-sig'))

    if dfs:
        all_denshou = pd.concat(dfs, ignore_index=True)
    else:
        all_denshou = pd.DataFrame(columns=['発生年', '建立年_数値', '取り出した災害'])

    # 年代のラベル付け（NaNはNone）
    all_denshou['発生年代'] = all_denshou['発生年'].apply(decade_label)
    all_denshou['建立年代'] = all_denshou['建立年_数値'].apply(decade_label)

    decades = ["1600年より前"] + [f"{d}年代" for d in range(1600, 2030, 10)]
    rows = []

    for dec in decades:
        sub_occur = all_denshou[all_denshou['発生年代'] == dec]
        sub_built = all_denshou[all_denshou['建立年代'] == dec]
        cnt_occur = len(sub_occur)
        cnt_built = len(sub_built)

        disaster_counts = {}
        for val in sub_occur['取り出した災害']:
            if pd.isna(val) or not str(val).strip():
                continue
            # 「；」で区切った先頭
            first_entry = str(val).split('；')[0].strip()
            # 末尾の年の括弧「(1854)」を除く
            name = re.sub(r'\(\d+\)$', '', first_entry).strip()
            if name:
                disaster_counts[name] = disaster_counts.get(name, 0) + 1

        if disaster_counts:
            # 件数の多い順（降順）→名前順（昇順）で明示的にソート
            top_name, top_count = sorted(disaster_counts.items(), key=lambda x: (-x[1], x[0]))[0]
            main_disaster = f"{top_name}({top_count})"
        else:
            main_disaster = ""

        rows.append({
            '年代': dec,
            '発生年代_碑の数': cnt_occur,
            '建立年代_碑の数': cnt_built,
            '発生年代_主な災害': main_disaster,
        })

    cols = ['年代', '発生年代_碑の数', '建立年代_碑の数', '発生年代_主な災害']
    return pd.DataFrame(rows, columns=cols)


def draw_years_chart(years_df, out_path):
    """
    年代別推移の上下2段棒グラフを作成する。
    上段：発生年代、下段：建立年代
    """
    set_jp_font()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    x = np.arange(len(years_df))
    occur_counts = years_df['発生年代_碑の数'].values
    built_counts = years_df['建立年代_碑の数'].values

    # 棒グラフの描画
    ax1.bar(x, occur_counts, color='steelblue', width=0.8)
    ax1.set_ylabel("碑の数", fontsize=11)
    ax1.set_title("発生年代", fontsize=12, loc='left')
    ax1.grid(axis='y', linestyle='--', alpha=0.5)

    ax2.bar(x, built_counts, color='cadetblue', width=0.8)
    ax2.set_ylabel("碑の数", fontsize=11)
    ax2.set_title("建立年代", fontsize=12, loc='left')
    ax2.grid(axis='y', linestyle='--', alpha=0.5)

    # 横軸の目盛りとラベル（共通）
    tick_pos = []
    tick_labels = []
    for i, dec in enumerate(years_df['年代']):
        if dec == "1600年より前" or (dec.endswith("年代") and int(dec[:-2]) >= 1650 and int(dec[:-2]) % 50 == 0):
            tick_pos.append(i)
            tick_labels.append(dec)

    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_labels, fontsize=10)
    ax1.set_xticks(tick_pos)

    # 上段：碑の数の多い6つの年代の棒の上に「主な災害」の名前（件数なし）を書く
    # 多い順→年代の古い順で6つ
    temp_df = years_df.copy()
    temp_df['idx'] = range(len(temp_df))
    top6 = temp_df.sort_values(by=['発生年代_碑の数', 'idx'], ascending=[False, True]).head(6)

    max_occur = occur_counts.max() if len(occur_counts) > 0 else 100
    ax1.set_ylim(0, max_occur * 1.6)

    max_built = built_counts.max() if len(built_counts) > 0 else 100
    ax2.set_ylim(0, max_built * 1.15)

    for _, row in top6.iterrows():
        idx = row['idx']
        cnt = row['発生年代_碑の数']
        main_disaster = row['発生年代_主な災害']
        name = re.sub(r'\(\d+\)$', '', main_disaster).strip()
        if name:
            ax1.text(
                idx,
                cnt + max_occur * 0.02,
                name,
                ha='center',
                va='bottom',
                rotation=90,
                fontsize=9
            )

    fig.suptitle("自然災害伝承碑の年代別推移（全国）", fontsize=15, y=0.98)

    footer_text = "出典：国土地理院（自然災害伝承碑）を加工して作成\n注：発生年は、複数の災害がある碑では最も古い年"
    fig.text(0.5, 0.01, footer_text, ha='center', va='bottom', fontsize=9)

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def draw_pref_counts_chart(pref_counts_df, out_path):
    """
    都道府県別の自然災害伝承碑の数の横棒グラフを作成する。
    「全国」行を除く47本、上から北海道→沖縄の順。
    """
    set_jp_font()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 「全国」行を除く47都道府県
    df_prefs = pref_counts_df[pref_counts_df['県コード'] != '全国'].copy()

    fig, ax = plt.subplots(figsize=(10, 12))

    y_pos = np.arange(len(df_prefs))
    counts = df_prefs['碑_数'].values
    pref_names = df_prefs['県名'].values

    ax.barh(y_pos, counts, color='steelblue', height=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(pref_names, fontsize=9)
    ax.invert_yaxis()  # 上から北海道→沖縄の順

    max_cnt = counts.max() if len(counts) > 0 else 100
    ax.set_xlim(0, max_cnt * 1.15)
    ax.set_xlabel("碑の数", fontsize=11)
    ax.set_title("都道府県別の自然災害伝承碑の数", fontsize=14, pad=15)
    ax.grid(axis='x', linestyle='--', alpha=0.5)

    for i, cnt in enumerate(counts):
        ax.text(cnt + max_cnt * 0.01, i, f"{cnt:,}", va='center', ha='left', fontsize=9)

    footer_text = "出典：国土地理院（自然災害伝承碑）を加工して作成"
    fig.text(0.5, 0.01, footer_text, ha='center', va='bottom', fontsize=9)

    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def write_with_notes(df, path, notes):
    """
    データフレームを utf-8-sig・indexなしで CSV 出力し、続けて notes の各行を書き込む。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        df.to_csv(f, index=False)
        for note in notes:
            line = note if note.endswith('\n') else note + '\n'
            f.write(line)


def main(args=None, base_dir=None):
    """
    全国集計のメイン処理。
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    missing_prefs = check_all_files(base_dir)
    if missing_prefs:
        missing_str = "、".join([f"{PREFECTURES[c]}（{c}）" for c in missing_prefs])
        pref_arg = ",".join(missing_prefs)
        print(f"エラー：ファイルが足りない県があります：{missing_str}")
        print(f'先に実行してください：python src/run_batch.py --pref "{pref_arg}"')
        sys.exit(1)

    mon_list = []
    pt_list = []
    mon_haz_list = []
    pt_haz_list = []

    for pref in sorted(PREFECTURES.keys()):
        m, p, mh, ph = load_pref(pref, base_dir)
        mon_list.append(m)
        pt_list.append(p)
        mon_haz_list.append(mh)
        pt_haz_list.append(ph)

    all_mon = pd.concat(mon_list, ignore_index=True)
    all_pt = pd.concat(pt_list, ignore_index=True)
    all_mon_haz = pd.concat(mon_haz_list, ignore_index=True)
    all_pt_haz = pd.concat(pt_haz_list, ignore_index=True)

    relocated_df = extract_relocated(all_mon)
    relocated_ids = relocated_df['ID'].tolist()

    summary_df, landform_df = build_summary_tables(all_mon, all_pt, relocated_ids)
    hazard_df = build_hazard_table(all_mon_haz, all_pt_haz, relocated_ids)
    pref_counts_df = build_pref_counts(base_dir)

    out_dir = base_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. relocated_all.csv
    relocated_out = relocated_df.rename(columns={'前後30字': '伝承内容の該当箇所の前後30字'})
    relocated_out.to_csv(out_dir / "relocated_all.csv", index=False, encoding='utf-8-sig')

    # 2. summary_all.csv
    note_common = "注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。"
    write_with_notes(summary_df, out_dir / "summary_all.csv", [note_common])

    # 3. landform_all.csv
    write_with_notes(landform_df, out_dir / "landform_all.csv", [note_common])

    # 4. hazard_summary_all.csv
    note_hazard = [
        note_common,
        "注：想定区域との重なりを示すもので、危険度の判定ではありません。出典：ハザードマップポータルサイト（加工して作成）"
    ]
    write_with_notes(hazard_df, out_dir / "hazard_summary_all.csv", note_hazard)

    # 5. pref_counts_all.csv
    note_pref = ["注：1基が複数の災害種別を持つため、種別ごとの合計は碑の数より多くなります。"]
    write_with_notes(pref_counts_df, out_dir / "pref_counts_all.csv", note_pref)

    # 6. years_all.csv
    years_df = build_years_table(base_dir)

    all_denshou_list = []
    for pref in sorted(PREFECTURES.keys()):
        d_file = out_dir / f"denshou_{pref}.csv"
        if d_file.exists():
            all_denshou_list.append(pd.read_csv(d_file, dtype={'ID': str}, encoding='utf-8-sig'))
    if all_denshou_list:
        all_denshou_df = pd.concat(all_denshou_list, ignore_index=True)
        occur_unknown = int(all_denshou_df['発生年'].isna().sum())
        built_unknown = int(all_denshou_df['建立年_数値'].isna().sum())
    else:
        occur_unknown = 0
        built_unknown = 0

    note_years = [
        "注：発生年は、複数の災害がある碑では最も古い年です。",
        f"注：発生年が不明の碑 {occur_unknown}基、建立年が不明の碑 {built_unknown}基は数えていません。"
    ]
    write_with_notes(years_df, out_dir / "years_all.csv", note_years)

    # グラフ作成
    fig_dir = out_dir / "fig"
    fig_dir.mkdir(parents=True, exist_ok=True)
    draw_years_chart(years_df, fig_dir / "years_all.png")
    draw_pref_counts_chart(pref_counts_df, fig_dir / "pref_counts_all.png")

    # 画面表示
    total_mon = len(all_mon)
    total_pt = len(all_pt)
    ex_mon = len(all_mon[~all_mon['ID'].isin(relocated_ids)])
    ex_pt = len(all_pt[~all_pt['元の碑ID'].isin(relocated_ids)])
    num_rel = len(relocated_ids)

    print("全国集計：47都道府県")
    print(f"碑：全碑 {total_mon:,}基／移転碑を除く {ex_mon:,}基　比較地点：全碑 {total_pt:,}点／移転碑を除く {ex_pt:,}点")
    print(f"移転碑（伝承内容に「移転」「移設」を含む碑）：{num_rel:,}基")
    print("全碑・全種別の中央値（碑／比較地点）")

    indicators = ['標高_m', '傾斜_度', '河川までの距離_m', '河川との高さの差_m', '海岸までの距離_m']
    for ind in indicators:
        row = summary_df[(summary_df['範囲'] == '全碑') & (summary_df['災害種別'] == '全種別') & (summary_df['指標'] == ind)]
        m_val = row['碑_中央値'].values[0]
        p_val = row['比較地点_中央値'].values[0]
        print(f"  {ind}：{m_val:.1f}／{p_val:.1f}")

    print("全碑・全種別のハザード区域内の割合（碑／比較地点）")
    hazard_names = ['洪水（想定最大規模）', '津波', '高潮', '土砂災害']
    for h_name in hazard_names:
        row = hazard_df[(hazard_df['範囲'] == '全碑') & (hazard_df['災害種別'] == '全種別') & (hazard_df['ハザード'] == h_name)]
        m_val = float(row['碑_区域内の割合'].values[0])
        p_val = float(row['比較地点_区域内の割合'].values[0])
        print(f"  {h_name}：{m_val:.3f}／{p_val:.3f}")

    total_occur = int(years_df['発生年代_碑の数'].sum())
    total_built = int(years_df['建立年代_碑の数'].sum())
    print(f"年代別推移（発生年は {total_occur:,}基、建立年は {total_built:,}基で集計）")

    temp_df = years_df.copy()
    temp_df['idx'] = range(len(temp_df))

    top_occur = temp_df.sort_values(by=['発生年代_碑の数', 'idx'], ascending=[False, True]).head(3)
    occur_strs = []
    for _, r in top_occur.iterrows():
        main_d = r['発生年代_主な災害']
        m = re.match(r'^(.*)\((\d+)\)$', main_d)
        if m:
            dis_info = f"（{m.group(1)} {m.group(2)}）"
        else:
            dis_info = ""
        occur_strs.append(f"{r['年代']} {r['発生年代_碑の数']:,}基{dis_info}")
    print(f"  発生年代の上位：{'／'.join(occur_strs)}")

    top_built = temp_df.sort_values(by=['建立年代_碑の数', 'idx'], ascending=[False, True]).head(3)
    built_strs = [f"{r['年代']} {r['建立年代_碑の数']:,}基" for _, r in top_built.iterrows()]
    print(f"  建立年代の上位：{'／'.join(built_strs)}")

    print("出力：")
    print("  output/summary_all.csv")
    print("  output/landform_all.csv")
    print("  output/hazard_summary_all.csv")
    print("  output/relocated_all.csv")
    print("  output/pref_counts_all.csv")
    print("  output/years_all.csv")
    print("  output/fig/years_all.png")
    print("  output/fig/pref_counts_all.png")


if __name__ == "__main__":
    main()

