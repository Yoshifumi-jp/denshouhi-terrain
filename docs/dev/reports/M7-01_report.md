# 完了報告 M7-01

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| `src/analyze_denshou.py` | 新規作成（伝承碑の災害名から年を取り出し建立年と比較する集計コマンド） | 15,338 |
| `tests/test_analyze_denshou.py` | 新規作成（`analyze_denshou.py` の自動テスト） | 14,975 |
| `output/denshou_36.csv` | コマンド実行による生成 | 11,814 |
| `output/denshou_summary_36.csv` | コマンド実行による生成 | 482 |
| `output/disaster_groups_36.csv` | コマンド実行による生成 | 2,505 |
| `output/fig/denshou_years_36.png` | コマンド実行による生成 | 30,463 |
| `output/fig/disaster_groups_36.png` | コマンド実行による生成 | 54,218 |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - `python src/analyze_denshou.py --pref 36` がエラーなく終わり、まとめ表示の数字が指示書の答えと一致することを確認。
  - 出力ファイル5つが生成され、CSV が文字化けしないことを確認。
  - `python -m pytest` で既存のテストも含め全件合格することを確認。
  - VS Code の「問題」タブでエラーが0件であることを確認。
  - 各ファイルが空になっておらず、変更前にも戻っていないことを確認（上記にバイト数を記載）。

### コマンド実行結果

```
伝承内容の分析：徳島県（36）
碑の数：71基
区分：差あり 62／災害前の建立 0／対象外（建立年不明） 9／不明（災害名に年なし） 0（合計 71）
建立までの年数（差あり 62基）：中央値 39.0年（最小 0年、最大 150年）
碑の数が多い災害：昭和南海地震(1946) 28基／安政南海地震(1854) 20基／安政東海地震(1854) 6基／昭和29年台風12号(ジューン台風)(1954) 3基／昭和51年台風17号(1976) 3基
出力：
  output/denshou_36.csv
  output/denshou_summary_36.csv
  output/disaster_groups_36.csv
  output/fig/denshou_years_36.png
  output/fig/disaster_groups_36.png
```

### テスト実行結果

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: <プロジェクト>
collected 97 items

tests\test_add_elevation.py ...........                                  [ 11%]
tests\test_add_landform.py ......                                        [ 17%]
tests\test_add_river_coast.py ..................                         [ 36%]
tests\test_analyze_denshou.py ........                                   [ 44%]
tests\test_build_site.py .....                                           [ 49%]
tests\test_check_public.py ....                                          [ 53%]
tests\test_load_monuments.py ..........                                  [ 63%]
tests\test_make_comparison_points.py .........                           [ 73%]
tests\test_make_map.py .........                                         [ 82%]
tests\test_summarize.py .....                                            [ 87%]
tests\test_update.py ............                                        [100%]

============================= 97 passed in 6.78s ==============================
```

## 残った課題・気になる点
特になし。

## 確認したいこと（あれば）
特になし。
