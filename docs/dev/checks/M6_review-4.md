# ソース確認 M6（4回目）　確認日：2026-10-03

- 確認範囲：1df4f7f（M6-03 作業中）からの差分（src/build_site.py、src/check_public.py、tests/test_build_site.py、tests/test_check_public.py）と生成物 docs/index.html
- ファイル：報告のバイト数とディスク上のサイズが一致。消失なし
- Claude の確認：docs/index.html の比較表5行が output/summary_36.csv と一致（標高 4.0｜38.5｜-28.0｜14% ほか）。check_public.py を実行
- M6-05 の「問題あり」3件の原因：2件は Claude が書いた M6_review-3・M6-05_fix の説明文（偽のユーザー名入りのパスの例）。下記 No.2 の誤検出も重なった。Claude が docs/dev の該当行（M6_review-3、M6-05_fix、M6-05_report の2行）を言い換え・伏せ字にし、再実行で「問題なし」を確認

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 済 | M6_review-3 No.1・2・4・5・7 | 比較表の列名、docs/data/ の除外、報告の書式・問題タブ件数、表示のテスト k、整理・出典リンク。すべて対応済み | — |
| 2 | 中 | src/check_public.py unix_pattern・win_pattern | ユーザー名の部分が空白・バッククォート（`）・引用符も含めて、同じ行の次の区切りまで続けて読む。そのため「…/home/index.html` のような説明。…（後ろに円記号）」の行で、URL を誤って検出する（M6_review-3 の説明文で実際に起きた）。テスト n は URL だけの行で試しているため見逃した | M6-06_fix |
| 3 | 中 | tests/test_check_public.py test_check_real_project | 指示（docs/dev を除外しない）に反し、結果から dev を含むパスを除いている。また推測を書き連ねた長いコメントが残っている | M6-06_fix |
| 4 | 中 | tests/test_build_site.py テスト d | 「2026-09-24」の最初の位置が、更新履歴の表ではなくページ上部の「伝承碑データ取得日：2026-09-24」になるため、表の並び順が逆でも合格する（順序を確かめていない） | M6-07_fix |
| 5 | 軽微 | reports/M6-04_report.md | M6-04 の対象外の tests/test_check_public.py を変更していた（報告には記載あり）。M6-05 で置き換わったため実害なし | — |

## 判定：不合格（修正3回目＝M6-06_fix・M6-07_fix。上限3回。これで不合格なら計画の見直しを相談）
