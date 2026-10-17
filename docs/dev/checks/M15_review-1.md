# ソース確認 M15（1回目）　確認日：2026-10-16

- 確認範囲：前回のコミット 5094e3a からの新しいファイル（src/add_landform_region.py・tests/test_add_landform_region.py・data/processed/landform_region_* 6件）。既存ファイルの変更なし（git status は「??」3件のみ。data/processed は .gitignore の対象）
- 報告の実行結果とコードの表示文の照合：一致（まとめ表示の文言・状態4行の順・名前の並び順は process_monuments の print と同じ。6回＋再実行の数値は指示書の既知の答えとすべて一致）
- バイト数：報告の9ファイルすべて実ファイルと一致。新しいファイルの \r は 0（Claude も確認）
- pytest：報告 238 passed（224＋新しいテスト関数14＝238、Claude がテスト関数の数で検算）。skip なし
- 実データの照合：Claude が出力 CSV から8件を確かめ、すべて既知の答えと一致。キャッシュは z13 225枚・z8 5枚（指示書の見込みどおり）
- 変わってはいけないファイル：docs/dev/v3_hashes.md の100件（landform 94・*_all 6）すべてハッシュ不変

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/add_landform_region.py _resolve_code | 覆う地物の code が空（None）のとき、状態は「取得済」で名前が空のまま「地形分類名ごとの件数」に空の名前で数えられる（詳細版 add_landform.py と同じ作り。実データでは0件） | 記録のみ |
| 2 | 軽微 | tests/test_add_landform_region.py | pytest 全体が 396秒かかっている（新しいテストの所要時間は未確認。推測ですが既存の実データテストが大半） | 記録のみ |

## 判定：合格（修正0回）。M15 は M15-02（update.py への組み込み）と確認シートの後に合格判定
