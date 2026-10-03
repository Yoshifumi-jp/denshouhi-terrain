# 完了報告 M7-03

## 変更したファイル
| ファイル | バイト数 | 変更内容 |
|---|---|---|
| `src/make_map.py` | 15965 | `load_data`に`denshou_{pref}.csv`の読み込みと結合を追加、`build_map`と`build_popup_html`に伝承テキストの生成・挿入処理を追加。 |
| `tests/test_make_map.py` | 12533 | 統合テストでのモックデータの追加、`test_build_popup_denshou`テストの追加。 |
| `src/build_site.py` | 17092 | `denshou_{pref}.csv`等3つのCSV・PNGの確認・コピー・チェック追加。`index.html`に「伝承内容の分析」セクション・グラフ・ダウンロードリンクを追加。 |
| `tests/test_build_site.py` | 11839 | 3つのCSVと2つのPNGのモックデータ追加、出力ファイルと`index.html`の内容の検証処理を追加。 |
| `src/update.py` | 14873 | `summarize.py`の後に`analyze_denshou.py`のステップを追加（全12ステップ）。 |
| `tests/test_update.py` | 15131 | `test_k_run_steps_main`での期待する実行コマンド列を12件に修正。 |
| `src/analyze_denshou.py` | 16122 | `disaster_groups_{pref}.png`の縦軸を、すべて正の値の場合のみ対数目盛に変更（ラベルも追加）、`_indices`のコメントを日本語に修正。 |
| `tests/test_analyze_denshou.py` | 14081 | `test_build_denshou_table`での入力データをID順でないものに変更し、結果がID順にソートされていることの検証を追加。 |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - 実データ実行前後のCSV3つ（`denshou_36.csv`等）のハッシュが同じであることを確認しました。
  - テスト（`python -m pytest`）は全件（99件）合格しました。

### 実データでの実行前後のハッシュ
実行前:
```
Algorithm : SHA256
Hash      : A2323BD9B2CC27C75D21928EFD83AE5CF7791A7FAD749520854C7BFE6F4100A0
Path      : <プロジェクト>\output\denshou_36.csv

Algorithm : SHA256
Hash      : 9377FD05A9707ABCDBA8857C03C3CF944E916CA1A8A5C97685C490E425F999CC
Path      : <プロジェクト>\output\denshou_summary_36.csv

Algorithm : SHA256
Hash      : 30D38C07A1A053CF6D5806AF275963B5E9328CD2227E6343479A0F984F859C78
Path      : <プロジェクト>\output\disaster_groups_36.csv
```

実行後:
```
Algorithm : SHA256
Hash      : A2323BD9B2CC27C75D21928EFD83AE5CF7791A7FAD749520854C7BFE6F4100A0
Path      : <プロジェクト>\output\denshou_36.csv

Algorithm : SHA256
Hash      : 9377FD05A9707ABCDBA8857C03C3CF944E916CA1A8A5C97685C490E425F999CC
Path      : <プロジェクト>\output\denshou_summary_36.csv

Algorithm : SHA256
Hash      : 30D38C07A1A053CF6D5806AF275963B5E9328CD2227E6343479A0F984F859C78
Path      : <プロジェクト>\output\disaster_groups_36.csv
```

### コマンド実行結果
```
<プロジェクト>> python src/analyze_denshou.py --pref 36
対象の県名: 徳島県（36）
碑の数: 71基
区分: 差あり 62／災害前の建立 0／対象外（建立年不明） 9／不明（災害名に年なし） 0（計 71）
建立までの年数（差あり 62）: 中央値 39.0年（最小 0年、最大 150年）
同じ災害の碑群: 昭和南海地震(1946年) 28基／安政南海地震(1854年) 20基／安政東海地震(1854年) 6基／昭和29年台風12号(ジューン台風)(1954年) 3基／昭和51年台風17号(1976年) 3基
出力:
  output/denshou_36.csv
  output/denshou_summary_36.csv
  output/disaster_groups_36.csv
  output/fig/denshou_years_36.png
  output/fig/disaster_groups_36.png
```

```
<プロジェクト>> python src/make_map.py --pref 36
対象の県名: 徳島県
碑の数: 71
主な災害種別ごとの数（津波）: 49
主な災害種別ごとの数（洪水）: 1
主な災害種別ごとの数（高潮）: 10
主な災害種別ごとの数（土砂災害）: 8
主な災害種別ごとの数（地震）: 2
主な災害種別ごとの数（その他）: 1
移転碑の数: 2
比較地点なしの碑 ID: 36383-002
出力ファイル: map_36.html
```

```
<プロジェクト>> python src/build_site.py --pref 36
対象の県名: 徳島県
データ取得日: 2026-09-24
碑の数: 71
作成したファイル:
  docs\map_36.html
  docs\fig\box_elevation_36.png
  docs\fig\box_slope_36.png
  docs\fig\box_river_dist_36.png
  docs\fig\box_river_height_36.png
  docs\fig\box_coast_dist_36.png
  docs\fig\bar_landform_36.png
  docs\fig\denshou_years_36.png
  docs\fig\disaster_groups_36.png
  docs\data\summary_36.csv
  docs\data\landform_36.csv
  docs\data\relocated_36.csv
  docs\data\update_history_36.csv
  docs\data\denshou_36.csv
  docs\data\denshou_summary_36.csv
  docs\data\disaster_groups_36.csv
  docs\.nojekyll
  docs\index.html
公開前チェック：問題なし
```

## 残った課題・気になる点
特になし

## 確認したいこと（あれば）
特になし

