# ソース確認 M7（4回目）　確認日：2026-10-03

- 確認範囲：作業中コミット f61003a（M7-03 作業中）からの差分（src/make_map.py、src/analyze_denshou.py、tests/test_make_map.py、tests/test_analyze_denshou.py）＋生成物（output/map_36.html、docs/map_36.html）
- 完了報告：M7-04_report.md。各ファイルのバイト数は報告と一致（消失なし）
- **報告の実行結果とコードの表示文の照合：一致**（analyze_denshou・make_map・build_site の3つとも、見出しの言葉がコードの print 文どおり。make_map の件数も 津波49／高潮1／洪水10／土砂災害8／地震2／その他1 で正しい）
- 地図の文言：36201-001「7年」、36387-003「59年（最も古い災害から）」、36203-001「—（建立年不明）」、36387-001「同じ年」で修正前と同じ。71基すべてに行あり。docs/map_36.html は output と同一。CSV は git 上で不変
- Claude の別環境での実行：`python -m pytest -q tests/test_analyze_denshou.py tests/test_make_map.py tests/test_build_site.py tests/test_update.py` で 38 passed・1 skipped

## 変異テスト
| 変異 | 結果 |
|---|---|
| 1 差0で「0年」と出す | 検出 |
| 2 「（最も古い災害から）」を付けない | 検出 |
| 3 年の数1でも付ける | 検出 |
| 4 対象外の碑に文言を出さない | 検出 |
| 5 対数目盛にしない | 検出 |
| 6 0を含む図でも対数 | 検出 |
| 7 （追加）災害前の文言を変える | 検出 |
| 8 （追加）地図に文言を渡さない | 検出 |
| 9 （追加）対数のときラベルに「対数目盛」を付けない | 検出 |

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | ルート直下 pytest_out.txt | 指示書で禁止した作業ファイルを作り、報告にも書いていない（M7-01 の tmp_out.txt と同じ）。ユーザー名入りのパスは含まれていない → Claude が _to_delete/M7-04_work/ へ移動 | 移動済み。M7-05 で公開前チェックがルート直下・UTF-16 のファイルも調べるようにする |
| 2 | 軽微 | docs/dev/reports/M7-04_report.md | 報告の書式が _template.md と違う（ファイル一覧が表でない等）。内容は足りている | 次回の報告で注意 |
| 3 | 軽微（容認） | src/analyze_denshou.py 8〜9行 | 指示外の `matplotlib.use('Agg')`（画面なしでグラフを作る設定）を追加。出力・動作に影響なし | 対応不要 |

## 判定：**合格**（修正2回目で合格。重大・中 0件）
