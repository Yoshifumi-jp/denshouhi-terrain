import pytest
import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from src.run_batch import main, format_duration

def test_format_duration():
    assert format_duration(30) == "1分未満"
    assert format_duration(60) == "1分"
    assert format_duration(119.4) == "1分"
    assert format_duration(120) == "2分"
    assert format_duration(3600) == "1時間0分"
    assert format_duration(11520) == "3時間12分"

def setup_mock_env(tmp_path):
    
    raw_dir = tmp_path / "data" / "raw"
    rivers_dir = raw_dir / "rivers"
    coast_dir = raw_dir / "coastline"
    rivers_dir.mkdir(parents=True)
    coast_dir.mkdir(parents=True)
    
    (tmp_path / "output").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "cache").mkdir(parents=True, exist_ok=True)
    
    # Dummy raw CSV
    date_dir = raw_dir / "2026-09-24"
    date_dir.mkdir()
    csv_path = date_dir / "denshouhi_20260924.csv"
    
    # 03, 20, 28 (163, 111, 103)
    records = []
    for i in range(163):
        records.append([f"03001-{i:03}", "碑", "1900", "岩手", "地震", "地震", "内容", "39", "141", "2020", "2020", "なし"])
    for i in range(111):
        records.append([f"20001-{i:03}", "碑", "1900", "長野", "地震", "地震", "内容", "36", "138", "2020", "2020", "なし"])
    for i in range(103):
        records.append([f"28001-{i:03}", "碑", "1900", "兵庫", "地震", "地震", "内容", "34", "135", "2020", "2020", "なし"])
        
    df = pd.DataFrame(records, columns=[
        "ID", "碑名", "建立年", "所在地", "災害名", "災害種別", 
        "伝承内容", "緯度", "経度", "公開日", "修正等公開日", "制限事項"
    ])
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    return tmp_path

def create_dummy_shapefiles(tmp_path, prefs, target_prefs, kind):
    # kind: 'rivers' or 'coastline'
    d = tmp_path / "data" / "raw" / kind
    for p in target_prefs:
        if kind == 'rivers':
            subdir = d / f"W05-test_{p}_GML"
            subdir.mkdir(exist_ok=True)
            (subdir / f"test_{p}_Stream.shp").touch()
        else:
            subdir = d / f"C23-test_{p}_GML"
            subdir.mkdir(exist_ok=True)
            (subdir / f"test_{p}_Coastline.shp").touch()

def test_missing_data(tmp_path, capsys):
    setup_mock_env(tmp_path)
    # 河川データを置かない
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03'], root=str(tmp_path))
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert "足りません" in out
    assert "データが足りない県があります" in out

def test_check_only(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    target_20 = [ '20' ] + NEIGHBORS['20']
    target_28 = [ '28' ] + NEIGHBORS['28']
    
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    
    create_dummy_shapefiles(tmp_path, ['20'], target_20, 'rivers')
    # 長野(20)は海なし県なので海岸線は置かなくてもよい
    
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'coastline')
    
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28', '--check-only'], root=str(tmp_path))
        
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "一括実行の対象: 岩手県（03）、長野県（20）、兵庫県（28）（3県・377基）" in out
    assert "データの確認だけ行いました" in out
    assert "岩手県（03）163基　河川 4県分・海岸線 4県分　そろっています" in out
    assert "長野県（20）111基　河川 9県分・海岸線 なし（海のない県）　そろっています" in out
    assert "兵庫県（28）103基　河川 5県分・海岸線 5県分　そろっています" in out

def test_all_pref(tmp_path, capsys):
    setup_mock_env(tmp_path)
    
    with pytest.raises(SystemExit) as e:
        main(['--pref', 'all', '--check-only'], root=str(tmp_path))
        
    # All prefs won't have shapefiles, so it will print error and exit 1
    # But it should not throw ValueError/KeyError
    # We allow exit code 1 or 0
    assert e.value.code in (0, 1)
    
    out = capsys.readouterr().out
    assert "47県" in out
    # 47 counties should be printed
    printed_count = sum(1 for line in out.splitlines() if "）0基" in line or "基　河川" in line)
    assert printed_count == 47

def test_success(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    target_20 = [ '20' ] + NEIGHBORS['20']
    target_28 = [ '28' ] + NEIGHBORS['28']
    
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    create_dummy_shapefiles(tmp_path, ['20'], target_20, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'coastline')
    
    called_cmds = []
    def fake_runner(cmd):
        called_cmds.append(cmd)
        res = MagicMock()
        res.returncode = 0
        return res
        
    times = [
        datetime.datetime(2026, 10, 7, 22, 0, 0),
        datetime.datetime(2026, 10, 8, 1, 12, 0), # 3h 12m for 03
        datetime.datetime(2026, 10, 8, 1, 12, 0),
        datetime.datetime(2026, 10, 8, 1, 57, 0), # 45m for 20
        datetime.datetime(2026, 10, 8, 1, 57, 0),
        datetime.datetime(2026, 10, 8, 1, 57, 30), # 30s for 28
    ]
    def fake_now():
        return times.pop(0)
        
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28'], runner=fake_runner, root=str(tmp_path), now=fake_now)
        
    assert e.value.code == 0
    assert len(called_cmds) == 3
    for cmd in called_cmds:
        assert "--no-site" in cmd
        
    log_file = tmp_path / "output" / "batch_log.csv"
    assert log_file.exists()
    df_log = pd.read_csv(log_file)
    assert len(df_log) == 3
    assert list(df_log['結果']) == ['完了', '完了', '完了']
    
    out = capsys.readouterr().out
    assert "完了 3県／失敗 0県／飛ばした 0県" in out

def test_resume_and_force(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    target_20 = [ '20' ] + NEIGHBORS['20']
    target_28 = [ '28' ] + NEIGHBORS['28']
    
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    create_dummy_shapefiles(tmp_path, ['20'], target_20, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'coastline')
    
    # 03 は完了済みにする
    hist_03 = tmp_path / "output" / "update_history_03.csv"
    hist_03.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        '実行日時': '2026-10-07 20:00',
        '結果': '完了',
        '新データのファイル': 'data/raw/2026-09-24/denshouhi_20260924.csv'
    }]).to_csv(hist_03, index=False, encoding='utf-8-sig')
    
    called_cmds = []
    def fake_runner(cmd):
        called_cmds.append(cmd)
        res = MagicMock()
        res.returncode = 0
        return res
        
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28'], runner=fake_runner, root=str(tmp_path))
        
    assert e.value.code == 0
    assert len(called_cmds) == 2
    
    out = capsys.readouterr().out
    assert "岩手県（03）完了済みのため飛ばします" in out
    
    # --force
    called_cmds.clear()
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28', '--force'], runner=fake_runner, root=str(tmp_path))
    assert e.value.code == 0
    assert len(called_cmds) == 3
    cmd_03 = [c for c in called_cmds if "03" in c][0]
    cmd_20 = [c for c in called_cmds if "20" in c][0]
    cmd_28 = [c for c in called_cmds if "28" in c][0]
    assert "--old=" in cmd_03
    assert "--old=" not in cmd_20
    assert "--old=" not in cmd_28
    for cmd in called_cmds:
        assert "--no-site" in cmd

def test_force_check_only_display(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    target_20 = [ '20' ] + NEIGHBORS['20']

    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    create_dummy_shapefiles(tmp_path, ['20'], target_20, 'rivers')

    # 03 は完了済みにする
    hist_03 = tmp_path / "output" / "update_history_03.csv"
    hist_03.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{
        '実行日時': '2026-10-07 20:00',
        '結果': '完了',
        '新データのファイル': 'data/raw/2026-09-24/denshouhi_20260924.csv'
    }]).to_csv(hist_03, index=False, encoding='utf-8-sig')

    fake_runner = MagicMock()

    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20', '--check-only', '--force'], runner=fake_runner, root=str(tmp_path))

    assert e.value.code == 0
    fake_runner.assert_not_called()

    out = capsys.readouterr().out
    assert "岩手県（03）163基　河川 4県分・海岸線 4県分　そろっています（完了済み・--force でやり直します）" in out

def test_failure(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    target_20 = [ '20' ] + NEIGHBORS['20']
    target_28 = [ '28' ] + NEIGHBORS['28']
    
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    create_dummy_shapefiles(tmp_path, ['20'], target_20, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'coastline')
    
    def fake_runner(cmd):
        res = MagicMock()
        if "20" in cmd:
            res.returncode = 1
        else:
            res.returncode = 0
        return res
        
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28'], runner=fake_runner, root=str(tmp_path))
        
    assert e.value.code == 1
    log_file = tmp_path / "output" / "batch_log.csv"
    df_log = pd.read_csv(log_file)
    assert len(df_log) == 3
    assert df_log.iloc[1]['結果'] == '失敗'
    
    out = capsys.readouterr().out
    assert "完了 2県／失敗 1県／飛ばした 0県" in out

def test_interrupt(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    target_20 = [ '20' ] + NEIGHBORS['20']
    target_28 = [ '28' ] + NEIGHBORS['28']
    
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    create_dummy_shapefiles(tmp_path, ['20'], target_20, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'rivers')
    create_dummy_shapefiles(tmp_path, ['28'], target_28, 'coastline')
    
    def fake_runner(cmd):
        if "20" in cmd:
            raise KeyboardInterrupt()
        res = MagicMock()
        res.returncode = 0
        return res
        
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28'], runner=fake_runner, root=str(tmp_path))
        
    assert e.value.code == 1
    log_file = tmp_path / "output" / "batch_log.csv"
    df_log = pd.read_csv(log_file)
    assert len(df_log) == 2
    assert df_log.iloc[1]['結果'] == '中断'
    
    out = capsys.readouterr().out
    assert "中断しました" in out

def test_api_calls(tmp_path, capsys):
    setup_mock_env(tmp_path)
    from src.prefectures import NEIGHBORS
    target_03 = [ '03' ] + NEIGHBORS['03']
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'rivers')
    create_dummy_shapefiles(tmp_path, ['03'], target_03, 'coastline')
    
    def fake_runner(cmd):
        cache_dir = tmp_path / "data" / "cache"
        elev_cache = cache_dir / "elevation_cache.csv"
        with open(elev_cache, "w") as f:
            f.write("lat,lon,elev,hsrc\n1,1,1,1\n2,2,2,2\n3,3,3,3\n")
            
        haz_dir = cache_dir / "hazard" / "test"
        haz_dir.mkdir(parents=True, exist_ok=True)
        (haz_dir / "h1.json").touch()
        (haz_dir / "h2.json").touch()
        
        land_dir = cache_dir / "landform" / "test"
        land_dir.mkdir(parents=True, exist_ok=True)
        (land_dir / "l1.json").touch()
        
        res = MagicMock()
        res.returncode = 0
        return res
        
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03'], runner=fake_runner, root=str(tmp_path))
        
    assert e.value.code == 0
        
    log_file = tmp_path / "output" / "batch_log.csv"
    df_log = pd.read_csv(log_file)
    assert df_log.iloc[0]['標高の問い合わせ'] == 3
    assert df_log.iloc[0]['ハザードタイルの取得'] == 2
    assert df_log.iloc[0]['地形分類タイルの取得'] == 1

def test_real_data(capsys, tmp_path):
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    date_dir = raw_dir / "2026-09-24"
    if not date_dir.exists():
        pytest.skip("実データなし")
        
    from src.add_river_coast import find_input_shapefiles
    
    missing_any = False
    for p in ['03', '20', '28']:
        _, _, missing = find_input_shapefiles(p, raw_dir)
        if missing:
            missing_any = True
            break
            
    if missing_any:
        pytest.skip("実シェープファイルなし")
        
    # Check if output is empty
    output_dir = project_root / "output"
    # To check that no files are modified or written in data/ and output/
    # we just run the command and then we can check. But we are not writing tests for file integrity unless asked. The instruction says:
    # このテストは output/ と data/ に何も書かないこと（--check-only は書かない作りのはず。確かめる）
    
    def get_mtimes(d):
        if not d.exists(): return {}
        return {f: f.stat().st_mtime for f in d.rglob('*') if f.is_file()}
        
    out_mtimes = get_mtimes(output_dir)
    data_mtimes = get_mtimes(project_root / "data")
    
    with pytest.raises(SystemExit) as e:
        main(['--pref', '03,20,28', '--check-only'])
        
    assert e.value.code == 0
    out = capsys.readouterr().out
    
    assert "一括実行の対象: 岩手県（03）、長野県（20）、兵庫県（28）（3県・377基）" in out
    assert "  岩手県（03）163基　河川 4県分・海岸線 4県分　そろっています" in out
    assert "  長野県（20）111基　河川 9県分・海岸線 なし（海のない県）　そろっています" in out
    assert "  兵庫県（28）103基　河川 5県分・海岸線 5県分　そろっています" in out
    
    new_out_mtimes = get_mtimes(output_dir)
    new_data_mtimes = get_mtimes(project_root / "data")
    
    assert out_mtimes == new_out_mtimes
    assert data_mtimes == new_data_mtimes
