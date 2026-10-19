# 完了報告 M20-01

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| `src/make_map.py` | `load_data` での人工地形 CSV（`landform_artificial_{pref}.csv`）の左結合、`build_popup_html` での「人工地形：」行の追加、凡例の出典・注意事項への2行追加、`main` のまとめ表示への「人工地形のある碑」の追加 | 25,153 bytes |
| `src/build_site.py` | `landform_artificial_{pref}.csv` の `docs/data/` へのコピー、ダウンロード一覧への「地形分類（人工地形）の集計」リンク追加、出典・ご利用上の注意への追記、公開前チェック対象への追加 | 26,624 bytes |
| `tests/test_make_map.py` | 人工地形のポップアップ表示に関するテスト3件（`test_popup_artificial_line`、`test_popup_artificial_absent`、`test_popup_artificial_escape`）を追加 | 25,845 bytes |
| `tests/test_build_site.py` | 県別ページの人工地形リンクに関するテスト1件（`test_build_site_artificial_link`）を追加 | 27,151 bytes |
| `output/map_36.html` | `make_map.py --pref 36` による再生成 | 214,929 bytes |
| `output/map_13.html` | `make_map.py --pref 13` による再生成 | 174,274 bytes |
| `output/map_41.html` | `make_map.py --pref 41` による再生成 | 154,236 bytes |
| `docs/pref_36.html` | `build_site.py --pref 36` による再生成 | 11,733 bytes |
| `docs/map_36.html` | `build_site.py --pref 36` によるコピー更新 | 214,929 bytes |
| `docs/data/landform_artificial_36.csv` | `build_site.py --pref 36` による新規コピー | 5,602 bytes |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：すべて一致を確認済

### 1. pytest の実行結果
`.\.venv\Scripts\python.exe -m pytest -q`
```text
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 67%]
........................................................................ [ 90%]
..............................                                           [100%]
318 passed in 407.39s (0:06:47)
```

### 2. `make_map.py` の実行結果（36・13・41）

`.\.venv\Scripts\python.exe src\make_map.py --pref 36`
```text
対象の県名: 徳島県
碑の数: 71
主な種別ごとの件数（津波）: 49
主な種別ごとの件数（高潮）: 1
主な種別ごとの件数（洪水）: 10
主な種別ごとの件数（土砂災害）: 8
主な種別ごとの件数（地震）: 2
主な種別ごとの件数（その他）: 1
移転碑の数: 2
地形分類を地域版で補った碑: 11
地形分類のデータなし（地域版でも補えない）: 0
人工地形のある碑: 12
比較地点なしの碑の ID: 36383-002
ハザードの重ね表示: 洪水（想定最大規模）、津波、高潮、土砂災害警戒区域
出力ファイル名: map_36.html
```

`.\.venv\Scripts\python.exe src\make_map.py --pref 13`
```text
対象の県名: 東京都
碑の数: 56
主な種別ごとの件数（高潮）: 6
主な種別ごとの件数（洪水）: 5
主な種別ごとの件数（土砂災害）: 2
主な種別ごとの件数（火山災害）: 2
主な種別ごとの件数（地震）: 40
主な種別ごとの件数（その他）: 1
移転碑の数: 7
地形分類を地域版で補った碑: 4
地形分類のデータなし（地域版でも補えない）: 0
人工地形のある碑: 36
比較地点なしの碑の ID: なし
ハザードの重ね表示: 洪水（想定最大規模）、津波、高潮、土砂災害警戒区域
出力ファイル名: map_13.html
```

`.\.venv\Scripts\python.exe src\make_map.py --pref 41`
```text
対象の県名: 佐賀県
碑の数: 52
主な種別ごとの件数（高潮）: 9
主な種別ごとの件数（洪水）: 33
主な種別ごとの件数（土砂災害）: 7
主な種別ごとの件数（地震）: 1
主な種別ごとの件数（その他）: 2
移転碑の数: 1
地形分類を地域版で補った碑: 17
地形分類のデータなし（地域版でも補えない）: 0
人工地形のある碑: 7
比較地点なしの碑の ID: なし
ハザードの重ね表示: 洪水（想定最大規模）、津波、高潮、土砂災害警戒区域
出力ファイル名: map_41.html
```

### 3. `build_site.py` の実行結果（36）

`.\.venv\Scripts\python.exe src\build_site.py --pref 36`
```text
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
  docs\data\landform_region_36.csv
  docs\data\landform_artificial_36.csv
  docs\data\relocated_36.csv
  docs\data\update_history_36.csv
  docs\data\denshou_36.csv
  docs\data\denshou_summary_36.csv
  docs\data\disaster_groups_36.csv
  docs\data\hazard_summary_36.csv
  docs\.nojekyll
  docs\pref_36.html
公開前チェック：問題なし
```

### 4. 個別の例7件の確認（`map_XX.html` から抜き出し）
| ID | 碑名 | 「地形分類：」の行 | 「人工地形：」の行 |
|---|---|---|---|
| 36203-002 | 金磯弁財天碑 | `<li>地形分類：氾濫平野・海岸平野</li>` | `<li>人工地形：盛土地・埋立地</li>` |
| 36401-001 | 敬震碑 | `<li>地形分類：旧水部</li>` | `<li>人工地形：盛土地・埋立地</li>` |
| 36201-001 | 沖洲蛭子神社百度石 | `<li>地形分類：砂州・砂丘</li>` | 行なし |
| 36207-001 | 災害復旧記念碑 | `<li>地形分類：山地（地域版）</li>` | 行なし |
| 13101-001 | 工部大学校阯碑 | `<li>地形分類：氾濫平野・海岸平野</li>` | `<li>人工地形：切土地</li>` |
| 13108-001 | 波除碑 | `<li>地形分類：旧水部</li>` | `<li>人工地形：盛土地・埋立地</li>` |
| 41425-001 | 大正三年高潮災害紀念碑・潮塞(しおどめ) | `<li>地形分類：旧水部</li>` | `<li>人工地形：干拓地</li>` |

### 5. その他の確認事項
- 地図ファイル内の `人工地形：` の出現数：`output/map_36.html`＝12、`output/map_13.html`＝36、`output/map_41.html`＝7
- 作成・変更したすべてのファイルの改行コード：LF（CRLF なし）
- `docs/data/landform_artificial_36.csv` と `output/landform_artificial_36.csv`：バイト単位で完全一致（5,602 bytes）

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
なし

