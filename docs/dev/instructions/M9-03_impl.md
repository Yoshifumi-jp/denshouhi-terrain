# 指示書 M9-03（実装・テストの使っていない import の整理と M9-01 の軽微な指摘）　作成日：2026-10-05

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」「完了報告」「作業用のスクリプトを作らない」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ：動きを変えない整理）
第1版から持ち越した「tests の使っていない import・変数」と、M9-01 のソース確認で見つかった軽微な指摘を直す。
**プログラムの動き・出力ファイルは変えない**（2章の空要素の扱いだけは表示が変わる）。
GitHub への push・git commit は行わない。

## 対象ファイル
- 変更：tests/ の下の次の11ファイル（1章の一覧）、src/load_monuments.py、tests/test_load_monuments.py
- **変えないもの**：src/ のほかのファイル、data/ の中、docs/ の中（報告書の追加以外）

## 1. 使っていない import・変数を消す（Claude が pyflakes＝使われていない名前を見つけるツール で調べた結果。これがすべて）
| ファイル | 行 | 内容 | 直し方 |
|---|---|---|---|
| tests/test_add_elevation.py | 362 | 変数 out_file を作って使っていない | 代入の行を消す（右辺に副作用がなければ） |
| tests/test_add_elevation.py | 389・497 | hashlib を2回 import（389行は使っていない） | 389行の import を消し、497行（関数の中）の import は残す。または 389行をファイル先頭の import にまとめて 497行を消す。どちらか一方 |
| tests/test_add_hazard.py | 9 | pathlib.Path | import を消す |
| tests/test_add_hazard.py | 12 | src.hazard_layers.DOSHA_NAMES | import を消す（同じ行のほかの名前は残す） |
| tests/test_add_hazard.py | 299 | 変数 stderr_str を使っていない | 代入の行を消す |
| tests/test_add_landform.py | 2・4・222 | json、datetime.datetime、（関数内の）pathlib.Path | import を消す |
| tests/test_add_river_coast.py | 5・6 | pathlib.Path、math | import を消す |
| tests/test_analyze_denshou.py | 2・4・5・6 | sys、numpy、pathlib.Path、src.analyze_denshou の classify_monument・main・check_files_exist_local | import を消す（6行のほかの名前は残す） |
| tests/test_build_site.py | 2・6 | shutil、src.check_public.find_private_info | import を消す |
| tests/test_make_comparison_points.py | 1・5・212 | os、pathlib.Path（5行と関数内212行で2回） | os を消す。Path は5行を消して212行を残す、または212行を消して5行を残す。どちらか一方 |
| tests/test_make_map.py | 4・7・297 | sys、html（7行と関数内297行で2回） | sys を消す。html は7行か297行のどちらか一方を残す |
| tests/test_summarize.py | 4・5 | sys、pathlib.Path | import を消す |
| tests/test_summarize_hazard.py | 10 | src.summarize_hazard.check_files | import を消す（同じ行のほかの名前は残す） |
| tests/test_update.py | 5・6 | os、subprocess | import を消す |

- 行番号は 2026-10-05 時点（コミット 2e396c4）のもの。消す前に、その名前がファイルの中で本当に使われていないか検索して確かめる（mock の文字列 "subprocess.run" などで名前を文字列として書いている所は「使っている」に当たらない）
- テストの中身（確かめている内容）は変えない。テスト関数を消さない

## 2. src/load_monuments.py（M9-01 の軽微な指摘）
1. parse_pref_arg に日本語の説明（docstring）を付ける：何を受け取り、何を返し、どんなときに ValueError になるか
2. 空の要素を含む指定（例 `"03,,20"`、`"03,"`）は、使えない値として「（空）」と表示する
   - 例：`"03,,20"` → `エラー: --pref に使えない県コードがあります: （空）（01〜47 の2桁をカンマ区切りで、または all を指定してください）`
   - 例：`"03,,99"` → `…あります: （空）, 99（01〜47 …）`（空は1回だけ、元の並びで最初に出た位置に）
3. ファイルの最後の空行を1行にする（今は最後に空行が2つ続いている）

## 3. tests/test_load_monuments.py（M9-01 の軽微な指摘）
1. parse_pref_arg のテストに、2章2の例（`"03,,20"`、`"03,"`、`"03,,99"`）とメッセージの確認を足す
2. 実データでの照合に、main を通すテストを1つ足す：data/raw/2026-09-24/denshouhi_20260924.csv があるときだけ（ないときは pytest.skip）、`main(["--raw", <そのCSV>, "--pref", "36,03,28,20"], output_dir=<tmp_path>)` を実行し、
   - tmp_path に monuments_03.csv・monuments_20.csv・monuments_28.csv・monuments_36.csv の4つができ、行数がそれぞれ 163・111・103・71
   - 表示の最後の行が `対象の県数: 4県　合計: 448基`

## 4. やらないこと
- src/ のほかのファイルの変更、テストの確かめる内容の変更、テストの追加（3章以外）
- 書式の一括整形（自動フォーマッタ）、import の並べ替え

## 5. 完成の条件
- 1章の一覧の名前がすべて消えている（Claude が pyflakes で確かめる。Antigravity は1章の各行を検索で確かめればよい）
- `python -m pytest` が全件合格（目安 146件。テスト全体を実行すること）
- 「問題」タブのエラー0件／改行コードは LF のまま

## 6. 完了後
- 自己チェックを行い、docs/dev/reports/M9-03_report.md に報告を書く。変更したファイルの一覧（バイト数つき）と、次の実行結果を画面に出た文のまま貼る
  - `.\.venv\Scripts\python.exe src\load_monuments.py --pref 03,,99` の表示
  - `.\.venv\Scripts\python.exe -m pytest` の最後の行（テスト全体）
