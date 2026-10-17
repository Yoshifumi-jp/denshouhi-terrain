# ソース確認 M17（1回目：M17-01）　確認日：2026-10-16

- 確認範囲：b110617（M16 合格）からの差分＋影響範囲（src/make_map.py、src/build_site.py、tests/test_make_map.py、tests/test_build_site.py、output/map_36・03・38・43.html、docs/map_36.html、docs/pref_36.html、docs/data/landform_region_36.csv）
- 報告の実行結果とコードの表示文の照合：一致（「地形分類を地域版で補った碑: 」「地形分類のデータなし（地域版でも補えない）: 」の2行は print 文どおり。build_site の作成ファイル一覧に landform_region_36.csv）
- 既知の答えとの照合（Claude が map_XX.html から数え直し）：
  - 補った碑／データなし：徳島 11／0、岩手 149／0、愛媛 14／1、熊本 54／1（すべて一致）
  - map_36.html：「データなし」0、「山地（地域版）」10、「低地（地域版）」1、他の分類の数は不変（砂州・砂丘21、氾濫平野・海岸平野18、山地斜面等13）
  - 個別7件：報告どおり
- テスト：追加4関数（make_map 3・build_site 1）、既存テストの変更なし → 264＋4＝268 と報告の 268 passed が一致
- バイト数：報告と一致。CR 0（py・html・csv）。docs/data/landform_region_36.csv は output と同一（cmp）
- data/ の変更なし、output/ の変更は map_XX.html の4つだけ（v3_hashes の100ファイル・地域版のファイルは不変）
- 地図の差分は、ポップアップの「地形分類：」の行・凡例の注意1行・folium の要素ID（乱数）だけ

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/make_map.py main()（522〜531行付近） | 「地域版で補ったか」の判定を build_popup_html と main で二重に書いている（決まりを変えるときに片方だけ直す恐れ）。動作は一致 | 記録のみ |

## 判定：合格（M17-01、修正0回）
