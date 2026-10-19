# ソース確認 M20（2回目：M20-02）　確認日：2026-10-18

- 確認範囲：4d7a50f（M20-02 作業中）からの差分＋影響範囲（src/build_national.py・tests/test_build_national.py、docs/index.html・docs/data/landform_artificial_all.csv・landform_artificial_cross_all.csv）
- 報告の実行結果とコードの表示文の照合：一致（まとめ表示の2行は print 文と同じ形、数のカンマも :, どおり。既存の行は不変）
- Claude の独立の照合（docs/index.html を読み直し）：MONUMENTS 2,481件・全件12要素、添字11の件数（盛土地・埋立地199・干拓地47・切土地39・改変工事中2・農耕平坦化地1・人工地形なし1,264・範囲外929）がデータ（landform_artificial_XX.csv）と ID 単位で不一致0。絞り込みの例（干拓地47〔愛知20・熊本9・三重7・佐賀6…〕、東京×盛土地・埋立地33、兵庫×切土地8、旧水部×干拓地47）一致。最初の200行はすべて10列。表A6行・表B24行・注 C 929・D 4,890・E 929 が既知の答えと一致。index.html の削除行は見出し1行・最初の200行・MONUMENTS・JS のコメントだけ（列の追加による置き換え）。docs/data の CSV 2つは output とバイト単位で同一。CR 0
- その他：pytest 321＝318＋3。作成したファイル 13

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | tests/test_build_national.py（test_national_region_column_and_filter の見出しの確認1行） | 既存テストの期待値を `…<th>地形分類（地域版）</th><th>建立年</th>` から `…<th>地形分類（地域版）</th>` に短くした。列の追加で避けられない変更で、報告にも書いてある（指示書側の書き漏れ）。ただし短くしたことで「地域版の次の列」の確認が弱くなった（新しいテストの `<th>人工地形</th>` の確認で実質は補われている） | 記録のみ |

## 判定：合格（修正0回）
