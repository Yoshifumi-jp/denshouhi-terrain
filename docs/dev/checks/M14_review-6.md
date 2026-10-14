# ソース確認 M14（6回目・M14-06 修正）　確認日：2026-10-14

- 確認範囲：f20a617（M14-05 作業中）からの差分（src/update_all.py 2行、tests/test_update_all.py +122行）＋影響範囲（update_all.main の段階の組み立て、get_prefs_for_site_build）
- 報告の実行結果とコードの表示文の照合：一致（--dry-run の7行は M14-05 で照合済みの print 文から変化なし。表示の文は差分で変わっていない）
- 差分：指示書どおり。「県の作り直し」に --force、get_prefs_for_site_build に reset_index(drop=True)。run_batch.py・update.py は不変
- テストの効き目（Claude の別環境、pandas 2.3.3）：修正前の src/update_all.py に新しいテストを当てると test_2・test_6・test_8・test_9 の4件が失敗、修正後は test_update_all の8件合格（test_7 は実データがないため skip）。test_9 は reset_index がないと空の一覧を返して失敗する（index のずれを正しく捕まえている）
- pytest 215＝213＋2（報告）、pyflakes 0（Claude も0）、LF、バイト数一致（17,669・23,317・4,052）、git status は M 2件＋報告の ?? 1件だけ

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | tests/test_update_all.py（test_2・test_6×2・test_8） | 呼び出しを「run_batch.py --pref 36 --force」の文字列にする処理が4か所に同じ形で書かれている。小さな関数にまとめると読みやすい | 記録のみ（次に test_update_all を触るとき） |

## 判定：合格（M14_review-5 の中1件・軽微1件は解消。M14 の修正2回目）
