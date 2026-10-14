# ソース確認 M14（1回目）　確認日：2026-10-14

- 確認範囲：7cd2a48（M14 作業中）からの差分＋影響範囲（src/build_site.py、tests/test_build_site.py、docs/ の生成物）
- 報告の実行結果とコードの表示文の照合：一致（1県1行の書式「県名（XX）：碑 N基　docs/pref_XX.html」、まとめ4行の文言は main() の print 文と同じ。47県の碑の数は output/pref_counts_all.csv と全県一致・合計2,481）
- 生成物（Claude 確認）：docs/pref_XX.html 47、map_XX.html 47、県別グラフ371、県別CSV 376、作成ファイル数 842＝841＋.nojekyll。pref_06.html に戻るリンクと「5基以上の碑群がないため…」の文あり。docs/index.html は変化なし。ユーザー名を含む文字列なし
- バイト数：src/build_site.py 24,989・tests/test_build_site.py 23,812（報告と一致）、LF、pyflakes 0件
- pytest：195 passed・1 failed（196＝189＋追加7件。テスト関数の増分7と一致）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | tests/test_make_map.py 409行 | 実データテスト test_real_hazard_popup がハザード取得日を「2026-10-04」と固定で比べており、徳島の作り直し（7cd2a48、Claude の案内）で取得日が 2026-10-14 になったため失敗。プログラムの不具合ではなくテストの書き方の問題。Antigravity が対象外のファイルとして直さずに報告したのは正しい | M14-02_fix |
| 2 | 中 | tests/test_build_site.py（test_real_hazard_table 付近） | 同じ種類の固定日付を「2026-10-14」に書き換えて合わせている。次に作り直すとまた失敗する | M14-02_fix（No.1 と同じテーマ） |
| 3 | 軽微 | src/build_site.py main() | all のとき monuments_XX.csv を build_site() の中と main() で2回読む | 記録のみ |

## 判定：不合格（修正1回目）。M14-01 の実装内容は指示書どおりで問題なし。テスト全件合格の条件だけが未達のため M14-02_fix で直す
