# 完了報告 M14-05

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/update_all.py | 17635 | 全国の更新コマンド（差分のある県・前回未完了の県のみ再構築、全国ページ等の一連の更新）の新規作成 |
| tests/test_update_all.py | 17987 | 全国の更新コマンドのテスト（全最新、差分1県、前回未完了、dry-run、失敗時の停止、再実行時のスキップと全国更新、実データdry-run）の新規作成 |
| src/make_national_pdf.py | 28809 | M14_review-4 軽微2件の修正（3ページの表見出しを全国ページと統一、ページ数取得を get_pagecount() に変更） |
| output/national_report.pdf | 620635 | 3ページ見出し変更の反映による再作成 |
| docs/national_report.pdf | 620635 | output/ からのコピー |
| docs/dev/reports/M14-05_report.md | 5174 | 本報告書 |

## 指示された実行結果

### 1. `git status --short`（作業前と、--dry-run の直前・直後）

- 作業前：
```
（出力なし、変更なし）
```

- `--dry-run` の直前：
```
 M docs/national_report.pdf
 M output/national_report.pdf
 M src/make_national_pdf.py
?? src/update_all.py
?? tests/test_update_all.py
```

- `--dry-run` の直後：
```
 M docs/national_report.pdf
 M output/national_report.pdf
 M src/make_national_pdf.py
?? src/update_all.py
?? tests/test_update_all.py
```
（※ `--dry-run` の前後でファイルの増減・変更がないことを確認）

### 2. `python src/update_all.py --dry-run`
```
全国の更新：使う伝承碑データ data/raw/2026-09-24/denshouhi_20260924.csv（取得日 2026-09-24、2,481基・47都道府県）
県ごとの判定：
  最新で作成済み：47県
  変更なし（作り直しません）：0県
  作り直す：0県
全国のページ：作り直します（全国の作り直しの記録がないため）
確認だけ行いました（--dry-run）。何も書き込んでいません
```

### 3. `python src/make_national_pdf.py` と `python src/build_national.py`

- `python src/make_national_pdf.py`:
```
印刷用PDF：output/national_report.pdf
ページ数：6（A4 縦）
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
ファイルのサイズ：606.1 KB
```

- `python src/build_national.py`:
```
全国ページ：docs/index.html
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
色分け地図（碑の数）：0：0／1〜9：1／10〜19：6／20〜49：18／50〜99：15／100以上：7
一覧の地形分類：17区分＋データなし（データなし 929基）
作成したファイル：10
docs/index.html のサイズ：579.3 KB
公開前チェック：問題なし
```

### 4. `git status --short` と `git diff --stat`（最後）

- `git status --short`:
```
 M docs/national_report.pdf
 M output/national_report.pdf
 M src/make_national_pdf.py
?? docs/dev/reports/M14-05_report.md
?? src/update_all.py
?? tests/test_update_all.py
```

- `git diff --stat`:
```
 docs/national_report.pdf   | Bin 618950 -> 620635 bytes
 output/national_report.pdf | Bin 618950 -> 620635 bytes
 src/make_national_pdf.py   |  12 +++++++-----
 3 files changed, 7 insertions(+), 5 deletions(-)
```

### 5. `python -m pytest -q`（最後の行）、`python -m pyflakes src/update_all.py src/make_national_pdf.py tests/test_update_all.py tests/test_make_national_pdf.py`

- `python -m pytest -q`（最後の行）：
```
213 passed in 391.83s (0:06:31)
```

- `python -m pyflakes src/update_all.py src/make_national_pdf.py tests/test_update_all.py tests/test_make_national_pdf.py`：
```
（出力なし、0件）
```

### 6. 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/update_all.py','src/make_national_pdf.py','tests/test_update_all.py','tests/test_make_national_pdf.py']]"`
```
src/update_all.py False
src/make_national_pdf.py False
tests/test_update_all.py False
tests/test_make_national_pdf.py False
```

### 7. 作成・変更したファイルのバイト数
```
src/update_all.py: 17635 bytes
src/make_national_pdf.py: 28809 bytes
tests/test_update_all.py: 17987 bytes
output/national_report.pdf: 620635 bytes
docs/national_report.pdf: 620635 bytes
docs/dev/reports/M14-05_report.md: 5174 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. 実データの `python src/update_all.py --dry-run` の表示が既知の答えと同じで、git status が実行の前後で変わらないこと：確認済み
  2. テスト1〜7が合格、pytest 全件合格（213件）、pyflakes 0件、LF であること：確認済み
  3. PDF の3ページの見出しが全国ページと同じであること、`python src/build_national.py` の表示が M14-04 と同じ7行で docs/index.html が変わらないこと：確認済み
  4. 作成・変更した各ファイルが空（0バイト）でないこと：確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
