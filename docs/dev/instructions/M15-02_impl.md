# 指示書 M15-02（実装・更新コマンドに地形分類（地域版）の段階を加える）　作成日：2026-10-16

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update.py・update_all.py・run_batch.py・add_landform_region.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」4・5 のコマンドだけです。

## 目的（このテーマ1つ）
1県の更新コマンド src/update.py の段階に、M15-01 で作った地形分類（地域版）の付与を碑・比較地点の2段階として加える（計画書 版12 の M15）。

## 対象ファイル
- 変更する：src/update.py、tests/test_update.py
- 新しく作る：docs/dev/reports/M15-02_report.md
- 変えないもの：上記以外のすべて（特に src/run_batch.py・src/update_all.py・tests/test_update_all.py。test_update_all.py の「[9/14]」は偽の履歴の文字列なので変えなくてよい）

## やること
1. src/update.py の `steps` の一覧で、`("ハザード区域の判定（比較地点）", …)` の行の**直後**（`("集計", …)` の前）に次の2行を加える。ほかの行・順番は変えない（1〜10段階目の番号が今と変わらないようにするため）。
   ```
   ("地形分類（地域版）の付与（碑）", ["add_landform_region.py", "--pref", pref_code]),
   ("地形分類（地域版）の付与（比較地点）", ["add_landform_region.py", "--pref", pref_code, "--target", "points"]),
   ```
   これで段階は16（公開用ページありは17）になる。
2. tests/test_update.py の test_k_run_steps_main と test_m_no_site の `expected_cmds` に、同じ位置（add_hazard.py の points の直後）へ次の2行を加える（ほかは変えない）。
   ```
   [exe, str(tmp_path / "src" / "add_landform_region.py"), "--pref", "36"],
   [exe, str(tmp_path / "src" / "add_landform_region.py"), "--pref", "36", "--target", "points"],
   ```
3. tests/test_update.py にテストを1件足す：偽の runner で 11番目のコマンド（add_landform_region.py の碑）だけ returncode=1 にして main を実行すると、(a) 画面に `[11/17] 地形分類（地域版）の付与（碑） で失敗しました。` で始まる行が出る (b) update_history_36.csv の最後の行の結果が `失敗（[11/17] 地形分類（地域版）の付与（碑））` (c) 呼ばれたコマンドは11個。作り方は既存の test_run_steps_error にならう（SystemExit を pytest.raises で受ける）。
4. pyflakes src/update.py tests/test_update.py で指摘0件を確かめる。
5. .venv を有効にして `python -m pytest -q` を実行する。続けて次を実行し、出力を報告に貼る。
   ```
   git diff --numstat
   git status --short
   python -c "print([f for f in ['src/update.py','tests/test_update.py'] if b'\r' in open(f,'rb').read()])"
   ```

## 完成の条件（既知の答え）
- pytest：239 passed（238＋1）
- git diff --numstat：`2	0	src/update.py`、tests/test_update.py は追加だけ（削除 0）
- git status --short：` M src/update.py`・` M tests/test_update.py`・`?? docs/dev/reports/M15-02_report.md` の3行だけ
- 改行コードの確認の出力：`[]`

## やらないこと
- run_batch.py・update_all.py への組み込み、全国の実行（M16）
- 集計・地図・ページでの地域版の利用（M16・M17）

## 完了後
- 自己チェックを行い、docs/dev/reports/M15-02_report.md に報告を書く。pytest の最後の行と 5 の出力は、画面に出た文をそのまま貼る。ファイル名とバイト数の一覧も書く。報告に貼る絶対パスは `<プロジェクト>` に置き換える。
