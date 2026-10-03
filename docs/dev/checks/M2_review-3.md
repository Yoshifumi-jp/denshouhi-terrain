# ソース確認 M2（3回目）　確認日：2026-09-28

- 確認範囲：M2-04 の変更（src/add_elevation.py、tests/test_add_elevation.py、src/load_monuments.py）
- Claude による独立確認：
  - ファイルはディスクに保存済み（19:44）。src/load_monuments.py は import os 削除・docstring 追加済み（M1 合格時からの差分で確認）
  - pytest（Claude の環境、pandas 2.3.3）：21件中19件合格、2件失敗（下記 No.2）。本人の環境（pandas 3.0.6）は全件合格
  - プログラム本体の経路（キャッシュなしからの初回実行、1行追加後の型の確認）は pandas 2.3.3 でも合格

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | — | src/add_elevation.py 107〜109行 | M2_review-2 No.3（1行追加後の型）：解消 | — |
| 2 | 軽微 | tests/test_add_elevation.py 22、74行 | test_calculate_slope・test_api_result_parsing が、load_cache を使わずに型の決まっていない空の表を自分で作っているため、pandas 2.x ではこの2件だけ失敗する。プログラム本体の動作には影響しない | M3 の指示書でまとめて修正 |
| 3 | 軽微 | src/add_elevation.py 113行ほか | 使っていない変数・import（add_elevation.py の e、test_add_elevation.py の math・Path・datetime・368行の df、test_load_monuments.py の os） | M3 の指示書でまとめて修正 |
| 4 | — | src/load_monuments.py | M2_review-2 No.4：解消 | — |

## 判定：ソース確認は合格（重大・中 0件、修正3回目）
- No.2 はテストの準備部分の書き方の問題で、本人の環境では全件合格、本体は pandas 2.x でも正しく動くため軽微とした
- 残りは本人の動作確認（checks/M2_check-1.md）
