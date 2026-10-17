# ソース確認 F3（第3版 最終確認・1回目）　確認日：2026-10-17

- 確認範囲：第3版の全ソース。6e30f2d（第3版着手前）から ad05fa1（M17 合格）までの src・tests・README・AGENTS・.gitignore の差分（21ファイル、追加3,735行・削除43行）と、公開されるファイル全体
- 報告の実行結果とコードの表示文の照合：M15-01〜M17-04 の各回で実施済み（すべて一致）

## 確認した観点と結果
| 観点 | 結果 |
|---|---|
| 不要ファイル | なし。src/.gitkeep（0バイト）は既存のもの。未追跡ファイルなし |
| 秘密情報・個人情報 | src・tests・README・AGENTS・公開ページ・docs/dev に Windows のユーザー名を含むパス・APIキー・メールアドレスなし（tests の "secret" は公開前チェックの試験用の文字） |
| コメントの日本語 | 新しい3ファイル（add_landform_region・run_region_batch・summarize_region）は日本語。英字だけのコメントは1行（下表 No.4） |
| 秘密情報の置き場（.env） | 新しいプログラムは APIキー等を使わない。.gitignore に .env あり |
| 必要なパッケージ | 新しいプログラムが使うのは pandas・shapely と標準ライブラリだけで、requirements.txt にある |
| 改行 | src・tests・README・AGENTS・.gitignore に CR なし（LF） |
| README との整合 | Claude が第3版の状態に更新（状態の行、「できること」に地域版3行、使い方に「4. 地域版だけを作る」、出典、注意）。コマンド名・引数（--pref all・--check-only）・出力ファイル名はソースと一致 |
| 既存の結果の不変 | M15〜M17 の各回で v3_hashes.md の100ファイルと徳島のハザード3件の不変を確認済み |

## 指摘（重大・中 0件。軽微はすべて動作に影響なし）
| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 軽微 | src/make_national_pdf.py（目次・地域版の表の注・A/B の数え方） | M17_review-3 の3件（目次とフッターの間が狭い／注2行目が表より右に出る／build_national.py との二重書き） | 記録のみ・第4版以降 |
| 2 | 軽微 | src/make_map.py main() | 地域版で補ったかの判定の二重書き（M17_review-1） | 記録のみ・第4版以降 |
| 3 | 軽微 | src/count_missing.py | count_region の2回呼び（M16_review-3） | 記録のみ・第4版以降 |
| 4 | 軽微 | src/add_landform_region.py 179行 | 英字だけのコメント「key: (z, x, y), value: geojson_dict or "error"」 | 記録のみ・第4版以降（意味は前後の日本語で分かる） |
| 5 | 軽微 | src/add_landform_region.py _resolve_code ほか | M15_review-1 の2件（code が空の地物の数え方／pytest の所要時間）、M16_review-1 No.2（開始の行の3桁区切り） | 記録のみ・第4版以降 |

## 判定：合格（重大・中 0件）。最終確認シート F3_check-1 がすべて○になれば完全合格
