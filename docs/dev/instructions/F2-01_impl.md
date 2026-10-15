# 指示書 F2-01（実装・印刷用PDFへのリンクを見つけやすくする）　作成日：2026-10-15

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・output/・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・update.py・summarize_national.py・make_national_pdf.py・count_missing.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」4 の2つのコマンドと pytest・check_public.py だけです。

## 目的（このテーマ1つ）
印刷用PDF（docs/national_report.pdf）へのリンクを、全国ページの上部と、47都道府県の県別ページにも置く（計画書 版11.7 の変更要求）。
今はリンクが全国ページの下の「データのダウンロード」にしかなく、スマホで見つけにくい。

## 対象ファイル
- 変更する：src/build_national.py、src/build_site.py、tests/test_build_national.py、tests/test_build_site.py
- 作り直される（コマンドの実行で）：docs/index.html、docs/pref_01.html〜docs/pref_47.html
- 新しく作る：docs/dev/reports/F2-01_report.md
- 変えないもの：上記以外のすべて（ページ下部の「データのダウンロード」にある既存の PDF リンクも残す）

## やること
1. src/build_national.py：全国ページの HTML の、説明文の段落（「国土地理院の自然災害伝承碑に、碑ごとの地形…災害の予測・安全の保証ではありません。」）の直後、`<h2>都道府県の色分け地図</h2>` の前の空行の前に、次の1行を足す（字下げは前後の行と同じ4文字）。
   ```
   <p><a href="national_report.pdf">印刷用PDF（A4・6ページ）を開く</a></p>
   ```
2. src/build_site.py：県別ページの HTML の `<p><a href="index.html">← 全国のページへ</a></p>` の直後（`<h1>` の前）に、次の1行を足す（字下げは前後の行と同じ4文字）。既存の「← 全国のページへ」の行は変えない。
   ```
   <p><a href="national_report.pdf">全国の印刷用PDF（A4・6ページ）</a></p>
   ```
   県別ページと PDF は同じ docs/ にあるので、リンク先は `national_report.pdf` のままでよい。
3. テストを2件足す（既存のテストは変えない）。
   - tests/test_build_national.py：偽のデータで作った index.html に `href="national_report.pdf"` が**2回**出ること、1回目が最初の `<h2>` より前にあること
   - tests/test_build_site.py：偽のデータで作った pref_36.html に `<p><a href="national_report.pdf">全国の印刷用PDF（A4・6ページ）</a></p>` があり、その位置が「← 全国のページへ」の行より後、`<h1>` より前であること
4. .venv を有効にして、次の順に実行する（県コードの all は引用符なしでよい）。
   ```
   python src/build_site.py --pref all
   python src/build_national.py
   ```
5. 次を実行し、出力をそのまま報告書に貼る。
   ```
   python -m pytest -q
   python src/check_public.py
   git status --short
   git diff --numstat
   git ls-files --eol src/build_national.py src/build_site.py tests/test_build_national.py tests/test_build_site.py docs/index.html docs/pref_36.html
   ```

## やらないこと
- 既存の文・リンク・表示の順序の変更、ページ数「6ページ」を数えて出す変更（M14_review-4 No.2 の件は今回扱わない）
- CSS・見た目の変更、ボタン化
- 上記以外のファイルの変更・リファクタリング

## 完成の条件（既知の答え）
- pytest：**223 passed**（今の 221＋2）
- check_public.py：「問題なし」
- `git status --short` に出るのは次の 52 ファイルだけ（すべて ` M`。`??` はレポート1件のみ）：src/build_national.py、src/build_site.py、tests/test_build_national.py、tests/test_build_site.py、docs/index.html、docs/pref_01.html〜docs/pref_47.html、`?? docs/dev/reports/F2-01_report.md`
  - docs/fig/・docs/data/・docs/map_XX.html・docs/national_report.pdf は中身が同じなので変更として出ない。出たら止まって報告する
- `git diff --numstat` で、src/build_national.py・src/build_site.py・docs/index.html・docs/pref_XX.html（47件）はすべて「1　0」（1行追加・削除0）
- 改行コードは LF（`i/lf w/lf`）。CRLF になっていたら報告で止まる

## 完了後
- 自己チェックを行い、docs/dev/reports/F2-01_report.md に報告を書く（変更したファイルのバイト数一覧を含める。パスはユーザー名を含めず `<プロジェクト>` と書く）。
