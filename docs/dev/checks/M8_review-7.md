# ソース確認 M8（7回目＝M8-07_fix）　確認日：2026-10-04

- 確認範囲：作業中コミット a9b8fe5（M8-06 作業中）からの差分（src/make_map.py、tests/test_make_map.py、output/map_36.html）＋ load_data・build_map の影響範囲
- 報告の実行結果とコードの表示文の照合：make_map.py の画面表示 12行は print 文（504〜512行）と一致。pytest 127件＝M8-06 時点 121件＋新しいテスト関数 6件で一致。**改行コード「LF」の記載は事実と違う（下の No.1）**
- Claude の再実行（Claude の作業環境。geopandas がないため test_add_landform・test_add_river_coast の24件は除外）：tests/test_make_map.py は **17 passed**（実データの test_real_hazard_popup も skip されずに合格）。全体は 100 passed・3 failed（test_add_hazard::test_launch_method、test_make_comparison_points::test_target_logic、test_summarize_hazard::test_j_script_launch。いずれも Windows の .venv の起動や未導入モジュールによるもので、Claude の環境だけの失敗と判断。推測ですが、本人の環境では合格）
- 変わってはいけないファイルのハッシュ：hazard_summary_36.csv 9a96085d74dcb2a6、hazard_36.csv b191e3742645ec6c、hazard_points_36.csv 99c87b0ba59527e8 → 3件とも不変
- 不具合 No.2・8・9（M8_review-6）：直っている。overlay=True・control=True の追加、hazard_lines の1行化、取得日を load_data の「ハザード取得日」から取る、凡例の注記の html.escape、すべて指示どおり
- 追加テスト a〜e・g：指示書のコードどおり。g の期待値は指示書 M8-06 8章 g と一致

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | src/make_map.py 全体 | 改行コードが CRLF のまま（CR を含む行 515行。M7 合格時 66c4db7 は 0行）。M8_review-6 No.10 が直っていない。報告書の「改行コード LF」「LF であることを確認しました」は事実と違う | M8-08_fix に追加（同じ「改行コード」の不具合のため。確かめ方の PowerShell コマンドを明記） |
| 2 | 軽微 | 報告書 | 「テストが本当に誤りを見つけるか」で、元に戻す前後のバイト数を書いていない（指示書で求めた項目） | M8-08 報告で求める |
| 3 | 軽微 | tests/test_make_map.py.patch | 作業中にできた不要ファイル（UTF-16、32バイト、中身は「import pytest」1行。Git 管理外） | Claude が _to_delete/M8-07_work/ へ移動済み |

## 判定：不合格（修正4回目。中1件＝改行コードのみ。コードの中身は合格水準）
- 修正の上限（5回）の範囲で収めるため、No.1 は M8-08_fix（5回目）に「make_map.py の改行コードだけ LF に戻す」として加え、M8_review-8 で一緒に確かめる
