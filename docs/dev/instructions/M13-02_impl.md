# 指示書 M13-02（実装・年代別推移とグラフ）　作成日：2026-10-13

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る。言い換え・要約・記憶からの作り直しをしない」）。
作業前に、エディタのタブをすべて閉じてから始めてください。作業中に docs/dev/status.md・output/ 配下の既存ファイル・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。実データでの本番の実行（`python src/run_batch.py --pref ...`（--check-only を除く）や `python src/update.py ...`）はしない。

## 目的（このテーマ1つ）
計画書 M13（版11.5）の残り「年代別推移（災害の発生年代・建立年代ごとの碑の数）」と「グラフを output/ に出力」を、M13-01 で作った src/summarize_national.py に追加する。ネットへの問い合わせはしない。

## 対象ファイル
- 変更：src/summarize_national.py、tests/test_summarize_national.py
- 新しく作る：docs/dev/reports/M13-02_report.md
- 実行で作られる：output/years_all.csv、output/fig/years_all.png、output/fig/pref_counts_all.png（M13-01 の5つの CSV も作り直される。中身は変わらないこと）
- 変えないもの：上記以外のすべてのファイル（src/summarize.py・src/analyze_denshou.py なども変更しない）

## 読むファイル
- output/denshou_XX.csv（XX＝01〜47。utf-8-sig、ID は str）。県別の伝承内容の分析（analyze_denshou.py）の出力で、使う列は「発生年」「建立年_数値」「取り出した災害」
  - 「発生年」は、複数の災害がある碑では最も古い年がすでに入っている。そのまま使う（作り直さない）
  - 空欄（発生年 6基・建立年 287基）は数えない
- check_all_files で調べるファイルに output/denshou_XX.csv を加える（足りないときの「先に実行してください」の表示は今のままでよい）

## やること
1. src/summarize_national.py に関数を追加する（名前・引数はこのとおり）
   1. `decade_label(year)`：数値の年を年代の文字にする。1600未満は「1600年より前」、それ以外は「1940年代」の形（年を10で切り捨て）。空（NaN）は None
   2. `build_years_table(base_dir)`：47都道府県の denshou_XX.csv を県コード順に読んで束ね、年代別の表を返す。列（この順・この名前）：
      `年代,発生年代_碑の数,建立年代_碑の数,発生年代_主な災害`
      - 行は「1600年より前」、続けて「1600年代」〜「2020年代」の10年ごと（計44行。碑が0の年代も行を出す）
      - 発生年代_主な災害：その発生年代の碑について「取り出した災害」の**最初の災害名**（「；」で区切った先頭から、末尾の「(1854)」のような年の括弧を除いたもの）を数え、最も多い名前と件数を「関東大震災(166)」の形で書く。同じ件数なら名前の文字順で先のもの。碑が0の年代は空
      - **並べ替えはすべて明示する**（value_counts の順番に頼らない。件数の多い順→名前順）。M13_review-1 の No.2 のとおり、同じ件数の順番は pandas の版で変わるため
   3. `draw_years_chart(years_df, out_path)`：上下2段の棒グラフ（上：発生年代、下：建立年代）。横軸は44の年代（共通）、縦軸は碑の数
      - 上の段は、碑の数の多い6つの年代の棒の上に「主な災害」の名前（件数なし）を書く（多い順→年代の古い順で6つ）
      - タイトル「自然災害伝承碑の年代別推移（全国）」。横軸のラベルは「1600年より前」と、1650・1700…のように50年ごとの年代だけ表示してよい（読みやすさ優先）
      - 日本語フォントは summarize.py の set_jp_font を import して使う。下に出典「出典：国土地理院（自然災害伝承碑）を加工して作成」と注「発生年は、複数の災害がある碑では最も古い年」
      - サイズは横12×縦8インチ、dpi 150、`plt.close()` で閉じる
   4. `draw_pref_counts_chart(pref_counts_df, out_path)`：都道府県別の碑の数の横棒グラフ（「全国」行を除く47本、上から北海道→沖縄の順）。各棒の右に数を書く。タイトル「都道府県別の自然災害伝承碑の数」、出典は上と同じ。横10×縦12インチ、dpi 150
   5. main に追加：years_all.csv（注記2行「注：発生年は、複数の災害がある碑では最も古い年です。」「注：発生年が不明の碑 6基、建立年が不明の碑 287基は数えていません。」— 6・287 はハードコードせず計算した値）を write_with_notes で書き、2つのグラフを output/fig/ に作る
2. 表示（M13-01 の表示の「出力：」の前に、次の3行を足す。「出力：」の一覧には years_all.csv と2つのグラフを足す）
```
年代別推移（発生年は 2,475基、建立年は 2,194基で集計）
  発生年代の上位：1940年代 288基（昭和南海地震 81）／2010年代 246基（東日本大震災 126）／1920年代 240基（関東大震災 166）
  建立年代の上位：2010年代 239基／1930年代 218基／1980年代 190基
```
   「出力：」は次のとおり
```
出力：
  output/summary_all.csv
  output/landform_all.csv
  output/hazard_summary_all.csv
  output/relocated_all.csv
  output/pref_counts_all.csv
  output/years_all.csv
  output/fig/years_all.png
  output/fig/pref_counts_all.png
```
   - 数値はハードコードせず、作った表から取り出す（上は既知の答え）。上位3つの並びは件数の多い順→年代の古い順
3. tests/test_summarize_national.py にテストを追加する
   1. decade_label：1599→「1600年より前」、1600→「1600年代」、1946→「1940年代」、2026→「2020年代」、NaN→None
   2. 小さな作りもののデータ（tmp_path）で build_years_table：行数44、同じ件数の「主な災害」が名前順で選ばれること、年の括弧が除かれること、空欄を数えないこと
   3. 既存の作りもののデータのテスト（test_dummy_data_and_missing_checks）が denshou_XX.csv の追加で失敗しないよう、作りもののデータに denshou の2県分を足す。main を通すテストでは years_all.csv と2つの PNG が tmp_path/output にできることも確かめる
   4. 実データのテスト（data/processed/monuments_36.csv がなければ skip）：下の「既知の答え」の年代の行と合計
4. `python src/summarize_national.py` を1回実行し、2つの PNG を開いて文字化け・はみ出しがないことを自分で確かめる。下の「報告に貼るもの」を、**画面に出た文をコピーしてそのまま**報告に貼る

## 既知の答え（Claude が 2026-10-13 に実データで計算した値）
- years_all.csv：44行、発生年代_碑の数の合計 2,475、建立年代_碑の数の合計 2,194
| 年代 | 発生 | 建立 | 発生年代_主な災害 |
|---|---|---|---|
| 1600年より前 | 9 | 1 | 洪水(2) |
| 1600年代 | 3 | 0 | 慶長南海地震(2) |
| 1850年代 | 99 | 40 | 安政南海地震(39) |
| 1890年代 | 181 | 78 | 明治三陸地震(67) |
| 1920年代 | 240 | 169 | 関東大震災(166) |
| 1930年代 | 235 | 218 | 昭和三陸地震(90) |
| 1940年代 | 288 | 66 | 昭和南海地震(81) |
| 2010年代 | 246 | 239 | 東日本大震災(126) |
| 2020年代 | 4 | 94 | 令和5年台風第7号(2) |
- 上の段で名前を書く6つの年代：1940年代・2010年代・1920年代・1930年代・1950年代（伊勢湾台風）・1890年代
- M13-01 の5つの CSV は作り直しても中身が同じ（改行コードを除き、作業前のファイルと一致）

## やらないこと
- 公開ページへの組み込み（M14）、県別のグラフ・出力の変更
- 災害名の表記ゆれの統合（「洪水」「（名称なし）」なども、そのまま1つの名前として数える）

## 完成の条件
1. 表示・years_all.csv が既知の答えと一致し、2つのグラフが開けて、上の段で昭和南海地震・東日本大震災・関東大震災などの名前が読める
2. M13-01 の5つの CSV が変わっていない、output/*_XX.csv も変わっていない（`git status --short` に出るのは src・tests・新しい3ファイル・報告だけ）
3. pytest 全件合格、pyflakes 0件、問題タブ エラー0件、変更したファイルは LF

## 報告に貼るもの（それぞれ実行したコマンドを1行目に、出力はそのまま）
1. `python src/summarize_national.py` の出力（全行）
2. `python -c "import pandas as pd,io;t=open('output/years_all.csv',encoding='utf-8-sig').read();d=pd.read_csv(io.StringIO(''.join(l for l in t.splitlines(True) if not l.startswith('注：'))));print(len(d),d.iloc[:,1].sum(),d.iloc[:,2].sum());print(d[d['年代'].isin(['1600年より前','1920年代','1940年代','2010年代','2020年代'])].to_string())"` の出力
3. `python -m pytest` の最後の数行
4. `python -m pyflakes src tests` の出力
5. `git status --short` の出力
6. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/summarize_national.py','tests/test_summarize_national.py']]"` の出力
7. 作成・変更したファイルとバイト数の一覧（**報告を書く直前に**測る。PNG も含む）
- 出力に絶対パス（C:\Users\…）が出たら、その部分だけ「<プロジェクト>」に置き換える（pytest の rootdir 行も同じ）

## 完了後
- 自己チェックを行い、docs/dev/reports/M13-02_report.md に報告を書く（書式は docs/dev/reports/_template.md）。
