# -*- coding: utf-8 -*-
import argparse
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import pandas as pd

try:
    from src.prefectures import PREFECTURES
    import src.load_monuments as lm
    import src.update as update
except ImportError:
    from prefectures import PREFECTURES
    import load_monuments as lm
    import update

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def to_rel_path(path, root):
    """root からの相対パス（スラッシュ区切り）を返す"""
    if not path:
        return ""
    try:
        p = Path(path).resolve()
        r = Path(root).resolve()
        try:
            rel = p.relative_to(r)
            return rel.as_posix()
        except ValueError:
            return p.as_posix()
    except Exception:
        return str(path).replace("\\", "/")


def default_now():
    """現在時刻を返す"""
    return datetime.now()


def default_runner(cmd, cwd=None):
    """外部コマンドを実行する既定のランナー"""
    return subprocess.run(cmd, cwd=cwd)


def load_and_cache_csv(csv_path, cache_dict):
    """CSV を読み込み、県コード列を付与してキャッシュする"""
    csv_str = str(csv_path)
    if csv_str in cache_dict:
        return cache_dict[csv_str]
    try:
        df = lm.load_csv(csv_str)
        lm.validate_dataframe(df)
        if "県コード" not in df.columns:
            df["県コード"] = df["ID"].str[:2]
        cache_dict[csv_str] = df
        return df
    except Exception:
        return None


def judge_prefectures(root, latest_csv_rel, df_latest):
    """
    47都道府県の更新要否を判定する。
    戻り値: (latest_prefs, no_change_prefs, rebuild_prefs)
    """
    cached_old_dfs = {}
    latest_prefs = []
    no_change_prefs = []
    rebuild_prefs = []

    for p in sorted(PREFECTURES.keys()):
        hist_path = root / "output" / f"update_history_{p}.csv"
        if not hist_path.exists():
            rebuild_prefs.append({"pref_code": p, "reason": "更新の記録がありません"})
            continue

        try:
            df_hist = pd.read_csv(hist_path, encoding="utf-8-sig", dtype=str)
        except Exception:
            rebuild_prefs.append({"pref_code": p, "reason": "更新の記録がありません"})
            continue

        df_hist = df_hist.dropna(how="all")
        if df_hist.empty:
            rebuild_prefs.append({"pref_code": p, "reason": "更新の記録がありません"})
            continue

        last_row = df_hist.iloc[-1]
        last_result = str(last_row.get("結果", "")).strip()

        if last_result != "完了":
            rebuild_prefs.append({
                "pref_code": p,
                "reason": f"前回が完了していません（{last_result}）"
            })
            continue

        prev_new_file = str(last_row.get("新データのファイル", "")).strip()
        if prev_new_file == latest_csv_rel:
            latest_prefs.append(p)
            continue

        old_csv_path = root / prev_new_file
        if not old_csv_path.exists():
            rebuild_prefs.append({
                "pref_code": p,
                "reason": "前回のデータが見つかりません"
            })
            continue

        df_old = load_and_cache_csv(old_csv_path, cached_old_dfs)
        if df_old is None:
            rebuild_prefs.append({
                "pref_code": p,
                "reason": "前回のデータが見つかりません"
            })
            continue

        df_old_pref = lm.filter_by_prefecture(df_old, p)
        df_new_pref = lm.filter_by_prefecture(df_latest, p)
        df_diff = update.compare_dataframes(df_old_pref, df_new_pref)

        if len(df_diff) == 0:
            no_change_prefs.append({
                "pref_code": p,
                "prev_new_date": str(last_row.get("新データ取得日", "")).strip(),
                "prev_new_file": prev_new_file,
                "prev_new_count": str(last_row.get("新基数", "")).strip(),
                "current_count": len(df_new_pref),
            })
        else:
            add_c = len(df_diff[df_diff["区分"] == "追加"])
            mod_c = len(df_diff[df_diff["区分"] == "変更"])
            loc_c = len(df_diff[(df_diff["区分"] == "変更") & (df_diff["位置の変更"] == "あり")])
            del_c = len(df_diff[df_diff["区分"] == "削除"])
            reason = f"追加 {add_c}・変更 {mod_c}（うち位置 {loc_c}）・削除 {del_c}"
            rebuild_prefs.append({
                "pref_code": p,
                "reason": reason
            })

    return latest_prefs, no_change_prefs, rebuild_prefs


def check_national_rebuild(root, rebuild_prefs, latest_csv_rel):
    """
    全国の作り直しが必要か判定する。
    戻り値: (needed, reason)
    """
    if len(rebuild_prefs) > 0:
        return True, "県を作り直すため"

    hist_all_path = root / "output" / "update_history_all.csv"
    if not hist_all_path.exists():
        return True, "全国の作り直しの記録がないため"

    try:
        df_all = pd.read_csv(hist_all_path, encoding="utf-8-sig", dtype=str)
        df_all = df_all.dropna(how="all")
        if df_all.empty:
            return True, "全国の作り直しの記録がないため"
        last_row = df_all.iloc[-1]
        last_result = str(last_row.get("結果", "")).strip()
        if last_result != "完了":
            return True, "前回の全国の作り直しが完了していないため"
        last_new_file = str(last_row.get("新データのファイル", "")).strip()
        if last_new_file != latest_csv_rel:
            return True, "新しい伝承碑データに切り替えたため"
        return False, ""
    except Exception:
        return True, "全国の作り直しの記録がないため"


def get_prefs_for_site_build(rebuild_pref_codes, update_history_all_path):
    """
    県別ページを作る県の一覧（県コード順）を返す。
    今回の作り直す県 ∪ update_history_all.csv の最後の「完了」より後にある行の「作り直した県」
    """
    target_prefs = set(rebuild_pref_codes)
    if update_history_all_path.exists():
        try:
            df_hist = pd.read_csv(update_history_all_path, encoding="utf-8-sig", dtype=str)
            df_hist = df_hist.dropna(how="all").reset_index(drop=True)
            if not df_hist.empty:
                completed_indices = df_hist.index[df_hist["結果"] == "完了"].tolist()
                if completed_indices:
                    last_completed_idx = completed_indices[-1]
                    target_rows = df_hist.iloc[last_completed_idx + 1:]
                else:
                    target_rows = df_hist

                for _, row in target_rows.iterrows():
                    rebuilt_val = str(row.get("作り直した県", "")).strip()
                    if rebuilt_val and rebuilt_val != "なし":
                        codes = [c.strip() for c in rebuilt_val.split(",") if c.strip()]
                        for c in codes:
                            if c in PREFECTURES:
                                target_prefs.add(c)
        except Exception:
            pass
    return sorted(list(target_prefs))


def get_rebuilt_completed_prefs(rebuild_pref_codes, root, latest_csv_rel):
    """
    今回の作り直す県のうち、終わった時点で update_history_XX.csv の最後の行が「完了」かつ
    新データのファイル＝最新の県のコード（カンマ区切り、なければ「なし」）を返す。
    """
    completed_rebuilt = []
    for p in rebuild_pref_codes:
        hist_file = root / "output" / f"update_history_{p}.csv"
        if hist_file.exists():
            try:
                df = pd.read_csv(hist_file, encoding="utf-8-sig", dtype=str)
                df = df.dropna(how="all")
                if not df.empty:
                    last_row = df.iloc[-1]
                    if (
                        str(last_row.get("結果", "")).strip() == "完了"
                        and str(last_row.get("新データのファイル", "")).strip() == latest_csv_rel
                    ):
                        completed_rebuilt.append(p)
            except Exception:
                pass
    if completed_rebuilt:
        return ",".join(completed_rebuilt)
    return "なし"


def record_no_change_prefs(no_change_prefs, root, now_dt, latest_fetch_date, latest_csv_rel):
    """「変更なし」の県それぞれの update_history_XX.csv に完了行を足す"""
    now_str = now_dt.strftime("%Y-%m-%d %H:%M")
    for info in no_change_prefs:
        p = info["pref_code"]
        hist_file = root / "output" / f"update_history_{p}.csv"
        record = {
            "実行日時": now_str,
            "県コード": p,
            "旧データ取得日": info["prev_new_date"],
            "新データ取得日": latest_fetch_date,
            "旧データのファイル": info["prev_new_file"],
            "新データのファイル": latest_csv_rel,
            "旧基数": info["prev_new_count"],
            "新基数": info["current_count"],
            "追加": 0,
            "変更": 0,
            "うち位置の変更": 0,
            "削除": 0,
            "結果": "完了",
        }
        df_row = pd.DataFrame([record])
        if not hist_file.exists():
            hist_file.parent.mkdir(parents=True, exist_ok=True)
            df_row.to_csv(hist_file, index=False, encoding="utf-8-sig")
        else:
            df_row.to_csv(hist_file, index=False, encoding="utf-8-sig", mode="a", header=False)


def save_update_history_all(root, now_dt, fetch_date, latest_csv_rel, rebuilt_prefs_str, no_change_count, result):
    """output/update_history_all.csv に1行書き込む"""
    history_file = root / "output" / "update_history_all.csv"
    record = {
        "実行日時": now_dt.strftime("%Y-%m-%d %H:%M"),
        "新データ取得日": fetch_date,
        "新データのファイル": latest_csv_rel,
        "作り直した県": rebuilt_prefs_str,
        "変更なしの県数": no_change_count,
        "結果": result,
    }
    df_row = pd.DataFrame([record])
    if not history_file.exists():
        history_file.parent.mkdir(parents=True, exist_ok=True)
        df_row.to_csv(history_file, index=False, encoding="utf-8-sig")
    else:
        df_row.to_csv(history_file, index=False, encoding="utf-8-sig", mode="a", header=False)


def main(args=None, runner=None, root=None, now=None):
    if root is None:
        root = PROJECT_ROOT
    else:
        root = Path(root)

    if now is None:
        now = default_now

    if runner is None:
        runner = lambda cmd: default_runner(cmd, cwd=root)

    parser = argparse.ArgumentParser(description="自然災害伝承碑の全国更新コマンド")
    parser.add_argument("--dry-run", action="store_true", help="確認だけ行い、ファイルを書き込まない")
    parsed = parser.parse_args(args)
    dry_run = parsed.dry_run

    # 最新の伝承碑データを取得
    try:
        latest_csv = lm.get_latest_raw_csv(base_dir=root / "data" / "raw")
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

    latest_fetch_date = lm.get_fetch_date(latest_csv)
    latest_csv_rel = to_rel_path(latest_csv, root)

    try:
        df_latest = lm.load_csv(latest_csv)
        lm.validate_dataframe(df_latest)
        if "県コード" not in df_latest.columns:
            df_latest["県コード"] = df_latest["ID"].str[:2]
    except Exception as e:
        print(f"エラー: 最新伝承碑データの読み込みに失敗しました: {e}")
        sys.exit(1)

    total_monuments = len(df_latest)

    # 1. 県ごとの判定
    latest_prefs, no_change_prefs, rebuild_prefs = judge_prefectures(
        root=root,
        latest_csv_rel=latest_csv_rel,
        df_latest=df_latest
    )

    # 2. 全国の作り直しが必要か
    national_needed, national_reason = check_national_rebuild(
        root=root,
        rebuild_prefs=rebuild_prefs,
        latest_csv_rel=latest_csv_rel
    )

    # 3. 表示
    print(
        f"全国の更新：使う伝承碑データ {latest_csv_rel}（取得日 {latest_fetch_date}、"
        f"{total_monuments:,}基・{len(PREFECTURES)}都道府県）"
    )
    print("県ごとの判定：")
    print(f"  最新で作成済み：{len(latest_prefs)}県")

    print(f"  変更なし（作り直しません）：{len(no_change_prefs)}県")
    if no_change_prefs:
        no_change_strs = [f"{PREFECTURES[info['pref_code']]}（{info['pref_code']}）" for info in no_change_prefs]
        print(f"    {'、'.join(no_change_strs)}")

    print(f"  作り直す：{len(rebuild_prefs)}県")
    if rebuild_prefs:
        for item in rebuild_prefs:
            p = item["pref_code"]
            r = item["reason"]
            print(f"    {PREFECTURES[p]}（{p}）{r}")

    if national_needed:
        print(f"全国のページ：作り直します（{national_reason}）")
    else:
        print("全国のページ：作り直しは不要です")

    # dry-run または更新不要時の終了判定
    if dry_run:
        print("確認だけ行いました（--dry-run）。何も書き込んでいません")
        sys.exit(0)

    if len(rebuild_prefs) == 0 and not national_needed:
        print("すべて最新です。作り直すものはありません")
        sys.exit(0)

    # 4. 実行
    now_dt = now()

    # 「変更なし」の県それぞれの update_history_XX.csv に完了行を足す
    record_no_change_prefs(
        no_change_prefs=no_change_prefs,
        root=root,
        now_dt=now_dt,
        latest_fetch_date=latest_fetch_date,
        latest_csv_rel=latest_csv_rel
    )

    # ステップの組み立て
    rebuild_codes = [item["pref_code"] for item in rebuild_prefs]
    site_build_codes = get_prefs_for_site_build(
        rebuild_pref_codes=rebuild_codes,
        update_history_all_path=root / "output" / "update_history_all.csv"
    )

    steps = []
    if rebuild_codes:
        steps.append((
            f"県の作り直し（{len(rebuild_codes)}県）",
            [sys.executable, str(root / "src" / "run_batch.py"), "--pref", ",".join(rebuild_codes), "--force"]
        ))

    steps.append((
        "全国集計",
        [sys.executable, str(root / "src" / "summarize_national.py")]
    ))
    steps.append((
        "地形分類（地域版）の全国集計",
        [sys.executable, str(root / "src" / "summarize_region.py")]
    ))
    steps.append((
        "地形分類（人工地形）の全国集計",
        [sys.executable, str(root / "src" / "summarize_artificial.py")]
    ))

    for p in site_build_codes:
        steps.append((
            f"県別ページの作成（{PREFECTURES[p]}）",
            [sys.executable, str(root / "src" / "build_site.py"), "--pref", p]
        ))

    steps.append((
        "印刷用PDF",
        [sys.executable, str(root / "src" / "make_national_pdf.py")]
    ))

    steps.append((
        "全国ページ",
        [sys.executable, str(root / "src" / "build_national.py")]
    ))

    steps.append((
        "取得不可の件数",
        [sys.executable, str(root / "src" / "count_missing.py")]
    ))

    total_steps = len(steps)
    for idx, (stage_name, cmd) in enumerate(steps, 1):
        step_tag = f"[{idx}/{total_steps}] {stage_name}"
        print(step_tag, flush=True)
        try:
            res = runner(cmd)
            retcode = getattr(res, "returncode", 0)
            if retcode != 0:
                print(
                    f"{step_tag} で失敗しました。原因を直してから、もう一度 python src/update_all.py を実行してください"
                    "（作り直しが済んだ県は飛ばします）",
                    flush=True
                )
                rebuilt_str = get_rebuilt_completed_prefs(rebuild_codes, root, latest_csv_rel)
                save_update_history_all(
                    root=root,
                    now_dt=now(),
                    fetch_date=latest_fetch_date,
                    latest_csv_rel=latest_csv_rel,
                    rebuilt_prefs_str=rebuilt_str,
                    no_change_count=len(no_change_prefs),
                    result=f"失敗（{step_tag}）"
                )
                sys.exit(1)
        except KeyboardInterrupt:
            print(
                "中断しました。もう一度 python src/update_all.py を実行すると続きから始まります",
                flush=True
            )
            rebuilt_str = get_rebuilt_completed_prefs(rebuild_codes, root, latest_csv_rel)
            save_update_history_all(
                root=root,
                now_dt=now(),
                fetch_date=latest_fetch_date,
                latest_csv_rel=latest_csv_rel,
                rebuilt_prefs_str=rebuilt_str,
                no_change_count=len(no_change_prefs),
                result=f"中断（{step_tag}）"
            )
            sys.exit(1)

    # すべて完了
    rebuilt_str = get_rebuilt_completed_prefs(rebuild_codes, root, latest_csv_rel)
    completed_rebuilt_count = 0 if rebuilt_str == "なし" else len(rebuilt_str.split(","))
    save_update_history_all(
        root=root,
        now_dt=now(),
        fetch_date=latest_fetch_date,
        latest_csv_rel=latest_csv_rel,
        rebuilt_prefs_str=rebuilt_str,
        no_change_count=len(no_change_prefs),
        result="完了"
    )
    print(
        f"全国の更新：完了（作り直した県 {completed_rebuilt_count}県・変更なし {len(no_change_prefs)}県。"
        "output/update_history_all.csv に記録しました）",
        flush=True
    )
    sys.exit(0)


if __name__ == "__main__":
    main()

