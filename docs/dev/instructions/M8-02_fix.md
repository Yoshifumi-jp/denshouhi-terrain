# 指示書 M8-02（修正・区域判定コマンドの起動方法・近い色の記録・テストの不足）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
M8-01 のソース確認（docs/dev/checks/M8_review-1.md）の No.1〜3 を直す。判定の結果（どの地点が区域内か、浸水深の区分）は変えない。

## 対象ファイル
- src/add_hazard.py、tests/test_add_hazard.py
- 生成物：data/processed/hazard_36.csv、hazard_points_36.csv（作り直し。キャッシュがあるので問い合わせは0件のはず）

## 不具合の内容
1. （No.1）`from src.prefectures import …` と `from src.hazard_layers import …` が try/except なしのため、`python src/add_hazard.py --pref 36` をスクリプトとして実行すると、環境変数 PYTHONPATH にプロジェクトのルートが入っていない限り "No module named 'src'" で止まる
   - 本来の動き：src/add_landform.py と同じく、`try: from src.xxx import …` ／ `except ImportError: from xxx import …` の形で、どちらの起動方法でも動く
2. （No.2）近い色の記録で、洪水・津波・高潮のときにキー（例「flood=255,215,190,255」）を書いている
   - 本来の動き：「洪水=…」「津波=…」「高潮=…」（土砂は今どおり「急傾斜地の崩壊=…」）。名前は src/hazard_layers.py に表として置き、コードに直接書かない（例 `SHINSUI_NAMES = {'flood': '洪水', 'tsunami': '津波', 'hightide': '高潮'}`）
3. （No.3）テストの不足（下の「テスト」）

## やること
1. 不具合1・2を直す
2. tests/test_add_hazard.py に次を足す・直す（既存のテストは残してよい。偽のタイルは「その地点の画素 (i, j) に色を塗る」形で作り、i, j は lonlat_to_pixel で求める）
   - k. 起動方法：`subprocess.run([sys.executable, "src/add_hazard.py", "--pref", "00"], cwd=PROJECT_ROOT, env=PYTHONPATH を取り除いた環境)` が、ImportError ではなく「--pref には 01〜47」のエラー文で終了コード1になる
   - f（直す）. main を偽データで実行（碑3件・比較地点3件）。偽タイル：1件目の地点の画素に洪水 255,216,192（完全一致）と急傾斜 250,70,0（近い色）、2件目の地点の画素に津波 255,215,190（近い色）、3件目は全レイヤー透明。確かめること：
     - 列名がこの順：ID、碑名、（比較地点だけ）元の碑ID、緯度、経度、洪水_状態、洪水_浸水深、洪水_色の一致、津波_状態、津波_浸水深、津波_色の一致、高潮_状態、高潮_浸水深、高潮_色の一致、土砂_状態、土砂_区分、土砂_現象、土砂_指定予定、土砂_色の一致、近い色の記録、取得日
     - ファイルの先頭が BOM（utf-8-sig）、行の順が入力どおり
     - 1件目：洪水 区域内・0.5m〜3m・完全一致／土砂 区域内・特別警戒区域・急傾斜地の崩壊・近い色／近い色の記録「急傾斜地の崩壊=250,70,0,255」
     - 2件目：津波 区域内・0.5m〜3m・近い色／近い色の記録「津波=255,215,190,255」
     - 3件目：すべて区域外、浸水深・区分・現象・色の一致・近い色の記録が空欄
     - 取得日が YYYY-MM-DD の形。取得不可がある行は空欄（偽 fetch で例外を出すレイヤーを1つ作った別の実行で確かめる）
     - 2回実行して、取得日の列を除き CSV がバイト単位で同じ
   - e（足す）. 404 のとき <y>.none ができる／例外のとき <y>.png も <y>.none もできない
   - g（足す）. --pref 48 で終了コード1／--target points で points_99.csv がないとき「先に python src/make_comparison_points.py --pref 99 を実行してください」で終了コード1
   - i（足す）. 本物のキャッシュでの照合に、浸水深の区分ごとの件数（M8-01_impl.md 5-2 の浸水深の行すべて）と、個別7基（M8-01_impl.md 7章 i の個別）を加える。結果は戻り値やファイルではなく、os.devnull への書き出しのままでよいので、照合のために process_monuments の結果（行のリスト）を返すようにしてよい
   - j（足す）. テストの前後で data/processed/ の hazard_36.csv・hazard_points_36.csv の更新日時が変わらない（ファイルがなければ skip）
3. 2つのコマンドを実行し直して CSV を作り直す（判定の結果は M8-01 と同じになること）

## やらないこと
- 判定のルール（色・透明度・近い色の決め方）、まとめ表示の文言、列の名前と順番の変更
- src/hazard_layers.py の既存の表の変更（SHINSUI_NAMES などの追加だけ可）
- 集計表・地図・公開ページ・update.py（M8-03 以降）
- docs/dev/ の中は報告書の追加以外は触れない

## 完成の条件
- `python src/add_hazard.py --pref 36` と `--target points` がエラーなく終わり、まとめ表示の件数が M8-01 の報告と同じ（問い合わせ0件）
- data/processed/hazard_36.csv の近い色の記録は「急傾斜地の崩壊=250,70,0,255」（36388-006）のまま
- `python -m pytest` で全件合格。`python -m pytest -q tests/test_add_hazard.py` も合格
- 問題タブのエラー0件

## 完了後
- 自己チェックを行い、docs/dev/reports/M8-02_report.md に報告を書く。まとめ表示とテスト結果は出力をそのまま貼る。**ただし pytest の rootdir 行など、ユーザー名入りの絶対パスは「<プロジェクト>」に置き換える**（AGENTS.md「個人情報の扱い」）。ファイル名とバイト数の一覧を必ず書く
