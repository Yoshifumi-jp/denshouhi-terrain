# ソース確認 M6（5回目）　確認日：2026-10-03

- 確認範囲：作業中コミット 283171b（M6-05 作業中）からの差分（src/check_public.py、tests/test_check_public.py、tests/test_build_site.py）＋影響範囲（collect_targets・main、build_site.py の更新履歴の表）
- 完了報告：M6-06_report.md・M6-07_report.md。各ファイルのバイト数は報告と一致（消失なし）。src/build_site.py は差分なし（M6-07 手順3の一時変更は元に戻っている）
- Claude の別環境（Linux の Python）での実行：`python -m pytest` で 88 passed・1 skipped（報告の 89 passed と合計一致。skipped は Windows 専用の1件と推測）
- 本物のフォルダでの公開前チェック：「公開前チェック：問題なし」（exit 0）

## 変異テスト（わざと壊して、テストが気づくか）
| 変異 | 結果 |
|---|---|
| check_public の正規表現を修正前（ユーザー名の部分を読みすぎる形）に戻す | 検出（test_collect_targets_and_patterns の n2、test_check_real_project が失敗） |
| build_site の更新履歴を「新しい順」にしない（iloc[::-1] を外す） | 検出（テスト d が失敗） |
| build_site で「完了」以外の行も表に出す | 検出（テスト d が失敗） |

## 試験用 CSV による差分一覧（確認項目①の下確認）
- _to_delete/M6_trial/2026-10-01/denshouhi_20261001.csv（Claude 作成）。仕込んだ答え：追加 36203-901／変更 36201-002（伝承内容）・36203-001（緯度＝位置の変更）／削除 36204-005／北海道 01202-001 の碑名変更（徳島の一覧に出てはいけない）
- `update.py --pref 36 --old … --new … --dry-run` の結果は答えと完全に一致（追加1／変更2・うち位置1／削除1、北海道は出ない）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/check_public.py 14・17行 | 指示書は読点句点（、。）までを除く指定だったが、半角の「,」「.」も除いている（指示外の変更）。そのため macOS・Linux 形式のホームのパスでユーザー名にドットを含むもの（例：home の下の「名.姓」）は検出されない。Windows 形式はドットの前までで検出できる（確認済み）。本プロジェクトは Windows で作成し、本物のフォルダのチェックは問題なしのため、公開への影響はない | M7-01 にまとめる（半角「.」「,」を除外から外し、URL のテスト n2 が引き続き0件であることを確かめる） |
| 2 | 軽微 | src/check_public.py 110行（M6-03 から） | main() の中で parse_args() が sys.argv（コマンドの引数）を読むため、`pytest -q` や `pytest tests/…` のように引数を付けて実行すると test_main_output が失敗する（引数なしの `python -m pytest` では合格） | M7-01 にまとめる（parse_args(args) の形にするか、引数を使わないなら argparse を外す） |

## 判定：**合格**（修正3回目。重大・中 0件、軽微2件は M7-01 に持ち越し）
