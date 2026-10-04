# ソース確認 M8（1回目）　確認日：2026-10-04

- 確認範囲：66c4db7（M7 合格）からの差分＋影響範囲（src/add_hazard.py、src/hazard_layers.py、tests/test_add_hazard.py、src/check_public.py、tests/test_check_public.py、requirements.txt）
- ファイルの消失：なし（報告のバイト数と一致）
- 報告の実行結果とコードの表示文の照合：一致（まとめ表示の見出し・項目名・並び順は add_hazard.py の print 文どおり）
- 実データの照合：data/processed/hazard_36.csv の碑71基を、Claude が内蔵ブラウザで別に判定した結果（洪水・津波・高潮の浸水深、土砂の区分・現象）と1基ずつ照合 → **71基すべて一致**。比較地点は「近い色」5件（すべて急傾斜地の崩壊の境界）
- 公開前チェック：報告書の pytest 結果の rootdir 行にユーザー名入りの絶対パスがあった（AGENTS.md「個人情報の扱い」違反）→ Claude が「<プロジェクト>」に置き換え、check_public.py「問題なし」を確認

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | src/add_hazard.py 17〜18行 | `from src.prefectures import …` を try/except なしで書いている。指示書のコマンド `python src/add_hazard.py`（スクリプトとして実行）では、実行フォルダがプロジェクトのルートでも `src` を import できず止まる（Claude の環境で再現：sys.path の先頭が src/ になり "No module named 'src'"）。他のスクリプト（add_landform.py など）は try/except で両方に対応している。M8-03 以降で update.py から子プロセスとして呼ぶと失敗するおそれ | M8-02_fix |
| 2 | 中 | src/add_hazard.py 209行 | 近い色の記録で、洪水・津波・高潮はキー（flood= など）を書いている。指示書 5-1 は「キーではなく現象・災害の名前」（洪水=、津波=、高潮=） | M8-02_fix |
| 3 | 中 | tests/test_add_hazard.py | 指示書のテストの不足：f（列の並び順、行の順、utf-8-sig、近い色の記録・取得日の書き方、2回実行で取得日以外が同じ）を確かめていない。test_main_execution は偽タイルの色を塗った画素（203,249）に地点が当たっておらず、近い色・区域内の判定が出力に出ていない／e（.none ができること、取得不可でキャッシュができないこと）を直接確かめていない／g（--pref 48、比較地点の入力がないときの案内）がない／i（個別7基の照合、浸水深の区分ごとの件数の一部）がない／j（data/processed の中身が変わらないこと）がない。No.2 の誤りもテストで見つからなかった | M8-02_fix |
| 4 | 軽微 | docs/dev/reports/M8-01_report.md | 実行結果の絶対パスを伏せていなかった（Claude が修正済み） | M8-02_fix の完了後の注意として再掲 |
| 5 | 軽微 | src/add_hazard.py 42〜43行 | lonlat_to_pixel の 0〜255 への丸め込みは指示外だが、計算上 0〜255 に収まるため結果は変わらない | 対応不要（容認） |

## 判定：不合格（修正1回目へ。M8-02_fix）
