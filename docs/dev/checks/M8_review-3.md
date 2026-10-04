# ソース確認 M8（3回目）　確認日：2026-10-04

- 確認範囲：671cc9b（M8-03 依頼前）からの差分＋影響範囲（src/summarize_hazard.py、tests/test_summarize_hazard.py、tests/test_add_hazard.py、pytest.ini、output/hazard_summary_36.csv）
- ファイルの消失：なし（報告のバイト数と一致）
- 報告の実行結果とコードの表示文の照合：**一致**（まとめ表示の見出し・項目名・数値は summarize() の print 文の形どおり）。pytest「120 passed」はテスト関数の数（M8-02 時点の114件＋新規6件）と一致
- 出力の照合：output/hazard_summary_36.csv の56行すべてが、Claude が別の方法で計算した値と一致。注2行あり
- 公開前チェック：報告書・新規ファイルにユーザー名入りのパスなし
- 変異テスト（Claude が別環境で本体を1か所ずつわざと壊して実行）：8件中7件検出（ハザードの並び順の入れ替えだけ見逃し）。ただし実データのテスト i を外すと、「移転碑の比較地点を除かない」「比較地点を種別で絞らない」「注の2行目を消す」も見逃す＝偽データのテストが指示書 7章 d・e・g を確かめていない
- 本人の画面のターミナルの「1 failed, 113 passed」「114 passed」は 04:50 の実行の履歴（M8-03 前）

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 中 | tests/test_summarize_hazard.py test_d_e_f_g_main | 指示書 7章 d「比較地点も points の種別列で絞られる」、e「移転碑の比較地点（元の碑ID）が除かれる」、g「行の順・注2行」を偽データで確かめていない。実データのない環境（公開リポジトリを取得した人、全国展開時の他県）では誤りを見逃す | M8-04_fix |
| 2 | 軽微 | tests/test_add_hazard.py test_main_execution | No.4 で碑3を「取得不可」に変えたため、元にあった「すべて区域外の行（浸水深が空欄）」の確認がなくなった（加えるべきところを置き換えた） | M8-04_fix |
| 3 | 軽微 | tests/test_add_hazard.py test_summarize_dosha | 戻したコメントが M8-01 指示書 7章 d の文言と違う独自の文。③は指示書にない動き（指定済と指定予定の扱い）を書いている | M8-04_fix |
| 4 | 軽微 | tests/test_summarize_hazard.py test_i_real_data | 実データの場所が Path("data/processed")＝実行フォルダ基準（M7_review-1 と同じ指摘） | M8-04_fix |
| 5 | 軽微 | src/summarize_hazard.py | 関数の説明コメントがない。3m以上の区分を hazard_layers の凡例から取らず文字で直書き | M8-05（組み込み）でまとめて |

## 判定：**不合格**（修正2回目＝M8-04_fix へ。出力の値は正しいため、本体 src/summarize_hazard.py は変えない）
