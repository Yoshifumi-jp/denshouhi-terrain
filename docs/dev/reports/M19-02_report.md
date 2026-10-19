# 完了報告 M19-02

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| `src/summarize_artificial.py` | 新規作成：地形分類（人工地形）の県別・全国の集計表（「災害種別×人工地形」および「自然地形×人工地形」）を作成・出力するプログラム（改行 LF） | 17,562 |
| `tests/test_summarize_artificial.py` | 新規作成：`src/summarize_artificial.py` の単体テスト（(a)〜(h)）および実データ照合テスト（(i)）全9件（改行 LF） | 36,081 |
| `output/landform_artificial_01.csv` 〜 `output/landform_artificial_47.csv`（47ファイル） | 新規生成：47都道府県の県別「災害種別×人工地形」集計表（UTF-8 BOM 付き、改行 LF） | 262,446（47ファイル合計） |
| `output/landform_artificial_all.csv` | 新規生成：全国の「災害種別×人工地形」集計表（UTF-8 BOM 付き、改行 LF） | 5,954 |
| `output/landform_artificial_cross_all.csv` | 新規生成：全国の「自然地形×人工地形」集計表（UTF-8 BOM 付き、改行 LF） | 13,130 |
| `docs/dev/reports/M19-02_report.md` | 新規作成：本完了報告書（改行 LF） | - |

※ `output/landform_artificial_*.csv` 49ファイルの合計バイト数：281,530 バイト（全ファイル非0バイトを確認済み）

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - 自動テスト：既存298件＋今回追加9件＝合計307件すべて合格（298＋9＝307）
  - 徳島（36）および全国（all）の画面表示が指示書の既知の答えと数字まで完全一致することを確認
  - 表1（`output/landform_artificial_all.csv`、注を除き96行）および表2（`output/landform_artificial_cross_all.csv`、自然地形18種、注を除き216行）の件数・割合・並び順が既知の答えと一致することを確認
  - 県別（徳島36、佐賀41）の件数・割合が既知の答えと一致することを確認
  - 既存ファイル（`data/processed/` の全ファイル、`output/` の既存ファイル、`src/`・`tests/` の既存ファイル）に変更がないことを確認
  - 新しく作成・出力した全ファイルに `\r`（CR）が含まれないことを確認（`49 0`）

### 6. pytest の実行結果
```text
........................................................................ [ 23%]
........................................................................ [ 46%]
........................................................................ [ 70%]
........................................................................ [ 93%]
...................                                                      [100%]
307 passed in 1132.00s (0:18:52)
```

### 7. `python src/summarize_artificial.py --pref 36` の実行結果（全文）
```text
地形分類（人工地形）の集計：徳島県（36）
碑：全碑 71基／移転碑を除く 69基　比較地点：全碑 349点／移転碑を除く 339点
人工地形を調べた地点（全碑）：碑 60基／比較地点 287点
数えていない地点（全碑）：範囲外 碑 11・比較地点 62、取得不可 碑 0・比較地点 0
人工地形ありの割合（全碑・全種別）：碑 0.200／比較地点 0.108
人工地形ごと（全碑・全種別。碑の件数・割合／比較地点の件数・割合）
  盛土地・埋立地：12・0.200／29・0.101
  切土地：0・0.000／2・0.007
  干拓地：0・0.000／0・0.000
  農耕平坦化地：0・0.000／0・0.000
  改変工事中：0・0.000／0・0.000
出力：
  output/landform_artificial_36.csv
```

### 8. `python src/summarize_artificial.py` の実行結果（全文）
```text
地形分類（人工地形）の集計：47都道府県
碑：全碑 2,481基／移転碑を除く 2,379基　比較地点：全碑 12,395点／移転碑を除く 11,885点
人工地形を調べた地点（全碑）：碑 1,552基／比較地点 7,505点
数えていない地点（全碑）：範囲外 碑 929・比較地点 4,890、取得不可 碑 0・比較地点 0
人工地形ありの割合（全碑・全種別）：碑 0.186／比較地点 0.159
人工地形ごと（全碑・全種別。碑の件数・割合／比較地点の件数・割合）
  盛土地・埋立地：199・0.128／732・0.098
  切土地：39・0.025／214・0.029
  干拓地：47・0.030／222・0.030
  農耕平坦化地：1・0.001／9・0.001
  改変工事中：2・0.001／16・0.002
出力：
  output/landform_artificial_XX.csv（47ファイル）
  output/landform_artificial_all.csv
  output/landform_artificial_cross_all.csv
```

### 9. 確認コマンドの出力
`python -c "import glob;fs=['src/summarize_artificial.py','tests/test_summarize_artificial.py']+sorted(glob.glob('output/landform_artificial_*.csv'));print(len(fs)-2, sum(open(f,'rb').read().count(b'\r') for f in fs))"` の出力：
```text
49 0
```

`git status --short` の出力：
```text
?? output/landform_artificial_01.csv
?? output/landform_artificial_02.csv
?? output/landform_artificial_03.csv
?? output/landform_artificial_04.csv
?? output/landform_artificial_05.csv
?? output/landform_artificial_06.csv
?? output/landform_artificial_07.csv
?? output/landform_artificial_08.csv
?? output/landform_artificial_09.csv
?? output/landform_artificial_10.csv
?? output/landform_artificial_11.csv
?? output/landform_artificial_12.csv
?? output/landform_artificial_13.csv
?? output/landform_artificial_14.csv
?? output/landform_artificial_15.csv
?? output/landform_artificial_16.csv
?? output/landform_artificial_17.csv
?? output/landform_artificial_18.csv
?? output/landform_artificial_19.csv
?? output/landform_artificial_20.csv
?? output/landform_artificial_21.csv
?? output/landform_artificial_22.csv
?? output/landform_artificial_23.csv
?? output/landform_artificial_24.csv
?? output/landform_artificial_25.csv
?? output/landform_artificial_26.csv
?? output/landform_artificial_27.csv
?? output/landform_artificial_28.csv
?? output/landform_artificial_29.csv
?? output/landform_artificial_30.csv
?? output/landform_artificial_31.csv
?? output/landform_artificial_32.csv
?? output/landform_artificial_33.csv
?? output/landform_artificial_34.csv
?? output/landform_artificial_35.csv
?? output/landform_artificial_36.csv
?? output/landform_artificial_37.csv
?? output/landform_artificial_38.csv
?? output/landform_artificial_39.csv
?? output/landform_artificial_40.csv
?? output/landform_artificial_41.csv
?? output/landform_artificial_42.csv
?? output/landform_artificial_43.csv
?? output/landform_artificial_44.csv
?? output/landform_artificial_45.csv
?? output/landform_artificial_46.csv
?? output/landform_artificial_47.csv
?? output/landform_artificial_all.csv
?? output/landform_artificial_cross_all.csv
?? src/summarize_artificial.py
?? tests/test_summarize_artificial.py
```

## 残った課題・気になる点
- なし（`count_missing.py`・`update.py`・`update_all.py` への組み込みは次の M19-03・M19-04 で実施予定）

## 確認したいこと（あれば）
- なし

