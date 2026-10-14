# 指示書 M14-05（実装・全国の更新コマンド）　作成日：2026-10-14

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る。言い換え・要約・記憶からの作り直しをしない」）。
作業前に、エディタのタブをすべて閉じてから始めてください。作業中に docs/dev/status.md・docs/dev/01_plan.md・output/ 配下・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください（下の「実行してよいコマンド」で作られる・変わるものを除く）。
GitHub への push・git commit は行わない。

## 目的（このテーマ1つ）
計画書 M14（版11.6）の「全国の更新コマンド（新しい伝承碑データで差分のある県だけ作り直す）」を作る。新しいプログラム `src/update_all.py` で、
1. data/raw/ の最新の伝承碑データと、各県の前回の完了データを県ごとに比べ、
2. 差分のある県（と、前回が完了していない県）だけを `src/run_batch.py` で作り直し、
3. 全国集計・県別ページ・印刷用PDF・全国ページ・取得不可の件数を順に作り直す。
あわせて、M14_review-4 の軽微2件（PDF の表見出し・戻り値）を直す。

## 対象ファイル
- 新しく作る：src/update_all.py、tests/test_update_all.py、docs/dev/reports/M14-05_report.md
- 変更する：src/make_national_pdf.py（軽微2件だけ）、tests/test_make_national_pdf.py（必要なら）
- 実行で変わる：output/national_report.pdf・docs/national_report.pdf（3ページの見出しだけ変わる）
- 変えないもの：上記以外のすべて（update.py・run_batch.py・build_site.py・build_national.py・summarize_national.py・count_missing.py は変えない。呼ぶだけ）

## 実行してよいコマンド
- `python src/update_all.py --dry-run`（実データ。何も書かないこと）
- `python src/make_national_pdf.py` と `python src/build_national.py`（軽微2件の確認のため）
- pytest・pyflakes・改行コードの確認
- **`python src/update_all.py`（--dry-run なし）は実行しない**（本人が確認シートで実行する）。run_batch.py・update.py・summarize_national.py・build_site.py・count_missing.py も直接は実行しない

## update_all.py の動き

### 呼び出し
- `main(args=None, runner=None, root=None, now=None)`（run_batch.py と同じ形。root はプロジェクトのフォルダ、runner は外部コマンドを動かす関数＝既定は update.default_runner と同じく `subprocess.run(cmd, cwd=root)`、now は現在時刻を返す関数）
- 引数は `--dry-run` だけ（判定と表示までで止め、**ファイルを1つも書かない**）
- ファイルの場所はすべて root からたどる（PROJECT_ROOT を直接使わない。テストで本物の output/ に書かないため）。update.py の `get_history_file`・`save_update_history`・`determine_old_csv` は PROJECT_ROOT を使うので **呼ばない**。使ってよいのは `update.compare_dataframes` と load_monuments の `get_latest_raw_csv(base_dir=...)`・`get_fetch_date`・`load_csv`・`validate_dataframe`・`filter_by_prefecture`

### 1. 県ごとの判定（47都道府県、県コード順）
最新の伝承碑データ（`get_latest_raw_csv(base_dir=root/"data"/"raw")`、root からの相対パス＝`新データのファイル` の書き方と同じ `data/raw/YYYY-MM-DD/xxx.csv`）を1回だけ読み、県ごとに `output/update_history_XX.csv` の**最後の行**を見て、次の4つに分ける。
| 区分 | 条件 |
|---|---|
| 最新で作成済み | 最後の行の 結果＝「完了」で、新データのファイル＝最新のファイル |
| 変更なし | 最後の行の 結果＝「完了」、新データのファイルが最新と違い、そのファイルが存在し、`compare_dataframes`（その県の旧・新）の差分が0件 |
| 作り直す | 上の2つ以外。理由は次のどれか：`更新の記録がありません`（履歴ファイルなし・行なし）／`前回が完了していません（<最後の行の結果>）`／`前回のデータが見つかりません`（前回の新データのファイルがない）／`追加 a・変更 b（うち位置 c）・削除 d` |
- 旧データの CSV も1つのファイルにつき1回だけ読む（47県で同じファイルのことが多い）

### 2. 全国の作り直しが必要か
`output/update_history_all.csv`（新規。列：`実行日時,新データ取得日,新データのファイル,作り直した県,変更なしの県数,結果`、utf-8-sig）の**最後の行**で決める。
- 作り直す県が1県以上 → 必要（理由「県を作り直すため」）
- 記録がない → 必要（理由「全国の作り直しの記録がないため」）
- 最後の行の 結果 が「完了」でない → 必要（理由「前回の全国の作り直しが完了していないため」）
- 最後の行の 新データのファイル が最新と違う → 必要（理由「新しい伝承碑データに切り替えたため」）
- それ以外 → 不要

### 3. 表示（この文のとおり。<> は値）
```
全国の更新：使う伝承碑データ <新データのファイル>（取得日 <日付>、<碑の数（3桁区切り）>基・47都道府県）
県ごとの判定：
  最新で作成済み：<n>県
  変更なし（作り直しません）：<n>県
  作り直す：<n>県
全国のページ：<作り直します（<理由>）／作り直しは不要です>
```
- 「変更なし」が1県以上のときは、その行の下に `    <県名>（<コード>）` を「、」でつないだ1行を出す
- 「作り直す」が1県以上のときは、その行の下に県ごとに `    <県名>（<コード>）<理由>` を1行ずつ出す
- `--dry-run` のときはここで `確認だけ行いました（--dry-run）。何も書き込んでいません` と出して終了コード0
- 作り直す県0・全国も不要のときは `すべて最新です。作り直すものはありません` と出して終了コード0（何も書かない）

### 4. 実行（--dry-run でないとき）
1. 「変更なし」の県それぞれの `output/update_history_XX.csv` に、update.py と同じ13列で1行足す（旧データ取得日・旧データのファイル・旧基数＝前回の完了行の新データの値、新データ＝最新、追加・変更・うち位置の変更・削除＝0、結果＝`完了`、実行日時＝now() を `%Y-%m-%d %H:%M`）。これで run_batch.py もこの県を「完了済み」とみなす。作り直しはしない（中身が同じため）
2. 次の段階を順に、`[<i>/<段階の数>] <段階名>` を出してから runner で実行する。コマンドは `[sys.executable, str(root/"src"/<ファイル>), ...]`
   | 段階名 | コマンド | いつ |
   |---|---|---|
   | 県の作り直し（<n>県） | run_batch.py --pref <作り直す県のコードを , でつなぐ> | 作り直す県が1県以上のとき |
   | 全国集計 | summarize_national.py | 毎回 |
   | 県別ページの作成（<県名>） | build_site.py --pref <コード> | 「県別ページを作る県」ごとに1段階（下の注） |
   | 印刷用PDF | make_national_pdf.py | 毎回 |
   | 全国ページ | build_national.py | 毎回 |
   | 取得不可の件数 | count_missing.py | 毎回 |
   - 注：県別ページを作る県＝今回の作り直す県 ∪ update_history_all.csv の最後の「完了」の行より後にある行の「作り直した県」（前回が途中で止まったときに、作り直し済みの県のページを作り残さないため。「完了」の行が1つもないときは全部の行。「なし」は県なしとして扱う）。県コード順
3. どの段階も終了コードが0でなければ、`[<i>/<段階の数>] <段階名> で失敗しました。原因を直してから、もう一度 python src/update_all.py を実行してください（作り直しが済んだ県は飛ばします）` を出し、update_history_all.csv に結果 `失敗（[<i>/<段階の数>] <段階名>）` の行を書いて終了コード1
4. Ctrl+C（KeyboardInterrupt）のときは `中断しました。もう一度 python src/update_all.py を実行すると続きから始まります` を出し、結果 `中断（[<i>/<段階の数>] <段階名>）` の行を書いて終了コード1
5. すべて終わったら結果 `完了` の行を書き、`全国の更新：完了（作り直した県 <n>県・変更なし <n>県。output/update_history_all.csv に記録しました）` を出して終了コード0
- update_history_all.csv の「作り直した県」：今回の作り直す県のうち、終わった時点で update_history_XX.csv の最後の行が「完了」かつ新データのファイル＝最新の県のコード（, でつなぐ。なければ `なし`）。失敗・中断の行でも同じ求め方で書く
- 「変更なしの県数」：今回の「変更なし」の県の数

## 軽微2件（M14_review-4）
1. make_national_pdf.py の3ページの表の見出しを全国ページ（build_national.py）と同じにする：比較の表 `指標／碑の中央値／まわりの中央値／差の中央値／碑の方が大きい割合`、ハザードの表 `ハザード／碑：区域内／まわり：区域内／碑：浸水深3m以上／まわり：浸水深3m以上`（地形分類の表は今のまま）。列の幅は文字がはみ出さないように調整してよい
2. make_national_pdf() の戻り値を固定の 6 ではなく、PdfPages の `get_pagecount()` で数えた値にする（表示の「ページ数：6（A4 縦）」もその値を使う）

## テスト（tests/test_update_all.py）
偽のプロジェクトを tmp_path に作る（data/raw/<日付>/<csv>、output/update_history_XX.csv。県は47都道府県すべてにしないと判定できないので、47県それぞれ碑1基の小さな CSV を作る）。runner は偽物にし、渡されたコマンドを記録して returncode を返す。run_batch.py を渡されたときは、その県の update_history_XX.csv に「完了・最新のファイル」の行を足す（本物の run_batch の結果をまねる）。
1. 47県すべて最新で作成済み＋update_history_all の最後が「完了・最新」→ runner は呼ばれない、終了コード0、何も書かれない
2. 新しい日付フォルダを足し、1県（例：36）だけ1基追加・残り46県は同じ → 46県に「完了」の行が足される、runner の順が run_batch（--pref 36）→ summarize_national → build_site --pref 36 → make_national_pdf → build_national → count_missing、update_history_all に「完了」・作り直した県 36・変更なしの県数 46
3. 最後の行が「失敗（…）」の県は、差分0でも「作り直す」になり、理由に「前回が完了していません」が出る
4. --dry-run：判定の表示は出るが、tmp_path のファイルが1つも増えない・変わらない（実行前後でファイル一覧と中身を比べる）
5. run_batch が returncode 1 → 以降の段階は呼ばれない、update_history_all に「失敗（[1/6] 県の作り直し（1県））」、終了コード1
6. 全国の段階（例：build_national）が失敗した後の再実行：2回目は run_batch を呼ばず、build_site --pref 36 を含む全国の段階だけが呼ばれる（「県別ページを作る県」の注の確認）
7. 実データ（root を指定せず、本物の output/update_history_XX.csv があるときだけ。ないときは skip）：`--dry-run` で「最新で作成済み：47県」「作り直す：0県」と表示され、本物のファイルが変わらない
- make_national_pdf のテスト：戻り値が6のまま通ること（必要ならテストを直す）

## 既知の答え（実データの --dry-run。2026-10-14 時点）
- 47都道府県すべて、update_history_XX.csv の最後の行が「完了」・新データのファイル `data/raw/2026-09-24/denshouhi_20260924.csv`
- update_history_all.csv はまだない
- よって表示は次のとおり：
```
全国の更新：使う伝承碑データ data/raw/2026-09-24/denshouhi_20260924.csv（取得日 2026-09-24、2,481基・47都道府県）
県ごとの判定：
  最新で作成済み：47県
  変更なし（作り直しません）：0県
  作り直す：0県
全国のページ：作り直します（全国の作り直しの記録がないため）
確認だけ行いました（--dry-run）。何も書き込んでいません
```

## やらないこと
- 公開前チェックの対象拡大・GitHub への公開（M14-06）
- 標高・ハザード・地形分類・河川海岸線のデータの更新の検出（今回は伝承碑データの差分だけ）
- 既存のプログラムの変更（make_national_pdf.py の軽微2件を除く）、新しいライブラリの追加
- 「変更なし」の県の data/processed・県別ページの作り直し（取得日の列は前回のまま。中身が同じため）

## 完成の条件
- 実データの `python src/update_all.py --dry-run` の表示が上の既知の答えと同じで、git status が実行の前後で変わらない
- テスト1〜7が合格、pytest 全件合格（今の206件＋追加分）、pyflakes 0件、LF
- PDF の3ページの見出しが全国ページと同じ。`python src/build_national.py` の表示は M14-04 と同じ7行（サイズの値を除く）で、docs/index.html は変わらない

## 報告に貼るもの（画面に出た文をそのまま。ユーザー名を含む絶対パスは `<プロジェクト>` に置き換える）
- `git status --short`（作業前と、--dry-run の直前・直後）
- `python src/update_all.py --dry-run`
- `python src/make_national_pdf.py` と `python src/build_national.py`
- `git status --short` と `git diff --stat`（最後）
- `python -m pytest -q`（最後の行）、`python -m pyflakes src/update_all.py src/make_national_pdf.py tests/test_update_all.py tests/test_make_national_pdf.py`
- 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/update_all.py','src/make_national_pdf.py','tests/test_update_all.py','tests/test_make_national_pdf.py']]"`（すべて False）
- 作成・変更したファイルのバイト数

## 完了後
- 自己チェックを行い、docs/dev/reports/M14-05_report.md に報告を書く。
