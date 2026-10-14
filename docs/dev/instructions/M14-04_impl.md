# 指示書 M14-04（実装・印刷用PDF）　作成日：2026-10-14

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る。言い換え・要約・記憶からの作り直しをしない」）。
作業前に、エディタのタブをすべて閉じてから始めてください。作業中に docs/dev/status.md・docs/dev/01_plan.md・output/ 配下（今回作る PDF を除く）・data/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。`python src/run_batch.py ...`（--check-only を除く）・`python src/update.py ...`・`python src/build_site.py ...`・`python src/summarize_national.py` の実行はしない。

## 目的（このテーマ1つ）
計画書 M14（版11.6）の「印刷用PDF（A4）」を作る。新しいプログラム `src/make_national_pdf.py` で、全国の集計を A4 縦・6ページの PDF `output/national_report.pdf` にまとめる。あわせて、全国ページ（src/build_national.py）がこの PDF を docs/ にコピーし、ダウンロード欄にリンクを1行出すようにする。
作り方は matplotlib（.venv に入っている。新しい部品は入れない）の PdfPages、フォントは既存の `set_jp_font()`（src/summarize.py。Yu Gothic）。

## 対象ファイル
- 新しく作る：src/make_national_pdf.py、tests/test_make_national_pdf.py、docs/dev/reports/M14-04_report.md
- 変更する：src/build_national.py（PDF のコピーとリンクだけ）、tests/test_build_national.py（偽のデータに PDF を足す・作成数を10に）
- 実行で作られる・変わる：output/national_report.pdf（新規）、docs/national_report.pdf（新規）、docs/index.html（リンク1行だけ増える）
- 変えないもの：上記以外のすべてのファイル

## 使うデータ（読むだけ。M14-03 と同じ）
output/pref_counts_all.csv・summary_all.csv・hazard_summary_all.csv・landform_all.csv・relocated_all.csv、output/fig/years_all.png・pref_counts_all.png、data/processed/monuments_XX.csv・landform_XX.csv・landform_points_XX.csv（47県）。
数の求め方は M14-03 と同じにする。そのために src/build_national.py の `TILE_LAYOUT`・`COLOR_CLASSES`・`short_name`・`get_color_info`・`load_monument_list`・`landform_options` は import して使う（コピーしない）。

## PDF の中身（A4 縦：figsize=(8.27, 11.69) インチ、6ページ）
すべてのページの下に、小さい文字（8pt、灰色）で `自然災害伝承碑と地形（全国）　伝承碑データ取得日：2026-09-24　<ページ>／6` を入れる。文字は 9〜11pt を基本にする（見出しは 14〜16pt）。長い文は textwrap などで折り返し、ページからはみ出さないようにする（目安：10pt で1行44字程度）。

1. **1ページ：表紙と色分け地図**
   - 題名「自然災害伝承碑と地形（全国）」、その下に `伝承碑データ取得日：2026-09-24　碑：2,481基（47都道府県）　比較地点：12,395点`（比較地点は pref_counts_all の全国の行の 比較地点_数）
   - 説明（全国ページの最初の段落と同じ文）
   - 色分け地図（碑の数）：TILE_LAYOUT の位置に四角（matplotlib の Rectangle）を並べ、中に short_name と碑の数の2行。色は COLOR_CLASSES（get_color_info）。凡例は6区分の色見本と表示名、見出し「碑の数（単位：基）」
   - 目次（2ページ 都道府県別の件数／3ページ 碑とまわりの比較・ハザード・地形分類／4ページ 年代別の碑の数／5ページ 都道府県別の碑の数（グラフ）／6ページ 出典・ご利用上の注意）
2. **2ページ：都道府県別の件数**：全国ページの件数表と同じ列から「地図」の列を除いたもの（都道府県／碑の数／移転碑／洪水／地震／津波／土砂災害／高潮／火山災害／その他）。47県＋全国の48行を1ページに収める（ax.table、fontsize 7〜8 を `auto_set_font_size(False)` で固定）。表の下に「1基が複数の災害種別を持つため、種別ごとの合計は碑の数より多くなります。」
3. **3ページ：3つの表**：全国ページと同じ3つの表（碑とまわりの比較／ハザードマップの想定区域との重なり／地形分類）を上から順に。値の書き方も全国ページと同じ（例：`28%`、`35%（860／2481基）`、`29.1%`）。地形分類の表の下に `地形分類のデータがない碑 929基・まわりの地点 4,890点は、割合の計算から除いています。`、ハザードの表の下に「想定区域との重なりを示すもので、危険度の判定ではありません。」
4. **4ページ**：見出し「災害の発生年代と碑の建立年代」と output/fig/years_all.png（matplotlib.image.imread で読み、軸を消して縦横比を保ったまま幅いっぱいに）
5. **5ページ**：見出し「都道府県別の碑の数」と output/fig/pref_counts_all.png（同じく縦横比を保ち、ページに収まる大きさで）
6. **6ページ：出典・ご利用上の注意**：全国ページの「出典」と「ご利用上の注意」と同じ文を箇条書き（「・」で始める）。ハザードの注意と県ごとの注記（「徳島県：…」）は別の項目に分けてよい。URL は文字で出す（https://www.gsi.go.jp/bousaichiri/denshouhi.html と HAZARD_SOURCE_URL）

## プログラムの作り
1. src/make_national_pdf.py
   - `make_national_pdf(output_dir=None, data_dir=None, out_path=None, quiet=False)`：必要なファイルがそろっているか確かめ（足りなければ `エラー：ファイルが足りません：<ファイル名を「、」でつなぐ。最大10個、超えたら「ほか N 個」>` と `先に実行してください：python src/summarize_national.py` を出して終了コード1、何も書かない）、PDF を書いて、ページ数を返す
   - PdfPages の metadata は `{'Title': '自然災害伝承碑と地形（全国）', 'Author': None, 'Creator': None, 'Producer': None, 'CreationDate': None}`（作成者名・作成日時・作った道具の名前を PDF に残さない）
   - `pdf.fonttype` などフォントの埋め込み方の設定は変えない（matplotlib の既定のまま）
   - 表示（この文のとおり。quiet=True のときは出さない）：
```
印刷用PDF：output/national_report.pdf
ページ数：6（A4 縦）
碑：2,481基（47都道府県）　伝承碑データ取得日：2026-09-24
ファイルのサイズ：<KB、小数1桁> KB
```
   - 日本語フォントが見つからないとき（set_jp_font の警告が出たとき）も止めずに続けてよい（警告はそのまま画面に出る）
2. src/build_national.py（この2点だけ）
   - `required_files` に `output/national_report.pdf` を足し、`build_national()` で docs/national_report.pdf にコピーして created_files に加える（作成したファイルは 9→10）。足りないときの「先に実行してください」の文は `先に実行してください：python src/summarize_national.py、python src/make_national_pdf.py と python src/build_site.py --pref all` に変える
   - 「データのダウンロード」の `<ul>` の先頭に `<li><a href="national_report.pdf">印刷用PDF（A4・6ページ）</a></li>` を1行足す
   - **これ以外の index.html の中身は変えない**（git diff docs/index.html が1行の追加だけになること）

## テスト
1. tests/test_make_national_pdf.py
   - 足りないファイルがあるとき：tmp_path で呼び、終了コード1・何も書かない
   - 偽のデータ（tmp_path に2県分。test_build_national.py の偽のデータの作り方を参考に。グラフは matplotlib で小さな PNG を実際に作る）で PDF を作り、(a) 戻り値が6 (b) ファイルが `%PDF` で始まる (c) バイト列の中の `/Type /Page`（`/Type /Pages` を除く）の数が6 (d) `/MediaBox [ 0 0 595.44 841.68 ]` が6回現れる（A4 縦）(e) `Matplotlib` と `CreationDate` の文字が含まれない
   - 実データ（ファイルがなければ skip。**書き込みは tmp_path だけ**）：ページ数6
2. tests/test_build_national.py：偽のデータに national_report.pdf（中身は `%PDF-1.4` の数バイトでよい）を足し、作成数を10に、index.html に `href="national_report.pdf"` があることを確かめる

## 既知の答え
- 1ページ目の数：碑 2,481・比較地点 12,395・取得日 2026-09-24。色分け地図の区分ごとの県の数は M14-03 と同じ（0・1・6・18・15・7）
- 3ページ目の表の値は M14-03 の既知の答え（全国ページの表）と同じ
- PDF の大きさは推測ですが 0.5〜3MB（グラフ画像2枚で約250KB＋日本語フォントの文字の形）

## やらないこと
- 更新コマンド（M14-05）、公開前チェックの対象拡大と公開（M14-06）
- 全国ページの見た目・表・注意書きの変更（リンク1行の追加を除く）
- 新しいライブラリ（reportlab など）の追加、フォントファイルの同梱

## 完成の条件
- `python src/make_national_pdf.py` の表示が上の4行のとおり（サイズの値を除く）
- `python src/build_national.py` の表示が M14-03 と同じ7行で、「作成したファイル：10」に変わるだけ（サイズの値は少し増える）
- PDF を開くと A4 縦の6ページで、日本語が文字化けせず、表・地図・グラフがページからはみ出していない
- git diff docs/index.html はリンク1行の追加だけ
- pytest 全件合格（今の203件＋追加分）、pyflakes 0件、LF

## 報告に貼るもの（画面に出た文をそのまま。ユーザー名を含む絶対パスは `<プロジェクト>` に置き換える）
- `python src/make_national_pdf.py`
- `python src/build_national.py`
- `git status --short` と `git diff --stat docs/index.html` と `git diff -U0 docs/index.html`
- `python -m pytest -q`（最後の行）、`python -m pyflakes src/make_national_pdf.py src/build_national.py tests/test_make_national_pdf.py tests/test_build_national.py`
- 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/make_national_pdf.py','src/build_national.py','tests/test_make_national_pdf.py','tests/test_build_national.py','docs/index.html']]"`（すべて False）
- PDF を PDF ビューアー（ブラウザでも可）で開いたときのページ数と、各ページで見えたものを1行ずつ（実際に開いて見た場合だけ書く。開けなかったときはそう書く）
- 作成・変更したファイルのバイト数

## 完了後
- 自己チェックを行い、docs/dev/reports/M14-04_report.md に報告を書く。
