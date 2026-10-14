# ソース確認 M9（1回目）　確認日：2026-10-05

- 確認範囲：b9fb852（第2版 計画承認）からの差分＋影響範囲（src/load_monuments.py、src/add_elevation.py、tests/ 13ファイル）。M9-01〜03 の報告ごとに確認済み
- 報告の実行結果とコードの表示文の照合：一致（M9-01 の pytest は1ファイルだけの実行だったが、本人実行で 140 passed を確認。M9-02 以降はテスト全体）
- 静的確認：pyflakes（使われていない名前を見つけるツール）で src・tests とも指摘0件。改行コード LF、CRLF なし
- 徳島の作り直し（確認シート No.4、2026-10-05）：
  - output/hazard_summary_36.csv：9a96085d74dcb2a6（第1版と一致）
  - data/processed/hazard_36.csv・hazard_points_36.csv：ハッシュは変わったが、差は最後の列「取得日」（実行日）だけで、ほかの列はすべて一致（作り直し前の控え _to_delete/M9_before_processed と比較）。monuments_36.csv（7b0ca38f…）・points_36.csv も控えと同一
  - 作り直し後、hazard_36.csv・hazard_points_36.csv は控えから戻した（ハッシュ b191e374…・99c87b0b… の第1版の状態）
  - 以後の照合は、取得日の列を含むファイルは「取得日の列を除いて比較」とする（status.md に記録）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/add_elevation.py（キャッシュへの行の追加） | cache_df.loc による行の追加と astype が、キャッシュの行数に比例して重くなる。結果には影響なし | M11 の実測で遅ければ検討 |

## 判定：合格（修正0回）。確認シート No.1〜4 すべて○、問題タブ エラー0・警告0、重大・中 0件
