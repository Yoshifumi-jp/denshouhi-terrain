# ソース確認 M10（2回目・M10-02_fix）　確認日：2026-10-05

- 確認範囲：M10-01 からの差分（src/add_river_coast.py、tests/test_add_river_coast.py）
- 報告の実行結果とコードの表示文の照合：一致。報告のバイト数（22326・22977）・LF も実際と一致
- Claude の実行（本人のPCの作業環境・別の Python）：tests/test_add_river_coast.py・test_prefectures.py・test_check_public.py は 33 passed。全体では 151 passed。失敗4件のうち3件は Claude 側の環境の文字コード（日本語の表示を cp932 で読む起動テスト）によるもので、本人の環境では起きない（推測を含む）。残り1件は下の No.1

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 中（対応済み） | docs/dev/reports/M10-02_report.md 19・21行 | 報告に貼った pytest -v の出力にユーザー名入りのパスがあり、公開前チェックのテスト（test_check_real_project）が失敗する。第1版の振り返りで決めた注意の再発 | Claude が `<ユーザー名>` に置き換えた（docs/dev は Claude が書いてよい範囲。ソースの編集ではない）。置き換え後 test_check_public は合格。M10-03 の指示書に置き換えの注意を追記 |
| — | — | M10_review-1 の No.1〜5 | すべて解消（未定義の関数を定義、碑の位置を河川の近くに、距離の比較を必ず通る形に、import の整理、docstring・空行） | — |

## 判定：M10-02 の修正は合格。M10 は M10-03（隣接県）の実装へ進む（M10 全体の合格判定は M10-03 の後）
