# 指示書 M16-01（実装・地形分類（地域版）だけを複数県で一括実行するコマンド）　作成日：2026-10-16

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/processed の既存ファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・update.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」5〜8 のコマンドだけです（全国の本番実行は本人が別に行います）。

## 目的（このテーマ1つ）
計画書 版12 の M16「地域版の段階だけを47都道府県で実行するコマンド（既存の段階は再実行しない）」として、
`src/add_landform_region.py` を指定した県ぶん（碑・比較地点の順）に呼び出し、結果を数えて記録する新しいプログラム `src/run_region_batch.py` を作る。
標高・河川・ハザード・詳細版の地形分類など、既存の段階は一切呼ばない。

## 対象ファイル
- 新しく作る：src/run_region_batch.py、tests/test_run_region_batch.py、docs/dev/reports/M16-01_report.md
- 実行で新しくできる：output/region_batch_log.csv
- 実行で書き直される（中身は変わらないはず）：data/processed/landform_region_36.csv・landform_region_points_36.csv・同 35（4ファイル）
- 変えないもの：上記以外のすべて（src/ の既存ファイル、tests/ の既存ファイル、data/processed の既存ファイル）

## やること
1. src/run_region_batch.py を作る。作りは src/run_batch.py にならう（`main(args=None, runner=None, root=None, now=None)`、runner は既定で update.default_runner、県コードの解釈は load_monuments.parse_pref_arg、所要時間の表示は run_batch.format_duration を import して使う）。
   - 引数：`--pref`（必須。01〜47 のカンマ区切り、または all）、`--check-only`（入力ファイルの確認だけ。問い合わせなし）
   - 県コードが不正なときは parse_pref_arg のエラー文を出して終了コード 1
   - 入力の確認：各県で data/processed/monuments_XX.csv と points_XX.csv があるか調べる。足りない県があれば、足りない県ごとに `  県名（XX）monuments_XX.csv がありません` のように1行ずつ（両方なければ2行）出し、最後に `先に実行してください：python src/run_batch.py --pref "XX,YY"` を出して終了コード 1
   - 最初の表示（この文言）：
     ```
     地域版の一括実行の対象: 47都道府県（碑 2,481基・比較地点 12,395点）
     データの確認: そろっています
     ```
     （県が1つのときも「1都道府県」。件数は monuments_XX.csv・points_XX.csv の行数の合計、3桁区切り）
   - `--check-only` のときは続けて `データの確認だけ行いました（--check-only）` を出して終了コード 0
   - 県ごとの処理（県コードの昇順）：
     1. `[i/N] 県名（XX）碑 n基・比較地点 m点 開始 YYYY-MM-DD HH:MM` を出す
     2. 実行前に data/cache/landform/13 と data/cache/landform/8 の下のファイル数を数える
     3. runner で `[sys.executable, <root>/src/add_landform_region.py, "--pref", XX]`、続けて同じく `"--target", "points"` を付けたものを実行する。1つ目の returncode が 0 以外なら2つ目は実行せず、その県は「失敗」
     4. 実行後に 13・8 のファイル数を数え直し、増えた枚数を「地域版タイルの取得」「広域版タイルの取得」とする（減ったときは 0）
     5. 失敗でなければ、data/processed/landform_region_XX.csv と landform_region_points_XX.csv を読み、`地域版_状態` の4つの値（取得済（地域版）／取得済（広域版）／データなし／取得不可）を碑と比較地点の合計で数える。行数が monuments_XX.csv・points_XX.csv の行数と違う、ファイルがない、または取得不可が1件以上なら、その県は「要再実行」、そうでなければ「完了」
     6. 表示（この文言）：
        - 完了：`[i/N] 県名（XX）完了　所要時間 ○分　地域版 a・広域版 b・データなし c・取得不可 d（碑＋比較地点）　タイル：地域版 x枚・広域版 y枚`
        - 要再実行：`[i/N] 県名（XX）要再実行（取得不可 d件・行数の不一致 あり／なし）　所要時間 ○分　タイル：地域版 x枚・広域版 y枚`
        - 失敗：`[i/N] 県名（XX）失敗（上の表示で原因を確かめてください）　所要時間 ○分　タイル：地域版 x枚・広域版 y枚`
        （a〜d・x・y は3桁区切り。所要時間は run_batch.format_duration の表記）
     7. output/region_batch_log.csv に1行追記する（なければ見出し付きで作る）。UTF-8（BOM 付き）、**改行 LF**。列：`実行開始,実行終了,県コード,県名,碑_数,比較地点_数,結果,所要時間_秒,地域版タイルの取得,広域版タイルの取得,取得済_地域版,取得済_広域版,データなし,取得不可`（失敗の県の4つの件数は空）
   - Ctrl+C（KeyboardInterrupt）のとき：その県を「中断」としてログに1行書き、`中断しました。もう一度同じコマンドを実行すると、取得済みのタイルはキャッシュから読むので短時間で続きまで進みます` を出して終了コード 1
   - 最後のまとめ（この順・この文言）：
     ```
     地域版の一括実行のまとめ（output/region_batch_log.csv に記録しました）
       徳島県（36）完了　地域版 412・広域版 0・データなし 8・取得不可 0
       …（県ごとに1行。要再実行・失敗は「完了」の代わりにその語、失敗の県は件数を出さない）
     完了 2県／要再実行 0県／失敗 0県
     合計（完了と要再実行の県）：地域版 594・広域版 0・データなし 12・取得不可 0　タイル：地域版 0枚・広域版 0枚
     ```
     終了コードは、すべて「完了」なら 0、それ以外は 1
2. コメントは日本語。ファイルの先頭に「何をするプログラムか」と「長時間の実行前に Windows のスリープを『なし』にすること」を書く。
3. tests/test_run_region_batch.py を作る（tmp_path に偽の data/processed を作り、偽の runner が landform_region_XX.csv を書き、キャッシュのファイルも作る。ネットに出ない。now は差し替える）。最低限：
   (a) 2県で完了 → まとめの文言・終了コード 0・ログ2行（列名と順番、改行が LF）
   (b) runner に渡すコマンドの順番が「県1 碑 → 県1 比較地点 → 県2 碑 → 県2 比較地点」で、add_landform_region.py 以外を呼ばない
   (c) 碑のコマンドが returncode 1 → 比較地点は呼ばれない・「失敗」・終了コード 1・次の県は続ける
   (d) 取得不可が1件 → 「要再実行」・終了コード 1
   (e) 出力の行数が入力と違う → 「要再実行」（行数の不一致 あり）
   (f) キャッシュのファイル数の増加（13 に3枚・8 に1枚）がタイルの枚数として出る
   (g) --check-only → runner は呼ばれず、終了コード 0、件数の表示
   (h) points_XX.csv がない県 → 足りない旨と `python src/run_batch.py --pref "XX"` の案内・終了コード 1・runner は呼ばれない
   (i) 不正な県コード（例 "48"）→ 終了コード 1
   (j) KeyboardInterrupt → 「中断」がログに残り、終了コード 1
4. 既存のテストは変えない。pyflakes で src/run_region_batch.py・tests/test_run_region_batch.py の指摘0件。
5. .venv を有効にして `python src/run_region_batch.py --pref all --check-only` を実行する。
6. `python src/run_region_batch.py --pref "36,35"` を実行する（PowerShell では県コードを必ず "…" で囲む。キャッシュがそろっているので問い合わせは 0 のはず。1分前後）。
7. `python -m pytest -q` を実行する（全件。件数は 239 ＋ 足したテスト関数の数になるはず）。
8. 確認のため次を実行して出力を報告に貼る：
   ```
   python -c "import glob;[print(f, open(f,'rb').read().count(b'\r')) for f in ['src/run_region_batch.py','tests/test_run_region_batch.py','output/region_batch_log.csv']]"
   git status --short
   ```

## 完成の条件（既知の答え）
- 5 の表示が次と一致する：
  ```
  地域版の一括実行の対象: 47都道府県（碑 2,481基・比較地点 12,395点）
  データの確認: そろっています
  データの確認だけ行いました（--check-only）
  ```
- 6 のまとめが次と一致する（各県の行の前の [i/2] の表示・add_landform_region.py の表示は省略しないで貼る）：
  ```
    山口県（35）完了　地域版 182・広域版 0・データなし 4・取得不可 0
    徳島県（36）完了　地域版 412・広域版 0・データなし 8・取得不可 0
  完了 2県／要再実行 0県／失敗 0県
  合計（完了と要再実行の県）：地域版 594・広域版 0・データなし 12・取得不可 0　タイル：地域版 0枚・広域版 0枚
  ```
  （内訳：山口 碑31＝地域版31、比較地点155＝地域版151・データなし4／徳島 碑71＝地域版69・データなし2、比較地点349＝地域版343・データなし6。M15 の結果と同じ）
- 6 の実行の後も、landform_region_35・36 の4ファイルは「取得日」の列を除いて M15 のときと同じ（今日 2026-10-16 に実行すれば、sha256 先頭16桁がそのまま一致：landform_region_35.csv e81a703913c1577d、landform_region_36.csv 2944953791000844、landform_region_points_35.csv b6412c46aa80155f、landform_region_points_36.csv 36551d2a61e45bfc）。git status で「M」が付かないこと
- git status で新しいファイル「??」は src/run_region_batch.py・tests/test_run_region_batch.py・docs/dev/reports/M16-01_report.md・output/region_batch_log.csv だけ（output/ が .gitignore の対象なら出なくてよい）
- pytest 全件合格、pyflakes 0件、新しいファイルの \r は 0

## やらないこと
- 全国（--pref all）の本番実行（本人が別に行う）
- 県別・全国の地域版の集計、count_missing.py・update_all.py の変更（M16-02）
- run_batch.py・update.py・add_landform_region.py の変更

## 完了後
- 自己チェックを行い、docs/dev/reports/M16-01_report.md に報告を書く。5・6 の表示、7 の pytest の最後の行、8 の出力は、画面に出た文をそのまま貼る。ファイル名とバイト数の一覧も書く。
- 報告に貼る絶対パスは `<プロジェクト>` に置き換える。
