import pytest
import pandas as pd
from pathlib import Path
import sys
import os
import subprocess
from unittest.mock import MagicMock, patch

from src.update import main, compare_dataframes, run_steps, determine_old_csv

REQUIRED_COLUMNS = [
    "ID", "碑名", "建立年", "所在地", "災害名", "災害種別", 
    "伝承内容", "緯度", "経度", "公開日", "修正等公開日", "制限事項"
]

def make_dummy_csv(path, records):
    df = pd.DataFrame(records, columns=REQUIRED_COLUMNS)
    df.to_csv(path, index=False, encoding='utf-8-sig')
    return path

def test_a_b_c_d_compare(tmp_path):
    old_records = [
        ["36001-001", "碑A", "1900", "徳島県A", "地震", "地震", "内容A", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-002", "碑B", "1900", "徳島県B", "地震", "地震", "内容B", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-003", "碑C", "1900", "徳島県C", "地震", "地震", "内容C", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-004", "碑D", "1900", "徳島県D", "地震", "地震", "内容D", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-005", "碑E", "1900", "徳島県E", "地震", "地震", "内容E", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-006", "碑F", "1900", "徳島県F", "地震", "地震", "内容F", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-007", "碑G", "1900", "徳島県G", "地震", "地震", "", "34.0", "134.0", "2020", "2020", "なし"],
    ]
    
    new_records = [
        ["36001-001", "碑A改", "1900", "徳島県A", "地震", "地震", "内容A", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-008", "碑H", "1900", "徳島県H", "地震", "地震", "内容H", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-003", "碑C", "1900", "徳島県C", "地震", "地震", "内容C新", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-004", "碑D", "1900", "徳島県D", "地震", "地震", "内容D", "34.0001", "134.0", "2020", "2020", "なし"],
        ["36001-005", "碑E", "1900", "徳島県E", "地震", "地震", "内容E", "34.00000001", "134.0", "2020", "2020", "なし"],
        ["36001-006", "碑F", "1900", "徳島県F ", "地震", "地震", " 内容F", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-007", "碑G", "1900", "徳島県G", "地震", "地震", float('nan'), "34.0", "134.0", "2020", "2020", "なし"],
    ]

    df_old = pd.DataFrame(old_records, columns=REQUIRED_COLUMNS)
    df_new = pd.DataFrame(new_records, columns=REQUIRED_COLUMNS)
    
    df_old_36 = df_old[df_old['ID'].str.startswith('36')]
    df_new_36 = df_new[df_new['ID'].str.startswith('36')]
    
    df_diff = compare_dataframes(df_old_36, df_new_36)
    
    assert len(df_diff) == 5
    
    adds = df_diff[df_diff['区分'] == '追加']
    assert len(adds) == 1
    assert adds.iloc[0]['ID'] == "36001-008"
    
    mods = df_diff[df_diff['区分'] == '変更']
    assert len(mods) == 3
    
    dels = df_diff[df_diff['区分'] == '削除']
    assert len(dels) == 1
    assert dels.iloc[0]['ID'] == "36001-002"

def test_e_main(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    old_records = [
        ["12001-001", "千葉A", "1900", "千葉県A", "地震", "地震", "内容", "35.0", "140.0", "2020", "2020", "なし"],
        ["36001-001", "碑A", "1900", "徳島県A", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
    ]
    new_records = [
        ["12001-001", "千葉A改", "1900", "千葉県A", "地震", "地震", "内容", "35.0", "140.0", "2020", "2020", "なし"],
        ["36001-001", "碑A改", "1900", "徳島県A", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
    ]
    old_csv = make_dummy_csv(tmp_path / "old.csv", old_records)
    new_csv = make_dummy_csv(tmp_path / "new.csv", new_records)
    
    with patch('src.load_monuments.get_fetch_date', side_effect=["2026-09-24", "2026-09-20"]):
        main(['--pref', '36', '--new', str(new_csv), '--old', str(old_csv), '--dry-run'])
        
    diff_dir = tmp_path / "output" / "diff"
    diff_files = list(diff_dir.glob("diff_36_*.csv"))
    assert len(diff_files) == 1
    
    df_diff = pd.read_csv(diff_files[0], encoding='utf-8-sig', dtype=str)
    assert len(df_diff) == 1
    assert "12001-001" not in df_diff['ID'].values
    assert df_diff.iloc[0]['ID'] == "36001-001"

def test_f_duplicate_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    new_records = [
        ["36001-001", "碑A", "1900", "徳島県A", "地震", "地震", "内容A", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-001", "碑A", "1900", "徳島県A", "地震", "地震", "内容A", "34.0", "134.0", "2020", "2020", "なし"]
    ]
    new_csv = make_dummy_csv(tmp_path / "new.csv", new_records)
    old_csv = make_dummy_csv(tmp_path / "old.csv", [])
    
    with pytest.raises(SystemExit) as e:
        main(['--pref', '36', '--new', str(new_csv), '--old', str(old_csv), '--dry-run'])
    
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "重複したIDがあります" in captured.out

def test_g_sort_bom(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    old_records = [
        ["36001-005", "碑5", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-001", "碑1", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-008", "碑8", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-003", "碑3", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
    ]
    new_records = [
        ["36001-009", "碑9", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-002", "碑2", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-005", "碑5改", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-001", "碑1改", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
    ]
    old_csv = make_dummy_csv(tmp_path / "old.csv", old_records)
    new_csv = make_dummy_csv(tmp_path / "new.csv", new_records)
    
    with patch('src.load_monuments.get_fetch_date', side_effect=["2026-09-24", "2026-09-20"]):
        main(['--pref', '36', '--new', str(new_csv), '--old', str(old_csv), '--dry-run'])
        
    diff_dir = tmp_path / "output" / "diff"
    diff_files = list(diff_dir.glob("diff_36_*.csv"))
    assert len(diff_files) == 1
    diff_file = diff_files[0]
    
    with open(diff_file, 'rb') as f:
        assert f.read(3) == b'\xef\xbb\xbf'
        
    df_diff = pd.read_csv(diff_file, encoding='utf-8-sig', dtype=str)
    assert list(df_diff['ID']) == [
        "36001-002", "36001-009",
        "36001-001", "36001-005",
        "36001-003", "36001-008"
    ]
    assert list(df_diff['区分']) == ["追加", "追加", "変更", "変更", "削除", "削除"]

def test_h_first_time(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    new_records = [
        ["36001-001", "碑1", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-002", "碑2", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
        ["36001-003", "碑3", "1900", "徳島県", "地震", "地震", "内容", "34.0", "134.0", "2020", "2020", "なし"],
    ]
    new_csv = make_dummy_csv(tmp_path / "2026-09-24.csv", new_records)
    
    with patch('src.load_monuments.get_fetch_date', return_value="2026-09-24"):
        main(['--pref', '36', '--new', str(new_csv), '--dry-run'])
        
    diff_dir = tmp_path / "output" / "diff"
    diff_files = list(diff_dir.glob("diff_36_none_2026-09-24.csv"))
    assert len(diff_files) == 1
    
    df_diff = pd.read_csv(diff_files[0], encoding='utf-8-sig', dtype=str)
    assert len(df_diff) == 3
    assert all(df_diff['区分'] == '追加')

def test_i_determine_old_csv(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    d1 = raw_dir / "2026-09-01"
    d1.mkdir()
    (d1 / "csv1.csv").touch()
    d2 = raw_dir / "2026-09-10"
    d2.mkdir()
    (d2 / "csv2.csv").touch()
    d3 = raw_dir / "2026-09-20"
    d3.mkdir()
    (d3 / "csv3.csv").touch()
    
    old_csv = determine_old_csv('36', base_dir=str(raw_dir))
    assert Path(old_csv).name == "csv2.csv"
    
    hist_file = tmp_path / "output" / "update_history_36.csv"
    hist_file.parent.mkdir(parents=True, exist_ok=True)
    df_hist = pd.DataFrame([
        {'結果': '失敗', '新データのファイル': 'data/raw/2026-09-10/csv2.csv'},
        {'結果': '完了', '新データのファイル': 'data/raw/2026-09-01/csv1.csv'}
    ])
    df_hist.to_csv(hist_file, index=False, encoding='utf-8-sig')
    
    old_csv = determine_old_csv('36', base_dir=str(raw_dir))
    assert Path(old_csv).name == "csv1.csv"

def test_determine_old_csv_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    d1 = raw_dir / "2026-09-01"
    d1.mkdir()
    (d1 / "csv1.csv").touch()
    d2 = raw_dir / "2026-09-10"
    d2.mkdir()
    (d2 / "csv2.csv").touch()
    d3 = raw_dir / "2026-09-20"
    d3.mkdir()
    (d3 / "csv3.csv").touch()
    
    hist_file = tmp_path / "output" / "update_history_36.csv"
    hist_file.parent.mkdir(parents=True, exist_ok=True)
    with open(hist_file, 'w', encoding='utf-8-sig') as f:
        f.write("a,b,c\n1,2,3")
        
    old_csv = determine_old_csv('36', base_dir=str(raw_dir))
    captured = capsys.readouterr()
    assert "注意：更新履歴の完了記録またはその新データファイルが見つかりません。2番目に新しい日付フォルダと比べます" in captured.out
    assert Path(old_csv).name == "csv2.csv"

def test_j_update_history(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    new_csv_path = tmp_path / "2026-09-24" / "new.csv"
    new_csv_path.parent.mkdir(parents=True, exist_ok=True)
    new_csv = make_dummy_csv(new_csv_path, [])
    
    with patch('src.load_monuments.get_fetch_date', return_value="2026-09-24"):
        main(['--pref', '36', '--new', str(new_csv), '--dry-run'])
    hist_file = tmp_path / "output" / "update_history_36.csv"
    assert not hist_file.exists()
    
    def dummy_runner(cmd):
        res = MagicMock()
        res.returncode = 0
        return res
        
    with patch('src.load_monuments.get_fetch_date', return_value="2026-09-24"):
        main(['--pref', '36', '--new', str(new_csv)], runner=dummy_runner)
    
    assert hist_file.exists()
    df_hist = pd.read_csv(hist_file, encoding='utf-8-sig')
    assert len(df_hist) == 1
    assert df_hist.iloc[0]['結果'] == '完了'

def test_k_run_steps_main(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    new_csv_path = tmp_path / "new.csv"
    new_csv = make_dummy_csv(new_csv_path, [])
    
    called_cmds = []
    def fake_runner(cmd):
        called_cmds.append(cmd)
        res = MagicMock()
        res.returncode = 0
        return res
        
    with patch('src.load_monuments.get_fetch_date', return_value="2026-09-24"):
        main(['--pref', '36', '--new', str(new_csv)], runner=fake_runner)
        
    exe = sys.executable
    expected_cmds = [
        [exe, str(tmp_path / "src" / "load_monuments.py"), "--pref", "36", "--raw", str(new_csv.resolve())],
        [exe, str(tmp_path / "src" / "add_elevation.py"), "--pref", "36"],
        [exe, str(tmp_path / "src" / "add_river_coast.py"), "--pref", "36"],
        [exe, str(tmp_path / "src" / "add_landform.py"), "--pref", "36"],
        [exe, str(tmp_path / "src" / "make_comparison_points.py"), "--pref", "36"],
        [exe, str(tmp_path / "src" / "add_elevation.py"), "--pref", "36", "--target", "points"],
        [exe, str(tmp_path / "src" / "add_river_coast.py"), "--pref", "36", "--target", "points"],
        [exe, str(tmp_path / "src" / "add_landform.py"), "--pref", "36", "--target", "points"],
        [exe, str(tmp_path / "src" / "summarize.py"), "--pref", "36"],
        [exe, str(tmp_path / "src" / "make_map.py"), "--pref", "36"],
        [exe, str(tmp_path / "src" / "build_site.py"), "--pref", "36"]
    ]
    
    assert called_cmds == expected_cmds

def test_run_steps_error(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    df_diff = pd.DataFrame(columns=['ID', '区分', '碑名', '変わった列', '位置の変更'])
    steps = [
        ("step1", ["script1.py"]),
        ("step2", ["script2.py"]),
        ("step3", ["script3.py"]),
    ]
    
    called_cmds = []
    def fail_at_3(cmd):
        called_cmds.append(cmd)
        res = MagicMock()
        res.returncode = 1 if "script3.py" in cmd[1] else 0
        return res
        
    with pytest.raises(SystemExit) as e:
        run_steps(steps, fail_at_3, "new.csv", "36", df_diff, "none", "2026", "", "new.csv", 0, 0)
    assert e.value.code == 1
    assert len(called_cmds) == 3
    
    hist_file = tmp_path / "output" / "update_history_36.csv"
    df_hist = pd.read_csv(hist_file, encoding='utf-8-sig')
    assert "失敗" in df_hist.iloc[-1]['結果']
    
    def interrupt_at_2(cmd):
        if "script2.py" in cmd[1]:
            raise KeyboardInterrupt()
        res = MagicMock()
        res.returncode = 0
        return res
        
    with pytest.raises(SystemExit) as e:
        run_steps(steps, interrupt_at_2, "new.csv", "36", df_diff, "none", "2026", "", "new.csv", 0, 0)
    assert e.value.code == 1
    df_hist = pd.read_csv(hist_file, encoding='utf-8-sig')
    assert "中断" in df_hist.iloc[-1]['結果']

def test_l_same_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    same_file = tmp_path / "same.csv"
    same_file.touch()
    with pytest.raises(SystemExit) as e:
        main(['--pref', '36', '--new', str(same_file), '--old', str(same_file), '--dry-run'])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "古いデータと新しいデータが同じファイルです" in captured.out

def test_default_runner_cwd(tmp_path, monkeypatch):
    monkeypatch.setattr('src.update.PROJECT_ROOT', tmp_path)
    from src.update import default_runner
    
    with patch('subprocess.run') as mock_run:
        default_runner(["echo", "test"])
        mock_run.assert_called_once_with(["echo", "test"], cwd=tmp_path)
