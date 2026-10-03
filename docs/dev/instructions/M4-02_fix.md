# 指示書 M4-02（修正・比較地点のテストと確認のやり直し）　作成日：2026-10-02

最初に AGENTS.md を読んでから作業してください。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
M4-01 のテストと報告の確認不足を補う（docs/dev/checks/M4_review-1.md の No.1〜3）。
本体（src/）の処理は変えない。

## 対象ファイル
- 変更：tests/test_make_comparison_points.py
- 改行コードのみ：tests/test_add_elevation.py、tests/test_add_river_coast.py
- 新規：docs/dev/reports/M4-02_report.md

## やること（手順）
1. tests/test_make_comparison_points.py のテストを、確認内容ごとに別の関数に分ける（例：test_a_same_seed …）。すべて tmp_path と偽物の標高関数だけで動かす
2. 次のテストを、指示どおりの内容で確かめる形に直す
   - d. 偽物の標高関数が「特定の候補」（例：呼び出し2回目と4回目）に `"-----"` を返すとき、①その緯度・経度が出力に無い ②まとめ表示の「海上などで捨てた候補の数」が 2 ③その碑の点は5点そろう
   - e. 常に `"-----"` を返す碑で、偽物の標高関数の呼び出し回数がちょうど 50 回、その碑の点は0点、まとめに「ID(0点)」が出る
   - f. 碑の並び順を入れ替えて作り直したとき、ID ごとの緯度・経度が完全に一致する（IDの集合だけでなく位置も比べる）
3. tests/test_add_elevation.py・tests/test_add_river_coast.py の改行コードを LF に戻す（中身は変えない）。`git diff --ignore-cr-at-eol` ではなく通常の `git diff 2d0097e --stat` で、この2ファイルの変更行数が数十行以内になっていることを確かめる
4. 実データで次を実行する（キャッシュがあるため問い合わせは0回の見込み）。出力はファイルに保存し、まとめ表示を **そのまま貼る**（書き換え・要約・作り直しをしない）
   ```
   .\.venv\Scripts\python.exe src\make_comparison_points.py --pref 36
   .\.venv\Scripts\python.exe src\add_landform.py --pref 36 --target points
   ```
   - make_comparison_points.py の実行前に points_36.csv をプロジェクト外へコピーし、実行後のファイルとハッシュ値（`Get-FileHash`）を比べて完全一致を確かめる
5. 作業用のファイル（ログ・バッチ・一時スクリプト）を作った場合は、プロジェクトの外に置くか、報告書に場所を書く

## やらないこと
- src/ の変更
- 既存テストの期待値の変更
- 本物の data/cache・data/processed をテストで読み書きすること

## 完成の条件
- `.\.venv\Scripts\python.exe -m pytest` で全件合格（d・e・f が上の内容を確かめている）
- 2ファイルの改行コードが LF
- points_36.csv の再作成前後でハッシュ値が一致し、問い合わせ回数 0
- 報告書のまとめ表示が、実行時の出力と1文字も違わない

## 完了後
- 自己チェックを行い、docs/dev/reports/M4-02_report.md に報告を書く。変更したファイルは **すべて**（改行コードだけの変更も含む）名前とバイト数を書く
