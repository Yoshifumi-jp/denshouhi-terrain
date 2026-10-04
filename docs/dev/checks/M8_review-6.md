# ソース確認 M8（6回目＝M8-06_impl）　確認日：2026-10-04

- 確認範囲：46c5faf（M8-06 依頼前）からの差分＋影響範囲（src/make_map.py、src/build_site.py、src/update.py、src/hazard_layers.py、src/summarize_hazard.py、tests/ の4ファイル、docs/index.html、docs/map_36.html、output/map_36.html、docs/data/hazard_summary_36.csv）
- ファイルの消失：なし（報告のバイト数と一致）
- 変わってはいけないファイル：output/hazard_summary_36.csv・data/processed/hazard_36.csv・hazard_points_36.csv のハッシュは不変（9a96085d74dcb2a6／b191e3742645ec6c／99c87b0ba59527e8）
- 報告の実行結果とコードの表示文の照合：**照合できない**（6章の画面表示が1行も貼られていない）。pytest「121 passed」はテスト関数の数 116（＋パラメータ化）と矛盾しないが、増えたテスト関数は test_l_shinsui_3m_ijou の1つだけ
- 実物の確認（Claude）：
  - ポップアップ：3基（36201-001・36368-003・36383-001）の4行は指示書 8章 g の期待値と一致
  - タイルの URL 6つは正しい。土砂の FeatureGroup は重ね表示（overlays）に入り、最初は非表示
  - **洪水・津波・高潮の3つは「背景地図」（base_layers、ラジオボタン）に入っている**。選ぶと淡色地図と入れ替わり、碑の上に重ねられない
  - docs/index.html に「ハザードマップの想定区域との重なり」の節（表・取得日・津波の注意）が**出ていない**。出典のリンク先が文字どおり「{HAZARD_SOURCE_URL}」
- 指示外の作業：報告に「一時的なテスト書き換えに使用した Python スクリプト群は全て削除済み」＝AGENTS.md「作業用のスクリプトを作らない」に反する（削除済みのため実害は確認できず）
- 改行コード：src/build_site.py・src/make_map.py・tests/test_update.py がファイル全体で CRLF に変わった（差分が大きく見える原因。中身の変更は 260行追加・8行削除）

| No | 重大度 | ファイル・行 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | 重大 | src/build_site.py hazard_section_html | 節の HTML を作っているが html_content に入れていない。公開ページに表・注意書き・取得日・津波の注意が出ない（確認項目②④を満たさない） | 修正 |
| 2 | 中 | src/make_map.py build_map | 洪水・津波・高潮の TileLayer に overlay=True がなく、背景地図の扱いになった（確認項目③を満たさない）。**指示書に overlay=True を書かなかった Claude の不足も原因** | 修正 |
| 3 | 中 | src/build_site.py source_html | f 文字列でないため href が「{HAZARD_SOURCE_URL}」のまま（出典のリンク切れ） | 修正 |
| 4 | 中 | src/build_site.py | ハザード情報取得日が "2026-10-04" の直書き（hazard_{pref}.csv の取得日を読んでいない）。次の更新で誤った日付が出る | 修正 |
| 5 | 中 | src/build_site.py | 「ご利用上の注意」に入れる文が「データのダウンロード」「出典」の一覧にも入った（3か所） | 修正 |
| 6 | 中 | tests/ | 指示書 8章 a〜g のテストがほぼない（a・b・c・e・f・g なし。d は件名だけ）。No.1〜4 はテストがあれば見つかった | 修正 |
| 7 | 中 | docs/dev/reports/M8-06_report.md | 6章の画面表示なし、テスト関数の数の内訳なし、「テストを追加」「index.html に表が表示」「update.py でエラーなく終了」と実際と食い違う記載 | 修正（報告の書き直し） |
| 8 | 軽微 | src/make_map.py build_map | hazard_lines を作る条件が入り組んでおり、洪水_状態だけ空で他がある行（指示書 row4）でポップアップに4行が出ない。常に make_hazard_lines を呼べばよい | 修正に含める |
| 9 | 軽微 | src/make_map.py | 凡例の HAZARD_DATA_NOTES をエスケープしていない／取得日を PROJECT_ROOT のファイルから読み直している（load_data で読んだものを使う） | 修正に含める |
| 10 | 軽微 | src/build_site.py・make_map.py・tests/test_update.py | 改行コードが CRLF に変わった | 修正に含める（LF に戻す） |
| 11 | 軽微 | src/add_hazard.py 画面表示 | 「{県名}県」で「徳島県県」になる（M8-01 からの持ち越し。Claude の気づき） | 次の指示書でまとめて |

良かった点：make_hazard_lines の中身、hazard_layers の定数、summarize_hazard の No.5 対応（出力不変）、update.py の15ステップは指示どおり。

## 判定：**不合格**（M8 は修正の上限3回に達しているため、計画の見直しを本人に相談）
