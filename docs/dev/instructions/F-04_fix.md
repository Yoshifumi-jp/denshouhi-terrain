# 指示書 F-04（修正・make_comparison_points.py の整理のやり直し）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「作業用のスクリプトを作らない」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください。

## 目的（このテーマ1つ）
F-03 で文字化けして動かなくなった src/make_comparison_points.py を、Claude が F-02 合格時の版に戻しました（M8 までの正しい中身。改行コードは CRLF のまま）。
このファイルだけについて、F-03 の整理を**文字化けさせずに**やり直す。

## 不具合の内容（F_review-4 より）
| No | 起きていたこと | 本来の動き |
|---|---|---|
| 1 | CRLF→LF の変換の途中で日本語が化け（「比較地点」→「比輁E��点」など）、文法の誤り（SyntaxError）で動かなくなった | 日本語は1文字も変わらず、改行コードだけが LF になる |
| 2 | 報告では問題タブ 0件だったが、実際は 3件 | 最後の変更の後に問題タブ・pytest を確かめ、その結果を書く |

## 対象ファイル
- 変更：src/make_comparison_points.py だけ
- 変えないもの：それ以外のすべて（F-03 で直した他の13ファイルは合格水準なので触らない）

## やること
1. VS Code で src/make_comparison_points.py を開く。右下が「UTF-8」であることを確かめる（違う表示なら止まって報告に書く）
2. 次の4行を消す（どれもファイルの中で使われていない）
   ```
   import os
   from collections import Counter
   import datetime
   import time
   ```
3. 193行目付近の `# try to extract from input_csv path` を `# 入力ファイルのパスから県コードを取り出す` に書き換える（行の位置・字下げは変えない）
4. 改行コードを LF にする：**VS Code 右下の「CRLF」をクリック →「LF」を選ぶ → 保存（Ctrl+S）** の方法だけを使う。
   PowerShell の Get-Content・Set-Content・Out-File、その他のツールやスクリプトでファイルを書き換えない（F-03 の文字化けの原因とみられるため）
5. **4 の後に**、次を順に実行し、出力をそのまま報告に貼る
   ```
   foreach ($f in 'src\make_comparison_points.py') { "$f " + [IO.File]::ReadAllText($f).Contains("`r") }
   git diff --ignore-cr-at-eol --stat -- src/make_comparison_points.py
   git diff --ignore-cr-at-eol -- src/make_comparison_points.py
   .\.venv\Scripts\python.exe -m pytest
   git status --short
   ```
   （1行目：CR が残っていれば True。2・3行目：改行コードの違いを無視した差分。消した4行と書き換えた1行だけが出るはず。日本語の行が出たら文字化けしている）
6. **5 の後に** VS Code の「問題」タブを開き、件数（エラー・警告）を報告に書く

## やらないこと
- 他のファイルを開いて保存する・書き換える
- 2・3 以外の行を変える
- 作業用のスクリプト・パッチファイルを作る、git commit・push

## 完成の条件
- 5 の1行目が `src\make_comparison_points.py False`
- 5 の差分が「4行の削除」と「コメント1行の書き換え」だけ（`1 file changed, 1 insertion(+), 5 deletions(-)`）
- pytest が「135 passed」（失敗・エラー・skipped 0件）
- 問題タブのエラー0件

## 完了後
docs/dev/reports/F-04_report.md に報告を書く。変更したファイルとバイト数、5 の出力（そのまま）、6 の件数を入れる。
