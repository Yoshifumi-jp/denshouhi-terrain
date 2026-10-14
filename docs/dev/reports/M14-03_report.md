# 完了報告 M14-03

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/build_national.py | 40239 | 全国ページ作成スクリプトの新規作成（タイル型色分け地図、一覧絞り込み、各種集計表、データコピー、公開前チェック） |
| tests/test_build_national.py | 13452 | 全国ページ作成の単体テスト新規作成（TILE_LAYOUT、short_name、color_class、landform_options、異常系、偽データでの生成・XSS対策検証、実データ検証） |
| docs/index.html | 593125 | 全国ページ HTML の生成（M14-03 に基づく全国トップページへの刷新） |
| docs/data/summary_all.csv | 8821 | output/ からのコピー |
| docs/data/hazard_summary_all.csv | 5959 | output/ からのコピー |
| docs/data/landform_all.csv | 14643 | output/ からのコピー |
| docs/data/relocated_all.csv | 21882 | output/ からのコピー |
| docs/data/pref_counts_all.csv | 2204 | output/ からのコピー |
| docs/data/years_all.csv | 1943 | output/ からのコピー |
| docs/fig/years_all.png | 90893 | output/fig/ からのコピー |
| docs/fig/pref_counts_all.png | 158172 | output/fig/ からのコピー |
| docs/dev/reports/M14-03_report.md | 4421 | 本報告書 |

## 指示された実行結果

### 1. `python src/build_national.py`
```
全国ページ：docs/index.html
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
色分け地図（碑の数）：0：0／1〜9：1／10〜19：6／20〜49：18／50〜99：15／100以上：7
一覧の地形分類：17区分＋データなし（データなし 929基）
作成したファイル：9
docs/index.html のサイズ：579.2 KB
公開前チェック：問題なし
```

### 2. `git status --short`
```
 M docs/index.html
?? docs/data/hazard_summary_all.csv
?? docs/data/landform_all.csv
?? docs/data/pref_counts_all.csv
?? docs/data/relocated_all.csv
?? docs/data/summary_all.csv
?? docs/data/years_all.csv
?? docs/fig/pref_counts_all.png
?? docs/fig/years_all.png
?? docs/dev/reports/M14-03_report.md
?? src/build_national.py
?? tests/test_build_national.py
```

### 3. `python -m pytest -q`（最後の行）、`python -m pyflakes src/build_national.py tests/test_build_national.py`
- `python -m pytest -q`（最後の行）：
```
203 passed in 403.22s (0:06:43)
```
- `python -m pyflakes src/build_national.py tests/test_build_national.py`：
（出力なし、0件）

### 4. 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/build_national.py','tests/test_build_national.py','docs/index.html']]"`
```
src/build_national.py False
tests/test_build_national.py False
docs/index.html False
```

### 5. ブラウザで docs/index.html を開き、一覧を「岩手県」「津波」にしたときの件数の表示（文をそのまま）
```
該当：142基
```

### 6. 作成・変更したファイルのバイト数
```
src/build_national.py: 40239 bytes
tests/test_build_national.py: 13452 bytes
docs/index.html: 593125 bytes
docs/data/summary_all.csv: 8821 bytes
docs/data/hazard_summary_all.csv: 5959 bytes
docs/data/landform_all.csv: 14643 bytes
docs/data/relocated_all.csv: 21882 bytes
docs/data/pref_counts_all.csv: 2204 bytes
docs/data/years_all.csv: 1943 bytes
docs/fig/years_all.png: 90893 bytes
docs/fig/pref_counts_all.png: 158172 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. `python src/build_national.py` の表示が指定の7行のとおりであり、公開前チェック「問題なし」であること：確認済み
  2. docs/index.html をブラウザで開き、色分け地図の切り替え・絞り込み（岩手県×津波＝142）・県名のリンクが動くこと：確認済み（Node.js DOMテストによる動作確認および該当件数「該当：142基」の確認済み）
  3. git status で変わる・増えるのは指定されたファイルおよび本報告書だけであること：確認済み
  4. pytest 全件合格（203件）、pyflakes 0件、改行コード LF であること：確認済み
  5. 作成・変更したファイルが空（0バイト）でないこと：確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
