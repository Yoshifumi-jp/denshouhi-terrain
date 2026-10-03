# 指示書 M4-01（実装・比較地点の作成と地形情報の付与）　作成日：2026-10-02

最初に AGENTS.md を読んでから作業してください。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
碑と比べるための「比較地点」（碑のない、碑の周辺の場所）を作り、碑と同じ地形情報（標高・傾斜・河川・海岸・地形分類）を付けて保存する。
集計・グラフ・移転碑の印は次の指示書（M4-02）で行うので、今回は行わない。

## 比較地点の選び方（計画書 版6・2026-10-02 本人決定）
- 各碑について、碑から **100m以上 2,000m以内** の範囲に、**5点ずつ** 無作為に選ぶ（徳島71基 → 最大355点）
- 範囲内で面積あたり均等になるように選ぶ。距離 r は `r = sqrt(U × (2000² − 100²) + 100²)`（U は 0〜1 の一様乱数）、方角は 0〜360度の一様乱数
- メートル → 緯度・経度の換算は、src/add_elevation.py の `calc_delta_degrees` と同じ考え方（地球半径 6,371,000m）でよい
- **海上の点は除く**：候補点の標高を src/add_elevation.py の `get_elevation_with_cache`（キャッシュ共用）で調べ、標高が `"-----"`（データなし＝海上など）の候補は捨てて次の候補を引く
- 1基あたりの候補は **最大50回** まで。50回で5点に届かない碑は、取れた点数のまま次の碑へ進み、まとめ表示にその碑のIDと点数を出す（無限ループにしない）
- 乱数は **固定する**（既定のシード値 `20261002`。`--seed` で変更可）。碑ごとに `random.Random(f"{シード値}-{碑ID}")` のように碑IDを混ぜた乱数を作り、碑の並び順や他の碑の結果で点が変わらないようにする
- 標高が 0m 以下の陸地（干拓地など）は除かない

## 対象ファイル
- 新規：src/make_comparison_points.py、tests/test_make_comparison_points.py
- 変更：src/add_elevation.py、src/add_river_coast.py、src/add_landform.py（`--target` の追加のみ）
- 変更：tests/test_add_landform.py（持ち越しの軽微1件のみ）
- 必要なら既存テストに `--target` のテストを追加してよい（既存テストの期待値は変えない）

## やること（手順）
1. **src/make_comparison_points.py** を新しく作る。起動は `python src/make_comparison_points.py --pref 36`（`--seed` は省略可）。県コードの確認・エラー文は add_river_coast.py の main と同じ書き方にする
   - 入力：data/processed/monuments_{県コード}.csv
   - 出力：data/processed/points_{県コード}.csv（utf-8-sig）。列は次のとおり
     - `ID`：`{碑ID}-P{1〜5}`（例 36383-001-P1）
     - `碑名`：「比較地点」（後続の処理が 碑名 列を使うため）
     - `元の碑ID`、`碑からの距離_m`（整数に丸める）、`方角_度`（整数に丸める）
     - `緯度`、`経度`（小数6桁）
     - `県コード`、`災害種別`、`種別_洪水`〜`種別_その他`の7列（元の碑の値をそのまま写す。M4-02 の集計で使う）
     - `シード値`
   - 標高の問い合わせ関数・待ち関数は引数で差し替えられるようにする（テストで偽物を渡すため。add_elevation.py の fetch_func・sleep_fn と同じ考え方）
   - 通信エラーの候補は「海上」と区別して数え、点として採用しない
   - まとめ表示：対象の県名／碑の数／作った比較地点の数／海上などで捨てた候補の数／通信エラーの数／5点に届かなかった碑（IDと点数）／今回サーバーに問い合わせた回数／キャッシュから読んだ回数／保存先
   - Ctrl+C で止めた場合は「中断しました。もう一度実行すると続きから再開します。」と出して終わる（標高はキャッシュされるため、再実行で同じ点が問い合わせなしで再現される）
2. **3つの付与スクリプトに `--target` を追加**する（src/add_elevation.py、src/add_river_coast.py、src/add_landform.py）
   - `--target monuments`（既定）：今までと全く同じ動き。入出力ファイル名も変えない
   - `--target points`：入力を points_{県コード}.csv に、出力をそれぞれ elevation_points_{県コード}.csv、river_coast_points_{県コード}.csv、landform_points_{県コード}.csv にする。add_river_coast.py が読む標高ファイルも elevation_points_{県コード}.csv にする
   - points_ のファイルが無いときは「先に python src/make_comparison_points.py --pref 36 を実行してください」と出して終わる
   - 計算部分（process_〜 関数）の中身は変えない。変えるのは main のファイル名の決め方だけにする
3. **tests/test_make_comparison_points.py** を作る。ネットに接続せず、偽物の標高関数と tmp_path（一時フォルダ）だけで動かす。本物の data/cache・data/processed には読み書きしない
   - a. 同じシード値で2回作ると、points CSV の中身が完全に一致する
   - b. シード値を変えると点の位置が変わる
   - c. すべての点が、元の碑から 100m以上 2,000m以内（ハバーサイン式で計算し、誤差 ±1m を許す）
   - d. 偽物の標高関数が特定の候補に `"-----"` を返すとき、その位置の点は出力されず、捨てた候補の数に数えられる
   - e. 偽物の標高関数が常に `"-----"` を返す碑では、候補50回で止まり、その碑の点は0点、まとめに IDと点数が出る
   - f. 碑の並び順を入れ替えても、各碑の点の位置は変わらない（碑IDを混ぜた乱数の確認）
   - g. 元の碑の災害種別・種別_7列が、比較地点にそのまま写っている
   - h. ID が `{碑ID}-P{n}` の形で、1基あたり最大5点
4. **`--target` のテスト**を追加する（どのファイルに書いてもよい）：`--target points` のときの入出力ファイル名、`--target` 省略時に今までのファイル名のままであること。ファイル名の決め方を関数に分けて、その関数を直接テストする形でよい
5. **持ち越しの軽微1件（M3_review-7 No.1）**：tests/test_add_landform.py の test_cache_untouched で、`Path("data") / "cache" / "landform" / "16"` をプロジェクトの場所（PROJECT_ROOT。src/add_landform.py の PROJECT_ROOT を import するか、`Path(__file__).parent.parent`）を基準にした書き方に直す。中身の確認内容は変えない
6. 実データで実行する（順番どおり。徳島）
   ```
   .\.venv\Scripts\python.exe src\make_comparison_points.py --pref 36
   .\.venv\Scripts\python.exe src\add_elevation.py --pref 36 --target points
   .\.venv\Scripts\python.exe src\add_river_coast.py --pref 36 --target points
   .\.venv\Scripts\python.exe src\add_landform.py --pref 36 --target points
   ```
   - 問い合わせは1秒間隔のため、全体で **1〜1.5時間程度** かかる見込み（推測ですが、標高 約355×5回＋川岸 約355×最大7回＋地形タイル 数百枚）。途中で止まっても再実行で続きから進む
   - 最後に、碑の側（`--target` なし）の3スクリプトも1回ずつ実行し、まとめの「問い合わせ回数 0」と、出力CSV（elevation_36・river_coast_36・landform_36）の中身が実行前と変わらないことを確かめる（実行前にコピーを一時フォルダに取って比べる。比較用コピーはプロジェクトの外か、終わったら報告書で場所を示す）

## やらないこと
- 集計表・グラフ・移転碑の印（M4-02 で行う）
- 既存の計算部分（標高の取り方、川岸の標高の選び方、地形分類の判定）の変更
- 既存テストの期待値の変更
- 本物の data/cache・data/processed をテストで読み書きすること
- data/cache の中身の削除

## 完成の条件
- `.\.venv\Scripts\python.exe -m pytest` で全件合格（今の45件＋今回追加分）
- data/processed/points_36.csv ができ、点の数が 355 以下で、5点に届かなかった碑がまとめに出ている
- elevation_points_36.csv・river_coast_points_36.csv・landform_points_36.csv の行数が points_36.csv と同じ
- make_comparison_points.py を同じ設定でもう一度実行すると、points_36.csv の中身が1回目と完全に一致し、問い合わせ回数が0
- 碑の側の3つの出力CSVが、今回の作業の前後で変わっていない

## 完了後
- 自己チェックを行い、docs/dev/reports/M4-01_report.md に報告を書く。報告には次も書く
  - 実データのまとめ表示（4スクリプト分。そのまま貼る）
  - 2回目の make_comparison_points.py の問い合わせ回数と、1回目との一致確認の方法・結果
  - 碑の側の出力CSVが変わっていないことの確認方法・結果
  - 作成・変更したファイルの名前とバイト数の一覧
