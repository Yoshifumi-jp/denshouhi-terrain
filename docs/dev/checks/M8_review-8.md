# ソース確認 M8（8回目＝M8-08_fix）　確認日：2026-10-04

- 確認範囲：作業中コミット a957263（M8-07 作業中）からの差分（src/build_site.py、tests/test_build_site.py、tests/test_update.py、src/make_map.py、docs/index.html、docs/map_36.html）
- 報告の実行結果とコードの表示文の照合：build_site.py の画面表示は print 文（443〜465行）と一致。pytest 134件＝M8-07 時点 127件＋新しいテスト関数 7件（test_build_site.py 5→12）で一致。改行コードの確認コマンドの出力（4つとも False）は実ファイルと一致（CR を含む行 0）
- Claude の再実行：tests/test_build_site.py・test_make_map.py・test_update.py で 41 passed（12＋17＋12）
- 変わってはいけないファイルのハッシュ：3件とも不変
- src/make_map.py・tests/test_update.py：改行コード以外の変更なし（git diff --ignore-cr-at-eol で差分0）。make_map.py 21979→21464 バイト＝CR 515個分の減少で一致
- 不具合 No.1・3・4・5・10（M8_review-6）と R7-1（M8_review-7）：すべて直っている
  - ハザードの節が「伝承内容の分析」の後・「データのダウンロード」の前に入った
  - 表の4行が指示書 M8-06 3章の expected_rows と完全に一致
  - 「ハザード情報取得日：2026-10-04」は hazard_36.csv の「取得日」から取っている（直書きなし）
  - 出典のリンク先が https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html になった
  - 注意文は「ご利用上の注意」の1か所だけ
  - docs/map_36.html は output/map_36.html と同一
- 「テストが本当に誤りを見つけるか」：前後のバイト数あり。M8_review-7 No.2 は解消

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | temp_rows.py（プロジェクト直下） | 作業中にできた作業用ファイル（208バイト、Git 管理外）。AGENTS.md の「作業用のスクリプトを作らない」に反する | Claude が _to_delete/M8-08_work/ へ移動済み |
| 2 | 軽微 | 報告書 | 見出しが「作業報告」でテンプレートの「完了報告」と違う | 対応不要（記録のみ） |

## 判定：合格（修正5回目。M8-07 の未達分を含めて合格）
- 次は確認シート M8_check-1（計画書の確認項目①〜④）
