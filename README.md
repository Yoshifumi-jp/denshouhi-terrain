# denshouhi-terrain（自然災害伝承碑×地形 分析システム）

国土地理院の「自然災害伝承碑」データに、碑ごとの地形情報（標高・傾斜・地形分類〔自然地形・人工地形〕・河川や海岸との位置関係）とハザードマップの想定区域との重なりを付け、
碑のまわりの地点と比べて「碑はどんな地形に立っているか」を災害種別ごとに集計・地図化する個人開発プロジェクトです。

- 公開ページ：https://yoshifumi-jp.github.io/denshouhi-terrain/
- 対象：全国47都道府県（2,481基、伝承碑データ取得日 2026-09-24）
- 公開ページの構成：トップ（index.html）が全国ページ（都道府県の色分け地図、絞り込みできる碑の一覧、全国集計の表とグラフ、印刷用PDF national_report.pdf。PDF へのリンクはページ上部と下部の2か所）。県別ページは pref_{県コード}.html（上部に全国ページと全国の印刷用PDFへのリンク）、県別の地図は map_{県コード}.html
- 状態：第4版 公開（地形分類の人工地形〔盛土地・埋立地、干拓地、切土地など〕を追加。第1版は徳島県のみ、第2版で全国に展開、第3版で地形分類の詳細版がない碑を地域版で補完。開発の記録は docs/dev/）

## できること
| 内容 | 主なプログラム | 出力 |
|---|---|---|
| 伝承碑データの読み込み（災害種別を列に分ける） | src/load_monuments.py | data/processed/monuments_{県コード}.csv |
| 標高・傾斜の付与 | src/add_elevation.py | data/processed/elevation_{県コード}.csv |
| 最寄り河川・海岸までの距離、河川との高さの差 | src/add_river_coast.py | data/processed/river_coast_{県コード}.csv |
| 地形分類（自然地形）の付与 | src/add_landform.py | data/processed/landform_{県コード}.csv |
| 地形分類（地域版。取れないときは広域版）の付与（碑・比較地点の全件） | src/add_landform_region.py | data/processed/landform_region_{県コード}.csv、landform_region_points_{県コード}.csv |
| 地形分類（人工地形）の付与（詳細版で地形分類が取れた碑・比較地点） | src/add_landform_artificial.py | data/processed/landform_artificial_{県コード}.csv、landform_artificial_points_{県コード}.csv |
| 比較地点（各碑から100m〜2,000m、5点ずつ）の作成 | src/make_comparison_points.py | data/processed/points_{県コード}.csv |
| ハザードマップの想定区域（洪水・津波・高潮・土砂災害）の判定 | src/add_hazard.py | data/processed/hazard_{県コード}.csv |
| 碑と比較地点の集計・グラフ | src/summarize.py、src/summarize_hazard.py | output/summary_{県コード}.csv、output/fig/ ほか |
| 伝承内容の分析（災害から建立までの年数、同じ災害の碑群） | src/analyze_denshou.py | output/denshou_{県コード}.csv ほか |
| 地図（碑をクリックで診断結果、ハザードマップの重ね表示） | src/make_map.py | output/map_{県コード}.html |
| 県別の公開用ページの作成 | src/build_site.py | docs/pref_{県コード}.html、docs/map_{県コード}.html |
| 公開前チェック（個人情報・パスの混入を確認） | src/check_public.py | 画面表示 |
| 差分更新（1県：新しいデータとの比較→上の全工程を順に実行） | src/update.py | output/diff/、output/update_history_{県コード}.csv |
| 複数県の一括実行（中断しても同じコマンドで再開） | src/run_batch.py | output/batch_log.csv |
| 地形分類（地域版）だけの複数県の一括実行 | src/run_region_batch.py | output/region_batch_log.csv |
| 地形分類（人工地形）だけの複数県の一括実行 | src/run_artificial_batch.py | output/artificial_batch_log.csv |
| 全国集計（表・年代別推移・グラフ） | src/summarize_national.py | output/*_all.csv、output/fig/*_all.png |
| 地形分類（地域版）の県別・全国集計（詳細版の集計とは別の表） | src/summarize_region.py | output/landform_region_{県コード}.csv、output/landform_region_all.csv |
| 地形分類（人工地形）の県別・全国集計（災害種別×人工地形、自然地形×人工地形） | src/summarize_artificial.py | output/landform_artificial_{県コード}.csv、output/landform_artificial_all.csv、output/landform_artificial_cross_all.csv |
| 取得できなかった件数の県別一覧 | src/count_missing.py | output/missing_counts.csv |
| 印刷用PDF（A4・8ページ） | src/make_national_pdf.py | output/national_report.pdf |
| 全国ページの作成 | src/build_national.py | docs/index.html、docs/national_report.pdf |
| 全国の更新（差分のある県だけ作り直し→全国集計・ページ・PDFを作り直す） | src/update_all.py | output/update_history_all.csv |

## 使い方（Windows・PowerShell）
1. 準備（初回のみ）
   ```
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. 元データを置く（利用規約への同意が必要なため手動で取得）
   - 自然災害伝承碑：国土地理院のページから CSV をダウンロードし、`data/raw/<取得日 YYYY-MM-DD>/` に置く
   - 河川・海岸線：国土数値情報の河川データ（W05）・海岸線データ（C23）の対象県分を、`data/raw/rivers/`・`data/raw/coastline/` に展開する
3. 作成（県コードは2桁。徳島は 36。PowerShell では必ず "…" で囲む）
   ```
   .\.venv\Scripts\python.exe src\run_batch.py --pref "03,20,28"
   .\.venv\Scripts\python.exe src\run_batch.py --pref all --check-only
   ```
   1基あたり約2分半かかります（問い合わせのため）。途中で止めても、同じコマンドで続きから再開します。`--check-only` は元データがそろっているかの確認だけ行います。
   標高・地形分類・ハザードの問い合わせ結果は data/cache/ に保存し、2回目以降は再利用します。
4. 地形分類（地域版）だけを作る（3. の後。全国で約1時間。途中で止めても同じコマンドで再開）
   ```
   .\.venv\Scripts\python.exe src\run_region_batch.py --pref all --check-only
   .\.venv\Scripts\python.exe src\run_region_batch.py --pref all
   ```
   長時間の実行前に、Windows のスリープを「なし」にしてください。
5. 地形分類（人工地形）だけを作る（3. の後。全国でタイル約7,700枚を取得するため数時間かかります。途中で止めても同じコマンドで再開）
   ```
   .\.venv\Scripts\python.exe src\run_artificial_batch.py --pref all --check-only
   .\.venv\Scripts\python.exe src\run_artificial_batch.py --pref all
   ```
   3. の update.py・6. の update_all.py には地域版・人工地形の段階も含まれています。
6. 全国の更新（新しい取得日のフォルダを data/raw/ に置いてから）
   ```
   .\.venv\Scripts\python.exe src\update_all.py --dry-run
   .\.venv\Scripts\python.exe src\update_all.py
   ```
   県ごとに前回のデータと比べ、差分のある県だけ作り直したうえで、全国集計・県別ページ・PDF・全国ページを作り直します（`--dry-run` は確認だけで何も書き込みません）。
7. 自動テスト
   ```
   .\.venv\Scripts\python.exe -m pytest
   .\.venv\Scripts\python.exe src\check_public.py
   ```

## フォルダ構成
| フォルダ | 内容 |
|---|---|
| src/ | プログラム |
| tests/ | 自動テスト |
| data/raw/<取得日>/ | 国土地理院からダウンロードした元データ（手を加えない） |
| data/raw/rivers/、data/raw/coastline/ | 国土数値情報（容量が大きいため Git 対象外） |
| data/processed/ | 整形・地形付与後のデータ（再作成できるため Git 対象外） |
| data/cache/ | 問い合わせ結果の保存（Git 対象外） |
| output/ | 地図・集計表・グラフ |
| docs/ | 公開用ページ（GitHub Pages） |
| docs/dev/ | 開発管理資料（計画書・指示書・確認記録） |

## 出典
- 自然災害伝承碑：国土地理院（https://www.gsi.go.jp/bousaichiri/denshouhi.html）
- 背景地図：地理院タイル（淡色地図）
- 標高・傾斜：国土地理院 標高API（標高タイル）から算出
- 地形分類：国土地理院 地形分類（自然地形）の詳細版・地域版・広域版、地形分類（人工地形）
- 河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）。海岸線データは非商用に限り利用できます
- ハザード情報：ハザードマップポータルサイト（https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html）の配信データ（タイル画像）の色を読み取って判定
- 上記を加工して作成

## ご利用上の注意
- 分析結果は伝承碑の位置と地形との「相関」を示すもので、災害の発生を予測・保証するものではありません。
- ハザードマップの想定区域との重なりは、危険度の判定ではありません。防災上の判断には自治体のハザードマップをご利用ください。
- 碑の位置は被災した地点とは限りません（移設された碑もあります）。「移転碑」の判定は伝承内容の文字から機械的に行っており、集団移転など碑の移設ではないものを含みます。
- ハザードマップの想定の年次は都道府県によって異なります。地形分類は整備されていない地域があり、詳細版では全国の碑の約37%が「データなし」のため、地域版（中分類12種）で補っています（地域版でも取れない碑は島の5基）。地域版は詳細版より粗く、碑とまわりの地点が同じ分類になりやすいため、詳細版と地域版の集計は混ぜずに別の表にしています。人工地形（盛土地・埋立地、干拓地、切土地など）は詳細版がある範囲だけで調べています（全国の碑のうち929基は範囲外）。人工地形はデータを整備した時点の状態で、その後の造成・埋立は入っていません。伝承碑の登録は市町村の申請によるもので、すべての碑を網羅しているわけではありません。
