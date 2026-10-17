# ソース確認 M16（1回目・M16-01）　確認日：2026-10-16

- 確認範囲：「M16 作業中」（ec4f21d）からの新しいファイル src/run_region_batch.py（13,394バイト）・tests/test_run_region_batch.py（16,941バイト）・docs/dev/reports/M16-01_report.md、実行でできた output/region_batch_log.csv。影響範囲として src/add_landform_region.py（キャッシュの置き場所 data/cache/landform/<z>/<x>/<y>.geojson）と src/update.py の default_runner（subprocess.run、cwd＝プロジェクト）
- 報告の実行結果とコードの表示文の照合：一致（対象・データの確認・--check-only・[i/N] の開始／完了の行・まとめ・合計の文言が print 文と同じ。件数は既知の答え 山口 182/0/4/0・徳島 412/0/8/0・合計 594/0/12/0・タイル 0枚と一致）
- pytest 249 ＝ 239 ＋ 新しいテスト関数10（test_ で始まる関数を数えて検算）。(a)〜(j) の10項目に1対1で対応
- 地域版4ファイルの sha256 先頭16桁は M15 のときと同じ（35 e81a703913c1577d／36 2944953791000844／points_35 b6412c46aa80155f／points_36 36551d2a61e45bfc）。git diff は空、新しいファイルは「??」の4つだけ。新しいファイルの \r は0
- 既存の段階（標高・河川・ハザード・詳細版の地形分類）は呼ばれない（runner に渡すのは add_landform_region.py だけ）
- Ctrl+C：subprocess.run は子プロセスを止めたうえで KeyboardInterrupt を上げ直すため、runner の呼び出しを囲む try で受けられる（推測を含まない。Python の標準の動き）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | docs/dev/reports/M16-01_report.md の表 | output/region_batch_log.csv のバイト数を 718 と記載。実際は 721（BOM の3バイト分の差と推測）。ログは .gitignore の対象で、動作に影響なし | 記録のみ |
| 2 | 軽微 | src/run_region_batch.py 230行 | 県ごとの開始の行の「碑 n基・比較地点 m点」が3桁区切りでない（指示書は開始の行の区切りを指定していない。1県で1,000点以上の県は全国の実行で見た目が少し不揃いになるだけ） | 記録のみ（M16-02 で触るなら直す） |

## 判定：合格（M16-01、修正0回）
