# 指示書 F2-03（実装・全国ページと PDF の県別注記の書き方）　作成日：2026-10-15

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・update.py・summarize_national.py・build_site.py・count_missing.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」4・5 のコマンドだけです。

## 目的（このテーマ1つ）
全国ページ（docs/index.html）と印刷用PDF（national_report.pdf）の「ご利用上の注意」で、県ごとのハザードの注記を「【県名】」で始める書き方にする（計画書 版11.8 の変更要求）。

- 今：`徳島県：津波：徳島県は2025年9月に…`（「徳島県：」と「津波：」の見出しが重なる）
- 直した後：`【徳島県】津波：徳島県は2025年9月に…`

## 対象ファイル
- 変更する：src/build_national.py、src/make_national_pdf.py、tests/test_build_national.py
- 作り直される（コマンドの実行で）：output/national_report.pdf、docs/national_report.pdf、docs/index.html
- 新しく作る：docs/dev/reports/F2-03_report.md
- 変えないもの：上記以外のすべて。**src/hazard_layers.py の注記の文（HAZARD_DATA_NOTES）は変えない**（県別ページ・県の地図では県名を付けずにそのまま使っており、そちらは今のままでよい）

## やること
1. src/build_national.py の「8. 注意事項」の部分（`for p_code in sorted(HAZARD_DATA_NOTES.keys()):` のループ）で、
   `hazard_note_lines.append(f"{pref_name}：{note}")` を
   `hazard_note_lines.append(f"【{pref_name}】{note}")` にする（この1行だけ）。
2. src/make_national_pdf.py の同じ形のループで、`if note.startswith(f"{pref_name}："):` から始まる if／else（4行）を、次の1行にする（字下げは if と同じ）。
   ```
   notices.append(f"【{pref_name}】{note}")
   ```
3. tests/test_build_national.py にテストを1件足す（既存のテストは変えない）：偽のデータで作った index.html に、`【徳島県】` と HAZARD_DATA_NOTES['36'][0] の文（html.escape したもの）が続けて入っていること、`徳島県：津波：` が入っていないこと。偽のデータの作り方は既存の test_national_report_pdf_link にならい、PREFECTURES に「36：徳島県」を入れる。
4. .venv を有効にして、次の順に実行する（PDF を先に作り、全国ページの作成でそれを docs にコピーする）。
   ```
   python src/make_national_pdf.py
   python src/build_national.py
   ```
5. 次を実行し、出力をそのまま報告書に貼る。
   ```
   python -m pytest -q
   python src/check_public.py
   git status --short
   git diff --numstat
   git ls-files --eol src/build_national.py src/make_national_pdf.py tests/test_build_national.py docs/index.html
   ```

## やらないこと
- 注記の文そのもの・ほかの注意の文・順序の変更
- 県別ページ（build_site.py）・地図（make_map.py）の変更
- 上記以外のファイルの変更・リファクタリング

## 完成の条件（既知の答え）
- pytest：**224 passed**（今の 223＋1）
- check_public.py：「公開前チェック：問題なし」
- make_national_pdf.py の表示：ページ数は「6（A4 縦）」、碑は「2,481基（47都道府県）」のまま
- `git status --short` に出るのは次の 7 行だけ：` M` src/build_national.py・src/make_national_pdf.py・tests/test_build_national.py・output/national_report.pdf・docs/national_report.pdf・docs/index.html、`?? docs/dev/reports/F2-03_report.md`
- `git diff --numstat`：src/build_national.py「1　1」、src/make_national_pdf.py「1　4」、docs/index.html「1　1」（注意の項目は1行にまとめて書かれているため）、PDF 2件は「-　-」（バイナリ）
- docs/national_report.pdf と output/national_report.pdf は同じ内容（バイト数が同じ）
- 改行コードは LF（`i/lf w/lf`）

## 完了後
- 自己チェックを行い、docs/dev/reports/F2-03_report.md に報告を書く（変更したファイルのバイト数一覧を含める。パスはユーザー名を含めず `<プロジェクト>` と書く）。
