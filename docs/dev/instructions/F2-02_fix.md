# 指示書 F2-02（修正・県別ページの改行コードを LF にする）　作成日：2026-10-15

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・output/・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・update.py・summarize_national.py・make_national_pdf.py・build_national.py・count_missing.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」2・3 のコマンドだけです。

## 目的（このテーマ1つ）
県別ページ docs/pref_01.html〜pref_47.html を、ほかの生成ファイル（docs/index.html など）と同じ LF で書き出すようにする。

## 不具合の内容
- 起きていること：src/build_site.py 431行の `pref_html_path.write_text(html_content, encoding='utf-8')` に newline の指定がなく、Windows では CRLF で書き出される。M14-01（4ccaa08）から pref_XX.html 47件が CRLF でコミットされている（`git ls-files --eol` で `i/crlf w/crlf`）
- 本来の動き：build_national.py の index.html と同じく LF（`newline='\n'`）
- 原因の見立て（Claude のソース確認 F2_review-1 No.3）：src/build_site.py 431行。F2-01 で見つかった（F2-01 の変更による不具合ではない）

## 対象ファイル
- 変更する：src/build_site.py（431行の1か所だけ）
- 作り直される（コマンドの実行で）：docs/pref_01.html〜docs/pref_47.html
- 新しく作る：docs/dev/reports/F2-02_report.md
- 変えないもの：上記以外のすべて（テストは今回足さない）

## やること
1. src/build_site.py 431行を次のとおりにする（ほかの write_text・処理は変えない）。
   ```
   pref_html_path.write_text(html_content, encoding='utf-8', newline='\n')
   ```
2. .venv を有効にして実行する。
   ```
   python src/build_site.py --pref all
   ```
3. 次を実行し、出力をそのまま報告書に貼る。
   ```
   python -m pytest -q
   python src/check_public.py
   git status --short
   git diff --ignore-cr-at-eol --numstat
   git ls-files --eol src/build_site.py docs/pref_01.html docs/pref_36.html docs/pref_47.html docs/index.html
   ```

## やらないこと
- HTML の中身（文・リンク・順序）の変更
- 改行コードの手作業での変換、ほかのファイルの改行コードの変更
- 上記以外のファイルの変更・リファクタリング

## 完成の条件（既知の答え）
- pytest：**223 passed**（F2-01 と同じ件数）
- check_public.py：「公開前チェック：問題なし」
- `git status --short`（F2-01 は作業中コミット済み）：` M src/build_site.py`、` M docs/pref_01.html`〜` M docs/pref_47.html`（47件）、`?? docs/dev/reports/F2-02_report.md` の計49行だけ。docs/index.html・docs/fig/・docs/data/・docs/map_XX.html・tests は出ない
- `git diff --ignore-cr-at-eol --numstat`（改行コードの違いを無視した差分）：src/build_site.py は「1　1」。docs/pref_XX.html は「0　0」か、一覧に出ないかのどちらか（中身の差がないという意味。どちらでもよい）。1以上の数が出る pref があれば止まって報告する
- `git ls-files --eol`：docs/pref_01・36・47.html が `i/crlf w/lf`（作業ツリーは LF。インデックスは前回コミットのままなので crlf と出てよい）、src/build_site.py・docs/index.html は `i/lf w/lf`

## 完了後
- 自己チェックを行い、docs/dev/reports/F2-02_report.md に報告を書く（変更したファイルのバイト数一覧を含める。pref_XX.html は CRLF→LF で各ファイルが行数分だけ小さくなる。パスはユーザー名を含めず `<プロジェクト>` と書く）。
