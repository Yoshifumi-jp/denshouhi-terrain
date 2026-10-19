# ソース確認 M19（4回目：M19-04）　確認日：2026-10-18

- 確認範囲：6a7dfd2（M19-03 合格）からの差分＋影響範囲（src/update.py、src/update_all.py、tests/test_update.py、tests/test_update_all.py）。README の段階数の記述
- 報告の実行結果とコードの表示文の照合：一致
  - `git diff --numstat`：update.py 1行・update_all.py 4行（既知の答えどおり）。tests の差分は指示書の「テストを直す」の箇所と追加2関数だけで、報告の「直した箇所」15行と一致
  - pytest「314 passed」：表示の点の数 72×4＋26＝314、テスト関数 312＋2（test_p_fail_at_step_18・test_11_summarize_artificial_fails）と一致
  - 各ファイルのバイト数は報告と一致（0バイト・変更前への戻りなし）。CR 0。output/・data/ の変更なし
  - status.md の差分（第5版以降の検討候補4行）は Claude が指示書コミットの後に書いたもので、Antigravity の変更ではない
- 過去の記録として残す `[1/6]`（test_update_all.py 260・315行目）・`[9/14]` は指示どおり変えていない

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | tests/test_update_all.py 末尾 | ファイルの最後に空行が3行ある（PEP 8〔Python の書き方の決まり〕の W391） | 記録のみ。次にこのファイルを触る指示書でついでに直す |
| 2 | 軽微 | tests/test_update_all.py 175〜176行目 | test_2 の docstring（関数の説明文）の runner の順に summarize_region・summarize_artificial が書かれていない（第3版から。テスト本体の期待値は正しい） | 同上 |
| 3 | 軽微 | README.md 57行目 | 「update.py・update_all.py には地域版の段階も含まれています」に人工地形がない。README 全体に人工地形の説明がまだない | Claude が M20（または最終確認）で README を直す |

## 判定：合格（M19-04。修正0回）
