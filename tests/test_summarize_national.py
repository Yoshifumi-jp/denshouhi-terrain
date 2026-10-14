# -*- coding: utf-8 -*-
import pytest
import pandas as pd

from src.prefectures import PREFECTURES
from src.summarize import extract_relocated
from src.summarize_national import (
    get_project_root,
    load_pref,
    check_all_files,
    build_summary_tables,
    build_hazard_table,
    build_pref_counts,
    decade_label,
    build_years_table,
    main,
)


def create_dummy_pref_data(tmp_path):
    """tmp_path 配下に 01, 02 の2県分のダミー processed ファイル群を作成する"""
    proc_dir = tmp_path / "data" / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)

    # 01 (北海道): 碑3基、比較地点6点、移転碑2基
    mon_01 = pd.DataFrame({
        'ID': ['01001', '01002', '01003'],
        '碑名': ['碑1', '碑2', '碑3'],
        '所在地': ['所1', '所2', '所3'],
        '伝承内容': ['移転した記録', '移設された記録', 'そのまま残る'],
        '種別_洪水': [1, 0, 1],
        '種別_地震': [0, 1, 0],
        '種別_津波': [1, 0, 0],
        '種別_土砂災害': [0, 0, 1],
        '種別_高潮': [0, 0, 0],
        '種別_火山災害': [0, 0, 0],
        '種別_その他': [0, 0, 0],
    })
    elev_01 = pd.DataFrame({
        'ID': ['01001', '01002', '01003'],
        '標高_m': [10.0, 20.0, 30.0],
        '傾斜_度': [1.0, 2.0, 3.0],
        '取得状態': ['取得済', '取得済', '取得済']
    })
    rc_01 = pd.DataFrame({
        'ID': ['01001', '01002', '01003'],
        '河川までの距離_m': [100.0, 200.0, 300.0],
        '河川との高さの差_m': [1.0, 2.0, 3.0],
        '河川_状態': ['取得済', '取得済', '取得済'],
        '海岸までの距離_m': [500.0, 600.0, 700.0],
        '海岸_状態': ['取得済', '取得済', '取得済']
    })
    lf_01 = pd.DataFrame({
        'ID': ['01001', '01002', '01003'],
        '地形分類名': ['氾濫平野', '山地斜面等', '台地'],
        '地形分類コード': ['1', '2', '3'],
        '地形分類_状態': ['取得済', '取得済', '取得済']
    })
    haz_01 = pd.DataFrame({
        'ID': ['01001', '01002', '01003'],
        '洪水_状態': ['区域内', '区域外', '区域内'],
        '洪水_浸水深': ['0.5m〜3.0m未満', '', '3.0m〜5.0m未満'],
        '津波_状態': ['区域内', '区域外', '区域外'],
        '津波_浸水深': ['3.0m〜5.0m未満', '', ''],
        '高潮_状態': ['区域外', '区域外', '区域外'],
        '高潮_浸水深': ['', '', ''],
        '土砂_状態': ['区域外', '区域外', '区域内']
    })

    pts_01 = pd.DataFrame({
        'ID': ['01001-P1', '01001-P2', '01002-P1', '01002-P2', '01003-P1', '01003-P2'],
        '元の碑ID': ['01001', '01001', '01002', '01002', '01003', '01003'],
        '碑名': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
        '所在地': ['所1', '所1', '所2', '所2', '所3', '所3'],
        '種別_洪水': [1, 1, 0, 0, 1, 1],
        '種別_地震': [0, 0, 1, 1, 0, 0],
        '種別_津波': [1, 1, 0, 0, 0, 0],
        '種別_土砂災害': [0, 0, 0, 0, 1, 1],
        '種別_高潮': [0, 0, 0, 0, 0, 0],
        '種別_火山災害': [0, 0, 0, 0, 0, 0],
        '種別_その他': [0, 0, 0, 0, 0, 0],
    })
    elev_pts_01 = pd.DataFrame({
        'ID': ['01001-P1', '01001-P2', '01002-P1', '01002-P2', '01003-P1', '01003-P2'],
        '標高_m': [12.0, 14.0, 22.0, 24.0, 32.0, 34.0],
        '傾斜_度': [1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
        '取得状態': ['取得済', '取得済', '取得済', '取得済', '取得済', '取得済']
    })
    rc_pts_01 = pd.DataFrame({
        'ID': ['01001-P1', '01001-P2', '01002-P1', '01002-P2', '01003-P1', '01003-P2'],
        '河川までの距離_m': [110.0, 120.0, 210.0, 220.0, 310.0, 320.0],
        '河川との高さの差_m': [1.5, 1.8, 2.5, 2.8, 3.5, 3.8],
        '河川_状態': ['取得済', '取得済', '取得済', '取得済', '取得済', '取得済'],
        '海岸までの距離_m': [510.0, 520.0, 610.0, 620.0, 710.0, 720.0],
        '海岸_状態': ['取得済', '取得済', '取得済', '取得済', '取得済', '取得済']
    })
    lf_pts_01 = pd.DataFrame({
        'ID': ['01001-P1', '01001-P2', '01002-P1', '01002-P2', '01003-P1', '01003-P2'],
        '地形分類名': ['氾濫平野', '氾濫平野', '山地斜面等', '山地斜面等', '台地', '台地'],
        '地形分類コード': ['1', '1', '2', '2', '3', '3'],
        '地形分類_状態': ['取得済', '取得済', '取得済', '取得済', '取得済', '取得済']
    })
    haz_pts_01 = pd.DataFrame({
        'ID': ['01001-P1', '01001-P2', '01002-P1', '01002-P2', '01003-P1', '01003-P2'],
        '洪水_状態': ['区域内', '区域外', '区域外', '区域外', '区域内', '区域外'],
        '洪水_浸水深': ['0.5m〜3.0m未満', '', '', '', '3.0m〜5.0m未満', ''],
        '津波_状態': ['区域内', '区域外', '区域外', '区域外', '区域外', '区域外'],
        '津波_浸水深': ['3.0m〜5.0m未満', '', '', '', '', ''],
        '高潮_状態': ['区域外', '区域外', '区域外', '区域外', '区域外', '区域外'],
        '高潮_浸水深': ['', '', '', '', '', ''],
        '土砂_状態': ['区域外', '区域外', '区域外', '区域外', '区域外', '区域外']
    })

    mon_01.to_csv(proc_dir / "monuments_01.csv", index=False, encoding='utf-8-sig')
    elev_01.to_csv(proc_dir / "elevation_01.csv", index=False, encoding='utf-8-sig')
    rc_01.to_csv(proc_dir / "river_coast_01.csv", index=False, encoding='utf-8-sig')
    lf_01.to_csv(proc_dir / "landform_01.csv", index=False, encoding='utf-8-sig')
    haz_01.to_csv(proc_dir / "hazard_01.csv", index=False, encoding='utf-8-sig')

    pts_01.to_csv(proc_dir / "points_01.csv", index=False, encoding='utf-8-sig')
    elev_pts_01.to_csv(proc_dir / "elevation_points_01.csv", index=False, encoding='utf-8-sig')
    rc_pts_01.to_csv(proc_dir / "river_coast_points_01.csv", index=False, encoding='utf-8-sig')
    lf_pts_01.to_csv(proc_dir / "landform_points_01.csv", index=False, encoding='utf-8-sig')
    haz_pts_01.to_csv(proc_dir / "hazard_points_01.csv", index=False, encoding='utf-8-sig')

    # 02 (青森県): 碑2基、比較地点4点、移転碑0基
    mon_02 = pd.DataFrame({
        'ID': ['02001', '02002'],
        '碑名': ['碑A', '碑B'],
        '所在地': ['所A', '所B'],
        '伝承内容': ['昔の高潮', '火山の記憶'],
        '種別_洪水': [0, 0],
        '種別_地震': [0, 0],
        '種別_津波': [0, 0],
        '種別_土砂災害': [0, 0],
        '種別_高潮': [1, 0],
        '種別_火山災害': [0, 1],
        '種別_その他': [0, 1],
    })
    elev_02 = pd.DataFrame({
        'ID': ['02001', '02002'],
        '標高_m': [5.0, 100.0],
        '傾斜_度': [0.5, 15.0],
        '取得状態': ['取得済', '取得済']
    })
    rc_02 = pd.DataFrame({
        'ID': ['02001', '02002'],
        '河川までの距離_m': [50.0, 500.0],
        '河川との高さの差_m': [0.5, 20.0],
        '河川_状態': ['取得済', '取得済'],
        '海岸までの距離_m': [100.0, 5000.0],
        '海岸_状態': ['取得済', '取得済']
    })
    lf_02 = pd.DataFrame({
        'ID': ['02001', '02002'],
        '地形分類名': ['海岸平野', '山地斜面等'],
        '地形分類コード': ['1', '2'],
        '地形分類_状態': ['取得済', '取得済']
    })
    haz_02 = pd.DataFrame({
        'ID': ['02001', '02002'],
        '洪水_状態': ['区域外', '区域外'],
        '洪水_浸水深': ['', ''],
        '津波_状態': ['区域外', '区域外'],
        '津波_浸水深': ['', ''],
        '高潮_状態': ['区域内', '区域外'],
        '高潮_浸水深': ['3.0m〜5.0m未満', ''],
        '土砂_状態': ['区域外', '区域外']
    })

    pts_02 = pd.DataFrame({
        'ID': ['02001-P1', '02001-P2', '02002-P1', '02002-P2'],
        '元の碑ID': ['02001', '02001', '02002', '02002'],
        '碑名': ['PA1', 'PA2', 'PB1', 'PB2'],
        '所在地': ['所A', '所A', '所B', '所B'],
        '種別_洪水': [0, 0, 0, 0],
        '種別_地震': [0, 0, 0, 0],
        '種別_津波': [0, 0, 0, 0],
        '種別_土砂災害': [0, 0, 0, 0],
        '種別_高潮': [1, 1, 0, 0],
        '種別_火山災害': [0, 0, 1, 1],
        '種別_その他': [0, 0, 1, 1],
    })
    elev_pts_02 = pd.DataFrame({
        'ID': ['02001-P1', '02001-P2', '02002-P1', '02002-P2'],
        '標高_m': [6.0, 7.0, 105.0, 110.0],
        '傾斜_度': [0.6, 0.7, 16.0, 17.0],
        '取得状態': ['取得済', '取得済', '取得済', '取得済']
    })
    rc_pts_02 = pd.DataFrame({
        'ID': ['02001-P1', '02001-P2', '02002-P1', '02002-P2'],
        '河川までの距離_m': [60.0, 70.0, 510.0, 520.0],
        '河川との高さの差_m': [0.6, 0.7, 21.0, 22.0],
        '河川_状態': ['取得済', '取得済', '取得済', '取得済'],
        '海岸までの距離_m': [110.0, 120.0, 5100.0, 5200.0],
        '海岸_状態': ['取得済', '取得済', '取得済', '取得済']
    })
    lf_pts_02 = pd.DataFrame({
        'ID': ['02001-P1', '02001-P2', '02002-P1', '02002-P2'],
        '地形分類名': ['海岸平野', '海岸平野', '山地斜面等', '山地斜面等'],
        '地形分類コード': ['1', '1', '2', '2'],
        '地形分類_状態': ['取得済', '取得済', '取得済', '取得済']
    })
    haz_pts_02 = pd.DataFrame({
        'ID': ['02001-P1', '02001-P2', '02002-P1', '02002-P2'],
        '洪水_状態': ['区域外', '区域外', '区域外', '区域外'],
        '洪水_浸水深': ['', '', '', ''],
        '津波_状態': ['区域外', '区域外', '区域外', '区域外'],
        '津波_浸水深': ['', '', '', ''],
        '高潮_状態': ['区域内', '区域外', '区域外', '区域外'],
        '高潮_浸水深': ['0.5m〜3.0m未満', '', '', ''],
        '土砂_状態': ['区域外', '区域外', '区域外', '区域外']
    })

    mon_02.to_csv(proc_dir / "monuments_02.csv", index=False, encoding='utf-8-sig')
    elev_02.to_csv(proc_dir / "elevation_02.csv", index=False, encoding='utf-8-sig')
    rc_02.to_csv(proc_dir / "river_coast_02.csv", index=False, encoding='utf-8-sig')
    lf_02.to_csv(proc_dir / "landform_02.csv", index=False, encoding='utf-8-sig')
    haz_02.to_csv(proc_dir / "hazard_02.csv", index=False, encoding='utf-8-sig')

    pts_02.to_csv(proc_dir / "points_02.csv", index=False, encoding='utf-8-sig')
    elev_pts_02.to_csv(proc_dir / "elevation_points_02.csv", index=False, encoding='utf-8-sig')
    rc_pts_02.to_csv(proc_dir / "river_coast_points_02.csv", index=False, encoding='utf-8-sig')
    lf_pts_02.to_csv(proc_dir / "landform_points_02.csv", index=False, encoding='utf-8-sig')
    haz_pts_02.to_csv(proc_dir / "hazard_points_02.csv", index=False, encoding='utf-8-sig')

    # denshou_01.csv, denshou_02.csv
    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    denshou_01 = pd.DataFrame({
        'ID': ['01001', '01002', '01003'],
        '碑名': ['碑1', '碑2', '碑3'],
        '主な種別': ['洪水', '地震', '津波'],
        '災害名（元の表記）': ['洪水(1945年)', '地震(1923年)', '津波(1945年)'],
        '取り出した災害': ['洪水(1945)', '地震(1923)', '津波(1945)'],
        '年の数': [1, 1, 1],
        '発生年': [1945, 1923, 1945],
        '建立年（元の表記）': ['1950', '1930', '1950'],
        '建立年_数値': [1950, 1930, 1950],
        '建立までの年数': [5, 7, 5],
        '区分': ['差あり', '差あり', '差あり'],
        '注記': ['', '', '']
    })
    denshou_01.to_csv(out_dir / "denshou_01.csv", index=False, encoding='utf-8-sig')

    denshou_02 = pd.DataFrame({
        'ID': ['02001', '02002'],
        '碑名': ['碑A', '碑B'],
        '主な種別': ['高潮', '火山災害'],
        '災害名（元の表記）': ['高潮(1854年)', '火山(2011年)'],
        '取り出した災害': ['高潮(1854)', '火山(2011)'],
        '年の数': [1, 1],
        '発生年': [1854, 2011],
        '建立年（元の表記）': ['1860', '2015'],
        '建立年_数値': [1860, 2015],
        '建立までの年数': [6, 4],
        '区分': ['差あり', '差あり'],
        '注記': ['', '']
    })
    denshou_02.to_csv(out_dir / "denshou_02.csv", index=False, encoding='utf-8-sig')


def test_dummy_data_and_missing_checks(tmp_path):
    """
    小さな作りもののデータで以下を検証：
    1. build_pref_counts の県の行と「全国」行の合計
    2. check_all_files が足りない県を返すこと
    3. main が足りない県で終了コード1になり集計結果を output に書かないこと
    """
    create_dummy_pref_data(tmp_path)

    # 1. build_pref_counts
    df_counts = build_pref_counts(tmp_path)
    assert len(df_counts) == 3  # 01, 02, 全国

    row_01 = df_counts[df_counts['県コード'] == '01'].iloc[0]
    assert row_01['碑_数'] == 3
    assert row_01['移転碑_数'] == 2
    assert row_01['比較地点_数'] == 6
    assert row_01['種別_洪水'] == 2
    assert row_01['種別_地震'] == 1
    assert row_01['種別_津波'] == 1
    assert row_01['種別_土砂災害'] == 1
    assert row_01['種別_高潮'] == 0
    assert row_01['種別_火山災害'] == 0
    assert row_01['種別_その他'] == 0

    row_02 = df_counts[df_counts['県コード'] == '02'].iloc[0]
    assert row_02['碑_数'] == 2
    assert row_02['移転碑_数'] == 0
    assert row_02['比較地点_数'] == 4
    assert row_02['種別_洪水'] == 0
    assert row_02['種別_地震'] == 0
    assert row_02['種別_津波'] == 0
    assert row_02['種別_土砂災害'] == 0
    assert row_02['種別_高潮'] == 1
    assert row_02['種別_火山災害'] == 1
    assert row_02['種別_その他'] == 1

    row_total = df_counts[df_counts['県コード'] == '全国'].iloc[0]
    assert row_total['碑_数'] == 5
    assert row_total['移転碑_数'] == 2
    assert row_total['比較地点_数'] == 10
    assert row_total['種別_洪水'] == 2
    assert row_total['種別_地震'] == 1
    assert row_total['種別_津波'] == 1
    assert row_total['種別_土砂災害'] == 1
    assert row_total['種別_高潮'] == 1
    assert row_total['種別_火山災害'] == 1
    assert row_total['種別_その他'] == 1

    # 各列の合計が全国行と一致することを確認
    for col in ['碑_数', '移転碑_数', '比較地点_数', '種別_洪水', '種別_地震', '種別_津波', '種別_土砂災害', '種別_高潮', '種別_火山災害', '種別_その他']:
        assert row_01[col] + row_02[col] == row_total[col]

    # 2. check_all_files
    missing = check_all_files(tmp_path)
    assert '01' not in missing
    assert '02' not in missing
    assert len(missing) == 45
    assert '03' in missing

    # 3. main が足りない県で終了コード1になり集計結果を output に書かないこと
    with pytest.raises(SystemExit) as exc_info:
        main(base_dir=tmp_path)
    assert exc_info.value.code == 1

    out_dir = tmp_path / "output"
    assert out_dir.exists()
    # 事前に置いた denshou_01.csv, denshou_02.csv 以外は作成されていないこと
    assert set(p.name for p in out_dir.iterdir()) == {"denshou_01.csv", "denshou_02.csv"}


def clean_csv_lines(text):
    """CSV文字列から注記行を除き、改行をLFに統一して返す"""
    lines = [line for line in text.splitlines() if not line.startswith("注：")]
    return "\n".join(lines).strip()


def test_real_data_match_each_pref():
    """
    実データの照合テスト：
    47都道府県それぞれについて、load_pref → extract_relocated → build_summary_tables・build_hazard_table
    の結果を to_csv で文字列にしたものが、output/summary_XX.csv・landform_XX.csv・hazard_summary_XX.csv
    から「注：」で始まる行を除いた文字列と完全に一致すること。
    """
    root_dir = get_project_root()
    proc_dir = root_dir / "data" / "processed"
    if not (proc_dir / "monuments_36.csv").exists():
        pytest.skip("実データが存在しないためスキップします")

    for pref in sorted(PREFECTURES.keys()):
        mon, pt, mon_haz, pt_haz = load_pref(pref, root_dir)
        rel_df = extract_relocated(mon)
        rel_ids = rel_df['ID'].tolist()

        s_df, lf_df = build_summary_tables(mon, pt, rel_ids)
        h_df = build_hazard_table(mon_haz, pt_haz, rel_ids)

        # summary の照合
        s_actual = clean_csv_lines(s_df.to_csv(index=False))
        s_expected = clean_csv_lines((root_dir / "output" / f"summary_{pref}.csv").read_text(encoding='utf-8-sig'))
        assert s_actual == s_expected, f"summary 不一致: 県コード {pref}, summary_{pref}.csv"

        # landform の照合
        lf_actual = clean_csv_lines(lf_df.to_csv(index=False))
        lf_expected = clean_csv_lines((root_dir / "output" / f"landform_{pref}.csv").read_text(encoding='utf-8-sig'))
        assert lf_actual == lf_expected, f"landform 不一致: 県コード {pref}, landform_{pref}.csv"

        # hazard の照合
        h_actual = clean_csv_lines(h_df.to_csv(index=False))
        h_expected = clean_csv_lines((root_dir / "output" / f"hazard_summary_{pref}.csv").read_text(encoding='utf-8-sig'))
        assert h_actual == h_expected, f"hazard 不一致: 県コード {pref}, hazard_summary_{pref}.csv"


def test_real_data_national_values():
    """
    実データの全国の値のテスト：
    - 碑・比較地点・移転碑の数
    - pref_counts の「全国」行
    - summary の「全碑・全種別・標高_m」の行
    - hazard の「全碑・全種別・津波」の行
    （output/ には書き込まず DataFrame の値で検証）
    """
    root_dir = get_project_root()
    proc_dir = root_dir / "data" / "processed"
    if not (proc_dir / "monuments_36.csv").exists():
        pytest.skip("実データが存在しないためスキップします")

    mon_list = []
    pt_list = []
    mon_haz_list = []
    pt_haz_list = []

    for pref in sorted(PREFECTURES.keys()):
        m, p, mh, ph = load_pref(pref, root_dir)
        mon_list.append(m)
        pt_list.append(p)
        mon_haz_list.append(mh)
        pt_haz_list.append(ph)

    all_mon = pd.concat(mon_list, ignore_index=True)
    all_pt = pd.concat(pt_list, ignore_index=True)
    all_mon_haz = pd.concat(mon_haz_list, ignore_index=True)
    all_pt_haz = pd.concat(pt_haz_list, ignore_index=True)

    rel_df = extract_relocated(all_mon)
    rel_ids = rel_df['ID'].tolist()

    # 1. 碑・比較地点・移転碑の数
    assert len(all_mon) == 2481
    assert all_mon['ID'].nunique() == 2481
    assert len(all_pt) == 12395
    assert all_pt['ID'].nunique() == 12395
    assert len(rel_ids) == 102
    assert len(all_mon[~all_mon['ID'].isin(rel_ids)]) == 2379
    assert len(all_pt[~all_pt['元の碑ID'].isin(rel_ids)]) == 11885

    # 2. pref_counts の「全国」行
    pref_counts_df = build_pref_counts(root_dir)
    total_row = pref_counts_df[pref_counts_df['県コード'] == '全国'].iloc[0]
    assert total_row['碑_数'] == 2481
    assert total_row['移転碑_数'] == 102
    assert total_row['比較地点_数'] == 12395
    assert total_row['種別_洪水'] == 1112
    assert total_row['種別_地震'] == 888
    assert total_row['種別_津波'] == 596
    assert total_row['種別_土砂災害'] == 629
    assert total_row['種別_高潮'] == 138
    assert total_row['種別_火山災害'] == 82
    assert total_row['種別_その他'] == 119

    # 3. summary の「全碑・全種別・標高_m」の行
    summary_df, _ = build_summary_tables(all_mon, all_pt, rel_ids)
    elev_row = summary_df[
        (summary_df['範囲'] == '全碑') &
        (summary_df['災害種別'] == '全種別') &
        (summary_df['指標'] == '標高_m')
    ].iloc[0]
    assert elev_row['碑_数'] == 2479
    assert elev_row['碑_除外数'] == 2
    assert elev_row['碑_中央値'] == 18.6
    assert elev_row['碑_第1四分位'] == 6.1
    assert elev_row['碑_第3四分位'] == 93.0
    assert elev_row['比較地点_数'] == 12333
    assert elev_row['比較地点_除外数'] == 62
    assert elev_row['比較地点_中央値'] == 56.2
    assert elev_row['組の数'] == 2478
    assert elev_row['差の中央値'] == -11.15
    assert elev_row['碑の方が大きい割合'] == 0.282

    # 4. hazard の「全碑・全種別・津波」の行
    hazard_df = build_hazard_table(all_mon_haz, all_pt_haz, rel_ids)
    tsunami_row = hazard_df[
        (hazard_df['範囲'] == '全碑') &
        (hazard_df['災害種別'] == '全種別') &
        (hazard_df['ハザード'] == '津波')
    ].iloc[0]
    assert tsunami_row['碑_数'] == 2481
    assert tsunami_row['碑_取得不可'] == 0
    assert tsunami_row['碑_区域内'] == 595
    assert tsunami_row['碑_区域内の割合'] == 0.24
    assert tsunami_row['碑_3m以上'] == 372
    assert tsunami_row['碑_3m以上の割合'] == 0.15
    assert tsunami_row['比較地点_数'] == 12395
    assert tsunami_row['比較地点_取得不可'] == 0
    assert tsunami_row['比較地点_区域内'] == 1297
    assert tsunami_row['比較地点_区域内の割合'] == 0.105
    assert tsunami_row['比較地点_3m以上'] == 624
    assert tsunami_row['比較地点_3m以上の割合'] == 0.05


def test_decade_label():
    """
    decade_label のテスト：
    1599→「1600年より前」、1600→「1600年代」、1946→「1940年代」、2026→「2020年代」、NaN→None
    """
    assert decade_label(1599) == "1600年より前"
    assert decade_label(1600) == "1600年代"
    assert decade_label(1946) == "1940年代"
    assert decade_label(2026) == "2020年代"
    assert decade_label(float('nan')) is None
    assert decade_label(None) is None
    assert decade_label("") is None


def test_build_years_table_dummy(tmp_path):
    """
    小さな作りもののデータで build_years_table を検証：
    - 行数44
    - 同じ件数の「主な災害」が名前順で選ばれること
    - 年の括弧が除かれること
    - 空欄を数えないこと
    """
    out_dir = tmp_path / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1850年代: B災害(1850) 1件、A災害(1855) 1件 → 件数が同じ1件なら名前順で 'A災害(1)'
    # 1940年代: 洪水(1945)；二次災害(1946) 2件 → 最初の災害名「洪水」、年の括弧が除かれて '洪水(2)'
    # 1500年（1600年より前）: 古災害(1500) 1件、建立年は欠損
    # 発生年が欠損の碑: 建立年は2020年
    dummy_denshou = pd.DataFrame({
        'ID': ['01001', '01002', '01003', '01004', '01005', '01006'],
        '碑名': ['碑1', '碑2', '碑3', '碑4', '碑5', '碑6'],
        '主な種別': ['その他', 'その他', 'その他', 'その他', 'その他', 'その他'],
        '災害名（元の表記）': ['B災害(1850年)', 'A災害(1855年)', '洪水(1945年)', '洪水(1948年)', '古災害(1500年)', '不明'],
        '取り出した災害': ['B災害(1850)', 'A災害(1855)', '洪水(1945)；二次災害(1946)', '洪水(1948)', '古災害(1500)', ''],
        '年の数': [1, 1, 2, 1, 1, 0],
        '発生年': [1850, 1855, 1945, 1948, 1500, None],
        '建立年（元の表記）': ['1860', '1860', '1950', '1950', '', '2020'],
        '建立年_数値': [1860, 1860, 1950, 1950, None, 2020],
        '建立までの年数': [10, 5, 5, 2, None, None],
        '区分': ['差あり', '差あり', '差あり', '差あり', '対象外（建立年不明）', '対象外（建立年不明）'],
        '注記': ['', '', '', '', '', '']
    })
    dummy_denshou.to_csv(out_dir / "denshou_01.csv", index=False, encoding='utf-8-sig')

    df = build_years_table(tmp_path)

    # 行数は44行
    assert len(df) == 44
    assert list(df.columns) == ['年代', '発生年代_碑の数', '建立年代_碑の数', '発生年代_主な災害']

    # 1850年代：発生2基、同じ1件で名前順により「A災害(1)」
    row_1850 = df[df['年代'] == '1850年代'].iloc[0]
    assert row_1850['発生年代_碑の数'] == 2
    assert row_1850['発生年代_主な災害'] == 'A災害(1)'

    # 1940年代：発生2基、年の括弧「(1945)」や後続の「；二次災害」が除かれて「洪水(2)」
    row_1940 = df[df['年代'] == '1940年代'].iloc[0]
    assert row_1940['発生年代_碑の数'] == 2
    assert row_1940['発生年代_主な災害'] == '洪水(2)'

    # 1600年より前：発生1基、建立0基（建立年空欄のため数えない）
    row_pre1600 = df[df['年代'] == '1600年より前'].iloc[0]
    assert row_pre1600['発生年代_碑の数'] == 1
    assert row_pre1600['建立年代_碑の数'] == 0
    assert row_pre1600['発生年代_主な災害'] == '古災害(1)'

    # 2020年代：発生0基（発生年空欄のため数えない）、建立1基
    row_2020 = df[df['年代'] == '2020年代'].iloc[0]
    assert row_2020['発生年代_碑の数'] == 0
    assert row_2020['建立年代_碑の数'] == 1
    assert row_2020['発生年代_主な災害'] == ''

    # 碑が0の年代は空文字列
    row_1700 = df[df['年代'] == '1700年代'].iloc[0]
    assert row_1700['発生年代_碑の数'] == 0
    assert row_1700['建立年代_碑の数'] == 0
    assert row_1700['発生年代_主な災害'] == ''


def test_main_runs_with_dummy_data(tmp_path, monkeypatch):
    """
    ダミーデータで main が正常実行され、years_all.csv と 2つの PNG が作成されることを確認する。
    """
    create_dummy_pref_data(tmp_path)
    monkeypatch.setattr('src.summarize_national.PREFECTURES', {'01': '北海道', '02': '青森県'})

    main(base_dir=tmp_path)

    out_dir = tmp_path / "output"
    assert (out_dir / "years_all.csv").exists()
    assert (out_dir / "fig" / "years_all.png").exists()
    assert (out_dir / "fig" / "pref_counts_all.png").exists()

    # PNG ファイルのサイズが0より大きいこと
    assert (out_dir / "fig" / "years_all.png").stat().st_size > 0
    assert (out_dir / "fig" / "pref_counts_all.png").stat().st_size > 0

    # years_all.csv の検証
    text = (out_dir / "years_all.csv").read_text(encoding='utf-8-sig')
    lines = text.splitlines()
    assert any("注：発生年は、複数の災害がある碑では最も古い年です。" in l for l in lines)
    assert any("注：発生年が不明の碑 0基、建立年が不明の碑 0基は数えていません。" in l for l in lines)


def test_real_data_years_values():
    """
    実データの年代別推移（既知の答え）のテスト：
    - 44行
    - 発生年代_碑の数の合計 2,475
    - 建立年代_碑の数の合計 2,194
    - 既知の各年代の行
    - 上の段で名前を書く6つの年代
    """
    root_dir = get_project_root()
    proc_dir = root_dir / "data" / "processed"
    if not (proc_dir / "monuments_36.csv").exists():
        pytest.skip("実データが存在しないためスキップします")

    years_df = build_years_table(root_dir)

    assert len(years_df) == 44
    assert years_df['発生年代_碑の数'].sum() == 2475
    assert years_df['建立年代_碑の数'].sum() == 2194

    expected_rows = {
        '1600年より前': (9, 1, '洪水(2)'),
        '1600年代': (3, 0, '慶長南海地震(2)'),
        '1850年代': (99, 40, '安政南海地震(39)'),
        '1890年代': (181, 78, '明治三陸地震(67)'),
        '1920年代': (240, 169, '関東大震災(166)'),
        '1930年代': (235, 218, '昭和三陸地震(90)'),
        '1940年代': (288, 66, '昭和南海地震(81)'),
        '2010年代': (246, 239, '東日本大震災(126)'),
        '2020年代': (4, 94, '令和5年台風第7号(2)'),
    }

    for dec, (exp_occur, exp_built, exp_disaster) in expected_rows.items():
        row = years_df[years_df['年代'] == dec].iloc[0]
        assert row['発生年代_碑の数'] == exp_occur, f"{dec} の発生年代_碑の数が不一致"
        assert row['建立年代_碑の数'] == exp_built, f"{dec} の建立年代_碑の数が不一致"
        assert row['発生年代_主な災害'] == exp_disaster, f"{dec} の発生年代_主な災害が不一致"

    # 上の段で名前を書く6つの年代（多い順→年代の古い順）
    temp_df = years_df.copy()
    temp_df['idx'] = range(len(temp_df))
    top6 = temp_df.sort_values(by=['発生年代_碑の数', 'idx'], ascending=[False, True]).head(6)
    expected_top6_decades = ['1940年代', '2010年代', '1920年代', '1930年代', '1950年代', '1890年代']
    assert top6['年代'].tolist() == expected_top6_decades

    # 1950年代の主な災害が「伊勢湾台風」であること
    row_1950 = years_df[years_df['年代'] == '1950年代'].iloc[0]
    assert row_1950['発生年代_主な災害'].startswith('伊勢湾台風')

