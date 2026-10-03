import pytest
import pandas as pd
from pathlib import Path
import sys

# src へのパスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.load_monuments import (
    load_csv,
    validate_dataframe,
    decompose_disaster_types,
    filter_by_prefecture,
    save_dataframe,
    get_latest_raw_csv,
    get_fetch_date
)

SAMPLE_CSV = Path(__file__).parent / "data" / "sample.csv"
REAL_DATA_CSV = Path(__file__).parent.parent / "data" / "raw" / "2026-09-24" / "denshouhi_20260924.csv"

def test_decompose_disaster_types():
    df = load_csv(SAMPLE_CSV)
    df = decompose_disaster_types(df)
    
    # a. 「地震・津波」の行で 種別_地震=1、種別_津波=1、それ以外の種別=0 になる
    row = df[df['ID'] == '36001-001'].iloc[0]
    assert row['種別_地震'] == 1
    assert row['種別_津波'] == 1
    assert row['種別_洪水'] == 0
    assert row['種別_土砂災害'] == 0
    assert row['種別_高潮'] == 0
    assert row['種別_火山災害'] == 0
    assert row['種別_その他'] == 0

def test_filter_by_prefecture():
    df = load_csv(SAMPLE_CSV)
    df = decompose_disaster_types(df)
    
    # b. 県コードで絞り込んだ件数が正しい
    df_36 = filter_by_prefecture(df, "36")
    assert len(df_36) == 2
    
    df_12 = filter_by_prefecture(df, "12")
    assert len(df_12) == 2
    
    df_01 = filter_by_prefecture(df, "01")
    assert len(df_01) == 1
    
    df_all = filter_by_prefecture(df, "all")
    assert len(df_all) == 5

def test_validate_missing_columns(tmp_path):
    df = load_csv(SAMPLE_CSV)
    df = df.drop(columns=["碑名"])
    invalid_csv = tmp_path / "invalid.csv"
    df.to_csv(invalid_csv, index=False, encoding="utf-8-sig")
    
    df_invalid = load_csv(invalid_csv)
    # c. 必須の列が欠けたCSVで、処理が止まる（例外になる）
    with pytest.raises(ValueError, match="必須の列が欠けています"):
        validate_dataframe(df_invalid)

def test_validate_invalid_id(tmp_path):
    df = load_csv(SAMPLE_CSV)
    df.at[0, "ID"] = "123-456" # 不正なフォーマット
    invalid_csv = tmp_path / "invalid_id.csv"
    df.to_csv(invalid_csv, index=False, encoding="utf-8-sig")
    
    df_invalid = load_csv(invalid_csv)
    # d. ID の形が不正な行があると処理が止まる
    with pytest.raises(ValueError, match="IDの形式が不正な行があります"):
        validate_dataframe(df_invalid)

def test_save_and_reload(tmp_path):
    df = load_csv(SAMPLE_CSV)
    df = decompose_disaster_types(df)
    df = filter_by_prefecture(df, "36")
    
    filepath = save_dataframe(df, "36", output_dir=str(tmp_path))
    
    # e. 保存したCSVを読み直して、日本語が文字化けせず、ID の先頭の0が残っている
    df_reloaded = pd.read_csv(filepath, encoding="utf-8-sig", dtype=str)
    
    # 日本語が文字化けしていないか（適当な列でチェック）
    assert df_reloaded.iloc[0]['碑名'] == "テスト碑1"
    
    # IDの先頭の0が残っているか
    # 今回36001ですが、北海道は01から始まるので、それをテストする
    df_01 = load_csv(SAMPLE_CSV)
    df_01 = decompose_disaster_types(df_01)
    df_01 = filter_by_prefecture(df_01, "01")
    filepath_01 = save_dataframe(df_01, "01", output_dir=str(tmp_path))
    
    df_01_reloaded = pd.read_csv(filepath_01, encoding="utf-8-sig", dtype=str)
    assert df_01_reloaded.iloc[0]['ID'] == "01001-001"

def test_get_latest_raw_csv_multiple_csvs(tmp_path):
    # a. 日付フォルダに CSV が2つあると処理が止まる（例外になる）
    raw_dir = tmp_path / "raw"
    date_dir = raw_dir / "2026-01-01"
    date_dir.mkdir(parents=True)
    (date_dir / "file1.csv").touch()
    (date_dir / "file2.csv").touch()
    
    with pytest.raises(ValueError, match="複数のCSVファイルが存在します"):
        get_latest_raw_csv(base_dir=raw_dir)

def test_get_latest_raw_csv_selects_latest_date(tmp_path):
    # b. 日付フォルダが複数あるとき、最も新しい日付のフォルダの CSV が選ばれる
    raw_dir = tmp_path / "raw"
    date_dir1 = raw_dir / "2026-01-01"
    date_dir1.mkdir(parents=True)
    (date_dir1 / "file1.csv").touch()
    
    date_dir2 = raw_dir / "2026-01-02"
    date_dir2.mkdir(parents=True)
    (date_dir2 / "file2.csv").touch()
    
    csv_path = get_latest_raw_csv(base_dir=raw_dir)
    assert Path(csv_path).name == "file2.csv"

def test_get_fetch_date_invalid_format(tmp_path):
    # c. 日付形式でない親フォルダの CSV を指定したとき、データ取得日が「不明」になる
    csv_path = tmp_path / "downloads" / "data.csv"
    assert get_fetch_date(csv_path) == "不明"

def test_get_fetch_date_valid_format(tmp_path):
    csv_path = tmp_path / "2026-01-01" / "data.csv"
    assert get_fetch_date(csv_path) == "2026-01-01"

@pytest.mark.skipif(not REAL_DATA_CSV.exists(), reason="実データが存在しません")
def test_real_data_counts():
    df = load_csv(REAL_DATA_CSV)
    validate_dataframe(df)
    df = decompose_disaster_types(df)
    
    # 徳島(36)=71基、千葉(12)=52基、全国=2481基
    df_36 = filter_by_prefecture(df, "36")
    assert len(df_36) == 71
    
    df_12 = filter_by_prefecture(df, "12")
    assert len(df_12) == 52
    
    df_all = filter_by_prefecture(df, "all")
    assert len(df_all) == 2481
