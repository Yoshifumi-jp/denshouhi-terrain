# 指示書 M4-04（修正・グラフの横軸ラベルと県名の表示）　作成日：2026-10-02

最初に AGENTS.md を読んでから作業してください。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
summarize.py のグラフと表示の不具合（横軸ラベルのずれ、県名が「36」になる）を直す。

## 対象ファイル
- 変更：src/summarize.py、tests/test_summarize.py（テストの追加のみ）
- 他の src/ のファイルは変更しない

## 不具合の内容
1. 横軸ラベルのずれ（M4_review-3 No.1）
   - 起きていること：箱は 1・2.5・4・5.5・7 の位置に描くが、目盛りは 354 行の `range(1, ..., int(1.5))`（1刻み）で 1.2・2.2・3.2・4.2・5.2 に付く。「土砂災害」の箱にラベルがなく、ラベルが別の種別の箱の下に出る
   - 本来の動き：各種別の「碑」と「比較地点」の2つの箱の真ん中（pos + 0.2）に、その種別名が出る
   - 原因の見立て：src/summarize.py 354 行
2. 県名が「36」になる（M4_review-3 No.2）
   - 起きていること：`.\.venv\Scripts\python.exe src\summarize.py --pref 36` で「対象の県名: 36」、グラフのタイトルも「（36）」
   - 本来の動き：「徳島県」と表示される。--pref が 01〜47 以外や all のときは、add_river_coast.py の main と同じエラー文を出して終わる
   - 原因の見立て：src/summarize.py 179–183 行。`from src.prefectures import` が失敗したときの予備（`from prefectures import`）がない。県コードの確認がない

## やること（手順）
1. 箱を置く位置のリスト（positions）から、各種別の目盛り位置（2つの箱の中点）を作り、ax.set_xticks に渡す。目盛りの数と labels の数が一致するようにする
2. prefectures の import を add_river_coast.py と同じ書き方（try: from src.prefectures … except ImportError: from prefectures …）にし、ファイルの先頭に置く
3. main の最初で県コードを確認する（add_river_coast.py 367〜369 行と同じ条件・同じエラー文）。県名は PREFECTURES[pref] で取る
4. テストを追加する
   - i. 目盛り位置の確認：目盛り位置を作る処理を関数に分け（例 `tick_positions(positions)`）、種別5つのときに [1.2, 2.7, 4.2, 5.7, 7.2] を返すことを確かめる（手計算の値を直接書く）
   - j. --pref 99 と --pref all で SystemExit になり、エラー文が出る
   - 既存テストの偽データは県コード '99'・'98' を使っているため、県コードの確認で止まらないよう、テスト側で `summarize.PREFECTURES` に偽の県（'99'：'テスト県'、'98'：'テスト県2'）を monkeypatch で追加してよい。本体に偽の県を足さないこと
5. 実データで再実行し、グラフ6枚を作り直す

## やらないこと
- 集計の計算方法、CSV の列・値の変更（数値は今と同じになること）
- 地形分類の図の形（並べた横棒のままでよい）
- 既存テストの期待値の変更

## 完成の条件
- `.\.venv\Scripts\python.exe -m pytest` で全件合格
- まとめ表示が「対象の県名: 徳島県」
- box_*.png 5枚で、各種別名がその種別の2つの箱の真ん中の下に出ている（「土砂災害」も出る）。タイトルが「（徳島県）」
- summary_36.csv・landform_36.csv・relocated_36.csv のハッシュ値（Get-FileHash）が、修正前の報告の値と同じ
  - summary_36.csv：D2F374D65AF56EF4386E1514D10033119E857E4CBD89B79EA2BE997137D749BC
  - landform_36.csv：5276B6BE63FCF7604C0DD385F446EA3EECB3043AC22517F9ADDE7A39187598C4
  - relocated_36.csv：6FE701C5E6A47298596D70C3432FDCB31A7315548EA5529F5635599DC645FE04

## 完了後
- 自己チェックを行い、docs/dev/reports/M4-04_report.md に報告を書く。報告には次も書く
  - pytest の最後の行と、実データのまとめ表示（そのまま貼る）
  - CSV 3つのハッシュ値
  - 作成・変更したファイルの名前とバイト数の一覧
