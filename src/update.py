import argparse
import sys
import re
import math
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from src.prefectures import PREFECTURES
    import src.load_monuments as lm
except ImportError:
    from prefectures import PREFECTURES
    import load_monuments as lm

REQUIRED_COLS_FOR_COMPARE = [
    "碑名", "建立年", "所在地", "災害名", "災害種別", 
    "伝承内容", "緯度", "経度", "公開日", "修正等公開日", "制限事項"
]

def get_history_file(pref_code):
    return PROJECT_ROOT / "output" / f"update_history_{pref_code}.csv"

def get_second_latest_raw_csv(base_dir=None):
    if base_dir is None:
        base_dir = PROJECT_ROOT / "data" / "raw"
    base_path = Path(base_dir)
    if not base_path.exists():
        return None
    
    dirs = [d for d in base_path.iterdir() if d.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', d.name)]
    if len(dirs) < 2:
        return None
        
    second_latest_dir = sorted(dirs)[-2]
    csv_files = list(second_latest_dir.glob("*.csv"))
    if not csv_files:
        return None
    if len(csv_files) >= 2:
        file_names = ", ".join([f.name for f in csv_files])
        raise ValueError(f"エラー: 2番目に新しいフォルダ {second_latest_dir.name} に複数のCSVファイルが存在します: {file_names}")
    
    return str(csv_files[0])

def determine_old_csv(pref_code, base_dir=None):
    history_file = get_history_file(pref_code)
    warn_flag = False
    if history_file.exists():
        try:
            df_hist = pd.read_csv(history_file, encoding='utf-8-sig', dtype=str)
            completed = df_hist[df_hist['結果'] == '完了']
            if not completed.empty:
                last_completed = completed.iloc[-1]
                old_file_rel = last_completed['新データのファイル']
                old_file_abs = PROJECT_ROOT / old_file_rel
                if old_file_abs.exists():
                    return str(old_file_abs)
            warn_flag = True
        except Exception:
            warn_flag = True
            
    if warn_flag:
        print("注意：更新履歴の完了記録またはその新データファイルが見つかりません。2番目に新しい日付フォルダと比べます")
            
    # If no history or not found, try 2nd latest
    second_latest = get_second_latest_raw_csv(base_dir)
    return second_latest

def check_duplicates(df, name):
    if df.empty:
        return
    duplicates = df[df.duplicated('ID')]['ID'].unique()
    if len(duplicates) > 0:
        dup_str = ", ".join(map(str, duplicates))
        print(f"エラー: {name}に重複したIDがあります: {dup_str}")
        sys.exit(1)

def format_string(val):
    if pd.isna(val):
        return ""
    val_str = str(val).strip()
    if val_str == "nan":
        return ""
    return val_str

def parse_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return float('nan')

def compare_dataframes(df_old, df_new):
    if df_old is None:
        df_old = pd.DataFrame(columns=lm.REQUIRED_COLUMNS)
    if df_new is None:
        df_new = pd.DataFrame(columns=lm.REQUIRED_COLUMNS)

    old_ids = set(df_old['ID'].tolist()) if not df_old.empty else set()
    new_ids = set(df_new['ID'].tolist()) if not df_new.empty else set()
    
    diff_records = []
    
    df_old_indexed = df_old.set_index('ID') if not df_old.empty else pd.DataFrame()
    df_new_indexed = df_new.set_index('ID') if not df_new.empty else pd.DataFrame()
    
    added_ids = new_ids - old_ids
    for i in added_ids:
        row_new = df_new_indexed.loc[i]
        diff_records.append({
            'ID': i,
            '区分': '追加',
            '碑名': format_string(row_new.get('碑名', '')),
            '変わった列': '',
            '位置の変更': ''
        })
        
    deleted_ids = old_ids - new_ids
    for i in deleted_ids:
        row_old = df_old_indexed.loc[i]
        diff_records.append({
            'ID': i,
            '区分': '削除',
            '碑名': format_string(row_old.get('碑名', '')),
            '変わった列': '',
            '位置の変更': ''
        })
        
    common_ids = old_ids & new_ids
    for i in common_ids:
        row_old = df_old_indexed.loc[i]
        row_new = df_new_indexed.loc[i]
        
        changed_cols = []
        loc_changed = False
        
        for col in REQUIRED_COLS_FOR_COMPARE:
            val_old = row_old.get(col, '')
            val_new = row_new.get(col, '')
            
            if col in ['緯度', '経度']:
                f_old = parse_float(val_old)
                f_new = parse_float(val_new)
                if math.isnan(f_old) and math.isnan(f_new):
                    continue
                if math.isnan(f_old) or math.isnan(f_new):
                    changed_cols.append(col)
                    loc_changed = True
                elif abs(f_old - f_new) > 0.0000001:
                    changed_cols.append(col)
                    loc_changed = True
            else:
                s_old = format_string(val_old)
                s_new = format_string(val_new)
                if s_old != s_new:
                    changed_cols.append(col)
                    
        if changed_cols:
            diff_records.append({
                'ID': i,
                '区分': '変更',
                '碑名': format_string(row_new.get('碑名', '')),
                '変わった列': '、'.join(changed_cols),
                '位置の変更': 'あり' if loc_changed else 'なし'
            })
            
    df_diff = pd.DataFrame(diff_records, columns=['ID', '区分', '碑名', '変わった列', '位置の変更'])
    
    # Sort: 追加(1) -> 変更(2) -> 削除(3), then ID asc
    order_map = {'追加': 1, '変更': 2, '削除': 3}
    if not df_diff.empty:
        df_diff['sort_order'] = df_diff['区分'].map(order_map)
        df_diff = df_diff.sort_values(['sort_order', 'ID']).drop('sort_order', axis=1)
        
    return df_diff

def to_rel_path(path_str):
    if not path_str:
        return ""
    try:
        p = Path(path_str).resolve()
        r = PROJECT_ROOT.resolve()
        try:
            rel = p.relative_to(r)
            return rel.as_posix()
        except ValueError:
            return p.as_posix()
    except Exception:
        return str(path_str).replace('\\', '/')

def save_update_history(pref_code, old_date, new_date, old_file, new_file, old_count, new_count, df_diff, result):
    history_file = get_history_file(pref_code)
    
    add_c = len(df_diff[df_diff['区分'] == '追加']) if not df_diff.empty else 0
    mod_c = len(df_diff[df_diff['区分'] == '変更']) if not df_diff.empty else 0
    loc_c = len(df_diff[(df_diff['区分'] == '変更') & (df_diff['位置の変更'] == 'あり')]) if not df_diff.empty else 0
    del_c = len(df_diff[df_diff['区分'] == '削除']) if not df_diff.empty else 0
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    record = {
        '実行日時': now_str,
        '県コード': pref_code,
        '旧データ取得日': old_date if old_date else 'なし',
        '新データ取得日': new_date,
        '旧データのファイル': to_rel_path(old_file) if old_file else '',
        '新データのファイル': to_rel_path(new_file),
        '旧基数': old_count,
        '新基数': new_count,
        '追加': add_c,
        '変更': mod_c,
        'うち位置の変更': loc_c,
        '削除': del_c,
        '結果': result
    }
    
    df_new_row = pd.DataFrame([record])
    
    if not history_file.exists():
        history_file.parent.mkdir(parents=True, exist_ok=True)
        df_new_row.to_csv(history_file, index=False, encoding='utf-8-sig')
    else:
        df_new_row.to_csv(history_file, index=False, encoding='utf-8-sig', mode='a', header=False)

def default_runner(cmd):
    return subprocess.run(cmd, cwd=PROJECT_ROOT)

def run_steps(steps, runner, new_csv_path, pref_code, df_diff, old_date, new_date, old_file, new_file, old_count, new_count):
    total = len(steps)
    for idx, (desc, args) in enumerate(steps, 1):
        try:
            print(f"[{idx}/{total}] {desc}", flush=True)
            cmd = [sys.executable, str(PROJECT_ROOT / "src" / args[0])] + args[1:]
            res = runner(cmd)
            if res.returncode != 0:
                print(f"[{idx}/{total}] {desc} で失敗しました。原因を直してからもう一度 update.py を実行してください（取得済みの分はキャッシュから読むので短時間で済みます）", flush=True)
                save_update_history(pref_code, old_date, new_date, old_file, new_file, old_count, new_count, df_diff, f"失敗（[{idx}/{total}] {desc}）")
                sys.exit(1)
        except KeyboardInterrupt:
            print("中断しました", flush=True)
            save_update_history(pref_code, old_date, new_date, old_file, new_file, old_count, new_count, df_diff, f"中断（[{idx}/{total}] {desc}）")
            sys.exit(1)
            
    save_update_history(pref_code, old_date, new_date, old_file, new_file, old_count, new_count, df_diff, "完了")

def main(args=None, runner=default_runner):
    parser = argparse.ArgumentParser(description='データの更新と差分抽出')
    parser.add_argument('--pref', type=str, required=True, help='県コード (01-47)')
    parser.add_argument('--old', type=str, help='古いCSVのパス')
    parser.add_argument('--new', type=str, help='新しいCSVのパス')
    parser.add_argument('--dry-run', action='store_true', help='差分の判定までで止める')
    
    parsed = parser.parse_args(args)
    pref_code = parsed.pref
    
    if pref_code == "all" or pref_code not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれかを指定してください（all は不可）。")
        sys.exit(1)
        
    pref_name = PREFECTURES[pref_code]
    
    new_file = parsed.new
    if not new_file:
        try:
            new_file = lm.get_latest_raw_csv()
        except Exception as e:
            print(e)
            sys.exit(1)
    new_file = str(Path(new_file).resolve())
            
    old_file = parsed.old
    if not old_file and parsed.old is None:
        old_file = determine_old_csv(pref_code)
        
    if old_file and Path(old_file).resolve() == Path(new_file).resolve():
        print("古いデータと新しいデータが同じファイルです")
        sys.exit(1)
        
    new_date = lm.get_fetch_date(new_file)
    try:
        df_new_full = lm.load_csv(new_file)
        lm.validate_dataframe(df_new_full)
        df_new_full['県コード'] = df_new_full['ID'].str[:2]
        df_new = lm.filter_by_prefecture(df_new_full, pref_code)
        check_duplicates(df_new, "新しいデータ")
    except Exception as e:
        print(e)
        sys.exit(1)
        
    old_date = "none"
    df_old = None
    if old_file:
        old_date = lm.get_fetch_date(old_file)
        try:
            df_old_full = lm.load_csv(old_file)
            lm.validate_dataframe(df_old_full)
            df_old_full['県コード'] = df_old_full['ID'].str[:2]
            df_old = lm.filter_by_prefecture(df_old_full, pref_code)
            check_duplicates(df_old, "古いデータ")
        except Exception as e:
            print(e)
            sys.exit(1)
            
    df_diff = compare_dataframes(df_old, df_new)
    
    out_dir = PROJECT_ROOT / "output" / "diff"
    out_dir.mkdir(parents=True, exist_ok=True)
    diff_file = out_dir / f"diff_{pref_code}_{old_date}_{new_date}.csv"
    df_diff.to_csv(diff_file, index=False, encoding='utf-8-sig')
    
    # 画面へのまとめ表示
    old_count = len(df_old) if df_old is not None else 0
    new_count = len(df_new)
    
    print(f"対象の県名: {pref_name}")
    if old_file:
        print(f"古いデータ: {to_rel_path(old_file)}（取得日 {old_date}、{old_count}基）")
    else:
        print("古いデータ: なし（初回）")
        old_date = None
        
    print(f"新しいデータ: {to_rel_path(new_file)}（取得日 {new_date}、{new_count}基）")
    
    add_c = len(df_diff[df_diff['区分'] == '追加']) if not df_diff.empty else 0
    mod_c = len(df_diff[df_diff['区分'] == '変更']) if not df_diff.empty else 0
    loc_c = len(df_diff[(df_diff['区分'] == '変更') & (df_diff['位置の変更'] == 'あり')]) if not df_diff.empty else 0
    del_c = len(df_diff[df_diff['区分'] == '削除']) if not df_diff.empty else 0
    
    print(f"追加: {add_c}基 / 変更: {mod_c}基（うち位置の変更 {loc_c}基） / 削除: {del_c}基")
    
    if len(df_diff) > 0:
        first = True
        for _, row in df_diff.iterrows():
            prefix = "（1件ずつ）" if first else "           "
            if row['区分'] == '追加':
                print(f"{prefix}[追加] {row['ID']} {row['碑名']}")
            elif row['区分'] == '変更':
                print(f"{prefix}[変更] {row['ID']} {row['碑名']}（変わった列：{row['変わった列']}）")
            elif row['区分'] == '削除':
                print(f"{prefix}[削除] {row['ID']} {row['碑名']}")
            first = False
    else:
        print("前回からの変更はありません")
        
    print(f"差分ファイル: {to_rel_path(diff_file)}")
    
    if parsed.dry_run:
        return
        
    steps = [
        ("データの読み込み", ["load_monuments.py", "--pref", pref_code, "--raw", new_file]),
        ("標高の付与（碑）", ["add_elevation.py", "--pref", pref_code]),
        ("河川・海岸の付与（碑）", ["add_river_coast.py", "--pref", pref_code]),
        ("地形分類の付与（碑）", ["add_landform.py", "--pref", pref_code]),
        ("比較地点の作成", ["make_comparison_points.py", "--pref", pref_code]),
        ("標高の付与（比較地点）", ["add_elevation.py", "--pref", pref_code, "--target", "points"]),
        ("河川・海岸の付与（比較地点）", ["add_river_coast.py", "--pref", pref_code, "--target", "points"]),
        ("地形分類の付与（比較地点）", ["add_landform.py", "--pref", pref_code, "--target", "points"]),
        ("集計", ["summarize.py", "--pref", pref_code]),
        ("地図作成", ["make_map.py", "--pref", pref_code]),
        ("公開用ページの作成", ["build_site.py", "--pref", pref_code])
    ]
    
    run_steps(steps, runner, new_file, pref_code, df_diff, old_date, new_date, old_file, new_file, old_count, new_count)

if __name__ == '__main__':
    main()

