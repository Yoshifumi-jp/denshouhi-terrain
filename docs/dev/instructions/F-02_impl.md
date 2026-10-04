# 指示書 F-02（変更要求・地図の「出典・ご利用上の注意」の位置と見た目）　作成日：2026-10-04（10:40 改訂）

最初に AGENTS.md を読んでから作業してください（特に「作業用のスクリプトを作らない」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください。
（計画書 版10 の変更要求 CR-6 によるものです）

## 目的（このテーマ1つ）
地図（src/make_map.py が作る map_36.html）の左下の説明枠で、折りたたみの「出典・ご利用上の注意」を、注意の文「地形との相関を示すもので、災害の予測・安全の保証ではありません。」の上に移す。
あわせて、折りたたみの「出典・ご利用上の注意」が押せる場所だと分かる見た目にする。
今は開閉の印（▶）が表示されず、ただの文字に見えるため、本人が「出典が表示されていない」と受け取った（本人の画面で確認）。スマホでは説明枠が画面の半分までの高さでスクロールになるため、一番下にあると見つけにくいことも理由。

## 対象ファイル
- 変更：src/make_map.py（build_map 関数の legend_html の中だけ）、tests/test_make_map.py（テスト関数を1つ追加）
- 生成物：output/map_36.html、docs/map_36.html（build_site.py がコピー）
- 変えないもの：上記以外のすべて。特に src/build_site.py（公開ページ index.html は今回変えない）、data/、output/ の CSV、docs/dev/（報告書の追加を除く）

## やること
1. src/make_map.py の legend_html で、`<details>` から `</details>` までのかたまり（中身の出典・免責事項・取得日・hazard_notes_html を含む）を、**中身を1文字も変えずに**、次の行のすぐ上に移す
   ```
   <p style="margin-bottom: 10px;">地形との相関を示すもので、災害の予測・安全の保証ではありません。</p>
   ```
   移した後の並び（上から）：
   1. 見出し（自然災害伝承碑と地形（県名））
   2. 碑の数
   3. 凡例（災害種別の色）
   4. 「複数の種別を持つ碑は、…の順で色を決めています」
   5. **折りたたみ「出典・ご利用上の注意」**（ここに移す）
   6. 「地形との相関を示すもので、災害の予測・安全の保証ではありません。」
   7. 「右上の切り替えでハザードマップ（想定区域）を重ねられます。…危険度の判定ではありません。」
2. 移した `<details>` と `<summary>` を次のとおりにする（`<details>` の中の `<ul>` 以下は変えない）
   ```html
   <details class="src-notice" style="margin-bottom: 10px;">
       <summary style="list-style: none; cursor: pointer; color: #0066cc; text-decoration: underline;">▶ 出典・ご利用上の注意（タップで開きます）</summary>
   ```
   あわせて、legend_html の外枠 `<div ...>` の直前に、次の1行を加える（Safari でブラウザ標準の印が二重に出ないようにするため）
   ```html
   <style>.src-notice summary::-webkit-details-marker { display: none; }</style>
   ```
   （意味：`list-style: none` と `::-webkit-details-marker` でブラウザ標準の開閉の印を消し、文字の「▶」と青の下線で押せる場所だと分かるようにする）
   legend_html は f 文字列なので、`{ }` は `{{ }}` と2重にすること
3. tests/test_make_map.py に、新しいテスト関数 `test_legend_details_position(tmp_path, monkeypatch)` を加える（既存のテストは消さない・変えない）。準備は test_hazard_layers_overlay と同じ形（PREFECTURES に '99' を足し、同じ mon_df で `make_map.build_map(mon_df, None, '99')` → `html_ = m.get_root().render()`）にして、次を確かめる
   ```python
   pos_details = html_.find('▶ 出典・ご利用上の注意（タップで開きます）</summary>')
   pos_rule = html_.find('の順で色を決めています')
   pos_corr = html_.find('地形との相関を示すもので、災害の予測・安全の保証ではありません。')
   pos_switch = html_.find('右上の切り替えでハザードマップ（想定区域）を重ねられます。')
   assert -1 not in (pos_details, pos_rule, pos_corr, pos_switch)
   assert pos_rule < pos_details < pos_corr < pos_switch
   assert html_.count('<summary') == 1
   assert '.src-notice summary::-webkit-details-marker { display: none; }' in html_
   assert '【免責事項】' in html_ and 'ハザード情報取得日：2026-10-04' in html_
   ```
4. 改行コードを確かめる。次のコマンド（PowerShell）で2ファイルとも `False`（Windows 式の改行の文字 CR がない）と出ることを確かめ、出た文をそのまま報告に貼る。True と出たら、VS Code 右下の「CRLF」→「LF」→ 保存（Ctrl+S）で直してから、もう一度実行する
   ```
   foreach ($f in 'src\make_map.py','tests\test_make_map.py') { "$f " + [IO.File]::ReadAllText($f).Contains("`r") }
   ```
5. 作り直し（ネット接続不要）
   ```
   .\.venv\Scripts\python.exe src\make_map.py --pref 36
   .\.venv\Scripts\python.exe src\build_site.py --pref 36
   .\.venv\Scripts\python.exe -m pytest
   ```
6. 変わってはいけないファイルの指紋を確かめ、出力をそのまま報告に貼る（期待値 9a96085d74dcb2a6、b191e3742645ec6c、99c87b0ba59527e8）
   ```
   Get-FileHash output\hazard_summary_36.csv, data\processed\hazard_36.csv, data\processed\hazard_points_36.csv -Algorithm SHA256 | ForEach-Object { $_.Hash.Substring(0,16).ToLower() + " " + (Split-Path $_.Path -Leaf) }
   ```
7. `git status --short` の出力をそのまま報告に貼る（「M」は src/make_map.py、tests/test_make_map.py、output/map_36.html、docs/map_36.html と docs/dev/ のファイルだけ。「??」は docs/dev/ の報告書・指示書だけ）

## やらないこと
- `<details>` の中（`<ul>` 以下）の文言・リンク・並び、凡例、ポップアップ、ハザードの重ね表示を変える
- src/build_site.py・update.py を変える、update.py を実行する
- 作業用のスクリプト・パッチファイル（*.patch、temp_*.py など）を作る
- git commit・push

## 完成の条件
- src/make_map.py の差分が「`<details>` のかたまりの移動」「`<details>`・`<summary>` の2行の書き換え」「`<style>` 1行の追加」だけ
- pytest がすべて passed（失敗・エラー・skipped 0件）。件数は 135（今の 134＋新しいテスト1）
- 2ファイルとも改行コードが LF
- 3ファイルの指紋が期待値と一致
- ブラウザで output\map_36.html を開き、左下の枠で「複数の種別を持つ碑は…」の下に、青の下線付きで「▶ 出典・ご利用上の注意（タップで開きます）」が1つだけ（▶ が二重にならない）あり、その下に「地形との相関を…」の文があること。クリックで出典・免責事項・取得日が開き、もう一度クリックで閉じること
- VS Code の「問題」タブでエラー0件

## 完了後
自己チェックを行い、docs/dev/reports/F-02_report.md に報告を書く。報告には次を入れる。
- 変更したファイルとバイト数
- 4・6・7 のコマンドの出力（画面に出た文をそのまま）
- pytest の最後の行をそのまま
