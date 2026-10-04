# ソース確認 M8（2回目）　確認日：2026-10-04

- 確認範囲：998a0e4（M8-01 作業中）からの差分＋影響範囲（src/add_hazard.py、src/hazard_layers.py、tests/test_add_hazard.py）
- ファイルの消失：なし（報告のバイト数と一致）
- 報告の実行結果とコードの表示文の照合：まとめ表示は一致（件数は M8-01 と同じ、問い合わせ0件）。**pytest は test_add_hazard.py 単独の結果だけが貼られ、全体は「全113件合格」と文章で書かれていた。test_add_hazard.py が9件→10件に増えたので、全体は114件になるはず（食い違い）**
- 起動方法の確認（Claude）：PYTHONPATH にプロジェクトを入れない状態で `python src/add_hazard.py --pref 00` を実行 → ImportError ではなく「--pref には 01〜47」のエラー文・終了コード1（M8_review-1 No.1 は解消）
- 公開前チェック：問題なし

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 中 | docs/dev/reports/M8-02_report.md | 全体の pytest の結果を貼らず、件数（113件）を文章で書いた。実際は114件のはず。AGENTS.md「実行時の出力をそのまま貼る」違反（M4-01・M7-03 に続き3回目） | 本人が `.\.venv\Scripts\python.exe -m pytest -q` を実行し、最後の行で確認する（114 passed なら解消） |
| 2 | 軽微 | tests/test_add_hazard.py test_launch_method | PYTHONPATH を取り除いた env を作っているが、subprocess.run に `env=env` を渡していない（取り除けていない）。本体の修正は Claude が上の方法で確認済み | M8-03 に含める |
| 3 | 軽微 | tests/test_add_hazard.py test_real_cache | M8-01 で入れた「キャッシュの更新日時が変わらない」確認を消し、data/processed だけにした（両方必要） | M8-03 に含める |
| 4 | 軽微 | tests/test_add_hazard.py test_main_execution | 「取得不可がある行は取得日が空欄」の確認がない | M8-03 に含める |
| 5 | 軽微 | tests/test_add_hazard.py test_summarize_dosha | ①〜⑤の説明コメントを指示なく削除 | M8-03 で戻す |
| 6 | 軽微 | scratch/（指示外） | Antigravity の作業用スクリプト3つ → Claude が _to_delete/M8-02_work/ へ移動 | 済 |

- M8_review-1 の No.2（近い色の記録の名前）・No.3（テスト f・e・g・i・j）は解消（上の軽微を除く）

## 追記（2026-10-04 04:50 Claude）：本人の pytest 実行で起きたこと
- 本人の実行結果「1 failed, 113 passed」。失敗は _to_delete/M8-02_work/insert_test.py（Antigravity の作業用スクリプト）
- 原因：Claude が scratch/ の作業用スクリプトを _to_delete/M8-02_work/ へ移したが、名前が「〜_test.py」のため pytest がテストとして読み込んだ。読み込み時に remove_test.py の中身（tests/test_add_hazard.py から test_main_execution を削除して書き戻す処理）が実行され、**tests/test_add_hazard.py が 15,678B → 10,683B に変わった（改行も CRLF に変わった）**。scratch/ に置いたままでも同じことが起きた（推測ですが、Antigravity の全体実行の「113件」もこのため）
- 対応：作業用スクリプト3つを .py.txt に改名（pytest が読まない）。tests/test_add_hazard.py を、insert_test.py の本文と M8-02 の差分（remove_date の比較）から元どおりに復元（15,678B・LF・テスト関数10個・構文確認済み。復元は元に戻すだけ）
- 今後：作業用ファイルを移すときは、名前が test_*.py／*_test.py でないことを確かめる（Claude）。M8-03 の指示書に「作業用スクリプトを作らない。作るなら _to_delete/ に .txt で」を入れる

## 判定：**合格**（修正1回目で合格）。2026-10-04 04:50 本人が `python -m pytest -q` を実行し「114 passed」を確認（No.1 解消）。実行後も tests/test_add_hazard.py は 15,678B のまま
