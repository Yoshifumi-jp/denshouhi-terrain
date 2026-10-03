# 指示書 M2-04（修正）　作成日：2026-09-28

最初に AGENTS.md を読んでから作業してください。

## 目的（このテーマ1つ）
キャッシュに1行追加したあとも「緯度」「経度」の列が数値のままになるようにし、pandas 2.x でも 3.x でも同じように動くようにする。

## 対象ファイル
- src/add_elevation.py
- tests/test_add_elevation.py
- src/load_monuments.py（下の「あわせて行う軽微な修正」のみ）

## やること（手順）
1. src/add_elevation.py 107行 `cache_df.loc[len(cache_df)] = new_row.iloc[0]` を見直す。
   `new_row.iloc[0]` は文字と数値が混ざった1行のため、pandas 2.x ではこれを追加した時点で緯度・経度の列が文字型（object）に変わり、
   次の検索（60行の `.round(6)`）で TypeError になる。
   1行追加したあとも緯度・経度が float のままになる書き方に直す（例：追加後に緯度・経度を数値に変換し直す、検索用の辞書を別に持つ、など。方法は任せる）。
2. テストを1件追加する：空のキャッシュから2地点を取得したあと、キャッシュの「緯度」「経度」の列が数値型であることを確かめる。
3. `python -m pytest` で全件合格すること。

## あわせて行う軽微な修正（M2-01 で行ったが消えていたもの）
- src/load_monuments.py の未使用の `import os` を削除し、各関数に日本語の docstring（何をする関数か・引数・戻り値）を書く。処理の中身は変えない
- 修正後も `python src/load_monuments.py --pref 36` が「徳島県 71基」のままであること

## やらないこと
- 上記以外の変更、data/ 配下の実データの変更
- git commit、git push

## 完成の条件
- `python -m pytest` で全件合格（Claude が pandas 2.3 の環境でも実行して確かめます）
- `python src/add_elevation.py --pref 36` の結果が変わらない（71基すべて取得済、問い合わせ0回）
- VS Code の「問題」タブでエラー0件
- 変更したファイルがすべて保存されていること（Antigravity の変更を承認し、VS Code のタブに未保存の印●が残っていないこと）

## 完了後
- 自己チェックを行い、docs/dev/reports/M2-04_report.md に報告を書く。
- 報告の「使った pandas のバージョン」は、`.venv\Scripts\python -c "import pandas; print(pandas.__version__)"` の表示をそのまま貼り付ける。
