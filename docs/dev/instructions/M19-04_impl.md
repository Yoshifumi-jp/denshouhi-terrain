# 指示書 M19-04（実装・update.py と update_all.py に地形分類（人工地形）の集計の段階を加える）　作成日：2026-10-18

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/processed の既存ファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。**update.py・update_all.py・run_batch.py・run_artificial_batch.py・summarize_artificial.py・count_missing.py などのプログラムは実行しない**（テストからの呼び出しは可。テストでは実際のコマンドを動かさない偽の runner を使う）。
実行してよいのは `python -m pytest -q` と、下の「完成の条件」にある確認コマンドだけです。

## 目的（このテーマ1つ）
計画書 版13 の M19「update_all.py（全国の更新）に組み込む」を行う。
伝承碑データが更新されたとき、作り直した県の人工地形の県別集計（output/landform_artificial_XX.csv）と、全国の人工地形集計（output/landform_artificial_all.csv・landform_artificial_cross_all.csv）も自動で作り直されるようにする。
（人工地形の付与〔add_landform_artificial.py〕は M18 で update.py の13・14段階目に入っている。今回は「集計」の段階を足す）

## 対象ファイル
- 変更する：src/update.py、src/update_all.py、tests/test_update.py、tests/test_update_all.py
- 新しく作る：docs/dev/reports/M19-04_report.md
- 変えないもの：上記以外のすべて（output/・data/ のファイルは1つも変わらない）

## やること
1. src/update.py：steps の「地形分類（地域版）の集計」の**直後**に1行足す。ほかの段階の名前・順番・引数は変えない。
   ```python
   ("地形分類（人工地形）の集計", ["summarize_artificial.py", "--pref", pref_code]),
   ```
   → 段階は 1〜17 が今のまま、18 が「地形分類（人工地形）の集計」、19 伝承内容の分析、20 地図作成、21 公開用ページの作成（--no-site のときは20段階）
2. src/update_all.py：steps の「地形分類（地域版）の全国集計」（summarize_region.py）の**直後**に1つ足す。ほかの段階は変えない。
   ```python
   steps.append((
       "地形分類（人工地形）の全国集計",
       [sys.executable, str(root / "src" / "summarize_artificial.py")]
   ))
   ```
   → 1県を作り直すときの段階：[1/8] 県の作り直し（1県）→[2/8] 全国集計→[3/8] 地形分類（地域版）の全国集計→[4/8] 地形分類（人工地形）の全国集計→[5/8] 県別ページの作成（徳島県）→[6/8] 印刷用PDF→[7/8] 全国ページ→[8/8] 取得不可の件数
   - 人工地形のファイルが足りない県があると summarize_artificial.py は終了コード 1 で止まる。そのときは今の仕組み（「[4/8] 地形分類（人工地形）の全国集計 で失敗しました。…」と update_history_all.csv への「失敗（…）」の記録）がそのまま働くので、**新しい判定や表示は足さない**
3. コメントは日本語。update.py・update_all.py の段階の一覧を説明しているコメントや docstring があれば、新しい段階に合わせて直す（あれば。なければ足さなくてよい）
4. テストを直す（**期待値を新しい段階に合わせる直しだけ**。テストの数・確かめる中身は減らさない。段階の番号・総数・期待するコマンドの一覧のように、段階が1つ増えると必ず変わる数字や一覧は、既存のテスト関数の中でも直してよい。**直した箇所はすべて報告に「ファイル・行・前→後」で書く**）：
   - tests/test_update.py：
     - 期待するコマンドの一覧（2か所、今の267行目・364行目付近）：summarize_region.py の行の後ろに `[exe, str(tmp_path / "src" / "summarize_artificial.py"), "--pref", "36"],` を足す
     - `[11/20]` → `[11/21]`（2か所）、`[17/20]` → `[17/21]`（2か所）。ほかに段階の総数を書いている箇所があれば合わせる
   - tests/test_update_all.py：
     - 期待する runner の順（2か所、今の228行目・423行目付近の expected_scripts）：`"summarize_region.py",` の後ろに `"summarize_artificial.py",` を足す
     - `[1/7]` → `[1/8]`（344・351行目付近）、`[6/7] 全国ページ` → `[7/8] 全国ページ`（401行目付近と、それを起こしている偽の runner の設定があればそこも）、test_10 の `[3/7]` → `[3/8]`（docstring・assert とも）。test_10 の called_scripts（地域版で止まるので summarize_artificial.py は呼ばれない）は変えない
     - 259行目・314行目付近の `[1/6] 県の作り直し（1県）` は過去の記録として作った文字列なので**変えない**（第3版の test_8 の `[9/14]` と同じ扱い）
   - テストを1つずつ足す：
     (a) test_update.py：段階の18番目が「地形分類（人工地形）の集計」で、その段階で失敗すると `[18/21] 地形分類（人工地形）の集計 で失敗しました。` で始まる行が出て、update_history_36.csv の最後の行の結果が `失敗（[18/21] 地形分類（人工地形）の集計）` になる（既存の [17/21] のテストと同じ作り）
     (b) test_update_all.py：runner が summarize_artificial.py で終了コード 1 を返すと、`[4/8] 地形分類（人工地形）の全国集計 で失敗しました` が表示され、update_history_all.csv の最後の行の結果が `失敗（[4/8] 地形分類（人工地形）の全国集計）`、終了コード 1。呼ばれたのは `["run_batch.py", "summarize_national.py", "summarize_region.py", "summarize_artificial.py"]` だけ（県別ページ・印刷用PDF・全国ページ・取得不可の件数は呼ばれない）。既存の test_10 と同じ作り
5. `python -m pytest -q` を実行する。
6. 完了後、自己チェックを行い、docs/dev/reports/M19-04_report.md に報告を書く。

## やらないこと
- 新しい判定・表示の追加（人工地形のファイルの有無を update_all.py で調べる、など）
- run_batch.py・run_artificial_batch.py・summarize_artificial.py・count_missing.py・README.md の変更（README は Claude が直す）
- プログラムの実行（pytest と確認コマンド以外）、ネットへの問い合わせ

## 完成の条件（既知の答え）
- `git diff --numstat src/` が `1	0	src/update.py` と `4	0	src/update_all.py`（前後に空行を1行足した場合は 5。コメントを直した場合はその分だけ増えてよい。その場合は報告に理由を書く）
- 自動テスト：312件＋今回足したテスト関数の数（2）＝314件がすべて合格（報告に「312＋n＝合計」を書く）
- tests の差分は、上の「テストを直す」に書いた箇所と、足した2関数だけ（報告の「直した箇所」の一覧と `git diff tests/` が一致すること。Claude が照合する）
- `git status --short` に出るのは src/update.py・src/update_all.py・tests/test_update.py・tests/test_update_all.py・報告書だけ（output/・data/ は変わらない）
- 変更・新規のファイルに \r（CR）が含まれない

## 完了後
- 自己チェックを行い、docs/dev/reports/M19-04_report.md に報告を書く（変更したファイルとバイト数の一覧〔BOM を含めた実際のバイト数〕、既存テストで直した箇所の一覧、次の確認コマンドの出力、pytest の結果の最後の行をそのまま）。
  ```
  git diff --numstat
  git status --short
  python -c "fs=['src/update.py','src/update_all.py','tests/test_update.py','tests/test_update_all.py'];print(sum(open(f,'rb').read().count(b'\r') for f in fs))"
  ```
- 報告に貼る絶対パスは `<プロジェクト>` に置き換える。
