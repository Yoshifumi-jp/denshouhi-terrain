# ソース確認 M5（2回目）　確認日：2026-10-03

- 確認範囲：M5-02_fix の変更（src/make_map.py の build_popup_html・load_data、tests/test_make_map.py）と output/map_36.html
- ファイル消失：なし（make_map.py 14,072B、test_make_map.py 10,297B。報告と一致）
- pytest（Claude が別の場所のコピーで実行。本人のフォルダは変更なし）：67 passed、1 skipped（報告は 68 passed。skip の1件は Windows 以外で飛ばす既存テストで、環境の差）
- 実データの再実行：Claude の環境で作り直した map_36.html と、本人フォルダの map_36.html は、folium の乱数 ID を除いて完全一致
- 名前のある最寄り河川：9基すべてで距離が出る（例 瀬戸川 3416 m、牟岐川 367〜492 m）。「データなし」0件
- 標高のデータ種別：71基すべてに付く（1m（レーザ）52、5m（レーザ）18、5m（写真測量）1）
- ポップアップ全体に「nan」の文字なし
- テスト j・k・l は test_popup_contents にまとめて追加（実際の列名を使用）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| — | — | — | 指摘なし（M5_review-1 No.1〜5 は解消。No.6 は容認、No.7 は移動済み） | — |

## 判定：合格（修正1回目）。確認シート M5_check-1 へ
