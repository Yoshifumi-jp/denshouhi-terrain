# ソース確認 M20（3回目：M20-03）　確認日：2026-10-18

- 確認範囲：55bf04e（M20-03 作業中）からの差分＋影響範囲（src/make_national_pdf.py、src/build_national.py、tests/test_make_national_pdf.py、docs/index.html、output/national_report.pdf、docs/national_report.pdf）
- 報告の実行結果とコードの表示文の照合：一致（make_national_pdf の追加1行「地形分類（人工地形）の表：…」は print 文と同じ文。build_national のまとめ表示は M20-02 と同じ）
- 変更ファイルのサイズ：報告どおり（make_national_pdf.py 45,336／build_national.py 63,799／test 14,934／PDF 677,585）。0バイト・巻き戻りなし。CR 0（LF）
- data/・output/ の CSV は変更なし（git status で変更は上の6ファイルと報告書だけ）
- docs/national_report.pdf と output/national_report.pdf は同一（cmp）。docs/index.html の差分は「A4・7ページ」→「A4・8ページ」の2か所だけ

## 照合（Claude が PDF を pdftotext と画像で確認）
- 8ページ・A4（595.44×841.68）。フッターは 1／8〜8／8
- 5ページ 表A 6行・表B 24行：既知の答え（M20-02 と同じ値・並び）と全行一致。注の C 929・D 4,890 一致
- 8ページ：出典「地形分類（人工地形）：国土地理院 地形分類（人工地形）」、注意「（範囲外の碑 929基）」あり。最後の注意とフッターは離れている
- 1ページ：目次7行、最後の行（8ページ　出典・ご利用上の注意）とフッターは重ならない（高解像度で確認）
- 5ページ：表・注が重ならず枠内。表Bの注の開始を 0.085→0.075 に調整（報告に記載あり）。最後の注とフッターは重ならない
- C・D・E の数え方は build_national.py（M20-02）と同じ条件（取得済・人工地形なし以外を数える／ファイルの無い県は monuments の数を足す）
- pytest 323 passed（テスト関数 316→318、parametrize 1 か所で計 321→323。追加2件 test_page_artificial_tables・test_page_artificial_missing）。表B のテストは 人工地形なし・碑0・移転碑を除く・注・出典 の行が入らないことと、同数時の並び（崖・段丘崖→旧河道）を確かめている

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/make_national_pdf.py 7〜8行、tests/test_make_national_pdf.py 3〜4行 | 指示書にない `matplotlib.use("Agg")`（画面を使わない描画方式の指定）を追加し、報告に記載がない。analyze_denshou.py・summarize_national.py と同じ書き方で、PDF の出力に影響はない | 記録のみ |
| 2 | 軽微 | src/make_national_pdf.py（表Bの注） | 折り返しで「割合」が「割／合」と行をまたぐ（wrap_text_with_kinsoku は語の途中で切る）。読めるため見た目の問題のみ | 記録のみ（直すなら M20-04 以降で文の区切り位置を指定） |

## 判定：合格（修正0回）
