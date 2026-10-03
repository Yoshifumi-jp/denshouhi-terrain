# ソース確認 M3（2回目）　確認日：2026-10-01

- 確認範囲：ab108ad（M3-01 作業中）からの差分＋影響範囲（src/add_river_coast.py、tests/test_add_river_coast.py）。M3-02_fix・M3-03_impl の分
- ファイルサイズ：src/add_river_coast.py 16,170B、tests/test_add_river_coast.py 12,472B、reports/M3-02_report.md 1,408B、reports/M3-03_report.md 2,618B。報告の値と一致（0バイト・巻き戻りなし）
- 出力 river_coast_36.csv：71行、列は指示書 M3-03 の手順7どおり。河川_状態は 取得済66／参考値1／対象外4。高さの差マイナスは24基→1基（36402-001、参考値：10mメッシュ、−0.2m）。河川側の標高の種別は 1m（レーザ）42・5m（レーザ）22・5m（写真測量）2・10m 1
- 対象外4基：出羽島2基（3.3km）に加え、36204-003 福井住吉神社（福井川 1,050m）、36387-005 東由岐康暦碑（志和岐川 1,216m）。いずれも海岸まで100m以内の碑で、指示どおりの動き
- M3-02 の対応（M3_review-1 No.1・2・5）：read_line_shapefile の切り出し、test_encoding_and_crs の本体呼び出し、報告のバイト数一覧はいずれも確認済み

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | tests/test_add_river_coast.py 120–126行 | test_height_diff の場合1・2で、問い合わせ関数の種別を「10m」にし、期待する河川_状態を「取得済」から「取得済（参考値：10mメッシュ）」に変えている（指示書 M3-03 9 は「期待値は変えない」）。その結果、process_river_coast を通した「取得済」の経路が検査されていない。報告 M3-03 の「期待値は変えていません」とも食い違う | M3-04_fix |
| 2 | 軽微 | tests/test_add_river_coast.py 275–314行 | test_out_of_range で、対象外でも最寄り河川名・河川までの距離・河川最近点の緯度経度が記録されること（指示書 M3-03 手順2）を確かめていない | M3-04_fix |
| 3 | 軽微 | src/add_river_coast.py 5行・137行 | M3_review-1 No.3 の持ち越し：使っていない import glob と変数 p1（math は M3-03 で使用するようになった） | M3-04_fix |
| 4 | 軽微 | src/add_river_coast.py 11・14行 | M3_review-1 No.4 の持ち越し：warnings.filterwarnings("ignore") で全警告を消している | M3-04_fix |
| 5 | 軽微 | src/add_river_coast.py 23–51行 | make_bank_points は offsets が小さい順である前提で break している（既定値では問題なし） | 対応不要（記録のみ） |

## 判定：不合格（修正2回目へ）
- 本体の処理と実データの結果は妥当。不足はテスト1点（No.1、中）のみ
- M3-04_fix はテストの手直しと軽微な整理だけで、出力 river_coast_36.csv は変わらない。このため本人の確認シート M3_check-2 は M3-04_fix と並行して記入してよい
- 地形分類は M3-05_impl に番号を繰り下げる
