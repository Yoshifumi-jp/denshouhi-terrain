# ソース確認 M12（4回目・M12-05_fix）　確認日：2026-10-13

- 確認範囲：作業中コミット 52fa8bf からの差分（src/run_batch.py・tests/test_run_batch.py）と影響範囲（update.py の --old の扱い）
- 報告の実行結果とコードの表示文の照合：一致。`--pref "11,37" --check-only --force` と `--check-only` の出力を Claude が別環境で実行し、報告と1字も違わないことを確認（終了コード0、書き込みなし）
- バイト数：報告どおり（run_batch.py 11,665・test_run_batch.py 15,461）。改行コード LF。追加行に空白だけの行なし。git status の「??」は報告書だけ
- pytest：報告 178 passed。テスト関数 173（＋parametrize 分）で、前回 177 から新しいテスト1件分の増加と一致。Claude の別環境で -k force の2件 passed。pyflakes 指摘0件
- 動きの確認：is_completed を常に判定 → 飛ばす条件は `is_done and not force` のまま（--force なしの動きは不変）。--force かつ完了済みのときだけ cmd の最後に "--old=" を加える。update.py は parsed.old が空文字のとき determine_old_csv を呼ばず old_file も空になるため、同じファイルの判定（276〜280行）に入らず全件を処理し直す（本人が 2026-10-13 に手動で同じ指定をして完了したのと同じ動き）
- status.md：報告の「残った課題」のとおり、Antigravity は status.md を触っていない（52fa8bf の追記1行が残っている）。38-1 の対策が効いた

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | tests/test_run_batch.py 新テスト | コメント `# 03 is completed` が英語（既存テストからの複写。AGENTS.md は日本語コメント） | 次の指示書でまとめて |
| 2 | 軽微 | （運用） | --force でやり直した県の update_history は「旧データ なし・追加＝全件」と記録される。仕様どおりだが、履歴だけ見ると初回実行と区別しにくい | 記録のみ（必要なら変更要求で相談） |

## 判定：合格（M12-05 の指摘解消。M12 の修正3回目）
