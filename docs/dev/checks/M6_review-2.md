# ソース確認 M6（2回目）　確認日：2026-10-03

- 確認範囲：7f0e930（M6-01 作業中）からの差分（src/update.py、tests/test_update.py）
- ファイル：報告（08:34）の約2分後 08:35:59 に2ファイルが同時に更新されたが、中身・バイト数（14,712B／14,661B）は報告どおり。消失なし
- Claude の確認：別環境で test_update.py 11 passed。変異テスト10件中8件を検出（前回6件中1件）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 済 | M6_review-1 No.1〜8 | テスト e・g・h・j・k の補強、cwd=PROJECT_ROOT と絶対パス、run_steps への一本化、表示の相対パス化、flush=True、警告表示、不要な patch の削除。すべて対応済み | — |
| 2 | 軽微 | tests/test_update.py | default_runner が cwd=PROJECT_ROOT で実行することを確かめるテストがない（変異「cwd なし」を見逃し）。subprocess.run を差し替えて引数を確かめるテストを追加 | M6-03_impl |
| 3 | 軽微（容認） | src/update.py compare_dataframes | 片方だけ緯度経度が空のとき「位置の変更」がありになることのテストがない（変異を見逃し）。元データの検査（validate_dataframe）で空の座標は通らない見込みのため容認 | — |
| 4 | 軽微（容認） | reports/M6-02_report.md | 実データの --dry-run は「古いデータと新しいデータが同じファイルです」で終了。指示書どおり。差分一覧の確認は確認項目①（試験用 CSV）で行う | — |

## 判定：合格（修正1回目で合格。M6 の残り：M6-03_impl 公開用ページ → 確認シート）
