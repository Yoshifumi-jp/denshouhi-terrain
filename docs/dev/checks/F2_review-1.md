# ソース確認 F2（1回目）　確認日：2026-10-15

- 確認範囲：d384a42（フェーズ4 作業中）からの差分（src/build_national.py・src/build_site.py・tests 2ファイル・docs/index.html・docs/pref_01〜47.html）
- 報告の実行結果とコードの表示文の照合：一致（git status・numstat・ls-files --eol は Claude の実行と一致。バイト数6件を実測で照合し一致）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 確認済（指摘なし） | src/build_national.py・src/build_site.py | 追加は指示どおりの1行ずつ。字下げ4文字、既存のリンク・文は不変。docs/index.html・pref_XX.html はその1行の追加だけ（numstat 1 0） | — |
| 2 | 確認済（指摘なし） | tests 2ファイル | 指示どおりの2件（全国ページ：PDF リンク2回・1回目が最初の h2 より前／県別ページ：戻るリンク＜PDF リンク＜h1）。pytest 223＝221＋2 | — |
| 3 | 軽微（Claude の誤り） | 指示書 F2-01「完成の条件」 | docs/pref_XX.html は M14-01（4ccaa08）から CRLF で作られ・コミットされている（src/build_site.py 431行 write_text に newline 指定なし。Windows で CRLF になる）。今回の変更で CRLF になったのではない（HEAD の CR 数 170 → 今 171＝1行追加分）。Claude が M14-01 の確認でも F2-01 の指示書でも見落とし、pref_36 を LF と書いた。Antigravity は指示どおり止まって報告（正しい対応） | F2-02_fix：build_site.py に newline='\n' を付け、47県分を LF で作り直す（AGENTS.md の LF の決まりと、ほかの生成ファイル（index.html は LF）にそろえる） |

## 判定：合格（F2-01。CRLF は今回の変更による不具合ではないため、別テーマ F2-02 で扱う）
