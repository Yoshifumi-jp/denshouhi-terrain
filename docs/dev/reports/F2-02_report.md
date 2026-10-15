# 完了報告 F2-02

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/build_site.py | 25091 | 431行目の `pref_html_path.write_text` に `newline='\n'` を追加（改行コードを LF に統一） |
| docs/pref_01.html | 10573 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_02.html | 10300 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_03.html | 10425 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_04.html | 10267 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_05.html | 10067 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_06.html | 9600 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_07.html | 10408 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_08.html | 10397 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_09.html | 10143 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_10.html | 10330 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_11.html | 10551 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_12.html | 10229 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_13.html | 10308 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_14.html | 10168 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_15.html | 10749 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_16.html | 9983 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_17.html | 9925 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_18.html | 10013 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_19.html | 10169 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_20.html | 10557 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_21.html | 10280 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_22.html | 10737 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_23.html | 10540 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_24.html | 10509 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_25.html | 9980 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_26.html | 10249 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_27.html | 10152 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_28.html | 10479 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_29.html | 10171 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_30.html | 10798 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_31.html | 9971 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_32.html | 10088 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_33.html | 10089 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_34.html | 10852 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_35.html | 10180 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_36.html | 10939 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_37.html | 10087 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_38.html | 10001 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_39.html | 10671 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_40.html | 10095 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_41.html | 10332 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_42.html | 10425 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_43.html | 10494 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_44.html | 10162 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_45.html | 9655 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_46.html | 10387 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/pref_47.html | 9885 | `python src/build_site.py --pref all` の実行により再生成（改行コードが CRLF から LF に変更） |
| docs/dev/reports/F2-02_report.md | 10497 | 本報告書 |

## 指示されたコマンドの実行結果

### 1. `python -m pytest -q`
```
........................................................................ [ 32%]
........................................................................ [ 64%]
........................................................................ [ 96%]
.......                                                                  [100%]
223 passed in 394.44s (0:06:34)
```

### 2. `python src/check_public.py`
```
公開前チェック：問題なし
```

### 3. `git status --short`
```
 M docs/pref_01.html
 M docs/pref_02.html
 M docs/pref_03.html
 M docs/pref_04.html
 M docs/pref_05.html
 M docs/pref_06.html
 M docs/pref_07.html
 M docs/pref_08.html
 M docs/pref_09.html
 M docs/pref_10.html
 M docs/pref_11.html
 M docs/pref_12.html
 M docs/pref_13.html
 M docs/pref_14.html
 M docs/pref_15.html
 M docs/pref_16.html
 M docs/pref_17.html
 M docs/pref_18.html
 M docs/pref_19.html
 M docs/pref_20.html
 M docs/pref_21.html
 M docs/pref_22.html
 M docs/pref_23.html
 M docs/pref_24.html
 M docs/pref_25.html
 M docs/pref_26.html
 M docs/pref_27.html
 M docs/pref_28.html
 M docs/pref_29.html
 M docs/pref_30.html
 M docs/pref_31.html
 M docs/pref_32.html
 M docs/pref_33.html
 M docs/pref_34.html
 M docs/pref_35.html
 M docs/pref_36.html
 M docs/pref_37.html
 M docs/pref_38.html
 M docs/pref_39.html
 M docs/pref_40.html
 M docs/pref_41.html
 M docs/pref_42.html
 M docs/pref_43.html
 M docs/pref_44.html
 M docs/pref_45.html
 M docs/pref_46.html
 M docs/pref_47.html
 M src/build_site.py
?? docs/dev/reports/F2-02_report.md
```

### 4. `git diff --ignore-cr-at-eol --numstat`
```
1	1	src/build_site.py
```

### 5. `git ls-files --eol src/build_site.py docs/pref_01.html docs/pref_36.html docs/pref_47.html docs/index.html`
```
i/lf    w/lf    attr/                 	docs/index.html
i/crlf  w/lf    attr/                 	docs/pref_01.html
i/crlf  w/lf    attr/                 	docs/pref_36.html
i/crlf  w/lf    attr/                 	docs/pref_47.html
i/lf    w/lf    attr/                 	src/build_site.py
```

## 自己チェック結果
- 問題タブのエラー件数：0件（pyflakes による静的チェック 0件）
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - pytest：223 passed で全件合格（F2-01 と同じ件数）
  - check_public.py：「公開前チェック：問題なし」
  - `git status --short`：` M src/build_site.py`、` M docs/pref_01.html`〜` M docs/pref_47.html`（47件）、`?? docs/dev/reports/F2-02_report.md` の計49行だけ。docs/index.html・docs/fig/・docs/data/・docs/map_XX.html・tests は差分なし
  - `git diff --ignore-cr-at-eol --numstat`：src/build_site.py は「1 1」。docs/pref_XX.html は中身に差分がないため一覧に出ない（1以上の pref なし）
  - `git ls-files --eol`：docs/pref_01・36・47.html が `i/crlf w/lf`（作業ツリーは LF）、src/build_site.py・docs/index.html は `i/lf w/lf`（LF）
  - 各ファイルが空（0バイト）や変更前に戻っていないことを確認済み。pref_XX.html は CRLF→LF で行数分だけサイズが減少していることを確認。

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
