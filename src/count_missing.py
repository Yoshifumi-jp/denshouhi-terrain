# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd

try:
    from src.prefectures import PREFECTURES
except ImportError:
    from prefectures import PREFECTURES

# M9 データ調査（2026-09-24 版）の全国の碑の数
M9_TOTAL = 2481

# 出力CSVの列定義（順序固定）
COLUMNS = [
    "県コード", "県名", "碑_数", "比較地点_数",
    "標高傾斜_取得不可_碑", "標高傾斜_取得不可_比較地点",
    "ハザード_取得不可_碑", "ハザード_取得不可_比較地点",
    "地形分類_データなし_碑", "地形分類_データなし_碑_割合",
    "地形分類_データなし_比較地点", "地形分類_データなし_比較地点_割合",
    "河川標高_取得不可_碑", "河川標高_取得不可_比較地点",
    "河川_1000m超_碑", "河川_1000m超_比較地点",
    "海岸_対象外_碑", "海岸_対象外_比較地点",
    "通信エラー_碑", "通信エラー_比較地点",
    "地域版_データなし_碑", "地域版_データなし_比較地点",
    "地域版_取得不可_碑", "地域版_取得不可_比較地点",
    "詳細版データなしを補えた_碑", "詳細版データなしを補えた_比較地点",
    "人工地形_範囲外_碑", "人工地形_範囲外_比較地点",
    "人工地形_取得不可_碑", "人工地形_取得不可_比較地点"
]

REGION_COLS = [
    "地域版_データなし_碑", "地域版_データなし_比較地点",
    "地域版_取得不可_碑", "地域版_取得不可_比較地点",
    "詳細版データなしを補えた_碑", "詳細版データなしを補えた_比較地点"
]

ARTIFICIAL_COLS = [
    "人工地形_範囲外_碑", "人工地形_範囲外_比較地点",
    "人工地形_取得不可_碑", "人工地形_取得不可_比較地点"
]


def get_project_root():
    """プロジェクトのルートディレクトリのパスを返す"""
    return Path(__file__).resolve().parent.parent


def count_communication_errors(df):
    """データフレームの各行で、いずれかの列に「通信エラー」を含む行数を数える"""
    if df.empty:
        return 0
    mask = df.astype(str).apply(lambda col: col.str.contains("通信エラー", regex=False)).any(axis=1)
    return int(mask.sum())


def count_region(base_dir=None, pref_codes=None):
    """
    指定ディレクトリ下の data/processed から地域版の件数・補完件数を集計し、
    (県コード別の6列辞書, region_missing_prefs, データなしの碑リスト) を返す。
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"
    if pref_codes is None:
        pref_codes = sorted(PREFECTURES.keys())

    region_counts = {}
    region_missing_prefs = []
    region_no_data_monuments = []

    valid_region_prefs = []

    for pref in pref_codes:
        reg_m_file = proc_dir / f"landform_region_{pref}.csv"
        reg_p_file = proc_dir / f"landform_region_points_{pref}.csv"
        land_m_file = proc_dir / f"landform_{pref}.csv"
        land_p_file = proc_dir / f"landform_points_{pref}.csv"

        if not (reg_m_file.exists() and reg_p_file.exists()):
            region_missing_prefs.append(pref)
            region_counts[pref] = {col: "" for col in REGION_COLS}
            continue

        valid_region_prefs.append(pref)

        df_reg_m = pd.read_csv(reg_m_file, dtype={"ID": str}, encoding="utf-8-sig")
        df_reg_p = pd.read_csv(reg_p_file, dtype={"ID": str}, encoding="utf-8-sig")
        df_land_m = pd.read_csv(land_m_file, dtype={"ID": str}, encoding="utf-8-sig") if land_m_file.exists() else pd.DataFrame()
        df_land_p = pd.read_csv(land_p_file, dtype={"ID": str}, encoding="utf-8-sig") if land_p_file.exists() else pd.DataFrame()

        # 地域版_データなし
        if "地域版_状態" in df_reg_m.columns:
            no_data_mask_m = df_reg_m["地域版_状態"] == "データなし"
            reg_nd_m = int(no_data_mask_m.sum())
            for _, r in df_reg_m[no_data_mask_m].iterrows():
                m_id = str(r["ID"]) if "ID" in r and pd.notna(r["ID"]) else ""
                m_name = str(r["碑名"]) if "碑名" in r and pd.notna(r["碑名"]) else ""
                region_no_data_monuments.append((m_id, m_name))
        else:
            reg_nd_m = 0

        reg_nd_p = int((df_reg_p["地域版_状態"] == "データなし").sum()) if "地域版_状態" in df_reg_p.columns else 0

        # 地域版_取得不可
        reg_na_m = int((df_reg_m["地域版_状態"] == "取得不可").sum()) if "地域版_状態" in df_reg_m.columns else 0
        reg_na_p = int((df_reg_p["地域版_状態"] == "取得不可").sum()) if "地域版_状態" in df_reg_p.columns else 0

        # 詳細版データなしを補えた（IDで結合）
        comp_m = 0
        if not df_land_m.empty and "ID" in df_land_m.columns and "地形分類_状態" in df_land_m.columns and "ID" in df_reg_m.columns and "地域版_状態" in df_reg_m.columns:
            merged_m = pd.merge(
                df_land_m[["ID", "地形分類_状態"]],
                df_reg_m[["ID", "地域版_状態"]],
                on="ID",
                how="inner"
            )
            comp_m = int((
                (merged_m["地形分類_状態"] == "データなし") &
                (merged_m["地域版_状態"].isin(["取得済（地域版）", "取得済（広域版）"]))
            ).sum())

        comp_p = 0
        if not df_land_p.empty and "ID" in df_land_p.columns and "地形分類_状態" in df_land_p.columns and "ID" in df_reg_p.columns and "地域版_状態" in df_reg_p.columns:
            merged_p = pd.merge(
                df_land_p[["ID", "地形分類_状態"]],
                df_reg_p[["ID", "地域版_状態"]],
                on="ID",
                how="inner"
            )
            comp_p = int((
                (merged_p["地形分類_状態"] == "データなし") &
                (merged_p["地域版_状態"].isin(["取得済（地域版）", "取得済（広域版）"]))
            ).sum())

        region_counts[pref] = {
            "地域版_データなし_碑": reg_nd_m,
            "地域版_データなし_比較地点": reg_nd_p,
            "地域版_取得不可_碑": reg_na_m,
            "地域版_取得不可_比較地点": reg_na_p,
            "詳細版データなしを補えた_碑": comp_m,
            "詳細版データなしを補えた_比較地点": comp_p,
        }

    if valid_region_prefs:
        region_counts["全国"] = {
            col: sum(region_counts[p][col] for p in valid_region_prefs)
            for col in REGION_COLS
        }
    else:
        region_counts["全国"] = {col: "" for col in REGION_COLS}

    return region_counts, region_missing_prefs, region_no_data_monuments


def count_artificial(base_dir=None, pref_codes=None):
    """
    指定ディレクトリ下の data/processed から人工地形の範囲外・取得不可件数を集計し、
    (県コード別の4列の辞書〔"全国" を含む〕, artificial_missing_prefs) を返す。
    範囲外は詳細版のデータなしと同じ数になるはず。
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"
    if pref_codes is None:
        pref_codes = sorted(PREFECTURES.keys())

    artificial_counts = {}
    artificial_missing_prefs = []
    valid_artificial_prefs = []

    for pref in pref_codes:
        art_m_file = proc_dir / f"landform_artificial_{pref}.csv"
        art_p_file = proc_dir / f"landform_artificial_points_{pref}.csv"

        if not (art_m_file.exists() and art_p_file.exists()):
            artificial_missing_prefs.append(pref)
            artificial_counts[pref] = {col: "" for col in ARTIFICIAL_COLS}
            continue

        valid_artificial_prefs.append(pref)

        df_art_m = pd.read_csv(art_m_file, dtype={"ID": str}, encoding="utf-8-sig")
        df_art_p = pd.read_csv(art_p_file, dtype={"ID": str}, encoding="utf-8-sig")

        # 人工地形_範囲外
        art_out_m = int((df_art_m["人工地形_状態"] == "範囲外").sum()) if "人工地形_状態" in df_art_m.columns else 0
        art_out_p = int((df_art_p["人工地形_状態"] == "範囲外").sum()) if "人工地形_状態" in df_art_p.columns else 0

        # 人工地形_取得不可
        art_na_m = int((df_art_m["人工地形_状態"] == "取得不可").sum()) if "人工地形_状態" in df_art_m.columns else 0
        art_na_p = int((df_art_p["人工地形_状態"] == "取得不可").sum()) if "人工地形_状態" in df_art_p.columns else 0

        artificial_counts[pref] = {
            "人工地形_範囲外_碑": art_out_m,
            "人工地形_範囲外_比較地点": art_out_p,
            "人工地形_取得不可_碑": art_na_m,
            "人工地形_取得不可_比較地点": art_na_p,
        }

    if valid_artificial_prefs:
        artificial_counts["全国"] = {
            col: sum(artificial_counts[p][col] for p in valid_artificial_prefs)
            for col in ARTIFICIAL_COLS
        }
    else:
        artificial_counts["全国"] = {col: "" for col in ARTIFICIAL_COLS}

    return artificial_counts, artificial_missing_prefs


def count_missing(base_dir=None):
    """
    指定ディレクトリ下の data/processed を読み込み、
    県別および全国合計の欠損・対象外件数を集計する。
    """
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    proc_dir = base_dir / "data" / "processed"
    rows = []
    missing_prefs = []

    haz_cols = ["洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"]

    for pref in sorted(PREFECTURES.keys()):
        files = {
            "elev_m": proc_dir / f"elevation_{pref}.csv",
            "elev_p": proc_dir / f"elevation_points_{pref}.csv",
            "haz_m": proc_dir / f"hazard_{pref}.csv",
            "haz_p": proc_dir / f"hazard_points_{pref}.csv",
            "land_m": proc_dir / f"landform_{pref}.csv",
            "land_p": proc_dir / f"landform_points_{pref}.csv",
            "riv_m": proc_dir / f"river_coast_{pref}.csv",
            "riv_p": proc_dir / f"river_coast_points_{pref}.csv",
        }

        # 8ファイルのいずれかが欠けている県は集計から除外
        if not all(p.exists() for p in files.values()):
            missing_prefs.append(pref)
            continue

        df_e_m = pd.read_csv(files["elev_m"], encoding="utf-8-sig")
        df_e_p = pd.read_csv(files["elev_p"], encoding="utf-8-sig")
        df_h_m = pd.read_csv(files["haz_m"], encoding="utf-8-sig")
        df_h_p = pd.read_csv(files["haz_p"], encoding="utf-8-sig")
        df_l_m = pd.read_csv(files["land_m"], encoding="utf-8-sig")
        df_l_p = pd.read_csv(files["land_p"], encoding="utf-8-sig")
        df_r_m = pd.read_csv(files["riv_m"], encoding="utf-8-sig")
        df_r_p = pd.read_csv(files["riv_p"], encoding="utf-8-sig")

        m_cnt = len(df_e_m)
        p_cnt = len(df_e_p)

        # 標高傾斜の取得不可
        elev_na_m = int(df_e_m["取得状態"].astype(str).str.contains("取得不可", regex=False).sum()) if "取得状態" in df_e_m.columns else 0
        elev_na_p = int(df_e_p["取得状態"].astype(str).str.contains("取得不可", regex=False).sum()) if "取得状態" in df_e_p.columns else 0

        # ハザードの取得不可（4列のどれかが取得不可）
        h_m_cols = [c for c in haz_cols if c in df_h_m.columns]
        haz_na_m = int((df_h_m[h_m_cols] == "取得不可").any(axis=1).sum()) if h_m_cols else 0
        h_p_cols = [c for c in haz_cols if c in df_h_p.columns]
        haz_na_p = int((df_h_p[h_p_cols] == "取得不可").any(axis=1).sum()) if h_p_cols else 0

        # 地形分類のデータなし
        land_na_m = int((df_l_m["地形分類_状態"] == "データなし").sum()) if "地形分類_状態" in df_l_m.columns else 0
        land_na_p = int((df_l_p["地形分類_状態"] == "データなし").sum()) if "地形分類_状態" in df_l_p.columns else 0

        land_ratio_m = round(land_na_m / m_cnt, 3) if m_cnt > 0 and land_na_m > 0 else ""
        land_ratio_p = round(land_na_p / p_cnt, 3) if p_cnt > 0 and land_na_p > 0 else ""

        # 河川・海岸の状態
        riv_na_m = int(df_r_m["河川_状態"].astype(str).str.contains("取得不可", regex=False).sum()) if "河川_状態" in df_r_m.columns else 0
        riv_na_p = int(df_r_p["河川_状態"].astype(str).str.contains("取得不可", regex=False).sum()) if "河川_状態" in df_r_p.columns else 0

        riv_1000_m = int(df_r_m["河川_状態"].astype(str).str.contains("1000m超", regex=False).sum()) if "河川_状態" in df_r_m.columns else 0
        riv_1000_p = int(df_r_p["河川_状態"].astype(str).str.contains("1000m超", regex=False).sum()) if "河川_状態" in df_r_p.columns else 0

        coast_na_m = int(df_r_m["海岸_状態"].astype(str).str.contains("海のない県", regex=False).sum()) if "海岸_状態" in df_r_m.columns else 0
        coast_na_p = int(df_r_p["海岸_状態"].astype(str).str.contains("海のない県", regex=False).sum()) if "海岸_状態" in df_r_p.columns else 0

        # 通信エラー
        comm_m = sum(count_communication_errors(df) for df in [df_e_m, df_h_m, df_l_m, df_r_m])
        comm_p = sum(count_communication_errors(df) for df in [df_e_p, df_h_p, df_l_p, df_r_p])

        rows.append({
            "県コード": pref,
            "県名": PREFECTURES[pref],
            "碑_数": m_cnt,
            "比較地点_数": p_cnt,
            "標高傾斜_取得不可_碑": elev_na_m,
            "標高傾斜_取得不可_比較地点": elev_na_p,
            "ハザード_取得不可_碑": haz_na_m,
            "ハザード_取得不可_比較地点": haz_na_p,
            "地形分類_データなし_碑": land_na_m,
            "地形分類_データなし_碑_割合": land_ratio_m,
            "地形分類_データなし_比較地点": land_na_p,
            "地形分類_データなし_比較地点_割合": land_ratio_p,
            "河川標高_取得不可_碑": riv_na_m,
            "河川標高_取得不可_比較地点": riv_na_p,
            "河川_1000m超_碑": riv_1000_m,
            "河川_1000m超_比較地点": riv_1000_p,
            "海岸_対象外_碑": coast_na_m,
            "海岸_対象外_比較地点": coast_na_p,
            "通信エラー_碑": comm_m,
            "通信エラー_比較地点": comm_p,
        })

    # 全国の合計行
    if rows:
        tot_m_cnt = sum(r["碑_数"] for r in rows)
        tot_p_cnt = sum(r["比較地点_数"] for r in rows)
        tot_elev_m = sum(r["標高傾斜_取得不可_碑"] for r in rows)
        tot_elev_p = sum(r["標高傾斜_取得不可_比較地点"] for r in rows)
        tot_haz_m = sum(r["ハザード_取得不可_碑"] for r in rows)
        tot_haz_p = sum(r["ハザード_取得不可_比較地点"] for r in rows)
        tot_land_m = sum(r["地形分類_データなし_碑"] for r in rows)
        tot_land_p = sum(r["地形分類_データなし_比較地点"] for r in rows)
        tot_land_ratio_m = round(tot_land_m / tot_m_cnt, 3) if tot_m_cnt > 0 and tot_land_m > 0 else ""
        tot_land_ratio_p = round(tot_land_p / tot_p_cnt, 3) if tot_p_cnt > 0 and tot_land_p > 0 else ""
        tot_riv_na_m = sum(r["河川標高_取得不可_碑"] for r in rows)
        tot_riv_na_p = sum(r["河川標高_取得不可_比較地点"] for r in rows)
        tot_riv_1000_m = sum(r["河川_1000m超_碑"] for r in rows)
        tot_riv_1000_p = sum(r["河川_1000m超_比較地点"] for r in rows)
        tot_coast_m = sum(r["海岸_対象外_碑"] for r in rows)
        tot_coast_p = sum(r["海岸_対象外_比較地点"] for r in rows)
        tot_comm_m = sum(r["通信エラー_碑"] for r in rows)
        tot_comm_p = sum(r["通信エラー_比較地点"] for r in rows)

        total_row = {
            "県コード": "全国",
            "県名": "合計",
            "碑_数": tot_m_cnt,
            "比較地点_数": tot_p_cnt,
            "標高傾斜_取得不可_碑": tot_elev_m,
            "標高傾斜_取得不可_比較地点": tot_elev_p,
            "ハザード_取得不可_碑": tot_haz_m,
            "ハザード_取得不可_比較地点": tot_haz_p,
            "地形分類_データなし_碑": tot_land_m,
            "地形分類_データなし_碑_割合": tot_land_ratio_m,
            "地形分類_データなし_比較地点": tot_land_p,
            "地形分類_データなし_比較地点_割合": tot_land_ratio_p,
            "河川標高_取得不可_碑": tot_riv_na_m,
            "河川標高_取得不可_比較地点": tot_riv_na_p,
            "河川_1000m超_碑": tot_riv_1000_m,
            "河川_1000m超_比較地点": tot_riv_1000_p,
            "海岸_対象外_碑": tot_coast_m,
            "海岸_対象外_比較地点": tot_coast_p,
            "通信エラー_碑": tot_comm_m,
            "通信エラー_比較地点": tot_comm_p,
        }
    else:
        total_row = {
            "県コード": "全国",
            "県名": "合計",
            "碑_数": 0,
            "比較地点_数": 0,
            "標高傾斜_取得不可_碑": 0,
            "標高傾斜_取得不可_比較地点": 0,
            "ハザード_取得不可_碑": 0,
            "ハザード_取得不可_比較地点": 0,
            "地形分類_データなし_碑": 0,
            "地形分類_データなし_碑_割合": "",
            "地形分類_データなし_比較地点": 0,
            "地形分類_データなし_比較地点_割合": "",
            "河川標高_取得不可_碑": 0,
            "河川標高_取得不可_比較地点": 0,
            "河川_1000m超_碑": 0,
            "河川_1000m超_比較地点": 0,
            "海岸_対象外_碑": 0,
            "海岸_対象外_比較地点": 0,
            "通信エラー_碑": 0,
            "通信エラー_比較地点": 0,
        }

    # 地域版および人工地形の集計を結合
    valid_pref_codes = [r["県コード"] for r in rows]
    region_counts, _, _ = count_region(base_dir, valid_pref_codes)
    artificial_counts, _ = count_artificial(base_dir, valid_pref_codes)

    for r in rows:
        r.update(region_counts[r["県コード"]])
        r.update(artificial_counts[r["県コード"]])
    total_row.update(region_counts["全国"])
    total_row.update(artificial_counts["全国"])

    all_rows = rows + [total_row]
    df_result = pd.DataFrame(all_rows, columns=COLUMNS)
    return df_result, missing_prefs


def main(args=None, base_dir=None):
    """欠損・対象外件数を集計し、CSV出力および結果表示を行う"""
    if base_dir is None:
        base_dir = get_project_root()
    else:
        base_dir = Path(base_dir)

    df, missing_prefs = count_missing(base_dir)

    out_dir = base_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "missing_counts.csv"
    df.to_csv(out_file, index=False, encoding="utf-8-sig", lineterminator="\n")

    # 表示文の作成
    pref_rows = df[df["県コード"] != "全国"]
    total_row = df[df["県コード"] == "全国"].iloc[0]

    valid_pref_codes = list(pref_rows["県コード"])
    _, region_missing_prefs, region_no_data_monuments = count_region(base_dir, valid_pref_codes)
    _, artificial_missing_prefs = count_artificial(base_dir, valid_pref_codes)

    valid_count = len(pref_rows)
    if missing_prefs:
        missing_names = [PREFECTURES.get(p, p) for p in missing_prefs]
        target_str = f"対象：{valid_count}都道府県（ファイルが足りない県：{'、'.join(missing_names)}）"
    else:
        target_str = f"対象：{valid_count}都道府県（ファイルが足りない県：なし）"

    tot_m = int(total_row["碑_数"])
    tot_p = int(total_row["比較地点_数"])
    if tot_m == M9_TOTAL:
        m_total_str = f"碑の合計：{tot_m:,}基（M9 の全国件数 {M9_TOTAL:,}基と一致）"
    else:
        m_total_str = f"碑の合計：{tot_m:,}基（M9 の全国件数 {M9_TOTAL:,}基と不一致）"

    p_total_str = f"比較地点の合計：{tot_p:,}点"
    elev_str = f"標高・傾斜の取得不可：碑 {int(total_row['標高傾斜_取得不可_碑']):,}／比較地点 {int(total_row['標高傾斜_取得不可_比較地点']):,}"
    haz_str = f"ハザードの取得不可：碑 {int(total_row['ハザード_取得不可_碑']):,}／比較地点 {int(total_row['ハザード_取得不可_比較地点']):,}"

    m_land_pct = (int(total_row["地形分類_データなし_碑"]) / tot_m * 100) if tot_m > 0 else 0.0
    p_land_pct = (int(total_row["地形分類_データなし_比較地点"]) / tot_p * 100) if tot_p > 0 else 0.0
    land_str = f"地形分類のデータなし：碑 {int(total_row['地形分類_データなし_碑']):,}（{m_land_pct:.1f}%）／比較地点 {int(total_row['地形分類_データなし_比較地点']):,}（{p_land_pct:.1f}%）"

    # 地域版の表示文（4行、またはそろっている県が0のときは1行のみ）
    region_lines = []
    if region_missing_prefs:
        reg_missing_items = [f"{PREFECTURES.get(p, p)}（{p}）" for p in region_missing_prefs]
        codes_str = ",".join(region_missing_prefs)
        reg_line1 = f"地域版のファイルが足りない県：{'、'.join(reg_missing_items)}（地域版の列は空欄です。先に実行してください：python src/run_region_batch.py --pref \"{codes_str}\"）"
    else:
        reg_line1 = "地域版のファイルが足りない県：なし"
    region_lines.append(reg_line1)

    reg_valid_rows = pref_rows[~pref_rows["県コード"].isin(region_missing_prefs)]
    if len(reg_valid_rows) > 0:
        reg_tot_m = int(reg_valid_rows["碑_数"].sum())
        reg_tot_p = int(reg_valid_rows["比較地点_数"].sum())
        reg_land_na_m = int(reg_valid_rows["地形分類_データなし_碑"].sum())
        reg_land_na_p = int(reg_valid_rows["地形分類_データなし_比較地点"].sum())

        reg_nd_m = int(total_row["地域版_データなし_碑"])
        reg_nd_p = int(total_row["地域版_データなし_比較地点"])
        reg_na_m = int(total_row["地域版_取得不可_碑"])
        reg_na_p = int(total_row["地域版_取得不可_比較地点"])
        comp_m = int(total_row["詳細版データなしを補えた_碑"])
        comp_p = int(total_row["詳細版データなしを補えた_比較地点"])

        reg_nd_m_pct = (reg_nd_m / reg_tot_m * 100) if reg_tot_m > 0 else 0.0
        reg_nd_p_pct = (reg_nd_p / reg_tot_p * 100) if reg_tot_p > 0 else 0.0
        reg_line2 = (
            f"地形分類（地域版）のデータなし：碑 {reg_nd_m:,}（{reg_nd_m_pct:.1f}%）／"
            f"比較地点 {reg_nd_p:,}（{reg_nd_p_pct:.1f}%）、取得不可：碑 {reg_na_m:,}／比較地点 {reg_na_p:,}"
        )

        comp_m_pct = (comp_m / reg_land_na_m * 100) if reg_land_na_m > 0 else 0.0
        comp_p_pct = (comp_p / reg_land_na_p * 100) if reg_land_na_p > 0 else 0.0
        reg_line3 = (
            f"詳細版のデータなしを地域版・広域版で補えた地点：碑 {comp_m:,}／{reg_land_na_m:,}（{comp_m_pct:.1f}%）、"
            f"比較地点 {comp_p:,}／{reg_land_na_p:,}（{comp_p_pct:.1f}%）"
        )

        if not region_no_data_monuments:
            mon_list_str = "なし"
        else:
            shown = [f"{mid} {mname}" for mid, mname in region_no_data_monuments[:10]]
            mon_list_str = "、".join(shown)
            if len(region_no_data_monuments) > 10:
                mon_list_str += f"、ほか {len(region_no_data_monuments) - 10}基"
        reg_line4 = f"地形分類（地域版）のデータなしの碑：{mon_list_str}"

        region_lines.extend([reg_line2, reg_line3, reg_line4])

    # 人工地形の表示文（3行、またはそろっている県が0のときは1行のみ）
    artificial_lines = []
    if artificial_missing_prefs:
        art_missing_items = [f"{PREFECTURES.get(p, p)}（{p}）" for p in artificial_missing_prefs]
        art_codes_str = ",".join(artificial_missing_prefs)
        art_line1 = f"人工地形のファイルが足りない県：{'、'.join(art_missing_items)}（人工地形の列は空欄です。先に実行してください：python src/run_artificial_batch.py --pref \"{art_codes_str}\"）"
    else:
        art_line1 = "人工地形のファイルが足りない県：なし"
    artificial_lines.append(art_line1)

    art_valid_rows = pref_rows[~pref_rows["県コード"].isin(artificial_missing_prefs)]
    if len(art_valid_rows) > 0:
        art_tot_m = int(art_valid_rows["碑_数"].sum())
        art_tot_p = int(art_valid_rows["比較地点_数"].sum())

        art_out_m = int(total_row["人工地形_範囲外_碑"])
        art_out_p = int(total_row["人工地形_範囲外_比較地点"])
        art_na_m = int(total_row["人工地形_取得不可_碑"])
        art_na_p = int(total_row["人工地形_取得不可_比較地点"])

        art_out_m_pct = (art_out_m / art_tot_m * 100) if art_tot_m > 0 else 0.0
        art_out_p_pct = (art_out_p / art_tot_p * 100) if art_tot_p > 0 else 0.0
        art_line2 = (
            f"地形分類（人工地形）の範囲外：碑 {art_out_m:,}（{art_out_m_pct:.1f}%）／"
            f"比較地点 {art_out_p:,}（{art_out_p_pct:.1f}%）、取得不可：碑 {art_na_m:,}／比較地点 {art_na_p:,}"
        )

        mismatch_prefs = []
        for _, r in art_valid_rows.iterrows():
            p_code = r["県コード"]
            if int(r["人工地形_範囲外_碑"]) != int(r["地形分類_データなし_碑"]) or int(r["人工地形_範囲外_比較地点"]) != int(r["地形分類_データなし_比較地点"]):
                mismatch_prefs.append(p_code)

        if not mismatch_prefs:
            art_line3 = f"人工地形の範囲外と地形分類（詳細版）のデータなし：一致（碑 {art_out_m:,}・比較地点 {art_out_p:,}）"
        else:
            mismatch_items = [f"{PREFECTURES.get(p, p)}（{p}）" for p in mismatch_prefs]
            mismatch_codes = ",".join(mismatch_prefs)
            art_line3 = (
                f"人工地形の範囲外と地形分類（詳細版）のデータなし：不一致の県があります：{'、'.join(mismatch_items)}"
                f"（先に実行してください：python src/run_artificial_batch.py --pref \"{mismatch_codes}\"）"
            )

        artificial_lines.extend([art_line2, art_line3])

    riv_na_str = f"河川の標高の取得不可：碑 {int(total_row['河川標高_取得不可_碑']):,}／比較地点 {int(total_row['河川標高_取得不可_比較地点']):,}"
    riv_1000_str = f"（参考）河川まで1000m超で対象外：碑 {int(total_row['河川_1000m超_碑']):,}／比較地点 {int(total_row['河川_1000m超_比較地点']):,}"
    coast_str = f"（参考）海のない県で海岸は対象外：碑 {int(total_row['海岸_対象外_碑']):,}／比較地点 {int(total_row['海岸_対象外_比較地点']):,}"
    comm_str = f"通信エラー：碑 {int(total_row['通信エラー_碑']):,}／比較地点 {int(total_row['通信エラー_比較地点']):,}"

    # 地形分類のデータなしの割合が高い県（碑）：大きい順に5県（同じ割合なら県コード順）
    pref_list = []
    for _, row in pref_rows.iterrows():
        m_cnt = int(row["碑_数"])
        land_cnt = int(row["地形分類_データなし_碑"])
        ratio = (land_cnt / m_cnt) if m_cnt > 0 else 0.0
        pref_list.append((row["県コード"], row["県名"], ratio))

    sorted_prefs = sorted(pref_list, key=lambda x: (-x[2], x[0]))
    top5 = sorted_prefs[:5]
    top5_strs = [f"{name} {round(ratio * 100)}%" for _, name, ratio in top5]
    top5_line = f"地形分類のデータなしの割合が高い県（碑）：{'、'.join(top5_strs)}"

    try:
        rel_path = out_file.relative_to(base_dir).as_posix()
    except ValueError:
        rel_path = out_file.as_posix()
    out_line = f"出力：{rel_path}"

    print("県別の「取得不可」「データなし」の件数一覧")
    print(target_str)
    print(m_total_str)
    print(p_total_str)
    print(elev_str)
    print(haz_str)
    print(land_str)
    for rline in region_lines:
        print(rline)
    for aline in artificial_lines:
        print(aline)
    print(riv_na_str)
    print(riv_1000_str)
    print(coast_str)
    print(comm_str)
    print(top5_line)
    print(out_line)


if __name__ == "__main__":
    main()
