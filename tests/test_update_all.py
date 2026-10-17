# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path
import pytest
import pandas as pd

from src.prefectures import PREFECTURES
from src.update_all import main, PROJECT_ROOT, get_prefs_for_site_build


def create_dummy_raw_csv(target_path, records):
    """ダミーの伝承碑 CSV を作成する"""
    columns = [
        "ID", "碑名", "建立年", "所在地", "災害名", "災害種別",
        "伝承内容", "緯度", "経度", "公開日", "修正等公開日", "制限事項"
    ]
    df = pd.DataFrame(records, columns=columns)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target_path, index=False, encoding="utf-8-sig")


def setup_base_mock_project(tmp_path, date="2026-09-24", extra_records=None):
    """
    47都道府県すべてについて1基ずつ（および追加レコード）を持つ偽プロジェクトを作成する。
    また、各県の update_history_XX.csv をこの日付で「完了」状態で作成する。
    """
    raw_dir = tmp_path / "data" / "raw" / date
    csv_name = f"denshouhi_{date.replace('-', '')}.csv"
    raw_csv = raw_dir / csv_name

    records = []
    for p in sorted(PREFECTURES.keys()):
        pref_name = PREFECTURES[p]
        records.append([
            f"{p}001-001", f"{pref_name}碑1", "1900", f"{pref_name}某所",
            "地震", "地震", "伝承内容", "35.0", "135.0", "2020-01-01", "2020-01-01", "なし"
        ])
    if extra_records:
        records.extend(extra_records)

    create_dummy_raw_csv(raw_csv, records)

    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    rel_raw_path = f"data/raw/{date}/{csv_name}"
    for p in sorted(PREFECTURES.keys()):
        hist_file = out_dir / f"update_history_{p}.csv"
        df_hist = pd.DataFrame([{
            "実行日時": f"{date} 10:00",
            "県コード": p,
            "旧データ取得日": "なし",
            "新データ取得日": date,
            "旧データのファイル": "",
            "新データのファイル": rel_raw_path,
            "旧基数": "0",
            "新基数": "1",
            "追加": "1",
            "変更": "0",
            "うち位置の変更": "0",
            "削除": "0",
            "結果": "完了",
        }])
        df_hist.to_csv(hist_file, index=False, encoding="utf-8-sig")

    return rel_raw_path


class FakeRunner:
    """テスト用の擬似 runner"""
    def __init__(self, root, latest_rel_csv, latest_date, fail_targets=None):
        self.root = root
        self.latest_rel_csv = latest_rel_csv
        self.latest_date = latest_date
        self.fail_targets = fail_targets or {}
        self.calls = []

    def __call__(self, cmd):
        self.calls.append(cmd)
        cmd_str = " ".join(cmd)

        # 失敗条件チェック
        for target, retcode in self.fail_targets.items():
            if target in cmd_str:
                class FailResult:
                    returncode = retcode
                return FailResult()

        # run_batch.py の場合、対象県の update_history_XX.csv を「完了」に更新
        if any("run_batch.py" in arg for arg in cmd):
            pref_arg = ""
            for i, arg in enumerate(cmd):
                if arg == "--pref" and i + 1 < len(cmd):
                    pref_arg = cmd[i + 1]
                    break
            if pref_arg:
                prefs = [p.strip() for p in pref_arg.split(",") if p.strip()]
                for p in prefs:
                    hist_file = self.root / "output" / f"update_history_{p}.csv"
                    df_row = pd.DataFrame([{
                        "実行日時": f"{self.latest_date} 12:00",
                        "県コード": p,
                        "旧データ取得日": "2026-09-24",
                        "新データ取得日": self.latest_date,
                        "旧データのファイル": "data/raw/2026-09-24/denshouhi_20260924.csv",
                        "新データのファイル": self.latest_rel_csv,
                        "旧基数": "1",
                        "新基数": "2",
                        "追加": "1",
                        "変更": "0",
                        "うち位置の変更": "0",
                        "削除": "0",
                        "結果": "完了",
                    }])
                    if hist_file.exists():
                        df_row.to_csv(hist_file, index=False, encoding="utf-8-sig", mode="a", header=False)
                    else:
                        df_row.to_csv(hist_file, index=False, encoding="utf-8-sig")

        class SuccessResult:
            returncode = 0

        return SuccessResult()


def snapshot_directory(dir_path):
    """ディレクトリ内のファイル一覧とそのハッシュ値を取得する"""
    snapshot = {}
    for p in Path(dir_path).rglob("*"):
        if p.is_file():
            rel = p.relative_to(dir_path).as_posix()
            snapshot[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snapshot


def test_1_all_latest(tmp_path, capsys):
    """
    1. 47県すべて最新で作成済み＋update_history_all の最後が「完了・最新」
    → runner は呼ばれない、終了コード0、何も書かれない
    """
    rel_path = setup_base_mock_project(tmp_path, date="2026-09-24")

    # update_history_all.csv を作成（最新かつ完了）
    all_hist = tmp_path / "output" / "update_history_all.csv"
    df_all = pd.DataFrame([{
        "実行日時": "2026-09-24 10:30",
        "新データ取得日": "2026-09-24",
        "新データのファイル": rel_path,
        "作り直した県": "なし",
        "変更なしの県数": 0,
        "結果": "完了",
    }])
    df_all.to_csv(all_hist, index=False, encoding="utf-8-sig")

    snap_before = snapshot_directory(tmp_path)

    runner = FakeRunner(tmp_path, rel_path, "2026-09-24")
    with pytest.raises(SystemExit) as exc_info:
        main([], runner=runner, root=tmp_path)

    assert exc_info.value.code == 0
    assert len(runner.calls) == 0

    captured = capsys.readouterr()
    assert "すべて最新です。作り直すものはありません" in captured.out

    snap_after = snapshot_directory(tmp_path)
    assert snap_before == snap_after


def test_2_diff_one_pref(tmp_path, capsys):
    """
    2. 新しい日付フォルダを足し、1県（例：36）だけ1基追加・残り46県は同じ
    → 46県に「完了」の行が足される
    → runner の順が run_batch（--pref 36）→ summarize_national → build_site --pref 36
       → make_national_pdf → build_national → count_missing
    → update_history_all に「完了」・作り直した県 36・変更なしの県数 46
    """
    setup_base_mock_project(tmp_path, date="2026-09-24")

    # 2026-10-14 のデータを追加（36県だけ1基追加）
    extra = [
        ["36001-002", "徳島碑2", "1950", "徳島県某所", "津波", "津波", "内容2", "34.0", "134.0", "2026-10-14", "2026-10-14", "なし"]
    ]
    new_rel_path = "data/raw/2026-10-14/denshouhi_20261014.csv"
    raw_20261014 = tmp_path / "data" / "raw" / "2026-10-14" / "denshouhi_20261014.csv"

    records = []
    for p in sorted(PREFECTURES.keys()):
        pref_name = PREFECTURES[p]
        records.append([
            f"{p}001-001", f"{pref_name}碑1", "1900", f"{pref_name}某所",
            "地震", "地震", "伝承内容", "35.0", "135.0", "2020-01-01", "2020-01-01", "なし"
        ])
    records.extend(extra)
    create_dummy_raw_csv(raw_20261014, records)

    runner = FakeRunner(tmp_path, new_rel_path, "2026-10-14")
    with pytest.raises(SystemExit) as exc_info:
        main([], runner=runner, root=tmp_path)

    assert exc_info.value.code == 0

    # 46県に「完了」の行が足されているか確認（例：01北海道）
    df_hist_01 = pd.read_csv(tmp_path / "output" / "update_history_01.csv", encoding="utf-8-sig", dtype=str)
    assert len(df_hist_01) == 2
    last_01 = df_hist_01.iloc[-1]
    assert last_01["結果"] == "完了"
    assert last_01["新データのファイル"] == new_rel_path
    assert last_01["新データ取得日"] == "2026-10-14"

    # runner の呼び出し順序の検証
    called_scripts = []
    for call in runner.calls:
        # call のコマンドからスクリプト名と主要引数を抽出
        parts = [Path(c).name for c in call if str(c).endswith(".py")]
        script = parts[0] if parts else ""
        if "--pref" in call:
            pref_idx = call.index("--pref") + 1
            script += f" --pref {call[pref_idx]}"
        if "--force" in call:
            script += " --force"
        called_scripts.append(script)

    expected_scripts = [
        "run_batch.py --pref 36 --force",
        "summarize_national.py",
        "summarize_region.py",
        "build_site.py --pref 36",
        "make_national_pdf.py",
        "build_national.py",
        "count_missing.py",
    ]
    assert called_scripts == expected_scripts

    # update_history_all.csv の確認
    hist_all_path = tmp_path / "output" / "update_history_all.csv"
    assert hist_all_path.exists()
    df_all = pd.read_csv(hist_all_path, encoding="utf-8-sig", dtype=str)
    assert len(df_all) == 1
    row_all = df_all.iloc[-1]
    assert row_all["新データ取得日"] == "2026-10-14"
    assert row_all["新データのファイル"] == new_rel_path
    assert row_all["作り直した県"] == "36"
    assert row_all["変更なしの県数"] == "46"
    assert row_all["結果"] == "完了"


def test_3_pref_previous_not_completed(tmp_path, capsys):
    """
    3. 最後の行が「失敗（…）」の県は、差分0でも「作り直す」になり、
    理由に「前回が完了していません」が出る
    """
    setup_base_mock_project(tmp_path, date="2026-09-24")

    # 36県の最後の行を「失敗」にする
    hist_36 = tmp_path / "output" / "update_history_36.csv"
    df_36 = pd.read_csv(hist_36, encoding="utf-8-sig", dtype=str)
    df_36.at[len(df_36) - 1, "結果"] = "失敗（[1/6] 県の作り直し（1県））"
    df_36.to_csv(hist_36, index=False, encoding="utf-8-sig")

    runner = FakeRunner(tmp_path, "data/raw/2026-09-24/denshouhi_20260924.csv", "2026-09-24")
    with pytest.raises(SystemExit) as exc_info:
        main(["--dry-run"], runner=runner, root=tmp_path)

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "作り直す：1県" in captured.out
    assert "徳島県（36）前回が完了していません" in captured.out


def test_4_dry_run_no_files_written(tmp_path, capsys):
    """
    4. --dry-run：判定の表示は出るが、tmp_path のファイルが1つも増えない・変わらない
    （実行前後でファイル一覧と中身を比べる）
    """
    setup_base_mock_project(tmp_path, date="2026-09-24")

    # 2026-10-14 のデータを追加
    extra = [
        ["36001-002", "徳島碑2", "1950", "徳島県某所", "津波", "津波", "内容2", "34.0", "134.0", "2026-10-14", "2026-10-14", "なし"]
    ]
    new_rel_path = "data/raw/2026-10-14/denshouhi_20261014.csv"
    raw_20261014 = tmp_path / "data" / "raw" / "2026-10-14" / "denshouhi_20261014.csv"
    records = []
    for p in sorted(PREFECTURES.keys()):
        pref_name = PREFECTURES[p]
        records.append([
            f"{p}001-001", f"{pref_name}碑1", "1900", f"{pref_name}某所",
            "地震", "地震", "伝承内容", "35.0", "135.0", "2020-01-01", "2020-01-01", "なし"
        ])
    records.extend(extra)
    create_dummy_raw_csv(raw_20261014, records)

    snap_before = snapshot_directory(tmp_path)

    runner = FakeRunner(tmp_path, new_rel_path, "2026-10-14")
    with pytest.raises(SystemExit) as exc_info:
        main(["--dry-run"], runner=runner, root=tmp_path)

    assert exc_info.value.code == 0
    assert len(runner.calls) == 0

    captured = capsys.readouterr()
    assert "確認だけ行いました（--dry-run）。何も書き込んでいません" in captured.out

    snap_after = snapshot_directory(tmp_path)
    assert snap_before == snap_after


def test_5_run_batch_fails(tmp_path, capsys):
    """
    5. run_batch が returncode 1 → 以降の段階は呼ばれない、
    update_history_all に「失敗（[1/6] 県の作り直し（1県））」、終了コード1
    """
    setup_base_mock_project(tmp_path, date="2026-09-24")

    # 36県に1基追加
    extra = [
        ["36001-002", "徳島碑2", "1950", "徳島県某所", "津波", "津波", "内容2", "34.0", "134.0", "2026-10-14", "2026-10-14", "なし"]
    ]
    new_rel_path = "data/raw/2026-10-14/denshouhi_20261014.csv"
    raw_20261014 = tmp_path / "data" / "raw" / "2026-10-14" / "denshouhi_20261014.csv"
    records = []
    for p in sorted(PREFECTURES.keys()):
        pref_name = PREFECTURES[p]
        records.append([
            f"{p}001-001", f"{pref_name}碑1", "1900", f"{pref_name}某所",
            "地震", "地震", "伝承内容", "35.0", "135.0", "2020-01-01", "2020-01-01", "なし"
        ])
    records.extend(extra)
    create_dummy_raw_csv(raw_20261014, records)

    # run_batch.py が失敗するように設定
    runner = FakeRunner(tmp_path, new_rel_path, "2026-10-14", fail_targets={"run_batch.py": 1})

    with pytest.raises(SystemExit) as exc_info:
        main([], runner=runner, root=tmp_path)

    assert exc_info.value.code == 1
    assert len(runner.calls) == 1

    captured = capsys.readouterr()
    assert "[1/7] 県の作り直し（1県） で失敗しました" in captured.out

    hist_all_path = tmp_path / "output" / "update_history_all.csv"
    assert hist_all_path.exists()
    df_all = pd.read_csv(hist_all_path, encoding="utf-8-sig", dtype=str)
    assert len(df_all) == 1
    row_all = df_all.iloc[-1]
    assert row_all["結果"] == "失敗（[1/7] 県の作り直し（1県））"
    assert row_all["作り直した県"] == "なし"
    assert row_all["変更なしの県数"] == "46"


def test_6_retry_after_national_failure(tmp_path, capsys):
    """
    6. 全国の段階（例：build_national）が失敗した後の再実行：
    2回目は run_batch を呼ばず、build_site --pref 36 を含む全国の段階だけが呼ばれる
    （「県別ページを作る県」の注の確認）
    """
    setup_base_mock_project(tmp_path, date="2026-09-24")

    # 36県に1基追加
    extra = [
        ["36001-002", "徳島碑2", "1950", "徳島県某所", "津波", "津波", "内容2", "34.0", "134.0", "2026-10-14", "2026-10-14", "なし"]
    ]
    new_rel_path = "data/raw/2026-10-14/denshouhi_20261014.csv"
    raw_20261014 = tmp_path / "data" / "raw" / "2026-10-14" / "denshouhi_20261014.csv"
    records = []
    for p in sorted(PREFECTURES.keys()):
        pref_name = PREFECTURES[p]
        records.append([
            f"{p}001-001", f"{pref_name}碑1", "1900", f"{pref_name}某所",
            "地震", "地震", "伝承内容", "35.0", "135.0", "2020-01-01", "2020-01-01", "なし"
        ])
    records.extend(extra)
    create_dummy_raw_csv(raw_20261014, records)

    # 1回目：build_national.py で失敗
    runner1 = FakeRunner(tmp_path, new_rel_path, "2026-10-14", fail_targets={"build_national.py": 1})
    with pytest.raises(SystemExit) as exc_info1:
        main([], runner=runner1, root=tmp_path)
    assert exc_info1.value.code == 1

    # 1回目の完了後、36県は完了しており、update_history_all に「作り直した県: 36」が記録されている
    called_scripts_1 = []
    for call in runner1.calls:
        parts = [Path(c).name for c in call if str(c).endswith(".py")]
        script = parts[0] if parts else ""
        if "--pref" in call:
            pref_idx = call.index("--pref") + 1
            script += f" --pref {call[pref_idx]}"
        if "--force" in call:
            script += " --force"
        called_scripts_1.append(script)
    assert called_scripts_1[0] == "run_batch.py --pref 36 --force"

    df_all1 = pd.read_csv(tmp_path / "output" / "update_history_all.csv", encoding="utf-8-sig", dtype=str)
    assert df_all1.iloc[-1]["作り直した県"] == "36"
    assert "失敗（[6/7] 全国ページ）" in df_all1.iloc[-1]["結果"]

    # 2回目：失敗設定なしで再実行
    runner2 = FakeRunner(tmp_path, new_rel_path, "2026-10-14")
    with pytest.raises(SystemExit) as exc_info2:
        main([], runner=runner2, root=tmp_path)
    assert exc_info2.value.code == 0

    # 2回目の runner の呼び出し順序を確認
    called_scripts = []
    for call in runner2.calls:
        parts = [Path(c).name for c in call if str(c).endswith(".py")]
        script = parts[0] if parts else ""
        if "--pref" in call:
            pref_idx = call.index("--pref") + 1
            script += f" --pref {call[pref_idx]}"
        if "--force" in call:
            script += " --force"
        called_scripts.append(script)

    expected_scripts = [
        "summarize_national.py",
        "summarize_region.py",
        "build_site.py --pref 36",
        "make_national_pdf.py",
        "build_national.py",
        "count_missing.py",
    ]
    assert called_scripts == expected_scripts

    # update_history_all の最後の行が完了
    df_all2 = pd.read_csv(tmp_path / "output" / "update_history_all.csv", encoding="utf-8-sig", dtype=str)
    assert len(df_all2) == 2
    assert df_all2.iloc[-1]["結果"] == "完了"


def test_7_real_data_dry_run(capsys):
    """
    7. 実データ（root を指定せず、本物の output/update_history_XX.csv があるときだけ。
    ないときは skip）：
    `--dry-run` で「最新で作成済み：47県」「作り直す：0県」と表示され、本物のファイルが変わらない
    """
    for p in PREFECTURES.keys():
        hist_file = PROJECT_ROOT / "output" / f"update_history_{p}.csv"
        if not hist_file.exists():
            pytest.skip(f"実データ {hist_file.name} が存在しないためスキップします")

    # 本物のファイルが変わらないことを確認するため、git status などを想定
    with pytest.raises(SystemExit) as exc_info:
        main(["--dry-run"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "最新で作成済み：47県" in captured.out
    assert "変更なし（作り直しません）：0県" in captured.out
    assert "作り直す：0県" in captured.out
    assert "確認だけ行いました（--dry-run）。何も書き込んでいません" in captured.out


def test_8_rebuild_with_force_when_previous_failed(tmp_path, capsys):
    """
    8. 県36 の update_history_36.csv を「完了・最新のファイル」→
    「失敗（[9/14] ハザード区域の判定（碑））・最新のファイル」の2行にし、
    ほかの46県は「完了・最新」、update_history_all は「完了・最新」の状態で main([]) を呼ぶ。
    期待：
    - 表示に「徳島県（36）前回が完了していません（失敗（[9/14] ハザード区域の判定（碑）））」が出る
    - 最初の runner のコマンドが run_batch.py --pref 36 --force
    - 偽の runner が「完了」の行を足した後の update_history_all の最後の行が「完了」・作り直した県 36
    """
    latest_date = "2026-09-24"
    rel_path = setup_base_mock_project(tmp_path, date=latest_date)

    # 36県の update_history_36.csv に失敗行を追加して2行にする
    hist_36 = tmp_path / "output" / "update_history_36.csv"
    df_36_fail_row = pd.DataFrame([{
        "実行日時": f"{latest_date} 11:00",
        "県コード": "36",
        "旧データ取得日": "なし",
        "新データ取得日": latest_date,
        "旧データのファイル": "",
        "新データのファイル": rel_path,
        "旧基数": "0",
        "新基数": "1",
        "追加": "1",
        "変更": "0",
        "うち位置の変更": "0",
        "削除": "0",
        "結果": "失敗（[9/14] ハザード区域の判定（碑））",
    }])
    df_36_fail_row.to_csv(hist_36, index=False, encoding="utf-8-sig", mode="a", header=False)

    # update_history_all を「完了・最新」で作成
    all_hist = tmp_path / "output" / "update_history_all.csv"
    df_all = pd.DataFrame([{
        "実行日時": f"{latest_date} 10:30",
        "新データ取得日": latest_date,
        "新データのファイル": rel_path,
        "作り直した県": "なし",
        "変更なしの県数": 0,
        "結果": "完了",
    }])
    df_all.to_csv(all_hist, index=False, encoding="utf-8-sig")

    runner = FakeRunner(tmp_path, rel_path, latest_date)
    with pytest.raises(SystemExit) as exc_info:
        main([], runner=runner, root=tmp_path)

    assert exc_info.value.code == 0

    # 表示の確認
    captured = capsys.readouterr()
    assert "徳島県（36）前回が完了していません（失敗（[9/14] ハザード区域の判定（碑）））" in captured.out

    # 最初の runner のコマンド確認
    first_call = runner.calls[0]
    parts = [Path(c).name for c in first_call if str(c).endswith(".py")]
    first_script = parts[0] if parts else ""
    if "--pref" in first_call:
        pref_idx = first_call.index("--pref") + 1
        first_script += f" --pref {first_call[pref_idx]}"
    if "--force" in first_call:
        first_script += " --force"
    assert first_script == "run_batch.py --pref 36 --force"

    # update_history_all の最後の行が「完了」・作り直した県 36
    df_all_after = pd.read_csv(all_hist, encoding="utf-8-sig", dtype=str)
    last_row = df_all_after.iloc[-1]
    assert last_row["結果"] == "完了"
    assert last_row["作り直した県"] == "36"


def test_9_site_build_prefs_with_empty_rows(tmp_path):
    """
    9. update_history_all.csv の途中に全部が空の行がある（dropna で抜ける）場合でも、
    get_prefs_for_site_build が最後の「完了」より後の行の県だけを返す
    """
    hist_all = tmp_path / "update_history_all.csv"

    # 完了行の前に空行がある場合、dropna 後の index と iloc がずれる典型例:
    # 0行目: 失敗 (作り直した県: 01)
    # 1行目: 全部が空の行 (dropna で抜ける)
    # 2行目: 完了 (作り直した県: 02) -> reset_index 前の index は 2、dropna 後は 1番目の行
    # 3行目: 全部が空の行 (dropna で抜ける)
    # 4行目: 失敗 (作り直した県: 36) -> reset_index 前の index は 4、dropna 後は 2番目の行
    csv_content = (
        "実行日時,新データ取得日,新データのファイル,作り直した県,変更なしの県数,結果\n"
        "2026-09-24 09:00,2026-09-24,file1,01,46,失敗（...）\n"
        ",,,,,\n"
        "2026-09-24 10:00,2026-09-24,file1,02,46,完了\n"
        "\n"
        "2026-09-24 11:00,2026-09-24,file1,36,46,失敗（...）\n"
    )
    hist_all.write_text(csv_content, encoding="utf-8-sig")

    result = get_prefs_for_site_build(rebuild_pref_codes=[], update_history_all_path=hist_all)

    # 期待される県コード: 36 のみ（01, 02 は完了以前なので含まれない）
    assert result == ["36"]


def test_10_summarize_region_fails(tmp_path, capsys):
    """
    10. runner が summarize_region.py で終了コード 1 を返すと、
    [3/7] 地形分類（地域版）の全国集計 で失敗しました が表示され、
    update_history_all.csv の最後の行の結果が 失敗（[3/7] 地形分類（地域版）の全国集計）、終了コード 1。
    そのあと印刷用PDF・全国ページ・取得不可の件数は呼ばれない
    """
    setup_base_mock_project(tmp_path, date="2026-09-24")

    # 36県に1基追加
    extra = [
        ["36001-002", "徳島碑2", "1950", "徳島県某所", "津波", "津波", "内容2", "34.0", "134.0", "2026-10-14", "2026-10-14", "なし"]
    ]
    new_rel_path = "data/raw/2026-10-14/denshouhi_20261014.csv"
    raw_20261014 = tmp_path / "data" / "raw" / "2026-10-14" / "denshouhi_20261014.csv"
    records = []
    for p in sorted(PREFECTURES.keys()):
        pref_name = PREFECTURES[p]
        records.append([
            f"{p}001-001", f"{pref_name}碑1", "1900", f"{pref_name}某所",
            "地震", "地震", "伝承内容", "35.0", "135.0", "2020-01-01", "2020-01-01", "なし"
        ])
    records.extend(extra)
    create_dummy_raw_csv(raw_20261014, records)

    runner = FakeRunner(tmp_path, new_rel_path, "2026-10-14", fail_targets={"summarize_region.py": 1})

    with pytest.raises(SystemExit) as exc_info:
        main([], runner=runner, root=tmp_path)

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "[3/7] 地形分類（地域版）の全国集計 で失敗しました" in captured.out

    hist_all_path = tmp_path / "output" / "update_history_all.csv"
    assert hist_all_path.exists()
    df_all = pd.read_csv(hist_all_path, encoding="utf-8-sig", dtype=str)
    assert df_all.iloc[-1]["結果"] == "失敗（[3/7] 地形分類（地域版）の全国集計）"

    called_scripts = []
    for call in runner.calls:
        parts = [Path(c).name for c in call if str(c).endswith(".py")]
        script = parts[0] if parts else ""
        called_scripts.append(script)

    assert called_scripts == ["run_batch.py", "summarize_national.py", "summarize_region.py"]
    assert "make_national_pdf.py" not in called_scripts
    assert "build_national.py" not in called_scripts
    assert "count_missing.py" not in called_scripts


