# 指示書 M3-02（修正）　作成日：2026-09-30

最初に AGENTS.md を読んでから作業してください。

## 目的（このテーマ1つ）
M3-01 の自動テストを指示書 M3-01 の 11-e・11-f のとおりに直し、本体の処理を検査できるようにする。

## 対象ファイル
- src/add_river_coast.py（読み込み処理を関数に分けるだけ。計算・出力の中身は変えない）
- tests/test_add_river_coast.py

## 不具合の内容
- 起きていること：
  1. test_height_diff が「碑 2.0m・河川 5.0m → −3.0m」を −1.5m に変えて検査しており、「河川の標高なし」「通信エラー」の場合を検査していない
  2. test_encoding_and_crs が本体の関数を呼ばず、テストの中で read_file と set_crs を書き直している（本体が壊れても合格してしまう）
- 本来の動き：指示書 M3-01 の 11-e・11-f のとおり、本体の処理を通して結果を確かめる
- 原因の見立て（Claudeのソース確認 M3_review-1 より）：tests/test_add_river_coast.py 59–146行、src/add_river_coast.py 70–86行（河川・海岸線の読み込みが process_river_coast の中に直接書かれている）

## やること（手順）
1. src/add_river_coast.py に、シェープファイルを読む関数を1つ作る。
   - 名前：`read_line_shapefile(shp_path)`
   - 処理：cp932 で読み込み、EPSG:4612 を設定した GeoDataFrame を返す（平面直角座標系への変換はしない）
   - process_river_coast の河川・海岸線の読み込み（70–86行付近）は、この関数を呼んでから to_crs する形に置き換える。エラー表示の文言・sys.exit の動きは今のまま
2. test_encoding_and_crs を、`read_line_shapefile` を呼ぶ形に直す（.cpg・.prj を削除してから呼び、「吉野川」と読めること、crs が EPSG:4612 であることを確かめる）。
3. test_height_diff を、次の5つの場合を確かめる形に直す。場合ごとに問い合わせ関数（mock_fetch）の返す値を変える必要があるため、場合ごとに process_river_coast を呼び、キャッシュ・出力のフォルダは場合ごとに tmp_path の下に別々に作る（pytest.mark.parametrize を使ってよい）。
   | 場合 | 碑の標高 | 問い合わせ関数の動き | 期待する 河川との高さの差_m | 期待する 河川_状態 |
   |---|---|---|---|---|
   | 1 | 10.0 | {"elevation": 3.5} を返す | 6.5 | 取得済 |
   | 2 | 2.0 | {"elevation": 5.0} を返す | −3.0 | 取得済 |
   | 3 | 空欄（NaN） | {"elevation": 3.5} を返す | 空欄 | 高さの差 取得不可（碑の標高なし） |
   | 4 | 10.0 | {"elevation": "-----"} を返す | 空欄 | 高さの差 取得不可（河川の標高なし） |
   | 5 | 10.0 | 毎回例外（Exception）を出す | 空欄 | 高さの差 取得不可（通信エラー） |
   - 場合4・5では「河川最近点の標高_m」も空欄であることを確かめる
   - 待ち関数は何もしない関数を渡す（テストが待たないように）
4. 報告書を書く前に `.venv\Scripts\python -m pytest` を実行し、全件合格を確かめる。

## やらないこと
- 距離・最近点・高さの差の計算や出力列・表示の変更
- M3_review-1 の No.3・No.4（使っていない import、警告の抑制）の修正（次の指示書で行う）
- 地形分類の実装
- data/ フォルダの変更、git commit、git push

## 完成の条件
- test_height_diff が上の5つの場合を確かめ、test_encoding_and_crs が read_line_shapefile を呼んでいる
- `.venv\Scripts\python -m pytest` で全件合格（M1・M2 のテストを含む。件数は増えてよい）
- `.venv\Scripts\python src\add_river_coast.py --pref 36` を実行すると、問い合わせ回数0回で、river_coast_36.csv の中身が修正前と同じ（取得日の列を除く）
- VS Code の「問題」タブでエラー0件

## 完了後
- 自己チェックを行い、docs/dev/reports/M3-02_report.md に報告を書く。
- 報告には AGENTS.md のとおり「ファイル名とバイト数」の一覧を必ず入れる。pytest の最後の1行も貼り付ける。
