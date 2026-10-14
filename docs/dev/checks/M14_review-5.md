# ソース確認 M14（5回目）　確認日：2026-10-14

- 確認範囲：015ef90（M14 作業中・M14-05 指示書）からの追加分（src/update_all.py 新規、tests/test_update_all.py 新規、src/make_national_pdf.py、output・docs の national_report.pdf）
- 報告の実行結果とコードの表示文の照合：一致（update_all.py の print 文と --dry-run の7行、make_national_pdf の4行。サイズ 620,635÷1024＝606.1 KB）。--dry-run の表示は指示書の既知の答えと完全一致
- バイト数：報告の6ファイルすべて一致。docs の PDF は output と同一サイズ。pytest 213 passed（報告。206＋新しいテスト関数7＝213 と一致）、pyflakes 0件・LF（報告）。git diff --stat は make_national_pdf.py と PDF 2つだけ（docs/index.html 不変）
- make_national_pdf.py の差分は軽微2件の指示どおり（見出し2か所・get_pagecount()）

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 中 | src/update_all.py judge_prefectures と run_batch 呼び出し | 判定のずれで作り直しが永久に済まない場合がある。update_all は update_history_XX の**最後の行**が「完了」でなければ「作り直す」にするが、run_batch.py の is_completed は**最後の「完了」の行**だけを見る。最新データで一度「完了」した県が、その後の --force のやり直しなどで「失敗」「中断」で終わっていると、update_all は「作り直す（前回が完了していません）」→ run_batch は「完了済みのため飛ばします」で何もせず終了コード0 → 全国の段階は進むが、その県は直らないまま記録上は毎回「作り直す」になる（Claude が is_completed を偽の履歴（完了→失敗、どちらも最新のファイル）で実行し True を確認） | M14-06_fix：run_batch に --force を付けて呼ぶ（完了済みでも作り直す。差分のある県・未完了の県には影響しない）＋テスト追加 |
| 2 | 軽微 | src/update_all.py get_prefs_for_site_build | `df_hist.index`（ラベル）で見つけた位置を `iloc`（何番目か）に使っている。dropna で行が抜けたときにずれる | M14-06_fix で reset_index(drop=True) を入れる |

## 判定：不合格（中1件）。M14 の修正2回目＝M14-06_fix
