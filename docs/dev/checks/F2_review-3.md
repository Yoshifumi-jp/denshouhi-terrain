# ソース確認 F2（3回目・全ソースの最終確認）　確認日：2026-10-15

- 確認範囲：Git 管理の全 2,005 ファイル（d601bcc 時点）。src 23本・tests 21本は全文を対象に機械点検、README・AGENTS・.gitignore は目視
- 確認方法：pyflakes（src・tests）、改行コードの全数点検、日本語を含まないコメントの抽出、秘密情報・個人情報の文字列検索、作業用ファイルの残り、README と実際の作りの照合

| No | 重大度 | 対象 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 確認済（指摘なし） | src・tests | pyflakes 指摘0件。TODO・FIXME・デバッグ用の print なし | — |
| 2 | 確認済（指摘なし） | 全体 | APIキー・パスワード・トークンの記述なし（.env は使っていない）。ユーザー名入りのパス・メールアドレスは AGENTS.md の「書かない」決まりの例（伏せ字）だけ。check_public「問題なし」（F2-02 報告） | — |
| 3 | 確認済（指摘なし） | 不要ファイル | Git 管理内に作業用の残りなし（docs/dev/reports/_template.md は報告の書式で必要）。_to_delete/（作業前の控え CSV・旧 docs 34件・メモ txt）は .gitignore 済みで公開されない。本人が後で削除 | 本人（任意） |
| 4 | 確認済（指摘なし） | 改行コード | .py・.md・.html・.ini はすべて LF（F2-02 で県別ページも LF） | — |
| 5 | 軽微 | requirements.txt | この1ファイルだけ CRLF（第1版から）。pip は問題なく読む | 記録のみ |
| 6 | 軽微 | CSV 全般（output・docs/data 816件） | pandas の to_csv が Windows で CRLF を書く。すべてそろって CRLF で、Excel で開く用途には支障なし | 記録のみ（統一するなら第3版で lineterminator を指定） |
| 7 | 軽微 | tests の一部・src 2か所 | 日本語を含まないコメント29件。多くは番号付きの見出し（「1. relocated_all.csv」）や式（「2/3 = 0.666...」）で、英文は tests/test_run_batch.py 29・107〜108行、test_add_landform.py 206・212行など数件 | 記録のみ（次に該当テストを触るとき日本語に） |
| 8 | 軽微（Claude が修正） | README.md 8行 | PDF へのリンクの場所（全国ページの上部・下部、県別ページの上部）が書かれていなかった（F2-01 の反映漏れ） | Claude が README に追記（2026-10-15） |

## 持ち越しの軽微な指摘（M14 の確認から。いずれも動作に影響なし。final_report.md に記録）
M14_review-1 No.3／M14_review-2 No.1／M14_review-3 No.2・No.4／M14_review-4 No.2・No.3・No.4（No.4 は最終確認シート F2_check-1 No.8 で本人が判断）／M14_review-6 No.1／M14_review-7 No.2・No.3

## 判定：重大・中 0件（最終確認の条件を満たす。F2_check-1 の結果待ち）
