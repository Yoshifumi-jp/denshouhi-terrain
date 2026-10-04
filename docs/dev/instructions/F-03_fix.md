# 指示書 F-03（整理・コメントの日本語化と使っていない import の削除）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「作業用のスクリプトを作らない」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください。

## 目的（このテーマ1つ）
公開前の最終整理として、**動作を1つも変えずに**、英語だけのコメントを日本語にし、src/ の使っていない import・変数を消す（最終ソース確認 F_review-3 の軽微 No.1・No.2）。

## 対象ファイル
- 変更：下の表に出てくる src/*.py と tests/*.py（コメント行・import 行・該当の1行だけ）
- 変えないもの：上記以外のすべて。data/、output/、docs/（docs/dev/reports/ への報告書の追加を除く）。**プログラムの実行は pytest だけ**（make_map.py・build_site.py・update.py などは実行しない）

## やること
### 1. 英語だけのコメントを日本語にする（コメントの文だけを書き換える。行の位置・字下げは変えない）
意味が分からないものは、前後のコードから読み取れる内容を日本語で書く（例：`# map` → `# 地図`、`# Add new figures` → `# 追加したグラフ`、`# j` → `# j（M5 の確認項目 j）` のように記号だけのものは「〇〇の確認」と補う）。
| ファイル | 行（今の行番号） | 今のコメント |
|---|---|---|
| src/build_site.py | 108 | `# map` |
| src/build_site.py | 112 | `# fig` |
| src/build_site.py | 116 | `# Add new figures` |
| src/build_site.py | 125 | `# data` |
| src/build_site.py | 152 | `# Read denshou data` |
| src/build_site.py | 234 | `# Build denshou summary table (Table 1)` |
| src/build_site.py | 251 | `# Build disaster groups table (Table 2)` |
| src/check_public.py | 48 | `# Windows` |
| src/check_public.py | 56 | `# macOS/Linux` |
| src/check_public.py | 63 | `# Email` |
| src/prefectures.py | 1 | `# src/prefectures.py` |
| src/update.py | 68 | `# If no history or not found, try 2nd latest` |
| tests/test_add_hazard.py | 276 | `# for target points` |
| tests/test_add_landform.py | 132 | `# Check results` |
| tests/test_add_landform.py | 234 | `# Run the test` |
| tests/test_analyze_denshou.py | 22 | `# log scale test` |
| tests/test_analyze_denshou.py | 29 | `# linear scale test` |
| tests/test_analyze_denshou.py | 134 | `# Check A(1800)` |
| tests/test_analyze_denshou.py | 144 | `# Order: count desc -> year asc -> name asc` |
| tests/test_analyze_denshou.py | 145 | `# A(1800): count 3` |
| tests/test_analyze_denshou.py | 146 | `# C(1850): count 2` |
| tests/test_analyze_denshou.py | 147 | `# D(1800): count 2` |
| tests/test_analyze_denshou.py | 148 | `# B(1900): count 1` |
| tests/test_build_site.py | 18 | `# summary` |
| tests/test_build_site.py | 32 | `# others` |
| tests/test_build_site.py | 36 | `# denshou` |
| tests/test_build_site.py | 54 | `# fig` |
| tests/test_build_site.py | 67 | `# data/processed/monuments` |
| tests/test_build_site.py | 112 | `# b, c, d, g` |
| tests/test_make_map.py | 91 | `# j` |
| tests/test_make_map.py | 103 | `# k` |
| tests/test_make_map.py | 121 | `# l` |
| tests/test_make_map.py | 218 | `# Add denshou data for test` |
| tests/test_summarize.py | 165 | `# A (10) - pt_med(6.0) = 4.0` |
| tests/test_summarize.py | 166 | `# B (20) - pt_med(30.0) = -10.0` |

### 2. src/ の使っていない import・変数を消す（pyflakes＝使われていない名前を見つけるツール の指摘）
| ファイル・行 | 指摘 | やること |
|---|---|---|
| src/make_comparison_points.py 3 | `os` を import しているが使っていない | import 行を消す |
| src/make_comparison_points.py 8 | `collections.Counter` を使っていない | import 行を消す |
| src/make_comparison_points.py 9 | `datetime` を使っていない | import 行を消す |
| src/make_comparison_points.py 10 | `time` を使っていない | import 行を消す |
| src/make_map.py 4 | `math` を使っていない | import 行を消す |
| src/make_map.py 12 | `from src.summarize import check_files_exist, extract_relocated, get_filenames` の `get_filenames` を使っていない | `get_filenames` だけを消す。**同じファイルの except ImportError 側にも同じ import があれば、そちらも同じように直す** |
| src/add_landform.py 144 | `except Exception as e:` の `e` を使っていない | `except Exception:` にする |
| src/build_site.py 75 | `print(f"先に以下のコマンドを実行してください。")` の f が不要 | 先頭の `f` だけを消す（表示される文は変えない） |
| src/check_public.py 75 | `target_files = [...]` を使っていない（直下の for 文でルートのファイルはすべて調べているため不要） | この1行を消す |

消す前に、VS Code の検索（Ctrl+Shift+F）でその名前がファイルの中で本当に使われていないことを確かめる。使われていたら消さずに報告の「確認したいこと」に書く。

### 3. 改行コードを確かめる
変更した各ファイルについて、次のコマンド（PowerShell）で `False`（CR がない）と出ることを確かめ、出た文をそのまま報告に貼る。True のファイルは VS Code 右下「CRLF」→「LF」→ 保存（Ctrl+S）で直してから再実行する。
```
git diff --name-only | ForEach-Object { "$_ " + [IO.File]::ReadAllText($_).Contains("`r") }
```

### 4. テスト（ネット接続不要）
```
.\.venv\Scripts\python.exe -m pytest
```

### 5. 指紋と git status
```
Get-FileHash output\hazard_summary_36.csv, data\processed\hazard_36.csv, data\processed\hazard_points_36.csv -Algorithm SHA256 | ForEach-Object { $_.Hash.Substring(0,16).ToLower() + " " + (Split-Path $_.Path -Leaf) }
git status --short
```
（指紋の期待値 9a96085d74dcb2a6、b191e3742645ec6c、99c87b0ba59527e8。git status の「M」は src/・tests/ の .py と docs/dev/ だけ、「??」は報告書だけ）

## やらないこと
- コメント以外のコードの変更（上の表 2 の行を除く）。変数名・関数名・処理の順・表示される文の変更
- tests/ の使っていない import の削除（今回は対象外。第2版で扱う）
- 作業用のスクリプト・パッチファイルを作る、git commit・push

## 完成の条件
- 表 1 の35行がすべて日本語のコメントになっている
- 表 2 の9か所が直っている
- pytest が「135 passed」（失敗・エラー・skipped 0件）
- 変更したファイルがすべて LF
- 3ファイルの指紋が期待値と一致
- VS Code の「問題」タブでエラー0件

## 完了後
自己チェックを行い、docs/dev/reports/F-03_report.md に報告を書く。変更したファイルとバイト数、3・4・5 の出力（画面に出た文をそのまま）を入れる。
