# ソース確認 M4（1回目）　確認日：2026-10-02

- 確認範囲：2d0097e（M3 合格）からの差分＋影響範囲
  - src/make_comparison_points.py（新規）、src/add_elevation.py、src/add_river_coast.py、src/add_landform.py
  - tests/test_make_comparison_points.py（新規）、tests/test_add_elevation.py、tests/test_add_river_coast.py、tests/test_add_landform.py
  - 実データ：data/processed/points_36.csv ほか points 系3ファイル、碑の側3ファイル、作業ログ（_to_delete/M4-01_work/）
- Claude 別環境での pytest：46 passed、1 skipped（test_cache_untouched。本物のキャッシュが無い環境のため。想定どおり）

## 確認できたこと（問題なし）
- 比較地点の作り方は指示どおり（距離の式、方角、碑IDを混ぜた乱数、最大50回、海上と通信エラーを分けて数える、Ctrl+C の表示）
- points_36.csv：349点（5点×69基、0点 36383-002、4点 36383-003）。災害種別・種別_7列は元の碑と全件一致
- points 系3ファイル：いずれも349行、ID・緯度・経度が points_36.csv と全件一致
- 再現性：points_36.csv（23:36 再作成）と、それより前に作られた points 系3ファイル（22:41〜23:31）の座標が全件一致 → 同じシード値で同じ点が再現されていることを Claude が確認
- 碑の側3ファイル：実行前のコピーと比べ「取得日」列以外の差 0件（取得日は再実行で更新される既存の仕様。問題なしと判断）
- `--target` は main とファイル名の関数（get_filenames）のみの変更。既定は今までと同じファイル名

## 指摘
| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | tests/test_make_comparison_points.py | テスト d・e・f が指示の確認内容を満たしていない。d：捨てた候補の数を確かめていない／e：候補が50回で止まることを確かめていない（呼び出し回数の確認なし）／f：IDの集合しか比べておらず、点の位置（緯度・経度）が並び順で変わらないことを確かめていない（乱数の作り方を誤ってもテストが通る） | M4-02_fix |
| 2 | 中 | reports/M4-01_report.md | 報告の内容が実際と食い違う。①add_landform（points）のまとめ：報告「取得済349／データなし0／問い合わせ348」と地形分類名の一覧 ⇔ 実際のログ・CSV「取得済287／データなし62／問い合わせ246」、名前も対応表どおり（「谷底平野・氾濫平野」等は存在しない）②変更ファイル一覧に tests/test_add_elevation.py・tests/test_add_river_coast.py が無い ③2回目の一致確認が「目視および行数確認」で、完全一致の確認になっていない | M4-02_fix（実行し直してまとめをそのまま貼る）、AGENTS.md に規則を追記 |
| 3 | 軽微 | tests/test_add_elevation.py、tests/test_add_river_coast.py | 改行コードが LF → CRLF（Windows形式）に変わり、git の差分が全行になっている | M4-02_fix |
| 4 | 軽微 | src/add_elevation.py・add_river_coast.py の process_〜 | 引数を「出力フォルダ」→「出力ファイル」に変更（指示は main のみの変更）。計算内容は同じで、既存テストの期待値も変わっていないため可とする | 対応不要（記録のみ） |
| 5 | 軽微 | src/add_landform.py 171〜182行（M3 からの既存処理） | タイルの code が空文字のとき「不明（code=）」・状態「取得済」になる（比較地点 36203-001-P5 の1件）。集計で1つの地形分類として数えられてしまう | M4-03_impl（集計）で扱いを決める |
| 6 | 参考 | elevation_points_36.csv | 比較地点のうち4点が標高「データなし」（周囲の点が海上で傾斜が出せないためと推測）。地形分類「データなし」62点とあわせ、M4-03 の集計で除外の扱いを明記する | M4-03_impl |

## 判定：不合格（修正1回目へ。中2件）
