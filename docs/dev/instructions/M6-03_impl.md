# 指示書 M6-03（実装・公開用ページの作成と公開前チェック）　作成日：2026-10-03

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。

## 目的（このテーマ1つ）
GitHub Pages（「main ブランチの /docs フォルダ」から公開）で知人が見られるよう、output/ の成果物から公開用ページ一式を docs/ に作るコマンドを作る。
あわせて、公開するファイルにパソコンのユーザー名入りのパスやメールアドレスが含まれていないかを調べる公開前チェックを作る。
GitHub への push や Pages の設定は行わない（本人が行う）。

## 対象ファイル
- 新規：src/build_site.py、src/check_public.py、tests/test_build_site.py、tests/test_check_public.py
- 変更：src/update.py（ステップ11「公開用ページの作成」を追加）、tests/test_update.py（ステップ数の変更に合わせる＋M6_review-2 No.2 のテスト）
- 生成物（コマンドの実行でできるもの）：docs/index.html、docs/map_36.html、docs/fig/*.png、docs/data/*.csv、docs/.nojekyll
- **docs/dev/ の中は読み書きしない**（開発資料。build_site.py は docs/dev/ に触れないこと）

## 1. src/build_site.py
```
python src/build_site.py --pref 36
```
- --pref は 01〜47（all 不可。他のスクリプトと同じエラー文）
- 入力（output/）：map_36.html、fig/ の *_36.png、summary_36.csv、landform_36.csv、relocated_36.csv、update_history_36.csv。data/processed/monuments_36.csv（データ取得日・碑の数に使う）
  - 足りないファイルがあれば、ファイル名と先に実行するコマンド（`python src/update.py --pref 36` など）を出して終了（終了コード1）
- 出力（docs/）：
  - docs/map_36.html … output/map_36.html をそのままコピー
  - docs/fig/ … output/fig/ の *_36.png をコピー
  - docs/data/ … summary_36.csv、landform_36.csv、relocated_36.csv、update_history_36.csv をコピー
  - docs/.nojekyll … 空ファイル（GitHub Pages の加工を止めるため）
  - docs/index.html … 下の「トップページ」
- 出力先のフォルダは引数で差し替えられるようにする（テスト用。例 build_site(pref, output_dir, site_dir)）。既定は PROJECT_ROOT / "docs"
- 最後に check_public の検査を「作った公開ファイル」（docs/index.html、docs/map_36.html、docs/data/、docs/fig/ は画像のため除く）に対して行い、見つかればその内容を出して終了コード1
- 画面のまとめ表示：対象の県名／データ取得日／碑の数／作ったファイルの一覧（プロジェクトのルートからの相対パス）／公開前チェック：問題なし

## 2. トップページ docs/index.html（1ファイル。外部の CSS・JavaScript は読み込まない）
- `<meta charset="utf-8">`、`<meta name="viewport" content="width=device-width, initial-scale=1">`、`<title>自然災害伝承碑と地形（徳島県）</title>`
- 見た目：本文の最大幅 800px で中央寄せ、文字 16px 前後、スマホ（幅 375px）で横にはみ出さない（画像は max-width:100%、表は横スクロールできる枠に入れる）
- 中身（この順）：
  1. 見出し「自然災害伝承碑と地形（徳島県）」
  2. 1行：「伝承碑データ取得日：2026-09-24　碑の数：71基　最終更新：YYYY-MM-DD」（取得日は monuments のデータ取得日の最新、最終更新は更新履歴の最後の「完了」行の実行日時の日付。更新履歴がなければ「最終更新：—」）
  3. 説明（文言はこのまま）：「国土地理院の自然災害伝承碑に、碑ごとの地形（標高・傾斜・地形分類・河川や海岸との位置関係）を付け、碑のまわり（100m〜2,000m）の地点と比べた結果をまとめたものです。結果は地形との相関を示すもので、災害の予測・安全の保証ではありません。」
  4. 地図へのボタン状のリンク「地図を開く（碑をクリックすると地形の診断結果が出ます）」→ map_36.html
  5. 「碑とまわりの比較（全碑・全種別）」の表：summary_36.csv の 範囲=全碑・災害種別=全種別 の5行（標高_m、傾斜_度、河川までの距離_m、河川との高さの差_m、海岸までの距離_m）。列：指標（「標高(m)」のように読みやすく）、碑の中央値、まわりの中央値（比較地点_中央値）、差の中央値、碑の方が大きい割合（%表示、小数なし）。表の下に「移転碑を除いた集計や災害種別ごとの集計は、下の集計表（CSV）にあります。」
  6. 「グラフ」：fig/ の6枚を、見出し付きで縦に並べる（標高／傾斜／河川までの距離／河川との高さの差／海岸までの距離／地形分類）。画像の alt に見出しと同じ文
  7. 「データのダウンロード（CSV、Excel で開けます）」：data/ の4ファイルへのリンクと一言説明（集計表／地形分類の集計／移転碑の一覧／更新履歴）
  8. 「更新履歴」の表：更新履歴の「完了」行だけ、新しい順。列：更新日（実行日時の日付）、データ取得日、碑の数（新基数）、追加、変更、削除
  9. 「出典」：M5 の地図と同じ6行（文言は src/make_map.py と同じ。重複して書かず、make_map.py に定数があれば import して使う。なければ build_site.py に同じ文言を書く）＋「国土数値情報（海岸線データ）は非商用に限り利用できます。本ページは非商用です。」＋「地理院タイル」に地理院タイル一覧（https://maps.gsi.go.jp/development/ichiran.html）へのリンク
  10. 「ご利用上の注意」：M5 の地図と同じ免責文
- 文字はすべて HTML エスケープしてから埋め込む（CSV の値にも）

## 3. src/check_public.py（公開前チェック）
- 関数 find_private_info(paths) → 見つかったものの一覧（ファイルの相対パス、行番号、種類）。テキストとして読めないファイル（画像など）は飛ばす
- 調べる種類（**特定の人の名前やユーザー名をコードに書かない**。一般的な形で調べる）：
  - Windows のユーザーフォルダのパス：`[A-Za-z]:\Users\<何か>`（区切りは \ と / の両方、\\ のような重ねも）
  - macOS・Linux のホームのパス：`/Users/<何か>/`、`/home/<何か>/`
  - メールアドレス：一般的な形。ただし `@users.noreply.github.com` で終わるものは除く
  - 伏せ字は検出しない：ユーザー名の部分が `<` で始まるもの（例 `C:\Users\<ユーザー名>\`）、`%USERPROFILE%`（開発資料に説明として書いてあるため）
- コマンド：`python src/check_public.py` で、Git 管理対象になりうる場所（README.md、AGENTS.md、requirements.txt、src/、tests/、docs/、output/）を調べ、見つかれば一覧を出して終了コード1、なければ「公開前チェック：問題なし」で終了コード0。.venv/、.git/、data/、_to_delete/ は調べない
- 見つかった内容を表示するときは、ユーザー名の部分を「<ユーザー名>」に置き換えて表示する（表示そのものが個人情報を出さないように）

## 4. src/update.py の変更
- ステップ11「公開用ページの作成」：src/build_site.py --pref P を追加（表示は [11/11]）
- 既存のステップ・差分判定は変更しない

## やらないこと
- git push、GitHub の設定、docs/dev/ の読み書き
- output/ や data/ の既存の成果物の書き換え（コピー元として読むだけ）
- 外部への問い合わせ

## 自動テスト（ネット接続なし。本物の docs/・output/ に書き込まない。tmp_path の中で行う）
- tests/test_build_site.py
  - a 偽の output 一式（小さな CSV・ダミー PNG・ダミー map）から build_site を実行 → index.html・map_36.html・fig の PNG・data の4 CSV・.nojekyll ができる
  - b index.html に viewport の meta、「伝承碑データ取得日：」、碑の数、地図へのリンク（href="map_36.html"）、6枚の img、4つの CSV へのリンク、出典の「国土数値情報」「非商用」が入っている
  - c 比較の表：偽の summary（全碑・全種別の5行＋別の行）から、5行だけが表に出て、割合 0.143 が「14%」と出る
  - d 更新履歴の表：「完了」「失敗」が混ざった履歴から、「完了」だけが新しい順に出る。履歴がないとき「最終更新：—」
  - e site_dir の中に dev/ フォルダとファイルを置いてから build_site を実行しても、dev/ の中身が変わらない（作成日時・中身が同じ）
  - f 入力ファイルが1つ足りないとき、終了コード1で、足りないファイル名が表示される
  - g CSV の値に `<script>` を入れても、index.html ではエスケープされている
- tests/test_check_public.py（テストの中の偽の個人情報は、文字列をつなげて作り、テストファイル自体に検出される形を書かない。例 "C:" + "\\" + "Users" + "\\" + "taro"）
  - h Windows のパス（\ と /、\\ の重ね）、/Users/…/、/home/…/、メールアドレスを含むファイル → それぞれ見つかる
  - i `xxx@users.noreply.github.com`、伏せ字（`<ユーザー名>`、`%USERPROFILE%`）は見つからない。「所在地」のような普通の日本語・相対パス data/raw/… は見つからない
  - j 画像（バイナリ）は飛ばす
  - k 表示でユーザー名が「<ユーザー名>」に置き換わる
  - l **本物のプロジェクト**（README.md、AGENTS.md、requirements.txt、src/、tests/、docs/、output/）に対して find_private_info を実行し、0件であること（読むだけ）
- tests/test_update.py
  - test_k の期待値を11ステップに変える
  - M6_review-2 No.2：subprocess.run を差し替えて default_runner を呼び、cwd=PROJECT_ROOT が渡されることを確かめる

## 完成の条件
- `.\.venv\Scripts\python.exe -m pytest` で全件合格
- `.\.venv\Scripts\python.exe src\build_site.py --pref 36` を実行 → docs/ に上記ファイルができ、「公開前チェック：問題なし」。出力を省略せずに報告に貼る
- `.\.venv\Scripts\python.exe src\check_public.py` → 「公開前チェック：問題なし」。出力を報告に貼る
- docs/index.html をブラウザで開き、PC の幅とスマホの幅（ブラウザの開発者ツールの端末表示など）で、表・グラフ・リンクが見られることを確かめ、報告に書く
- docs/dev/ の中身が変わっていないこと（git status で docs/dev/ に変更が出ないこと）を報告に書く

## 完了後
- 自己チェックを行い、docs/dev/reports/M6-03_report.md に報告を書く（ファイル名とバイト数の一覧を含める。実行結果は省略しない。絶対パスは「<プロジェクト>」に置き換える）。
