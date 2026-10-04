# ソース確認 F（1回目・F-01_fix）　確認日：2026-10-04

- 確認範囲：f9ec8fd（M8 合格）からの差分＝src/add_hazard.py、tests/test_add_hazard.py
- 報告の実行結果とコードの表示文の照合：一致
  - 差分は print 文の「県」1文字削除（13469→13466 バイト＝UTF-8 の1文字3バイト分）と assert 1行の追加のみ
  - 改行コード：2ファイルとも CR 0行（Claude が確認。報告の False と一致）
  - pytest 134 passed：テスト関数129＋parametrize 6件（関数1つ分を差し引き＋5）＝134 で検算一致。skipped 0件のため test_real_cache は passed
  - ハッシュ3件：Claude の計算でも 9a96085d74dcb2a6／b191e3742645ec6c／99c87b0ba59527e8 で不変
  - git status：「??」は指示書と報告書のみ。作業用ファイルなし

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| — | — | — | 指摘なし | — |

## 判定：合格（修正なし）。M8_review-6 No.11 は解消
