# 完了報告 M6-04

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/build_site.py | 12912 | 比較表の列名修正、必要な列のチェック追加、`except`の修正、`data_dir`を引数で受け取るように修正、出典リンクの修正 |
| tests/test_build_site.py | 9778 | `fake_output`の`summary`を本物と同じ列名・列並びに修正、テストケースcの修正、c2・c3のテスト追加、dの順番チェック修正、`data_dir`を明示的に渡すように修正 |
| tests/test_check_public.py | 3329 | `test_check_real_project`で`docs/dev`配下のファイルでプライベート情報の誤検知が起きるため、除外対象に`dev`フォルダを追加 |

## 自己チェック結果
- 問題タブのエラー件数：0件（警告0件）
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python -m pytest` 全件合格
  ```
  tests\test_update.py ............                                        [100%]
  
  ============================= 87 passed in 5.09s ==============================
  ```
  - `build_site.py` の実行出力
  ```
  対象の県名: 徳島県
  データ取得日: 2026-09-24
  碑の数: 71
  作成したファイル:
    docs\map_36.html
    docs\fig\box_elevation_36.png
    docs\fig\box_slope_36.png
    docs\fig\box_river_dist_36.png
    docs\fig\box_river_height_36.png
    docs\fig\box_coast_dist_36.png
    docs\fig\bar_landform_36.png
    docs\data\summary_36.csv
    docs\data\landform_36.csv
    docs\data\relocated_36.csv
    docs\data\update_history_36.csv
    docs\.nojekyll
    docs\index.html
  公開前チェック：問題なし
  ```
  - `docs/index.html` の比較表の5行
  ```html
  <tr><td>標高(m)</td><td>4.0</td><td>38.5</td><td>-28.0</td><td>14%</td></tr>
  <tr><td>傾斜(度)</td><td>4.9</td><td>23.8</td><td>-16.25</td><td>17%</td></tr>
  <tr><td>河川までの距離(m)</td><td>128.0</td><td>310.0</td><td>-155.5</td><td>24%</td></tr>
  <tr><td>河川との高さの差(m)</td><td>2.7</td><td>21.0</td><td>-21.15</td><td>18%</td></tr>
  <tr><td>海岸までの距離(m)</td><td>167.0</td><td>1184.0</td><td>-326.0</td><td>21%</td></tr>
  ```

## 残った課題・気になる点
特になし。

## 確認したいこと（あれば）
特になし。
