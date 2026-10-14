# 完了報告 M12-06

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| src/count_missing.py | 新規作成。県別の「取得不可」「データなし」の件数一覧を集計するスクリプト（`count_missing`, `main`） | 14612 |
| tests/test_count_missing.py | 新規作成。小規模データ集計・ファイル欠落時の除外・main出力・47県実データ全国合計照合の各テスト関数（4件） | 13858 |
| tests/test_run_batch.py | 179行および229行のコメント `# 03 is completed` を `# 03 は完了済みにする` に変更 | 15485 |
| output/missing_counts.csv | `python src/count_missing.py` の実行により生成された全国47県＋全国合計の集計結果CSV | 3659 |
| docs/dev/reports/M12-06_report.md | 本完了報告書 | 6882 |

## 自己チェック結果
- 問題タブのエラー件数：0件（`pyflakes` で確認）
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python -m pytest` 全件合格（182件＝178件＋新しいテスト4件）
  - `python -m pyflakes src tests` 指摘0件
  - `git status --short` で、変更が `tests/test_run_batch.py`、新しいファイルが `src/count_missing.py`・`tests/test_count_missing.py`・`output/missing_counts.csv`・`docs/dev/reports/M12-06_report.md` のみ
  - `python src/count_missing.py` の表示について、後述の「確認したいこと」の1箇所（長崎県 vs 熊本県）を除き、指示書の表示と完全一致

## 残った課題・気になる点
なし

## 確認したいこと（あれば）
指示書53行目の表示例において、
`地形分類のデータなしの割合が高い県（碑）：岩手県 91%、栃木県 89%、奈良県 87%、北海道 78%、熊本県 69%`
と記載されていますが、指示書58行目のルール「割合が高い県は碑の割合の大きい順に5県（同じ割合なら県コード順）」に従って実データを集計すると、上位県は以下のようになります：
- 1位: 岩手県（03） 149 / 163 = 91.4% → 91%
- 2位: 栃木県（09） 42 / 47 = 89.4% → 89%
- 3位: 奈良県（29） 27 / 31 = 87.1% → 87%
- 4位: 北海道（01） 42 / 54 = 77.8% → 78%
- 5位: 長崎県（42） 34 / 49 = 69.4% → 69%
- 6位: 山口県（35） 21 / 31 = 67.7% → 68%
- 7位: 熊本県（43） 55 / 82 = 67.1% → 67%

指示書79行目の表でも熊本県は `地形分類データなし 55（0.671）` と正確に記載されており、5位の長崎県（69.4% → 69%）の割合「69%」に対して県名が「熊本県」と転記されたものと推測されます。
実装（`src/count_missing.py`）では指示書58行目のルール通りに「割合の大きい順に5県」としてソート・抽出しているため、画面表示は `長崎県 69%` となっています。
指示書90行目の完成条件「上の『表示』と1字も違わない」に対して、この1箇所（長崎県 vs 熊本県）のみ差分が生じておりますのでご確認ください。

## 報告に貼るもの

### 1. `python src/count_missing.py` の出力（全行）
```text
県別の「取得不可」「データなし」の件数一覧
対象：47都道府県（ファイルが足りない県：なし）
碑の合計：2,481基（M9 の全国件数 2,481基と一致）
比較地点の合計：12,395点
標高・傾斜の取得不可：碑 2／比較地点 62
ハザードの取得不可：碑 0／比較地点 0
地形分類のデータなし：碑 929（37.4%）／比較地点 4,890（39.5%）
河川の標高の取得不可：碑 5／比較地点 16
（参考）河川まで1000m超で対象外：碑 158／比較地点 990
（参考）海のない県で海岸は対象外：碑 418／比較地点 2,090
通信エラー：碑 0／比較地点 0
地形分類のデータなしの割合が高い県（碑）：岩手県 91%、栃木県 89%、奈良県 87%、北海道 78%、長崎県 69%
出力：output/missing_counts.csv
```

### 2. `python -c "import pandas as pd;d=pd.read_csv('output/missing_counts.csv',dtype={'県コード':str});print(len(d));print(d[d['県コード'].isin(['03','35','全国'])].to_string())"` の出力
```text
48
   県コード   県名   碑_数  比較地点_数  標高傾斜_取得不可_碑  標高傾斜_取得不可_比較地点  ハザード_取得不可_碑  ハザード_取得不可_比較地点  地形分類_データなし_碑  地形分類_データなし_碑_割合  地形分類_データなし_比較地点  地形分類_データなし_比較地点_割合  河川標高_取得不可_碑  河川標高_取得不可_比較地点  河川_1000m超_碑  河川_1000m超_比較地点  海岸_対象外_碑  海岸_対象外_比較地点  通信エラー_碑  通信エラー_比較地点
2    03  岩手県   163     815            0               9            0               0           149            0.914              754               0.925            0               0           38             192         0            0        0           0
34   35  山口県    31     155            1               1            0               0            21            0.677              104               0.671            0               1            2              12         0            0        0           0
47   全国   合計  2481   12395            2              62            0               0           929            0.374             4890               0.395            5              16          158             990       418         2090        0           0
```

### 3. `python -m pytest` の最後の数行
```text
tests\test_summarize.py .....                                            [ 89%]
tests\test_summarize_hazard.py .......                                   [ 92%]
tests\test_update.py .............                                       [100%]

======================= 182 passed in 295.65s (0:04:55) =======================
```

### 4. `python -m pyflakes src tests` の出力
```text

```
(出力なし)

### 5. `git status --short` の出力
```text
 M tests/test_run_batch.py
?? docs/dev/reports/M12-06_report.md
?? output/missing_counts.csv
?? src/count_missing.py
?? tests/test_count_missing.py
```

### 6. 改行コードの確認：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/count_missing.py','tests/test_count_missing.py','tests/test_run_batch.py']]"` の出力
```text
src/count_missing.py False
tests/test_count_missing.py False
tests/test_run_batch.py False
```

### 7. 作成・変更したファイルとバイト数の一覧
- src/count_missing.py: 14612 bytes
- tests/test_count_missing.py: 13858 bytes
- tests/test_run_batch.py: 15485 bytes
- output/missing_counts.csv: 3659 bytes
- docs/dev/reports/M12-06_report.md: 6882 bytes
