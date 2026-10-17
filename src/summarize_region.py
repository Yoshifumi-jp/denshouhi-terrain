# -*- coding: utf-8 -*-
"""地形分類（自然地形）の地域版（中分類）について、県別および全国の集計表を出力するプログラム。

何をするプログラムか:
data/processed/ の monuments_XX.csv・points_XX.csv・landform_region_XX.csv・landform_region_points_XX.csv を読み込み、
県別（output/landform_region_XX.csv）および全国（output/landform_region_all.csv）の
「範囲（全碑・移転碑を除く）×災害種別×地域版の地形分類」の件数・割合を集計して出力する。

詳細版の集計とは混ぜない理由:
既存の集計（summarize.py・summarize_national.py）が出力する詳細版の表（landform_XX.csv・landform_all.csv）は
自然地形のズーム14〜16（小分類）を集計したものであり、地域版（ズーム13、中分類）とは分類の細かさ・体系が異なるため、
既存の表とは混ぜずに新しいファイル（landform_region_XX.csv・landform_region_all.csv）に出力する。
同じ理由から、本プログラムの中でも「取得済（地域版）」の地点だけを数え、分類の細かさが異なる「取得済（広域版）」は数えない。
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

try:
    from src.prefectures import PREFECTURES
    from src.summarize import extract_relocated, DISASTER_TYPES
    from src.load_monuments import parse_pref_arg
except ImportError:
    from prefectures import PREFECTURES
    from summarize import extract_relocated, DISASTER_TYPES
    from load_monuments import parse_pref_arg


def get_project_root():
    """プロジェクトのルートディレクトリのパスを返す"""
    return Path(__file__).resolve().parent.parent


def check_region_files(pref_codes, base_dir=None):
    """対象の県コードについて、必要な4ファイルが data/processed/ にそろっているか調べ、足りない県コードのリストを返す"""
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
            proc_dir / f"landform_region_{pref}.csv",
            proc_dir / f"landform_region_points_{pref}.csv",
        ]
        if not all(p.exists() for p in required_files):
            missing_prefs.append(pref)

    return missing_prefs


def load_region_pref(pref, base_dir=None):
    """1県分の monuments・points と地域版の地形分類を読み込み、ID で左結合した (mon, pt) を返す"""
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
    mon_reg = pd.read_csv(
        proc_dir / f"landform_region_{pref}.csv",
        dtype={"ID": str, "地域版_コード": str, "地域版_地形分類名": str, "地域版_状態": str},
        encoding="utf-8-sig",
    )
    pt_reg = pd.read_csv(
        proc_dir / f"landform_region_points_{pref}.csv",
        dtype={"ID": str, "地域版_コード": str, "地域版_地形分類名": str, "地域版_状態": str},
        encoding="utf-8-sig",
    )

    reg_cols = ["ID", "地域版_地形分類名", "地域版_コード", "地域版_状態"]
    mon = mon_main.merge(mon_reg[reg_cols], on="ID", how="left")
    pt = pt_main.merge(pt_reg[reg_cols], on="ID", how="left")

    for col in ["地域版_地形分類名", "地域版_コード", "地域版_状態"]:
        mon[col] = mon[col].fillna("").astype(str)
        pt[col] = pt[col].fillna("").astype(str)

    return mon, pt


def _code_sort_key(code_str):
    """地域版コードを数値の小さい順で並べるためのソートキーを返す"""
    try:
        return (0, int(code_str), str(code_str))
    except (ValueError, TypeError):
        return (1, 0, str(code_str))


def build_region_table(mon, pt, relocated_ids):
    """mon・pt・移転碑IDリストから、地域版の地形分類の集計 DataFrame を作成して返す"""
    ranges = ["全碑", "移転碑を除く"]
    disaster_types = ["全種別"] + DISASTER_TYPES

    # そのファイル（全碑・全種別）に1回でも出てくる「取得済（地域版）」の分類を集め、並び順を決める
    # 順番：全碑・全種別の比較地点の件数の多い順 → 同数なら全碑・全種別の碑の件数の多い順 → 同数ならコードの数値の小さい順
    m_all_valid = mon[mon["地域版_状態"] == "取得済（地域版）"]
    p_all_valid = pt[pt["地域版_状態"] == "取得済（地域版）"]

    m_all_counts = {}
    for name, code in zip(m_all_valid["地域版_地形分類名"], m_all_valid["地域版_コード"]):
        key = (str(name), str(code))
        m_all_counts[key] = m_all_counts.get(key, 0) + 1

    p_all_counts = {}
    for name, code in zip(p_all_valid["地域版_地形分類名"], p_all_valid["地域版_コード"]):
        key = (str(name), str(code))
        p_all_counts[key] = p_all_counts.get(key, 0) + 1

    all_keys = set(m_all_counts.keys()) | set(p_all_counts.keys())
    ordered_lfs = sorted(
        all_keys,
        key=lambda k: (
            -p_all_counts.get(k, 0),
            -m_all_counts.get(k, 0),
            _code_sort_key(k[1]),
        ),
    )

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

            m_valid = m_sub[m_sub["地域版_状態"] == "取得済（地域版）"]
            p_valid = p_sub[p_sub["地域版_状態"] == "取得済（地域版）"]

            m_total = len(m_valid)
            p_total = len(p_valid)

            m_counts = {}
            for name, code in zip(m_valid["地域版_地形分類名"], m_valid["地域版_コード"]):
                key = (str(name), str(code))
                m_counts[key] = m_counts.get(key, 0) + 1

            p_counts = {}
            for name, code in zip(p_valid["地域版_地形分類名"], p_valid["地域版_コード"]):
                key = (str(name), str(code))
                p_counts[key] = p_counts.get(key, 0) + 1

            for lf_name, lf_code in ordered_lfs:
                m_c = m_counts.get((lf_name, lf_code), 0)
                p_c = p_counts.get((lf_name, lf_code), 0)
                m_r = m_c / m_total if m_total > 0 else 0.0
                p_r = p_c / p_total if p_total > 0 else 0.0
                rows.append([r, dt_name, lf_name, lf_code, m_c, m_r, p_c, p_r])

    cols = [
        "範囲",
        "災害種別",
        "地形分類名",
        "地形分類コード",
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
    """全碑の範囲で数えていない地点の件数 (a, b, c, d, e, f) を返す"""
    a = int((mon["地域版_状態"] == "データなし").sum())
    b = int((pt["地域版_状態"] == "データなし").sum())
    c = int((mon["地域版_状態"] == "取得済（広域版）").sum())
    d = int((pt["地域版_状態"] == "取得済（広域版）").sum())
    e = int((mon["地域版_状態"] == "取得不可").sum())
    f = int((pt["地域版_状態"] == "取得不可").sum())
    return a, b, c, d, e, f


def build_region_notes(mon, pt):
    """CSV の末尾に付ける注記4行のリストを返す（a〜f は3桁区切りなし）"""
    a, b, c, d, e, f = count_uncounted(mon, pt)
    return [
        "注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。",
        "注：地形分類（自然地形）の地域版（中分類）で値が取れた地点だけを数えています。詳細版の表（landform_XX.csv・landform_all.csv）とは分類の細かさが違うため、別の表にしています。",
        f"注：数えていない地点：データなし 碑 {a}・比較地点 {b}、広域版で補った地点 碑 {c}・比較地点 {d}、取得不可 碑 {e}・比較地点 {f}",
        "出典：国土地理院 地形分類（自然地形）を加工して作成",
    ]


def write_with_notes(df, path, notes):
    """データフレームを UTF-8 BOM 付き・index なし・改行 LF で CSV 出力し、続けて notes の各行を LF 付きで書く"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        df.to_csv(f, index=False, lineterminator="\n")
        for note in notes:
            line = note if note.endswith("\n") else note + "\n"
            f.write(line)


def main(args=None, base_dir=None):
    """地域版の地形分類集計のメイン処理"""
    if base_dir is None:
        root_dir = get_project_root()
    else:
        root_dir = Path(base_dir)

    if args is None:
        args = sys.argv[1:] if base_dir is None else []

    parser = argparse.ArgumentParser(description="地形分類（地域版）の県別・全国の集計")
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

    missing_prefs = check_region_files(pref_codes, root_dir)
    if missing_prefs:
        missing_str = "、".join([f"{PREFECTURES[c]}（{c}）" for c in missing_prefs])
        pref_arg = ",".join(missing_prefs)
        print(f"エラー：ファイルが足りない県があります：{missing_str}")
        print(f'先に実行してください：python src/run_region_batch.py --pref "{pref_arg}"')
        sys.exit(1)

    out_dir = root_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    mon_list = []
    pt_list = []
    pref_tables = {}

    for pref in pref_codes:
        mon, pt = load_region_pref(pref, root_dir)
        mon_list.append(mon)
        pt_list.append(pt)

        rel_df = extract_relocated(mon)
        rel_ids = rel_df["ID"].tolist()
        df_pref = build_region_table(mon, pt, rel_ids)
        notes_pref = build_region_notes(mon, pt)
        write_with_notes(df_pref, out_dir / f"landform_region_{pref}.csv", notes_pref)
        pref_tables[pref] = df_pref

    all_mon = pd.concat(mon_list, ignore_index=True)
    all_pt = pd.concat(pt_list, ignore_index=True)
    all_rel_df = extract_relocated(all_mon)
    all_rel_ids = all_rel_df["ID"].tolist()

    if is_all:
        df_all = build_region_table(all_mon, all_pt, all_rel_ids)
        notes_all = build_region_notes(all_mon, all_pt)
        write_with_notes(df_all, out_dir / "landform_region_all.csv", notes_all)

    # 画面の表示
    total_mon = len(all_mon)
    total_pt = len(all_pt)
    ex_mon = len(all_mon[~all_mon["ID"].isin(all_rel_ids)])
    ex_pt = len(all_pt[~all_pt["元の碑ID"].isin(all_rel_ids)])

    counted_mon = int((all_mon["地域版_状態"] == "取得済（地域版）").sum())
    counted_pt = int((all_pt["地域版_状態"] == "取得済（地域版）").sum())
    a, b, c, d, e, f = count_uncounted(all_mon, all_pt)

    if is_all:
        print(f"地形分類（地域版）の集計：{len(pref_codes)}都道府県")
    elif len(pref_codes) == 1:
        p = pref_codes[0]
        print(f"地形分類（地域版）の集計：{PREFECTURES[p]}（{p}）")
    else:
        print(f"地形分類（地域版）の集計：{len(pref_codes)}都道府県")

    print(f"碑：全碑 {total_mon:,}基／移転碑を除く {ex_mon:,}基　比較地点：全碑 {total_pt:,}点／移転碑を除く {ex_pt:,}点")
    print(f"地域版で数えた地点（全碑）：碑 {counted_mon:,}基／比較地点 {counted_pt:,}点")
    print(
        f"数えていない地点（全碑）：データなし 碑 {a:,}・比較地点 {b:,}、"
        f"広域版 碑 {c:,}・比較地点 {d:,}、取得不可 碑 {e:,}・比較地点 {f:,}"
    )

    if is_all:
        top_df = df_all[(df_all["範囲"] == "全碑") & (df_all["災害種別"] == "全種別")].head(5)
        print("全碑・全種別の上位5分類（碑の割合／比較地点の割合）")
        for _, row in top_df.iterrows():
            print(f"  {row['地形分類名']}：{float(row['碑_割合']):.3f}／{float(row['比較地点_割合']):.3f}")
    elif len(pref_codes) == 1:
        df_single = pref_tables[pref_codes[0]]
        top_df = df_single[(df_single["範囲"] == "全碑") & (df_single["災害種別"] == "全種別")].head(5)
        print("全碑・全種別の上位5分類（碑の割合／比較地点の割合）")
        for _, row in top_df.iterrows():
            print(f"  {row['地形分類名']}：{float(row['碑_割合']):.3f}／{float(row['比較地点_割合']):.3f}")

    print("出力：")
    if is_all:
        print(f"  output/landform_region_XX.csv（{len(pref_codes)}ファイル）")
        print("  output/landform_region_all.csv")
    else:
        for p in pref_codes:
            print(f"  output/landform_region_{p}.csv")


if __name__ == "__main__":
    main()

