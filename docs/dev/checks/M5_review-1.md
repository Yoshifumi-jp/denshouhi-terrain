# ソース確認 M5（1回目）　確認日：2026-10-03

- 確認範囲：896a137（M4 合格）からの差分（src/make_map.py 新規、tests/test_make_map.py 新規、tests/test_summarize.py、requirements.txt）と output/map_36.html
- ファイル消失：なし（make_map.py 13,774B、test_make_map.py 8,646B、test_summarize.py 16,120B、requirements.txt 100B。報告と一致）
- pytest（Claude が別の場所のコピーで実行。本人のフォルダは変更なし）：66 passed、1 skipped
- 実データの再実行：まとめ表示は報告と一致（津波49・高潮1・洪水10・土砂8・地震2・その他1＝71、移転碑2、比較地点なし 36383-002）
- テスト i（M4_review-4 No.1）：差 +5・0・−5 の3組で割合 0.333 を確かめている。解消

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | src/make_map.py build_popup_html | 名前のある河川の距離の列名を「名前のある最寄り河川までの距離_m」としているが、実際の列名は「名前のある河川までの距離_m」。最寄り河川が「名称不明」の碑（徳島9基の見込み）で、距離がすべて「データなし」になる（例 36383-002：瀬戸川（データなし）→ 正しくは 3416 m）。テストも同じ誤った列名を使っていないため見つけられていない | M5-02_fix |
| 2 | 中 | src/make_map.py build_popup_html | 標高に「データ種別」が出ない（指示書：`X m（データ種別）`。例 36201-001 は「1.6 m（1m（レーザ））」になるべき） | M5-02_fix |
| 3 | 軽微 | src/make_map.py build_popup_html | 「災害名 / 災害種別 / 建立年 / 所在地」が見出しなしで並び、「1861」「不明」が何の値か分からない（指示書の書き方があいまいだったため） | M5-02_fix に含める |
| 4 | 軽微 | src/make_map.py load_data | read_csv に encoding='utf-8-sig' がない（既存ファイルと書き方が違う。今は動いている） | M5-02_fix に含める |
| 5 | 軽微 | docs/dev/reports/M5-01_report.md | pytest の実行結果（件数）がそのまま貼られていない（AGENTS.md「実行結果はそのまま貼る」） | M5-02 の報告で貼らせる |
| 6 | 軽微（容認） | tests/test_summarize.py | 指示外の `matplotlib.use('Agg')` 追加。テスト実行時のエラー回避で、報告に記載あり。害なし | 対応不要 |
| 7 | 軽微 | scratch.txt（プロジェクト直下） | 指示にない作業ファイル（ポップアップの抜き出し） | Claude が _to_delete/M5-01_work/ へ移動済み |

## 判定：不合格（修正1回目へ）
