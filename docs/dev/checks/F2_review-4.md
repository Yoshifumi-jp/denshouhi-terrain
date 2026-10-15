# ソース確認 F2（4回目）　確認日：2026-10-15

- 確認範囲：a6fd615 からの差分（src/build_national.py・src/make_national_pdf.py・tests/test_build_national.py・docs/index.html・PDF 2件）
- 報告の実行結果とコードの表示文の照合：一致（make_national_pdf の4行・build_national の7行は print 文どおり、git status 7行・numstat も Claude の実行と一致。バイト数6件を実測で照合し一致）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 確認済（指摘なし） | src 2ファイル | 指示どおり。build_national は1行の置き換え、make_national_pdf は if／else 4行→1行。hazard_layers・build_site・make_map は変更なし | — |
| 2 | 確認済（指摘なし） | docs/index.html | 「【徳島県】津波：徳島県は2025年9月に…」になり、「徳島県：津波：」は0件 | — |
| 3 | 確認済（指摘なし） | national_report.pdf | docs と output は同一（621,083 バイト）。6ページ・A4、作成者等のメタデータなし。6ページ目の「ご利用上の注意」に「【徳島県】津波：…」と出ることを Claude が文字の取り出しと画像で確認（はみ出し・文字化けなし） | — |
| 4 | 確認済（指摘なし） | tests/test_build_national.py | 指示どおりの1件。pytest 224＝223＋1 | — |

## 判定：合格（F2-03）
