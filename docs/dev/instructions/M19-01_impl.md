# 指示書 M19-01（実装・地形分類（人工地形）だけを複数県で一括実行するコマンド）　作成日：2026-10-18

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/processed の既存ファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・run_region_batch.py・update.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」5〜8 のコマンドだけです（全国の本番実行は本人が別に行います）。

## 目的（このテーマ1つ）
計画書 版13 の M19「人工地形の段階だけを47都道府県で実行するコマンド（既存の段階は再実行しない、分けて実行できる）」として、
`src/add_landform_artificial.py` を指定した県ぶん（碑・比較地点の順）に呼び出し、結果を数えて記録する新しいプログラム `src/run_artificial_batch.py` を作る。
標高・河川・ハザード・自然地形（詳細版・地域版）など、既存の段階は一切呼ばない。作りは第3版の `src/run_region_batch.py` とほぼ同じにする（違いは下に明記）。

## 対象ファイル
- 新しく作る：src/run_artificial_batch.py、tests/test_run_artificial_batch.py、docs/dev/reports/M19-01_report.md
- 実行で新しくできる：output/artificial_batch_log.csv
- 実行で書き直される（「取得日」の列を除き中身は変わらないはず）：data/processed/landform_artificial_13.csv・landform_artificial_points_13.csv・同 36（4ファイル）
- 変えないもの：上記以外のすべて（src/ の既存ファイル、tests/ の既存ファイル、data/processed の既存ファイル、output/ の既存ファイル）

## やること
1. src/run_artificial_batch.py を作る。`src/run_region_batch.py` にならう（`main(args=None, runner=None, root=None, now=None)`、runner は既定で update.default_runner、県コードの解釈は load_monuments.parse_pref_arg、所要時間の表示は run_batch.format_duration を import して使う。`count_csv_rows` は run_region_batch から import してよい）。
   - 引数：`--pref`（必須。01〜47 のカンマ区切り、または all）、`--check-only`（入力ファイルの確認だけ。問い合わせなし）
   - 県コードが不正なときは parse_pref_arg のエラー文を出して終了コード 1
   - 入力の確認：各県で data/processed の **4ファイル** monuments_XX.csv・points_XX.csv・landform_XX.csv・landform_points_XX.csv があるか調べる（run_region_batch との違い：詳細版の2つも見る。人工地形は詳細版の結果を使うため）。足りない県があれば、足りないファイルごとに `  県名（XX）landform_XX.csv がありません` のように1行ずつ出し、最後に `先に実行してください：python src/run_batch.py --pref "XX,YY"`（足りない県を昇順・重複なし）を出して終了コード 1
   - 最初の表示（この文言）：
     ```
     人工地形の一括実行の対象: 47都道府県（碑 2,481基・比較地点 12,395点）
     データの確認: そろっています
     ```
     （県が1つのときも「1都道府県」。件数は monuments_XX.csv・points_XX.csv の行数の合計、3桁区切り）
   - `--check-only` のときは続けて `データの確認だけ行いました（--check-only）` を出して終了コード 0
   - 県ごとの処理（県コードの昇順）：
     1. `[i/N] 県名（XX）碑 n基・比較地点 m点 開始 YYYY-MM-DD HH:MM` を出す
     2. 実行前に data/cache/artificial/16 の下のファイル数を数える
     3. runner で `[sys.executable, <root>/src/add_landform_artificial.py, "--pref", XX]`、続けて同じく `"--target", "points"` を付けたものを実行する。1つ目の returncode が 0 以外なら2つ目は実行せず、その県は「失敗」
     4. 実行後に data/cache/artificial/16 のファイル数を数え直し、増えた枚数を「タイルの取得」とする（減ったときは 0）
     5. 失敗でなければ、data/processed/landform_artificial_XX.csv と landform_artificial_points_XX.csv を読み、`人工地形_状態` の4つの値（取得済／人工地形なし／範囲外／取得不可）を **碑と比較地点で別々に** 数える（run_region_batch との違い：合計しない。碑の「取得済」が M19 の確認項目「人工地形ありの碑の数」になるため）。行数が monuments_XX.csv・points_XX.csv の行数と違う、ファイルがない、または取得不可が碑・比較地点のどちらかで1件以上なら、その県は「要再実行」、そうでなければ「完了」
     6. 表示（この文言）：
        - 完了：`[i/N] 県名（XX）完了　所要時間 ○分　碑 取得済 a・人工地形なし b・範囲外 c・取得不可 d／比較地点 取得済 e・人工地形なし f・範囲外 g・取得不可 h　タイル x枚`
        - 要再実行：`[i/N] 県名（XX）要再実行（取得不可 d件・行数の不一致 あり／なし）　所要時間 ○分　タイル x枚`（d は碑と比較地点の取得不可の合計）
        - 失敗：`[i/N] 県名（XX）失敗（上の表示で原因を確かめてください）　所要時間 ○分　タイル x枚`
        （数字は3桁区切り。所要時間は run_batch.format_duration の表記）
     7. output/artificial_batch_log.csv に1行追記する（なければ見出し付きで作る）。UTF-8（BOM 付き）、**改行 LF**。列（この順）：
        `実行開始,実行終了,県コード,県名,碑_数,比較地点_数,結果,所要時間_秒,タイルの取得,碑_取得済,碑_人工地形なし,碑_範囲外,碑_取得不可,比較地点_取得済,比較地点_人工地形なし,比較地点_範囲外,比較地点_取得不可`
        （失敗・中断の県の8つの件数は空）
   - Ctrl+C（KeyboardInterrupt）のとき：その県を「中断」としてログに1行書き、`中断しました。もう一度同じコマンドを実行すると、取得済みのタイルはキャッシュから読むので短時間で続きまで進みます` を出して終了コード 1
   - 最後のまとめ（この順・この文言）：
     ```
     人工地形の一括実行のまとめ（output/artificial_batch_log.csv に記録しました）
       東京都（13）完了　碑 取得済 36・人工地形なし 16・範囲外 4・取得不可 0／比較地点 取得済 174・人工地形なし 90・範囲外 16・取得不可 0
       …（県ごとに1行。要再実行は「完了」の代わりにその語。失敗の県は `  県名（XX）失敗` だけ）
     完了 2県／要再実行 0県／失敗 0県
     合計（完了と要再実行の県）：碑 取得済 48・人工地形なし 64・範囲外 15・取得不可 0／比較地点 取得済 205・人工地形なし 346・範囲外 78・取得不可 0　タイル 0枚
     ```
     終了コードは、すべて「完了」なら 0、それ以外は 1
2. コメントは日本語。ファイルの先頭の docstring に「何をするプログラムか」「長時間の実行前に Windows のスリープを『なし』にすること」「途中で止めても、同じコマンドをもう一度実行すれば取得済みのタイルはキャッシュから読む（分けて実行するときは --pref で県を区切ってよい）」を書く。
3. tests/test_run_artificial_batch.py を作る（tmp_path に偽の data/processed を作り、偽の runner が landform_artificial_XX.csv を書き、キャッシュのファイルも作る。ネットに出ない。now は差し替える）。最低限：
   (a) 2県で完了 → まとめの文言・終了コード 0・ログ2行（列名と順番、改行が LF、BOM 付き）
   (b) runner に渡すコマンドの順番が「県1 碑 → 県1 比較地点 → 県2 碑 → 県2 比較地点」で、add_landform_artificial.py 以外を呼ばない
   (c) 碑のコマンドが returncode 1 → 比較地点は呼ばれない・「失敗」・ログの件数8列が空・終了コード 1・次の県は続ける
   (d) 比較地点だけ取得不可が1件 → 「要再実行（取得不可 1件・行数の不一致 なし）」・終了コード 1
   (e) 出力の行数が入力と違う → 「要再実行」（行数の不一致 あり）
   (f) キャッシュのファイル数の増加（data/cache/artificial/16 に3枚）が「タイル 3枚」として出る
   (g) 碑と比較地点の件数が別々に数えられ、ログの8列に正しく入る（碑と比較地点で違う件数にして確かめる）
   (h) --check-only → runner は呼ばれず、終了コード 0、件数の表示
   (i) landform_points_XX.csv がない県 → `  県名（XX）landform_points_XX.csv がありません` と `python src/run_batch.py --pref "XX"` の案内・終了コード 1・runner は呼ばれない
   (j) 不正な県コード（例 "48"）→ 終了コード 1
   (k) KeyboardInterrupt → 「中断」がログに残り、終了コード 1
4. 既存のテストは変えない。pyflakes で src/run_artificial_batch.py・tests/test_run_artificial_batch.py の指摘0件。
5. .venv を有効にして `python src/run_artificial_batch.py --pref all --check-only` を実行する。
6. `python src/run_artificial_batch.py --pref "36,13"` を実行する（PowerShell では県コードを必ず "…" で囲む。M18 のキャッシュがそろっているので問い合わせは 0 のはず。数分以内）。
7. `python -m pytest -q` を実行する（全件。件数は 287 ＋ 足したテスト関数の数になるはず）。
8. 確認のため次を実行して出力を報告に貼る：
   ```
   python -c "[print(f, open(f,'rb').read().count(b'\r')) for f in ['src/run_artificial_batch.py','tests/test_run_artificial_batch.py','output/artificial_batch_log.csv']]"
   git status --short
   ```

## 完成の条件（既知の答え）
- 5 の表示が次と一致する：
  ```
  人工地形の一括実行の対象: 47都道府県（碑 2,481基・比較地点 12,395点）
  データの確認: そろっています
  データの確認だけ行いました（--check-only）
  ```
- 6 のまとめが次と一致する（各県の [i/2] の表示・add_landform_artificial.py の表示も省略しないで貼る。各県のまとめ表示の「問い合わせ回数」は 0 のはず）：
  ```
    東京都（13）完了　碑 取得済 36・人工地形なし 16・範囲外 4・取得不可 0／比較地点 取得済 174・人工地形なし 90・範囲外 16・取得不可 0
    徳島県（36）完了　碑 取得済 12・人工地形なし 48・範囲外 11・取得不可 0／比較地点 取得済 31・人工地形なし 256・範囲外 62・取得不可 0
  完了 2県／要再実行 0県／失敗 0県
  合計（完了と要再実行の県）：碑 取得済 48・人工地形なし 64・範囲外 15・取得不可 0／比較地点 取得済 205・人工地形なし 346・範囲外 78・取得不可 0　タイル 0枚
  ```
  （M18 の結果と同じ。--pref "36,13" と書いても、処理は県コードの昇順で 13 → 36）
- 6 の実行の後も、4ファイルは「取得日」の列を除いて M18 のときと同じ。Claude が確かめる（参考：取得日の列を除いた sha256 先頭16桁 landform_artificial_13.csv 5610e8eb4b57c18b、landform_artificial_points_13.csv 41329aa04d97edc7、landform_artificial_36.csv 3d6d927e3e304a47、landform_artificial_points_36.csv bf58f8dd308faee7）
- git status で新しいファイル「??」は src/run_artificial_batch.py・tests/test_run_artificial_batch.py・docs/dev/reports/M19-01_report.md・output/artificial_batch_log.csv だけ。「M」はなし
- pytest 全件合格、pyflakes 0件、新しいファイルの \r は 0

## やらないこと
- 全国（--pref all）の本番実行（本人が別に行う）
- 県別・全国の人工地形の集計（M19-02）、count_missing.py の変更（M19-03）、update.py・update_all.py の変更（M19-04）
- run_region_batch.py・run_batch.py・update.py・add_landform_artificial.py の変更

## 完了後
- 自己チェックを行い、docs/dev/reports/M19-01_report.md に報告を書く。5・6 の表示、7 の pytest の最後の行、8 の出力は、画面に出た文をそのまま貼る。ファイル名とバイト数の一覧も書く。
- 報告に貼る絶対パスは `<プロジェクト>` に置き換える。
