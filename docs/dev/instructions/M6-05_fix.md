# 指示書 M6-05（修正・公開前チェックの対象範囲）　作成日：2026-10-03

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」）。
M6-04 の完了報告を書いたあとに行ってください。作業前に、エディタのタブをすべて閉じてください。

## 目的（このテーマ1つ）
公開前チェック（python src/check_public.py）が、公開する docs/data/ の CSV を調べていない不具合を直し、テストが本体と同じ処理を確かめるようにする。

## 対象ファイル
- src/check_public.py、tests/test_check_public.py

## 不具合の内容
- 起きていること：main の除外判定 `any(exclude in p.parts ...)` が「data」という名前のフォルダをどこでも除外するため、docs/data/summary_36.csv なども調べていない
- 本来の動き：除外するのはプロジェクト直下の .venv/、.git/、data/、_to_delete/ だけ。docs/data/ や output/ は調べる
- 原因の見立て（M6_review-3 No.2）：除外を「PROJECT_ROOT からの相対パスの先頭のフォルダ」で判定していない。テスト l は main と同じ判定を書き写しているため、同じ誤りを見逃した

## やること（手順）
1. 調べるファイルの一覧を作る関数（例 collect_targets(root)）を check_public.py に作り、main とテスト l の両方がこれを使う（テストに判定を書き写さない）。除外は root からの相対パスの先頭のフォルダが .venv／.git／data／_to_delete のときだけ。__pycache__ の中も除外してよい。
2. M6_review-3 No.6：ホームのパスは `/Users/<名前>/`、`/home/<名前>/` のように**後ろに区切りがあるとき**だけ検出し、`C:` の後ろの Users は数えない（同じ箇所を Windows とホームで二重に数えない）。
3. tests/test_check_public.py に追加：
   - m：tmp_path に「data/x.csv」「docs/data/y.csv」「_to_delete/z.txt」「output/w.csv」を作り、それぞれにメールアドレスを書く → collect_targets＋find_private_info で docs/data/y.csv と output/w.csv だけが見つかる
   - n：example.com の下の home フォルダを指す URL は見つからない。C ドライブのユーザーフォルダを円記号の重ねで書いた偽のパスは1件だけ数える（偽の個人情報は文字列をつなげて作る）
   - k：main を実行したときの表示（標準出力）に、偽のユーザー名（例 taro）とメールアドレスの文字が含まれないこと（tmp_path を root にして実行できるよう、main か関数に root を渡せるようにする）
   - l：collect_targets(PROJECT_ROOT)＋find_private_info で0件、かつ一覧に docs/data/summary_36.csv が含まれること（読むだけ）
4. `.\.venv\Scripts\python.exe src\check_public.py` を実行する。もし本物のファイルで見つかったら、直さずに報告に書いて止まる。

## やらないこと
- build_site.py の変更、docs/dev/ の読み書き、git commit・push

## 完成の条件
- `.\.venv\Scripts\python.exe -m pytest` で全件合格（出力の最後の数行をそのまま報告に貼る）
- check_public.py の実行出力をそのまま報告に貼る
- VS Code の問題タブのエラー件数・警告件数

## 完了後
- 自己チェックを行い、docs/dev/reports/M6-05_report.md に、**docs/dev/reports/_template.md の書式で**報告を書く（ファイル名とバイト数の一覧、問題タブの件数を含める。絶対パスは「<プロジェクト>」に置き換える）。
