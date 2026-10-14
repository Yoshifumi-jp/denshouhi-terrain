# 完了報告 M13-03

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| src/summarize_national.py | 27556 | draw_years_chart 内の災害名の書き方を縦書き（rotation=90, ha='center', va='bottom', fontsize=9）および上段の縦軸上限を最大値×1.6倍に修正 |
| output/fig/years_all.png | 90893 | 年代別推移グラフ（上段の災害名が重ならず枠内に収まるように修正） |
| docs/dev/reports/M13-03_report.md | 6076 | 本完了報告 |

## 指示された実行結果

### 1. `git diff src/summarize_national.py` の出力
```
diff --git a/src/summarize_national.py b/src/summarize_national.py
index 907da02..f3236de 100644
--- a/src/summarize_national.py
+++ b/src/summarize_national.py
@@ -461,7 +461,7 @@ def draw_years_chart(years_df, out_path):
     top6 = temp_df.sort_values(by=['発生年代_碑の数', 'idx'], ascending=[False, True]).head(6)
 
     max_occur = occur_counts.max() if len(occur_counts) > 0 else 100
-    ax1.set_ylim(0, max_occur * 1.35)
+    ax1.set_ylim(0, max_occur * 1.6)
 
     max_built = built_counts.max() if len(built_counts) > 0 else 100
     ax2.set_ylim(0, max_built * 1.15)
@@ -476,10 +476,10 @@ def draw_years_chart(years_df, out_path):
                 idx,
                 cnt + max_occur * 0.02,
                 name,
-                ha='left',
+                ha='center',
                 va='bottom',
-                rotation=50,
-                fontsize=8.5
+                rotation=90,
+                fontsize=9
             )
 
     fig.suptitle("自然災害伝承碑の年代別推移（全国）", fontsize=15, y=0.98)
```

### 2. `python src/summarize_national.py` の出力（全行）
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

======================= 189 passed in 388.82s (0:06:28) =======================
```

### 4. `python -m pyflakes src tests` の出力
```
```
（エラー・警告なし、終了コード 0）

### 5. `git status --short` の出力
```
 M output/fig/years_all.png
 M src/summarize_national.py
?? docs/dev/reports/M13-03_report.md
```

### 6. 改行コードの確認：`python -c "import pathlib;p='src/summarize_national.py';print(p, b'\r\n' in pathlib.Path(p).read_bytes())"` の出力
```
src/summarize_national.py False
```

### 7. 変更・作成したファイルとバイト数の一覧
```
src/summarize_national.py: 27556 bytes
output/fig/years_all.png: 90893 bytes
docs/dev/reports/M13-03_report.md: 6076 bytes
```

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  1. years_all.png の6つの名前（明治三陸地震・関東大震災・昭和三陸地震・昭和南海地震・伊勢湾台風・東日本大震災）が重ならず、枠の中に収まる：達成（上限の倍率 1.6 で枠内に完全に収まることを画像を開いて確認）
  2. 表示と output の CSV（6ファイル）が作業前と同じ（`git diff --stat` に出るのは src/summarize_national.py と output/fig/years_all.png だけ）：達成
  3. pytest 全件合格（189 passed）、pyflakes 0件、問題タブ エラー0件、LF：達成

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし
