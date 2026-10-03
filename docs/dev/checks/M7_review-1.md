# ソース確認 M7（1回目）　確認日：2026-10-03

- 確認範囲：作業中コミット 80212ec（M7-01 依頼前）からの差分（新規 src/analyze_denshou.py、tests/test_analyze_denshou.py、output/ の生成物5つ）＋影響範囲（import している summarize.set_jp_font・get_valid_series・calc_stats、make_map.main_type。これらは変更なし）
- 完了報告：M7-01_report.md。各ファイルのバイト数は報告と一致（消失なし）
- 実データの出力：まとめ表示・denshou_summary_36.csv・disaster_groups_36.csv・denshou_36.csv の個別行（36201-001、36387-003、36388-012、36403-001）は、指示書の答え（Claude の別計算）とすべて一致。グラフ2枚は開けて内容も妥当
- Claude の別環境（Linux の Python）での実行：`python -m pytest -q tests/test_analyze_denshou.py`（引数付き）で 8 passed
- 指示外のファイル：ルート直下の tmp_out.txt（実行結果の記録。UTF-16）。報告の一覧になし → _to_delete/M7-01_work/ へ移動（Claude）

## 変異テスト（わざと壊して、テストが気づくか）
| 変異（src/analyze_denshou.py の main の中だけを壊す） | 結果 |
|---|---|
| 集計表の年数に「災害前の建立」も含める | 見逃し（8 passed） |
| 碑群の並びを「碑の数の少ない順」にする | 見逃し |
| 「複数の災害（最も古い年を使用）」の注記を付けない | 見逃し |
| 年の数を「重複しない年の数」で数える | 見逃し |
| 発生年を「最も新しい年」にする | 見逃し |
| 集計表の「災害前の建立」の件数を常に0にする | 見逃し |
| 碑群の標高で「取得不可」の碑も使う（除外数0） | 見逃し |

原因：区分・注記・集計・碑群の計算がすべて main の中にあり、テスト c・d・e・j はその計算を**テストの中で書き直して**確かめている（本体の main の計算を通っていない）。テスト f は出力ファイルが「あること」とバイト一致だけを見ていて、中身の値を見ていない。

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | tests/test_analyze_denshou.py 全体、src/analyze_denshou.py main | テストが本体の計算を確かめていない（上の変異7件をすべて見逃す）。指示書「2. 読み取りのルール（関数に分け…）」「j. 読み込み・計算の関数だけを使う」に対し、計算が main に入ったままで、テストが同じ処理を書き直している | M7-02_fix |
| 2 | 軽微 | src/analyze_denshou.py 「年の数」の行 | 英語まじりの作業メモのようなコメント（"as per general requirement, wait instruction says …"）が残っている。コメントは日本語で簡潔に | M7-02_fix |
| 3 | 軽微 | tests/test_analyze_denshou.py test_real_data | 本物のデータを `Path("data/processed")`（実行時のフォルダ基準）で探すため、別のフォルダから pytest を実行すると黙って skip になる（M3_review-7 No.1 と同じ） | M7-02_fix |
| 4 | 軽微 | ルート直下 tmp_out.txt | 指示外の作業ファイルを作り、報告の一覧にも書いていない | Claude が移動済み。M7-02_fix で注意 |
| 5 | 軽微（容認） | output/fig/disaster_groups_36.png | 標高 115m・海岸から 12km などの碑があるため、箱が下に潰れて碑群の違いが読み取りにくい。指示書どおりの作りなので今回は容認し、公開ページに載せる M7-03 で表示の仕方を決める | M7-03 で検討 |

## 判定：**不合格**（修正1回目へ。中1件）
