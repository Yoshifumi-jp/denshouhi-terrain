# -*- coding: utf-8 -*-
import pandas as pd
import pytest

from src.count_missing import count_missing, main, get_project_root, COLUMNS
from src.prefectures import PREFECTURES


def create_dummy_csv(path, rows, columns):
    """指定パスにダミーCSVファイルを作成する（utf-8-sig）"""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def test_counts_small(tmp_path):
    """
    2県（36, 37）の小規模ダミーデータで各列の集計、割合の丸め、
    全国合計の再計算が正しく行われることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 36 徳島県（碑2件、比較地点2件）
    create_dummy_csv(proc_dir / "elevation_36.csv", [
        {"ID": "36001", "取得状態": "正常"},
        {"ID": "36002", "取得状態": "取得不可（データなし）"}
    ], ["ID", "取得状態"])

    create_dummy_csv(proc_dir / "elevation_points_36.csv", [
        {"ID": "36001-01", "取得状態": "正常"},
        {"ID": "36002-01", "取得状態": "取得不可（通信エラー）"}
    ], ["ID", "取得状態"])

    create_dummy_csv(proc_dir / "hazard_36.csv", [
        {"ID": "36001", "洪水_状態": "取得不可", "津波_状態": "取得不可", "高潮_状態": "正常", "土砂_状態": "正常"},
        {"ID": "36002", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"}
    ], ["ID", "洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"])

    create_dummy_csv(proc_dir / "hazard_points_36.csv", [
        {"ID": "36001-01", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"},
        {"ID": "36002-01", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"}
    ], ["ID", "洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"])

    create_dummy_csv(proc_dir / "landform_36.csv", [
        {"ID": "36001", "地形分類_状態": "データなし"},
        {"ID": "36002", "地形分類_状態": "正常"}
    ], ["ID", "地形分類_状態"])

    create_dummy_csv(proc_dir / "landform_points_36.csv", [
        {"ID": "36001-01", "地形分類_状態": "データなし"},
        {"ID": "36002-01", "地形分類_状態": "データなし"}
    ], ["ID", "地形分類_状態"])

    create_dummy_csv(proc_dir / "river_coast_36.csv", [
        {"ID": "36001", "河川_状態": "高さの差 取得不可（河川の標高なし）", "海岸_状態": "正常"},
        {"ID": "36002", "河川_状態": "高さの差 対象外（河川まで1000m超）", "海岸_状態": "正常"}
    ], ["ID", "河川_状態", "海岸_状態"])

    create_dummy_csv(proc_dir / "river_coast_points_36.csv", [
        {"ID": "36001-01", "河川_状態": "正常", "海岸_状態": "正常"},
        {"ID": "36002-01", "河川_状態": "正常", "海岸_状態": "対象外（海のない県）"}
    ], ["ID", "河川_状態", "海岸_状態"])

    # 37 香川県（碑3件、比較地点3件）
    create_dummy_csv(proc_dir / "elevation_37.csv", [
        {"ID": "37001", "取得状態": "正常"},
        {"ID": "37002", "取得状態": "正常"},
        {"ID": "37003", "取得状態": "正常"}
    ], ["ID", "取得状態"])

    create_dummy_csv(proc_dir / "elevation_points_37.csv", [
        {"ID": "37001-01", "取得状態": "正常"},
        {"ID": "37002-01", "取得状態": "正常"},
        {"ID": "37003-01", "取得状態": "正常"}
    ], ["ID", "取得状態"])

    create_dummy_csv(proc_dir / "hazard_37.csv", [
        {"ID": "37001", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"},
        {"ID": "37002", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"},
        {"ID": "37003", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"}
    ], ["ID", "洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"])

    create_dummy_csv(proc_dir / "hazard_points_37.csv", [
        {"ID": "37001-01", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"},
        {"ID": "37002-01", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"},
        {"ID": "37003-01", "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"}
    ], ["ID", "洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"])

    # 2/3 = 0.6666... -> 0.667
    create_dummy_csv(proc_dir / "landform_37.csv", [
        {"ID": "37001", "地形分類_状態": "データなし"},
        {"ID": "37002", "地形分類_状態": "データなし"},
        {"ID": "37003", "地形分類_状態": "正常"}
    ], ["ID", "地形分類_状態"])

    # 1/3 = 0.3333... -> 0.333
    create_dummy_csv(proc_dir / "landform_points_37.csv", [
        {"ID": "37001-01", "地形分類_状態": "データなし"},
        {"ID": "37002-01", "地形分類_状態": "正常"},
        {"ID": "37003-01", "地形分類_状態": "正常"}
    ], ["ID", "地形分類_状態"])

    create_dummy_csv(proc_dir / "river_coast_37.csv", [
        {"ID": "37001", "河川_状態": "取得不可（通信エラー）", "海岸_状態": "正常"},
        {"ID": "37002", "河川_状態": "正常", "海岸_状態": "正常"},
        {"ID": "37003", "河川_状態": "正常", "海岸_状態": "正常"}
    ], ["ID", "河川_状態", "海岸_状態"])

    create_dummy_csv(proc_dir / "river_coast_points_37.csv", [
        {"ID": "37001-01", "河川_状態": "正常", "海岸_状態": "正常"},
        {"ID": "37002-01", "河川_状態": "正常", "海岸_状態": "正常"},
        {"ID": "37003-01", "河川_状態": "正常", "海岸_状態": "正常"}
    ], ["ID", "河川_状態", "海岸_状態"])

    df, missing_prefs = count_missing(tmp_path)

    # 36, 37 以外の45県が missing_prefs に入る
    assert "36" not in missing_prefs
    assert "37" not in missing_prefs
    assert len(missing_prefs) == 45

    # 行の確認
    assert len(df) == 3  # 36, 37, 全国
    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_37 = df[df["県コード"] == "37"].iloc[0]
    row_all = df[df["県コード"] == "全国"].iloc[0]

    # 36 の確認
    assert row_36["碑_数"] == 2
    assert row_36["比較地点_数"] == 2
    assert row_36["標高傾斜_取得不可_碑"] == 1
    assert row_36["標高傾斜_取得不可_比較地点"] == 1
    assert row_36["ハザード_取得不可_碑"] == 1  # 2列取得不可でも1件
    assert row_36["ハザード_取得不可_比較地点"] == 0
    assert row_36["地形分類_データなし_碑"] == 1
    assert row_36["地形分類_データなし_碑_割合"] == 0.5
    assert row_36["地形分類_データなし_比較地点"] == 2
    assert row_36["地形分類_データなし_比較地点_割合"] == 1.0
    assert row_36["河川標高_取得不可_碑"] == 1
    assert row_36["河川標高_取得不可_比較地点"] == 0
    assert row_36["河川_1000m超_碑"] == 1
    assert row_36["河川_1000m超_比較地点"] == 0
    assert row_36["海岸_対象外_碑"] == 0
    assert row_36["海岸_対象外_比較地点"] == 1
    assert row_36["通信エラー_碑"] == 0
    assert row_36["通信エラー_比較地点"] == 1  # elevation_points_36 に1行

    # 37 の確認
    assert row_37["碑_数"] == 3
    assert row_37["比較地点_数"] == 3
    assert row_37["地形分類_データなし_碑"] == 2
    assert row_37["地形分類_データなし_碑_割合"] == 0.667  # 四捨五入
    assert row_37["地形分類_データなし_比較地点"] == 1
    assert row_37["地形分類_データなし_比較地点_割合"] == 0.333  # 四捨五入
    assert row_37["河川標高_取得不可_碑"] == 1
    assert row_37["通信エラー_碑"] == 1  # river_coast_37 に1行
    assert row_37["通信エラー_比較地点"] == 0

    # 全国の確認（合計と割合の再計算）
    assert row_all["碑_数"] == 5
    assert row_all["比較地点_数"] == 5
    assert row_all["標高傾斜_取得不可_碑"] == 1
    assert row_all["標高傾斜_取得不可_比較地点"] == 1
    assert row_all["ハザード_取得不可_碑"] == 1
    assert row_all["ハザード_取得不可_比較地点"] == 0
    assert row_all["地形分類_データなし_碑"] == 3
    # 3 / 5 = 0.6（県割合の平均ではなく合計から計算）
    assert row_all["地形分類_データなし_碑_割合"] == 0.6
    assert row_all["地形分類_データなし_比較地点"] == 3
    assert row_all["地形分類_データなし_比較地点_割合"] == 0.6
    assert row_all["河川標高_取得不可_碑"] == 2
    assert row_all["河川標高_取得不可_比較地点"] == 0
    assert row_all["河川_1000m超_碑"] == 1
    assert row_all["河川_1000m超_比較地点"] == 0
    assert row_all["海岸_対象外_碑"] == 0
    assert row_all["海岸_対象外_比較地点"] == 1
    assert row_all["通信エラー_碑"] == 1
    assert row_all["通信エラー_比較地点"] == 1


def test_missing_files(tmp_path):
    """1県だけ landform_points がない環境で、その県が結果の行になく、足りない県のリストに入ること"""
    proc_dir = tmp_path / "data" / "processed"

    # 36 は全ファイル作成
    for name in ["elevation_36.csv", "elevation_points_36.csv", "hazard_36.csv", "hazard_points_36.csv",
                 "landform_36.csv", "landform_points_36.csv", "river_coast_36.csv", "river_coast_points_36.csv"]:
        create_dummy_csv(proc_dir / name, [{"ID": "36001"}], ["ID"])

    # 37 は landform_points_37.csv 以外を作成
    for name in ["elevation_37.csv", "elevation_points_37.csv", "hazard_37.csv", "hazard_points_37.csv",
                 "landform_37.csv", "river_coast_37.csv", "river_coast_points_37.csv"]:
        create_dummy_csv(proc_dir / name, [{"ID": "37001"}], ["ID"])

    df, missing_prefs = count_missing(tmp_path)

    # 37 は結果の DataFrame になく、missing_prefs に含まれる
    assert "37" in missing_prefs
    assert "36" not in missing_prefs
    assert "37" not in df["県コード"].values
    assert "36" in df["県コード"].values


def test_main_output(tmp_path, capsys):
    """
    main(base_dir=tmp_path) で output/missing_counts.csv ができ、
    列名が仕様の順序と一致し、画面表示に必要な文言が含まれることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 36 のみ全ファイル作成
    for name in ["elevation_36.csv", "elevation_points_36.csv", "hazard_36.csv", "hazard_points_36.csv",
                 "landform_36.csv", "landform_points_36.csv", "river_coast_36.csv", "river_coast_points_36.csv"]:
        create_dummy_csv(proc_dir / name, [{"ID": "36001", "取得状態": "正常"}], ["ID", "取得状態"])

    main(base_dir=tmp_path)

    out_csv = tmp_path / "output" / "missing_counts.csv"
    assert out_csv.exists()

    df = pd.read_csv(out_csv, dtype={"県コード": str}, encoding="utf-8-sig")
    assert list(df.columns) == COLUMNS

    out = capsys.readouterr().out
    assert "ファイルが足りない県" in out
    assert "不一致" in out
    assert "出力：output/missing_counts.csv" in out


def test_real_data():
    """プロジェクトの data/processed に47県分のファイルがあるときだけ実行し、全国合計が既知の答えと一致することを確認する"""
    root = get_project_root()
    proc_dir = root / "data" / "processed"

    required_suffixes = [
        "elevation_{}.csv", "elevation_points_{}.csv",
        "hazard_{}.csv", "hazard_points_{}.csv",
        "landform_{}.csv", "landform_points_{}.csv",
        "river_coast_{}.csv", "river_coast_points_{}.csv",
    ]

    all_exist = True
    for pref in PREFECTURES.keys():
        for pattern in required_suffixes:
            if not (proc_dir / pattern.format(pref)).exists():
                all_exist = False
                break
        if not all_exist:
            break

    if not all_exist:
        pytest.skip("実データが47県分揃っていないためスキップします")

    df, missing_prefs = count_missing(root)
    assert len(missing_prefs) == 0

    row_all = df[df["県コード"] == "全国"].iloc[0]

    # 指示書「既知の答え」との照合
    assert int(row_all["碑_数"]) == 2481
    assert int(row_all["比較地点_数"]) == 12395
    assert int(row_all["標高傾斜_取得不可_碑"]) == 2
    assert int(row_all["標高傾斜_取得不可_比較地点"]) == 62
    assert int(row_all["ハザード_取得不可_碑"]) == 0
    assert int(row_all["ハザード_取得不可_比較地点"]) == 0
    assert int(row_all["地形分類_データなし_碑"]) == 929
    assert float(row_all["地形分類_データなし_碑_割合"]) == 0.374
    assert int(row_all["地形分類_データなし_比較地点"]) == 4890
    assert float(row_all["地形分類_データなし_比較地点_割合"]) == 0.395
    assert int(row_all["河川標高_取得不可_碑"]) == 5
    assert int(row_all["河川標高_取得不可_比較地点"]) == 16
    assert int(row_all["河川_1000m超_碑"]) == 158
    assert int(row_all["河川_1000m超_比較地点"]) == 990
    assert int(row_all["海岸_対象外_碑"]) == 418
    assert int(row_all["海岸_対象外_比較地点"]) == 2090
    assert int(row_all["通信エラー_碑"]) == 0
    assert int(row_all["通信エラー_比較地点"]) == 0


def _create_base_8_files(proc_dir, pref, m_rows, p_rows, land_m_rows, land_p_rows):
    """テスト用に既存の8ファイルを作成するヘルパー"""
    create_dummy_csv(proc_dir / f"elevation_{pref}.csv", m_rows, ["ID", "取得状態"])
    create_dummy_csv(proc_dir / f"elevation_points_{pref}.csv", p_rows, ["ID", "取得状態"])
    create_dummy_csv(
        proc_dir / f"hazard_{pref}.csv",
        [{"ID": r["ID"], "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"} for r in m_rows],
        ["ID", "洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"]
    )
    create_dummy_csv(
        proc_dir / f"hazard_points_{pref}.csv",
        [{"ID": r["ID"], "洪水_状態": "正常", "津波_状態": "正常", "高潮_状態": "正常", "土砂_状態": "正常"} for r in p_rows],
        ["ID", "洪水_状態", "津波_状態", "高潮_状態", "土砂_状態"]
    )
    create_dummy_csv(proc_dir / f"landform_{pref}.csv", land_m_rows, ["ID", "地形分類_状態"])
    create_dummy_csv(proc_dir / f"landform_points_{pref}.csv", land_p_rows, ["ID", "地形分類_状態"])
    create_dummy_csv(
        proc_dir / f"river_coast_{pref}.csv",
        [{"ID": r["ID"], "河川_状態": "正常", "海岸_状態": "正常"} for r in m_rows],
        ["ID", "河川_状態", "海岸_状態"]
    )
    create_dummy_csv(
        proc_dir / f"river_coast_points_{pref}.csv",
        [{"ID": r["ID"], "河川_状態": "正常", "海岸_状態": "正常"} for r in p_rows],
        ["ID", "河川_状態", "海岸_状態"]
    )


def test_region_counts_and_total(tmp_path):
    """
    (a) 地域版の2ファイルがある県で、6列の数（データなし・取得不可・補えた〔地域版・広域版の両方を数え、
    データなし・取得不可は数えない〕）と全国の合計が正しいことを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 36 徳島県（碑5件、比較地点4件）
    m_36 = [{"ID": f"3600{i}", "取得状態": "正常"} for i in range(1, 6)]
    p_36 = [{"ID": f"3600{i}-P1", "取得状態": "正常"} for i in range(1, 5)]
    land_m_36 = [
        {"ID": "36001", "地形分類_状態": "データなし"},  # 地域版で補完
        {"ID": "36002", "地形分類_状態": "データなし"},  # 広域版で補完
        {"ID": "36003", "地形分類_状態": "データなし"},  # 地域版もデータなし（補完ならず）
        {"ID": "36004", "地形分類_状態": "データなし"},  # 地域版が取得不可（補完ならず）
        {"ID": "36005", "地形分類_状態": "取得済"},      # 元から取得済（補完に数えない）
    ]
    land_p_36 = [
        {"ID": "36001-P1", "地形分類_状態": "データなし"},  # 地域版で補完
        {"ID": "36002-P1", "地形分類_状態": "データなし"},  # 広域版で補完
        {"ID": "36003-P1", "地形分類_状態": "データなし"},  # 地域版もデータなし
        {"ID": "36004-P1", "地形分類_状態": "データなし"},  # 地域版が取得不可
    ]
    _create_base_8_files(proc_dir, "36", m_36, p_36, land_m_36, land_p_36)

    create_dummy_csv(proc_dir / "landform_region_36.csv", [
        {"ID": "36001", "碑名": "碑A", "地域版_状態": "取得済（地域版）"},
        {"ID": "36002", "碑名": "碑B", "地域版_状態": "取得済（広域版）"},
        {"ID": "36003", "碑名": "碑C", "地域版_状態": "データなし"},
        {"ID": "36004", "碑名": "碑D", "地域版_状態": "取得不可"},
        {"ID": "36005", "碑名": "碑E", "地域版_状態": "取得済（地域版）"},
    ], ["ID", "碑名", "地域版_状態"])

    create_dummy_csv(proc_dir / "landform_region_points_36.csv", [
        {"ID": "36001-P1", "碑名": "比較地点", "地域版_状態": "取得済（地域版）"},
        {"ID": "36002-P1", "碑名": "比較地点", "地域版_状態": "取得済（広域版）"},
        {"ID": "36003-P1", "碑名": "比較地点", "地域版_状態": "データなし"},
        {"ID": "36004-P1", "碑名": "比較地点", "地域版_状態": "取得不可"},
    ], ["ID", "碑名", "地域版_状態"])

    # 37 香川県（碑2件、比較地点2件）
    m_37 = [{"ID": "37001", "取得状態": "正常"}, {"ID": "37002", "取得状態": "正常"}]
    p_37 = [{"ID": "37001-P1", "取得状態": "正常"}, {"ID": "37002-P1", "取得状態": "正常"}]
    land_m_37 = [
        {"ID": "37001", "地形分類_状態": "データなし"},
        {"ID": "37002", "地形分類_状態": "データなし"},
    ]
    land_p_37 = [
        {"ID": "37001-P1", "地形分類_状態": "データなし"},
        {"ID": "37002-P1", "地形分類_状態": "取得済"},
    ]
    _create_base_8_files(proc_dir, "37", m_37, p_37, land_m_37, land_p_37)

    create_dummy_csv(proc_dir / "landform_region_37.csv", [
        {"ID": "37001", "碑名": "碑F", "地域版_状態": "取得済（地域版）"},
        {"ID": "37002", "碑名": "碑G", "地域版_状態": "データなし"},
    ], ["ID", "碑名", "地域版_状態"])

    create_dummy_csv(proc_dir / "landform_region_points_37.csv", [
        {"ID": "37001-P1", "碑名": "比較地点", "地域版_状態": "データなし"},
        {"ID": "37002-P1", "碑名": "比較地点", "地域版_状態": "データなし"},
    ], ["ID", "碑名", "地域版_状態"])

    df, missing_prefs = count_missing(tmp_path)
    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_37 = df[df["県コード"] == "37"].iloc[0]
    row_all = df[df["県コード"] == "全国"].iloc[0]

    # 36 の確認
    assert row_36["地域版_データなし_碑"] == 1
    assert row_36["地域版_データなし_比較地点"] == 1
    assert row_36["地域版_取得不可_碑"] == 1
    assert row_36["地域版_取得不可_比較地点"] == 1
    assert row_36["詳細版データなしを補えた_碑"] == 2
    assert row_36["詳細版データなしを補えた_比較地点"] == 2

    # 37 の確認
    assert row_37["地域版_データなし_碑"] == 1
    assert row_37["地域版_データなし_比較地点"] == 2
    assert row_37["地域版_取得不可_碑"] == 0
    assert row_37["地域版_取得不可_比較地点"] == 0
    assert row_37["詳細版データなしを補えた_碑"] == 1
    assert row_37["詳細版データなしを補えた_比較地点"] == 0

    # 全国合計の確認
    assert row_all["地域版_データなし_碑"] == 2
    assert row_all["地域版_データなし_比較地点"] == 3
    assert row_all["地域版_取得不可_碑"] == 1
    assert row_all["地域版_取得不可_比較地点"] == 1
    assert row_all["詳細版データなしを補えた_碑"] == 3
    assert row_all["詳細版データなしを補えた_比較地点"] == 2


def test_region_missing_files(tmp_path, capsys):
    """
    (b) 地域版のファイルがない県：結果の行に入る、missing_prefs に入らない、6列が空欄、
    全国の合計に入らない、画面の1行目に県名と run_region_batch.py の案内が出ることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 36 は地域版も含め全10ファイル作成
    m_36 = [{"ID": "36001", "取得状態": "正常"}]
    p_36 = [{"ID": "36001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "36", m_36, p_36, [{"ID": "36001", "地形分類_状態": "データなし"}], [{"ID": "36001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_region_36.csv", [{"ID": "36001", "碑名": "碑A", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_region_points_36.csv", [{"ID": "36001-P1", "碑名": "比較地点", "地域版_状態": "データなし"}], ["ID", "碑名", "地域版_状態"])

    # 37 は既存の8ファイルのみ（地域版なし）
    m_37 = [{"ID": "37001", "取得状態": "正常"}]
    p_37 = [{"ID": "37001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "37", m_37, p_37, [{"ID": "37001", "地形分類_状態": "データなし"}], [{"ID": "37001-P1", "地形分類_状態": "データなし"}])

    # 38 は地域版の片方（landform_region_38.csv）だけ作成
    m_38 = [{"ID": "38001", "取得状態": "正常"}]
    p_38 = [{"ID": "38001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "38", m_38, p_38, [{"ID": "38001", "地形分類_状態": "データなし"}], [{"ID": "38001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_region_38.csv", [{"ID": "38001", "碑名": "碑B", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])

    df, missing_prefs = count_missing(tmp_path)

    assert "36" not in missing_prefs
    assert "37" not in missing_prefs
    assert "38" not in missing_prefs
    assert list(df["県コード"]) == ["36", "37", "38", "全国"]

    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_37 = df[df["県コード"] == "37"].iloc[0]
    row_38 = df[df["県コード"] == "38"].iloc[0]
    row_all = df[df["県コード"] == "全国"].iloc[0]

    region_cols = COLUMNS[20:26]
    for col in region_cols:
        assert row_37[col] == ""
        assert row_38[col] == ""

    # 全国の合計は 36 だけの値になる
    assert row_all["地域版_データなし_碑"] == row_36["地域版_データなし_碑"] == 0
    assert row_all["地域版_データなし_比較地点"] == row_36["地域版_データなし_比較地点"] == 1
    assert row_all["詳細版データなしを補えた_碑"] == row_36["詳細版データなしを補えた_碑"] == 1
    assert row_all["詳細版データなしを補えた_比較地点"] == row_36["詳細版データなしを補えた_比較地点"] == 0

    main(base_dir=tmp_path)
    out = capsys.readouterr().out
    expected_msg = '地域版のファイルが足りない県：香川県（37）、愛媛県（38）（地域版の列は空欄です。先に実行してください：python src/run_region_batch.py --pref "37,38"）'
    assert expected_msg in out


def test_region_display_lines_and_formatting(tmp_path, capsys):
    """
    (c) 画面の4行が「地形分類のデータなし」の行の直後にこの順で出る。
    データなしの碑が11基以上のとき「、ほか n基」、0基のとき「なし」になることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # まず0基のケース
    m_36 = [{"ID": "36001", "取得状態": "正常"}]
    p_36 = [{"ID": "36001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "36", m_36, p_36, [{"ID": "36001", "地形分類_状態": "データなし"}], [{"ID": "36001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_region_36.csv", [{"ID": "36001", "碑名": "碑1", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_region_points_36.csv", [{"ID": "36001-P1", "碑名": "比較地点", "地域版_状態": "取得済（広域版）"}], ["ID", "碑名", "地域版_状態"])

    main(base_dir=tmp_path)
    lines_0 = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    idx = next(i for i, l in enumerate(lines_0) if l.startswith("地形分類のデータなし："))
    assert lines_0[idx + 1] == "地域版のファイルが足りない県：なし"
    assert lines_0[idx + 2].startswith("地形分類（地域版）のデータなし：")
    assert lines_0[idx + 3].startswith("詳細版のデータなしを地域版・広域版で補えた地点：")
    assert lines_0[idx + 4] == "地形分類（地域版）のデータなしの碑：なし"

    # 次に12基（11基以上）のケース
    m_36_12 = [{"ID": f"360{i:02d}", "取得状態": "正常"} for i in range(1, 13)]
    land_m_36_12 = [{"ID": f"360{i:02d}", "地形分類_状態": "データなし"} for i in range(1, 13)]
    _create_base_8_files(proc_dir, "36", m_36_12, p_36, land_m_36_12, [{"ID": "36001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(
        proc_dir / "landform_region_36.csv",
        [{"ID": f"360{i:02d}", "碑名": f"碑{i}", "地域版_状態": "データなし"} for i in range(1, 13)],
        ["ID", "碑名", "地域版_状態"]
    )

    main(base_dir=tmp_path)
    lines_12 = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    idx12 = next(i for i, l in enumerate(lines_12) if l.startswith("地形分類のデータなし："))
    expected_10 = "、".join([f"360{i:02d} 碑{i}" for i in range(1, 11)])
    assert lines_12[idx12 + 4] == f"地形分類（地域版）のデータなしの碑：{expected_10}、ほか 2基"


def test_csv_bom_lf_and_columns(tmp_path):
    """
    (d) 出力の CSV が BOM 付き・LF（\r を含まない）、列が COLUMNS と同じ順であることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"
    m_36 = [{"ID": "36001", "取得状態": "正常"}]
    p_36 = [{"ID": "36001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "36", m_36, p_36, [{"ID": "36001", "地形分類_状態": "データなし"}], [{"ID": "36001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_region_36.csv", [{"ID": "36001", "碑名": "碑1", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_region_points_36.csv", [{"ID": "36001-P1", "碑名": "比較地点", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])

    main(base_dir=tmp_path)
    out_csv = tmp_path / "output" / "missing_counts.csv"
    raw = out_csv.read_bytes()

    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert len(COLUMNS) == 30

    df = pd.read_csv(out_csv, dtype={"県コード": str}, encoding="utf-8-sig")
    assert list(df.columns) == COLUMNS


def test_real_data_region():
    """
    (e) 実データでの照合（data/processed に47県の10ファイルがそろっているときだけ。なければ pytest.skip）
    """
    root = get_project_root()
    proc_dir = root / "data" / "processed"

    required_suffixes = [
        "elevation_{}.csv", "elevation_points_{}.csv",
        "hazard_{}.csv", "hazard_points_{}.csv",
        "landform_{}.csv", "landform_points_{}.csv",
        "river_coast_{}.csv", "river_coast_points_{}.csv",
        "landform_region_{}.csv", "landform_region_points_{}.csv",
    ]

    for pref in PREFECTURES.keys():
        for pattern in required_suffixes:
            if not (proc_dir / pattern.format(pref)).exists():
                pytest.skip("実データが47県×10ファイル分揃っていないためスキップします")

    df, missing_prefs = count_missing(root)
    assert len(missing_prefs) == 0

    row_all = df[df["県コード"] == "全国"].iloc[0]
    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_03 = df[df["県コード"] == "03"].iloc[0]

    # 既存の20列の全国の値
    assert int(row_all["碑_数"]) == 2481
    assert int(row_all["比較地点_数"]) == 12395
    assert int(row_all["標高傾斜_取得不可_碑"]) == 2
    assert int(row_all["標高傾斜_取得不可_比較地点"]) == 62
    assert int(row_all["ハザード_取得不可_碑"]) == 0
    assert int(row_all["ハザード_取得不可_比較地点"]) == 0
    assert int(row_all["地形分類_データなし_碑"]) == 929
    assert float(row_all["地形分類_データなし_碑_割合"]) == 0.374
    assert int(row_all["地形分類_データなし_比較地点"]) == 4890
    assert float(row_all["地形分類_データなし_比較地点_割合"]) == 0.395
    assert int(row_all["河川標高_取得不可_碑"]) == 5
    assert int(row_all["河川標高_取得不可_比較地点"]) == 16
    assert int(row_all["河川_1000m超_碑"]) == 158
    assert int(row_all["河川_1000m超_比較地点"]) == 990
    assert int(row_all["海岸_対象外_碑"]) == 418
    assert int(row_all["海岸_対象外_比較地点"]) == 2090
    assert int(row_all["通信エラー_碑"]) == 0
    assert int(row_all["通信エラー_比較地点"]) == 0

    # 全国 地域版6列
    assert int(row_all["地域版_データなし_碑"]) == 5
    assert int(row_all["地域版_データなし_比較地点"]) == 118
    assert int(row_all["地域版_取得不可_碑"]) == 0
    assert int(row_all["地域版_取得不可_比較地点"]) == 0
    assert int(row_all["詳細版データなしを補えた_碑"]) == 927
    assert int(row_all["詳細版データなしを補えた_比較地点"]) == 4818

    # 徳島（36） 2・6・0・0・11・62
    assert int(row_36["地域版_データなし_碑"]) == 2
    assert int(row_36["地域版_データなし_比較地点"]) == 6
    assert int(row_36["地域版_取得不可_碑"]) == 0
    assert int(row_36["地域版_取得不可_比較地点"]) == 0
    assert int(row_36["詳細版データなしを補えた_碑"]) == 11
    assert int(row_36["詳細版データなしを補えた_比較地点"]) == 62

    # 岩手（03） 0・17・0・0・149・737
    assert int(row_03["地域版_データなし_碑"]) == 0
    assert int(row_03["地域版_データなし_比較地点"]) == 17
    assert int(row_03["地域版_取得不可_碑"]) == 0
    assert int(row_03["地域版_取得不可_比較地点"]) == 0
    assert int(row_03["詳細版データなしを補えた_碑"]) == 149
    assert int(row_03["詳細版データなしを補えた_比較地点"]) == 737


def test_artificial_counts_and_total(tmp_path):
    """
    (a) 人工地形の2ファイルがある県で、4列の数（範囲外・取得不可。取得済・人工地形なしは数えない）と
    全国の合計が正しいことを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 36 徳島県（碑4件、比較地点4件）
    m_36 = [{"ID": f"3600{i}", "取得状態": "正常"} for i in range(1, 5)]
    p_36 = [{"ID": f"3600{i}-P1", "取得状態": "正常"} for i in range(1, 5)]
    land_m_36 = [
        {"ID": "36001", "地形分類_状態": "データなし"},
        {"ID": "36002", "地形分類_状態": "取得済"},
        {"ID": "36003", "地形分類_状態": "取得済"},
        {"ID": "36004", "地形分類_状態": "取得済"},
    ]
    land_p_36 = [
        {"ID": "36001-P1", "地形分類_状態": "データなし"},
        {"ID": "36002-P1", "地形分類_状態": "データなし"},
        {"ID": "36003-P1", "地形分類_状態": "取得済"},
        {"ID": "36004-P1", "地形分類_状態": "取得済"},
    ]
    _create_base_8_files(proc_dir, "36", m_36, p_36, land_m_36, land_p_36)

    create_dummy_csv(proc_dir / "landform_artificial_36.csv", [
        {"ID": "36001", "人工地形_状態": "範囲外"},
        {"ID": "36002", "人工地形_状態": "取得不可"},
        {"ID": "36003", "人工地形_状態": "取得済"},
        {"ID": "36004", "人工地形_状態": "人工地形なし"},
    ], ["ID", "人工地形_状態"])

    create_dummy_csv(proc_dir / "landform_artificial_points_36.csv", [
        {"ID": "36001-P1", "人工地形_状態": "範囲外"},
        {"ID": "36002-P1", "人工地形_状態": "範囲外"},
        {"ID": "36003-P1", "人工地形_状態": "取得済"},
        {"ID": "36004-P1", "人工地形_状態": "人工地形なし"},
    ], ["ID", "人工地形_状態"])

    # 37 香川県（碑3件、比較地点3件）
    m_37 = [{"ID": f"3700{i}", "取得状態": "正常"} for i in range(1, 4)]
    p_37 = [{"ID": f"3700{i}-P1", "取得状態": "正常"} for i in range(1, 4)]
    land_m_37 = [
        {"ID": "37001", "地形分類_状態": "データなし"},
        {"ID": "37002", "地形分類_状態": "データなし"},
        {"ID": "37003", "地形分類_状態": "取得済"},
    ]
    land_p_37 = [
        {"ID": "37001-P1", "地形分類_状態": "データなし"},
        {"ID": "37002-P1", "地形分類_状態": "取得済"},
        {"ID": "37003-P1", "地形分類_状態": "取得済"},
    ]
    _create_base_8_files(proc_dir, "37", m_37, p_37, land_m_37, land_p_37)

    create_dummy_csv(proc_dir / "landform_artificial_37.csv", [
        {"ID": "37001", "人工地形_状態": "範囲外"},
        {"ID": "37002", "人工地形_状態": "範囲外"},
        {"ID": "37003", "人工地形_状態": "人工地形なし"},
    ], ["ID", "人工地形_状態"])

    create_dummy_csv(proc_dir / "landform_artificial_points_37.csv", [
        {"ID": "37001-P1", "人工地形_状態": "範囲外"},
        {"ID": "37002-P1", "人工地形_状態": "取得不可"},
        {"ID": "37003-P1", "人工地形_状態": "取得不可"},
    ], ["ID", "人工地形_状態"])

    df, missing_prefs = count_missing(tmp_path)
    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_37 = df[df["県コード"] == "37"].iloc[0]
    row_all = df[df["県コード"] == "全国"].iloc[0]

    # 36 の確認
    assert row_36["人工地形_範囲外_碑"] == 1
    assert row_36["人工地形_範囲外_比較地点"] == 2
    assert row_36["人工地形_取得不可_碑"] == 1
    assert row_36["人工地形_取得不可_比較地点"] == 0

    # 37 の確認
    assert row_37["人工地形_範囲外_碑"] == 2
    assert row_37["人工地形_範囲外_比較地点"] == 1
    assert row_37["人工地形_取得不可_碑"] == 0
    assert row_37["人工地形_取得不可_比較地点"] == 2

    # 全国合計の確認
    assert row_all["人工地形_範囲外_碑"] == 3
    assert row_all["人工地形_範囲外_比較地点"] == 3
    assert row_all["人工地形_取得不可_碑"] == 1
    assert row_all["人工地形_取得不可_比較地点"] == 2


def test_artificial_missing_files(tmp_path, capsys):
    """
    (b) 人工地形のファイルがない県：結果の行に入る、missing_prefs に入らない、4列が空欄、
    全国の合計に入らない、画面の1行目に県名と run_artificial_batch.py の案内が出ることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 36 は人工地形も含めて作成
    m_36 = [{"ID": "36001", "取得状態": "正常"}]
    p_36 = [{"ID": "36001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "36", m_36, p_36, [{"ID": "36001", "地形分類_状態": "データなし"}], [{"ID": "36001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_artificial_36.csv", [{"ID": "36001", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_points_36.csv", [{"ID": "36001-P1", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])

    # 37 は既存の8ファイルのみ（人工地形なし）
    m_37 = [{"ID": "37001", "取得状態": "正常"}]
    p_37 = [{"ID": "37001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "37", m_37, p_37, [{"ID": "37001", "地形分類_状態": "データなし"}], [{"ID": "37001-P1", "地形分類_状態": "データなし"}])

    # 38 は人工地形の片方（landform_artificial_38.csv）だけ作成
    m_38 = [{"ID": "38001", "取得状態": "正常"}]
    p_38 = [{"ID": "38001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "38", m_38, p_38, [{"ID": "38001", "地形分類_状態": "データなし"}], [{"ID": "38001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_artificial_38.csv", [{"ID": "38001", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])

    df, missing_prefs = count_missing(tmp_path)

    assert "36" not in missing_prefs
    assert "37" not in missing_prefs
    assert "38" not in missing_prefs
    assert list(df["県コード"]) == ["36", "37", "38", "全国"]

    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_37 = df[df["県コード"] == "37"].iloc[0]
    row_38 = df[df["県コード"] == "38"].iloc[0]
    row_all = df[df["県コード"] == "全国"].iloc[0]

    art_cols = COLUMNS[26:30]
    for col in art_cols:
        assert row_37[col] == ""
        assert row_38[col] == ""

    # 全国の合計は 36 だけの値になる
    assert row_all["人工地形_範囲外_碑"] == row_36["人工地形_範囲外_碑"] == 1
    assert row_all["人工地形_範囲外_比較地点"] == row_36["人工地形_範囲外_比較地点"] == 1
    assert row_all["人工地形_取得不可_碑"] == row_36["人工地形_取得不可_碑"] == 0
    assert row_all["人工地形_取得不可_比較地点"] == row_36["人工地形_取得不可_比較地点"] == 0

    main(base_dir=tmp_path)
    out = capsys.readouterr().out
    expected_msg = '人工地形のファイルが足りない県：香川県（37）、愛媛県（38）（人工地形の列は空欄です。先に実行してください：python src/run_artificial_batch.py --pref "37,38"）'
    assert expected_msg in out


def test_artificial_display_lines_and_mismatch(tmp_path, capsys):
    """
    (c) 画面の3行が地域版の行の直後にこの順で出る。
    範囲外と詳細版のデータなしの数が違う県があると、3行目が「不一致の県があります」と県名・案内になることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"

    # 一致するケース（36）
    m_36 = [{"ID": "36001", "取得状態": "正常"}, {"ID": "36002", "取得状態": "正常"}]
    p_36 = [{"ID": "36001-P1", "取得状態": "正常"}, {"ID": "36002-P1", "取得状態": "正常"}]
    land_m_36 = [{"ID": "36001", "地形分類_状態": "データなし"}, {"ID": "36002", "地形分類_状態": "取得済"}]
    land_p_36 = [{"ID": "36001-P1", "地形分類_状態": "データなし"}, {"ID": "36002-P1", "地形分類_状態": "取得済"}]
    _create_base_8_files(proc_dir, "36", m_36, p_36, land_m_36, land_p_36)
    create_dummy_csv(proc_dir / "landform_region_36.csv", [
        {"ID": "36001", "碑名": "碑1", "地域版_状態": "取得済（地域版）"},
        {"ID": "36002", "碑名": "碑2", "地域版_状態": "取得済（地域版）"}
    ], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_region_points_36.csv", [
        {"ID": "36001-P1", "碑名": "比較地点", "地域版_状態": "取得済（広域版）"},
        {"ID": "36002-P1", "碑名": "比較地点", "地域版_状態": "取得済（広域版）"}
    ], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_36.csv", [
        {"ID": "36001", "人工地形_状態": "範囲外"},
        {"ID": "36002", "人工地形_状態": "人工地形なし"}
    ], ["ID", "人工地形_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_points_36.csv", [
        {"ID": "36001-P1", "人工地形_状態": "範囲外"},
        {"ID": "36002-P1", "人工地形_状態": "取得済"}
    ], ["ID", "人工地形_状態"])

    main(base_dir=tmp_path)
    lines = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    idx = next(i for i, l in enumerate(lines) if l.startswith("地形分類（地域版）のデータなしの碑："))
    assert lines[idx + 1] == "人工地形のファイルが足りない県：なし"
    assert lines[idx + 2] == "地形分類（人工地形）の範囲外：碑 1（50.0%）／比較地点 1（50.0%）、取得不可：碑 0／比較地点 0"
    assert lines[idx + 3] == "人工地形の範囲外と地形分類（詳細版）のデータなし：一致（碑 1・比較地点 1）"

    # 不一致があるケース（37・38を追加し、37は碑で不一致、38は比較地点で不一致）
    m_37 = [{"ID": "37001", "取得状態": "正常"}]
    p_37 = [{"ID": "37001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "37", m_37, p_37, [{"ID": "37001", "地形分類_状態": "データなし"}], [{"ID": "37001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_artificial_37.csv", [{"ID": "37001", "人工地形_状態": "人工地形なし"}], ["ID", "人工地形_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_points_37.csv", [{"ID": "37001-P1", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])

    m_38 = [{"ID": "38001", "取得状態": "正常"}]
    p_38 = [{"ID": "38001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "38", m_38, p_38, [{"ID": "38001", "地形分類_状態": "データなし"}], [{"ID": "38001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_artificial_38.csv", [{"ID": "38001", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_points_38.csv", [{"ID": "38001-P1", "人工地形_状態": "取得済"}], ["ID", "人工地形_状態"])

    main(base_dir=tmp_path)
    lines_mm = [line.strip() for line in capsys.readouterr().out.splitlines() if line.strip()]
    idx_mm = next(i for i, l in enumerate(lines_mm) if l.startswith("地形分類（地域版）のデータなしの碑："))
    assert lines_mm[idx_mm + 1] == "人工地形のファイルが足りない県：なし"
    assert lines_mm[idx_mm + 2].startswith("地形分類（人工地形）の範囲外：")
    assert lines_mm[idx_mm + 3] == '人工地形の範囲外と地形分類（詳細版）のデータなし：不一致の県があります：香川県（37）、愛媛県（38）（先に実行してください：python src/run_artificial_batch.py --pref "37,38"）'


def test_artificial_csv_bom_lf_and_30_columns(tmp_path):
    """
    (d) 出力の CSV が BOM 付き・LF（\r を含まない）、列が COLUMNS（30列）と同じ順であることを確認する
    """
    proc_dir = tmp_path / "data" / "processed"
    m_36 = [{"ID": "36001", "取得状態": "正常"}]
    p_36 = [{"ID": "36001-P1", "取得状態": "正常"}]
    _create_base_8_files(proc_dir, "36", m_36, p_36, [{"ID": "36001", "地形分類_状態": "データなし"}], [{"ID": "36001-P1", "地形分類_状態": "データなし"}])
    create_dummy_csv(proc_dir / "landform_region_36.csv", [{"ID": "36001", "碑名": "碑1", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_region_points_36.csv", [{"ID": "36001-P1", "碑名": "比較地点", "地域版_状態": "取得済（地域版）"}], ["ID", "碑名", "地域版_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_36.csv", [{"ID": "36001", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])
    create_dummy_csv(proc_dir / "landform_artificial_points_36.csv", [{"ID": "36001-P1", "人工地形_状態": "範囲外"}], ["ID", "人工地形_状態"])

    main(base_dir=tmp_path)
    out_csv = tmp_path / "output" / "missing_counts.csv"
    raw = out_csv.read_bytes()

    assert raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert len(COLUMNS) == 30

    df = pd.read_csv(out_csv, dtype={"県コード": str}, encoding="utf-8-sig")
    assert list(df.columns) == COLUMNS


def test_real_data_artificial():
    """
    (e) 実データでの照合（data/processed に47県の12ファイル〔既存の8＋地域版2＋人工地形2〕がそろっているときだけ。なければ pytest.skip）
    """
    root = get_project_root()
    proc_dir = root / "data" / "processed"

    required_suffixes = [
        "elevation_{}.csv", "elevation_points_{}.csv",
        "hazard_{}.csv", "hazard_points_{}.csv",
        "landform_{}.csv", "landform_points_{}.csv",
        "river_coast_{}.csv", "river_coast_points_{}.csv",
        "landform_region_{}.csv", "landform_region_points_{}.csv",
        "landform_artificial_{}.csv", "landform_artificial_points_{}.csv",
    ]

    for pref in PREFECTURES.keys():
        for pattern in required_suffixes:
            if not (proc_dir / pattern.format(pref)).exists():
                pytest.skip("実データが47県×12ファイル分揃っていないためスキップします")

    df, missing_prefs = count_missing(root)
    assert len(missing_prefs) == 0

    pref_rows = df[df["県コード"] != "全国"]
    row_all = df[df["県コード"] == "全国"].iloc[0]
    row_36 = df[df["県コード"] == "36"].iloc[0]
    row_03 = df[df["県コード"] == "03"].iloc[0]
    row_13 = df[df["県コード"] == "13"].iloc[0]

    # 既存の26列の全国の値
    assert int(row_all["碑_数"]) == 2481
    assert int(row_all["比較地点_数"]) == 12395
    assert int(row_all["標高傾斜_取得不可_碑"]) == 2
    assert int(row_all["標高傾斜_取得不可_比較地点"]) == 62
    assert int(row_all["ハザード_取得不可_碑"]) == 0
    assert int(row_all["ハザード_取得不可_比較地点"]) == 0
    assert int(row_all["地形分類_データなし_碑"]) == 929
    assert float(row_all["地形分類_データなし_碑_割合"]) == 0.374
    assert int(row_all["地形分類_データなし_比較地点"]) == 4890
    assert float(row_all["地形分類_データなし_比較地点_割合"]) == 0.395
    assert int(row_all["河川標高_取得不可_碑"]) == 5
    assert int(row_all["河川標高_取得不可_比較地点"]) == 16
    assert int(row_all["河川_1000m超_碑"]) == 158
    assert int(row_all["河川_1000m超_比較地点"]) == 990
    assert int(row_all["海岸_対象外_碑"]) == 418
    assert int(row_all["海岸_対象外_比較地点"]) == 2090
    assert int(row_all["通信エラー_碑"]) == 0
    assert int(row_all["通信エラー_比較地点"]) == 0
    assert int(row_all["地域版_データなし_碑"]) == 5
    assert int(row_all["地域版_データなし_比較地点"]) == 118
    assert int(row_all["地域版_取得不可_碑"]) == 0
    assert int(row_all["地域版_取得不可_比較地点"]) == 0
    assert int(row_all["詳細版データなしを補えた_碑"]) == 927
    assert int(row_all["詳細版データなしを補えた_比較地点"]) == 4818

    # 全国 人工地形4列
    assert int(row_all["人工地形_範囲外_碑"]) == 929
    assert int(row_all["人工地形_範囲外_比較地点"]) == 4890
    assert int(row_all["人工地形_取得不可_碑"]) == 0
    assert int(row_all["人工地形_取得不可_比較地点"]) == 0

    # 徳島（36） 11・62・0・0
    assert int(row_36["人工地形_範囲外_碑"]) == 11
    assert int(row_36["人工地形_範囲外_比較地点"]) == 62
    assert int(row_36["人工地形_取得不可_碑"]) == 0
    assert int(row_36["人工地形_取得不可_比較地点"]) == 0

    # 岩手（03） 149・754・0・0
    assert int(row_03["人工地形_範囲外_碑"]) == 149
    assert int(row_03["人工地形_範囲外_比較地点"]) == 754
    assert int(row_03["人工地形_取得不可_碑"]) == 0
    assert int(row_03["人工地形_取得不可_比較地点"]) == 0

    # 東京（13） 4・16・0・0
    assert int(row_13["人工地形_範囲外_碑"]) == 4
    assert int(row_13["人工地形_範囲外_比較地点"]) == 16
    assert int(row_13["人工地形_取得不可_碑"]) == 0
    assert int(row_13["人工地形_取得不可_比較地点"]) == 0

    # 47県すべてで 人工地形_範囲外 と 地形分類_データなし が碑・比較地点とも同じ
    for _, r in pref_rows.iterrows():
        assert int(r["人工地形_範囲外_碑"]) == int(r["地形分類_データなし_碑"])
        assert int(r["人工地形_範囲外_比較地点"]) == int(r["地形分類_データなし_比較地点"])


