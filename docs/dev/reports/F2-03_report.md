# 完了報告 F2-03

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/build_national.py | 41727 | 「8. 注意事項」のハザード注記で `hazard_note_lines.append(f"【{pref_name}】{note}")` に変更（1行変更） |
| src/make_national_pdf.py | 28702 | make_page_6 の注記追加処理を `notices.append(f"【{pref_name}】{note}")` に変更（if/else 4行を1行に変更） |
| tests/test_build_national.py | 22259 | `test_national_hazard_notes_format` を追加（偽データで index.html を作成し `【徳島県】` + 注記文が含まれ `徳島県：津波：` が含まれないことを検証） |
| output/national_report.pdf | 621083 | make_national_pdf.py の実行により再生成 |
| docs/national_report.pdf | 621083 | build_national.py の実行により output/ からコピー |
| docs/index.html | 593301 | build_national.py の実行により再生成（注記表記が「【徳島県】津波：…」に更新） |
| docs/dev/reports/F2-03_report.md | 4171 | 本報告書 |

## 指示されたコマンドの実行結果

### 1. `python src/make_national_pdf.py`
```
印刷用PDF：output/national_report.pdf
ページ数：6（A4 縦）
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
ファイルのサイズ：606.5 KB
```

### 2. `python src/build_national.py`
```
全国ページ：docs/index.html
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
色分け地図（碑の数）：0：0／1〜9：1／10〜19：6／20〜49：18／50〜99：15／100以上：7
一覧の地形分類：17区分＋データなし（データなし 929基）
作成したファイル：10
docs/index.html のサイズ：579.4 KB
公開前チェック：問題なし
```

### 3. `python -m pytest -q`
```
........................................................................ [ 32%]
........................................................................ [ 64%]
........................................................................ [ 96%]
........                                                                 [100%]
224 passed in 395.37s (0:06:35)
```

### 4. `python src/check_public.py`
```
公開前チェック：問題なし
```

### 5. `git status --short`
```
 M docs/index.html
 M docs/national_report.pdf
 M output/national_report.pdf
 M src/build_national.py
 M src/make_national_pdf.py
 M tests/test_build_national.py
?? docs/dev/reports/F2-03_report.md
```

### 6. `git diff --numstat`
```
1	1	docs/index.html
-	-	docs/national_report.pdf
-	-	output/national_report.pdf
1	1	src/build_national.py
1	4	src/make_national_pdf.py
50	0	tests/test_build_national.py
```

### 7. `git ls-files --eol src/build_national.py src/make_national_pdf.py tests/test_build_national.py docs/index.html`
```
i/lf    w/lf    attr/                 	docs/index.html
i/lf    w/lf    attr/                 	src/build_national.py
i/lf    w/lf    attr/                 	src/make_national_pdf.py
i/lf    w/lf    attr/                 	tests/test_build_national.py
```

## 自己チェック結果
- 問題タブのエラー件数：0件（pyflakes による静的チェック 0件）
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - pytest：224 passed（223＋1）で全件合格
  - check_public.py：「公開前チェック：問題なし」
  - make_national_pdf.py の表示：ページ数「6（A4 縦）」、碑「2,481基（47都道府県）」のまま
  - `git status --short`：指定の 7 行のみ
  - `git diff --numstat`：src/build_national.py「1 1」、src/make_national_pdf.py「1 4」、docs/index.html「1 1」、PDF 2件は「- -」、tests/test_build_national.py「50 0」
  - docs/national_report.pdf と output/national_report.pdf は同一内容（バイト数 621,083 バイト、ハッシュ一致を確認）
  - 改行コードは LF（`i/lf w/lf`）
  - 作成・変更した各ファイルがディスク上で空（0バイト）や変更前の内容に戻っていないことを確認済み

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
