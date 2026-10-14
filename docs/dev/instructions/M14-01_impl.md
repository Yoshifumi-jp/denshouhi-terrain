# 指示書 M14-01（実装・県別ページの置き場所変更と47都道府県分の作成）　作成日：2026-10-14

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る。言い換え・要約・記憶からの作り直しをしない」）。
作業前に、エディタのタブをすべて閉じてから始めてください。作業中に docs/dev/status.md・docs/dev/01_plan.md・output/ 配下・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。`python src/run_batch.py ...`（--check-only を除く）や `python src/update.py ...` の実行はしない。

## 目的（このテーマ1つ）
計画書 M14（版11.6）の準備として、公開用の県別ページを `docs/index.html` ではなく `docs/pref_XX.html` に作るように変え、47都道府県すべての県別ページを docs/ に作れるようにする。
全国ページ（新しい docs/index.html）は次の指示書（M14-02）で作るので、**今回は docs/index.html を作らない・変えない**。

## 対象ファイル
- 変更する：src/build_site.py、tests/test_build_site.py
- 新しく作る：docs/dev/reports/M14-01_report.md
- 実行で作られる：docs/pref_XX.html（47）、docs/map_XX.html、docs/fig/*_XX.png、docs/data/*_XX.csv（47都道府県分）
- 変えないもの：上記以外のすべてのファイル（**docs/index.html は変えない**。src/update.py・src/run_batch.py・src/check_public.py・output/・data/ も変えない）

## やること
1. src/build_site.py の `build_site()`
   1. 県別ページのファイル名を `site_dir / "index.html"` から `site_dir / f"pref_{pref}.html"` に変える（作成・created_files・公開前チェックの対象の3か所すべて）
   2. ページの `<h1>` の直前に、全国ページへ戻るリンクを1行入れる：`<p><a href="index.html">← 全国のページへ</a></p>`
   3. 必須ファイルの一覧（required_output_files）から `output/fig/disaster_groups_{pref}.png` を外す。このグラフは「5基以上の碑群」がない県では作られない（analyze_denshou.py の仕様。山形06・福井18・宮崎45・鹿児島44・沖縄47 がそう）。ページ側はすでに `if (...).exists()` で画像を出し分けているので、そのままでよい。画像がないときは、その位置に `<p>5基以上の碑群がないため、碑群の比較グラフはありません。</p>` を出す
   4. 引数に `quiet=False` を足す。quiet=True のときは「対象の県名／データ取得日／碑の数／作成したファイル」の表示と、関数の中の公開前チェックを行わない。どちらの場合も、作成したファイルのリスト（created_files）を戻り値で返す
2. src/build_site.py の `main()`：`--pref all` を受け付ける
   1. all のときは、まず47都道府県すべてについて必須ファイルがそろっているかを調べ、足りない県があれば `エラー：ファイルが足りない県があります：山形県（06）、…`（県名（コード）を「、」でつなぐ）と `先に実行してください：python src/run_batch.py --pref "XX,YY"` を表示して終了コード1で終わる（何も書かない）。調べ方は build_site() と同じ必須ファイルの一覧を使う（一覧を関数 `required_files(pref, output_dir, data_dir)` に切り出し、build_site() もそれを使う）
   2. そろっていれば、県コード順に `build_site(pref, quiet=True)` を呼び、1県ごとに次の1行を出す：`北海道（01）：碑 54基　docs/pref_01.html`
   3. 最後に、作ったすべてのファイルにまとめて find_private_info をかけ、次を出す：
```
作成した県：47
作成したファイル：<ファイル数>
docs の合計サイズ：<MB、小数1桁> MB
公開前チェック：問題なし
```
      （問題があれば「公開前チェック：問題あり」と各行を出して終了コード1。ファイル数は created_files の重複を除いた数、合計サイズは docs/ 配下（docs/dev/ を除く）のファイルの合計）
   4. 01〜47・all 以外は今と同じエラー文で終わる（文中の「（all は不可）」は削る）
3. tests/test_build_site.py
   1. 既存のテストの `index.html` を `pref_XX.html` に合わせる（テストの意味は変えない）
   2. 追加：(a) 県別ページに `href="index.html"` の戻るリンクがある (b) disaster_groups の画像がない県でもエラーにならず、上の文が出る (c) build_site() を呼んでも `index.html` が作られない (d) `--pref all` で1県でも足りないときは何も書かずに終了コード1（tmp_path に2県分の偽の出力を作り、PREFECTURES を2県に差し替えるなどで47県分を作らずに試す）
4. 実データで実行し、出力を貼る
   - `python src/build_site.py --pref all`
   - `git status --short docs | Measure-Object -Line`（変わった・増えたファイルの数）と `git status --short docs/index.html`（何も出ないこと）
   - `python -m pytest -q`（最後の行）、`python -m pyflakes src/build_site.py tests/test_build_site.py`
   - 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/build_site.py','tests/test_build_site.py']]"`（どちらも False）

## やらないこと
- docs/index.html の作成・変更、全国ページ、PDF、更新コマンドの変更（M14-02〜04）
- 県別ページの中身（表・グラフ・文）の変更（上の 1-2・1-3 以外）
- docs/map_36.html など、既にある docs/ のファイルを手で消すこと（実行で上書きされるのはよい）

## 完成の条件
- `python src/build_site.py --pref all` の表示が47行＋まとめ4行で、碑の数が output/pref_counts_all.csv の「碑_数」と47都道府県すべて一致（合計2,481）
- 作られる県別ページ：docs/pref_01.html〜pref_47.html の47ファイル。グラフは47×8−5＝371枚（disaster_groups がない5県の分を除く）、CSV は47×8＝376
- docs/index.html は変わらない（git status に出ない）
- 公開前チェック「問題なし」、pytest 全件合格（今の189件＋追加分）、pyflakes 0件、LF

## 報告に貼るもの
- 上の4の各コマンドの出力（画面に出た文をそのまま。ユーザー名を含む絶対パスは `<プロジェクト>` に置き換える）
- 変更した2ファイルのバイト数

## 完了後
- 自己チェックを行い、docs/dev/reports/M14-01_report.md に報告を書く。
