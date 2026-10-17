"""地形分類（地域版・広域版）だけを複数県で一括実行するプログラム。

指定した都道府県について src/add_landform_region.py を碑・比較地点の順に呼び出し、
結果の件数とタイルの取得枚数を集計して output/region_batch_log.csv に記録する。
長時間の実行前に Windows のスリープを「なし」にすること。
"""

import argparse
import csv
import datetime
import sys
from pathlib import Path

try:
    from src.prefectures import PREFECTURES
    import src.load_monuments as lm
    import src.update as update
    from src.run_batch import format_duration
except ImportError:
    from prefectures import PREFECTURES
    import load_monuments as lm
    import update
    from run_batch import format_duration

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_COLUMNS = [
    "実行開始",
    "実行終了",
    "県コード",
    "県名",
    "碑_数",
    "比較地点_数",
    "結果",
    "所要時間_秒",
    "地域版タイルの取得",
    "広域版タイルの取得",
    "取得済_地域版",
    "取得済_広域版",
    "データなし",
    "取得不可",
]


def default_now():
    """現在日時を返す既定の関数"""
    return datetime.datetime.now()


def count_csv_rows(csv_path):
    """CSVファイルのデータ行数（見出し行を除く）を数える"""
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def count_zoom_cache_files(zoom, project_root):
    """data/cache/landform/<zoom> の下のファイル数を数える"""
    cache_dir = project_root / "data" / "cache" / "landform" / str(zoom)
    if not cache_dir.exists():
        return 0
    return sum(1 for f in cache_dir.rglob("*") if f.is_file())


def inspect_region_outputs(pref_code, expected_mon, expected_pts, project_root):
    """出力された地域版CSV（碑・比較地点）を読み、状態別の件数と行数不一致の有無を返す"""
    proc_dir = project_root / "data" / "processed"
    mon_out = proc_dir / f"landform_region_{pref_code}.csv"
    pts_out = proc_dir / f"landform_region_points_{pref_code}.csv"

    counts = {
        "取得済（地域版）": 0,
        "取得済（広域版）": 0,
        "データなし": 0,
        "取得不可": 0,
    }
    row_mismatch = False

    for path, expected in ((mon_out, expected_mon), (pts_out, expected_pts)):
        if not path.exists():
            row_mismatch = True
            continue
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if len(rows) != expected:
            row_mismatch = True
        for row in rows:
            st = row.get("地域版_状態", "")
            if st in counts:
                counts[st] += 1

    return counts, row_mismatch


def append_region_log(
    start_time,
    end_time,
    pref_code,
    n_mon,
    n_pts,
    result_status,
    duration_sec,
    calls_13,
    calls_8,
    counts,
    project_root,
):
    """output/region_batch_log.csv に1行追記する（UTF-8 BOM付き、改行LF）"""
    log_file = project_root / "output" / "region_batch_log.csv"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    has_counts = counts is not None and result_status in ("完了", "要再実行")
    row = {
        "実行開始": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "実行終了": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "県コード": pref_code,
        "県名": PREFECTURES[pref_code],
        "碑_数": n_mon,
        "比較地点_数": n_pts,
        "結果": result_status,
        "所要時間_秒": int(round(duration_sec)),
        "地域版タイルの取得": calls_13,
        "広域版タイルの取得": calls_8,
        "取得済_地域版": counts["取得済（地域版）"] if has_counts else "",
        "取得済_広域版": counts["取得済（広域版）"] if has_counts else "",
        "データなし": counts["データなし"] if has_counts else "",
        "取得不可": counts["取得不可"] if has_counts else "",
    }

    if not log_file.exists():
        with open(log_file, "w", encoding="utf-8-sig", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS, lineterminator="\n")
            writer.writeheader()
            writer.writerow(row)
    else:
        with open(log_file, "a", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS, lineterminator="\n")
            writer.writerow(row)


def main(args=None, runner=None, root=None, now=None):
    """地域版の一括実行のメイン処理"""
    project_root = Path(root) if root else PROJECT_ROOT
    if now is None:
        now = default_now
    if runner is None:
        runner = update.default_runner

    parser = argparse.ArgumentParser(description="地形分類（地域版）の複数県一括処理")
    parser.add_argument(
        "--pref",
        type=str,
        required=True,
        help="県コード (01-47, カンマ区切りまたはall)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="入力ファイルの確認だけ（問い合わせなし）",
    )

    parsed = parser.parse_args(args)

    try:
        pref_codes = lm.parse_pref_arg(parsed.pref)
        if pref_codes == "all":
            pref_codes = sorted(PREFECTURES.keys())
    except ValueError as e:
        print(e)
        sys.exit(1)

    proc_dir = project_root / "data" / "processed"
    missing_lines = []
    missing_prefs = []

    for p in pref_codes:
        mon_path = proc_dir / f"monuments_{p}.csv"
        pts_path = proc_dir / f"points_{p}.csv"
        pref_missing = False
        if not mon_path.exists():
            missing_lines.append(f"  {PREFECTURES[p]}（{p}）monuments_{p}.csv がありません")
            pref_missing = True
        if not pts_path.exists():
            missing_lines.append(f"  {PREFECTURES[p]}（{p}）points_{p}.csv がありません")
            pref_missing = True
        if pref_missing:
            missing_prefs.append(p)

    if missing_lines:
        for line in missing_lines:
            print(line)
        missing_arg = ",".join(missing_prefs)
        print(f'先に実行してください：python src/run_batch.py --pref "{missing_arg}"')
        sys.exit(1)

    pref_counts = {}
    total_mon = 0
    total_pts = 0
    for p in pref_codes:
        n_mon = count_csv_rows(proc_dir / f"monuments_{p}.csv")
        n_pts = count_csv_rows(proc_dir / f"points_{p}.csv")
        pref_counts[p] = (n_mon, n_pts)
        total_mon += n_mon
        total_pts += n_pts

    print(
        f"地域版の一括実行の対象: {len(pref_codes)}都道府県（碑 {total_mon:,}基・比較地点 {total_pts:,}点）",
        flush=True,
    )
    print("データの確認: そろっています", flush=True)

    if parsed.check_only:
        print("データの確認だけ行いました（--check-only）", flush=True)
        sys.exit(0)

    script_path = str(project_root / "src" / "add_landform_region.py")
    total_prefs = len(pref_codes)
    results_summary = []

    for idx, p in enumerate(pref_codes, 1):
        n_mon, n_pts = pref_counts[p]
        pref_name = PREFECTURES[p]
        start_time = now()
        print(
            f"[{idx}/{total_prefs}] {pref_name}（{p}）碑 {n_mon}基・比較地点 {n_pts}点 開始 {start_time.strftime('%Y-%m-%d %H:%M')}",
            flush=True,
        )

        before_13 = count_zoom_cache_files(13, project_root)
        before_8 = count_zoom_cache_files(8, project_root)

        cmd_mon = [sys.executable, script_path, "--pref", p]
        cmd_pts = [sys.executable, script_path, "--pref", p, "--target", "points"]

        result_status = "完了"
        try:
            res_mon = runner(cmd_mon)
            if res_mon.returncode != 0:
                result_status = "失敗"
            else:
                res_pts = runner(cmd_pts)
                if res_pts.returncode != 0:
                    result_status = "失敗"
        except KeyboardInterrupt:
            result_status = "中断"

        end_time = now()
        duration_sec = (end_time - start_time).total_seconds()

        after_13 = count_zoom_cache_files(13, project_root)
        after_8 = count_zoom_cache_files(8, project_root)
        calls_13 = max(0, after_13 - before_13)
        calls_8 = max(0, after_8 - before_8)

        if result_status == "中断":
            append_region_log(
                start_time,
                end_time,
                p,
                n_mon,
                n_pts,
                result_status,
                duration_sec,
                calls_13,
                calls_8,
                None,
                project_root,
            )
            print(
                "中断しました。もう一度同じコマンドを実行すると、取得済みのタイルはキャッシュから読むので短時間で続きまで進みます"
            )
            sys.exit(1)

        counts = None
        row_mismatch = False
        if result_status != "失敗":
            counts, row_mismatch = inspect_region_outputs(p, n_mon, n_pts, project_root)
            if row_mismatch or counts["取得不可"] >= 1:
                result_status = "要再実行"
            else:
                result_status = "完了"

        append_region_log(
            start_time,
            end_time,
            p,
            n_mon,
            n_pts,
            result_status,
            duration_sec,
            calls_13,
            calls_8,
            counts,
            project_root,
        )

        dur_str = format_duration(duration_sec)
        if result_status == "完了":
            c_reg = counts["取得済（地域版）"]
            c_wide = counts["取得済（広域版）"]
            c_no = counts["データなし"]
            c_err = counts["取得不可"]
            print(
                f"[{idx}/{total_prefs}] {pref_name}（{p}）完了　所要時間 {dur_str}　"
                f"地域版 {c_reg:,}・広域版 {c_wide:,}・データなし {c_no:,}・取得不可 {c_err:,}（碑＋比較地点）　"
                f"タイル：地域版 {calls_13:,}枚・広域版 {calls_8:,}枚",
                flush=True,
            )
        elif result_status == "要再実行":
            c_err = counts["取得不可"]
            mismatch_str = "あり" if row_mismatch else "なし"
            print(
                f"[{idx}/{total_prefs}] {pref_name}（{p}）要再実行（取得不可 {c_err:,}件・行数の不一致 {mismatch_str}）　"
                f"所要時間 {dur_str}　タイル：地域版 {calls_13:,}枚・広域版 {calls_8:,}枚",
                flush=True,
            )
        elif result_status == "失敗":
            print(
                f"[{idx}/{total_prefs}] {pref_name}（{p}）失敗（上の表示で原因を確かめてください）　"
                f"所要時間 {dur_str}　タイル：地域版 {calls_13:,}枚・広域版 {calls_8:,}枚",
                flush=True,
            )

        results_summary.append(
            {
                "code": p,
                "status": result_status,
                "counts": counts,
                "calls_13": calls_13,
                "calls_8": calls_8,
            }
        )

    print("地域版の一括実行のまとめ（output/region_batch_log.csv に記録しました）")
    count_done = 0
    count_retry = 0
    count_fail = 0

    sum_reg = 0
    sum_wide = 0
    sum_no = 0
    sum_err = 0
    sum_tiles_13 = 0
    sum_tiles_8 = 0

    for r in results_summary:
        p = r["code"]
        pref_name = PREFECTURES[p]
        st = r["status"]
        if st in ("完了", "要再実行"):
            c = r["counts"]
            print(
                f"  {pref_name}（{p}）{st}　"
                f"地域版 {c['取得済（地域版）']:,}・広域版 {c['取得済（広域版）']:,}・"
                f"データなし {c['データなし']:,}・取得不可 {c['取得不可']:,}"
            )
            sum_reg += c["取得済（地域版）"]
            sum_wide += c["取得済（広域版）"]
            sum_no += c["データなし"]
            sum_err += c["取得不可"]
            sum_tiles_13 += r["calls_13"]
            sum_tiles_8 += r["calls_8"]
            if st == "完了":
                count_done += 1
            else:
                count_retry += 1
        else:
            print(f"  {pref_name}（{p}）失敗")
            count_fail += 1

    print(f"完了 {count_done}県／要再実行 {count_retry}県／失敗 {count_fail}県")
    print(
        f"合計（完了と要再実行の県）：地域版 {sum_reg:,}・広域版 {sum_wide:,}・データなし {sum_no:,}・取得不可 {sum_err:,}　"
        f"タイル：地域版 {sum_tiles_13:,}枚・広域版 {sum_tiles_8:,}枚"
    )

    if count_retry == 0 and count_fail == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
