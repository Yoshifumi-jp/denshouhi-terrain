# ソース確認 M6（1回目）　確認日：2026-10-03

- 確認範囲：105a6ed（M5 合格）からの差分＋影響範囲（src/update.py 新規、tests/test_update.py 新規、output/diff/、output/update_history_36.csv、output/map_36.html）
- ファイル消失：報告直後（08:13）に src/update.py・tests/test_update.py が0バイトになった（6回目）。本人が VS Code のタイムラインから復元（15,574B／11,269B。報告値より各1バイト多いのは末尾改行の差）
- Claude の確認：
  - 別環境で pytest（test_update.py）7 passed
  - 偽データで main を実行（追加1・変更2〈伝承内容／緯度〉・削除1・他県の行・前後空白だけの違い）→ 期待どおり（位置の変更 あり／なし も正しい）
  - 実データの実行記録（full_run.txt）：10ステップすべて成功、各ステップの問い合わせ回数 0、output/summary_36.csv のハッシュ不変（D2F374D6…）、更新履歴「完了」1行、差分ファイル 71行（追加71）
  - 変異テスト（わざと誤りを入れてテストが気づくか）：6件中5件を見逃し（並び順を逆／他県を数える／dry-run で履歴を記録／ステップを1つ抜く／BOM なし）。気づいたのは「前後の空白を比較に含める」のみ

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 中 | tests/test_update.py | 指示書のテストの不足：e（main を通した他県の除外。今は手で startswith して compare だけ呼んでいる）、g（並び順・utf-8-sig）、h（初回で全件「追加」。今は0件のみ）、j（--dry-run で履歴を記録しない）、k（10ステップが決まった順と引数で呼ばれる）。変異5件を見逃した | M6-02_fix |
| 2 | 中 | src/update.py do_run_steps | 子スクリプトを相対パス "src/xxx.py" で、作業フォルダを指定せずに実行している。プロジェクトのフォルダ以外から実行すると全ステップが失敗する（指示書「作業フォルダはプロジェクトのルート」） | M6-02_fix |
| 3 | 中 | src/update.py run_steps | 使われていない関数 run_steps が残っている。中断時に履歴を残さない誤った処理（except で pass）を含み、読み違いの元になる | M6-02_fix |
| 4 | 中 | reports/M6-01_report.md | 実行結果を「以下同文のため省略」「中略」と省いている（AGENTS.md「出力はそのまま貼る」に反する）。指示書外の作業ファイル dry.txt・dry_run.txt・full_run.txt をルートに作成（Claude が _to_delete/M6-01_work/ へ移動） | M6-02_fix（報告の書き方） |
| 5 | 軽微 | src/update.py main | 「古いデータ」「新しいデータ」のパスを渡されたまま表示する（--new に絶対パスを渡すとユーザー名入りのパスが出る）。AGENTS.md「個人情報の扱い」に合わせ to_rel_path で表示 | M6-02_fix |
| 6 | 軽微 | src/update.py do_run_steps | 「[n/10] …」の表示が、出力をファイルに保存したとき子の出力より後ろにまとめて出る（バッファのため）。print に flush=True | M6-02_fix |
| 7 | 軽微 | src/update.py determine_old_csv | 履歴の読み込み失敗を except で黙って無視し、完了行のファイルが無いときも黙って2番目のフォルダに切り替える。警告を表示する | M6-02_fix |
| 8 | 軽微 | tests/test_update.py test_j | 何もしない `with patch(...): pass` が残っている | M6-02_fix |

## 判定：不合格（修正1回目へ）
