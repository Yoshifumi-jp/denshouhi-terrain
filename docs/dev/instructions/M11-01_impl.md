# 指示書 M11-01（実装・複数県の一括実行）　作成日：2026-10-07

最初に AGENTS.md を読んでから作業してください（特に「完了報告」「作業用のスクリプトを作らない」）。
作業前に、エディタのタブをすべて閉じてから始めてください。

## 目的（このテーマ1つ）
複数の県を順に処理する一括実行 `src/run_batch.py` を作る。夜間などに長時間（試験3県で推測10時間前後）動かすため、
始める前にデータの不足を確かめて止まる／途中で止めても再実行で続きから始まる／県ごとの所要時間と問い合わせ回数を記録する。
**この指示書では 3県の本番の実行（ネットへの問い合わせ）はしない**（本人が後で行う）。GitHub への push・git commit は行わない。

## 対象ファイル
- 新規：src/run_batch.py、tests/test_run_batch.py
- 変更：src/update.py（`--no-site` の追加のみ）、tests/test_update.py（`--no-site` のテスト追加のみ）
- 軽微な修正（7章）：src/add_river_coast.py、tests/test_prefectures.py
- 変えないもの：ほかの src/*.py、docs/ の公開ファイル（index.html など）、data/ の中、output/ の既存ファイル

## 1. 背景（なぜ公開ページを作らないか）
`build_site.py` は県に関係なく `docs/index.html` を上書きする。一括実行で岩手などを処理すると、公開中の徳島のページが置き換わってしまう。
全国ページは M14 で作るため、一括実行では最後の手順「公開用ページの作成」を行わない（地図は output/map_XX.html で確かめる）。

## 2. src/update.py（変更：`--no-site` の追加だけ）
1. 引数 `--no-site`（store_true、help：`公開用ページの作成（build_site.py）を行わない`）を追加
2. `--no-site` のときは、steps の最後の `("公開用ページの作成", ["build_site.py", ...])` を除いた14手順にする（表示は `[1/14]`〜`[14/14]`）。それ以外の動き・表示・更新履歴の書き方は変えない
3. 付けないときは今までどおり15手順（既存のテストはそのまま合格すること）

## 3. src/run_batch.py（新規）
### 3-1. 使い方
```
python src/run_batch.py --pref 03,20,28              # 一括実行
python src/run_batch.py --pref 03,20,28 --check-only # データの確認だけ（問い合わせなし）
python src/run_batch.py --pref 03,20,28 --force      # 完了済みの県もやり直す
```
- `--pref` は load_monuments.py の `parse_pref_arg` をそのまま使う（`all` は全47県を 01〜47 の順）
- 県の処理順は parse_pref_arg が返す順（昇順）

### 3-2. 始める前の確認（--check-only でも、本番でも必ず行う）
1. 最新の伝承碑CSV（`lm.get_latest_raw_csv()`）を読み、県ごとの基数を数える（ID の先頭2桁）
2. 県ごとに `add_river_coast.find_input_shapefiles(県, PROJECT_ROOT / "data" / "raw")` で河川・海岸線の有無を確かめる
3. 県ごとに「完了済み」かを判定する：`output/update_history_{県}.csv` があり、`結果` が `完了` の行のうち最後の行の `新データのファイル` が、今回の最新CSVの相対パス（update.py の `to_rel_path` と同じ書き方）と同じなら完了済み。`--force` のときは完了済みとみなさない
4. 表示（この文のとおり。基数・県数は実際の値）
   ```
   一括実行の対象: 岩手県（03）、長野県（20）、兵庫県（28）（3県・377基）
   使う伝承碑データ: data/raw/2026-09-24/denshouhi_20260924.csv（取得日 2026-09-24）
   データの確認:
     岩手県（03）163基　河川 4県分・海岸線 4県分　そろっています
     長野県（20）111基　河川 9県分・海岸線 なし（海のない県）　そろっています
     兵庫県（28）103基　河川 5県分・海岸線 5県分　そろっています
   ```
   - 完了済みの県は行末を `そろっています（完了済みのため飛ばします）` にする
   - 足りない県は行末を `足りません` にし、その下に find_input_shapefiles の「足りないもののリスト」を1件ずつ `      ` （空白6つ）を付けて出す
5. 1県でも足りなければ、最後に `データが足りない県があります。docs/dev/m11_downloads.md のとおりダウンロード・展開して data/raw/ に置き、もう一度実行してください` を出してコード1で終了する（どの県の処理も始めない）
6. `--check-only` のときは、確認の表示のあと `データの確認だけ行いました（--check-only）` を出してコード0で終了する

### 3-3. 本番の実行（県ごと）
1. 完了済みの県は飛ばす（表示 `[1/3] 岩手県（03）完了済みのため飛ばします`）
2. 開始時に `[1/3] 岩手県（03）163基 開始 2026-10-07 22:00` を出す
3. 問い合わせ回数を数えるため、開始前と終了後に次の3つを数え、差を「その県の問い合わせ回数」とする
   - 標高：`data/cache/elevation_cache.csv` のデータ行数（見出し行を除く。ファイルがなければ0）
   - ハザードタイル：`data/cache/hazard/` の下のファイル数（下の階層も含む。なければ0）
   - 地形分類タイル：`data/cache/landform/` の下のファイル数（同上）
4. `update.py --pref {県} --no-site` を、runner（update.py の `default_runner` と同じ形。テストで差し替えられるようにする）で実行する。update.py の画面表示はそのまま流す
5. 終了コード0なら「完了」、0以外なら「失敗」。失敗しても次の県へ進む（夜間に1県の失敗で全体が止まらないように）
6. 県の終了時に次を出す（所要時間は「X時間Y分」、1時間未満は「Y分」、1分未満は「1分未満」。回数は3桁区切り）
   ```
   [1/3] 岩手県（03）完了　所要時間 3時間12分　問い合わせ：標高 15,800回・ハザードタイル 4,200枚・地形分類タイル 600枚
   ```
   失敗のときは `完了` の所に `失敗（上の表示で原因を確かめてください）`
7. 記録：`output/batch_log.csv`（UTF-8 BOM付き、なければ見出し付きで作り、あれば追記）に1県1行で書く
   - 列：`実行開始, 実行終了, 県コード, 県名, 基数, 結果, 所要時間_秒, 標高の問い合わせ, ハザードタイルの取得, 地形分類タイルの取得, 新データのファイル`
   - 日時は `YYYY-MM-DD HH:MM:SS`、所要時間_秒は整数、結果は `完了`／`失敗`／`中断`。飛ばした県は書かない
8. 中断（Ctrl+C。KeyboardInterrupt）：その県を `中断` として batch_log.csv に書き（回数はそこまでの差）、
   `中断しました。もう一度同じコマンドを実行すると、完了済みの県を飛ばして続きから始まります（取得済みの分はキャッシュから読みます）` を出してコード1で終了する（次の県へは進まない）
9. 全県の後のまとめ（この文のとおり）
   ```
   一括実行のまとめ（output/batch_log.csv に記録しました）
     岩手県（03）完了　3時間12分　標高 15,800・ハザード 4,200・地形分類 600
     長野県（20）完了済みのため飛ばしました
     兵庫県（28）失敗　0分　標高 0・ハザード 0・地形分類 0
   完了 1県／失敗 1県／飛ばした 1県
   ```
   失敗が1県でもあればコード1、なければコード0で終了する

### 3-4. 書き方
- `main(args=None, runner=None, root=None, now=None)` の形にし、テストで runner（実行）・root（PROJECT_ROOT の差し替え）・now（現在時刻を返す関数）を差し替えられるようにする
- PC のスリープで止まる点は、ファイル先頭の説明コメントに「長時間の実行前に Windows のスリープを『なし』にする」と書く
- 1秒間隔などの問い合わせ間隔には触れない（各スクリプトのまま）

## 4. tests/test_run_batch.py（新規。ネットに接続しない）
tmp_path に data/raw（ダミーの伝承碑CSVと、ダミーの `W05-*_XX_GML/*_Stream.shp`・`C23-*_XX_GML/*_Coastline.shp`。中身は空ファイルでよい）と output を作り、runner は偽物にする。
1. データ不足：1県の河川を置かない → コード1、`足りません` と足りないファイルの行が出る、runner は1回も呼ばれない
2. --check-only：そろっているとき、コード0、runner は呼ばれない、3-2 の表示の形（基数・河川 n県分・海のない県の表示）
3. 順番と引数：3県とも成功 → runner が `update.py --pref XX --no-site` で昇順に3回呼ばれる。batch_log.csv が3行・結果すべて `完了`
4. 再開：1県目の update_history に今回の新データで `完了` の行がある → その県は飛ばし、runner は2回。`--force` を付けると3回
5. 失敗しても続ける：2県目の runner が終了コード1 → 3県目も実行、batch_log の2県目は `失敗`、まとめ `完了 2県／失敗 1県／飛ばした 0県`、コード1
6. 中断：2県目の runner が KeyboardInterrupt → batch_log の2県目は `中断`、3県目は呼ばれない、コード1、中断の文が出る
7. 問い合わせ回数：偽の runner が elevation_cache.csv に3行足し、hazard の下に2ファイル、landform の下に1ファイル作る → batch_log の回数が 3・2・1
8. 所要時間の表示：now を差し替えて 3時間12分・45分・30秒（`1分未満`）になること
9. 実データ（data/raw/2026-09-24 と河川・海岸線がない環境では skip）：`--pref 03,20,28 --check-only` の表示が 3-2 の4の例と一致（3県・377基、163／111／103基、河川 4／9／5県分、海岸線 4県分／なし（海のない県）／5県分）

tests/test_update.py に1件追加：`--no-site` のとき runner の呼び出しが14回で、build_site.py が含まれないこと（既存の test_k はそのまま合格すること）

## 5. 完成の条件
- `python -m pytest` 全件合格（件数は報告に書く。追加したテスト関数の数と合うこと）
- `python src/run_batch.py --pref 03,20,28 --check-only` の表示が 3-2 の4の例と一致し、コード0
- `python src/update.py --pref 36 --dry-run` の表示が今までと変わらない（差分の判定までで止まる）
- docs/ と data/ の中、output/ の既存ファイルが変わっていない（`git status` で確かめ、出力を貼る）
- 問題タブのエラー0件

## 6. やらないこと
- 3県の本番の実行（ネットへの問い合わせ）
- 各スクリプトの問い合わせ間隔・キャッシュの書き方の変更
- build_site.py の変更（全国ページは M14）

## 7. あわせて行う軽微な修正（M10_review-3 の持ち越し。動きは変えない）
1. src/add_river_coast.py の main()：使っていない変数 `pref_name` を削除
2. tests/test_prefectures.py 150・172行付近：関数内で重複して import している `LANDLOCKED`・`NEIGHBORS` のうち使っていないものを削除
3. src/add_river_coast.py：`find_input_shapefiles` の `if pref_code in LANDLOCKED: pass / else:` を `if pref_code not in LANDLOCKED:` に直す。process_river_coast の coast_shp の空リスト判定の二重化と、`海岸までの距離_m` の no_sea 条件の冗長な分岐を1つにまとめる（結果は変えない）
- 確認：`python -m pyflakes src tests` の出力を貼る（指摘0件）。徳島の river_coast_36.csv を作り直す必要はない（既存テストの合格で確かめる）

## 8. 報告に貼るもの
1. `python src/run_batch.py --pref 03,20,28 --check-only` の出力（そのまま）
2. `python src/update.py --pref 36 --dry-run` の出力
3. `python -m pytest` の最後の数行、`python -m pyflakes src tests` の出力
4. `git status --short` の出力（「??」の作業用ファイルが残っていないこと）
5. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/run_batch.py','src/update.py','src/add_river_coast.py','tests/test_run_batch.py','tests/test_update.py','tests/test_prefectures.py']]"` の出力（すべて False）
6. 変更・作成したファイルとバイト数の一覧

## 完了後
- 自己チェックを行い、docs/dev/reports/M11-01_report.md に報告を書く。
