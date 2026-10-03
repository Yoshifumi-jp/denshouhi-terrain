# 指示書 M3-08（修正）　作成日：2026-10-01

最初に AGENTS.md を読んでから作業してください。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
add_landform.py のファイルの置き場所・問い合わせの作法を既存スクリプトと同じにし、**テストが本物のキャッシュに触れないようにする**。

## 対象ファイル
- src/add_landform.py
- tests/test_add_landform.py

## 不具合の内容（Claude のソース確認 M3_review-6 より）
1. 【重大】テスト test_process_monuments が本物のキャッシュ data/cache/landform/16 を shutil.rmtree で削除し、偽のタイルを本物のキャッシュに書いている（pytest のたびに取得済みタイルが消え、偽データが混ざる）
2. 【中】入出力・キャッシュのパスが相対パス（add_landform.py 58・59・68行）。実行する場所によって別のフォルダにファイルができる
3. 【中】取得に失敗したとき sleep_fn を呼ばない（118〜137行）。エラーが続くと間隔なしで問い合わせ続ける
4. 【軽微】県コードの確認が add_river_coast.py の main と違う（"99" でも動く）
5. 【軽微】`except URLError as e: raise e` は不要

## やること（手順）
1. add_landform.py の先頭で `PROJECT_ROOT = Path(__file__).parent.parent` を定め、main の入力・出力・キャッシュのパスをすべて PROJECT_ROOT 基準にする（add_river_coast.py と同じ書き方）
2. process_monuments に引数 cache_dir を追加し、関数の中でキャッシュの場所を決めない（呼び出し側が渡す）。main からは PROJECT_ROOT / "data" / "cache" / "landform" / "16" を渡す
3. テストは pytest の tmp_path の下にキャッシュフォルダを作って渡す。**shutil.rmtree を含め、data/ フォルダに触れる処理をテストからすべて取り除く**
4. 取得関数を呼んだ後は、成功・404・エラーのどれでも sleep_fn を1回呼ぶ（try の外、または finally で）
5. 県コードの確認を add_river_coast.py の main と同じにする（prefectures.py の PREFECTURES にない、または "all" なら同じエラー文で終了）
6. `except URLError as e: raise e` を削除する（URLError の import も不要なら削除）
7. テストを追加する
   k. テスト実行の前後で、本物の data/cache/landform フォルダの中身（ファイル名の一覧）が変わらない
   l. 通信エラーのタイルが2つあるとき、sleep_fn が2回呼ばれる
   m. 県コード "99" と "all" で終了する（SystemExit）
8. pytest 全件合格を確かめ、本体を実行して landform_36.csv を作り直す。結果（取得済60／データなし11）が変わらないこと、問い合わせ0回であることを確かめる

## やらないこと
- 地形分類の判定方法・出力列・対応表の変更
- data/ フォルダの手作業での変更（偽のタイル6枚の片付けは Claude が行う）、git commit、git push

## 完成の条件
- pytest 全件合格
- tests/test_add_landform.py に "data/cache" という文字列と shutil.rmtree がない
- 本体の結果が前回と同じ（取得済60／データなし11、地形分類名ごとの件数も同じ）、問い合わせ0回
- VS Code の「問題」タブでエラー0件

## 完了後
- 自己チェックを行い、docs/dev/reports/M3-08_report.md に報告を書く（ファイル名とバイト数の一覧、pytest の最後の1行、本体実行のまとめ表示を貼り付ける）。
- 報告を書いたら、エディタのタブに未保存（●）のファイルが残っていないことを確かめる。
