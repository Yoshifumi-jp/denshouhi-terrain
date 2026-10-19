"""地形分類（人工地形）だけを複数県で一括実行するプログラム。

指定した都道府県について src/add_landform_artificial.py を碑・比較地点の順に呼び出し、
結果の件数とタイルの取得枚数を集計して output/artificial_batch_log.csv に記録する。
長時間の実行前に Windows のスリープを「なし」にすること。
途中で止めても、同じコマンドをもう一度実行すれば取得済みのタイルはキャッシュから読む
（分けて実行するときは --pref で県を区切ってよい）。
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
    from src.run_region_batch import count_csv_rows
except ImportError:
    from prefectures import PREFECTURES
    import load_monuments as lm
    import update
    from run_batch import format_duration
    from run_region_batch import count_csv_rows

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
    "タイルの取得",
    "碑_取得済",
    "碑_人工地形なし",
    "碑_範囲外",
    "碑_取得不可",
    "比較地点_取得済",
    "比較地点_人工地形なし",
    "比較地点_範囲外",
    "比較地点_取得不可",
]

STATUS_KEYS = ("取得済", "人工地形なし", "範囲外", "取得不可")


def default_now():
    """現在日時を返す既定の関数"""
    return datetime.datetime.now()


def count_artificial_cache_files(project_root):
    """data/cache/artificial/16 の下のファイル数を数える"""
    cache_dir = project_root / "data" / "cache" / "artificial" / "16"
    if not cache_dir.exists():
        return 0
    return sum(1 for f in cache_dir.rglob("*") if f.is_file())


def _count_single_output(path, expected_rows):
    """1つの人工地形CSVを読み、状態別の件数と行数不一致の有無を返す"""
    counts = {k: 0 for k in STATUS_KEYS}
    if not path.exists():
        return counts, True
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    mismatch = len(rows) != expected_rows
    for row in rows:
        st = row.get("人工地形_状態", "")
        if st in counts:
            counts[st] += 1
    return counts, mismatch


def inspect_artificial_outputs(pref_code, expected_mon, expected_pts, project_root):
    """出力された人工地形CSV（碑・比較地点）を読み、それぞれの状態別件数と行数不一致の有無を返す"""
    proc_dir = project_root / "data" / "processed"
    mon_out = proc_dir / f"landform_artificial_{pref_code}.csv"
    pts_out = proc_dir / f"landform_artificial_points_{pref_code}.csv"

    mon_counts, mon_mismatch = _count_single_output(mon_out, expected_mon)
    pts_counts, pts_mismatch = _count_single_output(pts_out, expected_pts)
    row_mismatch = mon_mismatch or pts_mismatch

    return mon_counts, pts_counts, row_mismatch


def append_artificial_log(
    start_time,
    end_time,
    pref_code,
    n_mon,
    n_pts,
    result_status,
    duration_sec,
    tiles_fetched,
    mon_counts,
    pts_counts,
    project_root,
):
    """output/artificial_batch_log.csv に1行追記する（UTF-8 BOM付き、改行LF）"""
    log_file = project_root / "output" / "artificial_batch_log.csv"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    has_counts = (
        mon_counts is not None
        and pts_counts is not None
        and result_status in ("完了", "要再実行")
    )
    row = {
        "実行開始": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "実行終了": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "県コード": pref_code,
        "県名": PREFECTURES[pref_code],
        "碑_数": n_mon,
        "比較地点_数": n_pts,
        "結果": result_status,
        "所要時間_秒": int(round(duration_sec)),
        "タイルの取得": tiles_fetched,
        "碑_取得済": mon_counts["取得済"] if has_counts else "",
        "碑_人工地形なし": mon_counts["人工地形なし"] if has_counts else "",
        "碑_範囲外": mon_counts["範囲外"] if has_counts else "",
        "碑_取得不可": mon_counts["取得不可"] if has_counts else "",
        "比較地点_取得済": pts_counts["取得済"] if has_counts else "",
        "比較地点_人工地形なし": pts_counts["人工地形なし"] if has_counts else "",
        "比較地点_範囲外": pts_counts["範囲外"] if has_counts else "",
        "比較地点_取得不可": pts_counts["取得不可"] if has_counts else "",
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
    """人工地形の一括実行のメイン処理"""
    project_root = Path(root) if root else PROJECT_ROOT
    if now is None:
        now = default_now
    if runner is None:
        runner = update.default_runner

    parser = argparse.ArgumentParser(description="地形分類（人工地形）の複数県一括処理")
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
        required_files = [
            f"monuments_{p}.csv",
            f"points_{p}.csv",
            f"landform_{p}.csv",
            f"landform_points_{p}.csv",
        ]
        pref_missing = False
        for fname in required_files:
            if not (proc_dir / fname).exists():
                missing_lines.append(f"  {PREFECTURES[p]}（{p}）{fname} がありません")
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
        f"人工地形の一括実行の対象: {len(pref_codes)}都道府県（碑 {total_mon:,}基・比較地点 {total_pts:,}点）",
        flush=True,
    )
    print("データの確認: そろっています", flush=True)

    if parsed.check_only:
        print("データの確認だけ行いました（--check-only）", flush=True)
        sys.exit(0)

    script_path = str(project_root / "src" / "add_landform_artificial.py")
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

        before_16 = count_artificial_cache_files(project_root)

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

        after_16 = count_artificial_cache_files(project_root)
        tiles_fetched = max(0, after_16 - before_16)

        if result_status == "中断":
            append_artificial_log(
                start_time,
                end_time,
                p,
                n_mon,
                n_pts,
                result_status,
                duration_sec,
                tiles_fetched,
                None,
                None,
                project_root,
            )
            print(
                "中断しました。もう一度同じコマンドを実行すると、取得済みのタイルはキャッシュから読むので短時間で続きまで進みます"
            )
            sys.exit(1)

        mon_counts = None
        pts_counts = None
        row_mismatch = False
        if result_status != "失敗":
            mon_counts, pts_counts, row_mismatch = inspect_artificial_outputs(
                p, n_mon, n_pts, project_root
            )
            err_total = mon_counts["取得不可"] + pts_counts["取得不可"]
            if row_mismatch or err_total >= 1:
                result_status = "要再実行"
            else:
                result_status = "完了"

        append_artificial_log(
            start_time,
            end_time,
            p,
            n_mon,
            n_pts,
            result_status,
            duration_sec,
            tiles_fetched,
            mon_counts,
            pts_counts,
            project_root,
        )

        dur_str = format_duration(duration_sec)
        if result_status == "完了":
            print(
                f"[{idx}/{total_prefs}] {pref_name}（{p}）完了　所要時間 {dur_str}　"
                f"碑 取得済 {mon_counts['取得済']:,}・人工地形なし {mon_counts['人工地形なし']:,}・"
                f"範囲外 {mon_counts['範囲外']:,}・取得不可 {mon_counts['取得不可']:,}／"
                f"比較地点 取得済 {pts_counts['取得済']:,}・人工地形なし {pts_counts['人工地形なし']:,}・"
                f"範囲外 {pts_counts['範囲外']:,}・取得不可 {pts_counts['取得不可']:,}　"
                f"タイル {tiles_fetched:,}枚",
                flush=True,
            )
        elif result_status == "要再実行":
            c_err = mon_counts["取得不可"] + pts_counts["取得不可"]
            mismatch_str = "あり" if row_mismatch else "なし"
            print(
                f"[{idx}/{total_prefs}] {pref_name}（{p}）要再実行（取得不可 {c_err:,}件・行数の不一致 {mismatch_str}）　"
                f"所要時間 {dur_str}　タイル {tiles_fetched:,}枚",
                flush=True,
            )
        elif result_status == "失敗":
            print(
                f"[{idx}/{total_prefs}] {pref_name}（{p}）失敗（上の表示で原因を確かめてください）　"
                f"所要時間 {dur_str}　タイル {tiles_fetched:,}枚",
                flush=True,
            )

        results_summary.append(
            {
                "code": p,
                "status": result_status,
                "mon_counts": mon_counts,
                "pts_counts": pts_counts,
                "tiles": tiles_fetched,
            }
        )

    print("人工地形の一括実行のまとめ（output/artificial_batch_log.csv に記録しました）")
    count_done = 0
    count_retry = 0
    count_fail = 0

    sum_mon = {k: 0 for k in STATUS_KEYS}
    sum_pts = {k: 0 for k in STATUS_KEYS}
    sum_tiles = 0

    for r in results_summary:
        p = r["code"]
        pref_name = PREFECTURES[p]
        st = r["status"]
        if st in ("完了", "要再実行"):
            mc = r["mon_counts"]
            pc = r["pts_counts"]
            print(
                f"  {pref_name}（{p}）{st}　"
                f"碑 取得済 {mc['取得済']:,}・人工地形なし {mc['人工地形なし']:,}・"
                f"範囲外 {mc['範囲外']:,}・取得不可 {mc['取得不可']:,}／"
                f"比較地点 取得済 {pc['取得済']:,}・人工地形なし {pc['人工地形なし']:,}・"
                f"範囲外 {pc['範囲外']:,}・取得不可 {pc['取得不可']:,}"
            )
            for k in STATUS_KEYS:
                sum_mon[k] += mc[k]
                sum_pts[k] += pc[k]
            sum_tiles += r["tiles"]
            if st == "完了":
                count_done += 1
            else:
                count_retry += 1
        else:
            print(f"  {pref_name}（{p}）失敗")
            count_fail += 1

    print(f"完了 {count_done}県／要再実行 {count_retry}県／失敗 {count_fail}県")
    print(
        f"合計（完了と要再実行の県）："
        f"碑 取得済 {sum_mon['取得済']:,}・人工地形なし {sum_mon['人工地形なし']:,}・"
        f"範囲外 {sum_mon['範囲外']:,}・取得不可 {sum_mon['取得不可']:,}／"
        f"比較地点 取得済 {sum_pts['取得済']:,}・人工地形なし {sum_pts['人工地形なし']:,}・"
        f"範囲外 {sum_pts['範囲外']:,}・取得不可 {sum_pts['取得不可']:,}　"
        f"タイル {sum_tiles:,}枚"
    )

    if count_retry == 0 and count_fail == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

