# 完了報告 M6-02

## 変更したファイルとバイト数
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/update.py | 14,712 バイト | `do_run_steps`を`run_steps`に一本化、サブプロセスの実行パスを絶対パスに変更、画面表示のパスを相対パスに変更、完了記録読み込み失敗時の警告追加、print文に`flush=True`を追加 |
| tests/test_update.py | 14,661 バイト | テスト項目e, g, h, j, kを追加・修正。`determine_old_csv`の警告に関するテストを追加。 |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：すべて満たしていることを確認しました。

### pytest 実行結果
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: <プロジェクト>
collected 79 items

tests\test_add_elevation.py ...........                                  [ 13%]
tests\test_add_landform.py ......                                        [ 21%]
tests\test_add_river_coast.py ..................                         [ 44%]
tests\test_load_monuments.py ..........                                  [ 56%]
tests\test_make_comparison_points.py .........                           [ 68%]
tests\test_make_map.py .........                                         [ 79%]
tests\test_summarize.py .....                                            [ 86%]
tests\test_update.py ...........                                         [100%]

============================= 79 passed in 5.27s ==============================
```

### 実データの update.py (--dry-run) 実行結果
```
古いデータと新しいデータが同じファイルです
```
（新しいデータが来ていない状態であるため、期待通りの動きです。）

## 残った課題・気になる点
特になし

## 確認したいこと（あれば）
特になし
