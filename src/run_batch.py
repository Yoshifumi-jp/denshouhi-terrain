import argparse
import sys
import datetime
from pathlib import Path

# src.prefectures.PREFECTURESからキーを取得
try:
    from src.prefectures import PREFECTURES, LANDLOCKED
    import src.load_monuments as lm
    import src.add_river_coast as add_river_coast
    import src.update as update
except ImportError:
    from prefectures import PREFECTURES, LANDLOCKED
    import load_monuments as lm
    import add_river_coast
    import update

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 長時間の実行前に Windows のスリープを「なし」にすること

def count_cache_elevation(project_root):
    cache_file = project_root / "data" / "cache" / "elevation_cache.csv"
    if not cache_file.exists():
        return 0
    with open(cache_file, "rb") as f:
        # 見出し行を除くため、行数-1
        count = sum(1 for _ in f) - 1
        return count if count > 0 else 0

def count_cache_files(sub_dir, project_root):
    cache_dir = project_root / "data" / "cache" / sub_dir
    if not cache_dir.exists():
        return 0
    return sum(1 for f in cache_dir.rglob("*") if f.is_file())

def get_history_file(pref_code, project_root):
    return project_root / "output" / f"update_history_{pref_code}.csv"

def is_completed(pref_code, latest_csv_rel, project_root):
    history_file = get_history_file(pref_code, project_root)
    if not history_file.exists():
        return False
    import pandas as pd
    try:
        df = pd.read_csv(history_file, encoding='utf-8-sig', dtype=str)
        completed = df[df['結果'] == '完了']
        if completed.empty:
            return False
        last_completed = completed.iloc[-1]
        old_file_rel = last_completed['新データのファイル']
        if old_file_rel == latest_csv_rel:
            return True
        return False
    except Exception:
        return False

def default_now():
    return datetime.datetime.now()

def format_duration(seconds):
    seconds = int(round(seconds))
    if seconds < 60:
        return "1分未満"
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    if hours > 0:
        return f"{hours}時間{minutes}分"
    else:
        return f"{minutes}分"

def log_batch_result(start_time, end_time, pref_code, num_monuments, result, duration_sec, calls_elev, calls_haz, calls_land, new_csv_file, project_root):
    log_file = project_root / "output" / "batch_log.csv"
    
    import pandas as pd
    record = {
        '実行開始': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        '実行終了': end_time.strftime('%Y-%m-%d %H:%M:%S'),
        '県コード': pref_code,
        '県名': PREFECTURES[pref_code],
        '基数': num_monuments,
        '結果': result,
        '所要時間_秒': int(round(duration_sec)),
        '標高の問い合わせ': calls_elev,
        'ハザードタイルの取得': calls_haz,
        '地形分類タイルの取得': calls_land,
        '新データのファイル': new_csv_file
    }
    
    df_new = pd.DataFrame([record])
    if not log_file.exists():
        log_file.parent.mkdir(parents=True, exist_ok=True)
        df_new.to_csv(log_file, index=False, encoding='utf-8-sig')
    else:
        df_new.to_csv(log_file, index=False, encoding='utf-8-sig', mode='a', header=False)

def to_rel_path(p, project_root):
    try:
        return Path(p).resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return Path(p).as_posix()

def main(args=None, runner=None, root=None, now=None):
    project_root = Path(root) if root else PROJECT_ROOT
    if now is None:
        now = default_now
    if runner is None:
        runner = update.default_runner
        
    parser = argparse.ArgumentParser(description='複数県の一括処理')
    parser.add_argument('--pref', type=str, required=True, help='県コード (01-47, カンマ区切りまたはall)')
    parser.add_argument('--check-only', action='store_true', help='データの確認だけ（問い合わせなし）')
    parser.add_argument('--force', action='store_true', help='完了済みの県もやり直す')
    
    parsed = parser.parse_args(args)
    
    try:
        pref_codes = lm.parse_pref_arg(parsed.pref)
        if pref_codes == "all":
            pref_codes = sorted(PREFECTURES.keys())
    except ValueError as e:
        print(e)
        sys.exit(1)
        
    try:
        latest_csv = lm.get_latest_raw_csv(base_dir=project_root / "data" / "raw")
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)
        
    latest_csv_rel = to_rel_path(latest_csv, project_root)
    fetch_date = lm.get_fetch_date(latest_csv)
    
    try:
        df_full = lm.load_csv(latest_csv)
        lm.validate_dataframe(df_full)
        df_full['県コード'] = df_full['ID'].str[:2]
    except Exception as e:
        print(f"エラー: 最新CSVの読み込みに失敗しました: {e}")
        sys.exit(1)
        
    pref_counts = df_full.groupby('県コード').size().to_dict()
    
    total_monuments = sum(pref_counts.get(p, 0) for p in pref_codes)
    
    pref_names_display = "、".join([f"{PREFECTURES[p]}（{p}）" for p in pref_codes])
    print(f"一括実行の対象: {pref_names_display}（{len(pref_codes)}県・{total_monuments}基）")
    print(f"使う伝承碑データ: {latest_csv_rel}（取得日 {fetch_date}）")
    print("データの確認:")
    
    missing_all = []
    pref_info_list = []
    
    for p in pref_codes:
        count = pref_counts.get(p, 0)
        rivers_list, coast_list, missing = add_river_coast.find_input_shapefiles(p, project_root / "data" / "raw")
        
        river_text = f"河川 {len(rivers_list)}県分"
        if p in LANDLOCKED:
            coast_text = "海岸線 なし（海のない県）"
        else:
            coast_text = f"海岸線 {len(coast_list)}県分"
            
        is_done = is_completed(p, latest_csv_rel, project_root)

        status_text = ""
        if missing:
            status_text = "足りません"
            missing_all.extend(missing)
        else:
            if is_done:
                if parsed.force:
                    status_text = "そろっています（完了済み・--force でやり直します）"
                else:
                    status_text = "そろっています（完了済みのため飛ばします）"
            else:
                status_text = "そろっています"
                
        print(f"  {PREFECTURES[p]}（{p}）{count}基　{river_text}・{coast_text}　{status_text}")
        if missing:
            for m in missing:
                print(f"      {m}")
                
        pref_info_list.append({
            'code': p,
            'count': count,
            'is_done': is_done,
            'missing': len(missing) > 0
        })
        
    if missing_all:
        print("データが足りない県があります。docs/dev/m11_downloads.md のとおりダウンロード・展開して data/raw/ に置き、もう一度実行してください")
        sys.exit(1)
        
    if parsed.check_only:
        print("データの確認だけ行いました（--check-only）")
        sys.exit(0)
        
    results_summary = []
    
    for idx, info in enumerate(pref_info_list, 1):
        p = info['code']
        count = info['count']
        
        if info['is_done'] and not parsed.force:
            print(f"[{idx}/{len(pref_codes)}] {PREFECTURES[p]}（{p}）完了済みのため飛ばします")
            results_summary.append({
                'code': p, 'status': '飛ばした'
            })
            continue
            
        start_time = now()
        print(f"[{idx}/{len(pref_codes)}] {PREFECTURES[p]}（{p}）{count}基 開始 {start_time.strftime('%Y-%m-%d %H:%M')}")
        
        elev_before = count_cache_elevation(project_root)
        haz_before = count_cache_files("hazard", project_root)
        land_before = count_cache_files("landform", project_root)
        
        cmd = [sys.executable, str(project_root / "src" / "update.py"), "--pref", p, "--no-site"]
        if info['is_done'] and parsed.force:
            # 完了済みの県をやり直すときは、古いデータを「なし」にして全件を処理し直す（同じファイルどうしの比較で止まるのを防ぐ）
            cmd.append("--old=")
        
        result_status = "完了"
        try:
            res = runner(cmd)
            if res.returncode != 0:
                result_status = "失敗"
        except KeyboardInterrupt:
            result_status = "中断"
            
        end_time = now()
        duration_sec = (end_time - start_time).total_seconds()
        
        elev_after = count_cache_elevation(project_root)
        haz_after = count_cache_files("hazard", project_root)
        land_after = count_cache_files("landform", project_root)
        
        calls_elev = max(0, elev_after - elev_before)
        calls_haz = max(0, haz_after - haz_before)
        calls_land = max(0, land_after - land_before)
        
        log_batch_result(start_time, end_time, p, count, result_status, duration_sec, calls_elev, calls_haz, calls_land, latest_csv_rel, project_root)
        
        dur_str = format_duration(duration_sec)
        if result_status == "完了":
            print(f"[{idx}/{len(pref_codes)}] {PREFECTURES[p]}（{p}）完了　所要時間 {dur_str}　問い合わせ：標高 {calls_elev:,}回・ハザードタイル {calls_haz:,}枚・地形分類タイル {calls_land:,}枚")
            results_summary.append({
                'code': p, 'status': '完了', 'dur_str': dur_str, 'calls_elev': calls_elev, 'calls_haz': calls_haz, 'calls_land': calls_land
            })
        elif result_status == "失敗":
            print(f"[{idx}/{len(pref_codes)}] {PREFECTURES[p]}（{p}）失敗（上の表示で原因を確かめてください）　所要時間 {dur_str}　問い合わせ：標高 {calls_elev:,}回・ハザードタイル {calls_haz:,}枚・地形分類タイル {calls_land:,}枚")
            results_summary.append({
                'code': p, 'status': '失敗', 'dur_str': dur_str, 'calls_elev': calls_elev, 'calls_haz': calls_haz, 'calls_land': calls_land
            })
        elif result_status == "中断":
            print("中断しました。もう一度同じコマンドを実行すると、完了済みの県を飛ばして続きから始まります（取得済みの分はキャッシュから読みます）")
            sys.exit(1)
            
    print("一括実行のまとめ（output/batch_log.csv に記録しました）")
    count_done = 0
    count_fail = 0
    count_skip = 0
    
    for r in results_summary:
        p = r['code']
        if r['status'] == '飛ばした':
            print(f"  {PREFECTURES[p]}（{p}）完了済みのため飛ばしました")
            count_skip += 1
        elif r['status'] == '完了':
            print(f"  {PREFECTURES[p]}（{p}）完了　{r['dur_str']}　標高 {r['calls_elev']:,}・ハザード {r['calls_haz']:,}・地形分類 {r['calls_land']:,}")
            count_done += 1
        elif r['status'] == '失敗':
            print(f"  {PREFECTURES[p]}（{p}）失敗　{r['dur_str']}　標高 {r['calls_elev']:,}・ハザード {r['calls_haz']:,}・地形分類 {r['calls_land']:,}")
            count_fail += 1
            
    print(f"完了 {count_done}県／失敗 {count_fail}県／飛ばした {count_skip}県")
    if count_fail > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
