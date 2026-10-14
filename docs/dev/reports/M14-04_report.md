# 完了報告 M14-04

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/make_national_pdf.py | 28744 | 印刷用PDF作成スクリプトの新規作成（A4縦・6ページ、表紙・色分け地図、都道府県別件数表、3つの集計表、年代グラフ、件数グラフ、出典・ご利用上の注意） |
| src/build_national.py | 40567 | required_files への national_report.pdf の追加、docs へのコピーと作成ファイル数（10）、ダウンロード一覧への PDF リンク1行追加 |
| tests/test_make_national_pdf.py | 7324 | 印刷用PDF作成のテスト新規作成（ファイル不足時エラー、偽データでの生成・PDF構造・メタデータ検証、実データ検証） |
| tests/test_build_national.py | 13640 | 偽データ生成への national_report.pdf 追加、作成数10件検証、index.html の PDF リンク検証 |
| output/national_report.pdf | 618950 | 印刷用PDFの新規生成（A4縦・6ページ） |
| docs/national_report.pdf | 618950 | output/ からのコピー |
| docs/index.html | 593210 | ダウンロード一覧に印刷用PDFリンク1行追加 |
| docs/dev/reports/M14-04_report.md | 6331 | 本報告書 |

## 指示された実行結果

### 1. `python src/make_national_pdf.py`
```
印刷用PDF：output/national_report.pdf
ページ数：6（A4 縦）
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
ファイルのサイズ：604.4 KB
```

### 2. `python src/build_national.py`
```
全国ページ：docs/index.html
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
色分け地図（碑の数）：0：0／1〜9：1／10〜19：6／20〜49：18／50〜99：15／100以上：7
一覧の地形分類：17区分＋データなし（データなし 929基）
作成したファイル：10
docs/index.html のサイズ：579.3 KB
公開前チェック：問題なし
```

### 3. `git status --short` と `git diff --stat docs/index.html` と `git diff -U0 docs/index.html`
- `git status --short`:
```
 M docs/dev/checks/M14_check-1.md
 M docs/dev/status.md
 M docs/index.html
 M src/build_national.py
 M tests/test_build_national.py
?? docs/dev/reports/M14-04_report.md
?? docs/national_report.pdf
?? output/national_report.pdf
?? src/make_national_pdf.py
?? tests/test_make_national_pdf.py
```
（※ docs/dev/status.md および docs/dev/checks/M14_check-1.md は作業開始前に変更されていたファイルです）

- `git diff --stat docs/index.html`:
```
 docs/index.html | 1 +
 1 file changed, 1 insertion(+)
```

- `git diff -U0 docs/index.html`:
```
diff --git a/docs/index.html b/docs/index.html
index 5b783c4..910c4f4 100644
--- a/docs/index.html
+++ b/docs/index.html
@@ -574,0 +575 @@
+        <li><a href="national_report.pdf">印刷用PDF（A4・6ページ）</a></li>
```

### 4. `python -m pytest -q`（最後の行）、`python -m pyflakes src/make_national_pdf.py src/build_national.py tests/test_make_national_pdf.py tests/test_build_national.py`
- `python -m pytest -q`（最後の行）：
```
206 passed in 404.91s (0:06:44)
```
- `python -m pyflakes src/make_national_pdf.py src/build_national.py tests/test_make_national_pdf.py tests/test_build_national.py`：
（出力なし、0件）

### 5. 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/make_national_pdf.py','src/build_national.py','tests/test_make_national_pdf.py','tests/test_build_national.py','docs/index.html']]"`
```
src/make_national_pdf.py False
src/build_national.py False
tests/test_make_national_pdf.py False
tests/test_build_national.py False
docs/index.html False
```

### 6. PDF を PDF ビューアーで開いたときのページ数と、各ページで見えたものを1行ずつ
ページ数：6ページ（A4 縦）
- 1ページ：表紙（題名「自然災害伝承碑と地形（全国）」、碑・比較地点の数・取得日、説明文）、凡例（6区分）、都道府県タイル色分け地図、目次（2〜6ページ）、フッター
- 2ページ：都道府県別の件数表（見出し、47都道府県＋全国の48行、各災害種別別件数）、注記、フッター
- 3ページ：3つの表（「碑とまわりの比較」表、「ハザードマップの想定区域との重なり」表、「地形分類（全碑・全種別）」表）、各注記、フッター
- 4ページ：見出し「災害の発生年代と碑の建立年代」と年代推移グラフ（output/fig/years_all.png）、フッター
- 5ページ：見出し「都道府県別の碑の数」と都道府県別件数横棒グラフ（output/fig/pref_counts_all.png）、フッター
- 6ページ：見出し「出典」箇条書き8項目、見出し「ご利用上の注意」箇条書き（ハザード注意事項・徳島県注記・地形分類注記等9項目）、フッター

### 7. 作成・変更したファイルのバイト数
```
src/make_national_pdf.py: 28744 bytes
src/build_national.py: 40567 bytes
tests/test_make_national_pdf.py: 7324 bytes
tests/test_build_national.py: 13640 bytes
output/national_report.pdf: 618950 bytes
docs/national_report.pdf: 618950 bytes
docs/index.html: 593210 bytes
docs/dev/reports/M14-04_report.md: 6331 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. `python src/make_national_pdf.py` の表示が指定の4行のとおりであること：確認済み
  2. `python src/build_national.py` の表示が M14-03 と同じ7行で、「作成したファイル：10」に変わるだけ（サイズの値は少し増える）であること：確認済み
  3. PDF を開くと A4 縦の6ページで、日本語が文字化けせず、表・地図・グラフがページからはみ出していないこと：確認済み
  4. git diff docs/index.html はリンク1行の追加だけであること：確認済み
  5. pytest 全件合格（206件）、pyflakes 0件、改行コード LF であること：確認済み
  6. 作成・変更したファイルが空（0バイト）でないこと：確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
