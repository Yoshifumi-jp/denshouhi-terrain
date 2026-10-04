# -*- coding: utf-8 -*-
import pytest
import pandas as pd
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch

from src.summarize_hazard import calc_hazard_stats, summarize, check_files, main

def test_a_b_c_f_calc_hazard_stats():
    df_a = pd.DataFrame({
        '洪水_状態': ['区域内', '区域内', '区域外', '取得不可'],
        '洪水_浸水深': ['5m〜10m', '0.5m〜3m', '', '']
    })
    total, na, in_a, in_r, over3, over3_r = calc_hazard_stats(df_a, '洪水_', True)
    assert total == 3
    assert na == 1
    assert in_a == 2
    assert in_r == 0.667
    assert over3 == 1
    assert over3_r == 0.333
    
    df_b = pd.DataFrame({
        '洪水_状態': ['区域内']*8,
        '洪水_浸水深': ['0.3m未満', '0.5m未満', '0.5m〜1m', '0.5m〜3m', '3m〜5m', '5m〜10m', '10m〜20m', '20m以上']
    })
    total, na, in_a, in_r, over3, over3_r = calc_hazard_stats(df_b, '洪水_', True)
    assert total == 8
    assert in_a == 8
    assert over3 == 4
    
    df_c = pd.DataFrame({
        '土砂_状態': ['区域内'],
        '土砂_浸水深': ['']
    })
    total, na, in_a, in_r, over3, over3_r = calc_hazard_stats(df_c, '土砂_', False)
    assert over3 == ''
    assert over3_r == ''
    
    df_f = pd.DataFrame({
        '洪水_状態': ['取得不可']
    })
    total, na, in_a, in_r, over3, over3_r = calc_hazard_stats(df_f, '洪水_', True)
    assert total == 0
    assert na == 1
    assert in_a == 0
    assert in_r == ''
    assert over3 == 0
    assert over3_r == ''

def make_fake_data(base_dir):
    base_dir.mkdir(parents=True, exist_ok=True)
    m_main = base_dir / "monuments_99.csv"
    m_main.write_text("ID,碑名,所在地,伝承内容,種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\n1,碑1,場所1,移転した,1,0,1,0,0,0,0\n2,碑2,場所2,,0,1,1,0,0,0,0", encoding='utf-8-sig')
    
    m_haz = base_dir / "hazard_99.csv"
    m_haz.write_text("ID,洪水_状態,洪水_浸水深,津波_状態,津波_浸水深,高潮_状態,高潮_浸水深,土砂_状態\n1,区域内,5m〜10m,区域内,5m〜10m,区域外,,区域外\n2,区域外,,区域内,0.5m〜3m,区域外,,区域外", encoding='utf-8-sig')
    
    p_main = base_dir / "points_99.csv"
    p_main.write_text("ID,元の碑ID,種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他\np1,1,1,0,1,0,0,0,0\np2,2,0,1,1,0,0,0,0", encoding='utf-8-sig')
    
    p_haz = base_dir / "hazard_points_99.csv"
    p_haz.write_text("ID,元の碑ID,洪水_状態,洪水_浸水深,津波_状態,津波_浸水深,高潮_状態,高潮_浸水深,土砂_状態\np1,1,区域内,3m〜5m,区域内,3m〜5m,区域外,,区域外\np2,2,区域外,,区域内,0.5m〜3m,区域外,,区域外", encoding='utf-8-sig')

def test_d_e_f_g_main(tmp_path):
    base_dir = tmp_path / "data" / "processed"
    out_dir = tmp_path / "output"
    make_fake_data(base_dir)
    
    with patch("src.summarize_hazard.PREFECTURES", {"99": "テスト"}):
        summarize("99", base_dir, out_dir)
        
    out_csv = out_dir / "hazard_summary_99.csv"
    assert out_csv.exists()
    
    with open(out_csv, 'rb') as f:
        content = f.read()
        assert content.startswith(b'\xef\xbb\xbf') # utf-8-sig
        
    df = pd.read_csv(out_csv, encoding='utf-8-sig', skipfooter=2, engine='python')
    cols = ['範囲', '災害種別', 'ハザード', '碑_数', '碑_取得不可', '碑_区域内', '碑_区域内の割合', '碑_3m以上', '碑_3m以上の割合', '比較地点_数', '比較地点_取得不可', '比較地点_区域内', '比較地点_区域内の割合', '比較地点_3m以上', '比較地点_3m以上の割合']
    assert list(df.columns) == cols
    
    row_t = df[(df['範囲'] == '全碑') & (df['災害種別'] == '津波') & (df['ハザード'] == '津波')].iloc[0]
    assert row_t['碑_数'] == 2
    
    row_e = df[(df['範囲'] == '全碑') & (df['災害種別'] == '地震') & (df['ハザード'] == '津波')].iloc[0]
    assert row_e['碑_数'] == 1
    assert row_e['比較地点_数'] == 1
    
    row_f = df[(df['範囲'] == '全碑') & (df['災害種別'] == '洪水') & (df['ハザード'] == '洪水（想定最大規模）')].iloc[0]
    assert row_f['比較地点_数'] == 1
    
    row_t_ex = df[(df['範囲'] == '移転碑を除く') & (df['災害種別'] == '全種別') & (df['ハザード'] == '津波')].iloc[0]
    assert row_t_ex['比較地点_数'] == 1
    assert row_t_ex['比較地点_区域内'] == 1
    assert row_t_ex['比較地点_3m以上'] == 0
    
    row_t_ex2 = df[(df['範囲'] == '移転碑を除く') & (df['災害種別'] == '津波') & (df['ハザード'] == '津波')].iloc[0]
    assert row_t_ex2['碑_数'] == 1
    
    assert len(df[df['災害種別'] == '火山災害']) == 0
    
    # g 行の順：範囲 → 災害種別 → ハザード
    hazards = ['洪水（想定最大規模）', '津波', '高潮', '土砂災害']
    expected = []
    for r, types in [('全碑', ['全種別', '洪水', '地震', '津波']), ('移転碑を除く', ['全種別', '地震', '津波'])]:
        for t in types:
            for h in hazards:
                expected.append([r, t, h])
    assert df[['範囲', '災害種別', 'ハザード']].values.tolist() == expected
    
    with open(out_csv, 'r', encoding='utf-8-sig') as f:
        lines = f.read().splitlines()
    assert lines[-2] == '注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。'
    assert lines[-1] == '注：想定区域との重なりを示すもので、危険度の判定ではありません。出典：ハザードマップポータルサイト（加工して作成）'
    
    with patch("src.summarize_hazard.PREFECTURES", {"99": "テスト"}):
        summarize("99", base_dir, out_dir)
    with open(out_csv, 'rb') as f:
        content2 = f.read()
    assert content == content2

def test_h_missing_files(tmp_path, capsys):
    base_dir = tmp_path / "data" / "processed"
    base_dir.mkdir(parents=True, exist_ok=True)
    m_main = base_dir / "monuments_99.csv"
    m_main.touch()
    
    with pytest.raises(SystemExit) as exc:
        summarize("99", base_dir, tmp_path / "output")
    assert exc.value.code == 1
    
    out = capsys.readouterr().out
    assert "ファイルが見つかりません: hazard_99.csv" in out
    assert "先に実行してください: python src/add_hazard.py --pref 99" in out

def test_i_real_data():
    base_dir = Path(__file__).resolve().parent.parent / "data" / "processed"
    if not (base_dir / "monuments_36.csv").exists() or not (base_dir / "hazard_36.csv").exists():
        pytest.skip("実データなし")
        
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_out:
        summarize("36", base_dir, Path(tmp_out))
        
        df = pd.read_csv(Path(tmp_out) / "hazard_summary_36.csv", skipfooter=2, engine='python')
        assert len(df) == 56
        
        r1 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '全種別') & (df['ハザード'] == '洪水（想定最大規模）')].iloc[0]
        assert (r1['碑_数'], r1['碑_区域内'], r1['碑_区域内の割合'], r1['碑_3m以上'], r1['碑_3m以上の割合']) == (71.0, 16.0, 0.225, 4.0, 0.056)
        assert (r1['比較地点_数'], r1['比較地点_区域内'], r1['比較地点_区域内の割合'], r1['比較地点_3m以上'], r1['比較地点_3m以上の割合']) == (349.0, 53.0, 0.152, 28.0, 0.08)
        
        r2 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '全種別') & (df['ハザード'] == '津波')].iloc[0]
        assert (r2['碑_数'], r2['碑_区域内'], r2['碑_区域内の割合'], r2['碑_3m以上'], r2['碑_3m以上の割合']) == (71.0, 50.0, 0.704, 39.0, 0.549)
        assert (r2['比較地点_数'], r2['比較地点_区域内'], r2['比較地点_区域内の割合'], r2['比較地点_3m以上'], r2['比較地点_3m以上の割合']) == (349.0, 75.0, 0.215, 37.0, 0.106)

        r3 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '全種別') & (df['ハザード'] == '高潮')].iloc[0]
        assert (r3['碑_数'], r3['碑_区域内'], r3['碑_区域内の割合'], r3['碑_3m以上'], r3['碑_3m以上の割合']) == (71.0, 24.0, 0.338, 0.0, 0.0)
        assert (r3['比較地点_数'], r3['比較地点_区域内'], r3['比較地点_区域内の割合'], r3['比較地点_3m以上'], r3['比較地点_3m以上の割合']) == (349.0, 53.0, 0.152, 1.0, 0.003)

        r4 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '全種別') & (df['ハザード'] == '土砂災害')].iloc[0]
        assert (r4['碑_数'], r4['碑_区域内'], r4['碑_区域内の割合']) == (71.0, 22.0, 0.31)
        assert pd.isna(r4['碑_3m以上'])
        assert (r4['比較地点_数'], r4['比較地点_区域内'], r4['比較地点_区域内の割合']) == (349.0, 30.0, 0.086)

        r5 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '津波') & (df['ハザード'] == '津波')].iloc[0]
        assert (r5['碑_数'], r5['碑_区域内'], r5['碑_区域内の割合'], r5['碑_3m以上'], r5['碑_3m以上の割合']) == (49.0, 46.0, 0.939, 38.0, 0.776)
        assert (r5['比較地点_数'], r5['比較地点_区域内'], r5['比較地点_区域内の割合'], r5['比較地点_3m以上'], r5['比較地点_3m以上の割合']) == (239.0, 60.0, 0.251, 37.0, 0.155)

        r6 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '洪水') & (df['ハザード'] == '洪水（想定最大規模）')].iloc[0]
        assert (r6['碑_数'], r6['碑_区域内'], r6['碑_区域内の割合'], r6['碑_3m以上'], r6['碑_3m以上の割合']) == (10.0, 8.0, 0.8, 4.0, 0.4)
        assert (r6['比較地点_数'], r6['比較地点_区域内'], r6['比較地点_区域内の割合'], r6['比較地点_3m以上'], r6['比較地点_3m以上の割合']) == (50.0, 28.0, 0.56, 24.0, 0.48)

        r7 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '土砂災害') & (df['ハザード'] == '土砂災害')].iloc[0]
        assert (r7['碑_数'], r7['碑_区域内'], r7['碑_区域内の割合']) == (8.0, 4.0, 0.5)
        assert (r7['比較地点_数'], r7['比較地点_区域内'], r7['比較地点_区域内の割合']) == (40.0, 4.0, 0.1)

        r8 = df[(df['範囲'] == '全碑') & (df['災害種別'] == '高潮') & (df['ハザード'] == '高潮')].iloc[0]
        assert (r8['碑_数'], r8['碑_区域内'], r8['碑_区域内の割合'], r8['碑_3m以上'], r8['碑_3m以上の割合']) == (2.0, 2.0, 1.0, 0.0, 0.0)
        assert (r8['比較地点_数'], r8['比較地点_区域内'], r8['比較地点_区域内の割合'], r8['比較地点_3m以上'], r8['比較地点_3m以上の割合']) == (10.0, 0.0, 0.0, 0.0, 0.0)

        r9 = df[(df['範囲'] == '移転碑を除く') & (df['災害種別'] == '全種別') & (df['ハザード'] == '洪水（想定最大規模）')].iloc[0]
        assert (r9['碑_数'], r9['碑_区域内'], r9['碑_区域内の割合'], r9['碑_3m以上'], r9['碑_3m以上の割合']) == (69.0, 15.0, 0.217, 4.0, 0.058)
        assert (r9['比較地点_数'], r9['比較地点_区域内'], r9['比較地点_区域内の割合'], r9['比較地点_3m以上'], r9['比較地点_3m以上の割合']) == (339.0, 50.0, 0.147, 28.0, 0.083)

        r10 = df[(df['範囲'] == '移転碑を除く') & (df['災害種別'] == '全種別') & (df['ハザード'] == '津波')].iloc[0]
        assert (r10['碑_数'], r10['碑_区域内'], r10['碑_区域内の割合'], r10['碑_3m以上'], r10['碑_3m以上の割合']) == (69.0, 48.0, 0.696, 38.0, 0.551)
        assert (r10['比較地点_数'], r10['比較地点_区域内'], r10['比較地点_区域内の割合'], r10['比較地点_3m以上'], r10['比較地点_3m以上の割合']) == (339.0, 70.0, 0.206, 36.0, 0.106)
        
        assert r1['碑_数'] + r1['碑_取得不可'] == 71.0

def test_j_script_launch():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
    res = subprocess.run([sys.executable, "src/summarize_hazard.py", "--pref", "00"], cwd=str(Path(__file__).parent.parent), capture_output=True, env=env)
    assert res.returncode == 1
    stdout_str = res.stdout.decode('cp932', errors='replace')
    assert "エラー: --pref には 01" in stdout_str and "47" in stdout_str

def test_k_sys_argv(tmp_path):
    base_dir = tmp_path / "data" / "processed"
    out_dir = tmp_path / "output"
    make_fake_data(base_dir)
    
    with patch("src.summarize_hazard.check_files") as mock_check, \
         patch("src.summarize_hazard.PREFECTURES", {"99": "テスト"}), \
         patch.object(sys, 'argv', ["pytest", "-q", "tests/xxx.py"]):
        mock_check.return_value = (base_dir / "monuments_99.csv", base_dir / "hazard_99.csv", base_dir / "points_99.csv", base_dir / "hazard_points_99.csv")
        with patch("src.summarize_hazard.get_project_root") as mock_root:
            mock_root.return_value = tmp_path
            main(["--pref", "99"])
            
    assert (out_dir / "hazard_summary_99.csv").exists()

def test_l_shinsui_3m_ijou():
    from src.hazard_layers import SHINSUI_3M_IJOU
    assert SHINSUI_3M_IJOU == ['3m〜5m', '5m〜10m', '10m〜20m', '20m以上']
