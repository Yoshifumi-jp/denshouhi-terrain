# ソース確認 M10（1回目）　確認日：2026-10-05

- 確認範囲：694d265（M9 合格）からの差分＋影響範囲（src/prefectures.py、src/add_river_coast.py、tests/test_prefectures.py、tests/test_add_river_coast.py）
- 報告の実行結果とコードの表示文の照合：まとめ表示は print 文の書式と一致。Claude が作業用の複製（本人のフォルダの外）で徳島を作り直し、monuments・points のまとめ表示が報告と同じ数値・「一致」2件であることを確認。**pytest の「155 passed」は再現しない**（下表 No.1）
- 確認の補足：報告に「文字化けしたため正しい日本語に復元して記載」とある。今回は内容が一致したが、AGENTS.md の「画面に出た文をそのまま貼る」に反する。文字化けするときは `$env:PYTHONIOENCODING="utf-8"` と `[Console]::OutputEncoding=[Text.Encoding]::UTF8` を先に実行してから貼る
- 良い点：系の判定（select_zone）は指示書・告示どおり。北海道の市町村コード42件・49件も一致。1件ごとの処理の中身は字下げ以外変わっていない

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 重大 | tests/test_add_river_coast.py 453・484・518行 | 追加テスト3件が、どこにも定義されていない `create_dummy_shapefiles`・`mock_fetch`・`mock_sleep` を使っており、NameError で失敗する（Claude の実行：3 failed）。報告の「155 passed」はこのファイルの最終版では出ない | M10-02_fix |
| 2 | 中 | tests/test_add_river_coast.py 503行付近 | 系が混ざるテストの距離の比較が `if pd.notna(...)` の中にあり、距離が空でも合格してしまう（確かめたいことを確かめていない） | M10-02_fix |
| 3 | 軽微 | src/add_river_coast.py make_epsg_by_id | 説明（docstring）がない。関数の中の `import pandas as pd` は不要（ファイルの先頭で読み込み済み） | M10-02_fix |
| 4 | 軽微 | src/add_river_coast.py main() | 「未設定」の判定を消した跡に空行が3行残っている | M10-02_fix |
| 5 | 軽微 | tests/test_add_river_coast.py 441行 | import がファイルの途中にある（先頭の import にまとめる） | M10-02_fix |
| 6 | 軽微 | 報告書 | _to_delete の .txt 3件のバイト数が実際と違う（報告 4872・536・3167 → 実際 9335・803・5231） | 次の報告で注意 |

## 判定：不合格（修正1回目へ）
