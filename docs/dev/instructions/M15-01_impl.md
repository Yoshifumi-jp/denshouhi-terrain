# 指示書 M15-01（実装・地形分類の地域版・広域版を付ける新しいプログラム）　作成日：2026-10-16

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/processed の既存ファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・update.py・add_landform.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」6〜8 のコマンドだけです。

## 目的（このテーマ1つ）
地形分類（自然地形）の詳細版がない碑・比較地点にも地形の情報を付けるため、国土地理院の**地域版（ズーム13、中分類）**を全件に付け、地域版で取れないときだけ**広域版（ズーム8、大分類）**で補う新しいプログラム `src/add_landform_region.py` を作る（計画書 版12 の M15）。
今の詳細版（src/add_landform.py・data/processed/landform_XX.csv）は一切変えない。

## 対象ファイル
- 新しく作る：src/add_landform_region.py、tests/test_add_landform_region.py、docs/dev/reports/M15-01_report.md
- 実行で新しくできる：data/processed/landform_region_36.csv・landform_region_points_36.csv・同 03・同 35（計6ファイル）、data/cache/landform/13/・data/cache/landform/8/ の下のタイル
- 変えないもの：上記以外のすべて（src/ の既存ファイル、tests/ の既存ファイル、data/processed の既存ファイル、data/cache/landform/16/）

## データの仕様（Claude が実データで確かめ済み）
- URL：`https://cyberjapandata.gsi.go.jp/xyz/experimental_landformclassification1/{z}/{x}/{y}.geojson`（今の詳細版と同じレイヤで、ズームだけ違う）。z は 13（地域版）と 8（広域版）
- 中身：GeoJSON。地物は Polygon／MultiPolygon、属性は `code` だけ（文字列。例 `"11"`）。404 は「その範囲に地物なし」として扱う（詳細版と同じ）。gzip のときは解凍する（詳細版の default_fetch_func と同じ）
- タイル番号の計算は src/add_landform.py の lonlat_to_tile と同じ式（import して使ってよい）
- 名前の対応（凡例。これ以外の code は `不明（code=…）` とし、件数を数える）
  - 地域版（z=13）：11 山地／12 残丘状地形／13 カルスト地形／21 丘陵・小起伏地／31 火山地形（明瞭）／32 火山地形（やや不明瞭）／33 火山性丘陵／34 火山麓地形／41 台地・段丘／51 低地／61 砂丘／71 湖
  - 広域版（z=8）：1 山地・丘陵／3 火山地形／4 台地・段丘／5 低地／6 砂丘／7 湖
  - 出典：https://github.com/gsi-cyberjapan/experimental_landformclassification （style.js の凡例）。この URL を対応表のコメントに書く

## やること
1. src/add_landform_region.py を作る。作りは src/add_landform.py にならう（キャッシュ・1秒の間隔・10件ごとの進捗・まとめ表示）。違う点：
   - 引数：`--pref`（01〜47。all は不可。add_landform.py と同じ判定と文言）、`--target`（monuments／points、既定 monuments）
   - 入力：monuments_XX.csv／points_XX.csv（add_landform.py と同じ。なければ同じ案内を出して終了）
   - 出力：data/processed/landform_region_XX.csv（碑）／landform_region_points_XX.csv（比較地点）。UTF-8（BOM 付き、既存の CSV と同じ）、**改行 LF**（`newline='\n'` を明記）
   - 列：`ID,碑名,緯度,経度,地域版_地形分類名,地域版_コード,地域版_重なり数,地域版_状態,取得日`
   - 判定の順番（1地点ごと）：
     1. z=13 のタイルで、点を覆う（shapely の `covers`）地物を探す。あれば 状態「取得済（地域版）」、名前は地域版の対応、コードは最初の地物の code、重なり数は覆う地物の数
     2. z=13 で見つからない（地物なし・404・覆う地物なし）ときだけ z=8 で同じことをする。あれば「取得済（広域版）」、名前は広域版の対応
     3. どちらでも見つからなければ「データなし」（名前・コードは空、重なり数 0）
     4. z=13 または z=8 の取得で通信エラー（404 以外の HTTP エラー・タイムアウトなど）が起きたら「取得不可」（名前・コードは空、重なり数 0、取得日は空）。z=13 がエラーのときは z=8 を見ない。**エラーのタイルはキャッシュに残さない**（次の実行で取り直す）
   - 取得日：「取得不可」以外は実行日（YYYY-MM-DD）
   - キャッシュ：data/cache/landform/{z}/{x}/{y}.geojson（404 は空の FeatureCollection として保存。詳細版と同じ）。1回の実行の中では同じタイルをメモリに持ち、読み直さない
   - 問い合わせの間隔：ネットに問い合わせたときだけ、1回ごとに1秒待つ（キャッシュから読んだときは待たない）
   - fetch_func は `fetch_func(z, x, y)` の形（テストで差し替えるため）。process 関数は add_landform.py の process_monuments と同じく、入力・出力・キャッシュの置き場所・fetch_func・sleep_fn・clock を引数で受け取る
   - 進捗：`from progress import should_print, progress_line` を使い、label は `地形分類（地域版）`。問い合わせ枚数・キャッシュ枚数は z=13 と z=8 の合計
   - まとめ表示（この順・この文言。状態の4行は件数0でも必ず出す）：
     ```
     対象件数: 71
       取得済（地域版）: 69件
       取得済（広域版）: 0件
       データなし: 2件
       取得不可: 0件
     問い合わせ回数: 33
     キャッシュから読んだ回数: 0
     表にないcodeの件数: 0
     地形分類名ごとの件数:
       低地: 44件
       山地: 24件
       台地・段丘: 1件
     ```
     「地形分類名ごとの件数」は件数の多い順、同数は名前順（Python の文字列の並び）。「問い合わせ回数」はネットに問い合わせたタイルの数、「キャッシュから読んだ回数」はディスクのキャッシュから読んだタイルの数（どちらも z=13 と z=8 の合計。同じ実行の中でメモリから使い回した分は数えない）
2. コメントは日本語で書く。ファイルの先頭に「何をするプログラムか」「出典」を書く。
3. tests/test_add_landform_region.py を作る（偽の fetch_func・tmp_path を使い、ネットに出ない）。最低限：
   (a) タイル番号：経度 134.584699・緯度 34.066366 の z=13 → (7158, 3270)、z=8 → (223, 102)
   (b) z=13 で覆う地物あり → 取得済（地域版）・名前・コード・重なり数
   (c) z=13 は地物あるが覆わない、z=8 で覆う → 取得済（広域版）・広域版の名前
   (d) z=13・z=8 とも 404 → データなし（キャッシュには空の FeatureCollection が残る）
   (e) z=13 が通信エラー → 取得不可・取得日は空・z=8 は呼ばれない・z=13 のキャッシュファイルはできない
   (f) z=13 は覆わない、z=8 が通信エラー → 取得不可
   (g) 点がポリゴンの辺の上 → 覆う（取得済）
   (h) 表にない code → 名前 `不明（code=99）`、表にないcodeの件数 1
   (i) 2つの地物が覆う → 重なり数 2、コードは最初の地物
   (j) 同じタイルの2地点 → 問い合わせは1回
   (k) 2回目の実行（同じキャッシュ）→ 問い合わせ 0、結果は1回目と同じ（中断後の再開の代わり）
   (l) 出力の列名と順番、改行が LF（ファイルに \r がない）
   (m) まとめ表示の文言（capsys で、状態の4行が件数0でも出ること）
   (n) 実データの照合（キャッシュだけを読む。キャッシュがなければ pytest.skip）：下の「実データでの照合テスト」の8件
4. 既存のテストは変えない。
5. 自己チェック：pyflakes で src/add_landform_region.py・tests/test_add_landform_region.py の指摘0件。
6. .venv を有効にして、次の6つをこの順に実行する（ネットへの問い合わせは合計約230枚、推測で10分前後）。
   ```
   python src/add_landform_region.py --pref 36
   python src/add_landform_region.py --pref 36 --target points
   python src/add_landform_region.py --pref 03
   python src/add_landform_region.py --pref 03 --target points
   python src/add_landform_region.py --pref 35
   python src/add_landform_region.py --pref 35 --target points
   ```
7. もう一度 `python src/add_landform_region.py --pref 36` を実行し、問い合わせ回数が 0 であることを確かめる。
8. `python -m pytest -q` を実行する（全件。件数は 224 ＋ 足したテスト関数の数になるはず）。
9. 改行コードの確認：次を実行して出力を報告に貼る。
   ```
   python -c "import glob;[print(f, open(f,'rb').read().count(b'\r')) for f in ['src/add_landform_region.py','tests/test_add_landform_region.py']+sorted(glob.glob('data/processed/landform_region_*.csv'))]"
   git status --short
   ```

## 完成の条件（既知の答え）
- 6 の実行のまとめ表示が次と一致する（取得済（広域版）・取得不可・表にないcode は6回とも 0）

| 実行 | 対象件数 | 取得済（地域版） | データなし | 問い合わせ | キャッシュ | 地形分類名ごとの件数 |
|---|---|---|---|---|---|---|
| 36 碑 | 71 | 69 | 2 | 33 | 0 | 低地44・山地24・台地・段丘1 |
| 36 地点 | 349 | 343 | 6 | 33 | 33 | 山地221・低地112・丘陵・小起伏地8・台地・段丘2 |
| 03 碑 | 163 | 163 | 0 | 64 | 0 | 低地62・山地46・丘陵・小起伏地42・台地・段丘13 |
| 03 地点 | 815 | 798 | 17 | 53 | 64 | 山地360・丘陵・小起伏地243・低地115・台地・段丘80 |
| 35 碑 | 31 | 31 | 0 | 22 | 0 | 低地16・山地9・丘陵・小起伏地3・台地・段丘2・火山地形（やや不明瞭）1 |
| 35 地点 | 155 | 151 | 4 | 25 | 20 | 山地91・低地35・丘陵・小起伏地16・残丘状地形5・台地・段丘3・火山地形（やや不明瞭）1 |

  （問い合わせ・キャッシュの数は、この順に実行し、実行前に data/cache/landform/13・8 が空であることが前提。違ったら、報告に実行前のキャッシュの状態を書く）
- 7 の再実行で 問い合わせ回数 0・キャッシュから読んだ回数 33
- 実データでの照合テスト（n）の8件：

| ID | 碑名など | 地域版_地形分類名 | 地域版_状態 | 備考 |
|---|---|---|---|---|
| 36207-001 | 災害復旧記念碑 | 山地 | 取得済（地域版） | 詳細版はデータなし |
| 36204-003 | 福井住吉神社海嘯潮痕標石 | 山地 | 取得済（地域版） | 詳細版は氾濫平野・海岸平野（地域版が粗い例） |
| 36383-002 | 出羽島観栄寺石碑(旧碑) | （空） | データなし | 島。詳細版は山地斜面等 |
| 03202-007 | 海嘯横死者之碑 | 丘陵・小起伏地 | 取得済（地域版） | 詳細版はデータなし |
| 03207-002 | 昭和八年津浪記念碑 | 台地・段丘 | 取得済（地域版） | 詳細版はデータなし |
| 35204-004 | 鎭魂石 | 火山地形（やや不明瞭） | 取得済（地域版） | 詳細版はデータなし |
| 35202-001 | 厚南大風水害受難追悼之碑 | 低地 | 取得済（地域版） | 詳細版はデータなし |
| 03202-003-P4 | 比較地点 | （空） | データなし | 海際の比較地点 |

- 既存の data/processed の CSV（landform_XX・landform_points_XX など）・src・tests の既存ファイルが変わっていない（git status で新しいファイル「??」だけ）
- pytest 全件合格、pyflakes 0件、新しいファイルの \r は 0

## やらないこと
- add_landform.py・update.py・run_batch.py・集計・地図・ページへの組み込み（M15-02 以降）
- 3県以外の実行
- 詳細版と地域版を1つの列にまとめること

## 完了後
- 自己チェックを行い、docs/dev/reports/M15-01_report.md に報告を書く。6・7 のまとめ表示（6回＋1回）、8 の pytest の最後の行、9 の出力は、画面に出た文をそのまま貼る。ファイル名とバイト数の一覧も書く。
- 報告に貼る絶対パスは `<プロジェクト>` に置き換える。
