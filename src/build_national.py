# -*- coding: utf-8 -*-
import html
import json
import shutil
import sys
from pathlib import Path
import pandas as pd

try:
    from src.prefectures import PREFECTURES
    from src.hazard_layers import HAZARD_DATA_NOTES, HAZARD_SOURCE_URL
    from src.check_public import find_private_info
except ImportError:
    from prefectures import PREFECTURES
    from hazard_layers import HAZARD_DATA_NOTES, HAZARD_SOURCE_URL
    from check_public import find_private_info

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# タイル型日本地図の配置（14列×11行、県コード -> (行, 列)）
TILE_LAYOUT = {
    '01': (0, 13),
    '02': (1, 13),
    '05': (2, 12), '03': (2, 13),
    '06': (3, 12), '04': (3, 13),
    '17': (4, 9), '16': (4, 10), '15': (4, 11), '07': (4, 12),
    '18': (5, 8), '21': (5, 9), '20': (5, 10), '10': (5, 11), '09': (5, 12), '08': (5, 13),
    '32': (6, 4), '31': (6, 5), '28': (6, 6), '26': (6, 7), '25': (6, 8), '23': (6, 9), '19': (6, 10), '11': (6, 11),
    '35': (7, 3), '34': (7, 4), '33': (7, 5), '27': (7, 6), '29': (7, 7), '24': (7, 8), '22': (7, 9), '14': (7, 10), '13': (7, 11), '12': (7, 12),
    '42': (8, 0), '41': (8, 1), '40': (8, 2), '38': (8, 4), '37': (8, 5), '30': (8, 6),
    '43': (9, 1), '44': (9, 2), '39': (9, 4), '36': (9, 5),
    '47': (10, 0), '46': (10, 1), '45': (10, 2),
}

# 色分けの区分定義
COLOR_CLASSES = [
    {"label": "0", "min": 0, "max": 0, "bg": "#f2f2f2", "text": "#333333"},
    {"label": "1〜9", "min": 1, "max": 9, "bg": "#deebf7", "text": "#333333"},
    {"label": "10〜19", "min": 10, "max": 19, "bg": "#9ecae1", "text": "#333333"},
    {"label": "20〜49", "min": 20, "max": 49, "bg": "#6baed6", "text": "#333333"},
    {"label": "50〜99", "min": 50, "max": 99, "bg": "#3182bd", "text": "#ffffff"},
    {"label": "100以上", "min": 100, "max": float("inf"), "bg": "#08519c", "text": "#ffffff"},
]

DISASTER_TYPES = ['洪水', '地震', '津波', '土砂災害', '高潮', '火山災害', 'その他']


def short_name(pref):
    """
    都道府県名から末尾の「都・府・県」を1字だけ除く（北海道はそのまま）。
    pref には県名または県コードを渡すことができる。
    """
    if pref in PREFECTURES:
        name = PREFECTURES[pref]
    else:
        name = str(pref)
    if name == "北海道":
        return "北海道"
    if name.endswith(("都", "府", "県")):
        return name[:-1]
    return name


def color_class(n):
    """件数 n に対応する色分け区分の表示名を返す"""
    n = int(n)
    if n == 0:
        return "0"
    elif 1 <= n <= 9:
        return "1〜9"
    elif 10 <= n <= 19:
        return "10〜19"
    elif 20 <= n <= 49:
        return "20〜49"
    elif 50 <= n <= 99:
        return "50〜99"
    else:
        return "100以上"


def get_color_info(n):
    """件数 n に対応する区分情報辞書を返す"""
    n = int(n)
    for c in COLOR_CLASSES:
        if c["min"] <= n <= c["max"]:
            return c
    return COLOR_CLASSES[-1]


def required_files(output_dir, data_dir, site_dir):
    """実行に必要なファイル一覧を返す"""
    output_dir = Path(output_dir)
    data_dir = Path(data_dir)
    site_dir = Path(site_dir)

    files = [
        output_dir / "summary_all.csv",
        output_dir / "hazard_summary_all.csv",
        output_dir / "landform_all.csv",
        output_dir / "relocated_all.csv",
        output_dir / "pref_counts_all.csv",
        output_dir / "years_all.csv",
        output_dir / "national_report.pdf",
        output_dir / "fig" / "years_all.png",
        output_dir / "fig" / "pref_counts_all.png",
    ]
    for p in sorted(PREFECTURES.keys()):
        files.append(data_dir / f"monuments_{p}.csv")
        files.append(data_dir / f"landform_{p}.csv")
        files.append(data_dir / f"landform_points_{p}.csv")
        files.append(site_dir / f"pref_{p}.html")
    return files


def load_monument_list(data_dir):
    """
    47県の monuments と landform を ID で結合し、
    県コード・ID の順に並べた表を返す。地形分類名が空の碑は「データなし」。
    """
    data_dir = Path(data_dir)
    records = []
    for pref in sorted(PREFECTURES.keys()):
        mon_path = data_dir / f"monuments_{pref}.csv"
        lf_path = data_dir / f"landform_{pref}.csv"
        if not mon_path.exists() or not lf_path.exists():
            continue
        df_mon = pd.read_csv(mon_path, dtype=str, encoding='utf-8-sig')
        df_lf = pd.read_csv(lf_path, dtype=str, encoding='utf-8-sig')
        df_merged = df_mon.merge(df_lf[['ID', '地形分類名']], on='ID', how='left')
        records.append(df_merged)

    if not records:
        return pd.DataFrame()

    df = pd.concat(records, ignore_index=True)
    df['地形分類名'] = df['地形分類名'].fillna('データなし')
    df.loc[df['地形分類名'] == '', '地形分類名'] = 'データなし'
    df = df.sort_values(by=['県コード', 'ID']).reset_index(drop=True)
    return df


def landform_options(df):
    """一覧の絞り込み用地形分類の選択肢を返す（多い順、同数は名前順、最後がデータなし）"""
    if df.empty or '地形分類名' not in df.columns:
        return ['データなし']
    valid_lf = df[df['地形分類名'] != 'データなし']['地形分類名']
    counts = valid_lf.value_counts()
    items = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    options = [name for name, _ in items]
    options.append('データなし')
    return options


def build_national(output_dir=None, site_dir=None, data_dir=None, quiet=False):
    """全国ページを作成し、必要なファイルを docs にコピーする"""
    if output_dir is None:
        output_dir = PROJECT_ROOT / "output"
    else:
        output_dir = Path(output_dir)

    if site_dir is None:
        site_dir = PROJECT_ROOT / "docs"
    else:
        site_dir = Path(site_dir)

    if data_dir is None:
        data_dir = PROJECT_ROOT / "data" / "processed"
    else:
        data_dir = Path(data_dir)

    # 必須ファイルのチェック
    req_files = required_files(output_dir, data_dir, site_dir)
    missing = [f.name for f in req_files if not f.exists()]
    if missing:
        if len(missing) > 10:
            disp_missing = "、".join(missing[:10]) + f"、ほか {len(missing) - 10} 個"
        else:
            disp_missing = "、".join(missing)
        print(f"エラー：ファイルが足りません：{disp_missing}")
        print("先に実行してください：python src/summarize_national.py、python src/make_national_pdf.py と python src/build_site.py --pref all")
        sys.exit(1)

    site_dir.mkdir(parents=True, exist_ok=True)
    docs_data_dir = site_dir / "data"
    docs_data_dir.mkdir(parents=True, exist_ok=True)
    fig_dir = site_dir / "fig"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. 碑一覧の読み込み
    df_monuments = load_monument_list(data_dir)
    total_monuments = len(df_monuments)

    dates = df_monuments['データ取得日'].dropna().unique() if 'データ取得日' in df_monuments.columns else []
    latest_date = sorted(dates)[-1] if len(dates) > 0 else ""

    # 地形分類の「データなし」集計
    mon_no_data = (df_monuments['地形分類名'] == 'データなし').sum()

    pt_no_data = 0
    for p in sorted(PREFECTURES.keys()):
        pt_lf_path = data_dir / f"landform_points_{p}.csv"
        if pt_lf_path.exists():
            df_pt_lf = pd.read_csv(pt_lf_path, dtype=str, encoding='utf-8-sig')
            if '地形分類_状態' in df_pt_lf.columns:
                pt_no_data += (df_pt_lf['地形分類_状態'] == 'データなし').sum()

    lf_options = landform_options(df_monuments)

    # 2. pref_counts_all.csv の読み込み
    pref_counts_file = output_dir / "pref_counts_all.csv"
    df_pref_counts = pd.read_csv(pref_counts_file, dtype=str, encoding='utf-8-sig')

    counts_by_pref = {}
    pref_counts_rows = []
    national_row = None

    for idx, row in df_pref_counts.iterrows():
        p_code = str(row.get('県コード', '')).strip()
        if p_code in PREFECTURES:
            counts_by_pref[p_code] = {
                '碑_数': int(row['碑_数']),
                '移転碑_数': int(row['移転碑_数']),
                '種別_洪水': int(row['種別_洪水']),
                '種別_地震': int(row['種別_地震']),
                '種別_津波': int(row['種別_津波']),
                '種別_土砂災害': int(row['種別_土砂災害']),
                '種別_高潮': int(row['種別_高潮']),
                '種別_火山災害': int(row['種別_火山災害']),
                '種別_その他': int(row['種別_その他']),
            }
            pref_name = PREFECTURES[p_code]
            row_html = (
                f"<tr>"
                f'<td><a href="pref_{p_code}.html">{html.escape(pref_name)}</a></td>'
                f'<td><a href="map_{p_code}.html">地図</a></td>'
                f"<td>{row['碑_数']}</td>"
                f"<td>{row['移転碑_数']}</td>"
                f"<td>{row['種別_洪水']}</td>"
                f"<td>{row['種別_地震']}</td>"
                f"<td>{row['種別_津波']}</td>"
                f"<td>{row['種別_土砂災害']}</td>"
                f"<td>{row['種別_高潮']}</td>"
                f"<td>{row['種別_火山災害']}</td>"
                f"<td>{row['種別_その他']}</td>"
                f"</tr>"
            )
            pref_counts_rows.append(row_html)
        elif p_code == '全国' or str(row.get('県名', '')).strip() == '合計':
            national_row = row

    if national_row is not None:
        nat_html = (
            f"<tr>"
            f"<td>全国</td>"
            f"<td>—</td>"
            f"<td>{national_row['碑_数']}</td>"
            f"<td>{national_row['移転碑_数']}</td>"
            f"<td>{national_row['種別_洪水']}</td>"
            f"<td>{national_row['種別_地震']}</td>"
            f"<td>{national_row['種別_津波']}</td>"
            f"<td>{national_row['種別_土砂災害']}</td>"
            f"<td>{national_row['種別_高潮']}</td>"
            f"<td>{national_row['種別_火山災害']}</td>"
            f"<td>{national_row['種別_その他']}</td>"
            f"</tr>"
        )
        pref_counts_rows.append(nat_html)

    pref_counts_rows_html = "\n".join(pref_counts_rows)

    # 色分け地図のタイル HTML 生成
    tile_html_list = []
    c_dist = {c["label"]: 0 for c in COLOR_CLASSES}

    sorted_tiles = sorted(TILE_LAYOUT.items(), key=lambda x: (x[1][0], x[1][1]))
    for p, (r, c) in sorted_tiles:
        if p not in PREFECTURES:
            continue
        p_name = PREFECTURES[p]
        s_name = short_name(p)
        count = counts_by_pref.get(p, {}).get('碑_数', 0)
        c_info = get_color_info(count)
        c_dist[c_info["label"]] += 1
        title = f"{p_name}：碑の数 {count}基"
        tile_html = (
            f'<a href="pref_{p}.html" id="tile-{p}" class="pref-tile" '
            f'style="grid-row: {r + 1}; grid-column: {c + 1}; background-color: {c_info["bg"]}; color: {c_info["text"]};" '
            f'title="{html.escape(title)}">'
            f'<div class="tile-name">{html.escape(s_name)}</div>'
            f'<div class="tile-count">{count}</div>'
            f'</a>'
        )
        tile_html_list.append(tile_html)
    tile_html_str = "\n".join(tile_html_list)

    # 3. 碑の一覧用データの準備
    mon_list = []
    initial_rows = []
    for idx, row in df_monuments.iterrows():
        m_id = str(row.get('ID', ''))
        m_name = str(row.get('碑名', ''))
        m_pref = str(row.get('県コード', '')).zfill(2)
        m_loc = str(row.get('所在地', ''))
        m_dtype = str(row.get('災害種別', ''))
        m_lf = str(row.get('地形分類名', 'データなし'))
        m_year = str(row.get('建立年', ''))
        m_lat = str(row.get('緯度', ''))
        m_lon = str(row.get('経度', ''))

        types = []
        for t in DISASTER_TYPES:
            col = f"種別_{t}"
            if str(row.get(col, '')) == '1':
                types.append(t)

        mon_item = [m_id, m_name, m_pref, m_loc, m_dtype, m_lf, m_year, m_lat, m_lon, types]
        mon_list.append(mon_item)

        if len(initial_rows) < 200:
            p_name = PREFECTURES.get(m_pref, m_pref)
            map_url = f"https://maps.gsi.go.jp/#16/{m_lat}/{m_lon}/"
            r_html = (
                f"<tr>"
                f"<td>{html.escape(m_id)}</td>"
                f"<td>{html.escape(m_name)}</td>"
                f'<td><a href="pref_{m_pref}.html">{html.escape(p_name)}</a></td>'
                f"<td>{html.escape(m_loc)}</td>"
                f"<td>{html.escape(m_dtype)}</td>"
                f"<td>{html.escape(m_lf)}</td>"
                f"<td>{html.escape(m_year)}</td>"
                f'<td><a href="{html.escape(map_url)}" target="_blank" rel="noopener noreferrer">地理院地図</a></td>'
                f"</tr>"
            )
            initial_rows.append(r_html)

    initial_monument_rows_html = "\n".join(initial_rows)
    json_monuments = json.dumps(mon_list, ensure_ascii=False).replace('</', r'<\/')
    json_pref_counts = json.dumps(counts_by_pref, ensure_ascii=False).replace('</', r'<\/')
    pref_names_dict = {p: PREFECTURES[p] for p in sorted(PREFECTURES.keys())}
    json_pref_names = json.dumps(pref_names_dict, ensure_ascii=False).replace('</', r'<\/')

    # 都道府県・地形分類セレクトボックスの option
    pref_options_html = "\n".join(
        f'<option value="{p}">{html.escape(PREFECTURES[p])}</option>'
        for p in sorted(PREFECTURES.keys())
    )
    landform_options_html = "\n".join(
        f'<option value="{html.escape(opt)}">{html.escape(opt)}</option>'
        for opt in lf_options
    )

    limit_note_style = "" if total_monuments > 200 else ' style="display: none;"'

    # 4. summary_all.csv の比較表
    df_sum = pd.read_csv(output_dir / "summary_all.csv", dtype=str, encoding='utf-8-sig')
    df_sum_filtered = df_sum[(df_sum['範囲'] == '全碑') & (df_sum['災害種別'] == '全種別')]

    summary_rows_html_list = []
    for idx, row in df_sum_filtered.iterrows():
        metric = row.get('指標', '')
        if '標高_m' in metric:
            metric = '標高(m)'
        elif '傾斜_度' in metric:
            metric = '傾斜(度)'
        elif '河川までの距離_m' in metric:
            metric = '河川までの距離(m)'
        elif '河川との高さの差_m' in metric:
            metric = '河川との高さの差(m)'
        elif '海岸までの距離_m' in metric:
            metric = '海岸までの距離(m)'

        mon_med = html.escape(str(row.get('碑_中央値', '')))
        pt_med = html.escape(str(row.get('比較地点_中央値', '')))
        diff = html.escape(str(row.get('差の中央値', '')))

        pct_val = row.get('碑の方が大きい割合')
        try:
            pct_val = float(pct_val)
            pct_str = f"{int(round(pct_val * 100))}%"
        except (TypeError, ValueError):
            pct_str = html.escape(str(pct_val))

        summary_rows_html_list.append(
            f"<tr><td>{html.escape(metric)}</td><td>{mon_med}</td><td>{pt_med}</td><td>{diff}</td><td>{pct_str}</td></tr>"
        )
    summary_rows_html = "\n".join(summary_rows_html_list)

    # 5. hazard_summary_all.csv のハザード表
    df_hazard = pd.read_csv(output_dir / "hazard_summary_all.csv", dtype=str, encoding='utf-8-sig')
    df_hazard_filtered = df_hazard[(df_hazard['範囲'] == '全碑') & (df_hazard['災害種別'] == '全種別')]

    def calc_ratio(count_in, count_total, unit, is_3m=False, hazard_name=''):
        if is_3m and hazard_name == '土砂災害':
            return '—'
        if not count_in or not str(count_in).isdigit() or not count_total or not str(count_total).isdigit():
            return '—'
        c_in = int(count_in)
        c_total = int(count_total)
        if c_total == 0:
            return '—'
        pct = round(c_in / c_total * 100)
        return f"{pct}%（{c_in}／{c_total}{unit}）"

    hazard_rows_list = []
    for idx, row in df_hazard_filtered.iterrows():
        hazard = str(row.get('ハザード', ''))
        m_c = str(row.get('碑_数', ''))
        m_in = str(row.get('碑_区域内', ''))
        p_c = str(row.get('比較地点_数', ''))
        p_in = str(row.get('比較地点_区域内', ''))
        m_3m = str(row.get('碑_3m以上', ''))
        p_3m = str(row.get('比較地点_3m以上', ''))

        m_in_str = calc_ratio(m_in, m_c, '基')
        p_in_str = calc_ratio(p_in, p_c, '点')
        m_3m_str = calc_ratio(m_3m, m_c, '基', True, hazard)
        p_3m_str = calc_ratio(p_3m, p_c, '点', True, hazard)

        hazard_rows_list.append(
            f"<tr><td>{html.escape(hazard)}</td><td>{m_in_str}</td><td>{p_in_str}</td><td>{m_3m_str}</td><td>{p_3m_str}</td></tr>"
        )
    hazard_rows_html = "\n".join(hazard_rows_list)

    # 6. landform_all.csv の地形分類表
    df_lf = pd.read_csv(output_dir / "landform_all.csv", dtype=str, encoding='utf-8-sig')
    df_lf_filtered = df_lf[(df_lf['範囲'] == '全碑') & (df_lf['災害種別'] == '全種別')].copy()
    df_lf_filtered['碑_件数_num'] = df_lf_filtered['碑_件数'].astype(int)
    df_lf_sorted = df_lf_filtered.sort_values(
        by=['碑_件数_num', '地形分類名'],
        ascending=[False, True]
    )

    lf_rows_list = []
    for idx, row in df_lf_sorted.iterrows():
        lf_name = html.escape(str(row.get('地形分類名', '')))
        m_count = html.escape(str(row.get('碑_件数', '')))
        try:
            m_pct = f"{float(row.get('碑_割合', 0)) * 100:.1f}%"
        except (TypeError, ValueError):
            m_pct = html.escape(str(row.get('碑_割合', '')))

        p_count = html.escape(str(row.get('比較地点_件数', '')))
        try:
            p_pct = f"{float(row.get('比較地点_割合', 0)) * 100:.1f}%"
        except (TypeError, ValueError):
            p_pct = html.escape(str(row.get('比較地点_割合', '')))

        lf_rows_list.append(
            f"<tr><td>{lf_name}</td><td>{m_count}</td><td>{m_pct}</td><td>{p_count}</td><td>{p_pct}</td></tr>"
        )
    landform_rows_html = "\n".join(lf_rows_list)

    # 7. relocated_all.csv の件数取得
    df_relocated = pd.read_csv(output_dir / "relocated_all.csv", dtype=str, encoding='utf-8-sig')
    relocated_count = len(df_relocated)

    # 8. 注意事項（ハザード情報の各県注記）
    hazard_note_lines = [
        "ハザードマップの想定区域は、都道府県や河川ごとに公表の時期や想定が異なります。ハザードマップポータルサイトの配信データが最新の公表と一致しない場合もあります。"
    ]
    for p_code in sorted(HAZARD_DATA_NOTES.keys()):
        pref_name = PREFECTURES.get(p_code, p_code)
        for note in HAZARD_DATA_NOTES[p_code]:
            hazard_note_lines.append(f"{pref_name}：{note}")
    hazard_note_combined = "<br>".join(html.escape(line) for line in hazard_note_lines)

    lf_no_data_pct = (mon_no_data / total_monuments * 100) if total_monuments > 0 else 0.0

    # 9. 最下部の県別ページリンク
    pref_links = [f'<a href="pref_{p}.html">{html.escape(PREFECTURES[p])}</a>' for p in sorted(PREFECTURES.keys())]
    bottom_links_html = f"<p>県別のページ：{'　'.join(pref_links)}</p>"

    # HTML 本体の構築
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>自然災害伝承碑と地形（全国）</title>
    <style>
        body {{ max-width: 800px; margin: 0 auto; padding: 10px; font-family: sans-serif; font-size: 16px; line-height: 1.5; }}
        img {{ max-width: 100%; height: auto; }}
        .table-container {{ overflow-x: auto; margin-bottom: 10px; }}
        table {{ border-collapse: collapse; width: 100%; min-width: 500px; margin-bottom: 10px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        h2 {{ margin-top: 30px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
        
        .map-container {{ overflow-x: auto; margin-bottom: 10px; }}
        .tile-grid {{
            display: grid;
            grid-template-columns: repeat(14, 1fr);
            grid-gap: 4px;
            min-width: 480px;
            max-width: 700px;
            margin: 10px 0;
        }}
        .pref-tile {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-decoration: none;
            padding: 4px 2px;
            border-radius: 4px;
            border: 1px solid #ccc;
            font-size: 12px;
            line-height: 1.2;
            text-align: center;
            box-sizing: border-box;
            aspect-ratio: 1;
        }}
        .pref-tile:hover {{
            opacity: 0.85;
            outline: 2px solid #333;
        }}
        .pref-tile .tile-name {{ font-weight: bold; }}
        .pref-tile .tile-count {{ font-size: 11px; }}
        
        .legend-container {{ margin: 10px 0; font-size: 14px; }}
        .legend-items {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }}
        .legend-item {{ display: flex; align-items: center; gap: 4px; }}
        .legend-color-box {{ display: inline-block; width: 16px; height: 16px; border: 1px solid #ccc; }}
        
        .filter-group {{ display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; align-items: center; }}
        .filter-item {{ display: flex; align-items: center; gap: 6px; }}
        select {{ padding: 4px 8px; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>自然災害伝承碑と地形（全国）</h1>
    <p>伝承碑データ取得日：{html.escape(latest_date)}　碑の数：{total_monuments:,}基（{len(PREFECTURES)}都道府県）</p>
    <p>国土地理院の自然災害伝承碑に、碑ごとの地形（標高・傾斜・地形分類・河川や海岸との位置関係）を付け、碑のまわり（100m〜2,000m）の地点と比べた結果をまとめたものです。結果は地形との相関を示すもので、災害の予測・安全の保証ではありません。</p>

    <h2>都道府県の色分け地図</h2>
    <div class="filter-item" style="margin-bottom: 10px;">
        <label for="map-type">表示する災害種別：</label>
        <select id="map-type">
            <option value="碑_数">碑の数</option>
            <option value="種別_洪水">洪水</option>
            <option value="種別_地震">地震</option>
            <option value="種別_津波">津波</option>
            <option value="種別_土砂災害">土砂災害</option>
            <option value="種別_高潮">高潮</option>
            <option value="種別_火山災害">火山災害</option>
            <option value="種別_その他">その他</option>
        </select>
    </div>
    <div class="legend-container">
        <div id="legend-title" style="font-weight: bold;">碑の数（単位：基）</div>
        <div class="legend-items">
            <div class="legend-item"><span class="legend-color-box" style="background-color: #f2f2f2;"></span><span>0</span></div>
            <div class="legend-item"><span class="legend-color-box" style="background-color: #deebf7;"></span><span>1〜9</span></div>
            <div class="legend-item"><span class="legend-color-box" style="background-color: #9ecae1;"></span><span>10〜19</span></div>
            <div class="legend-item"><span class="legend-color-box" style="background-color: #6baed6;"></span><span>20〜49</span></div>
            <div class="legend-item"><span class="legend-color-box" style="background-color: #3182bd;"></span><span>50〜99</span></div>
            <div class="legend-item"><span class="legend-color-box" style="background-color: #08519c;"></span><span>100以上</span></div>
        </div>
    </div>
    <div class="map-container">
        <div class="tile-grid">
{tile_html_str}
        </div>
    </div>
    <p>スマホでは地図を横にずらして見られます。県の四角を押すと、その県のページに移ります。</p>

    <h2>都道府県別の件数</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>都道府県</th><th>地図</th><th>碑の数</th><th>移転碑</th><th>洪水</th><th>地震</th><th>津波</th><th>土砂災害</th><th>高潮</th><th>火山災害</th><th>その他</th></tr>
            </thead>
            <tbody>
{pref_counts_rows_html}
            </tbody>
        </table>
    </div>
    <p>1基が複数の災害種別を持つため、種別ごとの合計は碑の数より多くなります。</p>

    <h2>碑の一覧（絞り込み）</h2>
    <div class="filter-group">
        <div class="filter-item">
            <label for="f-pref">都道府県：</label>
            <select id="f-pref">
                <option value="">全国</option>
{pref_options_html}
            </select>
        </div>
        <div class="filter-item">
            <label for="f-type">災害種別：</label>
            <select id="f-type">
                <option value="">すべて</option>
                <option value="洪水">洪水</option>
                <option value="地震">地震</option>
                <option value="津波">津波</option>
                <option value="土砂災害">土砂災害</option>
                <option value="高潮">高潮</option>
                <option value="火山災害">火山災害</option>
                <option value="その他">その他</option>
            </select>
        </div>
        <div class="filter-item">
            <label for="f-landform">地形分類：</label>
            <select id="f-landform">
                <option value="">すべて</option>
{landform_options_html}
            </select>
        </div>
    </div>
    <p id="f-count">該当：{total_monuments:,}基</p>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>ID</th><th>碑名</th><th>都道府県</th><th>所在地</th><th>災害種別</th><th>地形分類</th><th>建立年</th><th>地図</th></tr>
            </thead>
            <tbody id="f-tbody">
{initial_monument_rows_html}
            </tbody>
        </table>
    </div>
    <p id="f-limit-note"{limit_note_style}>該当が多いため、最初の200基を表示しています。都道府県や災害種別で絞り込んでください。</p>

    <h2>碑とまわりの比較（全碑・全種別）</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>指標</th><th>碑の中央値</th><th>まわりの中央値</th><th>差の中央値</th><th>碑の方が大きい割合</th></tr>
            </thead>
            <tbody>
{summary_rows_html}
            </tbody>
        </table>
    </div>
    <p>移転碑を除いた集計や災害種別ごとの集計は、下の集計表（CSV）にあります。</p>

    <h2>ハザードマップの想定区域との重なり（全碑・全種別）</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>ハザード</th><th>碑：区域内</th><th>まわり：区域内</th><th>碑：浸水深3m以上</th><th>まわり：浸水深3m以上</th></tr>
            </thead>
            <tbody>
{hazard_rows_html}
            </tbody>
        </table>
    </div>
    <p>想定区域との重なりを示すもので、危険度の判定ではありません。</p>

    <h2>地形分類（全碑・全種別）</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>地形分類</th><th>碑の数</th><th>碑の割合</th><th>まわりの数</th><th>まわりの割合</th></tr>
            </thead>
            <tbody>
{landform_rows_html}
            </tbody>
        </table>
    </div>
    <p>地形分類のデータがない碑 {mon_no_data:,}基・まわりの地点 {pt_no_data:,}点は、割合の計算から除いています。</p>

    <h2>グラフ</h2>
    <h3>災害の発生年代と碑の建立年代</h3>
    <img src="fig/years_all.png" alt="災害の発生年代と碑の建立年代">
    <h3>都道府県別の碑の数</h3>
    <img src="fig/pref_counts_all.png" alt="都道府県別の碑の数">

    <h2>データのダウンロード（CSV、Excel で開けます）</h2>
    <ul>
        <li><a href="national_report.pdf">印刷用PDF（A4・6ページ）</a></li>
        <li><a href="data/summary_all.csv">集計表</a></li>
        <li><a href="data/hazard_summary_all.csv">ハザードマップの想定区域との重なり</a></li>
        <li><a href="data/landform_all.csv">地形分類</a></li>
        <li><a href="data/relocated_all.csv">移転碑の一覧</a></li>
        <li><a href="data/pref_counts_all.csv">都道府県別の件数</a></li>
        <li><a href="data/years_all.csv">年代別の碑の数</a></li>
    </ul>
    <p>都道府県別のデータは各県のページからダウンロードできます。</p>

    <h2>出典</h2>
    <ul>
        <li>自然災害伝承碑：国土地理院（<a href="https://www.gsi.go.jp/bousaichiri/denshouhi.html">https://www.gsi.go.jp/bousaichiri/denshouhi.html</a>）</li>
        <li>標高・傾斜：国土地理院 標高API（標高タイル）から算出</li>
        <li>地形分類：国土地理院 地形分類（自然地形）</li>
        <li>河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）</li>
        <li>ハザード情報：<a href="{HAZARD_SOURCE_URL}">ハザードマップポータルサイト</a>（洪水浸水想定区域（想定最大規模）・津波浸水想定・高潮浸水想定区域・土砂災害警戒区域）</li>
        <li>ハザード情報は同サイトの配信データ（タイル画像）の色を読み取って判定・集計しています（加工して作成）</li>
        <li>上記を加工して作成</li>
        <li>国土数値情報（海岸線データ）は非商用に限り利用できます。本ページは非商用です。</li>
    </ul>

    <h2>ご利用上の注意</h2>
    <ul>
        <li>ハザードマップの想定区域は国・都道府県が公表した想定です。本ページの集計は想定区域との重なりを示すもので、危険度の判定ではありません。防災上の判断には自治体のハザードマップをご利用ください。</li>
        <li>本地図の分析結果は、伝承碑の位置と地形との「相関」を示すもので、災害の発生を予測・保証するものではありません。防災上の判断には自治体のハザードマップをご利用ください。</li>
        <li>碑の位置は被災した地点とは限りません（移設された碑もあります）。伝承碑の登録は市町村の申請によるもので、すべての碑を網羅しているわけではありません。</li>
        <li>移転碑（伝承内容に「移転」「移設」を含む碑、全国{relocated_count}基）は文字で機械的に選んでいるため、集団移転や施設の移転を伝える碑など、碑そのものが移設されていないものも含まれます。</li>
        <li>{hazard_note_combined}</li>
        <li>地形分類（自然地形）のデータは整備された地域が限られ、全国の碑の {lf_no_data_pct:.1f}%（{mon_no_data:,}基）はデータがありません。</li>
        <li>1基の碑が複数の災害種別を持つことがあります。</li>
    </ul>

    {bottom_links_html}

    <script>
    const PREF_NAMES = {json_pref_names};
    const PREF_COUNTS = {json_pref_counts};
    const COLOR_CLASSES = [
        {{ label: "0", min: 0, max: 0, bg: "#f2f2f2", text: "#333333" }},
        {{ label: "1〜9", min: 1, max: 9, bg: "#deebf7", text: "#333333" }},
        {{ label: "10〜19", min: 10, max: 19, bg: "#9ecae1", text: "#333333" }},
        {{ label: "20〜49", min: 20, max: 49, bg: "#6baed6", text: "#333333" }},
        {{ label: "50〜99", min: 50, max: 99, bg: "#3182bd", text: "#ffffff" }},
        {{ label: "100以上", min: 100, max: Infinity, bg: "#08519c", text: "#ffffff" }}
    ];
    const MONUMENTS = {json_monuments};

    function getColorClass(n) {{
        for (let i = 0; i < COLOR_CLASSES.length; i++) {{
            const c = COLOR_CLASSES[i];
            if (n >= c.min && n <= c.max) {{
                return c;
            }}
        }}
        return COLOR_CLASSES[COLOR_CLASSES.length - 1];
    }}

    function updateMap() {{
        const mapSelect = document.getElementById('map-type');
        const selectedField = mapSelect.value;
        const selectedText = mapSelect.options[mapSelect.selectedIndex].text;
        
        const legendTitle = document.getElementById('legend-title');
        if (selectedText === '碑の数') {{
            legendTitle.textContent = '碑の数（単位：基）';
        }} else {{
            legendTitle.textContent = selectedText + 'の碑の数（単位：基）';
        }}

        for (const p in PREF_COUNTS) {{
            const tile = document.getElementById('tile-' + p);
            if (!tile) continue;
            const counts = PREF_COUNTS[p];
            const n = counts[selectedField] !== undefined ? counts[selectedField] : 0;
            const cInfo = getColorClass(n);
            tile.style.backgroundColor = cInfo.bg;
            tile.style.color = cInfo.text;
            
            const prefName = PREF_NAMES[p] || p;
            const countText = selectedText === '碑の数' ? '碑の数 ' + n + '基' : selectedText + ' ' + n + '基';
            tile.title = prefName + '：' + countText;
            
            const countEl = tile.querySelector('.tile-count');
            if (countEl) {{
                countEl.textContent = n;
            }}
        }}
    }}

    function updateMonumentList() {{
        const prefVal = document.getElementById('f-pref').value;
        const typeVal = document.getElementById('f-type').value;
        const landformVal = document.getElementById('f-landform').value;

        const tbody = document.getElementById('f-tbody');
        tbody.textContent = '';

        let matchCount = 0;
        const maxDisplay = 200;

        for (let i = 0; i < MONUMENTS.length; i++) {{
            const mon = MONUMENTS[i];
            // mon = [ID, 碑名, 県コード, 所在地, 災害種別, 地形分類, 建立年, 緯度, 経度, 種別リスト]
            if (prefVal && mon[2] !== prefVal) continue;
            if (typeVal && (!mon[9] || mon[9].indexOf(typeVal) === -1)) continue;
            if (landformVal && mon[5] !== landformVal) continue;

            matchCount++;
            if (matchCount <= maxDisplay) {{
                const tr = document.createElement('tr');

                // ID
                const tdId = document.createElement('td');
                tdId.textContent = mon[0];
                tr.appendChild(tdId);

                // 碑名
                const tdName = document.createElement('td');
                tdName.textContent = mon[1];
                tr.appendChild(tdName);

                // 都道府県 (リンク)
                const tdPref = document.createElement('td');
                const aPref = document.createElement('a');
                aPref.href = 'pref_' + mon[2] + '.html';
                aPref.textContent = PREF_NAMES[mon[2]] || mon[2];
                tdPref.appendChild(aPref);
                tr.appendChild(tdPref);

                // 所在地
                const tdLoc = document.createElement('td');
                tdLoc.textContent = mon[3];
                tr.appendChild(tdLoc);

                // 災害種別
                const tdDisaster = document.createElement('td');
                tdDisaster.textContent = mon[4];
                tr.appendChild(tdDisaster);

                // 地形分類
                const tdLf = document.createElement('td');
                tdLf.textContent = mon[5];
                tr.appendChild(tdLf);

                // 建立年
                const tdYear = document.createElement('td');
                tdYear.textContent = mon[6];
                tr.appendChild(tdYear);

                // 地図 (リンク)
                const tdMap = document.createElement('td');
                const aMap = document.createElement('a');
                aMap.href = 'https://maps.gsi.go.jp/#16/' + mon[7] + '/' + mon[8] + '/';
                aMap.target = '_blank';
                aMap.rel = 'noopener noreferrer';
                aMap.textContent = '地理院地図';
                tdMap.appendChild(aMap);
                tr.appendChild(tdMap);

                tbody.appendChild(tr);
            }}
        }}

        const countEl = document.getElementById('f-count');
        countEl.textContent = '該当：' + matchCount.toLocaleString() + '基';

        const limitNote = document.getElementById('f-limit-note');
        if (matchCount > maxDisplay) {{
            limitNote.style.display = 'block';
        }} else {{
            limitNote.style.display = 'none';
        }}
    }}

    document.getElementById('map-type').addEventListener('change', updateMap);
    document.getElementById('f-pref').addEventListener('change', updateMonumentList);
    document.getElementById('f-type').addEventListener('change', updateMonumentList);
    document.getElementById('f-landform').addEventListener('change', updateMonumentList);
    </script>
</body>
</html>"""

    # コピーとファイル保存
    created_files = []

    csv_names = [
        "summary_all.csv",
        "hazard_summary_all.csv",
        "landform_all.csv",
        "relocated_all.csv",
        "pref_counts_all.csv",
        "years_all.csv",
    ]
    for name in csv_names:
        src = output_dir / name
        dst = docs_data_dir / name
        shutil.copy(src, dst)
        created_files.append(dst)

    fig_names = [
        "years_all.png",
        "pref_counts_all.png",
    ]
    for name in fig_names:
        src = output_dir / "fig" / name
        dst = fig_dir / name
        shutil.copy(src, dst)
        created_files.append(dst)

    pdf_src = output_dir / "national_report.pdf"
    pdf_dst = site_dir / "national_report.pdf"
    shutil.copy(pdf_src, pdf_dst)
    created_files.append(pdf_dst)

    index_html_path = site_dir / "index.html"
    index_html_path.write_text(html_content, encoding='utf-8', newline='\n')
    created_files.append(index_html_path)

    # 公開前チェック
    issues = find_private_info(created_files)

    if issues:
        if quiet:
            raise RuntimeError(f"公開前チェック：問題あり（{len(issues)}件）")
        else:
            size_kb = index_html_path.stat().st_size / 1024
            try:
                rel_index_path = index_html_path.relative_to(PROJECT_ROOT).as_posix()
            except ValueError:
                rel_index_path = str(index_html_path)
            print(f"全国ページ：{rel_index_path}")
            print(f"碑：{total_monuments:,}基（{len(PREFECTURES)}都道府県）\u3000伝承碑データ取得日：{latest_date}")
            print(f"色分け地図（碑の数）：0：{c_dist['0']}／1〜9：{c_dist['1〜9']}／10〜19：{c_dist['10〜19']}／20〜49：{c_dist['20〜49']}／50〜99：{c_dist['50〜99']}／100以上：{c_dist['100以上']}")
            print(f"一覧の地形分類：{len(lf_options) - 1}区分＋データなし（データなし {mon_no_data:,}基）")
            print(f"作成したファイル：{len(created_files)}")
            print(f"docs/index.html のサイズ：{size_kb:.1f} KB")
            print("公開前チェック：問題あり")
            for p, l, msg in issues:
                try:
                    rel_p = Path(p).relative_to(PROJECT_ROOT)
                except ValueError:
                    rel_p = p
                print(f"{rel_p} ({l}行目): {msg}")
            sys.exit(1)

    if not quiet:
        size_kb = index_html_path.stat().st_size / 1024
        try:
            rel_index_path = index_html_path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            rel_index_path = str(index_html_path)
        print(f"全国ページ：{rel_index_path}")
        print(f"碑：{total_monuments:,}基（{len(PREFECTURES)}都道府県）\u3000伝承碑データ取得日：{latest_date}")
        print(f"色分け地図（碑の数）：0：{c_dist['0']}／1〜9：{c_dist['1〜9']}／10〜19：{c_dist['10〜19']}／20〜49：{c_dist['20〜49']}／50〜99：{c_dist['50〜99']}／100以上：{c_dist['100以上']}")
        print(f"一覧の地形分類：{len(lf_options) - 1}区分＋データなし（データなし {mon_no_data:,}基）")
        print(f"作成したファイル：{len(created_files)}")
        print(f"docs/index.html のサイズ：{size_kb:.1f} KB")
        print("公開前チェック：問題なし")

    return created_files


def main():
    build_national()


if __name__ == "__main__":
    main()
