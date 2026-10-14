# 指示書 M12-01（実装・取得中の進捗表示）　作成日：2026-10-08

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、実行時の出力をそのまま貼る」）。
作業前に、エディタのタブをすべて閉じてから始めてください。
GitHub への push・git commit は行わない。実データでの本番の実行（ネットへの問い合わせ、`python src/add_hazard.py --pref 36` などの手動実行）はしない（data/processed の徳島のファイルが書き換わるため）。

## 目的（このテーマ1つ）
ハザード区域の判定（add_hazard.py）と地形分類の付与（add_landform.py）は、終わるまで何も表示しないため、長いときは15分以上止まって見える（M11 の岩手で発生）。
処理の途中で「10件ごと」と「最後の1件」に進捗の行を1行表示する。出力CSV・まとめ表示・キャッシュの扱いは一切変えない。

## 対象ファイル
- 新規：src/progress.py、tests/test_progress.py
- 変更：src/add_hazard.py、src/add_landform.py、tests/test_add_hazard.py、tests/test_add_landform.py
- 変えないもの：ほかの src/*.py・tests/*.py（add_elevation.py・add_river_coast.py は既に1件ごとに表示しているので触らない）、docs/ の公開ファイル、data/ の中、output/ の中

## やること
1. src/progress.py を作る（コメントは日本語）
   - `PROGRESS_EVERY = 10`
   - `format_elapsed(seconds)`：経過秒（小数可。切り捨てて整数秒にする）を文字列にする
     - 3600秒未満：`f"{分}分{秒:02d}秒"`／3600秒以上：`f"{時間}時間{分:02d}分"`（秒は出さない）
   - `should_print(done, total, every=PROGRESS_EVERY)`：`total > 0` かつ（`done % every == 0` または `done == total`）のとき True
   - `progress_line(label, done, total, elapsed_sec, fetch_count, cache_count)`：次の形の文字列を返す（先頭は半角スペース2つ、区切りの「　」は全角スペース）
     `  進捗 {label} {done}/{total}（{割合}%）経過 {format_elapsed(elapsed_sec)}　問い合わせ {fetch_count}枚・キャッシュ {cache_count}枚`
     - 割合は `done * 100 // total`（切り捨て）
2. src/add_hazard.py の process_monuments
   - 引数の最後に `clock=time.monotonic` を追加（既存の呼び出しはそのまま動くこと）。処理の最初に `start = clock()`
   - ループの前に入力の全行を list に読み込んで `total` を決める（今の `for row in reader` と同じ順で処理する）
   - ラベルは `"ハザード（碑）"`（target が monuments）／`"ハザード（比較地点）"`（points）。target_str を作る行は処理の最初に移してよい
   - 1件の処理（その行の results への追加）が終わるたびに、`should_print(done, total)` なら `print(progress_line(ラベル, done, total, clock() - start, stats["fetch_count"], stats["cache_count"]), flush=True)`
   - `flush=True` は必須（update.py・run_batch.py から別のプロセスとして動くとき、表示がためこまれないようにするため）
3. src/add_landform.py の process_monuments：2. と同じ。ラベルは `"地形分類"`、`clock=time.monotonic` を引数の最後に追加。枚数は stats["fetch_count"]・stats["cache_count"] を使う
4. テスト
   - tests/test_progress.py（新規）。既知の答え：
     - format_elapsed：0 → `0分00秒`、52 → `0分52秒`、59.9 → `0分59秒`、3599 → `59分59秒`、3600 → `1時間00分`、7265 → `2時間01分`
     - should_print（every=10）：(10,815)→True、(11,815)→False、(815,815)→True、(0,0)→False、(5,5)→True
     - progress_line("ハザード（比較地点）", 10, 815, 52, 48, 12) が `  進捗 ハザード（比較地点） 10/815（1%）経過 0分52秒　問い合わせ 48枚・キャッシュ 12枚` と完全一致
   - tests/test_add_hazard.py に1件追加：tmp_path に25行の入力を作り、偽の fetch・sleep と `clock=lambda: 0.0` で process_monuments を実行。capsys の出力で「  進捗 ハザード（碑） 」で始まる行がちょうど3行（10/25・20/25・25/25）で、最後の行が `25/25（100%）経過 0分00秒` を含むこと
   - test_add_hazard.py の test_real_cache に追記：出力に `進捗 ハザード（碑） 71/71（100%）` と `問い合わせ 0枚` を含み、「進捗」で始まる行（先頭空白を除く）が8行（10,20,…,70,71）であること。既存の assert は消さない
   - tests/test_add_landform.py に1件追加：上と同じ考え方で、12行の入力 → 「  進捗 地形分類 」の行が2行（10/12・12/12）

## やらないこと
- 出力CSVの列・値・順番、まとめ表示の文、キャッシュの読み書きの変更
- 残り時間の予測、時刻の表示、tqdm などのライブラリの追加（requirements.txt は変えない）
- add_elevation.py・add_river_coast.py・update.py・run_batch.py の変更

## 完成の条件
- `python -m pytest` 全件合格（171件＋新規の見込み：test_progress の関数の数＋2件。報告では、増えた件数とテスト関数の数が合うことを書く）。test_add_hazard.py の test_real_cache は本人の環境で skip されずに合格すること
- `python -m pyflakes src tests` 指摘0件
- `git status --short` で、変更が対象ファイルと docs/dev の報告だけであること（data/processed・output に変更がないこと）
- 改行コードは LF

## 報告に貼るもの（それぞれ実行したコマンドを1行目に、出力はそのまま）
1. `python -m pytest -v tests/test_progress.py tests/test_add_hazard.py tests/test_add_landform.py` の出力（PASSED／SKIPPED が分かるもの）と、`python -m pytest` の最後の数行
2. `python -m pytest -s tests/test_add_hazard.py -k real_cache` の出力のうち「進捗」の8行（画面の表示をそのまま。経過時間の値も書き換えない）
3. `python -m pyflakes src tests` の出力
4. `git status --short` の出力
5. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/progress.py','src/add_hazard.py','src/add_landform.py','tests/test_progress.py','tests/test_add_hazard.py','tests/test_add_landform.py']]"` の出力
6. 変更・作成したファイルとバイト数の一覧
- 出力に絶対パス（C:\Users\…）が出たら、その部分だけ「<プロジェクト>」に置き換える（pytest の rootdir 行も同じ）

## 完了後
- 自己チェックを行い、docs/dev/reports/M12-01_report.md に報告を書く。
