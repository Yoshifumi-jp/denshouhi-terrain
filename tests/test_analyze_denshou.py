import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from src.analyze_denshou import (
    parse_disasters, parse_built_year, classify_monument, main, check_files_exist_local,
    load_inputs, build_denshou_table, build_summary, build_groups, PROJECT_ROOT,
    choose_yscale, draw_group_axis
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def test_choose_yscale():
    assert choose_yscale([1, 10, 100]) == "log"
    assert choose_yscale([0, 5]) == "linear"
    assert choose_yscale([-1.5, 3]) == "linear"
    assert choose_yscale([]) == "linear"

def test_draw_group_axis():
    # 対数スケールのテスト
    fig, ax = plt.subplots()
    draw_group_axis(ax, [[1, 2], [3, 4]], ["A", "B"], "標高")
    assert ax.get_yscale() == "log"
    assert "対数目盛" in ax.get_ylabel()
    plt.close(fig)
    
    # 線形スケールのテスト
    fig, ax = plt.subplots()
    draw_group_axis(ax, [[0, 2], [3, 4]], ["A", "B"], "標高")
    assert ax.get_yscale() == "linear"
    assert "対数目盛" not in ax.get_ylabel()
    plt.close(fig)

def test_parse_disasters():
    cases = [
        ("安政南海地震(1854年12月24日)", [("安政南海地震", 1854)]),
        ("昭和南海地震（１９４６年１２月２１日）", [("昭和南海地震", 1946)]),
        ("正平南海地震(1361年7月26日(ユリウス暦))", [("正平南海地震", 1361)]),
        ("昭和29年台風12号(ジューン台風)(1954年9月13日～14日)", [("昭和29年台風12号(ジューン台風)", 1954)]),
        ("安政南海地震(1854年12月24日)大正元年の台風(1912年9月22日～23日)", [("安政南海地震", 1854), ("大正元年の台風", 1912)]),
        ("安政東海地震(1854年12月23日)　安政南海地震(1854年12月24日)", [("安政東海地震", 1854), ("安政南海地震", 1854)]),
        ("昭和南海地震(1946年12月21日)ほか", [("昭和南海地震", 1946)]),
        ("慶応2年の寅年の大水(1866年)慶応3年の洪水(1867年)", [("慶応2年の寅年の大水", 1866), ("慶応3年の洪水", 1867)]),
        ("貞観地震(869年7月13日)", [("貞観地震", 869)]),
        ("地震", []),
        ("", [])
    ]
    for inp, expected in cases:
        assert parse_disasters(inp) == expected

def test_parse_built_year():
    assert parse_built_year("1861") == 1861
    assert parse_built_year("１８６１") == 1861
    assert parse_built_year("不明") is None
    assert parse_built_year("") is None
    assert parse_built_year("1664(慶長碑)、不明(宝永碑)") == 1664
    assert parse_built_year("1900年頃") == 1900

def test_build_denshou_table():
    rows = [
        {"ID": "3", "碑名": "C", "災害名": "宝永地震(1707年)", "建立年": "1700"},
        {"ID": "1", "碑名": "A", "災害名": "安政南海地震(1854年)", "建立年": "1861"},
        {"ID": "4", "碑名": "D", "災害名": "安政南海地震(1854年)", "建立年": "不明"},
        {"ID": "2", "碑名": "B", "災害名": "安政南海地震(1854年)", "建立年": "1854"},
        {"ID": "6", "碑名": "F", "災害名": "安政(1854年)大正(1912年)", "建立年": "1913"},
        {"ID": "5", "碑名": "E", "災害名": "地震", "建立年": "1800"},
        {"ID": "7", "碑名": "G", "災害名": "慶長地震(1605年)", "建立年": "1664(慶長碑)、不明(宝永碑)"}
    ]
    df = pd.DataFrame(rows)
    res_df = build_denshou_table(df)
    
    assert res_df['ID'].tolist() == ["1", "2", "3", "4", "5", "6", "7"]
    assert res_df.loc[res_df['ID'] == '1', '区分'].values[0] == "差あり"
    assert res_df.loc[res_df['ID'] == '1', '建立までの年数'].values[0] == 7
    assert res_df.loc[res_df['ID'] == '1', '年の数'].values[0] == 1
    assert res_df.loc[res_df['ID'] == '1', '発生年'].values[0] == 1854
    assert res_df.loc[res_df['ID'] == '1', '注記'].values[0] == ""
    
    assert res_df.loc[res_df['ID'] == '2', '区分'].values[0] == "差あり"
    assert res_df.loc[res_df['ID'] == '2', '建立までの年数'].values[0] == 0
    assert res_df.loc[res_df['ID'] == '3', '区分'].values[0] == "災害前の建立"
    assert res_df.loc[res_df['ID'] == '3', '建立までの年数'].values[0] == -7
    assert res_df.loc[res_df['ID'] == '4', '区分'].values[0] == "対象外（建立年不明）"
    assert res_df.loc[res_df['ID'] == '5', '区分'].values[0] == "不明（災害名に年なし）"
    
    assert res_df.loc[res_df['ID'] == '6', '区分'].values[0] == "差あり"
    assert res_df.loc[res_df['ID'] == '6', '建立までの年数'].values[0] == 59
    assert res_df.loc[res_df['ID'] == '6', '年の数'].values[0] == 2
    assert res_df.loc[res_df['ID'] == '6', '発生年'].values[0] == 1854
    assert res_df.loc[res_df['ID'] == '6', '注記'].values[0] == "複数の災害（最も古い年を使用）"
    
    assert res_df.loc[res_df['ID'] == '7', '注記'].values[0] == "建立年の記載に注記あり（最も古い年を使用）"

def test_build_summary():
    rows = [
        {"ID": "1", "碑名": "A", "災害名": "安政南海地震(1854年)", "建立年": "1861"},
        {"ID": "2", "碑名": "B", "災害名": "安政南海地震(1854年)", "建立年": "1854"},
        {"ID": "3", "碑名": "C", "災害名": "宝永地震(1707年)", "建立年": "1700"},
        {"ID": "4", "碑名": "D", "災害名": "安政南海地震(1854年)", "建立年": "不明"},
        {"ID": "5", "碑名": "E", "災害名": "地震", "建立年": "1800"},
        {"ID": "6", "碑名": "F", "災害名": "安政(1854年)大正(1912年)", "建立年": "1913"},
        {"ID": "7", "碑名": "G", "災害名": "慶長地震(1605年)", "建立年": "1664(慶長碑)、不明(宝永碑)"}
    ]
    df = pd.DataFrame(rows)
    res_df = build_denshou_table(df)
    sum_df = build_summary(res_df)
    
    row_all = sum_df[sum_df['主な種別'] == '全種別'].iloc[0]
    assert row_all['碑の数'] == 7
    assert row_all['差あり'] == 4
    assert row_all['災害前の建立'] == 1
    assert row_all['対象外（建立年不明）'] == 1
    assert row_all['不明（災害名に年なし）'] == 1
    
    assert row_all['年数_中央値'] == 33.0  # 0, 7, 59, 59 -> med is 33.0
    assert row_all['年数_最小'] == 0
    assert row_all['年数_最大'] == 59

def test_build_groups():
    data = [
        {"ID": "1", "災害名": "A(1800年)", "標高_m": 10, "取得状態": "取得済", "海岸までの距離_m": 100, "海岸_状態": "取得済"},
        {"ID": "2", "災害名": "A(1800年)", "標高_m": 20, "取得状態": "取得不可", "海岸までの距離_m": 200, "海岸_状態": "取得済"},
        {"ID": "3", "災害名": "A(1800年)B(1900年)", "標高_m": 30, "取得状態": "取得済", "海岸までの距離_m": 300, "海岸_状態": "取得済"},
        {"ID": "4", "災害名": "C(1850年)", "標高_m": 40, "取得状態": "取得済", "海岸までの距離_m": 400, "海岸_状態": "取得済"},
        {"ID": "5", "災害名": "C(1850年)", "標高_m": 50, "取得状態": "取得済", "海岸までの距離_m": 500, "海岸_状態": "取得済"},
        {"ID": "6", "災害名": "D(1800年)", "標高_m": 60, "取得状態": "取得済", "海岸までの距離_m": 600, "海岸_状態": "取得済"},
        {"ID": "7", "災害名": "D(1800年)", "標高_m": 70, "取得状態": "取得済", "海岸までの距離_m": 700, "海岸_状態": "取得済"},
    ]
    df = pd.DataFrame(data)
    g_df = build_groups(df)
    
    # A(1800)の確認
    row_a = g_df[g_df['災害の名前'] == 'A'].iloc[0]
    assert row_a['碑の数'] == 3
    assert row_a['標高_中央値'] == 20.0
    assert row_a['標高_最小'] == 10.0
    assert row_a['標高_最大'] == 30.0
    assert row_a['標高_除外数'] == 1
    assert row_a['海岸までの距離_中央値'] == 200.0
    assert row_a['碑のID'] == "1；2；3"
    
    # 順序: 件数の降順 -> 年の昇順 -> 名前の昇順
    # A(1800): 3件
    # C(1850): 2件
    # D(1800): 2件
    # B(1900): 1件
    
    names = g_df['災害の名前'].tolist()
    assert names == ["A", "D", "C", "B"]

def test_main_with_dummy_data(monkeypatch, tmp_path):
    import src.analyze_denshou
    import src.prefectures
    
    monkeypatch.setattr(src.analyze_denshou, "PROJECT_ROOT", tmp_path)
    monkeypatch.setitem(src.prefectures.PREFECTURES, "99", "テスト県")
    
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    mon_df = pd.DataFrame([
        {"ID": "001", "碑名": "碑1", "災害名": "テスト災害(2000年)", "建立年": "2005", "種別_津波": 1, "緯度": 35.0, "経度": 135.0},
        {"ID": "002", "碑名": "碑2", "災害名": "テスト災害(2000年)", "建立年": "2010", "種別_洪水": 1, "緯度": 35.1, "経度": 135.1},
        {"ID": "003", "碑名": "碑3", "災害名": "テスト災害(2000年)", "建立年": "2015", "種別_津波": 1, "緯度": 35.2, "経度": 135.2},
        {"ID": "004", "碑名": "碑4", "災害名": "テスト災害(2000年)", "建立年": "2020", "種別_津波": 1, "緯度": 35.3, "経度": 135.3},
        {"ID": "005", "碑名": "碑5", "災害名": "テスト災害(2000年)", "建立年": "2025", "種別_津波": 1, "緯度": 35.4, "経度": 135.4}
    ])
    mon_df.to_csv(data_dir / "monuments_99.csv", index=False, encoding="utf-8-sig")
    
    elev_df = pd.DataFrame([{"ID": f"00{i}", "標高_m": i*10, "取得状態": "取得済"} for i in range(1, 6)])
    elev_df.to_csv(data_dir / "elevation_99.csv", index=False, encoding="utf-8-sig")
    
    rc_df = pd.DataFrame([{"ID": f"00{i}", "海岸までの距離_m": i*100, "海岸_状態": "取得済"} for i in range(1, 6)])
    rc_df.to_csv(data_dir / "river_coast_99.csv", index=False, encoding="utf-8-sig")
    
    src.analyze_denshou.main(["--pref", "99"])
    out_dir = tmp_path / "output"
    
    content1 = (out_dir / "denshou_99.csv").read_bytes()
    src.analyze_denshou.main(["--pref", "99"])
    content2 = (out_dir / "denshou_99.csv").read_bytes()
    assert content1 == content2
    assert content1.startswith(b'\xef\xbb\xbf')
    
    res_df = pd.read_csv(out_dir / "denshou_99.csv", dtype={'ID': str})
    assert res_df.loc[0, '建立までの年数'] == 5
    
    sum_df = pd.read_csv(out_dir / "denshou_summary_99.csv")
    assert sum_df.loc[0, '碑の数'] == 5
    
    g_df = pd.read_csv(out_dir / "disaster_groups_99.csv")
    assert g_df.loc[0, '災害の名前'] == 'テスト災害'
    
    monkeypatch.setattr("sys.argv", ["pytest", "-q", "tests/xxx.py"])
    src.analyze_denshou.main(["--pref", "99"])

def test_errors():
    import src.analyze_denshou
    with pytest.raises(SystemExit) as e:
        src.analyze_denshou.main(["--pref", "all"])
    assert e.value.code == 1
    
    with pytest.raises(SystemExit) as e:
        src.analyze_denshou.main(["--pref", "00"])
    assert e.value.code == 1
    
    with pytest.raises(SystemExit) as e:
        src.analyze_denshou.main(["--pref", "48"])
    assert e.value.code == 1
    
def test_missing_files(monkeypatch, tmp_path, capsys):
    import src.analyze_denshou
    import src.prefectures
    
    monkeypatch.setattr(src.analyze_denshou, "PROJECT_ROOT", tmp_path)
    monkeypatch.setitem(src.prefectures.PREFECTURES, "99", "テスト県")
    
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    pd.DataFrame({"ID": []}).to_csv(data_dir / "monuments_99.csv", index=False)
    
    with pytest.raises(SystemExit) as e:
        src.analyze_denshou.main(["--pref", "99"])
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "ファイルが見つかりません: elevation_99.csv" in captured.out
    assert "先に実行してください: python src/add_elevation.py --pref 99" in captured.out

def test_real_data():
    base_dir = PROJECT_ROOT / "data" / "processed"
    if not (base_dir / "monuments_36.csv").exists():
        pytest.skip("No real data for 36")
        
    df = load_inputs("36", PROJECT_ROOT)
    res = build_denshou_table(df)
    sum_df = build_summary(res)
    groups = build_groups(df)
    
    assert len(res) == 71
    c_diff = len(res[res['区分'] == '差あり'])
    c_pre = len(res[res['区分'] == '災害前の建立'])
    c_out = len(res[res['区分'] == '対象外（建立年不明）'])
    c_unk = len(res[res['区分'] == '不明（災害名に年なし）'])
    
    assert c_diff == 62
    assert c_pre == 0
    assert c_out == 9
    assert c_unk == 0
    assert len(res[res['年の数'] >= 2]) == 10
    
    row_all = sum_df[sum_df['主な種別'] == '全種別'].iloc[0]
    assert abs(row_all['年数_中央値'] - 39.0) < 0.01
    assert abs(row_all['年数_第1四分位'] - 7.25) < 0.01
    assert abs(row_all['年数_第3四分位'] - 49.0) < 0.01
    assert row_all['年数_最小'] == 0
    assert row_all['年数_最大'] == 150
    
    def check_type(t, count, med_val):
        row = sum_df[sum_df['主な種別'] == t]
        if count == 0:
            assert len(row) == 0
        else:
            assert len(row) == 1
            assert row.iloc[0]['差あり'] == count
            assert abs(row.iloc[0]['年数_中央値'] - med_val) < 0.01
            
    check_type("津波", 44, 39.0)
    check_type("洪水", 6, 40.0)
    check_type("土砂災害", 8, 6.5)
    check_type("地震", 2, 12.5)
    check_type("高潮", 1, 1.0)
    check_type("その他", 1, 0.0)
    
    r201 = res[res['ID'] == '36201-001'].iloc[0]
    assert r201['建立までの年数'] == 7
    
    r387_005 = res[res['ID'] == '36387-005'].iloc[0]
    assert r387_005['建立までの年数'] == 19
    
    r403_001 = res[res['ID'] == '36403-001'].iloc[0]
    assert r403_001['建立までの年数'] == 2
    assert r403_001['年の数'] == 2
    
    r388_012 = res[res['ID'] == '36388-012'].iloc[0]
    assert r388_012['建立までの年数'] == 59
    assert "建立年の記載に注記あり" in r388_012['注記']
    
    r387_003 = res[res['ID'] == '36387-003'].iloc[0]
    assert r387_003['建立までの年数'] == 59
    assert r387_003['年の数'] == 2
    
    r387_001 = res[res['ID'] == '36387-001'].iloc[0]
    assert r387_001['建立までの年数'] == 0
    
    def check_group(n, y, count, em=None, cm=None):
        r = groups[(groups['災害の名前'] == n) & (groups['発生年'] == y)]
        assert len(r) == 1
        r = r.iloc[0]
        assert r['碑の数'] == count
        if em is not None:
            assert abs(r['標高_中央値'] - em) < 0.01
            assert abs(r['海岸までの距離_中央値'] - cm) < 0.01
            
    check_group("昭和南海地震", 1946, 28, 3.1, 117.5)
    check_group("安政南海地震", 1854, 20, 5.15, 131.5)
    check_group("安政東海地震", 1854, 6)
