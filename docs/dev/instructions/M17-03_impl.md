# 指示書 M17-03（実装）　作成日：2026-10-16

最初に AGENTS.md を読んでから作業してください。

## 目的（このテーマ1つ）
全国の印刷用PDF（src/make_national_pdf.py）に、地形分類（地域版）の表のページを足す。3ページ目はすでに3つの表で埋まっているため、**新しい4ページ目**にし、PDF は6ページ → **7ページ**になる。

## 対象ファイル
- src/make_national_pdf.py（変更）
- src/build_national.py（「A4・6ページ」の文言2か所だけ変更）
- tests/test_make_national_pdf.py（既存テストは「6」を「7」にする期待値の書き換えだけ。テスト関数を2つ追加）

## やること（手順）

### 1. 新しいページを作る関数
`make_page_region(output_dir, mon_reg_uncounted, pt_reg_uncounted, latest_date)` を make_page_3 の後に新設し、fig を返す。
- 題名：`地形分類（地域版・全碑・全種別）`（今の make_page_3 の表題と同じ fontsize=12・bold、位置 0.08, 0.955）
- 表：`output/landform_region_all.csv` の 範囲＝全碑・災害種別＝全種別 の行。列・並び・割合の書き方・表の見た目は make_page_3 の地形分類の表（表3）と同じ（5列、碑の数の多い順・同数は名前順、×100 で小数1桁＋%、見出し行の色、1列目左寄せ、交互の色）。表の置き場所は `fig.add_axes([0.08, Y, 0.84, H])` で、1行の高さが表3と同じくらいになるよう H を決める（12行＋見出し。目安 Y=0.60・H=0.33。はみ出さなければ調整してよい）。
- 表の下の注（fontsize=8、左 0.08）を2行：
  - `地域版で値が取れなかった碑 <A>基・まわりの地点 <B>点は、割合の計算から除いています。`
  - `地域版は詳細版より分類が粗い（中分類12種）ため、碑とまわりの地点（100m〜2,000m）が同じ分類になりやすく、差が出にくくなります。`
- `landform_region_all.csv` が無いときは、表と注を出さず、題名の下に `地域版の集計（landform_region_all.csv）がないため、表はありません。` を出す（ページ数は7のまま）。
- フッターは `draw_footer(fig, 4, latest_date)`。
- A・B の数え方は build_national.py（M17-02）と同じ：A＝47都道府県の `data_dir/landform_region_XX.csv` で 地域版_状態 が「取得済（地域版）」でない碑の数（ファイルの無い県は monuments_XX.csv の碑の数を足す）、B＝`landform_region_points_XX.csv` の同じ条件の比較地点の数。make_national_pdf の中で数える（build_national から関数を import して使ってもよい。build_national の動きは変えない）。

### 2. ページ番号と目次
1. `draw_footer` の `／6` を `／7` にする。
2. 今の4・5・6ページを5・6・7ページにずらす（make_page_4〜6 の draw_footer の番号を 5・6・7 にする。関数名は変えなくてよい）。PdfPages に入れる順番：1、2、3、地域版、旧4、旧5、旧6。
3. 1ページ目の目次を次の6行にする（行の間隔は今と同じ 0.028。最後の行がフッターに重ならないことを確かめる）：
   ```
   2ページ　都道府県別の件数
   3ページ　碑とまわりの比較・ハザード・地形分類
   4ページ　地形分類（地域版）
   5ページ　年代別の碑の数
   6ページ　都道府県別の碑の数（グラフ）
   7ページ　出典・ご利用上の注意
   ```
4. make_national_pdf の docstring の「6ページ」を「7ページ」にする。

### 3. 出典・ご利用上の注意（7ページ）
「地形分類（自然地形）のデータは整備された地域が限られ…」の注意の直後に、全国ページ（M17-02）と同じ文を1つ足す：
`地形分類（地域版）は、詳細版のない地域も含めて全国の碑に付けたものです（値が取れなかった碑 <A>基）。詳細版とは分類の細かさが違うため、別の列・別の表にしています。`

### 4. まとめ表示
「ページ数：」の行の直後に1行足す：
`地形分類（地域版）の表：<行数>行（値が取れなかった碑 <A>基・まわりの地点 <B>点）`
（表が無いときは 行数 0）

### 5. build_national.py
`印刷用PDF（A4・6ページ）` の2か所（658行付近・802行付近）の「6」を「7」にするだけ。ほかは変えない。

### 6. テスト
- tests/test_make_national_pdf.py の既存テストは、ページ数の期待値 6 を 7 にする（戻り値・/Type /Page の数・/MediaBox の回数・実データのテスト、と docstring・コメントの「6」）。それ以外は変えない。
- 追加2つ：
  - `test_page_region_table`：一時フォルダに小さな landform_region_all.csv（全碑・全種別の3行＋他の範囲の行）を置き、`make_page_region` の戻り値の fig から表（`fig.axes` の table）のセルの文字を取り出し、並び（碑の数の多い順）・割合（例 0.535 → `53.5%`）・見出しを確かめる。fig.texts に題名と注（A・B の数）がある。
  - `test_page_region_missing`：landform_region_all.csv を置かない → 表が無く、`表はありません` の文がある。
- 合計 **273 passed**（今の271＋2）。

### 7. 実行して確かめる
1. `python -m pytest -q` → 273 passed
2. `python src/make_national_pdf.py` → 表示をそのまま貼る
3. `python src/build_national.py` → 表示をそのまま貼る（PDF を docs にコピーし、リンクの文言を更新するため）

## 既知の答え（Claude が手元のデータから計算）
- make_national_pdf のまとめ表示：`ページ数：7（A4 縦）`、`地形分類（地域版）の表：12行（値が取れなかった碑 5基・まわりの地点 118点）`、碑 2,481基
- 4ページの表（並び・碑の数・碑の割合・まわりの数・まわりの割合）は全国ページ（M17-02）の地域版の表と同じ12行：低地 1325 53.5% 4331 35.3% ／ … ／ 湖 1 0.0% 50 0.4%
- build_national のまとめ表示は M17-02 と同じ（作成したファイル 11、地域版 12区分＋データなし 5基、集計表 12行）。docs/index.html の差分は「A4・6ページ」→「A4・7ページ」の2か所だけ
- docs/national_report.pdf は output/national_report.pdf と同一

## やらないこと
- 1〜3ページ・旧4〜6ページの中身（表・グラフ・文）を変えない（ページ番号・目次・注意1行の追加だけ）。
- check_public.py・update.py・update_all.py・make_map.py・build_site.py は変えない。build_national.py は文言2か所だけ。
- data/ と output/ の CSV・図を変えない（output/national_report.pdf と docs/ の書き出しだけ）。

## 完成の条件
- 既知の答えと一致する。7ページ（A4 縦）で、目次の最後の行がフッターに重ならず、4ページの表と注が枠からはみ出さない（PDF を開いて目で確かめ、報告に書く）。
- pytest 273 passed、問題タブのエラー0件。テキストは LF。

## 完了後
- 自己チェックを行い、docs/dev/reports/M17-03_report.md に報告を書く。まとめ表示・pytest の結果は画面に出た文をそのまま貼る。
