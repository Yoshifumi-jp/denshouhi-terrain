# ソース確認 M14（7回目・M14-07 公開前チェックの対象拡大）　確認日：2026-10-14

- 確認範囲：47b8263（M14-07 指示書）からの差分（src/check_public.py +134行、src/build_national.py、tests/test_check_public.py +112行、tests/test_build_national.py +51行）＋影響範囲（collect_targets のフィルタ、find_private_info の PDF・PNG の分岐）
- 報告の実行結果とコードの表示文の照合：一致（`python src/check_public.py` は「公開前チェック：問題なし」、対象の数 1,991・拡張子ごとの内訳は Claude の実行と完全一致）
- 差分：指示書どおり（data/raw 直下の .csv と .agents を対象に追加、PDF は stream〜endstream を除いて調べ /Author を検出、PNG は tEXt・zTXt・iTXt を調べる、quiet=True でも問題があれば RuntimeError）
- バイト数一致（10,370・41,636・12,543・16,525・報告 14,891）、LF（4ファイルとも \r なし）、git status は M 4件＋報告の ?? 1件だけ
- テスト関数の数：HEAD 210 → 今 215（test_check_public +4、test_build_national +1）。報告の pytest 220＝215＋5 と一致（Claude の別環境には pandas・pytest がなく、pytest 自体は報告と本人の画面で確認）
- Claude の追加検査（別環境）：PNG に iTXt（非圧縮）・iTXt（圧縮）・zTXt でメールアドレスを入れて find_private_info を実行 → 非圧縮 iTXt＝1件、zTXt＝1件、**圧縮した iTXt＝0件（見逃し）**

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | src/check_public.py（PNG の iTXt の分岐） | iTXt の中身を `split(b'\x00', 3)` で分けているが、iTXt は「キーワード 00 圧縮フラグ(1バイト) 圧縮方式(1バイト) 言語タグ 00 翻訳キーワード 00 本文」の順で、圧縮フラグ・圧縮方式の1バイトも 00 になりうるため、区切りの数え方がずれる。圧縮した iTXt（フラグ 1）では本文の前に言語タグ等が残ったまま zlib 展開に失敗し、except で黙って飛ばすので、中にメールアドレスやパスがあっても見つからない。非圧縮でもフラグ・方式の取り方が実際のバイトと合っていない（たまたま全文を調べるので検出はできる）。公開前チェックに既知の見逃しがあるため合格不可。現在の実データ（PNG 746件は tEXt のみ）には影響なし | M14-08_fix |
| 2 | 軽微 | src/check_public.py | 3つのパターンを当てる同じ形のループが、テキスト・PDF・PNG の3か所に書かれている。小さな関数にまとめると読みやすい | 記録のみ（次に check_public を触るとき） |
| 3 | 軽微 | src/build_national.py（公開前チェックの後） | 問題ありのときと問題なしのときで、同じ5行の表示（全国ページ・碑・色分け・地形分類・作成数・サイズ）が2か所に書かれている。表示の文・順序は変わっておらず動きは正しい | 記録のみ |

## 判定：不合格（M14 の修正3回目へ。上限は3回）
