# 指示書 M13-01（実装・全国集計表と都道府県別の件数表）　作成日：2026-10-13

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る。言い換え・要約・記憶からの作り直しをしない」）。
作業前に、エディタのタブをすべて閉じてから始めてください。作業中に docs/dev/status.md・output/ 配下の既存ファイル・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。実データでの本番の実行（`python src/run_batch.py --pref ...`（--check-only を除く）や `python src/update.py ...`）はしない。

## 目的（このテーマ1つ）
計画書 M13（版11.5）のうち「全国の集計表（地形指標・地形分類・ハザード区域との重なり。碑と比較地点、全碑と移転碑を除く）」と「都道府県別の件数表」を作る。
data/processed の47都道府県のファイルを読むだけで、ネットへの問い合わせはしない。年代別推移とグラフは次の指示書（M13-02）で行うので、今回は作らない。

## 対象ファイル
- 新しく作る：src/summarize_national.py、tests/test_summarize_national.py、docs/dev/reports/M13-01_report.md
- 実行で作られる：output/summary_all.csv、output/landform_all.csv、output/hazard_summary_all.csv、output/relocated_all.csv、output/pref_counts_all.csv
- 変えないもの：上記以外のすべてのファイル（**src/summarize.py・src/summarize_hazard.py も変更しない**。県別の出力 output/*_XX.csv も変わらないこと）

## 作り方の方針
- 県別の集計と同じ計算にするため、既存の関数を import して使う（コピーしない）：
  - src/summarize.py の `get_filenames`、`get_valid_series`、`analyze_indicator`、`extract_relocated`、`DISASTER_TYPES`
  - src/summarize_hazard.py の `calc_hazard_stats`
- 既存の `summarize.main()`・`summarize_hazard.summarize()` の中にある「範囲×災害種別×指標」のループは関数になっていないため、同じ手順を新しいファイルの関数として書く。**行の順番・列名・丸め方・空欄の扱い・注記行は県別のファイルとまったく同じにする**（下の「完成の条件」1 の照合テストで確かめる）
- 書き方は src/count_missing.py に合わせる（`# -*- coding: utf-8 -*-`、try/except の import、get_project_root()、関数ごとに日本語の docstring）。県名は src/prefectures.py の PREFECTURES

## やること
1. src/summarize_national.py を作る。関数は次のとおり（名前・引数はこのとおり）
   1. `load_pref(pref, base_dir)`：1県分を読み、`(mon, pt, mon_haz, pt_haz)` の4つの DataFrame を返す
      - mon・pt：`summarize.load_and_merge` と同じ列・同じ結合（monuments／points に elevation・river_coast・landform を ID で left 結合）。ファイル名は `summarize.get_filenames(pref, target, base_dir / "data" / "processed")` で得る
      - mon_haz・pt_haz：`summarize_hazard.summarize` と同じ結合（monuments_XX と hazard_XX を、hazard 側の 碑名・緯度・経度 を落として ID で inner 結合。points 側は 碑名・緯度・経度・元の碑ID を落とす）
      - read_csv の dtype・encoding は既存と同じ（ID・元の碑ID は str、utf-8-sig）
   2. `check_all_files(base_dir)`：47都道府県について、上で読む10ファイル（monuments・elevation・river_coast・landform・hazard と、それぞれの比較地点版）がそろっているかを調べ、足りない県コードのリストを返す
   3. `build_summary_tables(mon, pt, relocated_ids)`：`summarize.main()` と同じ手順で summary の表と landform の表の2つの DataFrame を返す（丸め：中央値・四分位・差の中央値は小数2桁、碑の方が大きい割合は3桁、地形の割合は3桁）
   4. `build_hazard_table(mon_haz, pt_haz, relocated_ids)`：`summarize_hazard.summarize()` と同じ手順で hazard_summary の表を返す（碑が0基の災害種別は行を出さない、も同じ）
   5. `build_pref_counts(base_dir)`：都道府県別の件数表を返す。列（この順・この名前）：
      `県コード,県名,碑_数,移転碑_数,比較地点_数,種別_洪水,種別_地震,種別_津波,種別_土砂災害,種別_高潮,種別_火山災害,種別_その他`
      - 碑_数＝monuments_XX の行数、比較地点_数＝points_XX の行数、移転碑_数＝その県の monuments に `extract_relocated` を使った件数、種別_○○＝monuments_XX の「種別_○○」列の合計（碑の数）
      - 県コード順（"01"〜"47"、2桁の文字列）。最後に 県コード「全国」・県名「合計」の行（各列の合計）
   6. `write_with_notes(df, path, notes)`：utf-8-sig・index なしで書き、続けて notes の各行を書く（県別と同じく `open(path, 'w', encoding='utf-8-sig', newline='')` に `df.to_csv(f, index=False)`）
   7. `main(args=None, base_dir=None)`：引数はなし。base_dir が None ならプロジェクトのルート
      - check_all_files で足りない県があれば、`エラー：ファイルが足りない県があります：岩手県（03）、…`（県名（コード）を「、」でつなぐ）と `先に実行してください：python src/run_batch.py --pref "XX,YY"` を表示して終了コード1で終わる（何も書かない）
      - 47都道府県を load_pref で読み、`pd.concat(..., ignore_index=True)` で全国の表にする（県コード順）
      - relocated_ids は全国の mon に `extract_relocated` を使って得る。output/relocated_all.csv に、県別と同じ列名（ID,碑名,所在地,該当語,伝承内容の該当箇所の前後30字）で書く（注記行なし）
      - summary_all.csv・landform_all.csv は県別と同じ注記1行、hazard_summary_all.csv は県別と同じ注記2行を付けて書く。pref_counts_all.csv は注記1行「注：1基が複数の災害種別を持つため、種別ごとの合計は碑の数より多くなります。」
      - 下の「表示」を出す
2. 表示（この文のとおり。件数は3桁ごとにカンマ。中央値は小数1桁、割合は小数3桁）
```
全国集計：47都道府県
碑：全碑 2,481基／移転碑を除く 2,379基　比較地点：全碑 12,395点／移転碑を除く 11,885点
移転碑（伝承内容に「移転」「移設」を含む碑）：102基
全碑・全種別の中央値（碑／比較地点）
  標高_m：18.6／56.2
  傾斜_度：4.3／7.2
  河川までの距離_m：145.0／288.0
  河川との高さの差_m：3.5／8.0
  海岸までの距離_m：2742.0／2770.0
全碑・全種別のハザード区域内の割合（碑／比較地点）
  洪水（想定最大規模）：0.347／0.247
  津波：0.240／0.105
  高潮：0.101／0.076
  土砂災害：0.243／0.069
出力：
  output/summary_all.csv
  output/landform_all.csv
  output/hazard_summary_all.csv
  output/relocated_all.csv
  output/pref_counts_all.csv
```
   - 数値はハードコードせず、作った表から取り出して表示する（上は既知の答え）
3. tests/test_summarize_national.py を作る
   1. 小さな作りもののデータ（tmp_path に2県分、各2〜3基・比較地点は1基あたり2点）で：build_pref_counts の県の行と「全国」行の合計、check_all_files が足りない県を返すこと、main が足りない県で終了コード1になり output に何も書かないこと
   2. **実データの照合テスト**（data/processed/monuments_36.csv がなければ pytest.skip）：47都道府県それぞれについて、load_pref → extract_relocated → build_summary_tables・build_hazard_table の結果を to_csv で文字列にしたものが、output/summary_XX.csv・landform_XX.csv・hazard_summary_XX.csv から「注：」で始まる行を除いた文字列と**完全に一致**すること（比べる前に両方の改行を "\n" にそろえる。BOM は utf-8-sig で読んで外す）。一致しない県があれば、県コードとファイル名を assert のメッセージに出す
   3. 実データの全国の値のテスト（同じく skip 条件あり）：下の「既知の答え」のうち、碑・比較地点・移転碑の数、pref_counts の「全国」行、summary の「全碑・全種別・標高_m」の行、hazard の「全碑・全種別・津波」の行
   4. 実データのテストは output/ に書かない（main を呼ぶテストは tmp_path を base_dir にする）
4. `python src/summarize_national.py` を1回実行し、下の「報告に貼るもの」のコマンドを実行して、**画面に出た文をコピーしてそのまま**報告に貼る

## 既知の答え（Claude が 2026-10-13 に実データで計算した値）
- 碑 2,481（ID の重複0）・比較地点 12,395（ID の重複0）・移転碑 102・移転碑を除く 碑 2,379・比較地点 11,885
- pref_counts の「全国」行：碑 2,481・移転碑 102・比較地点 12,395・洪水 1,112・地震 888・津波 596・土砂災害 629・高潮 138・火山災害 82・その他 119
- pref_counts の県の行の例：
| 県 | 碑 | 移転碑 | 比較地点 | 洪水 | 地震 | 津波 | 土砂災害 | 高潮 | 火山災害 | その他 |
|---|---|---|---|---|---|---|---|---|---|---|
| 01 北海道 | 54 | 3 | 270 | 21 | 11 | 12 | 8 | 0 | 15 | 2 |
| 03 岩手県 | 163 | 17 | 815 | 18 | 142 | 142 | 1 | 0 | 0 | 1 |
| 36 徳島県 | 71 | 2 | 349 | 10 | 51 | 49 | 8 | 2 | 0 | 1 |
| 47 沖縄県 | 8 | 0 | 40 | 0 | 3 | 6 | 0 | 1 | 1 | 1 |
- summary「全碑・全種別」：標高_m 碑_数 2,479・除外 2・中央値 18.6・第1四分位 6.1・第3四分位 93.0／比較地点_数 12,333・除外 62・中央値 56.2／組の数 2,478・差の中央値 -11.15・碑の方が大きい割合 0.282
- summary「全碑・津波・標高_m」：碑 596・中央値 6.6／比較地点 2,926・中央値 35.4／差の中央値 -27.5・割合 0.19
- 地形分類（全碑・全種別）：碑の有効 1,552（除外 929）、比較地点の有効 7,504（除外 4,891）。碑の上位：氾濫平野・海岸平野 451、山地斜面等 205、自然堤防 172、台地・段丘 169、砂州・砂丘 138
  - 比較地点の除外 4,891 は「データなし」4,890 ＋ 徳島の 36203-001-P5（取得済だがコードが空。第1版からの既知の状態）
- hazard「全碑・全種別・津波」：碑 2,481・取得不可 0・区域内 595・割合 0.24・3m以上 372・割合 0.15／比較地点 12,395・0・1,297・0.105・624・0.05
- hazard「全碑・津波・津波」：碑 596・区域内 425・割合 0.713／比較地点 2,970・区域内 729・割合 0.245
- hazard「移転碑を除く・全種別・津波」：碑 2,379・区域内 565・割合 0.237

## やらないこと
- 年代別推移・グラフ（M13-02）、公開ページ（M14）
- 既存ファイルの変更（src/summarize.py などの関数化・整理もしない）
- 移転碑の判定方法の変更（第1版と同じ「移転」「移設」を含むかどうか。集団移転などの誤検出は承知のうえ。第3版以降の検討候補）

## 完成の条件
1. 照合テスト（やること 3-2）が47都道府県すべてで一致（＝全国集計の計算は県別と同じ手順。徳島の行は第1版の集計と一致）
2. 表示と5つの CSV が既知の答えと一致
3. output/*_XX.csv（県別の出力）が変わっていない（`git status --short output` に出るのは新しい5ファイルだけ）
4. pytest 全件合格、pyflakes 0件、問題タブ エラー0件、新しいファイルは LF

## 報告に貼るもの（それぞれ実行したコマンドを1行目に、出力はそのまま）
1. `python src/summarize_national.py` の出力（全行）
2. `python -c "import pandas as pd;d=pd.read_csv('output/pref_counts_all.csv',dtype={'県コード':str},encoding='utf-8-sig',comment='注');print(len(d));print(d[d['県コード'].isin(['03','36','全国'])].to_string())"` の出力
3. `python -m pytest` の最後の数行
4. `python -m pyflakes src tests` の出力
5. `git status --short` の出力
6. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/summarize_national.py','tests/test_summarize_national.py']]"` の出力
7. 作成・変更したファイルとバイト数の一覧（**報告を書く直前に**測る）
- 出力に絶対パス（C:\Users\…）が出たら、その部分だけ「<プロジェクト>」に置き換える（pytest の rootdir 行も同じ）

## 完了後
- 自己チェックを行い、docs/dev/reports/M13-01_report.md に報告を書く（書式は docs/dev/reports/_template.md）。
