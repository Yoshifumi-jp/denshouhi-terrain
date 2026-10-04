# 指示書 M8-07（修正・地図のハザード重ね表示）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「作業用のスクリプトを作らない」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください。

## 目的（このテーマ1つ）
M8-06 で作った地図（src/make_map.py）のハザード重ね表示とポップアップを、指示書 M8-06 の 2章どおりに直し、テストで確かめる。
**公開ページ（src/build_site.py）は M8-08 で直すので、この指示書では触れない。**

## 対象ファイル
- 変更：src/make_map.py、tests/test_make_map.py
- 生成物：output/map_36.html（docs/map_36.html は M8-08 で作り直すので触れない）
- 変えないもの：src/build_site.py、src/update.py、src/hazard_layers.py、src/summarize_hazard.py、src/add_hazard.py、tests/ の他のファイル、data/、output/hazard_summary_36.csv
- docs/dev/ の中は報告書の追加以外は触れない

## 不具合の内容（M8_review-6 より）
| No | 起きていること | 本来の動き |
|---|---|---|
| 2 | 洪水・津波・高潮の TileLayer に `overlay=True` がなく、LayerControl の「背景地図」（ラジオボタン）に入った。選ぶと淡色地図と入れ替わる | 4つとも「重ねる地図」（チェックボックス）に入り、淡色地図の上に重なる。最初は表示しない。※指示書 M8-06 に overlay=True を書かなかった Claude の不足も原因 |
| 8 | build_map で hazard_lines を作る条件が入り組んでいて、洪水_状態だけが空の碑ではポップアップに4行が出ない | すべての碑で `hazard_lines = make_hazard_lines(row)` を呼ぶ（列がない・空は「データなし」になる） |
| 9 | 凡例の HAZARD_DATA_NOTES の文をエスケープしていない。ハザード情報取得日を build_map の中で PROJECT_ROOT のファイルから読み直している | 文は html.escape する。取得日は load_data で読んだ hazard_{pref}.csv から取る（下の「やること」2） |
| 10 | src/make_map.py の改行コードがファイル全体で CRLF に変わった | LF に戻す（M8-06 前と同じ） |

## やること
1. 洪水・津波・高潮の3つの folium.TileLayer に `overlay=True` と `control=True` を付ける（show=False・opacity・max_native_zoom・max_zoom・attr・name はそのまま）。土砂の FeatureGroup はそのまま
2. load_data で hazard_{pref}.csv を結合するとき、「取得日」列を落とさず `ハザード取得日` に名前を変えて結合する（碑名・緯度・経度は今までどおり落とす）。build_map の凡例の「ハザード情報取得日」は mon_df['ハザード取得日'] の空でない値の最も新しい日付にする（列がない・すべて空なら空文字）。build_map の中の hazard_file の読み直しは消す
3. build_map のポップアップ部分を `hazard_lines = make_hazard_lines(row)` の1行にする（if/elif を消す）
4. 凡例の HAZARD_DATA_NOTES の各文を `html.escape(note)` してから <p> に入れる
5. 改行コードを LF にする（VS Code 右下の「CRLF」を「LF」にして保存）

## やらないこと
- make_hazard_lines の文言・判定を変える（M8-06 のままで正しい）
- 碑の色分け・既存のポップアップ項目・凡例の既存の文を変える
- 作業用のスクリプトを作る

## 自動テスト（tests/test_make_map.py。偽データで確かめる。実データのテストは実データがないとき skip）
既存のテストは消さない。次を**新しいテスト関数として**加える（関数名の例を付けた。1項目＝1関数）。
- a `test_make_hazard_lines_table`：指示書 M8-06 2-3 の4つの assert をそのまま入れる
- b `test_build_popup_hazard`：
  ```python
  html_ = make_map.build_popup_html({'碑名': 'A', 'ID': '01'}, '比較地点なし', False, '', ['洪水（想定最大規模）：区域外', '<script>x</script>', '高潮：区域外', '土砂災害：区域外'])
  assert 'ハザードマップの想定区域との重なり' in html_
  assert '<li>洪水（想定最大規模）：区域外</li>' in html_
  assert '&lt;script&gt;x&lt;/script&gt;' in html_ and '<script>x</script>' not in html_
  html_none = make_map.build_popup_html({'碑名': 'A', 'ID': '01'}, '比較地点なし', False, '')
  assert 'ハザードマップの想定区域との重なり' not in html_none
  ```
- c `test_hazard_layers_overlay`：偽の mon_df（2基。片方は洪水_状態だけ NaN で他は値あり＝No.8 の場合）で `m, _ = make_map.build_map(mon_df, None, '99')` を作り（`monkeypatch.setitem(make_map.PREFECTURES, '99', 'テスト県')`。mon_df には既存の test_main_integration と同じ列＋ハザードの列＋ハザード取得日 を入れる。TILE_URL・LAYERS は src.hazard_layers から import）、
  ```python
  import folium
  children = list(m._children.values())
  hz = [c for c in children if getattr(c, 'layer_name', '').startswith('ハザード：')]
  assert [c.layer_name for c in hz] == ['ハザード：洪水（想定最大規模）', 'ハザード：津波', 'ハザード：高潮', 'ハザード：土砂災害警戒区域']
  assert all(c.overlay and c.control and not c.show for c in hz)
  base = [c for c in children if isinstance(c, folium.TileLayer) and not c.overlay]
  assert [c.layer_name for c in base] == ['地理院タイル（淡色地図）']
  dosha_tiles = [c for c in hz[3]._children.values() if isinstance(c, folium.TileLayer)]
  assert sorted(c.tiles for c in dosha_tiles) == sorted(TILE_URL.replace('{path}', LAYERS[k]) for k in ['doseki', 'kyukei', 'jisuberi'])
  assert all(not c.control for c in dosha_tiles)
  assert [c.tiles for c in hz[:3]] == [TILE_URL.replace('{path}', LAYERS[k]) for k in ['flood', 'tsunami', 'hightide']]
  html_ = m.get_root().render()
  assert 'ハザード情報取得日：2026-10-04' in html_          # 偽データの ハザード取得日 に '2026-10-01' と '2026-10-04' を入れる
  assert '洪水（想定最大規模）：データなし' in html_         # 洪水_状態だけ NaN の碑のポップアップ
  ```
  ※ folium の属性名（layer_name・overlay・control・show・tiles）が違って動かない場合は、推測で書き換えず報告書の「確認したいこと」に書いて止まる
- d `test_missing_hazard_file`：既存の test_missing_files の確認を強める。出力に `hazard_98.csv` と `python src/add_hazard.py --pref 98` の両方が出て、SystemExit のコードが 1
- e `test_hazard_notes_escaped`：monkeypatch で `make_map.HAZARD_DATA_NOTES` に `{'99': ['<b>注</b>']}` を入れて build_map → 出力に `&lt;b&gt;注&lt;/b&gt;` があり `<b>注</b>` がない
- g `test_real_hazard_popup`（実データ。PROJECT_ROOT 基準で data/processed/hazard_36.csv がなければ skip）：`mon_df, pt_df = make_map.load_data('36')` の3基に make_hazard_lines を当て、指示書 M8-06 8章 g の辞書と一致。あわせて `mon_df['ハザード取得日'].dropna().max() == '2026-10-04'`

**テストが本当に誤りを見つけるか（自分で確かめて報告に書く）**：やること1の `overlay=True` を一時的に外すと c が失敗すること、やること3を元の if/elif に戻すと c が失敗することを確かめ、確かめたら元に戻す（元に戻す前後のファイルのバイト数を報告に書く）。作業用のスクリプトは使わず、エディタで直接書き換える。

## 完成の条件
- pytest がすべて合格。件数は「M8-06 時点の 121件＋このテストで増えた関数の数」と一致
- `.\.venv\Scripts\python.exe src\make_map.py --pref 36` を実行し、output/map_36.html を開くと、右上の切り替えの**下の段（チェックボックス）**に「ハザード：…」が4つ並び、上の段（ラジオボタン）は「地理院タイル（淡色地図）」だけ。4つを同時にオンにでき、淡色地図の上に色が重なる
- src/make_map.py の改行コードが LF
- 問題タブのエラー0件

## 完了後
docs/dev/reports/M8-07_report.md に、次を必ず書く（AGENTS.md の書式）
- make_map.py の実行で画面に出た文を**そのまま**全部（言い換えない）
- pytest の最後の行をそのまま（例「123 passed in 12.34s」）と、テスト関数の数の内訳（ファイルごと）
- 「テストが本当に誤りを見つけるか」の結果（どこを外して、どのテストが失敗したか）
- 変更したファイルとバイト数、改行コード
- 実際に行っていないことを「行った」と書かない（M8-06 の報告では「index.html に表が表示」「update.py でエラーなく終了」と実際と違う記載があった）
