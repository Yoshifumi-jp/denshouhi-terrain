# 完了報告 M13-02

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/summarize_national.py | 27557 | 年代別推移表作成（decade_label, build_years_table）、グラフ描画（draw_years_chart, draw_pref_counts_chart）、check_all_filesへのdenshou_XX.csv追加、mainでのyears_all.csv保存・グラフ出力・表示を追加 |
| tests/test_summarize_national.py | 29174 | decade_label、作りものデータでのbuild_years_table、main実行、実データ年代別推移の照合テストを追加 |
| output/years_all.csv | 1943 | 自然災害伝承碑の年代別推移（全国）の集計表 |
| output/fig/years_all.png | 100033 | 自然災害伝承碑の年代別推移（全国）の上下2段棒グラフ |
| output/fig/pref_counts_all.png | 158172 | 都道府県別の自然災害伝承碑の数の横棒グラフ |
| docs/dev/reports/M13-02_report.md | 6494 | 本完了報告 |

## 指示された実行結果

### 1. `python src/summarize_national.py` の出力（全行）
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
年代別推移（発生年は 2,475基、建立年は 2,194基で集計）
  発生年代の上位：1940年代 288基（昭和南海地震 81）／2010年代 246基（東日本大震災 126）／1920年代 240基（関東大震災 166）
  建立年代の上位：2010年代 239基／1930年代 218基／1980年代 190基
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

### 2. `python -c "import pandas as pd,io;t=open('output/years_all.csv',encoding='utf-8-sig').read();d=pd.read_csv(io.StringIO(''.join(l for l in t.splitlines(True) if not l.startswith('注：'))));print(len(d),d.iloc[:,1].sum(),d.iloc[:,2].sum());print(d[d['年代'].isin(['1600年より前','1920年代','1940年代','2010年代','2020年代'])].to_string())"` の出力
```
44 2475 2194
          年代  発生年代_碑の数  建立年代_碑の数     発生年代_主な災害
0   1600年より前         9         1         洪水(2)
33    1920年代       240       169    関東大震災(166)
35    1940年代       288        66    昭和南海地震(81)
42    2010年代       246       239   東日本大震災(126)
43    2020年代         4        94  令和5年台風第7号(2)
```

### 3. `python -m pytest` の最後の数行
```
rootdir: <プロジェクト>
configfile: pytest.ini
testpaths: tests
collected 189 items

tests\test_add_elevation.py ................                             [  8%]
tests\test_add_hazard.py ...........                                     [ 14%]
tests\test_add_landform.py .......                                       [ 17%]
tests\test_add_river_coast.py ..........................                 [ 31%]
tests\test_analyze_denshou.py ...........                                [ 37%]
tests\test_build_site.py ............                                    [ 43%]
tests\test_check_public.py ......                                        [ 47%]
tests\test_count_missing.py ....                                         [ 49%]
tests\test_load_monuments.py ................                            [ 57%]
tests\test_make_comparison_points.py .........                           [ 62%]
tests\test_make_map.py ..................                                [ 71%]
tests\test_prefectures.py .......                                        [ 75%]
tests\test_progress.py ...                                               [ 77%]
tests\test_run_batch.py ...........                                      [ 83%]
tests\test_summarize.py .....                                            [ 85%]
tests\test_summarize_hazard.py .......                                   [ 89%]
tests\test_summarize_national.py .......                                 [ 93%]
tests\test_update.py .............                                       [100%]

======================= 189 passed in 470.24s (0:07:50) =======================
```

### 4. `python -m pyflakes src tests` の出力
```
```
（エラー・警告なし、終了コード 0）

### 5. `git status --short` の出力
```
 M src/summarize_national.py
 M tests/test_summarize_national.py
?? docs/dev/reports/M13-02_report.md
?? output/fig/pref_counts_all.png
?? output/fig/years_all.png
?? output/years_all.csv
```

### 6. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/summarize_national.py','tests/test_summarize_national.py']]"` の出力
```
src/summarize_national.py False
tests/test_summarize_national.py False
```

### 7. 作成・変更したファイルとバイト数の一覧
```
src/summarize_national.py: 27557 bytes
tests/test_summarize_national.py: 29174 bytes
output/years_all.csv: 1943 bytes
output/fig/years_all.png: 100033 bytes
output/fig/pref_counts_all.png: 158172 bytes
docs/dev/reports/M13-02_report.md: 6494 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. 表示・years_all.csv が既知の答えと一致し、2つのグラフが開けて、上の段で昭和南海地震・東日本大震災・関東大震災などの名前が読める：達成（グラフ画像を直接開き確認済み）
  2. M13-01 の5つの CSV が変わっていない、output/*_XX.csv も変わっていない（`git status --short` に出るのは src・tests・新しい3ファイル・報告だけ）：達成
  3. pytest 全件合格（189 passed）、pyflakes 0件、問題タブ エラー0件、変更したファイルは LF：達成

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
