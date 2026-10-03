import argparse
import sys
import re
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent

try:
    from src.prefectures import PREFECTURES
except ImportError:
    from prefectures import PREFECTURES

REQUIRED_COLUMNS = [
    "ID", "碑名", "建立年", "所在地", "災害名", "災害種別", 
    "伝承内容", "緯度", "経度", "公開日", "修正等公開日", "制限事項"
]

DISASTER_TYPES = ["洪水", "地震", "津波", "土砂災害", "高潮", "火山災害", "その他"]

def get_latest_raw_csv(base_dir=None):
    """
    最新の日付フォルダから元データのCSVファイルのパスを取得する。
    
    Args:
        base_dir (str, optional): データのルートディレクトリのパス。デフォルトは None (PROJECT_ROOT/data/raw)
    Returns:
        str: 最新のCSVファイルの絶対パス
    """
    if base_dir is None:
        base_dir = PROJECT_ROOT / "data" / "raw"
    base_path = Path(base_dir)
    if not base_path.exists():
        raise FileNotFoundError(f"エラー: データディレクトリが見つかりません: {base_dir}")
    
    dirs = [d for d in base_path.iterdir() if d.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', d.name)]
    if not dirs:
        raise FileNotFoundError(f"エラー: {base_dir} 内に日付フォルダが見つかりません。")
        
    latest_dir = sorted(dirs)[-1]
    csv_files = list(latest_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"エラー: フォルダ {latest_dir} 内にCSVファイルが見つかりません。")
    if len(csv_files) >= 2:
        file_names = ", ".join([f.name for f in csv_files])
        raise ValueError(f"エラー: 最新のフォルダ {latest_dir.name} に複数のCSVファイルが存在します。どれを使用するか指定してください: {file_names}")
    
    return str(csv_files[0])

def get_fetch_date(csv_path):
    """
    CSVファイルのパスからデータ取得日を判定する。
    
    Args:
        csv_path (str): CSVファイルのパス
    Returns:
        str: 取得日（YYYY-MM-DD）。判定できない場合は "不明"
    """
    dir_name = Path(csv_path).parent.name
    if re.match(r'^\d{4}-\d{2}-\d{2}$', dir_name):
        return dir_name
    else:
        print("警告: データ取得日を判定できません")
        return "不明"

def load_csv(csv_path):
    """
    CSVファイルを読み込む。
    
    Args:
        csv_path (str): 読み込むCSVファイルのパス
    Returns:
        pd.DataFrame: 読み込んだデータのDataFrame
    """
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig', dtype=str)
        return df
    except Exception as e:
        raise ValueError(f"エラー: CSVの読み込みに失敗しました: {e}")

def validate_dataframe(df):
    """
    DataFrameが要件を満たしているか検査する。
    必須の列が存在するか、IDの形式が正しいかを確認する。
    
    Args:
        df (pd.DataFrame): 検査対象のDataFrame
    Raises:
        ValueError: 必須の列が欠けている、またはIDの形式が不正な場合
    """
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"エラー: 必須の列が欠けています: {', '.join(missing_cols)}")
    
    invalid_ids = df[~df['ID'].str.match(r'^\d{5}-\d{3}$', na=False)]['ID'].tolist()
    if invalid_ids:
        raise ValueError(f"エラー: IDの形式が不正な行があります: {', '.join(map(str, invalid_ids))}")

def decompose_disaster_types(df):
    """
    災害種別の分解と列追加を行う。
    「県コード」「市区町村コード」列、および各災害種別ごとのダミー変数（0/1）の列を追加する。
    
    Args:
        df (pd.DataFrame): 対象のDataFrame
    Returns:
        pd.DataFrame: 列が追加されたDataFrame
    """
    df = df.copy()
    
    df['県コード'] = df['ID'].str[:2]
    df['市区町村コード'] = df['ID'].str[:5]
    
    unknown_types = {}
    
    for dtype in DISASTER_TYPES:
        df[f'種別_{dtype}'] = 0
        
    for idx, row in df.iterrows():
        types_str = str(row['災害種別'])
        if pd.isna(types_str) or types_str.strip() == '' or types_str.strip() == 'nan':
            continue
            
        types = [t.strip() for t in types_str.split('・') if t.strip()]
        for t in types:
            if t in DISASTER_TYPES:
                df.at[idx, f'種別_{t}'] = 1
            else:
                unknown_types[t] = unknown_types.get(t, 0) + 1
                
    if unknown_types:
        for t, count in unknown_types.items():
            print(f"警告: 未知の災害種別 '{t}' が {count} 件見つかりました。")
            
    return df

def filter_by_prefecture(df, pref_code):
    """
    指定された県コードでDataFrameを絞り込む。
    
    Args:
        df (pd.DataFrame): 対象のDataFrame
        pref_code (str): 県コード (01-47 または "all")
    Returns:
        pd.DataFrame: 絞り込まれたDataFrame
    """
    if pref_code != "all":
        df = df[df['県コード'] == pref_code].copy()
    return df

def check_locations(df, pref_code):
    """
    所在地が指定された県の名称で始まっているか確認し、一致しない場合は警告を表示する。
    
    Args:
        df (pd.DataFrame): 対象のDataFrame
        pref_code (str): 県コード (01-47 または "all")
    """
    if pref_code == "all":
        return
    pref_name = PREFECTURES.get(pref_code)
    if not pref_name:
        return
        
    mismatch_mask = ~df['所在地'].str.startswith(pref_name, na=False)
    mismatch_ids = df[mismatch_mask]['ID'].tolist()
    if mismatch_ids:
        print(f"警告: 所在地が {pref_name} で始まらないIDがあります: {', '.join(map(str, mismatch_ids))}")

def save_dataframe(df, pref_code, output_dir=None):
    """
    DataFrameをCSVファイルとして保存する。
    
    Args:
        df (pd.DataFrame): 保存するDataFrame
        pref_code (str): 県コード (ファイル名に使用)
        output_dir (str, optional): 保存先のディレクトリ。デフォルトは None (PROJECT_ROOT/data/processed)
    Returns:
        Path: 保存されたファイルのパス
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "processed"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filename = f"monuments_{pref_code}.csv"
    filepath = Path(output_dir) / filename
    
    df = df.sort_values('ID')
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    return filepath

def print_summary(df, pref_code, fetch_date, filepath):
    """
    処理結果のサマリを標準出力に表示する。
    
    Args:
        df (pd.DataFrame): 処理結果のDataFrame
        pref_code (str): 県コード
        fetch_date (str): データの取得日
        filepath (Path): 保存先のファイルパス
    """
    print(f"データ取得日: {fetch_date}")
    
    if pref_code == "all":
        print("対象の県名: 全国")
    else:
        print(f"対象の県名: {PREFECTURES[pref_code]}")
        
    print(f"基数: {len(df)}基")
    
    print("災害種別ごとの基数:")
    for t in DISASTER_TYPES:
        col = f'種別_{t}'
        if col in df.columns:
            count = df[col].sum()
            print(f"  {t}: {count}基")
            
    if pref_code == "all":
        print("都道府県ごとの基数:")
        counts = df['県コード'].value_counts().sort_index()
        for code, count in counts.items():
            pref_name = PREFECTURES.get(code, "不明")
            print(f"  {pref_name}({code}): {count}基")
            
    print(f"保存先のファイル名: {filepath}")

def main():
    """
    メイン処理。引数を解析し、データの読み込み、整形、保存を行う。
    """
    parser = argparse.ArgumentParser(description='伝承碑データの読み込みと整形')
    parser.add_argument('--raw', type=str, help='元データのCSVファイルのパス')
    parser.add_argument('--pref', type=str, required=True, help='県コード (01-47 または all)')
    args = parser.parse_args()
    
    pref_code = args.pref
    if pref_code != "all" and pref_code not in PREFECTURES:
        print("エラー: --pref には 01〜47 のいずれか、または all を指定してください。")
        sys.exit(1)
        
    try:
        csv_path = args.raw
        if not csv_path:
            csv_path = get_latest_raw_csv()
            
        fetch_date = get_fetch_date(csv_path)
        
        df = load_csv(csv_path)
        validate_dataframe(df)
        
        df = decompose_disaster_types(df)
        df['データ取得日'] = fetch_date
        
        df = filter_by_prefecture(df, pref_code)
        check_locations(df, pref_code)
        
        filepath = save_dataframe(df, pref_code)
        
        print_summary(df, pref_code, fetch_date, filepath)
    except Exception as e:
        print(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
