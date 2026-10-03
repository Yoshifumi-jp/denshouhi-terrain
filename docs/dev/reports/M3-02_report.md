# 完了報告 M3-02

## 変更したファイル
| ファイル | 変更内容 |
|---|---|
| src/add_river_coast.py (11821 バイト) | 河川・海岸線のシェープファイルを読み込む `read_line_shapefile` 関数を追加し、既存の処理を置き換えました。 |
| tests/test_add_river_coast.py (8355 バイト) | `test_encoding_and_crs` を `read_line_shapefile` を呼ぶように修正し、`test_height_diff` を parametrize を使って5つのケースをテストするように修正しました。 |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `test_height_diff` で5つのケースをテストし、`test_encoding_and_crs` で `read_line_shapefile` を呼び出すようにしました。
  - `.venv\Scripts\python -m pytest` で全件合格を確認しました。
    (`============================= 33 passed in 8.68s ==============================`)
  - `.venv\Scripts\python src\add_river_coast.py --pref 36` を実行し、問い合わせ回数0回で正常終了し、修正前と同じ結果であることを確認しました。
  - 変更したファイルが空になっておらず、指定されたバイト数であることを確認しました。

## 残った課題・気になる点
特になし。

## 確認したいこと（あれば）
特になし。
