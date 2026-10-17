# ソース確認 M16（4回目：M16-04）　確認日：2026-10-16

- 確認範囲：6ad0908 からの差分（src/update.py、src/update_all.py、tests/test_update.py、tests/test_update_all.py、報告書）
- 報告の実行結果と実際の照合：一致（numstat・git status・バイト数・CR 0 を Claude が同じコマンドで確認）

## 確認したこと
- src/update.py：「ハザードの集計」の直後に「地形分類（地域版）の集計」（summarize_region.py --pref XX）の1行だけ。1〜14段階は不変、全18段階
- src/update_all.py：「全国集計」の直後に「地形分類（地域版）の全国集計」（summarize_region.py）の4行だけ。新しい判定・表示なし
- テストの削除行は5行で、すべて指示どおりの期待値の書き換え（[11/17]→[11/18] 2か所、[1/6]→[1/7] 2か所、[5/6]→[6/7] 全国ページ 1か所）。test_8 の [9/14] は不変
- 追加テスト2関数：test_o_fail_at_step_15（[15/18]、履歴の「失敗（[15/18] 地形分類（地域版）の集計）」）、test_10_summarize_region_fails（[3/7]、終了コード1、その後の印刷用PDF・全国ページ・取得不可の件数が呼ばれない）
- pytest：264 passed＝262＋2
- data/processed・output の更新なし

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| — | — | — | 指摘なし | — |

## 判定：合格（修正0回）
