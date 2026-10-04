# ソース確認 F（2回目・F-02_impl　CR-6）　確認日：2026-10-04

- 確認範囲：b73f8fa（F-01 合格）からの差分＝src/make_map.py、tests/test_make_map.py、output/map_36.html、docs/map_36.html
- 報告の実行結果とコードの表示文の照合：一致
  - make_map.py：`<style>` 1行の追加、`<details>`・`<summary>` の2行の書き換え、注意文2行を `</details>` の後へ移動のみ（中の出典・免責事項は不変）
  - map_36.html：folium の要素ID（32桁の英数字）を除くと差は上記9行だけ。docs/map_36.html と output/map_36.html は同一
  - 改行コード：2ファイルとも CR 0行
  - pytest 135 passed：テスト関数130＋parametrize 5件＝135 で検算一致
  - ハッシュ3件不変、作業用ファイルなし

| No | 重大度 | ファイル・行 | 内容 | 対応（指示書番号） |
|---|---|---|---|---|
| — | — | — | 指摘なし | — |

## 判定：合格（修正なし）。見た目（▶が二重にならない・開閉できる）は F_check-1 No.12〜15 で本人が確認
