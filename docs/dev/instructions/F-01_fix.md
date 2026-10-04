# 指示書 F-01（修正・ハザード判定の画面表示「徳島県県」）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「作業用のスクリプトを作らない」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください。
（F は「フェーズ4 最終確認」の指示書の番号です）

## 目的（このテーマ1つ）
src/add_hazard.py の画面表示（まとめ表示の1行目）で、県名が「徳島県県」と二重になる不具合を直し、テストで確かめる。

## 対象ファイル
- 変更：src/add_hazard.py（290行目付近の print 文1行だけ）、tests/test_add_hazard.py（test_real_cache に確かめる1行を足す）
- 変えないもの：上記以外のすべてのファイル。特に data/、output/、docs/（docs/dev/reports/ への報告書の追加を除く）
- **src/add_hazard.py そのものは実行しない**（実行すると data/processed/hazard_36.csv の「取得日」が書き換わるため）。確認は pytest だけで行う

## 不具合の内容（M8_review-6 No.11 より）
| 起きていること | 本来の動き |
|---|---|
| `print(f"ハザード区域の判定：{pref_name}県（{pref}）・{target_str}")` の pref_name は src/prefectures.py の PREFECTURES の値で、すでに「徳島県」のように「県」まで含む。そのため「ハザード区域の判定：徳島県県（36）・碑」と表示される | 「ハザード区域の判定：徳島県（36）・碑」と表示される（北海道・東京都・大阪府なども同じく、PREFECTURES の値をそのまま出す） |

## やること
1. src/add_hazard.py の該当の print 文から、`{pref_name}` の後ろの「県」の1文字だけを消す。他の行は1文字も変えない
2. tests/test_add_hazard.py の test_real_cache の `assert "対象：71件" in out` の直前に、次の1行を足す（既存の行は消さない・変えない）
   ```python
   assert "ハザード区域の判定：徳島県（36）・碑" in out
   ```
3. 改行コードを確かめる。次のコマンド（PowerShell）で2ファイルとも `False`（Windows 式の改行の文字 CR が残っていない）と出ることを確かめ、出た文をそのまま報告に貼る。True と出たら、VS Code 右下の「CRLF」をクリック →「LF」を選ぶ → 保存（Ctrl+S）で直してから、もう一度実行する
   ```
   foreach ($f in 'src\add_hazard.py','tests\test_add_hazard.py') { "$f " + [IO.File]::ReadAllText($f).Contains("`r") }
   ```
4. テストを実行する（ネット接続不要）
   ```
   .\.venv\Scripts\python.exe -m pytest
   ```
5. 変わってはいけないファイルが変わっていないことを確かめる。次のコマンドの出力をそのまま報告に貼る
   ```
   Get-FileHash output\hazard_summary_36.csv, data\processed\hazard_36.csv, data\processed\hazard_points_36.csv -Algorithm SHA256 | ForEach-Object { $_.Hash.Substring(0,16).ToLower() + " " + (Split-Path $_.Path -Leaf) }
   ```
   （意味：3つのファイルの指紋（SHA256 の先頭16文字）を表示する。期待値は 9a96085d74dcb2a6、b191e3742645ec6c、99c87b0ba59527e8）
6. `git status --short` の出力をそのまま報告に貼る（変更は2ファイルと報告書だけで、「??」の作業用ファイルがないこと）

## やらないこと
- 他の print 文・関数・変数名を変える、整形し直す
- src/add_hazard.py・update.py を実行する（data/・output/ が書き換わる）
- 作業用のスクリプト・パッチファイル（*.patch、temp_*.py など）を作る
- git commit・push

## 完成の条件
- src/add_hazard.py の差分が、print 文1行の「県」1文字の削除だけ
- tests/test_add_hazard.py の差分が、test_real_cache への assert 1行の追加だけ
- pytest がすべて passed（失敗・エラー 0件）。test_real_cache が skipped でなく passed であること
- 2ファイルとも改行コードが LF（3 のコマンドで2つとも False）
- 3ファイルの指紋が期待値と一致
- VS Code の「問題」タブでエラー0件

## 完了後
自己チェックを行い、docs/dev/reports/F-01_report.md に報告を書く。報告には次を入れる。
- 変更したファイルとバイト数
- 3・5・6 のコマンドの出力（画面に出た文をそのまま）
- pytest の最後の行（「〇 passed」など）をそのまま
