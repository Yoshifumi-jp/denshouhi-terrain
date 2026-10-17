# -*- coding: utf-8 -*-
import argparse
import sys
import unicodedata
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.image as mpimg
from matplotlib.backends.backend_pdf import PdfPages

try:
    from src.prefectures import PREFECTURES
    from src.hazard_layers import HAZARD_DATA_NOTES, HAZARD_SOURCE_URL
    from src.summarize import set_jp_font
    from src.build_national import (
        TILE_LAYOUT,
        COLOR_CLASSES,
        short_name,
        get_color_info,
        load_monument_list,
    )
except ImportError:
    from prefectures import PREFECTURES
    from hazard_layers import HAZARD_DATA_NOTES, HAZARD_SOURCE_URL
    from summarize import set_jp_font
    from build_national import (
        TILE_LAYOUT,
        COLOR_CLASSES,
        short_name,
        get_color_info,
        load_monument_list,
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# A4 縦サイズ（インチ）
A4_WIDTH = 8.27
A4_HEIGHT = 11.69


def get_required_files(output_dir, data_dir):
    """PDF 生成に必要なファイル一覧を返す"""
    output_dir = Path(output_dir)
    data_dir = Path(data_dir)

    files = [
        output_dir / "summary_all.csv",
        output_dir / "hazard_summary_all.csv",
        output_dir / "landform_all.csv",
        output_dir / "relocated_all.csv",
        output_dir / "pref_counts_all.csv",
        output_dir / "fig" / "years_all.png",
        output_dir / "fig" / "pref_counts_all.png",
    ]
    for p in sorted(PREFECTURES.keys()):
        files.append(data_dir / f"monuments_{p}.csv")
        files.append(data_dir / f"landform_{p}.csv")
        files.append(data_dir / f"landform_points_{p}.csv")
    return files


def draw_footer(fig, page_num, latest_date):
    """各ページ下部の共通フッターを描画する"""
    text = f"自然災害伝承碑と地形（全国）　伝承碑データ取得日：{latest_date}　{page_num}／7"
    fig.text(0.5, 0.03, text, ha="center", va="center", fontsize=8, color="#666666")


def get_char_width(c):
    """文字幅を返す（全角2、半角1）"""
    return 2 if unicodedata.east_asian_width(c) in ("F", "W", "A") else 1


def wrap_text_with_kinsoku(text, max_width=86):
    """
    全角文字を幅2、半角文字を幅1として計算し、
    max_width（全角43文字＝幅86）で禁則処理を考慮して折り返す。
    """
    lines = []
    current_line = []
    current_width = 0
    kinsoku = set("、。，．）)」』】・")

    i = 0
    while i < len(text):
        c = text[i]
        w = get_char_width(c)
        if current_width + w > max_width and current_line:
            if c in kinsoku:
                current_line.append(c)
                lines.append("".join(current_line))
                current_line = []
                current_width = 0
                i += 1
                continue
            else:
                lines.append("".join(current_line))
                current_line = [c]
                current_width = w
        else:
            current_line.append(c)
            current_width += w
        i += 1

    if current_line:
        lines.append("".join(current_line))

    return lines


def make_page_1(total_monuments, total_points, latest_date, counts_by_pref):
    """1ページ：表紙と色分け地図"""
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    # 題名
    fig.text(0.08, 0.940, "自然災害伝承碑と地形（全国）", fontsize=16, fontweight="bold", va="top")

    # サブタイトル
    sub_text = f"伝承碑データ取得日：{latest_date}　碑：{total_monuments:,}基（47都道府県）　比較地点：{total_points:,}点"
    fig.text(0.08, 0.905, sub_text, fontsize=10, va="top")

    # 説明文（全国ページの最初の段落と同じ文）
    desc_lines = [
        "国土地理院の自然災害伝承碑に、碑ごとの地形（標高・傾斜・地形分類・河川や海岸との位置関係）を付け、",
        "碑のまわり（100m〜2,000m）の地点と比べた結果をまとめたものです。",
        "結果は地形との相関を示すもので、災害の予測・安全の保証ではありません。",
    ]
    fig.text(0.08, 0.875, "\n".join(desc_lines), fontsize=9, va="top", linespacing=1.4)

    # 凡例（色分け地図の上部）
    fig.text(0.08, 0.800, "碑の数（単位：基）", fontsize=9.5, fontweight="bold", va="top")
    legend_start_x = 0.28
    box_w = 0.024
    box_h = 0.014
    for idx, c_info in enumerate(COLOR_CLASSES):
        x = legend_start_x + idx * 0.115
        y = 0.790
        rect = patches.Rectangle((x, y), box_w, box_h, transform=fig.transFigure,
                                 facecolor=c_info["bg"], edgecolor="#999999", linewidth=0.5)
        fig.add_artist(rect)
        fig.text(x + box_w + 0.006, y + box_h / 2, c_info["label"], transform=fig.transFigure,
                 fontsize=8, va="center", ha="left")

    # 色分け地図
    ax_map = fig.add_axes([0.08, 0.27, 0.84, 0.50])
    ax_map.axis("off")
    ax_map.set_xlim(-0.5, 14.0)
    ax_map.set_ylim(-0.5, 11.5)
    ax_map.set_aspect("equal")

    for p, (r, c) in TILE_LAYOUT.items():
        if p not in PREFECTURES:
            continue
        s_name = short_name(p)
        count = counts_by_pref.get(p, {}).get("碑_数", 0)
        c_info = get_color_info(count)
        bg = c_info["bg"]
        text_color = c_info["text"]

        x = c
        y = 10 - r

        tile_rect = patches.Rectangle((x - 0.45, y - 0.45), 0.9, 0.9,
                                      facecolor=bg, edgecolor="#cccccc", linewidth=0.5)
        ax_map.add_patch(tile_rect)
        ax_map.text(x, y + 0.12, s_name, ha="center", va="center",
                    fontsize=7.5, fontweight="bold", color=text_color)
        ax_map.text(x, y - 0.18, str(count), ha="center", va="center",
                    fontsize=6.5, color=text_color)

    # 目次
    fig.text(0.08, 0.23, "目次", fontsize=12, fontweight="bold", va="top")
    toc_items = [
        "2ページ　都道府県別の件数",
        "3ページ　碑とまわりの比較・ハザード・地形分類",
        "4ページ　地形分類（地域版）",
        "5ページ　年代別の碑の数",
        "6ページ　都道府県別の碑の数（グラフ）",
        "7ページ　出典・ご利用上の注意",
    ]
    for i, item in enumerate(toc_items):
        fig.text(0.10, 0.195 - i * 0.028, item, fontsize=9.5, va="top")

    draw_footer(fig, 1, latest_date)
    return fig


def make_page_2(df_pref_counts, latest_date):
    """2ページ：都道府県別の件数"""
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    fig.text(0.08, 0.955, "都道府県別の件数", fontsize=14, fontweight="bold", va="top")

    headers = ["都道府県", "碑の数", "移転碑", "洪水", "地震", "津波", "土砂災害", "高潮", "火山災害", "その他"]

    rows = []
    for p in sorted(PREFECTURES.keys()):
        p_row = df_pref_counts[df_pref_counts["県コード"] == p]
        if not p_row.empty:
            r = p_row.iloc[0]
            rows.append([
                PREFECTURES[p],
                r.get("碑_数", "0"),
                r.get("移転碑_数", "0"),
                r.get("種別_洪水", "0"),
                r.get("種別_地震", "0"),
                r.get("種別_津波", "0"),
                r.get("種別_土砂災害", "0"),
                r.get("種別_高潮", "0"),
                r.get("種別_火山災害", "0"),
                r.get("種別_その他", "0"),
            ])

    nat_row = df_pref_counts[df_pref_counts["県コード"] == "全国"]
    if nat_row.empty:
        nat_row = df_pref_counts[df_pref_counts["県名"] == "合計"]
    if not nat_row.empty:
        r = nat_row.iloc[0]
        rows.append([
            "全国",
            r.get("碑_数", "0"),
            r.get("移転碑_数", "0"),
            r.get("種別_洪水", "0"),
            r.get("種別_地震", "0"),
            r.get("種別_津波", "0"),
            r.get("種別_土砂災害", "0"),
            r.get("種別_高潮", "0"),
            r.get("種別_火山災害", "0"),
            r.get("種別_その他", "0"),
        ])

    ax = fig.add_axes([0.08, 0.075, 0.84, 0.86])
    ax.axis("off")

    col_widths = [0.19, 0.09, 0.09, 0.09, 0.09, 0.09, 0.10, 0.08, 0.10, 0.08]
    table = ax.table(cellText=rows, colLabels=headers, colWidths=col_widths,
                     loc="upper center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)

    cell_dict = table.get_celld()
    total_rows = len(rows)
    for (row_idx, col_idx), cell in cell_dict.items():
        cell.set_height(1.0 / (total_rows + 1))
        if row_idx == 0:
            cell.set_facecolor("#f0f0f0")
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_fontsize(7.5)
        else:
            if col_idx == 0:
                cell.get_text().set_ha("left")
                orig_text = cell.get_text().get_text()
                cell.get_text().set_text(" " + orig_text)
            if row_idx == total_rows:
                # 全国行
                cell.set_facecolor("#f2f2f2")
                cell.get_text().set_fontweight("bold")
            else:
                if row_idx % 2 == 1:
                    cell.set_facecolor("#ffffff")
                else:
                    cell.set_facecolor("#fcfcfc")

    fig.text(0.08, 0.052, "1基が複数の災害種別を持つため、種別ごとの合計は碑の数より多くなります。",
             fontsize=8, va="top")

    draw_footer(fig, 2, latest_date)
    return fig


def make_page_3(output_dir, mon_no_data, pt_no_data, latest_date):
    """3ページ：3つの表（碑とまわりの比較／ハザードマップの想定区域との重なり／地形分類）"""
    output_dir = Path(output_dir)
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    # --- 1. 碑とまわりの比較 ---
    fig.text(0.08, 0.955, "碑とまわりの比較", fontsize=12, fontweight="bold", va="top")

    df_sum = pd.read_csv(output_dir / "summary_all.csv", dtype=str, encoding="utf-8-sig")
    df_sum_filtered = df_sum[(df_sum["範囲"] == "全碑") & (df_sum["災害種別"] == "全種別")]

    sum_headers = ["指標", "碑の中央値", "まわりの中央値", "差の中央値", "碑の方が大きい割合"]
    sum_rows = []
    for idx, row in df_sum_filtered.iterrows():
        metric = row.get("指標", "")
        if "標高_m" in metric:
            metric = "標高(m)"
        elif "傾斜_度" in metric:
            metric = "傾斜(度)"
        elif "河川までの距離_m" in metric:
            metric = "河川までの距離(m)"
        elif "河川との高さの差_m" in metric:
            metric = "河川との高さの差(m)"
        elif "海岸までの距離_m" in metric:
            metric = "海岸までの距離(m)"

        mon_med = str(row.get("碑_中央値", ""))
        pt_med = str(row.get("比較地点_中央値", ""))
        diff = str(row.get("差の中央値", ""))

        pct_val = row.get("碑の方が大きい割合")
        try:
            pct_val = float(pct_val)
            pct_str = f"{int(round(pct_val * 100))}%"
        except (TypeError, ValueError):
            pct_str = str(pct_val)

        sum_rows.append([metric, mon_med, pt_med, diff, pct_str])

    # 表1の配置
    ax1 = fig.add_axes([0.08, 0.810, 0.84, 0.125])
    ax1.axis("off")
    sum_widths = [0.28, 0.18, 0.18, 0.18, 0.18]
    t1 = ax1.table(cellText=sum_rows, colLabels=sum_headers, colWidths=sum_widths,
                   loc="upper center", cellLoc="center")
    t1.auto_set_font_size(False)
    t1.set_fontsize(8)
    for (r, c), cell in t1.get_celld().items():
        cell.set_height(1.0 / (len(sum_rows) + 1))
        if r == 0:
            cell.set_facecolor("#f0f0f0")
            cell.get_text().set_fontweight("bold")
        else:
            if c == 0:
                cell.get_text().set_ha("left")
                orig = cell.get_text().get_text()
                cell.get_text().set_text(" " + orig)
            if r % 2 == 1:
                cell.set_facecolor("#ffffff")
            else:
                cell.set_facecolor("#fcfcfc")

    # --- 2. ハザードマップの想定区域との重なり ---
    fig.text(0.08, 0.770, "ハザードマップの想定区域との重なり", fontsize=12, fontweight="bold", va="top")

    df_hazard = pd.read_csv(output_dir / "hazard_summary_all.csv", dtype=str, encoding="utf-8-sig")
    df_hazard_filtered = df_hazard[(df_hazard["範囲"] == "全碑") & (df_hazard["災害種別"] == "全種別")]

    def calc_ratio(count_in, count_total, unit, is_3m=False, hazard_name=""):
        if is_3m and hazard_name == "土砂災害":
            return "—"
        if not count_in or not str(count_in).isdigit() or not count_total or not str(count_total).isdigit():
            return "—"
        c_in = int(count_in)
        c_total = int(count_total)
        if c_total == 0:
            return "—"
        pct = round(c_in / c_total * 100)
        return f"{pct}%（{c_in}／{c_total}{unit}）"

    haz_headers = ["ハザード", "碑：区域内", "まわり：区域内", "碑：浸水深3m以上", "まわり：浸水深3m以上"]
    haz_rows = []
    for idx, row in df_hazard_filtered.iterrows():
        hazard = str(row.get("ハザード", ""))
        m_c = str(row.get("碑_数", ""))
        m_in = str(row.get("碑_区域内", ""))
        p_c = str(row.get("比較地点_数", ""))
        p_in = str(row.get("比較地点_区域内", ""))
        m_3m = str(row.get("碑_3m以上", ""))
        p_3m = str(row.get("比較地点_3m以上", ""))

        m_in_str = calc_ratio(m_in, m_c, "基")
        p_in_str = calc_ratio(p_in, p_c, "点")
        m_3m_str = calc_ratio(m_3m, m_c, "基", True, hazard)
        p_3m_str = calc_ratio(p_3m, p_c, "点", True, hazard)

        haz_rows.append([hazard, m_in_str, p_in_str, m_3m_str, p_3m_str])

    # 表2の配置
    ax2 = fig.add_axes([0.08, 0.640, 0.84, 0.110])
    ax2.axis("off")
    haz_widths = [0.24, 0.19, 0.19, 0.19, 0.19]
    t2 = ax2.table(cellText=haz_rows, colLabels=haz_headers, colWidths=haz_widths,
                   loc="upper center", cellLoc="center")
    t2.auto_set_font_size(False)
    t2.set_fontsize(8)
    for (r, c), cell in t2.get_celld().items():
        cell.set_height(1.0 / (len(haz_rows) + 1))
        if r == 0:
            cell.set_facecolor("#f0f0f0")
            cell.get_text().set_fontweight("bold")
        else:
            if c == 0:
                cell.get_text().set_ha("left")
                orig = cell.get_text().get_text()
                cell.get_text().set_text(" " + orig)
            if r % 2 == 1:
                cell.set_facecolor("#ffffff")
            else:
                cell.set_facecolor("#fcfcfc")

    fig.text(0.08, 0.615, "想定区域との重なりを示すもので、危険度の判定ではありません。",
             fontsize=8, va="top")

    # --- 3. 地形分類（全碑・全種別） ---
    fig.text(0.08, 0.580, "地形分類（全碑・全種別）", fontsize=12, fontweight="bold", va="top")

    df_lf = pd.read_csv(output_dir / "landform_all.csv", dtype=str, encoding="utf-8-sig")
    df_lf_filtered = df_lf[(df_lf["範囲"] == "全碑") & (df_lf["災害種別"] == "全種別")].copy()
    df_lf_filtered["碑_件数_num"] = df_lf_filtered["碑_件数"].astype(int)
    df_lf_sorted = df_lf_filtered.sort_values(
        by=["碑_件数_num", "地形分類名"],
        ascending=[False, True]
    )

    lf_headers = ["地形分類", "碑の数", "碑の割合", "まわりの数", "まわりの割合"]
    lf_rows = []
    for idx, row in df_lf_sorted.iterrows():
        lf_name = str(row.get("地形分類名", ""))
        m_count = str(row.get("碑_件数", ""))
        try:
            m_pct = f"{float(row.get('碑_割合', 0)) * 100:.1f}%"
        except (TypeError, ValueError):
            m_pct = str(row.get("碑_割合", ""))

        p_count = str(row.get("比較地点_件数", ""))
        try:
            p_pct = f"{float(row.get('比較地点_割合', 0)) * 100:.1f}%"
        except (TypeError, ValueError):
            p_pct = str(row.get("比較地点_割合", ""))

        lf_rows.append([lf_name, m_count, m_pct, p_count, p_pct])

    # 表3の配置
    ax3 = fig.add_axes([0.08, 0.105, 0.84, 0.455])
    ax3.axis("off")
    lf_widths = [0.36, 0.16, 0.16, 0.16, 0.16]
    t3 = ax3.table(cellText=lf_rows, colLabels=lf_headers, colWidths=lf_widths,
                   loc="upper center", cellLoc="center")
    t3.auto_set_font_size(False)
    t3.set_fontsize(7.5)
    for (r, c), cell in t3.get_celld().items():
        cell.set_height(1.0 / (len(lf_rows) + 1))
        if r == 0:
            cell.set_facecolor("#f0f0f0")
            cell.get_text().set_fontweight("bold")
        else:
            if c == 0:
                cell.get_text().set_ha("left")
                orig = cell.get_text().get_text()
                cell.get_text().set_text(" " + orig)
            if r % 2 == 1:
                cell.set_facecolor("#ffffff")
            else:
                cell.set_facecolor("#fcfcfc")

    note_lf = f"地形分類のデータがない碑 {mon_no_data:,}基・まわりの地点 {pt_no_data:,}点は、割合の計算から除いています。"
    fig.text(0.08, 0.080, note_lf, fontsize=8, va="top")

    draw_footer(fig, 3, latest_date)
    return fig


def make_page_region(output_dir, mon_reg_uncounted, pt_reg_uncounted, latest_date):
    """4ページ：地形分類（地域版・全碑・全種別）"""
    output_dir = Path(output_dir)
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    fig.text(0.08, 0.955, "地形分類（地域版・全碑・全種別）", fontsize=12, fontweight="bold", va="top")

    lf_reg_path = output_dir / "landform_region_all.csv"
    if not lf_reg_path.exists():
        fig.text(
            0.08,
            0.915,
            "地域版の集計（landform_region_all.csv）がないため、表はありません。",
            fontsize=9,
            va="top",
        )
        draw_footer(fig, 4, latest_date)
        return fig

    df_lf = pd.read_csv(lf_reg_path, dtype=str, encoding="utf-8-sig")
    df_lf_filtered = df_lf[(df_lf["範囲"] == "全碑") & (df_lf["災害種別"] == "全種別")].copy()
    df_lf_filtered["碑_件数_num"] = df_lf_filtered["碑_件数"].astype(int)
    df_lf_sorted = df_lf_filtered.sort_values(
        by=["碑_件数_num", "地形分類名"],
        ascending=[False, True]
    )

    lf_headers = ["地形分類", "碑の数", "碑の割合", "まわりの数", "まわりの割合"]
    lf_rows = []
    for idx, row in df_lf_sorted.iterrows():
        lf_name = str(row.get("地形分類名", ""))
        m_count = str(row.get("碑_件数", ""))
        try:
            m_pct = f"{float(row.get('碑_割合', 0)) * 100:.1f}%"
        except (TypeError, ValueError):
            m_pct = str(row.get("碑_割合", ""))

        p_count = str(row.get("比較地点_件数", ""))
        try:
            p_pct = f"{float(row.get('比較地点_割合', 0)) * 100:.1f}%"
        except (TypeError, ValueError):
            p_pct = str(row.get("比較地点_割合", ""))

        lf_rows.append([lf_name, m_count, m_pct, p_count, p_pct])

    ax = fig.add_axes([0.08, 0.60, 0.84, 0.33])
    ax.axis("off")
    lf_widths = [0.36, 0.16, 0.16, 0.16, 0.16]
    t = ax.table(cellText=lf_rows, colLabels=lf_headers, colWidths=lf_widths,
                 loc="upper center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(7.5)
    for (r, c), cell in t.get_celld().items():
        cell.set_height(1.0 / (len(lf_rows) + 1))
        if r == 0:
            cell.set_facecolor("#f0f0f0")
            cell.get_text().set_fontweight("bold")
        else:
            if c == 0:
                cell.get_text().set_ha("left")
                orig = cell.get_text().get_text()
                cell.get_text().set_text(" " + orig)
            if r % 2 == 1:
                cell.set_facecolor("#ffffff")
            else:
                cell.set_facecolor("#fcfcfc")

    note1 = f"地域版で値が取れなかった碑 {mon_reg_uncounted:,}基・まわりの地点 {pt_reg_uncounted:,}点は、割合の計算から除いています。"
    note2 = "地域版は詳細版より分類が粗い（中分類12種）ため、碑とまわりの地点（100m〜2,000m）が同じ分類になりやすく、差が出にくくなります。"
    fig.text(0.08, 0.575, note1, fontsize=8, va="top")
    fig.text(0.08, 0.553, note2, fontsize=8, va="top")

    draw_footer(fig, 4, latest_date)
    return fig


def make_page_4(output_dir, latest_date):
    """5ページ：災害の発生年代と碑の建立年代"""
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    fig.text(0.08, 0.94, "災害の発生年代と碑の建立年代", fontsize=15, fontweight="bold", va="top")

    img_path = Path(output_dir) / "fig" / "years_all.png"
    if img_path.exists():
        img = mpimg.imread(str(img_path))
        ax = fig.add_axes([0.08, 0.25, 0.84, 0.60])
        ax.imshow(img)
        ax.axis("off")
        ax.set_aspect("equal")

    draw_footer(fig, 5, latest_date)
    return fig


def make_page_5(output_dir, latest_date):
    """6ページ：都道府県別の碑の数"""
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    fig.text(0.08, 0.94, "都道府県別の碑の数", fontsize=15, fontweight="bold", va="top")

    img_path = Path(output_dir) / "fig" / "pref_counts_all.png"
    if img_path.exists():
        img = mpimg.imread(str(img_path))
        ax = fig.add_axes([0.08, 0.12, 0.84, 0.79])
        ax.imshow(img)
        ax.axis("off")
        ax.set_aspect("equal")

    draw_footer(fig, 6, latest_date)
    return fig


def make_page_6(relocated_count, mon_no_data, total_monuments, latest_date, mon_reg_uncounted=0):
    """7ページ：出典・ご利用上の注意"""
    fig = plt.figure(figsize=(A4_WIDTH, A4_HEIGHT))

    sources = [
        "自然災害伝承碑：国土地理院（https://www.gsi.go.jp/bousaichiri/denshouhi.html）",
        "標高・傾斜：国土地理院 標高API（標高タイル）から算出",
        "地形分類：国土地理院 地形分類（自然地形）",
        "河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）",
        f"ハザード情報：ハザードマップポータルサイト（{HAZARD_SOURCE_URL}）（洪水浸水想定区域（想定最大規模）・津波浸水想定・高潮浸水想定区域・土砂災害警戒区域）",
        "ハザード情報は同サイトの配信データ（タイル画像）の色を読み取って判定・集計しています（加工して作成）",
        "上記を加工して作成",
        "国土数値情報（海岸線データ）は非商用に限り利用できます。本ページは非商用です。",
    ]

    lf_no_data_pct = (mon_no_data / total_monuments * 100) if total_monuments > 0 else 0.0

    notices = [
        "ハザードマップの想定区域は国・都道府県が公表した想定です。本ページの集計は想定区域との重なりを示すもので、危険度の判定ではありません。防災上の判断には自治体のハザードマップをご利用ください。",
        "本地図の分析結果は、伝承碑の位置と地形との「相関」を示すもので、災害の発生を予測・保証するものではありません。防災上の判断には自治体のハザードマップをご利用ください。",
        "碑の位置は被災した地点とは限りません（移設された碑もあります）。伝承碑の登録は市町村の申請によるもので、すべての碑を網羅しているわけではありません。",
        f"移転碑（伝承内容に「移転」「移設」を含む碑、全国{relocated_count}基）は文字で機械的に選んでいるため、集団移転や施設の移転を伝える碑など、碑そのものが移設されていないものも含まれます。",
        "ハザードマップの想定区域は、都道府県や河川ごとに公表の時期や想定が異なります。ハザードマップポータルサイトの配信データが最新の公表と一致しない場合もあります。",
    ]

    for p_code in sorted(HAZARD_DATA_NOTES.keys()):
        pref_name = PREFECTURES.get(p_code, p_code)
        for note in HAZARD_DATA_NOTES[p_code]:
            notices.append(f"【{pref_name}】{note}")

    notices.append(
        f"地形分類（自然地形）のデータは整備された地域が限られ、全国の碑の {lf_no_data_pct:.1f}%（{mon_no_data:,}基）はデータがありません。"
    )
    notices.append(
        f"地形分類（地域版）は、詳細版のない地域も含めて全国の碑に付けたものです（値が取れなかった碑 {mon_reg_uncounted:,}基）。詳細版とは分類の細かさが違うため、別の列・別の表にしています。"
    )
    notices.append("1基の碑が複数の災害種別を持つことがあります。")

    curr_y = 0.950

    fig.text(0.08, curr_y, "出典", fontsize=14, fontweight="bold", va="top")
    curr_y -= 0.032

    line_h = 0.0185
    item_gap = 0.006

    for item in sources:
        wrapped = wrap_text_with_kinsoku(item, max_width=86)
        for idx, line in enumerate(wrapped):
            prefix = "・" if idx == 0 else "　"
            fig.text(0.08, curr_y, prefix + line, fontsize=8.5, va="top")
            curr_y -= line_h
        curr_y -= item_gap

    curr_y -= 0.015
    fig.text(0.08, curr_y, "ご利用上の注意", fontsize=14, fontweight="bold", va="top")
    curr_y -= 0.032

    for item in notices:
        wrapped = wrap_text_with_kinsoku(item, max_width=86)
        for idx, line in enumerate(wrapped):
            prefix = "・" if idx == 0 else "　"
            fig.text(0.08, curr_y, prefix + line, fontsize=8.5, va="top")
            curr_y -= line_h
        curr_y -= item_gap

    draw_footer(fig, 7, latest_date)
    return fig


def make_national_pdf(output_dir=None, data_dir=None, out_path=None, quiet=False):
    """
    全国の集計を A4 縦・7ページの PDF にまとめる。
    戻り値：ページ数
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "output"
    else:
        output_dir = Path(output_dir)

    if data_dir is None:
        data_dir = PROJECT_ROOT / "data" / "processed"
    else:
        data_dir = Path(data_dir)

    if out_path is None:
        out_path = output_dir / "national_report.pdf"
    else:
        out_path = Path(out_path)

    # 必須ファイルチェック
    req_files = get_required_files(output_dir, data_dir)
    missing = [f.name for f in req_files if not f.exists()]
    if missing:
        if len(missing) > 10:
            disp_missing = "、".join(missing[:10]) + f"、ほか {len(missing) - 10} 個"
        else:
            disp_missing = "、".join(missing)
        print(f"エラー：ファイルが足りません：{disp_missing}")
        print("先に実行してください：python src/summarize_national.py")
        sys.exit(1)

    # 日本語フォント設定
    set_jp_font()

    # データ読み込み
    df_monuments = load_monument_list(data_dir)
    total_monuments = len(df_monuments)

    dates = df_monuments["データ取得日"].dropna().unique() if "データ取得日" in df_monuments.columns else []
    latest_date = sorted(dates)[-1] if len(dates) > 0 else ""

    mon_no_data = (df_monuments["地形分類名"] == "データなし").sum()

    pt_no_data = 0
    for p in sorted(PREFECTURES.keys()):
        pt_lf_path = data_dir / f"landform_points_{p}.csv"
        if pt_lf_path.exists():
            df_pt_lf = pd.read_csv(pt_lf_path, dtype=str, encoding="utf-8-sig")
            if "地形分類_状態" in df_pt_lf.columns:
                pt_no_data += (df_pt_lf["地形分類_状態"] == "データなし").sum()

    # 地域版の集計（値が取れなかった碑・比較地点の数、および表の行数）
    mon_reg_uncounted = 0
    for p in sorted(PREFECTURES.keys()):
        reg_path = data_dir / f"landform_region_{p}.csv"
        if reg_path.exists():
            df_reg = pd.read_csv(reg_path, dtype=str, encoding="utf-8-sig")
            if "地域版_状態" in df_reg.columns:
                mon_reg_uncounted += int((df_reg["地域版_状態"].fillna("") != "取得済（地域版）").sum())
        else:
            mon_p_path = data_dir / f"monuments_{p}.csv"
            if mon_p_path.exists():
                df_mon_p = pd.read_csv(mon_p_path, dtype=str, encoding="utf-8-sig")
                mon_reg_uncounted += len(df_mon_p)

    pt_reg_uncounted = 0
    for p in sorted(PREFECTURES.keys()):
        pt_reg_path = data_dir / f"landform_region_points_{p}.csv"
        if pt_reg_path.exists():
            df_pt_reg = pd.read_csv(pt_reg_path, dtype=str, encoding="utf-8-sig")
            if "地域版_状態" in df_pt_reg.columns:
                pt_reg_uncounted += int((df_pt_reg["地域版_状態"].fillna("") != "取得済（地域版）").sum())

    lf_reg_all_path = output_dir / "landform_region_all.csv"
    if lf_reg_all_path.exists():
        df_lf_reg = pd.read_csv(lf_reg_all_path, dtype=str, encoding="utf-8-sig")
        reg_table_rows = len(df_lf_reg[(df_lf_reg["範囲"] == "全碑") & (df_lf_reg["災害種別"] == "全種別")])
    else:
        reg_table_rows = 0

    pref_counts_file = output_dir / "pref_counts_all.csv"
    df_pref_counts = pd.read_csv(pref_counts_file, dtype=str, encoding="utf-8-sig")

    counts_by_pref = {}
    national_row = None
    for idx, row in df_pref_counts.iterrows():
        p_code = str(row.get("県コード", "")).strip()
        if p_code in PREFECTURES:
            counts_by_pref[p_code] = {
                "碑_数": int(row["碑_数"]),
                "移転碑_数": int(row["移転碑_数"]),
                "種別_洪水": int(row["種別_洪水"]),
                "種別_地震": int(row["種別_地震"]),
                "種別_津波": int(row["種別_津波"]),
                "種別_土砂災害": int(row["種別_土砂災害"]),
                "種別_高潮": int(row["種別_高潮"]),
                "種別_火山災害": int(row["種別_火山災害"]),
                "種別_その他": int(row["種別_その他"]),
            }
        elif p_code == "全国" or str(row.get("県名", "")).strip() == "合計":
            national_row = row

    total_points = int(national_row["比較地点_数"]) if national_row is not None and "比較地点_数" in national_row else 0

    relocated_file = output_dir / "relocated_all.csv"
    if relocated_file.exists():
        df_relocated = pd.read_csv(relocated_file, dtype=str, encoding="utf-8-sig")
        relocated_count = len(df_relocated)
    else:
        relocated_count = 0

    # PDF 出力ディレクトリ作成
    out_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "Title": "自然災害伝承碑と地形（全国）",
        "Author": None,
        "Creator": None,
        "Producer": None,
        "CreationDate": None,
    }

    with PdfPages(out_path, metadata=metadata) as pdf:
        # 1ページ
        fig1 = make_page_1(total_monuments, total_points, latest_date, counts_by_pref)
        pdf.savefig(fig1)
        plt.close(fig1)

        # 2ページ
        fig2 = make_page_2(df_pref_counts, latest_date)
        pdf.savefig(fig2)
        plt.close(fig2)

        # 3ページ
        fig3 = make_page_3(output_dir, mon_no_data, pt_no_data, latest_date)
        pdf.savefig(fig3)
        plt.close(fig3)

        # 4ページ（地域版）
        fig_reg = make_page_region(output_dir, mon_reg_uncounted, pt_reg_uncounted, latest_date)
        pdf.savefig(fig_reg)
        plt.close(fig_reg)

        # 5ページ
        fig4 = make_page_4(output_dir, latest_date)
        pdf.savefig(fig4)
        plt.close(fig4)

        # 6ページ
        fig5 = make_page_5(output_dir, latest_date)
        pdf.savefig(fig5)
        plt.close(fig5)

        # 7ページ
        fig6 = make_page_6(relocated_count, mon_no_data, total_monuments, latest_date, mon_reg_uncounted)
        pdf.savefig(fig6)
        plt.close(fig6)

        page_count = pdf.get_pagecount()

    try:
        rel_out = out_path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        rel_out = str(out_path)

    size_kb = out_path.stat().st_size / 1024

    if not quiet:
        print(f"印刷用PDF：{rel_out}")
        print(f"ページ数：{page_count}（A4 縦）")
        print(f"地形分類（地域版）の表：{reg_table_rows}行（値が取れなかった碑 {mon_reg_uncounted:,}基・まわりの地点 {pt_reg_uncounted:,}点）")
        print(f"碑：{total_monuments:,}基（{len(PREFECTURES)}都道府県）\u3000伝承碑データ取得日：{latest_date}")
        print(f"ファイルのサイズ：{size_kb:.1f} KB")

    return page_count


def main():
    parser = argparse.ArgumentParser(description="自然災害伝承碑の全国印刷用PDFを作成する")
    parser.add_argument("--output-dir", type=str, default=None, help="集計CSVやグラフのディレクトリ")
    parser.add_argument("--data-dir", type=str, default=None, help="中間データディレクトリ")
    parser.add_argument("--out-path", type=str, default=None, help="出力PDFパス")
    parser.add_argument("--quiet", action="store_true", help="進捗表示を抑止する")
    args = parser.parse_args()

    make_national_pdf(
        output_dir=args.output_dir,
        data_dir=args.data_dir,
        out_path=args.out_path,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()

