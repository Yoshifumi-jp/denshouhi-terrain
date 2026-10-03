# 指示書 M7-03（実装・伝承内容の分析を地図・公開ページ・更新コマンドに組み込む）　作成日：2026-10-03

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
M7-01・M7-02 で作った「伝承内容の分析」（src/analyze_denshou.py）の結果を、地図のポップアップ・公開用ページ（docs/）・更新コマンド（update.py）に組み込み、`python src/update.py` 1回で作り直せるようにする。
GitHub への push は行わない（本人が行う）。

## 対象ファイル
- 変更：src/make_map.py、src/build_site.py、src/update.py、src/analyze_denshou.py（グラフの目盛と持ち越しの軽微のみ）
- 変更：tests/test_make_map.py、tests/test_build_site.py、tests/test_update.py、tests/test_analyze_denshou.py
- 生成物：output/map_36.html、output/fig/disaster_groups_36.png、docs/index.html、docs/map_36.html、docs/fig/、docs/data/
- **docs/dev/ の中は報告書の追加以外は触れない**

## 1. 地図のポップアップ（src/make_map.py）
- 入力に output/denshou_{pref}.csv を加える（碑の ID で結合）。ファイルがなければ、ファイル名と `python src/analyze_denshou.py --pref 36` を出して終了コード1（既存の足りないファイルの出し方に合わせる）
- build_popup_html に引数を1つ追加する（例 `denshou_text=""`。既定値を付けて既存の呼び出しが壊れないように）。ポップアップの「建立年：…」の行の直後に、次の1行を出す（文言はこのとおり）
  | 区分 | 表示 |
  |---|---|
  | 差あり（年数が1以上） | 災害から建立まで：○年 |
  | 差あり（年数が0） | 災害から建立まで：同じ年 |
  | 災害前の建立 | 災害から建立まで：—（災害より前に建てられた碑） |
  | 対象外（建立年不明） | 災害から建立まで：—（建立年不明） |
  | 不明（災害名に年なし） | 災害から建立まで：—（災害名に年の記載なし） |
  - 年の数が2以上のときは、末尾に「（最も古い災害から）」を付ける（例「災害から建立まで：59年（最も古い災害から）」）
  - 文字列は他の項目と同じく HTML エスケープする

## 2. 公開用ページ（src/build_site.py）
- 必要なファイルに output/denshou_{pref}.csv、denshou_summary_{pref}.csv、disaster_groups_{pref}.csv、fig/denshou_years_{pref}.png、fig/disaster_groups_{pref}.png を加える（足りなければ既存と同じ形でファイル名と先に実行するコマンドを出して終了コード1）
- コピー：CSV 3つを docs/data/ へ、PNG 2つを docs/fig/ へ
- docs/index.html の「グラフ」の節の後、「データのダウンロード」の前に、次の節を加える
  - 見出し `<h2>伝承内容の分析</h2>`
  - 説明（文言はこのまま）：「災害名に書かれた発生年と碑の建立年から、災害の何年後に碑が建てられたかを数えました。複数の災害を伝える碑は最も古い災害から数えています。建立年が不明な碑は数に入れていません。」
  - 表1「災害から建立までの年数（主な種別ごと）」：denshou_summary の全行。列は「主な種別／碑の数／年数を出せた碑（＝差あり）／中央値（年）／最小〜最大（年）」。差ありが0の種別は中央値・最小〜最大を「—」
  - 図：fig/denshou_years_{pref}.png（alt「災害から碑の建立までの年数」）
  - 表2「同じ災害を伝える碑群（3基以上）」：disaster_groups のうち碑の数3以上の行を、CSV と同じ並び順で。列は「災害（発生年）／碑の数／標高の中央値（m）／海岸までの距離の中央値（m）」
  - 図：fig/disaster_groups_{pref}.png（alt「同じ災害を伝える碑群の比較」）
- 「データのダウンロード」に3行を加える：「碑ごとの建立までの年数」（denshou）、「建立までの年数の集計」（denshou_summary）、「同じ災害を伝える碑群」（disaster_groups）
- 公開前チェックの対象に、docs/data/ に加えた CSV 3つを含める
- 徳島の答え（テストの照合に使う）：表1は7行（全種別・津波・高潮・洪水・土砂災害・地震・その他）、全種別は 碑の数71／差あり62／中央値39.0。表2は5行（昭和南海地震(1946) 28基・3.1・117.5／安政南海地震(1854) 20基・5.2・131.5／安政東海地震(1854) 6基／昭和29年台風12号(ジューン台風)(1954) 3基／昭和51年台風17号(1976) 3基）

## 3. 更新コマンド（src/update.py）
- ステップ「集計」（summarize.py）の直後、「地図作成」の前に、ステップ「伝承内容の分析」`["analyze_denshou.py", "--pref", pref_code]` を加える（全12ステップ）
- tests/test_update.py の test_k の期待するコマンド列を12件に直す

## 4. 碑群のグラフの目盛（src/analyze_denshou.py。M7_review-1 No.5）
- output/fig/disaster_groups_{pref}.png の縦軸を、標高・海岸までの距離とも**対数目盛**にする（離れた値の碑があっても箱が潰れないように）。ただし、その図に0以下の値が1つでもあるときは、その図だけ通常の目盛のままにする
- 縦軸のラベルに「（対数目盛）」を付ける（通常の目盛のときは付けない）
- CSV 3つの中身は変えない（ハッシュが変わらないこと）

## 5. 持ち越しの軽微（M7_review-2）
- No.1：src/analyze_denshou.py の '_indices' の英語コメントを日本語にする
- No.2：tests/test_analyze_denshou.py の test_build_denshou_table で、入力の行を ID 順でない並びにし、戻り値が ID 順になっていることを確かめる

## 6. 自動テスト（ネット接続なしで動くこと。本物の data/・output/・docs/ には書き込まない）
- a. build_popup_html：区分5通り（差あり1以上・差あり0・災害前・対象外・不明）＋年の数2以上の「（最も古い災害から）」の6例で、ポップアップにその文言が入ること。HTML エスケープされること（災害名に `<` を含む偽データ）
- b. make_map の main を偽データで実行し、denshou の結果がポップアップに入ること。denshou_{pref}.csv がないと終了コード1とコマンドの案内
- c. build_site を偽データで実行し、index.html に「伝承内容の分析」の見出し・表1・表2（碑の数3以上だけ、並び順どおり。碑の数2の碑群が出ないこと）・図2つ・ダウンロードの3行があること。docs/data/ に CSV 3つ、docs/fig/ に PNG 2つがコピーされること。足りないファイルがあると終了コード1
- d. 対数目盛：偽データで、値がすべて正なら縦軸が対数（ax.get_yscale() == "log"）、0以下を含めば通常（"linear"）になること（グラフを作る部分を関数に分けて確かめてよい）
- e. update.py の test_k が12ステップで合格
- f. 既存のテストがすべて合格（`python -m pytest`、`python -m pytest -q tests/test_make_map.py` のように引数付きでも）

## 7. 実データでの実行
1. 実行前に output/denshou_36.csv、denshou_summary_36.csv、disaster_groups_36.csv のハッシュを記録
2. `python src/analyze_denshou.py --pref 36` → `python src/make_map.py --pref 36` → `python src/build_site.py --pref 36` を順に実行（問い合わせは発生しない）。まとめ表示をそのまま報告に貼る
3. CSV 3つのハッシュが実行前と同じであること
4. update.py の実データでの通し実行は行わない（--dry-run は差分の判定までで止まりステップを実行しないため）。12ステップになったことは test_k で確かめる。通しの実行は確認シートの段階で本人と行う
5. `python src/check_public.py` が「問題なし」

## やらないこと
- 分析の計算・CSV の中身の変更
- 既存のトップページの他の節の文言・順序の変更
- git commit・push、GitHub Pages の設定
- ルート直下などへの作業ファイルの作成（実行結果は報告書に直接貼る）
- check_public.py の変更（M7-04 で行う）

## 完成の条件
- 地図で碑をクリックすると「災害から建立まで：…」が出る（実データの 36201-001 は「7年」、36387-003 は「59年（最も古い災害から）」、36203-001 は「—（建立年不明）」）
- docs/index.html に「伝承内容の分析」の節があり、表1・表2・図2つ・ダウンロード3行がある
- update.py が12ステップ
- `python -m pytest` で全件合格、問題タブのエラー0件、公開前チェック「問題なし」

## 完了後
- 自己チェックを行い、docs/dev/reports/M7-03_report.md に報告を書く（docs/dev/reports/_template.md の書式。まとめ表示・テスト結果・ハッシュはそのまま貼る。ファイル名とバイト数の一覧を必ず書く）
