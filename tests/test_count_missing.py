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
