# ソース確認 M11（2回目・M11-02_fix）　確認日：2026-10-07

- 確認範囲：作業中コミット 7360035「M11-01 作業中」からの差分（src/run_batch.py、tests/test_run_batch.py、docs/dev/reports/M11-01_report.md）
- ファイルのサイズ：報告のバイト数（run_batch.py 11300・test_run_batch.py 13921）は実ファイルと一致
- 報告の実行結果とコードの表示文の照合：一致
  - `--check-only` の表示は print 文・既知の答えと一致
  - `update.py --pref 36 --dry-run` は「古いデータと新しいデータが同じファイルです」。update.py のコード（update_history_36.csv の完了行が今回のデータと同じ）どおり。M11_review-1 No.1 解消
  - pytest 171件＝170＋test_all_pref 1。test_run_batch 10件すべて PASSED（test_real_data も skip されず実行）

| No | 前回の指摘 | 確認結果 |
|---|---|---|
| 1 | 報告の dry-run 出力の食い違い | 解消（コマンド付きで実際の出力が貼られている） |
| 2 | `--pref all` で停止 | 解消。`sorted(PREFECTURES.keys())` に展開。test_all_pref で47行・「47県」を確認 |
| 3 | 実データテストが空 | 解消。--check-only の4行を照合し、output/・data/ のファイルの更新時刻が変わらないことも確認している |
| 4 | PROJECT_ROOT の書き換え | 解消。project_root を引数で渡し、相対パスも自前の関数。テストの update.PROJECT_ROOT 直接代入なし |
| 5 | 完了の判定 | 解消（`== '完了'`） |

## 新しい指摘
| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 軽微 | docs/dev/reports/M11-01_report.md | 指示書の範囲外のファイルを変更（rootdir のユーザー名入りパスを伏せる。内容は正しい）。その際ファイル全体の改行が CRLF に変わっていた | Claude が LF に戻した（差分は1行だけ） |
| 2 | 軽微 | docs/dev/reports/M11-02_report.md 50・52・74行 | pytest 出力にユーザー名入りのパス（test_check_public が次回失敗する原因） | Claude が `<プロジェクト>` に伏せた |

※ AGENTS.md 28行に「絶対パスは <プロジェクト> に置き換える」の決まりがあるが守られていない。次の指示書の「報告に貼るもの」に、この決まりを名指しで書く

## 判定：M11-02 は報告確認として合格（重大・中 0件）。M11 の合否は本番の一括実行のあとの確認シート M11_check-1 で判定
