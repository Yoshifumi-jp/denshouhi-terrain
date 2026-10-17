# 指示書 M16-04（実装・update.py と update_all.py に地形分類（地域版）の集計の段階を加える）　作成日：2026-10-16

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/processed の既存ファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。**update.py・update_all.py・run_batch.py・run_region_batch.py・summarize_region.py・count_missing.py などのプログラムは実行しない**（テストからの呼び出しは可。テストでは実際のコマンドを動かさない偽の runner を使う）。
実行してよいのは `python -m pytest -q` だけです。

## 目的（このテーマ1つ）
計画書 版12 の M16「update_all.py（全国の更新）に地域版を組み込む」を行う。
伝承碑データが更新されたとき、作り直した県の地域版の県別集計（output/landform_region_XX.csv）と、全国の地域版集計（output/landform_region_all.csv）も自動で作り直されるようにする。
（地域版の付与〔add_landform_region.py〕は M15-02 で update.py の11・12段階目に入っている。今回は「集計」の段階を足す）

## 対象ファイル
- 変更する：src/update.py、src/update_all.py、tests/test_update.py、tests/test_update_all.py
- 新しく作る：docs/dev/reports/M16-04_report.md
- 変えないもの：上記以外のすべて（output/・data/ のファイルは1つも変わらない）

## やること
1. src/update.py：steps の「ハザードの集計」の**直後**に1行足す。ほかの段階の名前・順番・引数は変えない。
   ```python
   ("地形分類（地域版）の集計", ["summarize_region.py", "--pref", pref_code]),
   ```
   → 段階は 1〜14 が今のまま、15 が「地形分類（地域版）の集計」、16 伝承内容の分析、17 地図作成、18 公開用ページの作成（--no-site のときは17段階）
2. src/update_all.py：steps の「全国集計」（summarize_national.py）の**直後**に1つ足す。ほかの段階は変えない。
   ```python
   steps.append((
       "地形分類（地域版）の全国集計",
       [sys.executable, str(root / "src" / "summarize_region.py")]
   ))
   ```
   → 1県を作り直すときの段階：[1/7] 県の作り直し（1県）→[2/7] 全国集計→[3/7] 地形分類（地域版）の全国集計→[4/7] 県別ページの作成（徳島県）→[5/7] 印刷用PDF→[6/7] 全国ページ→[7/7] 取得不可の件数
   - 地域版のファイルが足りない県があると summarize_region.py は終了コード 1 で止まる。そのときは今の仕組み（「[3/7] 地形分類（地域版）の全国集計 で失敗しました。…」と update_history_all.csv への「失敗（…）」の記録）がそのまま働くので、**新しい判定や表示は足さない**
3. コメントは日本語。update.py・update_all.py の段階の一覧を説明しているコメントや docstring があれば、新しい段階に合わせて直す（あれば。なければ足さなくてよい）
4. テストを直す（**期待値を新しい段階に合わせる直しだけ**。テストの数・確かめる中身は減らさない）：
   - tests/test_update.py：期待するコマンドの一覧（2か所。summarize_hazard.py の後ろに `[exe, str(tmp_path / "src" / "summarize_region.py"), "--pref", "36"]`）、`[11/17]` → `[11/18]`（2か所）。ほかに段階の総数を書いている箇所があれば合わせる
   - tests/test_update_all.py：期待する runner の順（2か所。summarize_national.py の後ろに summarize_region.py）、`[1/6]` → `[1/7]`、`[5/6] 全国ページ` → `[6/7] 全国ページ`。
     test_8 の `[9/14] ハザード区域の判定（碑）` は過去の記録として作った文字列なので**変えない**
   - テストを1つずつ足す：
     (a) test_update.py：段階の15番目が「地形分類（地域版）の集計」で、その段階で失敗すると `[15/18] 地形分類（地域版）の集計 で失敗しました。` で始まる行が出て、update_history_36.csv の最後の行の結果が `失敗（[15/18] 地形分類（地域版）の集計）` になる（既存の [11/17] のテストと同じ作り）
     (b) test_update_all.py：runner が summarize_region.py で終了コード 1 を返すと、`[3/7] 地形分類（地域版）の全国集計 で失敗しました` が表示され、update_history_all.csv の最後の行の結果が `失敗（[3/7] 地形分類（地域版）の全国集計）`、終了コード 1。そのあと印刷用PDF・全国ページ・取得不可の件数は呼ばれない
5. `python -m pytest -q` を実行する。
6. 完了後、自己チェックを行い、docs/dev/reports/M16-04_report.md に報告を書く。

## やらないこと
- 新しい判定・表示の追加（地域版のファイルの有無を update_all.py で調べる、など）
- run_batch.py・run_region_batch.py・summarize_region.py・count_missing.py・README.md の変更（README は Claude が直す）
- プログラムの実行（pytest 以外）、ネットへの問い合わせ

## 完成の条件（既知の答え）
- `git diff --numstat src/` が `1	0	src/update.py` と `4	0	src/update_all.py`（前後に空行を1行足した場合は 5。コメントを直した場合はその分だけ増えてよい。その場合は報告に理由を書く）
- 自動テスト：262件＋今回足したテスト関数の数（2）＝264件がすべて合格（報告に「262＋n＝合計」を書く）
- tests の差分は、上の「テストを直す」に書いた箇所と、足した2関数だけ
- `git status --short` に出るのは src/update.py・src/update_all.py・tests/test_update.py・tests/test_update_all.py・報告書だけ（output/・data/ は変わらない）
- 変更・新規のファイルに \r（CR）が含まれない

## 完了後
- 自己チェックを行い、docs/dev/reports/M16-04_report.md に報告を書く（変更したファイルとバイト数の一覧〔BOM を含めた実際のバイト数〕、`git diff --numstat` の結果、pytest の結果の最後の行をそのまま）。
