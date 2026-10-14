# ソース確認 M14（2回目）　確認日：2026-10-14

- 確認範囲：4ccaa08（M14-01 作業中）からの差分（tests/test_make_map.py、tests/test_build_site.py）
- 報告の実行結果とコードの照合：一致（git diff -w は2か所＋日付を求める数行だけ。実データ hazard_36.csv の取得日の最大値は 2026-10-14）
- バイト数：test_make_map.py 21,873・test_build_site.py 24,057（報告と一致）、LF、pyflakes 0件（報告）、pytest 196 passed（報告。189＋M14-01 の追加7件と一致）
- 偽のデータの固定日付（test_make_map.py 340・357・423・439行）は変えていない（指示どおり）

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 軽微 | tests/test_make_map.py 409行付近 | `import re` が関数の中にある（ファイルの先頭にまとめる方が読みやすい） | 記録のみ |

## 判定：M14_review-1 の中2件は解消。M14-01（県別ページの置き場所変更）は完了
