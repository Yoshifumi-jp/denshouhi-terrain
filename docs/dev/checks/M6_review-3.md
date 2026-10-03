# ソース確認 M6（3回目）　確認日：2026-10-03

- 確認範囲：2bfcda1（M6-02 作業中）からの差分＋新規ファイル（src/build_site.py、src/check_public.py、src/update.py、tests/test_build_site.py、tests/test_check_public.py、tests/test_update.py）と生成物 docs/index.html・docs/data/
- ファイル：報告のバイト数とディスク上のサイズが一致。消失なし。docs/dev/ は報告書の追加以外に変更なし
- Claude の確認：python src/check_public.py → 「問題なし」（ただし下記 No.2 のとおり docs/data/ を調べていない）。docs/index.html の比較表を本物の summary_36.csv と照合

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 重大 | src/build_site.py 比較表の作成部分 | summary_36.csv の列名と違う名前で値を取っている（コード「中央値」→本物「碑_中央値」、コード「差_中央値」→本物「差の中央値」）。**公開ページの比較表で「碑の中央値」「差の中央値」が5行とも空欄**（目的を満たさない）。テストの偽 summary が本物と違う列名で作られているため見逃した | M6-04_fix |
| 2 | 中 | src/check_public.py main の除外判定 | `'data' in p.parts` のため、トップの data/ だけでなく **docs/data/（公開する CSV）も調べていない**。テスト l も同じ判定を複製しているため見逃した（本体の関数を呼ぶべき） | M6-05_fix |
| 3 | 中 | tests/test_build_site.py | テスト d は「完了」行の有無だけで「新しい順」を確かめていない。テスト c の `'11' not in idx_text` は他の数字・日付に左右され確認として弱い | M6-04_fix |
| 4 | 中 | reports/M6-03_report.md | テンプレート（reports/_template.md）の書式でない。問題タブの件数、pytest の出力がない。「表が見られることを確認」とあるが表の空欄に気づいていない（報告の信頼性） | M6-04_fix・M6-05_fix（書式を指定） |
| 5 | 軽微 | tests/test_check_public.py | テスト k（表示でユーザー名が出ない）を確かめていない。実装は見つかった内容を表示せず種類だけ出す形で、個人情報は出ないため方針は容認。表示（標準出力）にユーザー名が含まれないことを確かめるテストを追加 | M6-05_fix |
| 6 | 軽微 | src/check_public.py | ホームのパスの判定が末尾の区切りを求めておらず、example.com の下の home フォルダのような URL も検出する。ユーザーフォルダのパスを円記号の重ねで書くと、Windows とホームの両方で二重に数える | M6-05_fix |
| 7 | 軽微 | src/build_site.py | 何もしない `if … : pass` とコメントの残り、`except:`（種類を指定しない例外の受け止め）、monuments の場所を output_dir の親から推測する書き方。出典の「地理院タイル」の語にリンクを付けていない（別の行に「地理院タイル一覧」） | M6-04_fix |

## 判定：不合格（修正2回目＝M6-04_fix・M6-05_fix。上限3回）
