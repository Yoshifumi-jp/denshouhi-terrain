import argparse
import sys
import shutil
import html
from pathlib import Path
import pandas as pd

try:
    from src.prefectures import PREFECTURES
    from src.check_public import find_private_info
except ImportError:
    from prefectures import PREFECTURES
    from check_public import find_private_info

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def build_site(pref, output_dir=None, site_dir=None, data_dir=None):
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
        
    pref_name = PREFECTURES[pref]
    
    # 必要なファイルの確認
    required_output_files = [
        output_dir / f"map_{pref}.html",
        output_dir / f"summary_{pref}.csv",
        output_dir / f"landform_{pref}.csv",
        output_dir / f"relocated_{pref}.csv",
        output_dir / f"update_history_{pref}.csv",
        output_dir / "fig" / f"box_elevation_{pref}.png",
        output_dir / "fig" / f"box_slope_{pref}.png",
        output_dir / "fig" / f"box_river_dist_{pref}.png",
        output_dir / "fig" / f"box_river_height_{pref}.png",
        output_dir / "fig" / f"box_coast_dist_{pref}.png",
        output_dir / "fig" / f"bar_landform_{pref}.png"
    ]

        
    monuments_file = data_dir / f"monuments_{pref}.csv"
    
    missing = []
    for f in required_output_files:
        if not f.exists():
            missing.append(f.name)
            
    if not monuments_file.exists():
        missing.append(monuments_file.name)
        
    if missing:
        print(f"エラー: 必要なファイルが足りません: {', '.join(missing)}")
        print(f"先に以下のコマンドを実行してください。")
        print(f"python src/update.py --pref {pref}")
        sys.exit(1)
        
    # data/processed/monuments から取得日と碑の数を取得
    df_mon = pd.read_csv(monuments_file, dtype=str, encoding='utf-8-sig')
    mon_count = len(df_mon)
    
    dates = []
    if 'データ取得日' in df_mon.columns:
        dates = df_mon['データ取得日'].dropna().unique()
    fetch_date = sorted(dates)[-1] if len(dates) > 0 else ""
    
    # update_history から最終更新を取得
    df_hist = pd.read_csv(output_dir / f"update_history_{pref}.csv", dtype=str, encoding='utf-8-sig')
    completed_hist = df_hist[df_hist['結果'] == '完了']
    if not completed_hist.empty:
        last_update = str(completed_hist.iloc[-1]['実行日時']).split()[0]
    else:
        last_update = "—"
        
    # docs フォルダの準備（dev には触れない）
    site_dir.mkdir(parents=True, exist_ok=True)
    
    fig_dir = site_dir / "fig"
    fig_dir.mkdir(exist_ok=True)
    
    docs_data_dir = site_dir / "data"
    docs_data_dir.mkdir(exist_ok=True)
    
    # コピーとリスト作成
    created_files = []
    
    # map
    shutil.copy(output_dir / f"map_{pref}.html", site_dir / f"map_{pref}.html")
    created_files.append(site_dir / f"map_{pref}.html")
    
    # fig
    fig_names = ["box_elevation", "box_slope", "box_river_dist", "box_river_height", "box_coast_dist", "bar_landform"]
    fig_titles = ["標高", "傾斜", "河川までの距離", "河川との高さの差", "海岸までの距離", "地形分類"]
    for f in fig_names:
        src = output_dir / "fig" / f"{f}_{pref}.png"
        dst = fig_dir / f"{f}_{pref}.png"
        shutil.copy(src, dst)
        created_files.append(dst)
        
    # data
    for csv_file in ["summary", "landform", "relocated", "update_history"]:
        src = output_dir / f"{csv_file}_{pref}.csv"
        dst = docs_data_dir / f"{csv_file}_{pref}.csv"
        shutil.copy(src, dst)
        created_files.append(dst)
        
    # .nojekyll
    nojekyll_file = site_dir / ".nojekyll"
    nojekyll_file.touch()
    created_files.append(nojekyll_file)
    
    # index.html の作成
    index_html_path = site_dir / "index.html"
    
    # 比較表 (summary_36.csv から「全碑」「全種別」の行を抽出)
    df_sum = pd.read_csv(output_dir / f"summary_{pref}.csv", dtype=str, encoding='utf-8-sig')
    
    required_cols = ['指標', '碑_中央値', '比較地点_中央値', '差の中央値', '碑の方が大きい割合']
    missing_cols = [c for c in required_cols if c not in df_sum.columns]
    if missing_cols:
        print(f"エラー: summary_{pref}.csv に必要な列がありません: {', '.join(missing_cols)}")
        sys.exit(1)
        
    df_sum_filtered = df_sum[(df_sum['範囲'] == '全碑') & (df_sum['災害種別'] == '全種別')]
    
    def esc(s):
        if pd.isna(s):
            return ""
        return html.escape(str(s))
        
    summary_rows_html = ""
    for idx, row in df_sum_filtered.iterrows():
        metric = row.get('指標', '')
        if '標高_m' in metric: metric = '標高(m)'
        elif '傾斜_度' in metric: metric = '傾斜(度)'
        elif '河川までの距離_m' in metric: metric = '河川までの距離(m)'
        elif '河川との高さの差_m' in metric: metric = '河川との高さの差(m)'
        elif '海岸までの距離_m' in metric: metric = '海岸までの距離(m)'
        
        mon_med = esc(row.get('碑_中央値'))
        pt_med = esc(row.get('比較地点_中央値'))
        diff = esc(row.get('差の中央値'))
        
        pct_val = row.get('碑の方が大きい割合')
        try:
            pct_val = float(pct_val)
            pct_str = f"{int(round(pct_val * 100))}%"
        except (TypeError, ValueError):
            pct_str = esc(pct_val)
            
        summary_rows_html += f"<tr><td>{esc(metric)}</td><td>{mon_med}</td><td>{pt_med}</td><td>{diff}</td><td>{pct_str}</td></tr>\n"
        
    # 更新履歴
    hist_rows_html = ""
    # 新しい順
    for idx, row in completed_hist.iloc[::-1].iterrows():
        exec_date = esc(str(row.get('実行日時')).split()[0])
        fetch_d = esc(row.get('新データ取得日'))
        n_count = esc(row.get('新基数'))
        add_c = esc(row.get('追加'))
        mod_c = esc(row.get('変更'))
        del_c = esc(row.get('削除'))
        hist_rows_html += f"<tr><td>{exec_date}</td><td>{fetch_d}</td><td>{n_count}</td><td>{add_c}</td><td>{mod_c}</td><td>{del_c}</td></tr>\n"
        
    # 出典（make_mapと同じ）
    source_html = """
    <ul>
        <li>自然災害伝承碑：国土地理院（<a href="https://www.gsi.go.jp/bousaichiri/denshouhi.html">https://www.gsi.go.jp/bousaichiri/denshouhi.html</a>）</li>
        <li>背景地図：<a href="https://maps.gsi.go.jp/development/ichiran.html">地理院タイル</a>（淡色地図）</li>
        <li>標高・傾斜：国土地理院 標高API（標高タイル）から算出</li>
        <li>地形分類：国土地理院 地形分類（自然地形）</li>
        <li>河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）</li>
        <li>上記を加工して作成</li>
        <li>国土数値情報（海岸線データ）は非商用に限り利用できます。本ページは非商用です。</li>
    </ul>
    """
    
    notice_html = """
    <ul>
        <li>本地図の分析結果は、伝承碑の位置と地形との「相関」を示すもので、災害の発生を予測・保証するものではありません。防災上の判断には自治体のハザードマップをご利用ください。</li>
        <li>碑の位置は被災した地点とは限りません（移設された碑もあります）。伝承碑の登録は市町村の申請によるもので、すべての碑を網羅しているわけではありません。</li>
    </ul>
    """
    
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>自然災害伝承碑と地形（{esc(pref_name)}）</title>
    <style>
        body {{ max-width: 800px; margin: 0 auto; padding: 10px; font-family: sans-serif; font-size: 16px; }}
        img {{ max-width: 100%; height: auto; }}
        .table-container {{ overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; min-width: 500px; margin-bottom: 10px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        .btn {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
        h2 {{ margin-top: 30px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
    </style>
</head>
<body>
    <h1>自然災害伝承碑と地形（{esc(pref_name)}）</h1>
    <p>伝承碑データ取得日：{esc(fetch_date)}　碑の数：{esc(mon_count)}基　最終更新：{esc(last_update)}</p>
    <p>国土地理院の自然災害伝承碑に、碑ごとの地形（標高・傾斜・地形分類・河川や海岸との位置関係）を付け、碑のまわり（100m〜2,000m）の地点と比べた結果をまとめたものです。結果は地形との相関を示すもので、災害の予測・安全の保証ではありません。</p>
    <p style="text-align: center;"><a href="map_{pref}.html" class="btn">地図を開く（碑をクリックすると地形の診断結果が出ます）</a></p>
    
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
    
    <h2>グラフ</h2>
"""
    for f, title in zip(fig_names, fig_titles):
        html_content += f'    <h3>{esc(title)}</h3>\n    <img src="fig/{f}_{pref}.png" alt="{esc(title)}">\n'
        
    html_content += f"""
    <h2>データのダウンロード（CSV、Excel で開けます）</h2>
    <ul>
        <li><a href="data/summary_{pref}.csv">集計表</a></li>
        <li><a href="data/landform_{pref}.csv">地形分類の集計</a></li>
        <li><a href="data/relocated_{pref}.csv">移転碑の一覧</a></li>
        <li><a href="data/update_history_{pref}.csv">更新履歴</a></li>
    </ul>
    
    <h2>更新履歴</h2>
    <div class="table-container">
        <table>
            <thead>
                <tr><th>更新日</th><th>データ取得日</th><th>碑の数</th><th>追加</th><th>変更</th><th>削除</th></tr>
            </thead>
            <tbody>
                {hist_rows_html}
            </tbody>
        </table>
    </div>
    
    <h2>出典</h2>
    {source_html}
    
    <h2>ご利用上の注意</h2>
    {notice_html}
</body>
</html>"""

    index_html_path.write_text(html_content, encoding='utf-8')
    created_files.append(index_html_path)
    
    # 画面への表示とチェック
    def get_rel_path(p):
        try:
            return p.relative_to(PROJECT_ROOT)
        except ValueError:
            return p
            
    print(f"対象の県名: {pref_name}")
    print(f"データ取得日: {fetch_date}")
    print(f"碑の数: {mon_count}")
    print("作成したファイル:")
    for f in created_files:
        print(f"  {get_rel_path(f)}")
        
    # check_public を作成したファイルの一部に対して実行
    paths_to_check = [site_dir / "index.html", site_dir / f"map_{pref}.html", docs_data_dir / f"summary_{pref}.csv", docs_data_dir / f"landform_{pref}.csv", docs_data_dir / f"relocated_{pref}.csv", docs_data_dir / f"update_history_{pref}.csv"]
    
    issues = find_private_info(paths_to_check)
    if issues:
        print("公開前チェック：問題あり")
        for p, l, msg in issues:
            print(f"{get_rel_path(Path(p))} ({l}行目): {msg}")
        sys.exit(1)
    else:
        print("公開前チェック：問題なし")

def main():
    parser = argparse.ArgumentParser(description="公開用ページの作成")
    parser.add_argument("--pref", type=str, required=True, help="県コード (01-47)")
    
    args = parser.parse_args()
    pref = args.pref
    if pref == "all" or pref not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください（all は不可）。")
        sys.exit(1)
        
    build_site(pref)

if __name__ == "__main__":
    main()
