# ソース確認 M10（3回目・M10-03）　確認日：2026-10-06

- 確認範囲：作業中コミット 139df9a（M10-01・M10-02 分）からの差分＋影響範囲（src/prefectures.py、src/add_river_coast.py、tests/test_prefectures.py、tests/test_add_river_coast.py）
- 報告の実行結果とコードの表示文の照合：一致
  - 「読み込む河川データ」「読み込む海岸線データ」「海岸「対象外（海のない県）」の件数」「次のデータが足りません…」の文は main()・process_river_coast の print 文と一致
  - 6章3の差分（碑7行・比較地点35行、違う列は海岸までの距離_m のみ）は指示書4章の既知の答えと一致。河川側の標高の問い合わせ0回
  - 報告のバイト数4件は実ファイルと一致、CRLFなし、ユーザー名入りパスなし
- データの戻し：river_coast_36.csv（sha256 先頭 5486d683…）・river_coast_points_36.csv（4ae10ea4…）は _to_delete の作業前コピーと同一。data/raw/rivers/W05-06_37_GML の名前も元どおり
- NEIGHBORS：docs/dev/m10_neighbors.md の表（47県・延べ174・87組）と完全一致、各リストは小さい順。LANDLOCKED は8県ちょうど
- pytest：収集 160件（報告の 160 passed と一致）。Claude の複製（Linux・data なし）で変更した2ファイルは 31 passed・1 skipped（実データ）。他ファイルの4件失敗は Claude の環境（data なし・ライブラリの版違い）によるもので、今回の変更と無関係（本人環境の結果は確認シート No.1）

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| 1 | 軽微 | src/add_river_coast.py 512行 | main() の `pref_name` が使われていない（pyflakes） | 次の指示書でまとめて |
| 2 | 軽微 | tests/test_prefectures.py 150・172行 | `LANDLOCKED`・`NEIGHBORS` の import が関数内で重複し未使用（pyflakes） | 同上 |
| 3 | 軽微 | src/add_river_coast.py find_input_shapefiles・process_river_coast | `if pref_code in LANDLOCKED: pass / else:` の書き方、coast_shp の空リスト判定の二重化、`海岸までの距離_m` の no_sea 条件が冗長（動きは正しい） | 同上 |

## 判定：M10-03 は報告確認として合格（重大・中 0件）。M10 の合否は確認シート M10_check-1 の結果で判定

## M10 判定（2026-10-07）：合格
- 確認シート M10_check-1 の4項目すべて○、問題タブのエラー0件、重大・中の指摘0件（M10_review-1〜3）。修正1回（M10-02_fix）
- 軽微3件（本書の No.1〜3）は M11 の最初の指示書へ持ち越し
