# 指示書 M8-06（実装・ハザードマップとの関係を地図・公開ページ・更新コマンドに組み込む）　作成日：2026-10-04

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」「完了報告」「作業用のスクリプトを作らない」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
M8-01〜M8-05 で作った「ハザード区域の判定」（src/add_hazard.py）と「集計表」（src/summarize_hazard.py）の結果を、地図（重ね表示の切り替え・ポップアップ）・公開用ページ（docs/）・更新コマンド（update.py）に組み込み、`python src/update.py` 1回で作り直せるようにする。
GitHub への push・git commit は行わない。

## 対象ファイル
- 変更：src/make_map.py、src/build_site.py、src/update.py、src/hazard_layers.py、src/summarize_hazard.py（7章の軽微のみ）
- 変更：tests/test_make_map.py、tests/test_build_site.py、tests/test_update.py、tests/test_summarize_hazard.py
- 生成物：output/map_36.html、docs/index.html、docs/map_36.html、docs/data/hazard_summary_36.csv
- **変えないもの**：src/add_hazard.py、data/processed/hazard_36.csv・hazard_points_36.csv、output/hazard_summary_36.csv（中身が1バイトも変わらないこと。7章の変更後に summarize_hazard.py を実行しても同じ）
- **docs/dev/ の中は報告書の追加以外は触れない**

## 1. 共通の定数（src/hazard_layers.py）
次の3つを追加する（既存の定数は変えない）。
```python
# 配信タイルのURL（add_hazard.py の default_fetch_func と同じ）
TILE_URL = "https://disaportaldata.gsi.go.jp/raster/{path}/{z}/{x}/{y}.png"

# 出典（ハザードマップポータルサイトのオープンデータの利用条件による）
HAZARD_SOURCE_NAME = "ハザードマップポータルサイト"
HAZARD_SOURCE_URL = "https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html"

# 浸水深3m以上とみなす区分（SHINSUI_LEGEND の「3m〜5m」から後ろ）
SHINSUI_3M_IJOU = [label for _, label in SHINSUI_LEGEND][[label for _, label in SHINSUI_LEGEND].index('3m〜5m'):]

# 県ごとのデータの年次に関する注意（全国展開時に県を追加する）
HAZARD_DATA_NOTES = {
    '36': [
        "津波：徳島県は2025年9月に新しい津波浸水想定を公表しましたが、ハザードマップポータルサイトの配信データは更新日が2023年で、それ以前の想定（平成24年公表）のままとみられます。最新の想定は徳島県のホームページでご確認ください。",
    ],
}
```
- add_hazard.py は変えない（TILE_URL を使うように書き換えない）

## 2. 地図（src/make_map.py）
### 2-1 入力
- 入力に data/processed/hazard_{pref}.csv を加える（碑の ID で結合。碑名・緯度・経度・取得日の列は結合前に落とす）。ファイルがなければ、ファイル名と `python src/add_hazard.py --pref 36` を出して終了コード1（denshou_{pref}.csv の足りないときの出し方に合わせる）

### 2-2 重ね表示の切り替え
- 背景（地理院タイル）の後、碑の FeatureGroup より前に、次の4項目を LayerControl に出す。**最初は表示しない**（show=False）。
  | LayerControl の名前（このとおり） | タイル |
  |---|---|
  | ハザード：洪水（想定最大規模） | LAYERS['flood'] |
  | ハザード：津波 | LAYERS['tsunami'] |
  | ハザード：高潮 | LAYERS['hightide'] |
  | ハザード：土砂災害警戒区域 | LAYERS['doseki']・LAYERS['kyukei']・LAYERS['jisuberi'] の3枚を1つの folium.FeatureGroup にまとめる（3枚の TileLayer は control=False） |
- 各 TileLayer：tiles は TILE_URL の {path} を埋めたもの、`opacity=0.7`、`max_native_zoom=17`、`max_zoom=18`、attr は `<a href="HAZARD_SOURCE_URL" target="_blank" rel="noopener">ハザードマップポータルサイト</a>`
- 土砂の3枚を FeatureGroup にまとめる方法で表示できない場合は、推測で別の方法にせず、報告書の「確認したいこと」に書いて止まる

### 2-3 ポップアップ
- 新しい関数 `make_hazard_lines(row) -> list[str]` を作る（4行。HTML エスケープ前の文字列を返す）。build_popup_html に引数 `hazard_lines=None` を追加し、「地形の診断」の ul の後に次を出す（各行は HTML エスケープ）
  ```
  <p><b>ハザードマップの想定区域との重なり</b>（危険度の判定ではありません）</p>
  <ul><li>（1行目）</li>…<li>（4行目）</li></ul>
  ```
  hazard_lines が None または空のときは何も出さない（既存の呼び出し・テストが壊れないように）
- 各行の作り方（文言はこのとおり）
  | 状態 | 浸水の3種（洪水・津波・高潮） | 土砂 |
  |---|---|---|
  | 区域内 | `洪水（想定最大規模）：区域内（浸水深 0.5m〜3m）`（浸水深が空なら `洪水（想定最大規模）：区域内`） | `土砂災害：区域内（特別警戒区域／土石流・急傾斜地の崩壊）`。土砂_指定予定が「あり」なら末尾に `（指定予定を含む）` |
  | 区域外 | `津波：区域外` | `土砂災害：区域外` |
  | 取得不可 | `高潮：取得不可` | `土砂災害：取得不可` |
  | 列がない・空・NaN | `洪水（想定最大規模）：データなし` | `土砂災害：データなし` |
  - 行の順は 洪水（想定最大規模）→ 津波 → 高潮 → 土砂災害
- テスト用の期待値（コードの形。tests/test_make_map.py にこのまま使う）
  ```python
  row1 = {'洪水_状態': '区域内', '洪水_浸水深': '0.5m〜3m', '津波_状態': '区域内', '津波_浸水深': '0.5m〜3m',
          '高潮_状態': '区域内', '高潮_浸水深': '0.5m〜3m', '土砂_状態': '区域外', '土砂_区分': '', '土砂_現象': '', '土砂_指定予定': ''}
  assert make_hazard_lines(row1) == ['洪水（想定最大規模）：区域内（浸水深 0.5m〜3m）', '津波：区域内（浸水深 0.5m〜3m）',
                                     '高潮：区域内（浸水深 0.5m〜3m）', '土砂災害：区域外']
  row2 = {'洪水_状態': '区域外', '洪水_浸水深': '', '津波_状態': '取得不可', '津波_浸水深': '',
          '高潮_状態': '区域内', '高潮_浸水深': '', '土砂_状態': '区域内', '土砂_区分': '特別警戒区域',
          '土砂_現象': '土石流・急傾斜地の崩壊', '土砂_指定予定': 'あり'}
  assert make_hazard_lines(row2) == ['洪水（想定最大規模）：区域外', '津波：取得不可', '高潮：区域内',
                                     '土砂災害：区域内（特別警戒区域／土石流・急傾斜地の崩壊）（指定予定を含む）']
  row3 = {}   # ハザードの列がない
  assert make_hazard_lines(row3) == ['洪水（想定最大規模）：データなし', '津波：データなし', '高潮：データなし', '土砂災害：データなし']
  row4 = {'洪水_状態': float('nan'), '津波_状態': '区域外', '高潮_状態': '区域外', '土砂_状態': '取得不可'}
  assert make_hazard_lines(row4) == ['洪水（想定最大規模）：データなし', '津波：区域外', '高潮：区域外', '土砂災害：取得不可']
  ```

### 2-4 凡例（左下の枠）
- 「地形との相関を示すもので…」の段落の後に1行追加：`右上の切り替えでハザードマップ（想定区域）を重ねられます。想定区域との重なりを示すもので、危険度の判定ではありません。`
- 「出典・ご利用上の注意」の ul に次の項目を加える（「上記を加工して作成」の前）：
  `ハザード情報：ハザードマップポータルサイト（洪水浸水想定区域（想定最大規模）・津波浸水想定・高潮浸水想定区域・土砂災害警戒区域）`（「ハザードマップポータルサイト」は HAZARD_SOURCE_URL へのリンク）
- 「伝承碑データ取得日」の行の後に `ハザード情報取得日：（hazard_{pref}.csv の取得日の最も新しい日付）`、続けて HAZARD_DATA_NOTES[pref] があれば各文を1段落ずつ
- 国や自治体が作成したかのような表示（「国土交通省のハザードマップ」等）はしない

### 2-5 画面表示
- 既存のまとめ表示の最後（出力ファイル名の前）に1行：`ハザードの重ね表示: 洪水（想定最大規模）、津波、高潮、土砂災害警戒区域`

## 3. 公開用ページ（src/build_site.py）
- 必要なファイルに output/hazard_summary_{pref}.csv と data/processed/hazard_{pref}.csv を加える（足りなければ既存と同じ形でファイル名と `python src/update.py --pref 36` を出して終了コード1）
- output/hazard_summary_{pref}.csv を docs/data/ へコピーし、公開前チェックの対象（paths_to_check）にも加える
- hazard_summary は末尾に「注：…」の2行がある。dtype=str で読み、`範囲 == '全碑' かつ 災害種別 == '全種別'` の行だけを使う（注の行はこれで落ちる）。読む列が足りないときは既存の summary と同じ形でエラー・終了コード1
- 「伝承内容の分析」の節の後、「データのダウンロード」の前に、次の節を追加する
  ```
  <h2>ハザードマップの想定区域との重なり</h2>
  <p>碑と、碑のまわり（100m〜2,000m）の地点が、ハザードマップの想定区域（洪水・津波・高潮・土砂災害）に入っているかを数えました。<b>想定区域との重なりを示すもので、危険度の判定ではありません。</b>地図では右上の切り替えで想定区域を重ねて見られます。</p>
  （表）
  <p>割合は判定できた碑・地点の数に対するものです。移転碑を除いた集計や災害種別ごとの集計は、下の集計表（CSV）にあります。</p>
  <p>ハザード情報取得日：2026-10-04</p>
  （HAZARD_DATA_NOTES[pref] があれば各文を <p> で）
  ```
- 表の列：`ハザード／碑：区域内／まわり：区域内／碑：浸水深3m以上／まわり：浸水深3m以上`
  - 割合は **件数から計算する**（CSV の割合の列を使わない）：`f"{round(区域内 / 数 * 100)}%（{区域内}／{数}基）"`、まわりは「点」。数が0なら「—」
  - 土砂災害の3m以上の列（CSV が空）は「—」
  - 行の順は CSV の順
- 実データでの表の期待値（徳島。テスト g で使う。コードの形）
  ```python
  expected_rows = [
      ['洪水（想定最大規模）', '23%（16／71基）', '15%（53／349点）', '6%（4／71基）', '8%（28／349点）'],
      ['津波', '70%（50／71基）', '21%（75／349点）', '55%（39／71基）', '11%（37／349点）'],
      ['高潮', '34%（24／71基）', '15%（53／349点）', '0%（0／71基）', '0%（1／349点）'],
      ['土砂災害', '31%（22／71基）', '9%（30／349点）', '—', '—'],
  ]
  ```
  ※高潮のまわり 3m以上は 1/349＝0.29% のため「0%（1／349点）」が正しい
- 「データのダウンロード」に `<li><a href="data/hazard_summary_{pref}.csv">ハザードマップの想定区域との重なりの集計</a></li>` を加える
- 「出典」の ul に、地図の凡例と同じ「ハザード情報：…」の項目（リンク付き）と `ハザード情報は同サイトの配信データ（タイル画像）の色を読み取って判定・集計しています（加工して作成）` を加える
- 「ご利用上の注意」に `ハザードマップの想定区域は国・都道府県が公表した想定です。本ページの集計は想定区域との重なりを示すもので、危険度の判定ではありません。防災上の判断には自治体のハザードマップをご利用ください。` を加える

## 4. 更新コマンド（src/update.py）
steps を次の15ステップにする（追加は ★ の3つ。他は順も文言も変えない）
```python
steps = [
    ("データの読み込み", ["load_monuments.py", "--pref", pref_code, "--raw", new_file]),
    ("標高の付与（碑）", ["add_elevation.py", "--pref", pref_code]),
    ("河川・海岸の付与（碑）", ["add_river_coast.py", "--pref", pref_code]),
    ("地形分類の付与（碑）", ["add_landform.py", "--pref", pref_code]),
    ("比較地点の作成", ["make_comparison_points.py", "--pref", pref_code]),
    ("標高の付与（比較地点）", ["add_elevation.py", "--pref", pref_code, "--target", "points"]),
    ("河川・海岸の付与（比較地点）", ["add_river_coast.py", "--pref", pref_code, "--target", "points"]),
    ("地形分類の付与（比較地点）", ["add_landform.py", "--pref", pref_code, "--target", "points"]),
    ("ハザード区域の判定（碑）", ["add_hazard.py", "--pref", pref_code]),                          # ★
    ("ハザード区域の判定（比較地点）", ["add_hazard.py", "--pref", pref_code, "--target", "points"]),  # ★
    ("集計", ["summarize.py", "--pref", pref_code]),
    ("ハザードの集計", ["summarize_hazard.py", "--pref", pref_code]),                               # ★
    ("伝承内容の分析", ["analyze_denshou.py", "--pref", pref_code]),
    ("地図作成", ["make_map.py", "--pref", pref_code]),
    ("公開用ページの作成", ["build_site.py", "--pref", pref_code]),
]
```
- tests/test_update.py の test_k_run_steps_main の expected_cmds を同じ15件に直す（★の3件を同じ位置に足す。他の行は変えない）

## 5. やらないこと
- add_hazard.py・summarize_hazard.py の判定・集計の中身を変える（7章の書き方の整理だけ）
- 碑の色分け・既存のポップアップ項目・既存の表の文言を変える
- update.py を実データで通し実行する（新旧が同じファイルだと止まる＝正しい動き。個別のコマンドで作り直す）
- 作業用のスクリプトを作る（AGENTS.md）

## 6. 実データでの作り直し（ネット接続不要。数分）
次の順に実行し、画面に出た文をそのまま報告に貼る（言い換えない）
```
.\.venv\Scripts\python.exe src\summarize_hazard.py --pref 36
.\.venv\Scripts\python.exe src\make_map.py --pref 36
.\.venv\Scripts\python.exe src\build_site.py --pref 36
.\.venv\Scripts\python.exe -m pytest
```
- summarize_hazard.py の実行後、output/hazard_summary_36.csv が変わっていないこと（git diff に出ないこと）を確かめる

## 7. 持ち越しの軽微（M8_review-3 No.5。src/summarize_hazard.py）
- 各関数（check_files・calc_hazard_stats・summarize・main）の先頭に、何をする関数かの日本語コメント（docstring）を付ける
- calc_hazard_stats の `('3m〜5m', '5m〜10m', '10m〜20m', '20m以上')` の直書きを、hazard_layers の SHINSUI_3M_IJOU に置き換える
- 出力は変わらないこと（6章で確認）

## 8. 自動テスト（必須。偽データで確かめる。実データのテストは実データがないとき skip）
a. tests/test_make_map.py：2-3 の make_hazard_lines の4つの assert をそのまま入れる
b. tests/test_make_map.py：build_popup_html に hazard_lines を渡すと、見出し「ハザードマップの想定区域との重なり」と4行が `<li>…</li>` で出る。`<script>` を含む行がエスケープされる。hazard_lines=None なら見出しが出ない
c. tests/test_make_map.py の test_main_integration：偽データに hazard_{pref}.csv（4基。区域内・区域外・取得不可・土砂の2現象を混ぜる）を加え、出力した map の HTML に次がすべて含まれることを確かめる
   - 4つの名前「ハザード：洪水（想定最大規模）」「ハザード：津波」「ハザード：高潮」「ハザード：土砂災害警戒区域」
   - 6つのタイルの URL（`https://disaportaldata.gsi.go.jp/raster/01_flood_l2_shinsuishin_data/{z}/{x}/{y}.png` など、LAYERS の6つすべて）
   - 「ハザードマップポータルサイト」と HAZARD_SOURCE_URL
   - 「危険度の判定ではありません」
   - 偽データの碑1基のポップアップの1行（例「土砂災害：区域内（特別警戒区域／土石流・急傾斜地の崩壊）」）
d. tests/test_make_map.py：hazard_{pref}.csv がないとき、「hazard_99.csv」と「python src/add_hazard.py --pref 99」が出て終了コード1
e. tests/test_build_site.py：偽の hazard_summary（全碑・全種別の4行＋移転碑を除くの行＋末尾の注2行）と偽の hazard_{pref}.csv で、index.html に
   - 表の4行が CSV の順で、件数から計算した文字列で出る（偽データの期待値もコードの形で書く。割合の列にわざと件数と合わない値を入れ、件数から計算していることを確かめる）
   - 「移転碑を除く」の行の値が表に出ない
   - 「想定区域との重なりを示すもので、危険度の判定ではありません」、ハザード情報取得日、pref='36' のときだけ津波の注意（pref='99' では出ない）
   - docs/data/hazard_summary_{pref}.csv がコピーされ、ダウンロードの一覧にリンクがある
f. tests/test_build_site.py：hazard_summary_{pref}.csv がないとき、ファイル名と `python src/update.py --pref` が出て終了コード1
g. 実データ（PROJECT_ROOT 基準。なければ skip）：
   - make_hazard_lines を data/processed/hazard_36.csv の次の3基に当てた結果
     ```python
     {'36201-001': ['洪水（想定最大規模）：区域内（浸水深 0.5m〜3m）', '津波：区域内（浸水深 0.5m〜3m）', '高潮：区域内（浸水深 0.5m〜3m）', '土砂災害：区域外'],
      '36368-003': ['洪水（想定最大規模）：区域外', '津波：区域外', '高潮：区域外', '土砂災害：区域内（特別警戒区域／土石流・急傾斜地の崩壊）'],
      '36383-001': ['洪水（想定最大規模）：区域外', '津波：区域内（浸水深 5m〜10m）', '高潮：区域内（浸水深 0.5m〜1m）', '土砂災害：区域外']}
     ```
   - output/hazard_summary_36.csv から作った表の行が 3章の expected_rows と一致
h. tests/test_summarize_hazard.py：`SHINSUI_3M_IJOU == ['3m〜5m', '5m〜10m', '10m〜20m', '20m以上']`
i. tests/test_update.py：4章のとおり

## 完成の条件
- pytest がすべて合格（件数は既存の120件＋新しく増やしたテスト関数の数と一致すること）。問題タブのエラー0件
- output/hazard_summary_36.csv・data/processed/hazard_36.csv・hazard_points_36.csv が変わっていない
- output/map_36.html を開くと、右上の切り替えに4つのハザードが出て、切り替えると色が重なる。最初はどれも表示されていない
- 碑 36383-001（牟岐大震潮記念碑）をクリックすると、8章 g の4行が出る
- docs/index.html に3章の表（expected_rows と同じ値）・注意書き・ハザード情報取得日・津波の注意が出る
- build_site.py の表示が「公開前チェック：問題なし」

## 完了後
- 自己チェックを行い、docs/dev/reports/M8-06_report.md に報告を書く（6章の画面表示をそのまま貼る。変更・作成したファイルとバイト数の一覧、テスト関数の数の内訳）
