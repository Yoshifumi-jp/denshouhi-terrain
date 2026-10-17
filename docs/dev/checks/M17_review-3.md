# ソース確認 M17（3回目：M17-03）　確認日：2026-10-17

- 確認範囲：a93641f（M17-02 作業中）からの差分＋影響範囲（src/make_national_pdf.py、src/build_national.py、tests/test_make_national_pdf.py、docs/index.html、output/national_report.pdf、docs/national_report.pdf）
- 報告の実行結果とコードの表示文の照合：一致（「地形分類（地域版）の表：」の1行は print 文どおり。「ページ数：」の直後）
- 既知の答えとの照合：ページ数7（pdfinfo で7ページ・A4 595.44×841.68）、表12行・A 5・B 118、碑2,481基、build_national のまとめ表示は M17-02 と同じ（作成したファイル11、地域版12区分＋データなし5基、集計表12行）。docs/index.html の差分は「A4・6ページ」→「A4・7ページ」の2か所だけ
- PDF の目視（Claude が画像にして確認）：
  - 1ページ：目次6行。最後の行「7ページ　出典・ご利用上の注意」とフッター「1／7」は重ならない（ただし間隔は約2pt と狭い）
  - 4ページ：題名・表12行（低地 1325 53.5% 4331 35.3% 〜 湖 1 0.0% 50 0.4%）・注2行。ページからのはみ出しなし（注2行目の右端 558pt、表の右端 548pt、ページ幅 595pt）
  - 7ページ：地域版の注意1文（値が取れなかった碑 5基）が地形分類の注意の直後。フッター「7／7」
- テスト：追加2関数（test_page_region_table・test_page_region_missing）、既存テストは 6→7 の期待値・docstring・コメントの書き換えのみ → 271＋2＝273 と報告の 273 passed が一致
- バイト数一致、CR 0、docs/national_report.pdf は output と同一（cmp）。data/ と output/ の CSV・図の変更なし

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/make_national_pdf.py make_page_1 目次 | 目次の最後の行とフッターの間が約2pt と狭い（重なりはない）。目次の開始位置を少し上げると見やすい | 記録のみ（必要なら M17-04 以降） |
| 2 | 軽微 | src/make_national_pdf.py make_page_region | 注2行目が表の右端より約10pt 右に出る（ページ内には収まる） | 記録のみ |
| 3 | 軽微 | src/make_national_pdf.py make_national_pdf | 地域版 A・B の数え方が build_national.py と二重書き（指示書で許可した範囲） | 記録のみ |

## 判定：合格（M17-03、修正0回）
