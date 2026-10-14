# ソース確認 M12（1回目・M12-01 進捗表示）　確認日：2026-10-08

- 確認範囲：「M11 合格」コミットからの差分（src/progress.py 新規、src/add_hazard.py、src/add_landform.py、tests/test_progress.py 新規、tests/test_add_hazard.py、tests/test_add_landform.py）
- 報告の実行結果とコードの表示文の照合：一致（進捗の行の形は progress_line の f 文字列どおり。71件で 10,20,…,70,71 の8行は should_print の条件どおり。キャッシュ枚数は get_tile の数え方（1基6レイヤー、同じタイルはメモリから読み数えない）と矛盾なし）
- テスト件数の検算：テスト関数 171（166＋5）＋ test_add_river_coast の parametrize 分 ＝ 176。報告の 176 passed と一致
- 空白を無視した差分（git diff -w）で、変更は「全行を list に読む」「1件ごとの進捗の print（flush=True）」「clock 引数」「target_str の移動」だけ。出力CSV・まとめ表示・キャッシュの処理は変わっていない。ループ内に continue・break はなく、全件で進捗判定が通る
- pyflakes（Claude が本人のPCの別環境で実行）：指摘0件。git status：data/processed・output に変更なし。改行コード：LF

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | tests/test_add_hazard.py 386行 | test_real_cache の末尾に `print(out)`（報告用に表示させたデバッグの残り） | 次の指示書で削除 |
| 2 | 軽微 | src/add_hazard.py 299〜300行ほか | target_str を移した跡の空行2行、`rows = list(reader)` の後の空白だけの行（add_landform も同じ） | 次の指示書で整理 |
| 3 | 軽微 | 報告 | tests/test_progress.py のバイト数 884 → 実際 885 | 記録のみ |

- 本人の画面（2026-10-08 18:07 のスクリーンショット）は 171 passed で test_progress.py の行がない → Antigravity が最後にファイルを保存した 18:02 より前の実行と推測。本人に `python -m pytest` の再実行を依頼

- 本人の再実行（2026-10-08 18:41）：176 passed（test_progress.py 3件を含む）、問題タブ エラー0・警告0

## 判定：M12-01 完了（重大・中0件。軽微1・2は次の指示書へ持ち越し）。M12 の合否は全国の実行後に判定
