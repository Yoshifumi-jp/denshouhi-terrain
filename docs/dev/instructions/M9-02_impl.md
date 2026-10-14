# 指示書 M9-02（実装・標高キャッシュの検索を速くする）　作成日：2026-10-05

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」「完了報告」「作業用のスクリプトを作らない」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
src/add_elevation.py で、標高キャッシュ（data/cache/elevation_cache.csv）から値を探す処理を、表全体を毎回比べるやり方から「索引（辞書）で1回で引く」やり方に変える。
全国展開でキャッシュは数十万行になる見込みで、今のやり方では1回の検索ごとに全行を比べるため遅くなる。**結果（返す値・問い合わせ回数・キャッシュファイルの中身）は1つも変えない。**
GitHub への push・git commit は行わない。

## 対象ファイル
- 変更：src/add_elevation.py、tests/test_add_elevation.py
- **変えないもの**：ほかの src/*.py、tests/ のほかのファイル、data/cache/ のキャッシュファイル（読むだけ）、docs/ の中（報告書の追加以外）

## 1. 索引を作る関数（新規）
`build_cache_index(cache_df)` を追加する。
- 戻り値：辞書。キーは `(緯度を小数6桁に丸めた値, 経度を小数6桁に丸めた値)`、値は cache_df の行ラベル（index の値）
- キーは今の検索と同じ丸め方で作る：`zip(cache_df['緯度'].round(6), cache_df['経度'].round(6), cache_df.index)`
- 同じキーが2行以上あるときは**最初の行**を残す（今の `match.iloc[0]` と同じ）。`dict.setdefault` を使う
- 関数の説明（docstring）とコメントは日本語で書く

## 2. get_elevation_with_cache の変更
- 引数の最後に `cache_index=None` を追加する（既存の呼び出し・テストはそのまま動くこと）
- `cache_index` が None のときは、関数の中で `build_cache_index(cache_df)` を作って使う（遅いが結果は同じ。既存テスト用）
- 検索：`lat_key = round(lat, 6)`、`lon_key = round(lon, 6)`（今と同じ）で `cache_index.get((lat_key, lon_key))` を引く
- 見つかったとき：`cache_df.at[ラベル, '標高']`、`cache_df.at[ラベル, '標高データ種別']` を返す（今の `row['標高']`、`row['標高データ種別']` と同じ値）。stats の数え方は今と同じ
- 見つからず新しく取得したとき：今と同じく CSV に追記し、cache_df に行を足したあと、`cache_index.setdefault((lat_key, lon_key), 足した行のラベル)` で索引にも足す
- 1秒待つ条件・3回までのやり直し・戻り値の形・"-----" の扱いは変えない
- `mask = ...` で表全体を比べる行は消す

## 3. calculate_slope・process_monuments の変更
- calculate_slope にも引数の最後に `cache_index=None` を追加し、get_elevation_with_cache にそのまま渡す
- process_monuments では、load_cache の直後に `cache_index = build_cache_index(cache_df)` を1回だけ作り、中心の標高・傾斜の両方の呼び出しに渡す
- まとめ表示の文言・項目は変えない

## 4. やらないこと
- キャッシュファイルの列・形式・保存場所の変更
- 問い合わせの間隔（1秒）・やり直し回数の変更
- 出力ファイル（elevation_*.csv）の列・並び順の変更
- ほかの処理（add_hazard.py・add_landform.py など）のキャッシュの変更

## 5. 自動テスト（tests/test_add_elevation.py に追加。既存のテストは消さない）
1. 索引の作り方：同じ座標が2行ある小さな cache_df で、索引が最初の行のラベルを指すこと。小数7桁目だけ違う座標が同じキーになること
2. 結果が同じこと：50行ほどの cache_df（重複・"-----" の行を含む）で、全行の座標について、cache_index を渡した場合と渡さない場合（None）の戻り値・stats が同じこと
3. 新しく取得した点が索引に入ること：キャッシュにない座標を1回取得したあと、同じ座標をもう一度引くと fetch_func が呼ばれず、cache_hits が1増えること
4. 速さ：20万行の cache_df（乱数で作る。ファイルには書かない）と索引を作り、キャッシュにある1,000地点を引く時間が2秒未満であること（time.perf_counter で測る）
5. 実データでの照合：data/cache/elevation_cache.csv があるときだけ実行（ないときは pytest.skip）。load_cache で読み、全行の座標について、索引で引いた (標高, 標高データ種別) が、今までのやり方（`(cache_df['緯度'].round(6) == lat_key) & (cache_df['経度'].round(6) == lon_key)` の最初の行）と同じであること。fetch_func には呼ばれたら例外を出す関数を渡し、ネットにつながず、キャッシュファイルを書き換えないこと（テストの前後でファイルの sha256 が同じことも確かめる）

## 6. 徳島での確認（作業の最後に行う。ネットへの問い合わせは0回になる見込み）
標高の出力ファイルには実行日が「取得日」の列に入るため、ファイルのハッシュは変わる。そこで「取得日」の列を除いて比べ、比べたあとは元のファイルに戻す。
1. 作業前に次の2つを _to_delete/ にコピーしておく（名前の先頭に M9-02_before_ を付ける）
   - data/processed/elevation_36.csv → _to_delete/M9-02_before_elevation_36.csv
   - data/processed/elevation_points_36.csv → _to_delete/M9-02_before_elevation_points_36.csv
2. 作業後に次を実行する
   ```
   .\.venv\Scripts\python.exe src\add_elevation.py --pref 36
   .\.venv\Scripts\python.exe src\add_elevation.py --pref 36 --target points
   ```
3. 「取得日」以外が同じか比べる（2回実行。2回目は points のファイル名に置き換える）
   ```
   .\.venv\Scripts\python.exe -c "import pandas as pd; a=pd.read_csv('_to_delete/M9-02_before_elevation_36.csv',dtype=str).drop(columns=['取得日']); b=pd.read_csv('data/processed/elevation_36.csv',dtype=str).drop(columns=['取得日']); print('一致' if a.equals(b) else '不一致')"
   ```
4. 比べたあと、_to_delete/ のコピーを data/processed/ の元の名前に戻す（上書き。data/processed/ を作業前の状態に戻すため）。_to_delete/ のコピーはそのまま残してよい
5. 既知の答え：monuments は「今回サーバーに問い合わせた回数: 0」「キャッシュから読んだ回数: 355」（71基×5地点＝中心1＋傾斜用4）。points も問い合わせ回数は0（キャッシュから読んだ回数は報告に貼る）

## 7. 完成の条件
- 1〜3章のとおりに動き、5章のテストを含めて `python -m pytest` が全件合格（目安 145件。テスト全体を実行すること。1ファイルだけの実行は不可）
- 6章で monuments・points とも「一致」、問い合わせ回数0
- 「問題」タブのエラー0件／改行コードは LF のまま

## 8. 完了後
- 自己チェックを行い、docs/dev/reports/M9-02_report.md に報告を書く。次の実行結果を、画面に出た文のまま貼る
  - 6章の2の2回の実行の「------」から下のまとめ表示（全文）
  - 6章の3の結果（2回分）
  - `.\.venv\Scripts\python.exe -m pytest` の最後の行（テスト全体）
