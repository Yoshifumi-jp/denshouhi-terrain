# ソース確認 M3（7回目：M3-08_fix）　確認日：2026-10-01

- 確認範囲：63cf258（M3-07 作業中）からの差分 src/add_landform.py（8,533B）、tests/test_add_landform.py（9,467B）
- 報告のバイト数とディスク上のサイズ：一致（消失なし）
- 本体の結果：前回と同じ（取得済60／データなし11、名前ごとの件数も同じ）、問い合わせ0回

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| M3_review-6 No.1（重大） | — | tests | rmtree・本物キャッシュへの書き込みを削除、tmp_path を使用 | 解消 |
| M3_review-6 No.2（中） | — | src 16・61〜63行 | PROJECT_ROOT 基準に変更、cache_dir を引数化 | 解消 |
| M3_review-6 No.3（中） | — | src 121〜141行 | finally で sleep_fn。テスト l で8回を確認 | 解消 |
| M3_review-6 No.4・5（軽微） | — | src | 県コード確認を add_river_coast と同じに／不要な except を削除 | 解消 |
| 1 | 軽微 | tests/test_add_landform.py 220行〜 | test_cache_untouched が相対パス Path("data")/... を使うため、プロジェクト以外の場所から pytest を実行すると「空＝空」で常に合格してしまう | M4-01 にまとめて（PROJECT_ROOT 基準に） |

- 片付け（Claude）：テストが作った偽タイル6枚（data/cache/landform/16/57161/、中身は 133.9〜134.1 の正方形）を _to_delete/fake_landform_tiles/ へ移動。残りのキャッシュ 44枚＝本体の問い合わせ回数と一致

## 判定：合格（ソース確認）。マイルストーン合格は確認シート M3_check-4 の結果による
