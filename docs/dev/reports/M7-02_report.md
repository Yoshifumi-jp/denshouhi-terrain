# 完了報告 M7-02

## 変更したファイル
| ファイル | 変更内容 | バイト数 |
|---|---|---|
| `src/analyze_denshou.py` | `main` の中の計算処理を関数（`load_inputs`, `build_denshou_table`, `build_summary`, `build_groups`）に分割 | 15,814 |
| `tests/test_analyze_denshou.py` | 本体の計算関数を直接テストするように書き換え。不具合の検出も確認 | 14,009 |
| `output/denshou_36.csv` | コマンド実行による再生成（ハッシュ一致） | 11,814 |
| `output/denshou_summary_36.csv` | コマンド実行による再生成（ハッシュ一致） | 482 |
| `output/disaster_groups_36.csv` | コマンド実行による再生成（ハッシュ一致） | 2,505 |
| `output/fig/denshou_years_36.png` | コマンド実行による再生成（ハッシュ一致） | 30,463 |
| `output/fig/disaster_groups_36.png` | コマンド実行による再生成（ハッシュ一致） | 54,218 |

## 自己チェック結果
- 問題タブのエラー件数：0件
- 起動・実行時のエラー：なし
- 完成の条件の確認：
  - テストが本体の関数を呼んで確かめていること。
  - 実データの出力ファイル5つのハッシュが修正前とすべて一致していること。
  - `python -m pytest` が全件合格することを確認。
  - 各ファイルが空になっておらず、変更前にも戻っていないことを確認（上記にバイト数を記載）。

### テストが気づくべき誤りの確認結果

下の7通りの誤りを1つずつ `src/analyze_denshou.py` に入れ、`pytest tests/test_analyze_denshou.py` が失敗することを確認した後、本体を元に戻しました。

| No | 誤り | 確認結果 |
|---|---|---|
| 1 | 集計表の年数（中央値など）に「災害前の建立」も含める | `test_build_summary` が `assert np.float64(7.0) == 33.0` 等で失敗した |
| 2 | 碑群の並びを碑の数の少ない順にする | `test_build_groups` が並び順の違いで失敗した |
| 3 | 「複数の災害（最も古い年を使用）」の注記を付けない | `test_build_denshou_table` が注記なしで失敗した |
| 4 | 年の数を重複しない年の数で数える（同じ1854年が2回なら1にする） | `test_real_data` が年の数>=2の件数が合わず失敗した |
| 5 | 発生年を最も新しい年にする | `test_build_denshou_table` が発生年 1912 != 1854 で失敗した |
| 6 | 集計表の「災害前の建立」の件数を常に0にする | `test_build_summary` が災害前の件数 0 != 1 で失敗した |
| 7 | 碑群の標高で「取得不可」の碑も使う（除外数を0にする） | `test_build_groups` が除外数 0 != 1 で失敗した |

### ハッシュ一致確認
出力5ファイルについて、変更前後でハッシュが完全に一致することを確認しました。

```
Algorithm       Hash                                                                   Path                            
---------       ----                                                                   ----                            
SHA256          A2323BD9B2CC27C75D21928EFD83AE5CF7791A7FAD749520854C7BFE6F4100A0       <プロジェクト>\output\denshou_36.csv
SHA256          9377FD05A9707ABCDBA8857C03C3CF944E916CA1A8A5C97685C490E425F999CC       <プロジェクト>\output\denshou_summary_36.csv
SHA256          30D38C07A1A053CF6D5806AF275963B5E9328CD2227E6343479A0F984F859C78       <プロジェクト>\output\disaster_groups_36.csv
SHA256          3B7655366644C9730EBC10FF53653A4D6D650BC3E918F08A5E82404BA2C35949       <プロジェクト>\output\fig\denshou_years_36.png
SHA256          26FB0E70BAF770D7C9FB304FBE2AA422AF61C61486D221065A0D39E9E9A718C6       <プロジェクト>\output\fig\disaster_groups_36.png
```

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
collected 98 items

tests\test_add_elevation.py ...........                                  [ 11%]
tests\test_add_landform.py ......                                        [ 17%]
tests\test_add_river_coast.py ..................                         [ 35%]
tests\test_analyze_denshou.py .........                                  [ 44%]
tests\test_build_site.py .....                                           [ 50%]
tests\test_check_public.py ....                                          [ 54%]
tests\test_load_monuments.py ..........                                  [ 64%]
tests\test_make_comparison_points.py .........                           [ 73%]
tests\test_make_map.py .........                                         [ 82%]
tests\test_summarize.py .....                                            [ 87%]
tests\test_update.py ............                                        [100%]

============================= 98 passed in 6.33s ==============================
```

## 残った課題・気になる点
特になし。

## 確認したいこと（あれば）
特になし。
