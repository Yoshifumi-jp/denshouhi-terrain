# ソース確認 M11（1回目・M11-01）　確認日：2026-10-07

- 確認範囲：「M10 合格」729ae43 からの差分＋影響範囲（src/run_batch.py、src/update.py、src/add_river_coast.py、tests/test_run_batch.py、tests/test_update.py、tests/test_prefectures.py）
- ファイルのサイズ：報告のバイト数6件は実ファイルと一致。0バイト・巻き戻りなし
- 報告の実行結果とコードの表示文の照合：
  - `--check-only` の表示は run_batch.py の print 文・指示書3-2の4と一致。基数 163／111／103（計377）、河川 4／9／5県分、海岸線 4県分／なし／5県分は Claude の事前確認と一致
  - `update.py --pref 36 --dry-run` の表示は**コードと食い違う**（No.1）
  - pytest 170件＝既存160＋test_run_batch 9＋test_update 1。関数の数と一致
- 軽微3件（M10_review-3）の修正：差分で確認。動きは変わらない（no_sea のとき coast_dist_rounded は None のまま）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | 報告 2章2) | output/update_history_36.csv に「新データ＝data/raw/2026-09-24/…・完了」の行があるため、`--pref 36 --dry-run` は determine_old_csv が同じファイルを返し「古いデータと新しいデータが同じファイルです」で終わるはず。報告の「古いデータ: なし（初回）…」は今のコードでは出ない（別の引数で実行したか、作り直した出力とみられる）。なお、指示書5章の「表示が今までと変わらない」は Claude の書き方が不十分だった（期待する表示を書いていなかった） | M11-02 |
| 2 | 中 | src/run_batch.py main | `--pref all` のとき parse_pref_arg は文字列 "all" を返すため、`for p in pref_codes` が "a"・"l"・"l" を回り KeyError で止まる。指示書3-1（all は01〜47の順）を満たさない。M12 の全国実行で使う | M11-02 |
| 3 | 中 | tests/test_run_batch.py 298行 test_real_data | 確認の処理がなく、何も確かめずに合格になる（指示書4章の9が未実装） | M11-02 |
| 4 | 中 | tests/test_run_batch.py setup_mock_env、src/run_batch.py main | テストが `update.PROJECT_ROOT` を直接書き換えて元に戻さない。main(root=…) も run_batch の PROJECT_ROOT（global）を書き換えたままになる。後に実行されるテストに影響しうる（保守が難しい書き方） | M11-02 |
| 5 | 軽微 | src/run_batch.py is_completed | 完了の判定が `str.contains('完了')`。update.py と同じ `== '完了'` にそろえる | M11-02 でまとめて |
| 6 | 軽微 | 報告 3章 | 作業用ファイル output1.txt 等を削除した（AGENTS.md では削除前に理由を報告）。今回は作業用の一時ファイルで影響なし | 指摘のみ |

## 判定：不合格（修正1回目）→ M11-02_fix
