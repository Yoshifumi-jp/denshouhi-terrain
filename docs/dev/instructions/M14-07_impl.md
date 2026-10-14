# 指示書 M14-07（実装・公開前チェックの対象拡大）　作成日：2026-10-14

最初に AGENTS.md を読んでから作業してください（特に「報告書に貼る実行結果は、画面に出た文をそのまま貼る」）。
作業前に、エディタのタブをすべて閉じてから始めてください。docs/dev/status.md・docs/dev/01_plan.md・output/・data/・docs/ 配下のファイルを開いたり保存したり元に戻したりしないでください。
GitHub への push・git commit は行わない。update_all.py・run_batch.py・update.py・summarize_national.py・build_site.py・make_national_pdf.py・build_national.py・count_missing.py は実行しない（テストからの呼び出しは可）。

## 目的（このテーマ1つ）
公開前チェック（src/check_public.py）が、GitHub に載るのに今は調べていないファイルも調べるようにする。あわせて、build_national を quiet=True で呼んだときにチェックの結果が無視される点を直す（M14_review-3 軽微 No.1）。

## 背景（Claude の調査 2026-10-14）
- 公開は第1版と同じく、main と同じ中身のコミットを public に作って GitHub に送る。つまり **Git で管理しているファイルはすべて公開される**
- 今の collect_targets は src・tests・docs・output とルート直下のファイルだけを見て、data/ は丸ごと飛ばす。しかし data/raw/2026-09-24/denshouhi_20260924.csv（1.3MB）は Git で管理されていて公開される
- find_private_info は先頭1024バイトに \x00 があるファイルを飛ばす。そのため PDF 2件（docs・output の national_report.pdf）と PNG 746件は、作成者情報などが入っていても見つけられない

## 対象ファイル
- 変更する：src/check_public.py、src/build_national.py、tests/test_check_public.py、tests/test_build_national.py
- 新しく作る：docs/dev/reports/M14-07_report.md
- 変えないもの：上記以外のすべて

## やること
1. src/check_public.py collect_targets：
   - data/ は今どおり飛ばすが、**data/raw/<フォルダ>/ の直下にある .csv だけ**は対象に加える（data/raw/rivers・coastline の地理データ、data/cache・data/processed は加えない。どれも .gitignore で公開されない）
   - ルート直下の隠しフォルダ .agents/ があれば、その中のファイルも対象にする（今はないが、Claude が書いてよいルールの置き場のため）
2. src/check_public.py find_private_info：バイナリのファイルのうち、次の2種類は飛ばさずに調べる（そのほかのバイナリは今どおり飛ばす）
   - .pdf：`stream`〜`endstream` の間（圧縮された中身）を取り除いた残りを latin-1 で文字にし、今の3つのパターン（Windows パス・ホームのパス・メールアドレス）を当てる。さらに `/Author` があれば種類「PDFの作成者情報」として1件にする（行番号は 1）
   - .png：チャンク（PNG の中の区切り）を順に読み、tEXt・iTXt・zTXt（zTXt は zlib で展開）の中身だけを utf-8（読めない文字は置き換え）で文字にして、3つのパターンを当てる（行番号は 1）
   - 見つけたときの表示の種類の文は、今の3種類（「Windowsパス（ユーザー名: <ユーザー名>）」など）と同じにする
3. src/build_national.py：quiet=True でも公開前チェックの結果を見る。問題があれば、表示はせずに `RuntimeError("公開前チェック：問題あり（<件数>件）")` を出す。quiet=False のときの表示・終了の仕方は変えない
4. テストを足す（tmp_path に作る。実データのファイルは書き換えない）：
   - test_check_public.py：(a) data/raw/2026-01-01/x.csv は対象、data/cache・data/processed・data/raw/rivers の下は対象外 (b) ユーザー名入りの Windows パスを /Author に入れた小さな PDF（文字列で組んでよい）→ 問題あり (c) 同じパスが stream〜endstream の中だけにある PDF → 問題なし (d) tEXt チャンクにメールアドレスを入れた PNG（struct と zlib.crc32 で組む）→ 問題あり (e) tEXt が「Software=Matplotlib…」だけの PNG → 問題なし
   - test_build_national.py：find_private_info が1件返すよう差し替えて quiet=True で呼ぶと RuntimeError
   - 既存の test_check_real_project は、data/raw/2026-09-24/denshouhi_20260924.csv と docs/national_report.pdf が対象に含まれることも確かめる

## やらないこと
- パターン（正規表現）そのものの変更、表示の文の変更
- build_site.py・update_all.py の変更
- PDF・PNG を作り直すこと

## 完成の条件（既知の答え：Claude が 2026-10-14 に実データで確かめた値）
- `python src/check_public.py` が「公開前チェック：問題なし」
- 対象のファイル数（ディレクトリを除く）：今（この指示書を置いた時点）は 1,989。data/raw の CSV 1件と報告書 M14-07_report.md 1件が増えて **1,991** になる。拡張子ごと：.csv 816・.png 746・.md 233・.html 142・.py 44・（拡張子なし）6・.pdf 2・.ini 1・.txt 1（テストで作業用ファイルを足した場合はその分を報告に書く）
- 実データでは：data/raw の CSV 0件、PDF 2件とも /Author・/Creator・/Producer なし・0件、PNG 746件はすべて tEXt が「Software=Matplotlib version3.11.2, https://matplotlib.org/」の1つだけで0件
- pytest 全件合格（215＋足したテスト関数の数）、pyflakes 0件、LF
- git diff は対象ファイルの4つだけ

## 報告に貼るもの（画面に出た文をそのまま。ユーザー名を含む絶対パスは `<プロジェクト>` に置き換える）
- `git diff src/check_public.py src/build_national.py`
- `python src/check_public.py`
- 対象の数：`python -c "import sys;sys.path.insert(0,'src');from check_public import collect_targets,PROJECT_ROOT;from collections import Counter;t=[p for p in collect_targets(PROJECT_ROOT) if p.is_file()];print(len(t));print(Counter(p.suffix for p in t).most_common())"`
- `python -m pytest -q`（最後の行）、`python -m pytest -q tests/test_check_public.py tests/test_build_national.py`（最後の行）、`python -m pyflakes src/check_public.py src/build_national.py tests/test_check_public.py tests/test_build_national.py`
- 改行コード：`python -c "import pathlib;[print(p, b'\r\n' in pathlib.Path(p).read_bytes()) for p in ['src/check_public.py','src/build_national.py','tests/test_check_public.py','tests/test_build_national.py']]"`（すべて False）
- `git status --short`（「??」が報告書だけであること）
- 変更したファイルのバイト数

## 完了後
- 自己チェックを行い、docs/dev/reports/M14-07_report.md に報告を書く。
