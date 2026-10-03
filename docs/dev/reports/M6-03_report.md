# 作業報告

## 1. 完了した作業と実行結果
指示書 M6-03 の内容を実装し、公開用ページの作成スクリプト（`src/build_site.py`）と公開前チェック（`src/check_public.py`）を作成しました。また、`src/update.py` を更新し、自動テストを実装・修正しました。

`src/build_site.py` 実行結果:
```
対象の県名: 徳島県
データ取得日: 2026-09-24
碑の数: 71
作成したファイル:
  docs\map_36.html
  docs\fig\box_elevation_36.png
  docs\fig\box_slope_36.png
  docs\fig\box_river_dist_36.png
  docs\fig\box_river_height_36.png
  docs\fig\box_coast_dist_36.png
  docs\fig\bar_landform_36.png
  docs\data\summary_36.csv
  docs\data\landform_36.csv
  docs\data\relocated_36.csv
  docs\data\update_history_36.csv
  docs\.nojekyll
  docs\index.html
公開前チェック：問題なし
```

`src/check_public.py` 実行結果:
```
公開前チェック：問題なし
```

- `docs/index.html` をブラウザで確認し、PCの幅とスマホの幅で表・グラフ・リンクが正しく見られること、表が横スクロールできる枠に入っていることを確認しました。
- `git status docs/dev/` で `docs/dev/` の中身が変わっていないことを確認しました。
- `pytest` による自動テスト（85件）が全て合格することを確認しました。

## 2. 変更・作成したファイルとバイト数
- `src/build_site.py` (12896 bytes)
- `src/check_public.py` (3898 bytes)
- `src/update.py` (14793 bytes)
- `tests/test_build_site.py` (6253 bytes)
- `tests/test_check_public.py` (3322 bytes)
- `tests/test_update.py` (15054 bytes)

## 3. 確認したいこと
特にありません。
