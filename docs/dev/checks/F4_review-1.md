# ソース確認 F4（第4版 最終確認・1回目）　確認日：2026-10-19

- 確認範囲：第4版の全ソース。aa6277e（最終合格（第3版））から 691c7af（M20 合格）までの src・tests・README・AGENTS・.gitignore の差分（21ファイル、追加4,532行・削除69行）と、公開されるファイル全体
- 報告の実行結果とコードの表示文の照合：M18-01〜M20-04 の各回で実施済み（すべて一致）

## 確認した観点と結果
| 観点 | 結果 |
|---|---|
| 不要ファイル | なし。未追跡ファイルなし（git status が空） |
| 秘密情報・個人情報 | src・tests・README・AGENTS・公開ページ・docs/dev に Windows のユーザー名を含むパス・APIキー・メールアドレスなし（見つかったのは AGENTS.md の決まりの文と check_public.py の検出用の説明だけ） |
| コメントの日本語 | 新しい3ファイル（add_landform_artificial・run_artificial_batch・summarize_artificial）は日本語。英字だけのコメントは1行（下表 No.1。summarize_artificial.py 1行目の `# -*- coding: utf-8 -*-` は文字コードの指定でコメントではない） |
| 秘密情報の置き場（.env） | 新しいプログラムは APIキー等を使わない。.gitignore に .env あり |
| 必要なパッケージ | 新しいプログラムが使うのは pandas・shapely と標準ライブラリだけで、requirements.txt にある |
| 改行 | 変更した src・tests・README に CR なし（LF） |
| README との整合 | 状態の行（第4版）、「できること」の人工地形3行、使い方「5. 人工地形だけを作る」、update.py・update_all.py に人工地形の段階を含む旨、PDF 8ページ、出典、注意。コマンド名・出力ファイル名はソースと一致（M19_review-4 の README の軽微1件は解消済み） |
| 既存の結果の不変 | v4_hashes.md の198ファイル（徳島のハザード3件を含む）を 2026-10-19 に再計算し、すべて一致（取得日を除く比較を含む） |
| 自動テスト | テスト関数318（パラメータ付きの展開で323件）。M20-03 の実行で 323 passed |

## 指摘（重大・中 0件。軽微はすべて動作に影響なし）
| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 軽微 | src/add_landform_artificial.py 177行 | 英字だけのコメント「key: (x, y), value: geojson_dict or "error"」（第3版 F3_review-1 No.4 と同じ形） | 記録のみ・第5版以降 |
| 2 | 軽微 | tests/test_add_landform_artificial.py test_j | 日付をまたいで実行すると取得日が変わり失敗しうる（M18_review-1） | 記録のみ・第5版以降 |
| 3 | 軽微 | src/summarize_artificial.py `_count_by_category` | 取得済で名前が空の地点の扱い（今は0件。M19_review-2） | 記録のみ・第5版以降 |
| 4 | 軽微 | tests/test_update_all.py | 末尾の空行・docstring（M19_review-4 の2件） | 記録のみ・第5版以降 |
| 5 | 軽微 | src/make_national_pdf.py | 指示書にない matplotlib.use("Agg")（影響なし）、表Bの注で「割合」が行をまたぐ（M20_review-3 の2件） | 記録のみ・第5版以降 |
| 6 | 軽微 | output/artificial_batch_log.csv | 試しの実行の行が重複（M19_review-1。集計には使わない） | 記録のみ |

## 判定：合格（重大・中 0件）。最終確認シート F4_check-1 がすべて○になれば完全合格
