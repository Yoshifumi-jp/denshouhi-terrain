# -*- coding: utf-8 -*-
"""地形分類（人工地形）について、県別および全国の集計表を出力するプログラム。

何をするプログラムか:
data/processed/ の monuments_XX.csv・points_XX.csv・landform_artificial_XX.csv・
landform_artificial_points_XX.csv・landform_XX.csv・landform_points_XX.csv を読み込み、
県別（output/landform_artificial_XX.csv）および全国（output/landform_artificial_all.csv）の
「災害種別×人工地形」の集計表と、全国（output/landform_artificial_cross_all.csv）の
「自然地形×人工地形」の集計表を出力する。

範囲外・取得不可を数えない理由:
人工地形は、地形分類（自然地形）の詳細版で値が取れた範囲だけで調べたため、
詳細版が「データなし」で人工地形を調べていない「範囲外」の地点や「取得不可」の地点は分母に含めず、
人工地形の有無を実際に調べた「取得済」と「人工地形なし」の地点だけを数える。
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

try:
    from src.prefectures import PREFECTURES
    from src.summarize import extract_relocated, DISASTER_TYPES
    from src.summarize_region import write_with_notes
    from src.load_monuments import parse_pref_arg
except ImportError:
    from prefectures import PREFECTURES
    from summarize import extract_relocated, DISASTER_TYPES
    from summarize_region import write_with_notes
    from load_monuments import parse_pref_arg

# 人工地形の固定5区分（この順番で並べ、最後に「人工地形なし」を置く）
FIXED_ARTIFICIAL_NAMES = [
    "盛土地・埋立地",
    "切土地",
    "干拓地",
    "農耕平坦化地",
    "改変工事中",
]


def get_project_root():
    """プロジェクトのルートディレクトリのパスを返す"""
    return Path(__file__).resolve().parent.parent


def check_artificial_files(pref_codes, base_dir=None):
    """対象の県コードについて、必要な6ファイルが data/processed/ にそろっているか調べ、足りない県コードのリストを返す"""
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"
    missing_prefs = []

    for pref in pref_codes:
        required_files = [
            proc_dir / f"monuments_{pref}.csv",
            proc_dir / f"points_{pref}.csv",
            proc_dir / f"landform_artificial_{pref}.csv",
            proc_dir / f"landform_artificial_points_{pref}.csv",
            proc_dir / f"landform_{pref}.csv",
            proc_dir / f"landform_points_{pref}.csv",
        ]
        if not all(p.exists() for p in required_files):
            missing_prefs.append(pref)

    return missing_prefs


def load_artificial_pref(pref, base_dir=None):
    """1県分の monuments・points と人工地形・自然地形（詳細版）を読み込み、ID で左結合した (mon, pt) を返す"""
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"

    mon_main = pd.read_csv(
        proc_dir / f"monuments_{pref}.csv",
        dtype={"ID": str},
        encoding="utf-8-sig",
    )
    pt_main = pd.read_csv(
        proc_dir / f"points_{pref}.csv",
        dtype={"ID": str, "元の碑ID": str},
        encoding="utf-8-sig",
    )
    mon_art = pd.read_csv(
        proc_dir / f"landform_artificial_{pref}.csv",
        dtype={"ID": str, "人工地形名": str, "人工地形コード": str, "人工地形_状態": str},
        encoding="utf-8-sig",
    )
    pt_art = pd.read_csv(
        proc_dir / f"landform_artificial_points_{pref}.csv",
        dtype={"ID": str, "人工地形名": str, "人工地形コード": str, "人工地形_状態": str},
        encoding="utf-8-sig",
    )
    mon_lf = pd.read_csv(
        proc_dir / f"landform_{pref}.csv",
        dtype={"ID": str, "地形分類名": str, "地形分類コード": str, "地形分類_状態": str},
        encoding="utf-8-sig",
    )
    pt_lf = pd.read_csv(
        proc_dir / f"landform_points_{pref}.csv",
        dtype={"ID": str, "地形分類名": str, "地形分類コード": str, "地形分類_状態": str},
        encoding="utf-8-sig",
    )

    art_cols = ["ID", "人工地形名", "人工地形_状態"]
    lf_cols = ["ID", "地形分類名"]

    mon = mon_main.merge(mon_art[art_cols], on="ID", how="left")
    mon = mon.merge(mon_lf[lf_cols], on="ID", how="left")

    pt = pt_main.merge(pt_art[art_cols], on="ID", how="left")
    pt = pt.merge(pt_lf[lf_cols], on="ID", how="left")

    for col in ["人工地形名", "人工地形_状態", "地形分類名"]:
        mon[col] = mon[col].fillna("").astype(str)
        pt[col] = pt[col].fillna("").astype(str)

    return mon, pt


def _get_ordered_categories(mon, pt):
    """人工地形の区分の並び順を返す（固定5区分の後、それ以外の人工地形名があれば名前順で入れ、最後に「人工地形なし」）"""
    m_names = set(mon.loc[mon["人工地形_状態"] == "取得済", "人工地形名"].astype(str))
    p_names = set(pt.loc[pt["人工地形_状態"] == "取得済", "人工地形名"].astype(str))
    extra_names = sorted(
        n
        for n in (m_names | p_names)
        if n and n not in FIXED_ARTIFICIAL_NAMES and n != "人工地形なし"
    )
    return FIXED_ARTIFICIAL_NAMES + extra_names + ["人工地形なし"]


def _count_by_category(df):
    """DataFrame の各行について、数える地点の区分ごとの件数辞書と合計件数を返す"""
    counts = {}
    total = 0
    for status, name in zip(df["人工地形_状態"], df["人工地形名"]):
        if status == "取得済":
            cat = str(name)
            counts[cat] = counts.get(cat, 0) + 1
            total += 1
        elif status == "人工地形なし":
            counts["人工地形なし"] = counts.get("人工地形なし", 0) + 1
            total += 1
    return counts, total


def build_artificial_table(mon, pt, relocated_ids):
    """表1「災害種別×人工地形」の集計 DataFrame を作成して返す"""
    ranges = ["全碑", "移転碑を除く"]
    disaster_types = ["全種別"] + DISASTER_TYPES
    categories = _get_ordered_categories(mon, pt)

    rows = []
    for r in ranges:
        if r == "全碑":
            m_df = mon
            p_df = pt
        else:
            m_df = mon[~mon["ID"].isin(relocated_ids)]
            p_df = pt[~pt["元の碑ID"].isin(relocated_ids)]

        for dt in disaster_types:
            if dt == "全種別":
                dt_name = "全種別"
                m_sub = m_df
                p_sub = p_df
            else:
                dt_name = dt.replace("種別_", "")
                m_sub = m_df[m_df[dt] == 1]
                p_sub = p_df[p_df[dt] == 1]

            m_counts, m_total = _count_by_category(m_sub)
            p_counts, p_total = _count_by_category(p_sub)

            for cat in categories:
                m_c = m_counts.get(cat, 0)
                p_c = p_counts.get(cat, 0)
                m_r = m_c / m_total if m_total > 0 else 0.0
                p_r = p_c / p_total if p_total > 0 else 0.0
                rows.append([r, dt_name, cat, m_c, m_r, p_c, p_r])

    cols = [
        "範囲",
        "災害種別",
        "人工地形名",
        "碑_件数",
        "碑_割合",
        "比較地点_件数",
        "比較地点_割合",
    ]
    df = pd.DataFrame(rows, columns=cols)
    df["碑_割合"] = df["碑_割合"].round(3)
    df["比較地点_割合"] = df["比較地点_割合"].round(3)
    return df


def build_artificial_cross_table(mon, pt, relocated_ids):
    """表2「自然地形×人工地形」の集計 DataFrame を作成して返す"""
    ranges = ["全碑", "移転碑を除く"]
    categories = _get_ordered_categories(mon, pt)

    # 全碑の範囲で数える地点について、自然地形（詳細版の地形分類名）ごとの件数を数えて並び順を決める
    # 順番：全碑の比較地点の件数の多い順 → 同数なら全碑の碑の件数の多い順 → 同数なら名前順
    m_all_valid = mon[mon["人工地形_状態"].isin(["取得済", "人工地形なし"])]
    p_all_valid = pt[pt["人工地形_状態"].isin(["取得済", "人工地形なし"])]

    m_nat_counts = {}
    for name in m_all_valid["地形分類名"]:
        key = str(name)
        m_nat_counts[key] = m_nat_counts.get(key, 0) + 1

    p_nat_counts = {}
    for name in p_all_valid["地形分類名"]:
        key = str(name)
        p_nat_counts[key] = p_nat_counts.get(key, 0) + 1

    all_nat_names = set(m_nat_counts.keys()) | set(p_nat_counts.keys())
    ordered_nat_names = sorted(
        all_nat_names,
        key=lambda k: (
            -p_nat_counts.get(k, 0),
            -m_nat_counts.get(k, 0),
            k,
        ),
    )

    rows = []
    for r in ranges:
        if r == "全碑":
            m_df = m_all_valid
            p_df = p_all_valid
        else:
            m_df = m_all_valid[~m_all_valid["ID"].isin(relocated_ids)]
            p_df = p_all_valid[~p_all_valid["元の碑ID"].isin(relocated_ids)]

        for nat_name in ordered_nat_names:
            m_sub = m_df[m_df["地形分類名"] == nat_name]
            p_sub = p_df[p_df["地形分類名"] == nat_name]

            m_counts, m_total = _count_by_category(m_sub)
            p_counts, p_total = _count_by_category(p_sub)

            for cat in categories:
                m_c = m_counts.get(cat, 0)
                p_c = p_counts.get(cat, 0)
                m_r = m_c / m_total if m_total > 0 else 0.0
                p_r = p_c / p_total if p_total > 0 else 0.0
                rows.append([r, nat_name, cat, m_c, m_r, p_c, p_r])

    cols = [
        "範囲",
        "自然地形名",
        "人工地形名",
        "碑_件数",
        "碑_割合",
        "比較地点_件数",
        "比較地点_割合",
    ]
    df = pd.DataFrame(rows, columns=cols)
    df["碑_割合"] = df["碑_割合"].round(3)
    df["比較地点_割合"] = df["比較地点_割合"].round(3)
    return df


def count_uncounted(mon, pt):
    """全碑の範囲で数えていない地点の件数 (a, b, c, d) を返す"""
    a = int((mon["人工地形_状態"] == "範囲外").sum())
    b = int((pt["人工地形_状態"] == "範囲外").sum())
    c = int((mon["人工地形_状態"] == "取得不可").sum())
    d = int((pt["人工地形_状態"] == "取得不可").sum())
    return a, b, c, d


def build_artificial_notes(mon, pt):
    """表1の末尾に付ける注記4行のリストを返す（a〜d は3桁区切りなし）"""
    a, b, c, d = count_uncounted(mon, pt)
    return [
        "注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。",
        "注：人工地形は、地形分類（自然地形）の詳細版で値が取れた地点だけで調べています。割合は「人工地形あり」と「人工地形なし」を合わせた数に対する割合です。",
        f"注：数えていない地点：範囲外（詳細版のデータなし）碑 {a}・比較地点 {b}、取得不可 碑 {c}・比較地点 {d}",
        "出典：国土地理院 地形分類（人工地形）を加工して作成",
    ]


def build_artificial_cross_notes(mon, pt):
    """表2の末尾に付ける注記3行のリストを返す（a〜d は3桁区切りなし）"""
    a, b, c, d = count_uncounted(mon, pt)
    return [
        "注：自然地形は地形分類（自然地形）の詳細版の分類名です。割合は、同じ自然地形の中で数えた地点に対する割合です。",
        f"注：数えていない地点：範囲外（詳細版のデータなし）碑 {a}・比較地点 {b}、取得不可 碑 {c}・比較地点 {d}",
        "出典：国土地理院 地形分類（自然地形）・地形分類（人工地形）を加工して作成",
    ]


def main(args=None, base_dir=None):
    """人工地形の集計のメイン処理"""
    if base_dir is None:
        root_dir = get_project_root()
    else:
        root_dir = Path(base_dir)

    if args is None:
        args = sys.argv[1:] if base_dir is None else []

    parser = argparse.ArgumentParser(description="地形分類（人工地形）の県別・全国の集計")
    parser.add_argument(
        "--pref",
        type=str,
        default="all",
        help="県コード（01〜47 のカンマ区切り、または all。省略時は all）",
    )
    parsed = parser.parse_args(args)

    try:
        pref_res = parse_pref_arg(parsed.pref)
    except ValueError as e:
        print(e)
        sys.exit(1)

    is_all = pref_res == "all"
    if is_all:
        pref_codes = sorted(PREFECTURES.keys())
    else:
        pref_codes = pref_res

    missing_prefs = check_artificial_files(pref_codes, root_dir)
    if missing_prefs:
        missing_str = "、".join([f"{PREFECTURES[c]}（{c}）" for c in missing_prefs])
        pref_arg = ",".join(missing_prefs)
        print(f"エラー：ファイルが足りない県があります：{missing_str}")
        print(f'先に実行してください：python src/run_artificial_batch.py --pref "{pref_arg}"')
        sys.exit(1)

    out_dir = root_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    mon_list = []
    pt_list = []
    pref_tables = {}

    for pref in pref_codes:
        mon, pt = load_artificial_pref(pref, root_dir)
        mon_list.append(mon)
        pt_list.append(pt)

        rel_df = extract_relocated(mon)
        rel_ids = rel_df["ID"].tolist()
        df_pref = build_artificial_table(mon, pt, rel_ids)
        notes_pref = build_artificial_notes(mon, pt)
        write_with_notes(df_pref, out_dir / f"landform_artificial_{pref}.csv", notes_pref)
        pref_tables[pref] = df_pref

    all_mon = pd.concat(mon_list, ignore_index=True)
    all_pt = pd.concat(pt_list, ignore_index=True)
    all_rel_df = extract_relocated(all_mon)
    all_rel_ids = all_rel_df["ID"].tolist()

    if is_all:
        df_all = build_artificial_table(all_mon, all_pt, all_rel_ids)
        notes_all = build_artificial_notes(all_mon, all_pt)
        write_with_notes(df_all, out_dir / "landform_artificial_all.csv", notes_all)

        df_cross = build_artificial_cross_table(all_mon, all_pt, all_rel_ids)
        notes_cross = build_artificial_cross_notes(all_mon, all_pt)
        write_with_notes(df_cross, out_dir / "landform_artificial_cross_all.csv", notes_cross)

    # 画面の表示
    total_mon = len(all_mon)
    total_pt = len(all_pt)
    ex_mon = len(all_mon[~all_mon["ID"].isin(all_rel_ids)])
    ex_pt = len(all_pt[~all_pt["元の碑ID"].isin(all_rel_ids)])

    counted_mon = int(all_mon["人工地形_状態"].isin(["取得済", "人工地形なし"]).sum())
    counted_pt = int(all_pt["人工地形_状態"].isin(["取得済", "人工地形なし"]).sum())
    a, b, c, d = count_uncounted(all_mon, all_pt)

    art_mon = int((all_mon["人工地形_状態"] == "取得済").sum())
    art_pt = int((all_pt["人工地形_状態"] == "取得済").sum())
    art_mon_ratio = art_mon / counted_mon if counted_mon > 0 else 0.0
    art_pt_ratio = art_pt / counted_pt if counted_pt > 0 else 0.0

    if is_all:
        print(f"地形分類（人工地形）の集計：{len(pref_codes)}都道府県")
    elif len(pref_codes) == 1:
        p = pref_codes[0]
        print(f"地形分類（人工地形）の集計：{PREFECTURES[p]}（{p}）")
    else:
        print(f"地形分類（人工地形）の集計：{len(pref_codes)}都道府県")

    print(f"碑：全碑 {total_mon:,}基／移転碑を除く {ex_mon:,}基　比較地点：全碑 {total_pt:,}点／移転碑を除く {ex_pt:,}点")
    print(f"人工地形を調べた地点（全碑）：碑 {counted_mon:,}基／比較地点 {counted_pt:,}点")
    print(
        f"数えていない地点（全碑）：範囲外 碑 {a:,}・比較地点 {b:,}、"
        f"取得不可 碑 {c:,}・比較地点 {d:,}"
    )
    print(f"人工地形ありの割合（全碑・全種別）：碑 {art_mon_ratio:.3f}／比較地点 {art_pt_ratio:.3f}")

    if is_all or len(pref_codes) == 1:
        target_df = df_all if is_all else pref_tables[pref_codes[0]]
        sub_df = target_df[
            (target_df["範囲"] == "全碑")
            & (target_df["災害種別"] == "全種別")
            & (target_df["人工地形名"] != "人工地形なし")
        ]
        print("人工地形ごと（全碑・全種別。碑の件数・割合／比較地点の件数・割合）")
        for _, row in sub_df.iterrows():
            m_c = int(row["碑_件数"])
            m_r = float(row["碑_割合"])
            p_c = int(row["比較地点_件数"])
            p_r = float(row["比較地点_割合"])
            print(f"  {row['人工地形名']}：{m_c:,}・{m_r:.3f}／{p_c:,}・{p_r:.3f}")

    print("出力：")
    if is_all:
        print(f"  output/landform_artificial_XX.csv（{len(pref_codes)}ファイル）")
        print("  output/landform_artificial_all.csv")
        print("  output/landform_artificial_cross_all.csv")
    else:
        for p in pref_codes:
            print(f"  output/landform_artificial_{p}.csv")


if __name__ == "__main__":
    main()

