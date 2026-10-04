# 指示書 M8-08（修正・公開ページのハザードの節）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「作業用のスクリプトを作らない」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください。
**M8-07 の後に行う（M8-07 は make_map.py の改行コードだけが未達。M8_review-7 No.1。この指示書で一緒に直す）。**

## 目的（このテーマ1つ）
M8-06 で作った公開用ページ（src/build_site.py → docs/index.html）のハザードの節を、指示書 M8-06 の 3章どおりに直し、テストで確かめる。

## 対象ファイル
- 変更：src/build_site.py、tests/test_build_site.py、tests/test_update.py（改行コードだけ）、src/make_map.py（改行コードだけ）
- 生成物：docs/index.html、docs/map_36.html（output/map_36.html のコピー）、docs/data/
- 変えないもの：src/make_map.py の中身（改行コード以外）、src/update.py、src/hazard_layers.py、src/summarize_hazard.py、src/add_hazard.py、data/、output/
- docs/dev/ の中は報告書の追加以外は触れない

## 不具合の内容（M8_review-6 より）
| No | 起きていること | 本来の動き |
|---|---|---|
| 1 | hazard_section_html を作っているが html_content に入れていない。docs/index.html に表・注意書き・取得日・津波の注意が出ない | 「伝承内容の分析」の節（denshou_section_html）の後、「データのダウンロード」の前に入れる |
| 3 | source_html が f 文字列でなく、出典のリンク先が文字どおり「{HAZARD_SOURCE_URL}」 | リンク先が HAZARD_SOURCE_URL の値になる（f 文字列にするか、文字列をつないで作る。f 文字列にするときは他の { } に注意） |
| 4 | ハザード情報取得日が "2026-10-04" の直書き | data/processed/hazard_{pref}.csv の「取得日」列の空でない値の最も新しい日付（列がない・すべて空なら「—」） |
| 5 | 「ハザードマップの想定区域は国・都道府県が公表した想定です。…」の文が「データのダウンロード」「出典」の一覧にも入った | この文は「ご利用上の注意」の1か所だけ。「データのダウンロード」「出典」の一覧から消す |
| 10 | src/build_site.py・tests/test_update.py の改行コードがファイル全体で CRLF に変わった | LF に戻す |
| R7-1 | src/make_map.py の改行コードが CRLF のまま（M8-07 の報告では「LF」と書かれていたが、実際は CR を含む行が515行あった） | LF に戻す。中身は1文字も変えない |

## やること
1. No.1・3・4・5・10・R7-1 を直す（表の作り方 calc_ratio はそのままで正しい）
1b. 改行コードは、VS Code 右下の「CRLF」をクリック →「LF」を選ぶ → **保存（Ctrl+S）** で直す。直したら、次のコマンド（PowerShell）で4ファイルとも `False`（CR が残っていない）と出ることを確かめ、出た文をそのまま報告に貼る
   ```
   foreach ($f in 'src\build_site.py','tests\test_build_site.py','tests\test_update.py','src\make_map.py') { "$f " + [IO.File]::ReadAllText($f).Contains("`r") }
   ```
   （意味：各ファイルに CR＝Windows 式の改行の文字が含まれるかを True／False で表示する）
2. 作り直し（ネット接続不要）：
   ```
   .\.venv\Scripts\python.exe src\build_site.py --pref 36
   .\.venv\Scripts\python.exe -m pytest
   ```

## やらないこと
- 表の列・文言、既存の節（比較表・伝承内容・更新履歴）の文言を変える
- make_map.py を変える（M8-07 で合格済みのもの）
- 作業用のスクリプトを作る

## 自動テスト（tests/test_build_site.py。新しいテスト関数として加える。既存のテストは消さない）
create_fake_output の偽の hazard_summary と hazard_{pref}.csv を、次のものに置き換える（他のテストが使う列もそろえる）
```python
HAZ_COLS = ['範囲', '災害種別', 'ハザード', '碑_数', '碑_取得不可', '碑_区域内', '碑_区域内の割合', '碑_3m以上', '碑_3m以上の割合',
            '比較地点_数', '比較地点_取得不可', '比較地点_区域内', '比較地点_区域内の割合', '比較地点_3m以上', '比較地点_3m以上の割合']
haz_rows = [
    ['全碑', '全種別', '洪水（想定最大規模）', 10, 0, 3, 0.999, 1, 0.999, 40, 0, 6, 0.999, 2, 0.999],   # 割合の列はわざと件数と合わない値
    ['全碑', '全種別', '津波', 10, 0, 7, 0.999, 5, 0.999, 40, 0, 10, 0.999, 0, 0.999],
    ['全碑', '全種別', '高潮', 10, 0, 0, 0.999, 0, 0.999, 40, 0, 1, 0.999, 1, 0.999],
    ['全碑', '全種別', '土砂災害', 10, 0, 2, 0.999, '', '', 40, 0, 4, 0.999, '', ''],
    ['移転碑を除く', '全種別', '津波', 9, 0, 9, 1.0, 9, 1.0, 35, 0, 35, 1.0, 35, 1.0],
]
# CSV に書いた後、末尾に注の2行を追記する（summarize_hazard.py の出力と同じ形）
#   注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。
#   注：想定区域との重なりを示すもので、危険度の判定ではありません。出典：ハザードマップポータルサイト（加工して作成）
# hazard_{pref}.csv は ID と 取得日 の列で3行（'2026-09-30'、'2026-10-02'、空）
```
- a `test_hazard_section_table`：index.html から <tr> を読み、ハザードの節の表の行が次と一致（順も）
  ```python
  expected = [
      ['洪水（想定最大規模）', '30%（3／10基）', '15%（6／40点）', '10%（1／10基）', '5%（2／40点）'],
      ['津波', '70%（7／10基）', '25%（10／40点）', '50%（5／10基）', '0%（0／40点）'],
      ['高潮', '0%（0／10基）', '2%（1／40点）', '0%（0／10基）', '2%（1／40点）'],
      ['土砂災害', '20%（2／10基）', '10%（4／40点）', '—', '—'],
  ]
  ```
  （1/40＝2.5% は Python の round で 2 になる。この期待値のまま。「移転碑を除く」の行の「9／9基」「35／35点」が出ないことも確かめる）
- b `test_hazard_section_texts`：pref='36' で build_site → index.html に「ハザードマップの想定区域との重なり」の見出し、「想定区域との重なりを示すもので、危険度の判定ではありません。」、「ハザード情報取得日：2026-10-02」、HAZARD_DATA_NOTES['36'][0] の文がある。見出しの位置が「伝承内容の分析」より後、「データのダウンロード」より前
- c `test_hazard_notes_only_36`：PREFECTURES に '99' を足して（monkeypatch）pref='99' で build_site → 津波の注意の文がない
- d `test_hazard_source_and_notice`：index.html に `href="https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html"` があり、「{HAZARD_SOURCE_URL}」の文字がない。「ハザードマップの想定区域は国・都道府県が公表した想定です。」が index.html にちょうど1回
- e `test_hazard_summary_copied`：docs/data/hazard_summary_{pref}.csv があり、ダウンロードの一覧に `data/hazard_summary_{pref}.csv` へのリンクがある
- f `test_missing_hazard_summary`：output/hazard_summary_{pref}.csv を消して build_site → 出力に `hazard_summary_` と `python src/update.py --pref` が出て SystemExit のコード1
- g `test_real_hazard_table`（実データ。PROJECT_ROOT 基準で output/hazard_summary_36.csv がなければ skip）：tmp_path の site_dir に作った index.html の表の行が、指示書 M8-06 3章の expected_rows と一致。あわせて「ハザード情報取得日：2026-10-04」

**テストが本当に誤りを見つけるか（自分で確かめて報告に書く）**：No.1 の挿入を一時的に外すと a・b が失敗すること、取得日を "2026-10-04" の直書きに戻すと b が失敗することを確かめ、元に戻す（前後のバイト数を報告に書く）。作業用のスクリプトは使わず、エディタで直接書き換える。

## 完成の条件
- pytest がすべて合格。件数は「M8-07 合格時の件数＋このテストで増えた関数の数」と一致
- build_site.py の表示が「公開前チェック：問題なし」
- docs/index.html をブラウザで開くと、ハザードの節に指示書 M8-06 3章の expected_rows と同じ表・注意書き・「ハザード情報取得日：2026-10-04」・津波の注意が出る。出典の「ハザードマップポータルサイト」をクリックすると同サイトの「オープンデータ配信」のページが開く
- src/build_site.py・tests/test_build_site.py・tests/test_update.py・src/make_map.py の改行コードが LF（1b のコマンドで4つとも False）
- 問題タブのエラー0件

## 完了後
docs/dev/reports/M8-08_report.md に、次を必ず書く
- build_site.py の実行で画面に出た文を**そのまま**全部
- pytest の最後の行をそのままと、テスト関数の数の内訳（ファイルごと）
- 「テストが本当に誤りを見つけるか」の結果
- 変更したファイルとバイト数、改行コード（1b のコマンドの出力をそのまま）
- 「テストが本当に誤りを見つけるか」で一時的に書き換えたときは、元に戻す前と後のバイト数
- 実際に行っていないことを「行った」と書かない
