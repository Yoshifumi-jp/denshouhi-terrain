# 完了報告 M1-01

## 変更したファイル
| ファイル | 変更内容 |
|---|---|
| `requirements.txt` | 新規作成。`pandas` と `pytest` を追加 |
| `src/prefectures.py` | 新規作成。都道府県コード（01〜47）と都道府県名の対応表を定義 |
| `src/load_monuments.py` | 新規作成。元データの読み込み、バリデーション、列の追加（災害種別フラグなど）、都道府県での絞り込み、および `data/processed/` への保存処理を実装 |
| `tests/data/sample.csv` | 新規作成。テスト用のダミーデータ（5行）を作成 |
| `tests/test_load_monuments.py` | 新規作成。データ整形、絞り込み、バリデーション、保存後の読み直し、および実データを利用した件数確認の自動テストを実装 |

## 開発環境情報
- **使用したPythonのバージョン**: Python 3.12.10
- **環境構築コマンド (PowerShell)**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\pip install -r requirements.txt
  ```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python src/load_monuments.py --pref 36` にて「徳島県 71基」と表示され、`data/processed/monuments_36.csv` が作成されることを確認しました。
  - `python src/load_monuments.py --pref 12` にて「千葉県 52基」と表示されることを確認しました。
  - `python src/load_monuments.py --pref all` にて全国 2,481基と、都道府県ごとの一覧が表示されることを確認しました。
  - `python src/load_monuments.py --pref 99` にてエラーメッセージが出て処理が止まることを確認しました。
  - `python -m pytest tests/test_load_monuments.py` を実行し、全件合格することを確認しました。

## 残った課題・気になる点
特になし

## 確認したいこと（あれば）
特になし
