# 指示書 M7-05（実装・公開前チェックの取りこぼしを減らす）　作成日：2026-10-03

最初に AGENTS.md を読んでから作業してください（特に「個人情報の扱い」「完了報告」）。
作業前に、エディタのタブをすべて閉じてから始めてください（ファイル消失の再発防止）。
**作業中に、プロジェクトのルート直下やその他の場所に作業ファイル（実行結果の記録など）を作らないでください。** 実行結果は報告書に直接貼ってください。

## 目的（このテーマ1つ）
公開前チェック（src/check_public.py）が見落としうる次の3点を直し、引数付きの pytest でも動くようにする。
1. ルート直下のファイルは README.md・AGENTS.md・requirements.txt しか調べていない（ルート直下に作られた作業ファイルを見落とす）
2. UTF-16 で書かれたファイル（PowerShell の出力を保存したものなど）は、先頭の判定で「バイナリ」とみなされ調べていない
3. ユーザー名の部分から半角の「.」「,」を除いているため、ドットを含むユーザー名（例：名.姓）のホームのパスを見落とす（M6_review-5 No.1）
4. main() の中の parse_args() が pytest の引数を読んでしまう（M6_review-5 No.2）

## 対象ファイル
- 変更：src/check_public.py、tests/test_check_public.py

## やること（手順）
1. collect_targets：ルート直下の**すべてのファイル**（フォルダは除く。.gitignore なども含む）を対象に加える。既存の除外（.venv、.git、data、_to_delete、__pycache__）はそのまま
2. find_private_info：ファイルの先頭が UTF-16 の BOM（バイト列 FF FE または FE FF）なら UTF-16 として読んで調べる。それ以外で先頭1024バイトに 00 を含むものは今までどおりバイナリとして飛ばす。UTF-8 で読めないファイルも今までどおり飛ばす
3. win_pattern・unix_pattern：ユーザー名の部分の除外文字から半角の「.」「,」を外す（全角の「、」「。」は除外のまま）
4. main：引数を `main(root=None, args=None)` とし、`parser.parse_args(args)` にする（既存の `check_main(root=tmp_path)` の呼び出しはそのまま動くこと）
5. 実データで `python src/check_public.py` を実行し、結果をそのまま報告に貼る。「問題あり」になった場合は、見つかったファイル名と行番号を報告に書いて止まる（ファイルの中身は直さない。Claude が判断する）

## 自動テスト（tests/test_check_public.py に追加）
- a. tmp_path のルート直下に out.txt（中身に偽のWindowsパス：C ドライブ＋Users＋偽の名前「taro」）を作ると、collect_targets の対象に入り、find_private_info で1件見つかる
- b. docs/ に UTF-16（BOM 付き、Python の `encoding="utf-16"`）で同じ偽のパスを書いたファイルを作ると1件見つかる。BOM なしで 00 を含むバイナリ（例 b"\x89PNG\x00\x00"）は0件
- c. ドットを含むユーザー名：Windows 形式（C ドライブ＋Users＋「taro.yamada」）と macOS 形式（スラッシュ＋Users＋スラッシュ＋「taro.yamada」＋スラッシュ）、Linux 形式（スラッシュ＋home＋スラッシュ＋「taro.yamada」＋スラッシュ）がそれぞれ1件見つかり、表示に「taro」が出ない
- d. 既存のテスト n・n2（URL を誤って拾わない）が変更後も合格する。さらに「https://example.com/home/index.html.」のように文末に半角ピリオドが付いた URL の行も0件であること
- e. sys.argv を `["pytest", "-q", "tests/test_check_public.py"]` にした状態で `check_main(root=tmp_path)` が引数エラーにならず、問題なしなら終了コード0
- 偽の名前・パスは、既存テストと同じく文字列を分けて書く（"C:" + "\\" + "Users" …）。本物のユーザー名は書かない

## テストが気づくべき誤り（自己チェック。1つずつ本体に入れて pytest が失敗することを確かめ、手で元に戻す。結果を報告に表で書く）
| No | 誤り |
|---|---|
| 1 | ルート直下のファイルを対象に加えない（元の3ファイルだけに戻す） |
| 2 | UTF-16 のファイルを読まない |
| 3 | ユーザー名の除外文字に半角「.」を戻す |
| 4 | main の parse_args を引数なし（sys.argv を読む形）に戻す |

## やらないこと
- 検出の表示文（「Windowsパス（ユーザー名: <ユーザー名>）」など）の変更
- 対象フォルダ（src、tests、docs、output）や除外フォルダの変更（ルート直下のファイルの追加以外）
- 他のソースの変更、ファイルの中身の書き換え

## 完成の条件
- 上の誤り4通りのどれを入れても pytest が失敗する
- `python -m pytest` 全件合格、`python -m pytest -q tests/test_check_public.py` も合格
- 実データの公開前チェックの結果を報告にそのまま貼ってある
- 問題タブのエラー0件。ルート直下などに新しい作業ファイルがない

## 完了後
- docs/dev/reports/M7-05_report.md に、docs/dev/reports/_template.md の書式どおりに報告を書く（「変更したファイル」は表で、バイト数付き。実行結果・テスト結果は画面の出力をそのまま貼る）
