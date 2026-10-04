# denshouhi-terrain（自然災害伝承碑×地形 分析システム）

国土地理院の「自然災害伝承碑」データに、碑ごとの地形情報（標高・傾斜・地形分類・河川や海岸との位置関係）とハザードマップの想定区域との重なりを付け、
碑のまわりの地点と比べて「碑はどんな地形に立っているか」を災害種別ごとに集計・地図化する個人開発プロジェクトです。

- 公開ページ：https://yoshifumi-jp.github.io/denshouhi-terrain/
- 対象：徳島県（第1版、71基、伝承碑データ取得日 2026-09-24）。全国展開は第2版で行う予定
- 状態：第1版 完成（開発の記録は docs/dev/）

## できること
| 内容 | 主なプログラム | 出力 |
|---|---|---|
| 伝承碑データの読み込み（災害種別を列に分ける） | src/load_monuments.py | data/processed/monuments_{県コード}.csv |
| 標高・傾斜の付与 | src/add_elevation.py | data/processed/elevation_{県コード}.csv |
| 最寄り河川・海岸までの距離、河川との高さの差 | src/add_river_coast.py | data/processed/river_coast_{県コード}.csv |
| 地形分類（自然地形）の付与 | src/add_landform.py | data/processed/landform_{県コード}.csv |
| 比較地点（各碑から100m〜2,000m、5点ずつ）の作成 | src/make_comparison_points.py | data/processed/points_{県コード}.csv |
| ハザードマップの想定区域（洪水・津波・高潮・土砂災害）の判定 | src/add_hazard.py | data/processed/hazard_{県コード}.csv |
| 碑と比較地点の集計・グラフ | src/summarize.py、src/summarize_hazard.py | output/summary_{県コード}.csv、output/fig/ ほか |
| 伝承内容の分析（災害から建立までの年数、同じ災害の碑群） | src/analyze_denshou.py | output/denshou_{県コード}.csv ほか |
| 地図（碑をクリックで診断結果、ハザードマップの重ね表示） | src/make_map.py | output/map_{県コード}.html |
| 公開用ページの作成（公開前チェック付き） | src/build_site.py、src/check_public.py | docs/index.html、docs/map_{県コード}.html |
| 差分更新（新しいデータとの比較→上の全工程を順に実行） | src/update.py | output/diff/、output/update_history_{県コード}.csv |

## 使い方（Windows・PowerShell）
1. 準備（初回のみ）
   ```
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. 元データを置く（利用規約への同意が必要なため手動で取得）
   - 自然災害伝承碑：国土地理院のページから CSV をダウンロードし、`data/raw/<取得日 YYYY-MM-DD>/` に置く
   - 河川・海岸線：国土数値情報の河川データ（W05）・海岸線データ（C23）の対象県分を、`data/raw/rivers/`・`data/raw/coastline/` に展開する
3. 作成・更新（県コードは2桁。徳島は 36）
   ```
   .\.venv\Scripts\python.exe src\update.py --pref 36
   ```
   新しい取得日のフォルダを置いて同じコマンドを実行すると、追加・変更・削除の一覧を出してから作り直します（`--dry-run` で一覧だけ）。
   標高・地形分類・ハザードの問い合わせ結果は data/cache/ に保存し、2回目以降は再利用します。
4. 自動テスト
   ```
   .\.venv\Scripts\python.exe -m pytest
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
- 地形分類：国土地理院 地形分類（自然地形）
- 河川・海岸線：「国土数値情報（河川データ、海岸線データ）」（国土交通省）。海岸線データは非商用に限り利用できます
- ハザード情報：ハザードマップポータルサイト（https://disaportal.gsi.go.jp/hazardmapportal/hazardmap/copyright/opendata.html）の配信データ（タイル画像）の色を読み取って判定
- 上記を加工して作成

## ご利用上の注意
- 分析結果は伝承碑の位置と地形との「相関」を示すもので、災害の発生を予測・保証するものではありません。
- ハザードマップの想定区域との重なりは、危険度の判定ではありません。防災上の判断には自治体のハザードマップをご利用ください。
- 碑の位置は被災した地点とは限りません（移設された碑もあります）。伝承碑の登録は市町村の申請によるもので、すべての碑を網羅しているわけではありません。
