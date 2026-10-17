"""src/run_region_batch.py の単体テスト。

tmp_path に偽の data/processed を作り、偽の runner と差し替えた now を使って通信なしで検証する。
"""

import csv
import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.run_region_batch import LOG_COLUMNS, main


def write_input_csv(path, num_rows, prefix):
    """テスト用の入力CSV（monuments_XX.csv または points_XX.csv）を作成する"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["ID", "碑名", "緯度", "経度"])
        for i in range(num_rows):
            writer.writerow([f"{prefix}-{i:03d}", f"地点{i}", "34.0", "134.0"])


def write_region_output_csv(path, statuses):
    """テスト用の出力CSV（landform_region_XX.csv 等）を指定した地域版_状態リストで作成する"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "ID",
        "碑名",
        "緯度",
        "経度",
        "地域版_地形分類名",
        "地域版_コード",
        "地域版_重なり数",
        "地域版_状態",
        "取得日",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for i, st in enumerate(statuses):
            writer.writerow(
                {
                    "ID": f"id-{i:03d}",
                    "碑名": f"地点{i}",
                    "緯度": "34.0",
                    "経度": "134.0",
                    "地域版_地形分類名": "低地" if st.startswith("取得済") else "",
                    "地域版_コード": "51" if st == "取得済（地域版）" else ("5" if st == "取得済（広域版）" else ""),
                    "地域版_重なり数": 1 if st.startswith("取得済") else 0,
                    "地域版_状態": st,
                    "取得日": "2026-10-16" if st != "取得不可" else "",
                }
            )


def make_clock(step_sec=30):
    """呼び出しごとに指定秒数ずつ進むテスト用の時刻関数を返す"""
    cur = [datetime.datetime(2026, 10, 16, 12, 0, 0)]

    def _now():
        val = cur[0]
        cur[0] = val + datetime.timedelta(seconds=step_sec)
        return val

    return _now


def setup_two_prefs(tmp_path):
    """35（山口：碑2・比較地点3）と36（徳島：碑3・比較地点4）の入力CSVを用意する"""
    proc = tmp_path / "data" / "processed"
    write_input_csv(proc / "monuments_35.csv", 2, "35M")
    write_input_csv(proc / "points_35.csv", 3, "35P")
    write_input_csv(proc / "monuments_36.csv", 3, "36M")
    write_input_csv(proc / "points_36.csv", 4, "36P")


def test_two_prefs_success_and_log(tmp_path, capsys):
    """(a) 2県で完了 → まとめの文言・終了コード 0・ログ2行（列名と順番、改行が LF）"""
    setup_two_prefs(tmp_path)
    proc = tmp_path / "data" / "processed"

    def fake_runner(cmd):
        pref = cmd[cmd.index("--pref") + 1]
        is_points = "--target" in cmd and "points" in cmd
        if pref == "35":
            if not is_points:
                write_region_output_csv(
                    proc / "landform_region_35.csv",
                    ["取得済（地域版）", "取得済（地域版）"],
                )
            else:
                write_region_output_csv(
                    proc / "landform_region_points_35.csv",
                    ["取得済（地域版）", "取得済（広域版）", "データなし"],
                )
        elif pref == "36":
            if not is_points:
                write_region_output_csv(
                    proc / "landform_region_36.csv",
                    ["取得済（地域版）", "取得済（地域版）", "データなし"],
                )
            else:
                write_region_output_csv(
                    proc / "landform_region_points_36.csv",
                    ["取得済（地域版）", "取得済（地域版）", "取得済（地域版）", "データなし"],
                )
        res = MagicMock()
        res.returncode = 0
        return res

    with pytest.raises(SystemExit) as e:
        main(["--pref", "36,35"], runner=fake_runner, root=str(tmp_path), now=make_clock(30))

    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "地域版の一括実行の対象: 2都道府県（碑 5基・比較地点 7点）" in out
    assert "データの確認: そろっています" in out
    assert "地域版の一括実行のまとめ（output/region_batch_log.csv に記録しました）" in out
    assert "  山口県（35）完了　地域版 3・広域版 1・データなし 1・取得不可 0" in out
    assert "  徳島県（36）完了　地域版 5・広域版 0・データなし 2・取得不可 0" in out
    assert "完了 2県／要再実行 0県／失敗 0県" in out
    assert (
        "合計（完了と要再実行の県）：地域版 8・広域版 1・データなし 3・取得不可 0　タイル：地域版 0枚・広域版 0枚"
        in out
    )

    log_file = tmp_path / "output" / "region_batch_log.csv"
    assert log_file.exists()
    raw_bytes = log_file.read_bytes()
    assert raw_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw_bytes

    with open(log_file, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    assert header == LOG_COLUMNS
    assert len(rows) == 2
    assert rows[0][2] == "35"
    assert rows[0][3] == "山口県"
    assert rows[0][6] == "完了"
    assert rows[1][2] == "36"
    assert rows[1][3] == "徳島県"
    assert rows[1][6] == "完了"


def test_runner_command_order_and_target(tmp_path):
    """(b) runner に渡すコマンドの順番が「県1 碑 → 県1 比較地点 → 県2 碑 → 県2 比較地点」で、add_landform_region.py 以外を呼ばない"""
    setup_two_prefs(tmp_path)
    proc = tmp_path / "data" / "processed"
    called_cmds = []

    def fake_runner(cmd):
        called_cmds.append(cmd)
        pref = cmd[cmd.index("--pref") + 1]
        is_points = "--target" in cmd and "points" in cmd
        if not is_points:
            n = 2 if pref == "35" else 3
            write_region_output_csv(proc / f"landform_region_{pref}.csv", ["取得済（地域版）"] * n)
        else:
            n = 3 if pref == "35" else 4
            write_region_output_csv(
                proc / f"landform_region_points_{pref}.csv", ["取得済（地域版）"] * n
            )
        res = MagicMock()
        res.returncode = 0
        return res

    with pytest.raises(SystemExit) as e:
        main(["--pref", "36,35"], runner=fake_runner, root=str(tmp_path), now=make_clock())

    assert e.value.code == 0
    assert len(called_cmds) == 4

    for cmd in called_cmds:
        script_name = Path(cmd[1]).name
        assert script_name == "add_landform_region.py"

    assert called_cmds[0][2:] == ["--pref", "35"]
    assert called_cmds[1][2:] == ["--pref", "35", "--target", "points"]
    assert called_cmds[2][2:] == ["--pref", "36"]
    assert called_cmds[3][2:] == ["--pref", "36", "--target", "points"]


def test_monuments_failure_skips_points_and_continues(tmp_path, capsys):
    """(c) 碑のコマンドが returncode 1 → 比較地点は呼ばれない・「失敗」・終了コード 1・次の県は続ける"""
    setup_two_prefs(tmp_path)
    proc = tmp_path / "data" / "processed"
    called_cmds = []

    def fake_runner(cmd):
        called_cmds.append(cmd)
        pref = cmd[cmd.index("--pref") + 1]
        is_points = "--target" in cmd and "points" in cmd
        res = MagicMock()
        if pref == "35":
            res.returncode = 1
            return res
        if not is_points:
            write_region_output_csv(proc / "landform_region_36.csv", ["取得済（地域版）"] * 3)
        else:
            write_region_output_csv(
                proc / "landform_region_points_36.csv", ["取得済（地域版）"] * 4
            )
        res.returncode = 0
        return res

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35,36"], runner=fake_runner, root=str(tmp_path), now=make_clock())

    assert e.value.code == 1
    assert len(called_cmds) == 3
    assert called_cmds[0][2:] == ["--pref", "35"]
    assert called_cmds[1][2:] == ["--pref", "36"]
    assert called_cmds[2][2:] == ["--pref", "36", "--target", "points"]

    out = capsys.readouterr().out
    assert "[1/2] 山口県（35）失敗（上の表示で原因を確かめてください）" in out
    assert "  山口県（35）失敗\n" in out
    assert "完了 1県／要再実行 0県／失敗 1県" in out

    log_file = tmp_path / "output" / "region_batch_log.csv"
    with open(log_file, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["結果"] == "失敗"
    assert rows[0]["取得済_地域版"] == ""
    assert rows[0]["取得不可"] == ""
    assert rows[1]["結果"] == "完了"


def test_status_error_marks_retry(tmp_path, capsys):
    """(d) 取得不可が1件 → 「要再実行」・終了コード 1"""
    proc = tmp_path / "data" / "processed"
    write_input_csv(proc / "monuments_35.csv", 2, "35M")
    write_input_csv(proc / "points_35.csv", 2, "35P")

    def fake_runner(cmd):
        is_points = "--target" in cmd and "points" in cmd
        if not is_points:
            write_region_output_csv(
                proc / "landform_region_35.csv", ["取得済（地域版）", "取得済（地域版）"]
            )
        else:
            write_region_output_csv(
                proc / "landform_region_points_35.csv", ["取得済（地域版）", "取得不可"]
            )
        res = MagicMock()
        res.returncode = 0
        return res

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35"], runner=fake_runner, root=str(tmp_path), now=make_clock())

    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "[1/1] 山口県（35）要再実行（取得不可 1件・行数の不一致 なし）" in out
    assert "  山口県（35）要再実行　地域版 3・広域版 0・データなし 0・取得不可 1" in out
    assert "完了 0県／要再実行 1県／失敗 0県" in out


def test_row_count_mismatch_marks_retry(tmp_path, capsys):
    """(e) 出力の行数が入力と違う → 「要再実行」（行数の不一致 あり）"""
    proc = tmp_path / "data" / "processed"
    write_input_csv(proc / "monuments_35.csv", 2, "35M")
    write_input_csv(proc / "points_35.csv", 3, "35P")

    def fake_runner(cmd):
        is_points = "--target" in cmd and "points" in cmd
        if not is_points:
            write_region_output_csv(
                proc / "landform_region_35.csv", ["取得済（地域版）", "取得済（地域版）"]
            )
        else:
            # 入力3行に対して2行だけ書き出す
            write_region_output_csv(
                proc / "landform_region_points_35.csv", ["取得済（地域版）", "取得済（地域版）"]
            )
        res = MagicMock()
        res.returncode = 0
        return res

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35"], runner=fake_runner, root=str(tmp_path), now=make_clock())

    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "[1/1] 山口県（35）要再実行（取得不可 0件・行数の不一致 あり）" in out
    assert "完了 0県／要再実行 1県／失敗 0県" in out


def test_cache_file_increase_counted(tmp_path, capsys):
    """(f) キャッシュのファイル数の増加（13 に3枚・8 に1枚）がタイルの枚数として出る"""
    proc = tmp_path / "data" / "processed"
    write_input_csv(proc / "monuments_35.csv", 2, "35M")
    write_input_csv(proc / "points_35.csv", 2, "35P")

    cache_13 = tmp_path / "data" / "cache" / "landform" / "13" / "7100"
    cache_8 = tmp_path / "data" / "cache" / "landform" / "8" / "220"
    cache_13.mkdir(parents=True, exist_ok=True)
    cache_8.mkdir(parents=True, exist_ok=True)
    # 既存のキャッシュ1枚ずつ
    (cache_13 / "existing.geojson").write_text("{}", encoding="utf-8", newline="\n")
    (cache_8 / "existing.geojson").write_text("{}", encoding="utf-8", newline="\n")

    def fake_runner(cmd):
        is_points = "--target" in cmd and "points" in cmd
        if not is_points:
            write_region_output_csv(
                proc / "landform_region_35.csv", ["取得済（地域版）", "取得済（地域版）"]
            )
            (cache_13 / "new1.geojson").write_text("{}", encoding="utf-8", newline="\n")
            (cache_13 / "new2.geojson").write_text("{}", encoding="utf-8", newline="\n")
        else:
            write_region_output_csv(
                proc / "landform_region_points_35.csv", ["取得済（地域版）", "取得済（広域版）"]
            )
            (cache_13 / "new3.geojson").write_text("{}", encoding="utf-8", newline="\n")
            (cache_8 / "new1.geojson").write_text("{}", encoding="utf-8", newline="\n")
        res = MagicMock()
        res.returncode = 0
        return res

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35"], runner=fake_runner, root=str(tmp_path), now=make_clock())

    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "タイル：地域版 3枚・広域版 1枚" in out

    log_file = tmp_path / "output" / "region_batch_log.csv"
    with open(log_file, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["地域版タイルの取得"] == "3"
    assert rows[0]["広域版タイルの取得"] == "1"


def test_check_only(tmp_path, capsys):
    """(g) --check-only → runner は呼ばれず、終了コード 0、件数の表示"""
    setup_two_prefs(tmp_path)
    fake_runner = MagicMock()

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35,36", "--check-only"], runner=fake_runner, root=str(tmp_path))

    assert e.value.code == 0
    fake_runner.assert_not_called()
    out = capsys.readouterr().out
    assert "地域版の一括実行の対象: 2都道府県（碑 5基・比較地点 7点）" in out
    assert "データの確認: そろっています" in out
    assert "データの確認だけ行いました（--check-only）" in out


def test_missing_points_csv(tmp_path, capsys):
    """(h) points_XX.csv がない県 → 足りない旨と python src/run_batch.py --pref "XX" の案内・終了コード 1・runner は呼ばれない"""
    proc = tmp_path / "data" / "processed"
    write_input_csv(proc / "monuments_35.csv", 2, "35M")
    # points_35.csv は作らない
    fake_runner = MagicMock()

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35"], runner=fake_runner, root=str(tmp_path))

    assert e.value.code == 1
    fake_runner.assert_not_called()
    out = capsys.readouterr().out
    assert "  山口県（35）points_35.csv がありません" in out
    assert '先に実行してください：python src/run_batch.py --pref "35"' in out


def test_invalid_pref_code(tmp_path, capsys):
    """(i) 不正な県コード（例 "48"）→ 終了コード 1"""
    fake_runner = MagicMock()

    with pytest.raises(SystemExit) as e:
        main(["--pref", "48"], runner=fake_runner, root=str(tmp_path))

    assert e.value.code == 1
    fake_runner.assert_not_called()
    out = capsys.readouterr().out
    assert "エラー: --pref に使えない県コードがあります: 48" in out


def test_keyboard_interrupt_logs_and_exits(tmp_path, capsys):
    """(j) KeyboardInterrupt → 「中断」がログに残り、終了コード 1"""
    setup_two_prefs(tmp_path)

    def fake_runner(cmd):
        raise KeyboardInterrupt()

    with pytest.raises(SystemExit) as e:
        main(["--pref", "35,36"], runner=fake_runner, root=str(tmp_path), now=make_clock())

    assert e.value.code == 1
    out = capsys.readouterr().out
    assert (
        "中断しました。もう一度同じコマンドを実行すると、取得済みのタイルはキャッシュから読むので短時間で続きまで進みます"
        in out
    )

    log_file = tmp_path / "output" / "region_batch_log.csv"
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["県コード"] == "35"
    assert rows[0]["結果"] == "中断"
    assert rows[0]["取得済_地域版"] == ""

