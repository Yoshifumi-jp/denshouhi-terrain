# 指示書 M16-02（実装・地形分類（地域版）の県別・全国の集計）　作成日：2026-10-16

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」「書き出すテキストは LF」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・data/processed の既存ファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・run_region_batch.py・update.py・summarize_national.py・count_missing.py は実行しない（テストからの呼び出しは可）。
実行してよいのは、下の「やること」6〜8 のコマンドだけです。ネットへの問い合わせは発生しません。

## 目的（このテーマ1つ）
計画書 版12 の M16「県別の地域版集計と、全国の『災害種別×地域版の地形分類』（碑と比較地点、全碑と移転碑を除く）を output/ に出力」として、
全国の本番実行（2026-10-16 完了）で作った data/processed/landform_region_XX.csv・landform_region_points_XX.csv を読み、
集計表を **新しいファイル** に書く新しいプログラム `src/summarize_region.py` を作る。
既存の集計（summarize.py・summarize_national.py）とその出力は一切変えない（詳細版と地域版は混ぜない方針）。
count_missing.py・update_all.py・update.py への組み込みは次の指示書（M16-03 以降）で行うので、今回は触らない。

## 対象ファイル
- 新しく作る：src/summarize_region.py、tests/test_summarize_region.py、docs/dev/reports/M16-02_report.md
- 実行で新しくできる：output/landform_region_XX.csv（47ファイル）、output/landform_region_all.csv
- 変えないもの：上記以外のすべて（src/ と tests/ の既存ファイル、data/processed の全ファイル、output/ の既存ファイル）

## やること
1. src/summarize_region.py を作る。作りは src/summarize_national.py にならい、次を import して使う（自分で同じ処理を書き直さない）：
   `PREFECTURES`（prefectures）、`extract_relocated`・`DISASTER_TYPES`（summarize）。
   CSV の書き出しは summarize_national.py の write_with_notes を**使わない**（pandas の to_csv が Windows では表の部分を CRLF で書き、注の行だけ LF になるため）。
   同じ形の関数を summarize_region.py の中に作り、`df.to_csv(f, index=False, lineterminator="\n")` で表を書いてから注の行を `\n` 付きで書く。
   import は既存と同じく `try: from src.xxx import ... / except ImportError: from xxx import ...` の形。
   - `main(args=None, base_dir=None)`。引数：`--pref`（省略可。01〜47 のカンマ区切り、または all。省略時は all）。県コードの解釈は load_monuments.parse_pref_arg を使い、不正なときはそのエラー文を出して終了コード 1
   - 入力（県ごと、data/processed/）：monuments_XX.csv、points_XX.csv、landform_region_XX.csv、landform_region_points_XX.csv。
     ID 系の列（ID・元の碑ID）と `地域版_コード` は文字列で読む。monuments／points に `地域版_地形分類名`・`地域版_コード`・`地域版_状態` を ID で左結合する
   - 入力の確認：対象の県で4ファイルのどれかがない県があれば、`エラー：ファイルが足りない県があります：県名（XX）、県名（YY）` と
     `先に実行してください：python src/run_region_batch.py --pref "XX,YY"` を出して終了コード 1（何も書き出さない）
2. 集計の決まり（県別・全国とも同じ関数で作る）
   - 数えるのは `地域版_状態` が「取得済（地域版）」の地点だけ。「取得済（広域版）」「データなし」「取得不可」は数えない（広域版は分類の細かさが違うため混ぜない）
   - 範囲は「全碑」「移転碑を除く」の2つ。移転碑は extract_relocated（伝承内容に「移転」「移設」）で決め、比較地点は `元の碑ID` で除く（summarize_national.py の build_summary_tables と同じ）。県別ファイルでは、その県の碑だけで extract_relocated を使う
   - 災害種別は「全種別」＋ DISASTER_TYPES の7つ（表示名は先頭の「種別_」を取る）。碑・比較地点とも、それぞれの `種別_xxx` 列が 1 の行
   - 列：`範囲,災害種別,地形分類名,地形分類コード,碑_件数,碑_割合,比較地点_件数,比較地点_割合`。割合はそのグループで数えた地点（取得済（地域版））に対する割合で、小数3桁に丸める。分母が 0 なら 0
   - 行の並び：範囲（全碑→移転碑を除く）→ 災害種別（全種別→洪水→地震→津波→土砂災害→高潮→火山災害→その他）→ 地形分類。
     地形分類は、**そのファイル（県または全国）に1回でも出てくる分類をすべて、どのグループにも同じ順で出す**（0件の行も出す）。
     順番は「全碑・全種別の比較地点の件数の多い順 → 同数なら全碑・全種別の碑の件数の多い順 → 同数ならコードの数値の小さい順」
   - 注の行（表の後ろに書く。この文言・この順）：
     ```
     注：1基が複数の災害種別を持つため、種別ごとの合計は全種別の碑の数より多くなる場合があります。
     注：地形分類（自然地形）の地域版（中分類）で値が取れた地点だけを数えています。詳細版の表（landform_XX.csv・landform_all.csv）とは分類の細かさが違うため、別の表にしています。
     注：数えていない地点：データなし 碑 a・比較地点 b、広域版で補った地点 碑 c・比較地点 d、取得不可 碑 e・比較地点 f
     出典：国土地理院 地形分類（自然地形）を加工して作成
     ```
     （a〜f はそのファイルの「全碑」の範囲での件数。3桁区切りなし）
3. 出力（output/、UTF-8 BOM 付き、**改行 LF**）
   - `--pref` で指定した各県：output/landform_region_XX.csv
   - `--pref` が all（または省略）のときだけ、47都道府県を合わせた output/landform_region_all.csv も書く（全国の移転碑は47県をつないだ碑で extract_relocated）
4. 画面の表示（この順・この文言。数は3桁区切り、割合は小数3桁）
   - all のとき：
     ```
     地形分類（地域版）の集計：47都道府県
     碑：全碑 2,481基／移転碑を除く 2,379基　比較地点：全碑 12,395点／移転碑を除く 11,885点
     地域版で数えた地点（全碑）：碑 2,476基／比較地点 12,277点
     数えていない地点（全碑）：データなし 碑 5・比較地点 118、広域版 碑 0・比較地点 0、取得不可 碑 0・比較地点 0
     全碑・全種別の上位5分類（碑の割合／比較地点の割合）
       低地：0.535／0.353
       山地：0.191／0.332
       丘陵・小起伏地：0.080／0.108
       台地・段丘：0.107／0.094
       火山麓地形：0.037／0.043
     出力：
       output/landform_region_XX.csv（47ファイル）
       output/landform_region_all.csv
     ```
     （上位5分類は、ファイルの並び順の先頭5つ）
   - 県を指定したとき（例 `--pref 36`）：1行目を `地形分類（地域版）の集計：徳島県（36）`（複数県なら `地形分類（地域版）の集計：2都道府県`）にし、2〜9行目は対象の県を合わせた数（上位5分類は、1県ならその県のファイルの先頭5つ、複数県なら表示しない）、
     出力は `  output/landform_region_36.csv` のように県ごとに1行（landform_region_all.csv は書かない・表示しない）
5. コメントは日本語。ファイルの先頭に「何をするプログラムか」「詳細版の集計とは混ぜない理由」を書く。
6. tests/test_summarize_region.py を作り、`python -m pytest -q` を実行する（tmp_path に偽の data/processed を作る。ネットに出ない）。最低限：
   (a) 「取得済（地域版）」だけを数え、広域版・データなし・取得不可を数えない（注の行の a〜f の件数も確かめる）
   (b) 移転碑（伝承内容に「移設」）とその比較地点が「移転碑を除く」から除かれる
   (c) 災害種別の絞り込み（1基が2種別を持つ例）
   (d) どのグループにも同じ分類が同じ順で出る（0件の行も出る）。並び順の同数の決め方（比較地点 → 碑 → コード）
   (e) 割合の分母が 0 のとき 0
   (f) 入力ファイルが足りない県があると、エラー文2行・終了コード 1・何も書き出さない
   (g) 出力が BOM 付き・LF・列名と順番が指示どおり
   (h) 実データでの照合（data/processed に47県の4ファイルがそろっているときだけ動かし、なければ pytest.skip）：
       全国の「全碑・全種別」で、低地 碑1,325・比較地点4,331、山地 碑472・比較地点4,078、湖 碑1・比較地点50、カルスト地形 碑2・比較地点5。
       分類は12種、行数は 2×8×12＝192（注の行を除く）。徳島（36）の「全碑・全種別」は 山地 24・221、低地 44・112、丘陵・小起伏地 0・8、台地・段丘 1・2 の4行
       （このテストは本物の data/processed を読むだけで、output/ には書かない。base_dir に tmp_path を渡し、data/processed だけ本物を読む作りにするか、集計関数を直接呼ぶ）
7. `python src/summarize_region.py --pref 36` を実行する（徳島だけ）。
8. `python src/summarize_region.py` を実行する（全国）。
9. 完了後、自己チェックを行い、docs/dev/reports/M16-02_report.md に報告を書く（7・8 の画面の表示は全文をそのまま貼る）。

## やらないこと
- summarize.py・summarize_national.py・count_missing.py・update.py・update_all.py・build_site.py・build_national.py・make_national_pdf.py の変更（ページ・PDF への反映は M17）
- data/processed のファイルの書き換え、ネットへの問い合わせ
- 既存の output/ のファイル（landform_XX.csv・landform_all.csv・*_all.csv・missing_counts.csv など）の書き換え

## 完成の条件（既知の答え。Claude が 2026-10-16 に同じデータで計算した値）
- 8 の表示が、上の「画面の表示」の例と数字まで一致する（碑 2,481・移転碑を除く 2,379、比較地点 12,395・11,885、数えた地点 2,476・12,277、データなし 5・118、広域版 0・0、取得不可 0・0、上位5分類の割合）
- output/landform_region_all.csv：注の行を除いて192行、12分類（低地・山地・丘陵・小起伏地・台地・段丘・火山麓地形・火山地形（やや不明瞭）・火山地形（明瞭）・火山性丘陵・砂丘・残丘状地形・湖・カルスト地形の順）
- 全国の災害種別ごとの「全碑」で数えた碑の数と、最も多い分類（碑の割合）：洪水 1,112基 低地 0.650／地震 885基 低地 0.472／津波 593基 低地 0.432／土砂災害 629基 低地 0.347（2位 山地 0.343）／高潮 137基 低地 0.854／火山災害 82基 火山麓地形 0.341／その他 118基 低地 0.441
- 7 の表示：碑 71基（移転碑を除く 69基）、比較地点 349点、数えた地点 碑 69基／比較地点 343点、データなし 碑 2・比較地点 6。output/landform_region_36.csv は注の行を除いて 2×8×4＝64行
- 県別：岩手（03）の「全碑・全種別」は 山地 46・360、丘陵・小起伏地 42・243、低地 62・115、台地・段丘 13・80（比較地点の多い順）。北海道（01）は8分類
- 自動テスト：249件＋今回足したテスト関数の数がすべて合格（報告に「249＋n＝合計」を書く）
- 変わってはいけないファイル：docs/dev/v3_hashes.md の100ファイル、data/processed/landform_region_* 94ファイル、output/missing_counts.csv・output/region_batch_log.csv が変わらない。`git status --short` に出るのは、新しく作ったファイル（src/summarize_region.py、tests/test_summarize_region.py、output/landform_region_*.csv 48ファイル、報告書）と、作業前から変更ありの output/region_batch_log.csv だけ
- 新しいファイルに \r（CR）が含まれない

## 完了後
- 自己チェックを行い、docs/dev/reports/M16-02_report.md に報告を書く（変更したファイルとバイト数の一覧、7・8 の表示の全文、pytest の結果の最後の行をそのまま）。
